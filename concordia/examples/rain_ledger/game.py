# Copyright 2026 DeepMind Technologies Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Compose Rain Ledger with standard prefabs, Asynchronous and shared controls."""

import json
from absl import logging

import dataclasses
import types
import pathlib
import threading
from typing import cast

from concordia.agents import entity_agent_with_logging

import numpy as np
from concordia.components.agent import human_act_component
from concordia.components.agent import constant
from concordia.components.agent import concat_act_component
from concordia.components.game_master import next_acting
from concordia.components.game_master import switch_act
from concordia.environment.engines import asynchronous
from concordia.environment import engine as engine_lib
from concordia.examples.astral_canticle import human_io
from concordia.examples.rain_ledger import content as c
from concordia.examples.rain_ledger import rules
from concordia.prefabs.entity import minimal
from concordia.prefabs.simulation import generic
from concordia.typing import entity as entity_lib
from concordia.typing import entity_component
from concordia.typing import prefab
from concordia.utils import async_measurements
from concordia.utils import operation_service as ops
from concordia.utils import simulation_server
from concordia.utils import structured_logging
from concordia.environment import step_controller

PUBLIC_JOBS = {
    'tools': 'Recover a crew’s pawned tools. Offered fee $12.',
    'photograph': (
        'Photograph a councillor’s midnight visitor. Offered fee $20.'
    ),
    'medicine': 'Carry cold medicine to the Narrows. Offered fee $9.',
}


class RainSession(human_io.HumanSession):
  """Use the existing inbox/retry contract, adding only scenario presentation."""

  def __init__(self, ledger, *, restored=False):
    super().__init__(initial_status='Port Mercy — opening the office')
    self.ledger = ledger
    self.pause_after = False
    self.controller: step_controller.StepController | None = None
    if not restored:
      self.add_observation(c.OPENING)
    else:
      self.add_observation(
          'Returned to Port Mercy. Your recorded case follows; the casebook'
          ' shows your current position.'
      )

  def __call__(self, request):
    # The GM publishes resolved player outcomes exactly once. Retain the full
    # standard actor context in the request, but do not duplicate its memory
    # observation history into the presentation transcript at every new prompt.
    return super().__call__(
        dataclasses.replace(
            request,
            contexts=types.MappingProxyType({
                **request.contexts,
                '__observation__': '',
            }),
        )
    )

  def snapshot(self):
    result = super().snapshot()
    if self.controller is not None and self.controller.at_pause_boundary:
      result['status'] = 'Paused safely. Read, inspect or resume when ready.'
      result['revision'] = str(result['revision']) + ':paused'
    result.update(
        casebook=self.ledger.public(),
        suggestions=self.ledger.available(),
        map={
            key: {'name': val[0], 'exits': val[2]}
            for key, val in c.PLACES.items()
        },
        contacts={
            key: value
            for key, value in c.CONTACTS.items()
            if key != 'iona' or 'ledger' in self.ledger.public()['evidence']
        },
        jobs={
            key: {'place': value['place'], 'description': PUBLIC_JOBS[key]}
            for key, value in c.JOBS.items()
        },
        pause_after=self.pause_after,
    )
    return result


class ResidentAct(concat_act_component.ConcatActComponent):
  """Standard ConcatAct choice policy, with explicit no-effect provider failure."""

  def __init__(self, model, name, session):
    super().__init__(model=model, randomize_choices=False)
    self.name, self.session = name, session

  def get_action_attempt(self, contexts, action_spec):
    try:
      return super().get_action_attempt(contexts, action_spec)
    except Exception as exc:
      logging.exception('Resident inference failed for %s', self.name)
      self._logging_channel(
          {'actor': self.name, 'provider_failure': type(exc).__name__}
      )
      self.session.add_observation(
          f'Local model unavailable for {self.name}; no resident consequence'
          ' was invented.'
      )
      return 'wait'


class PortAuthority(switch_act.SwitchAct):
  """Extend standard SwitchAct hooks with Port Mercy's bounded scenario rules.

  Base SwitchAct owns output-type dispatch and standard fixed-spec/termination
  components. Hooks execute in the caller's thread, preserving engine-provided
  capture keys; parallel context hooks must not guess an actor from thread ID.
  """

  def __init__(self, ledger, model, session):
    super().__init__(model=model, entity_names=(c.PLAYER, *c.NPCS))
    self.ledger, self.model, self.session = ledger, model, session

  def _next_acting(self, contexts, action_spec):
    del contexts
    s = self.ledger.get_state()
    return ', '.join(
        name
        for name in action_spec.options
        if name == c.PLAYER
        or (
            s['npc_turns'][name] < s['turn']
            and self.ledger.resident_moves(name)
        )
    )

  def _next_entity_action_spec(self, contexts, action_spec):
    actor = cast(
        entity_agent_with_logging.EntityAgentWithLogging, self.get_entity()
    ).get_capture_key_for_thread(threading.get_ident())
    if actor in c.NPCS:
      return engine_lib.action_spec_to_string(
          entity_lib.choice_action_spec(
              call_to_action=(
                  'Choose one practical step for {name}, using only their own'
                  ' knowledge and observations. Choose wait only if neither'
                  ' action is appropriate.'
              ),
              options=(*self.ledger.resident_moves(actor), 'wait'),
          )
      )
    return super()._next_entity_action_spec(contexts, action_spec)

  def _make_observation(self, contexts, action_spec):
    del contexts, action_spec
    actor = cast(
        entity_agent_with_logging.EntityAgentWithLogging, self.get_entity()
    ).get_capture_key_for_thread(threading.get_ident())
    if actor is None:
      raise RuntimeError(
          'Port Mercy requires the standard engine actor capture.'
      )
    if actor == c.PLAYER:
      return self.ledger.view()
    s = self.ledger.get_state()
    local = {
        'Nessa Rook': {
            'shelter_beds': s['shelter_beds'],
            'petition': s['petition'],
        },
        'Silas Marr': {
            'union_support': s['union_support'],
            'public_guard_pressure': s['security'],
        },
        'Edwin Holt': {
            'security': s['security'],
            'bond_offer': s['bond_offer'],
        },
    }
    return (
        c.NPCS[actor]['affordances']
        + '\nCurrent local conditions: '
        + str(local.get(actor, {}))
        + f" Your completed agenda actions: {s['agendas'].get(actor, 0)}."
        ' Public notices: '
        + ' '.join(s['news'][-4:])
        + '\nEvents witnessed at your workplace: '
        + ' '.join(s['witnessed'].get(actor, [])[-4:])
    )

  def _resolve(self, contexts, action_spec):
    del contexts, action_spec
    actor = cast(
        entity_agent_with_logging.EntityAgentWithLogging, self.get_entity()
    ).get_capture_key_for_thread(threading.get_ident())
    if actor is None:
      raise RuntimeError(
          'Port Mercy requires the standard engine actor capture.'
      )
    with self.ledger.lock:
      attempt = self.ledger.pending.pop(actor, None)
    if attempt is None:
      raise RuntimeError(f'No actor-scoped attempt for {actor}')
    dialogue_log = None
    if actor == c.PLAYER:
      try:
        intent = rules.parse_intent(attempt, self.model, self.ledger)
      except Exception as exc:
        logging.exception('Player interpretation failed')
        self._logging_channel({'provider_failure': type(exc).__name__})
        intent = {}
        self.session.add_observation(
            'Local interpretation is unavailable. No time or resources were'
            ' spent; exact shorthand remains available.'
        )
      confirmed = (
          self.ledger.public().get('proposal')
          if intent.get('verb') == 'confirm'
          else None
      )
      result = self.ledger.resolve(intent, attempt)
      effective = confirmed['intent'] if confirmed else intent
      spoken_attempt = (
          confirmed.get('attempt', attempt) if confirmed else attempt
      )
      target = effective.get('target')
      if (
          not intent.get('_needs_confirmation')
          and effective.get('verb') == 'talk'
          and target in c.CONTACTS
          and c.CONTACTS[target][1] == self.ledger.public()['location']
          and len(spoken_attempt.split()) > 3
      ):
        try:
          speech, dialogue_log = self.dialogue(target, spoken_attempt, result)
          result += speech
        except Exception as exc:
          self._logging_channel({'dialogue_failure': type(exc).__name__})
          result += (
              '\nLocal dialogue unavailable; the recorded response above'
              ' stands.'
          )
      self.session.add_observation(result)
    else:
      if attempt not in c.NPCS[actor]['moves']:
        result = (
            'Resident waits; no consequence committed.'
            if attempt == 'wait'
            else 'Resident proposal invalid; no consequence committed.'
        )
        with self.ledger.lock:
          self.ledger.state['npc_turns'][actor] = self.ledger.state['turn']
      else:
        result = self.ledger.npc_resolve(actor, attempt, '')
    self._logging_channel({
        'actor': actor,
        'attempt': attempt,
        'result': result,
        'ledger': self.ledger.get_state(),
        'interpretation': intent if actor == c.PLAYER else None,
        'dialogue': dialogue_log,
    })
    return result

  def dialogue(self, contact, attempt, ruling):
    """Character speech can respond to a subject but cannot grant game effects."""
    name, _, voice = c.CONTACTS[contact]
    text = self.model.sample_text(
        f'Speak in FIRST PERSON as {name}. Voice: {voice}\n'
        f'The investigator asks: {attempt}\n'
        f'Established facts and binding stance: {ruling}\n'
        'Answer the actual question in one or two NEW short sentences. Do not'
        ' repeat the recorded wording or narrate stage directions. Do not add'
        ' names, clues, facts, promises, actions, payments or relationship'
        ' changes. Preserve any refusal. No rain metaphors. Plain spoken text'
        ' only, no JSON or speaker label.',
        max_tokens=100,
        temperature=0.4,
    )
    record = {'speaker': name, 'subject': attempt, 'model_reply': text}
    if not text.strip():
      return '\nNo further reply; the recorded facts stand.', record
    return f'\n{name}: “{text.strip()}”', record


def configuration(ledger, session):
  """Runtime bindings in prefab closures keep locks out of prefab JSON."""

  class Investigator(prefab.Prefab):
    description = 'Human investigator with standard minimal memory and input.'

    def build(self, model, memory_bank):
      return minimal.Entity(
          params={
              **self.params,
              'measurements': async_measurements.ReactiveMeasurements(),  # pyrefly: ignore[bad-assignment]
          }
      ).build(
          model,
          memory_bank,
          act_component_factory=lambda order: human_act_component.HumanActComponent(
              session, component_order=order
          ),
      )

  class Resident(prefab.Prefab):
    description = 'Independent local-model resident with a scoped agenda.'

    def build(self, model, memory_bank):
      return minimal.Entity(
          params={
              **self.params,
              'measurements': async_measurements.ReactiveMeasurements(),  # pyrefly: ignore[bad-assignment]
          }
      ).build(
          model,
          memory_bank,
          act_component=ResidentAct(model, self.params['name'], session),
      )

  class City(prefab.Prefab):
    description = 'Port Mercy scenario ledger and actor-scoped adjudication.'

    def build(self, model, memory_bank):
      return minimal.Entity(
          params={
              **self.params,
              'measurements': async_measurements.ReactiveMeasurements(),  # pyrefly: ignore[bad-assignment]
              'extra_components': {  # pyrefly: ignore[bad-assignment]
                  'Ledger': ledger,
                  switch_act.DEFAULT_TERMINATE_COMPONENT_KEY: constant.Constant(
                      'No', pre_act_label=''
                  ),
                  switch_act.DEFAULT_NEXT_ACTION_SPEC_COMPONENT_KEY: next_acting.FixedActionSpec(
                      entity_lib.free_action_spec(
                          call_to_action=(
                              'What do you attempt? Use your own words or a'
                              ' suggested starting point.'
                          )
                      )
                  ),
              },
          }
      ).build(
          model,
          memory_bank,
          act_component=PortAuthority(ledger, model, session),
      )

  return prefab.Config(
      prefabs={
          'investigator': Investigator(),
          'resident': Resident(),
          'city': City(),
      },
      instances=[
          prefab.InstanceConfig(
              'investigator',
              prefab.Role.ENTITY,
              {
                  'name': c.PLAYER,
                  'custom_instructions': (
                      'You decide what Rowan attempts. No action is chosen for'
                      ' you.'
                  ),
              },
          )
      ]
      + [
          prefab.InstanceConfig(
              'resident',
              prefab.Role.ENTITY,
              {
                  'name': name,
                  'custom_instructions': (
                      value['voice']
                      + '\nPrivate knowledge: '
                      + value['knowledge']
                  ),
                  'goal': value['goal'],
              },
          )
          for name, value in c.NPCS.items()
      ]
      + [
          prefab.InstanceConfig('city', prefab.Role.GAME_MASTER, {'name': c.GM})
      ],
      default_max_steps=1_000_000_000,
  )


class Game:
  """One simulation and standard operation service; no replacement lifecycle."""

  def __init__(self, model, output, *, port=0, resume=False, checkpoint=None):
    self.output = pathlib.Path(output)
    self.ledger = rules.Ledger()
    if resume:
      self.ledger.set_state(
          json.loads((self.output / 'ledger.json').read_text())
      )
    self.session = RainSession(
        self.ledger, restored=resume or checkpoint is not None
    )
    self.config = configuration(self.ledger, self.session)
    self.engine = asynchronous.Asynchronous(sleep_time=0.2)
    self.simulation = generic.Simulation(
        self.config, model, lambda _: np.ones(8), engine=self.engine
    )
    if checkpoint is not None:
      self.simulation.load_from_checkpoint(
          json.loads(pathlib.Path(checkpoint).read_text())
      )
    if resume or checkpoint is not None:
      for entry in self.ledger.public()['history']:
        self.session.add_observation(
            '> ' + str(entry['attempt']) + '\n' + entry['result']
        )
      self.session.add_observation(self.ledger.view())
    self.operations = ops.OperationService(project_id='rain-ledger')
    self.server = simulation_server.SimulationServer(
        port=port, operation_service=self.operations
    )
    self.server.set_simulation(self.simulation)
    self.controller = self.server.step_controller
    self.session.controller = self.controller
    self.operations.set_view('developer', self.inspect)
    self.operations.set_view('player', self.session.snapshot)
    self._register()
    self.completed = 0

  def inspect(self):
    return {
        'engine': 'Asynchronous',
        'paused': self.controller.is_paused,
        'quiescent': self.controller.at_pause_boundary,
        'resident_goals': {
            actor.name: (
                cast(entity_component.EntityWithComponents, actor)
                .get_component('Goal', type_=constant.Constant)
                .get_state()['state']
            )
            for actor in self.simulation.get_entities()
            if actor.name in c.NPCS
        },
        'ledger': self.ledger.get_state(),
        'completed': self.completed,
    }

  def _register(self):
    for name, description, callback, mutation in (
        (
            'session.inspect',
            'Inspect authoritative ledger and actual pause boundary.',
            lambda _: self.inspect(),
            False,
        ),
        (
            'run.status',
            'Inspect engine status.',
            lambda _: self.inspect(),
            False,
        ),
        (
            'run.pause',
            'Request pause; pending human input remains pending.',
            lambda _: self.controller.pause(),
            True,
        ),
        (
            'run.resume',
            'Resume standard actor loops.',
            lambda _: self.controller.play(),
            True,
        ),
        (
            'run.pause_after_action',
            'Pause after the next genuine human action resolves.',
            self.arm_pause,
            True,
        ),
        (
            'checkpoint.save',
            'Save standard checkpoint at an acknowledged boundary.',
            self.checkpoint,
            True,
        ),
        (
            'log.export',
            'Export standard SimulationLog at an acknowledged pause boundary.',
            self.export_log,
            True,
        ),
    ):
      self.operations.register(
          ops.Operation(name, description, {}, callback, mutation=mutation)
      )
    self.operations.register(
        ops.Operation(
            'ledger.cash',
            'Edit cash only at a standard acknowledged pause boundary.',
            {'value': ops.Parameter('integer', 'Nonnegative cash.')},
            self.edit_cash,
            mutation=True,
        )
    )
    self.operations.register(
        ops.Operation(
            'resident.goal',
            'Edit a resident Goal through the standard component setter at'
            ' quiescence.',
            {
                'actor': ops.Parameter('string', 'Resident full name.'),
                'value': ops.Parameter(
                    'string', 'New goal, up to 1000 characters.'
                ),
            },
            self.edit_goal,
            mutation=True,
        )
    )

  def edit_goal(self, arguments):
    actor, value = arguments['actor'], arguments['value']
    if actor not in c.NPCS or not value.strip() or len(value) > 1000:
      raise ops.OperationError(
          'invalid_arguments',
          'Choose a resident and a nonempty goal of at most 1000 characters.',
      )
    try:
      with self.controller.paused_boundary():
        self.simulation.set_component_dynamic_state(
            actor, 'Goal', 'state', value
        )
    except ValueError as exc:
      raise ops.OperationError('paused_boundary_required', str(exc)) from exc
    return self.inspect()

  def arm_pause(self, _=None):
    self.session.pause_after = True
    return {'pause_after_action': True}

  def edit_cash(self, arguments):
    value = arguments['value']
    if type(value) is not int or not 0 <= value <= 10000:
      raise ValueError('Cash must be an integer between 0 and 10000.')
    try:
      with self.controller.paused_boundary():
        state = self.ledger.get_state()
        state['cash'] = value
        self.ledger.set_state(state)
    except ValueError as exc:
      raise ops.OperationError('paused_boundary_required', str(exc)) from exc
    return self.inspect()

  def checkpoint(self, _=None):
    with self.controller.paused_boundary():
      self.output.mkdir(parents=True, exist_ok=True)
      self.engine.pause()  # Materialize standard AsyncLogCollector only when quiescent.
      try:
        self.simulation.save_checkpoint(
            self.completed, str(self.output / 'checkpoints')
        )
      finally:
        self.engine.play()
    return {
        'directory': str(self.output / 'checkpoints'),
        'step': self.completed,
    }

  def export_log(self, _=None):
    with self.controller.paused_boundary():
      self.engine.pause()
      try:
        log = structured_logging.SimulationLog.from_raw_log(
            self.simulation.get_raw_log()
        )
        self.output.mkdir(parents=True, exist_ok=True)
        (self.output / 'simulation.json').write_text(log.to_json())
        (self.output / 'log.html').write_text(log.to_html())
      finally:
        self.engine.play()
    return {
        'json': str(self.output / 'simulation.json'),
        'html': str(self.output / 'log.html'),
    }

  def play(self, *, max_steps=1_000_000_000):
    self.output.mkdir(parents=True, exist_ok=True)
    self.controller.play()

    def completed(step):
      with self.ledger.lock:
        self.completed += 1
      if step.acting_entity == c.PLAYER and self.session.pause_after:
        self.controller.pause()
        self.session.pause_after = False
      # A lock-consistent scenario save is distinct from a complete checkpoint.
      # Standard simulation snapshots are only taken at acknowledged boundaries.
      with self.ledger.lock:
        temporary = self.output / 'ledger.json.tmp'
        temporary.write_text(json.dumps(self.ledger.get_state(), indent=2))
        temporary.replace(self.output / 'ledger.json')
      self.server.broadcast_step(step)

    log = self.simulation.play(
        max_steps=max_steps,
        step_controller=self.controller,
        step_callback=completed,
    )
    (self.output / 'simulation.json').write_text(log.to_json())
    (self.output / 'log.html').write_text(log.to_html())
    return log

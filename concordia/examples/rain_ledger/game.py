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
import pathlib
import re
import threading

import numpy as np
from concordia.components.agent import human_act_component
from concordia.components.game_master import event_resolution
from concordia.environment.engines import asynchronous
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

PUBLIC_JOBS = {
    'tools': 'Recover a crew’s pawned tools. Offered fee $12.',
    'photograph': (
        'Photograph a councillor’s midnight visitor. Offered fee $20.'
    ),
    'medicine': 'Carry cold medicine to the Narrows. Offered fee $9.',
}


class RainSession(human_io.HumanSession):
  """Use the existing inbox/retry contract, adding only scenario presentation."""

  def __init__(self, ledger):
    super().__init__(initial_status='Port Mercy — opening the office')
    self.ledger = ledger
    self.pause_after = False
    self.add_observation(c.OPENING)

  def snapshot(self):
    result = super().snapshot()
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


class ResidentAct(
    entity_component.ActingComponent, entity_component.ComponentWithLogging
):
  """Local model chooses a bounded agenda action using only its own observations."""

  def __init__(self, model, name):
    super().__init__()
    self.model, self.name = model, name

  def get_action_attempt(self, contexts, action_spec):
    person = c.NPCS[self.name]
    response = self.model.sample_text(
        f"You are {self.name}. {person['voice']} Goal: {person['goal']}\n"
        f"Private knowledge: {person['knowledge']}\n"
        + '\n'.join(contexts.values())
        + f"\nChoose one action from {person['moves']}. Return JSON with move"
        ' and a brief line spoken only to yourself. Do not invent other'
        " people's actions.",
        max_tokens=130,
        temperature=0.6,
    )
    self._logging_channel({'actor': self.name, 'proposal': response})
    return response

  def get_state(self):
    return {}

  def set_state(self, state):
    pass


class PortAuthority(
    entity_component.ActingComponent, entity_component.ComponentWithLogging
):
  """Scenario action rules; standard engine owns all scheduling and threading."""

  def __init__(self, ledger, model, session):
    super().__init__()
    self.ledger, self.model, self.session = ledger, model, session

  def get_action_attempt(self, contexts, action_spec):
    del contexts
    kind = action_spec.output_type
    actor = self.get_entity().get_capture_key_for_thread(threading.get_ident())
    if kind == entity_lib.OutputType.TERMINATE:
      return 'No'
    if kind == entity_lib.OutputType.NEXT_ACTING:
      # First engine setup call has every actor as options. Each actual actor
      # loop subsequently asks with its own singleton option.
      s = self.ledger.get_state()
      return ', '.join(
          name
          for name in action_spec.options
          if name == c.PLAYER or s['npc_turns'][name] < s['turn']
      )
    if kind == entity_lib.OutputType.NEXT_ACTION_SPEC:
      return json.dumps({
          'call_to_action': (
              'What do you attempt? Use your own words or a suggested starting'
              ' point.'
          ),
          'output_type': 'free',
          'options': [],
      })
    if kind == entity_lib.OutputType.MAKE_OBSERVATION:
      if actor == c.PLAYER:
        return self.ledger.view()
      s = self.ledger.get_state()
      local = {
          'Nessa Rook': {
              'shelter_beds': s['shelter_beds'],
              'petition': s['petition'],
          },
          'Silas Marr': {'union_support': s['union_support']},
          'Edwin Holt': {
              'security': s['security'],
              'bond_offer': s['bond_offer'],
          },
      }
      return (
          str(local.get(actor, {}))
          + f" Your completed agenda actions: {s['agendas'].get(actor, 0)}."
          ' Public notices: '
          + ' '.join(s['news'][-4:])
          + '\nEvents witnessed at your workplace: '
          + ' '.join(s['witnessed'].get(actor, [])[-4:])
      )
    if kind != entity_lib.OutputType.RESOLVE:
      raise ValueError(f'Unsupported GM request: {kind}')
    with self.ledger.lock:
      attempt = self.ledger.pending.pop(actor, None)
    if attempt is None:
      raise RuntimeError(f'No actor-scoped attempt for {actor}')
    if actor == c.PLAYER:
      intent = rules.parse_intent(attempt, self.model, self.ledger)
      result = self.ledger.resolve(intent, attempt)
      target = intent.get('target')
      if (
          intent.get('verb') == 'talk'
          and target in c.CONTACTS
          and c.CONTACTS[target][1] == self.ledger.public()['location']
          and len(attempt.split()) > 3
      ):
        result += self.dialogue(target, attempt, result)
      self.session.add_observation(result)
    else:
      try:
        match = re.search(r'\{[^{}]*\}', attempt)
        value = json.loads(match.group() if match else '{}')
      except (TypeError, ValueError):
        value = {}
      move = value.get('move') if isinstance(value, dict) else None
      if move not in c.NPCS[actor]['moves']:
        result = 'Resident proposal invalid; no consequence committed.'
        with self.ledger.lock:
          self.ledger.state['npc_turns'][actor] = self.ledger.state['turn']
      else:
        result = self.ledger.npc_resolve(
            actor, move, str(value.get('line', ''))
        )
    self._logging_channel({
        'actor': actor,
        'attempt': attempt,
        'result': result,
        'ledger': self.ledger.get_state(),
    })
    return result

  def dialogue(self, contact, attempt, ruling):
    """Character speech can respond to a subject but cannot grant game effects."""
    name, _, voice = c.CONTACTS[contact]
    text = self.model.sample_text(
        f'You speak as {name}. Voice: {voice}\nThe investigator says:'
        f' {attempt}\nOnly established facts and binding stance for your reply:'
        f' {ruling}\nReply to the actual subject in two short noir sentences.'
        ' Do not add names, clues, facts, promises, locations, actions,'
        ' payments or relationship changes. Preserve any refusal. No rain'
        ' metaphors. Return JSON with only line.',
        max_tokens=130,
        temperature=0.4,
    )
    try:
      match = re.search(r'\{[^{}]*\}', text)
      line = json.loads(match.group() if match else '{}').get('line', '')
    except (ValueError, AttributeError):
      line = ''
    self._logging_channel(
        {'speaker': name, 'subject': attempt, 'model_reply': text}
    )
    if not isinstance(line, str) or not line.strip():
      return (
          '\nThe conversation adds no clear reply; the recorded facts above'
          ' stand.'
      )
    return f'\n{name}: “{line.strip()}”'

  def get_state(self):
    return {}

  def set_state(self, state):
    pass


def configuration(ledger, session):
  """Runtime bindings in prefab closures keep locks out of prefab JSON."""

  class Investigator(prefab.Prefab):
    description = 'Human investigator with standard minimal memory and input.'

    def build(self, model, memory_bank):
      return minimal.Entity(
          params={
              **self.params,
              'measurements': async_measurements.ReactiveMeasurements(),
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
              'measurements': async_measurements.ReactiveMeasurements(),
          }
      ).build(
          model,
          memory_bank,
          act_component=ResidentAct(model, self.params['name']),
      )

  class City(prefab.Prefab):
    description = 'Port Mercy scenario ledger and actor-scoped adjudication.'

    def build(self, model, memory_bank):
      return minimal.Entity(
          params={
              **self.params,
              'measurements': async_measurements.ReactiveMeasurements(),
              'extra_components': {'Ledger': ledger},
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
                  'custom_instructions': value['voice'],
                  'goal': value['goal'],
              },
          )
          for name, value in c.NPCS.items()
      ]
      + [
          prefab.InstanceConfig('city', prefab.Role.GAME_MASTER, {'name': c.GM})
      ],
      default_max_steps=100000,
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
    self.session = RainSession(self.ledger)
    if resume:
      for entry in self.ledger.public()['history']:
        if entry['actor'] == c.PLAYER:
          self.session.add_observation(
              '> ' + str(entry['attempt']) + '\n' + entry['result']
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
    self.operations = ops.OperationService(project_id='rain-ledger')
    self.server = simulation_server.SimulationServer(
        port=port, operation_service=self.operations
    )
    self.server.set_simulation(self.simulation)
    self.controller = self.server.step_controller
    self.operations.set_view('developer', self.inspect)
    self.operations.set_view('player', self.session.snapshot)
    self._register()
    self.completed = 0

  def inspect(self):
    return {
        'engine': 'Asynchronous',
        'paused': self.controller.is_paused,
        'quiescent': self.controller.at_pause_boundary,
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

  def arm_pause(self, _=None):
    self.session.pause_after = True
    return {'pause_after_action': True}

  def edit_cash(self, arguments):
    value = arguments['value']
    if type(value) is not int or not 0 <= value <= 10000:
      raise ValueError('Cash must be an integer between 0 and 10000.')
    with self.controller.paused_boundary():
      state = self.ledger.get_state()
      state['cash'] = value
      self.ledger.set_state(state)
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

  def play(self, *, max_steps=100000):
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

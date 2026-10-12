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

"""Bounded actual-engine fixture; not evidence of language-model quality."""

import argparse
import json
import pathlib
import subprocess
import sys
import uuid
import threading
import time

from concordia.examples.rain_ledger import game
from concordia.examples.rain_ledger import rules
from concordia.language_model import no_language_model


class Fixture(no_language_model.NoLanguageModel):

  def sample_text(self, prompt, **kwargs):
    if 'You are Nessa' in prompt:
      return '{"move":"shelter","line":"Six beds. Start there."}'
    if 'You are Silas' in prompt:
      return '{"move":"petition","line":"Put the wages in writing."}'
    return '{"move":"offer","line":"I can discuss a bond."}'


def until(predicate, timeout=180):
  deadline = time.monotonic() + timeout
  while not predicate():
    if time.monotonic() >= deadline:
      raise TimeoutError('Timed out waiting for engine boundary')
    time.sleep(0.05)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--output', type=pathlib.Path, required=True)
  parser.add_argument('--live', action='store_true')
  parser.add_argument('--model', default='llama3.2:3b')
  parser.add_argument('--no-think', action='store_true')
  args = parser.parse_args()
  if args.live:
    from concordia.contrib.language_models.ollama import ollama_model
    from concordia.language_model import call_limit_wrapper

    model = call_limit_wrapper.CallLimitLanguageModel(
        ollama_model.OllamaLanguageModel(
            args.model,
            think=False if args.no_think else None,
            request_timeout=60,
            max_output_tokens=180,
            response_format=None,
            system_message=(
                'Follow the requested format. Choose only a supplied option'
                ' when asked to choose.'
            ),
        ),
        max_calls=40,
    )
  else:
    model = Fixture()
  instance = game.Game(model, args.output, port=8797)
  instance.server.start()
  cli_transcript = []

  def cli(operation, arguments=None, expected_code=0):
    prefix = [
        sys.executable,
        '-m',
        'concordia.command_line_interface.concordia_session',
        '--url',
        'http://127.0.0.1:8797',
    ]
    state = json.loads(
        subprocess.run(
            prefix + ['state'], capture_output=True, text=True, check=True
        ).stdout
    )
    request = {
        'operation': operation,
        'arguments': arguments or {},
        'references': state['references'],
        'revision': state['revision'],
        'retry_key': str(uuid.uuid4()),
    }
    result = subprocess.run(
        prefix + ['call'],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=20,
    )
    cli_transcript.append({
        'request': request,
        'code': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
    })
    assert result.returncode == expected_code, cli_transcript[-1]
    return result

  errors = []

  def run():
    try:
      instance.play(max_steps=1000)
    except Exception as exc:
      errors.append(repr(exc))

  worker = threading.Thread(target=run)
  worker.start()
  try:
    until(lambda: instance.session.snapshot()['pending'] or errors)
    assert not errors, errors
    pending = instance.session.snapshot()['pending']
    cli('run.pause')
    time.sleep(0.3)
    assert (
        not instance.controller.at_pause_boundary
    ), 'pending human is not quiescent'
    rejection = cli('ledger.cash', {'value': 999}, expected_code=2)
    assert (
        json.loads(rejection.stderr)['error']['code']
        == 'paused_boundary_required'
    )
    assert instance.ledger.public()['cash'] == 18
    cli('run.resume')
    actions = [
        'go cafe',
        'promise ada',
        'protect iona',
        'go narrows',
        'go warehouse',
        'investigate ledger',
    ]
    if args.live:
      actions = [
          'I walk from my office to the Lantern cafe.',
          'promise ada',
          'Arrange a safe bed for Iona above the cafe.',
          'go narrows',
          'go warehouse',
          'investigate ledger',
      ]
    previous = None
    for index, action in enumerate(actions):
      until(
          lambda: (p := instance.session.snapshot()['pending'])
          and p['id'] != previous
          or errors
      )
      assert not errors, errors
      pending = instance.session.snapshot()['pending']
      previous = pending['id']
      if index == len(actions) - 1:
        cli('run.pause_after_action')
      before_turn = instance.ledger.public()['turn']
      assert instance.session.submit(previous, action)
      assert not instance.session.submit(previous, action), 'duplicate applied'
      until(
          lambda: any(
              h['attempt'] == action
              for h in instance.ledger.get_state()['history']
          )
          or errors
      )
      if args.live and index in (0, 2):
        until(
            lambda: (p := instance.session.snapshot()['pending'])
            and p['id'] != previous
            or errors
        )
        proposal = instance.ledger.public()['proposal']
        assert proposal, 'Natural input must produce a reviewable proposal'
        wanted = ('go', 'cafe') if index == 0 else ('protect', 'iona')
        assert (
            proposal['intent']['verb'],
            proposal['intent']['target'],
        ) == wanted
        assert instance.ledger.public()['turn'] == before_turn
        previous = instance.session.snapshot()['pending']['id']
        assert instance.session.submit(previous, 'confirm')
        assert not instance.session.submit(previous, 'confirm')
        until(
            lambda: instance.ledger.public()['turn'] == before_turn + 1
            or errors
        )
    until(lambda: instance.controller.at_pause_boundary or errors)
    assert not errors, errors
    before = instance.ledger.get_state()
    assert before['turn'] == len(actions), before
    assert all(v > 0 for v in before['npc_turns'].values()), before['npc_turns']
    assert all(
        v > 0 for v in before['agendas'].values()
    ), 'No valid real resident action for some actor: ' + str(before['agendas'])
    cli('ledger.cash', {'value': 27})
    cli('checkpoint.save')
    cli('log.export')
    after = instance.ledger.get_state()
    time.sleep(0.4)
    assert after == instance.ledger.get_state(), 'Paused state changed'
    cli('run.pause_after_action')
    cli('run.resume')
    until(lambda: instance.session.snapshot()['pending'] or errors)
    request = instance.session.snapshot()['pending']
    instance.session.submit(request['id'], 'go narrows')
    until(lambda: instance.controller.at_pause_boundary or errors)
    assert not errors, errors
    assert instance.ledger.public()['cash'] == 27, 'Edited cash lost on resume'
    assert instance.ledger.public()['location'] == 'narrows'
    instance.controller.stop()
    worker.join(20)
    assert not worker.is_alive(), 'Engine did not stop at boundary'
    assert not errors, errors
    evidence = {
        'cli_transcript': cli_transcript,
        'backend': args.model if args.live else 'fixture',
        'actions': actions,
        'pending_pause_edit_rejected': True,
        'pause_after_quiescent': True,
        'resumed_action_preserves_edit': True,
        'duplicate_submission_noop': True,
        'before': before,
        'after': after,
        'completed': instance.completed,
    }
    (args.output / 'evidence.json').write_text(json.dumps(evidence, indent=2))
    print(
        'SMOKE PASS',
        json.dumps(
            {'completed': instance.completed, 'npc_turns': before['npc_turns']}
        ),
    )
  finally:
    instance.controller.stop()
    instance.session.finish('Playtest ended; clean human game untouched.')
    instance.server.stop()
    worker.join(65)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'driver-status.json').write_text(
        json.dumps(
            {
                'errors': errors,
                'thread_alive': worker.is_alive(),
                'cli_transcript': cli_transcript,
            },
            indent=2,
        )
    )


if __name__ == '__main__':
  main()

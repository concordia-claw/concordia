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
import threading
import time

from concordia.examples.rain_ledger import game
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
  args = parser.parse_args()
  if args.live:
    from concordia.contrib.language_models.ollama import ollama_model
    from concordia.language_model import call_limit_wrapper

    model = call_limit_wrapper.CallLimitLanguageModel(
        ollama_model.OllamaLanguageModel(
            'llama3.2:3b',
            request_timeout=60,
            max_output_tokens=180,
            system_message=(
                'Follow the JSON request. Return only the requested object.'
            ),
        ),
        max_calls=40,
    )
  else:
    model = Fixture()
  instance = game.Game(model, args.output)
  errors = []

  def run():
    try:
      instance.play(max_steps=1000)
    except Exception as exc:
      errors.append(repr(exc))

  worker = threading.Thread(target=run)
  worker.start()
  until(lambda: instance.session.snapshot()['pending'] or errors)
  assert not errors, errors
  pending = instance.session.snapshot()['pending']
  instance.controller.pause()
  time.sleep(0.3)
  assert (
      not instance.controller.at_pause_boundary
  ), 'pending human is not quiescent'
  try:
    instance.edit_cash({'value': 999})
    raise AssertionError('Unsafe live edit accepted')
  except ValueError:
    pass
  instance.controller.play()
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
      instance.arm_pause()
    assert instance.session.submit(previous, action)
    assert not instance.session.submit(previous, action), 'duplicate applied'
    until(
        lambda: any(
            h['attempt'] == action
            for h in instance.ledger.get_state()['history']
        )
        or errors
    )
  until(lambda: instance.controller.at_pause_boundary or errors)
  assert not errors, errors
  before = instance.ledger.get_state()
  assert before['turn'] == len(actions), before
  assert all(v > 0 for v in before['npc_turns'].values()), before['npc_turns']
  instance.edit_cash({'value': 27})
  instance.checkpoint()
  after = instance.ledger.get_state()
  time.sleep(0.4)
  assert after == instance.ledger.get_state(), 'Paused state changed'
  instance.controller.stop()
  worker.join(20)
  assert not worker.is_alive(), 'Engine did not stop at boundary'
  assert not errors, errors
  evidence = {
      'backend': 'llama3.2:3b' if args.live else 'fixture',
      'actions': actions,
      'pending_pause_edit_rejected': True,
      'pause_after_quiescent': True,
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


if __name__ == '__main__':
  main()

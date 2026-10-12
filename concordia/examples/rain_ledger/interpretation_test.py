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

"""Fake Together replies exercise interpretation contracts, not model semantics."""

import json
from types import SimpleNamespace
import unittest
from unittest import mock

from concordia.contrib.language_models.together import together_ai_model
from concordia.examples.rain_ledger import content, game, rules
from concordia.language_model import language_model
from concordia.utils import async_measurements


def fake_model(reply):
  client = mock.Mock()
  client.chat.completions.create.return_value = SimpleNamespace(
      choices=[SimpleNamespace(message=SimpleNamespace(content=reply))]
  )
  return (
      together_ai_model.Base(
          'deepseek-ai/DeepSeek-V4.1-Flash', api_key='fixture', client=client
      ),
      client,
  )


class InterpretationContractTest(unittest.TestCase):

  def test_natural_variants_keep_original_text_and_require_review(self):
    # Provider replies are fixtures, deliberately NOT a semantic accuracy score.
    for attempt, reply, place, expected in (
        ('Go to the cafe', '"go cafe"', 'office', 'go'),
        (
            'Head over to the Lantern for a coffee.',
            '{"choice":"go cafe"}',
            'office',
            'go',
        ),
        (
            'Could I ask Ada what happened to her sister?',
            'talk ada',
            'cafe',
            'talk',
        ),
        (
            'I will not take the missing-person case.',
            'refuse case',
            'office',
            'refuse',
        ),
        ('Do not move; just look around.', 'look', 'office', 'look'),
        (
            'Visit Ada, burn the records, then sell the evidence.',
            'unclear',
            'office',
            'unclear',
        ),
    ):
      with self.subTest(attempt=attempt):
        ledger = rules.Ledger()
        ledger.state['location'] = place
        model, client = fake_model(reply)
        intent = rules.parse_intent(attempt, model, ledger)
        self.assertEqual(intent['verb'], expected)
        self.assertTrue(intent['_needs_confirmation'])
        self.assertIn(
            attempt,
            client.chat.completions.create.call_args.kwargs['messages'][-1][
                'content'
            ],
        )
        ledger.resolve(intent, attempt)
        self.assertEqual(ledger.public()['turn'], 0)
        self.assertEqual(ledger.public()['cash'], 18)
        self.assertEqual(ledger.public()['location'], place)
        self.assertEqual(
            bool(ledger.public()['proposal']), expected != 'unclear'
        )
        ledger.resolve({'verb': 'cancel'}, 'cancel')
        ledger.resolve({'verb': 'confirm'}, 'confirm')
        self.assertEqual(ledger.public()['turn'], 0)

  def test_exact_command_never_calls_provider(self):
    model = mock.Mock()
    ledger = rules.Ledger()
    intent = rules.parse_intent('go cafe', model, ledger)
    model.sample_choice.assert_not_called()
    self.assertNotIn('_needs_confirmation', intent)

  def test_retry_after_failure_requires_fresh_review_and_commits_once(self):
    ledger = rules.Ledger()
    session = game.RainSession(ledger)
    model, client = fake_model('"go cafe"')
    client.chat.completions.create.side_effect = [
        ValueError('fixture unavailable'),
        client.chat.completions.create.return_value,
    ]
    authority = game.PortAuthority(ledger, model, session)
    entity = mock.Mock()
    entity.get_capture_key_for_thread.return_value = content.PLAYER
    authority.set_entity(entity)

    def submit(attempt):
      ledger.pending[content.PLAYER] = attempt
      return authority._resolve({}, None)

    with self.assertLogs(level='WARNING'):
      submit('Go to the cafe')
    self.assertIsNone(ledger.public()['proposal'])
    submit('Head over to the Lantern for a coffee.')
    self.assertEqual(ledger.public()['location'], 'office')
    self.assertEqual(ledger.public()['turn'], 0)
    self.assertEqual(ledger.public()['proposal']['intent']['target'], 'cafe')
    submit('confirm')
    self.assertEqual(ledger.public()['location'], 'cafe')
    self.assertEqual(ledger.public()['turn'], 1)
    self.assertEqual(ledger.public()['cash'], 18)
    submit('confirm')
    self.assertEqual(ledger.public()['turn'], 1)
    self.assertEqual(client.chat.completions.create.call_count, 2)

  def test_failure_is_single_sanitized_durable_event(self):
    for error, category in (
        (
            language_model.InvalidResponseError(
                'Together HTTP 401: DUMMY_SECRET'
            ),
            'provider_authentication',
        ),
        (
            language_model.InvalidResponseError(
                'Together transport/protocol: DUMMY_SECRET'
            ),
            'provider_transport',
        ),
        (
            language_model.InvalidResponseError(
                'Together returned no valid choice after 3 attempts.'
            ),
            'choice_contract',
        ),
        (ValueError('DUMMY_SECRET provider body'), 'interpretation_exception'),
    ):
      with self.subTest(category=category):
        ledger = rules.Ledger()
        ledger.resolve(
            dict(
                verb='go',
                target='records',
                method='careful',
                _needs_confirmation=True,
                _model_response='go records',
            ),
            'old draft',
        )
        session = game.RainSession(ledger)
        model = mock.Mock()
        model.sample_choice.side_effect = error
        authority = game.PortAuthority(ledger, model, session)
        entity = mock.Mock()
        entity.get_capture_key_for_thread.return_value = content.PLAYER
        authority.set_entity(entity)
        measurements = async_measurements.ReactiveMeasurements()
        authority.set_logging_channel(
            lambda datum: measurements.publish_datum(
                '__act__', datum, capture_key=content.PLAYER
            )
        )
        ledger.pending[content.PLAYER] = 'Go to the cafe'
        count = len(session.snapshot()['entries'])
        with self.assertLogs(level='WARNING') as stderr:
          with measurements.capture(content.PLAYER) as captured:
            authority._resolve({}, None)
        self.assertEqual(len(session.snapshot()['entries']), count + 1)
        response = session.snapshot()['entries'][-1]['text']
        self.assertIn('Interpretation is unavailable', response)
        self.assertNotIn('intent is unclear', response)
        self.assertEqual(
            captured['__act__']['interpretation_failure'], category
        )
        restored = rules.Ledger()
        restored.set_state(json.loads(json.dumps(ledger.get_state())))
        self.assertEqual(
            restored.public()['history'][-1]['interpretation_failure'], category
        )
        self.assertNotIn(
            'DUMMY_SECRET', json.dumps(captured) + str(stderr.output)
        )
        self.assertEqual(restored.public()['cash'], 18)
        self.assertEqual(restored.public()['turn'], 0)
        self.assertEqual(restored.public()['location'], 'office')
        self.assertIsNone(restored.public()['proposal'])

  def test_ambiguous_fake_provider_reply_fails_without_proposal(self):
    model, client = fake_model('Do not go cafe; go records instead')
    ledger = rules.Ledger()
    with self.assertRaises(language_model.InvalidResponseError):
      rules.parse_intent('Go to the cafe', model, ledger)
    self.assertEqual(client.chat.completions.create.call_count, 3)
    self.assertIsNone(ledger.public()['proposal'])


if __name__ == '__main__':
  unittest.main()

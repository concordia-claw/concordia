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

"""Rule contract checks only: no engines, servers or language models run here."""

import unittest
from concordia.examples.rain_ledger import game, rules
from concordia.typing import entity as entity_lib
from concordia.language_model import no_language_model
from unittest import mock


def act(ledger, command):
  words = command.split()
  return ledger.resolve(
      {
          'verb': words[0],
          'target': words[1] if len(words) > 1 else '',
          'method': words[2] if len(words) > 2 else 'careful',
      },
      command,
  )


class ConsequencesTest(unittest.TestCase):

  def test_initial_player_view_does_not_reveal_missing_bookkeeper(self):
    session = game.RainSession(rules.Ledger())
    view = session.snapshot()
    self.assertNotIn('iona', view['contacts'])
    self.assertNotIn('signed one', str(view))
    self.assertNotIn('patient', view['jobs']['photograph']['description'])
    self.assertNotIn('concealed dangerous', str(view['contacts']))
    self.assertNotIn('sick husband', str(view['contacts']))

  def test_unlocated_clue_not_guessed_into_inventory(self):
    ledger = rules.Ledger()
    for action in ('go docks', 'go warehouse', 'investigate ledger stealth'):
      act(ledger, action)
    self.assertNotIn('ledger', ledger.public()['evidence'])

  def test_public_documents_do_not_expose_uninvolved_witness(self):
    ledger = rules.Ledger()
    for action in (
        'go records',
        'investigate permit',
        'go office',
        'go docks',
        'job tools',
        'job tools bargain',
        'investigate manifest',
        'go press',
        'publish named',
    ):
      act(ledger, action)
    s = ledger.public()
    self.assertTrue(s['stayed'])
    self.assertFalse(s['source_exposed'])
    self.assertGreaterEqual(s['trust']['ada'], 0)

  def test_public_stay_survives_private_payment(self):
    ledger = rules.Ledger()
    for action in (
        'go records',
        'investigate permit',
        'go office',
        'go docks',
        'job tools',
        'job tools bargain',
        'investigate manifest',
        'go press',
        'publish redacted',
        'go mutual',
        'settle self',
        'settle self',
    ):
      act(ledger, action)
    self.assertTrue(ledger.public()['stayed'])
    self.assertIn('stayed', ledger.public()['neighbourhood'])
    self.assertEqual(ledger.public()['settlement'], 'self')

  def test_named_source_breaks_access_and_repair_is_earned(self):
    ledger = rules.Ledger()
    for action in (
        'go cafe',
        'promise ada',
        'talk ada',
        'investigate testimony',
        'protect iona',
        'go narrows',
        'go warehouse',
        'investigate ledger',
        'go docks',
        'go office',
        'go records',
        'investigate permit',
        'go mutual',
        'go press',
        'publish named',
        'go docks',
        'go office',
        'go cafe',
    ):
      act(ledger, action)
    self.assertIn('untouched', act(ledger, 'talk ada'))
    self.assertIn('Repair needs', act(ledger, 'apologize ada'))
    for action in ('go narrows', 'help families', 'go cafe', 'apologize ada'):
      act(ledger, action)
    self.assertEqual(ledger.public()['trust']['ada'], 0)
    self.assertIn('broken promise to Ada', ledger.public()['debts'])

  def test_injury_and_heat_block_dangerous_method_without_spending_turn(self):
    ledger = rules.Ledger()
    state = ledger.get_state()
    state.update(injury=2, heat=4)
    ledger.set_state(state)
    self.assertIn('Recover', act(ledger, 'investigate permit force'))
    self.assertIn('Watchmen', act(ledger, 'investigate permit stealth'))
    self.assertEqual(ledger.public()['turn'], 0)


class ResidentPolicyTest(unittest.TestCase):

  def test_completed_resident_work_is_not_offered_as_new_progress(self):
    ledger = rules.Ledger()
    for _ in range(3):
      act(ledger, 'wait')
      ledger.npc_resolve('Nessa Rook', 'organise', '')
    self.assertEqual(ledger.resident_moves('Nessa Rook'), ['shelter'])
    self.assertEqual(ledger.resident_moves('Silas Marr'), ['petition'])
    ledger.npc_resolve('Edwin Holt', 'offer', '')
    self.assertNotIn('offer', ledger.resident_moves('Edwin Holt'))

  def test_move_choice_changes_mechanical_opportunity(self):
    sheltered = rules.Ledger()
    organised = rules.Ledger()
    for ledger in (sheltered, organised):
      act(ledger, 'wait')
    sheltered.npc_resolve(
        'Nessa Rook', 'shelter', 'Private thought: hidden probe'
    )
    organised.npc_resolve('Nessa Rook', 'organise', 'Organise')
    self.assertEqual(sheltered.public()['shelter_beds'], 2)
    self.assertEqual(organised.public()['petition'], 1)
    self.assertNotEqual(sheltered.public(), organised.public())
    self.assertNotIn('hidden probe', str(sheltered.public()))
    before = sheltered.get_state()
    sheltered.npc_resolve('Nessa Rook', 'shelter', 'No new opportunity')
    self.assertEqual(sheltered.get_state(), before)

  def test_npc_private_proposals_and_remote_actions_are_not_observations(self):
    ledger = rules.Ledger()
    act(ledger, 'go records')
    act(ledger, 'investigate permit')
    self.assertFalse(ledger.get_state()['witnessed']['Edwin Holt'])
    act(ledger, 'go mutual')
    self.assertTrue(ledger.get_state()['witnessed']['Edwin Holt'])
    self.assertNotIn('witnessed', ledger.public())

  def test_medicine_is_not_paid_until_physical_delivery(self):
    ledger = rules.Ledger()
    for command in ('go cafe', 'go clinic', 'job medicine'):
      act(ledger, command)
    self.assertEqual(ledger.public()['cash'], 18)
    self.assertIn('cold medicine', ledger.public()['inventory'])
    act(ledger, 'deliver medicine')
    self.assertEqual(ledger.public()['cash'], 18)
    act(ledger, 'go narrows')
    act(ledger, 'deliver medicine')
    self.assertEqual(ledger.public()['cash'], 27)
    self.assertNotIn('cold medicine', ledger.public()['inventory'])

  def test_public_invitation_does_not_make_copy_collateral_redundant(self):
    ledger = rules.Ledger()
    act(ledger, 'go records')
    act(ledger, 'investigate permit')
    ledger.npc_resolve('Edwin Holt', 'offer', '')
    act(ledger, 'go mutual')
    self.assertIn('two pieces', act(ledger, 'settle families'))
    for command in (
        'go records',
        'go office',
        'copy permit',
        'go records',
        'go mutual',
        'barter holt',
        'settle families',
    ):
      act(ledger, command)
    self.assertTrue(ledger.public()['relocation'])
    self.assertEqual(len(ledger.public()['evidence']), 1)

  def test_copy_is_leverage_not_independent_source(self):
    ledger = rules.Ledger()
    for command in (
        'go records',
        'investigate permit',
        'go office',
        'copy permit',
        'go records',
        'go mutual',
        'barter holt',
        'settle families',
    ):
      act(ledger, command)
    self.assertTrue(ledger.public()['relocation'])
    self.assertEqual(len(ledger.public()['evidence']), 1)
    act(ledger, 'go press')
    self.assertIn('Two independent sources', act(ledger, 'publish named'))


class RecoveryTest(unittest.TestCase):

  def test_confidentiality_terms_precede_acceptance_and_breach_is_repayable(
      self,
  ):
    ledger = rules.Ledger()
    for command in (
        'go records',
        'investigate permit',
        'go mutual',
        'talk holt',
        'investigate carbon bargain',
    ):
      act(ledger, command)
    cash = ledger.public()['cash']
    self.assertIn('terms in writing', act(ledger, 'settle self'))
    self.assertEqual(ledger.public()['cash'], cash)
    act(ledger, 'settle self')
    act(ledger, 'go press')
    act(ledger, 'publish named')
    self.assertIn(
        'Mutual repayment: $35 after confidentiality breach',
        ledger.public()['debts'],
    )
    act(ledger, 'go mutual')
    self.assertIn('release', act(ledger, 'repay mutual'))
    self.assertTrue(ledger.public()['stayed'])
    self.assertFalse(ledger.public()['debts'])

  def test_declining_job_does_not_decline_main_case(self):
    ledger = rules.Ledger()
    for command in (
        'go records',
        'go mutual',
        'job photograph',
        'refuse photograph',
    ):
      act(ledger, command)
    self.assertEqual(ledger.public()['case'], 'unaccepted')
    self.assertEqual(ledger.public()['jobs']['photograph'], 'complete:declined')
    self.assertFalse(ledger.public()['photo_exposed'])

  def test_provider_failure_has_no_invented_npc_action(self):
    class Unavailable:

      def sample_choice(self, *args, **kwargs):
        raise ConnectionError('local daemon unavailable')

    ledger = rules.Ledger()
    session = game.RainSession(ledger)
    policy = game.ResidentAct(Unavailable(), 'Nessa Rook', session)
    policy.get_entity = mock.Mock(return_value=mock.Mock(name='Nessa Rook'))
    policy.get_entity.return_value.name = 'Nessa Rook'
    spec = entity_lib.choice_action_spec(
        call_to_action='Choose for {name}.',
        options=('organise', 'shelter', 'wait'),
    )
    self.assertEqual('wait', policy.get_action_attempt({}, spec))
    self.assertEqual(ledger.public()['shelter_beds'], 0)
    self.assertIn(
        'no resident consequence', session.snapshot()['entries'][-1]['text']
    )


class ProposalTest(unittest.TestCase):

  def test_short_ordinary_phrases_are_not_mistaken_for_exact_confirmation(self):
    ledger = rules.Ledger()
    model = no_language_model.NoLanguageModel()
    for phrase in ('confirm nothing', 'talk to Ada', 'rest a while'):
      intent = rules.parse_intent(phrase, model, ledger)
      self.assertTrue(intent['_needs_confirmation'])
      self.assertNotEqual(intent['verb'], 'confirm')
    self.assertEqual(
        rules.parse_intent('confirm', model, ledger)['verb'], 'confirm'
    )

  def test_wrong_natural_proposal_is_cancelled_without_action(self):
    ledger = rules.Ledger()
    intent = {
        'verb': 'go',
        'target': 'cafe',
        'method': 'careful',
        '_needs_confirmation': True,
        '_model_response': 'go cafe — travel to cafe',
    }
    ledger.resolve(intent, 'I need to rest')
    self.assertEqual(ledger.public()['location'], 'office')
    self.assertEqual(ledger.public()['turn'], 0)
    self.assertIn('confirm', ledger.available())
    self.assertEqual(ledger.public()['proposal']['attempt'], 'I need to rest')
    act(ledger, 'cancel')
    self.assertIsNone(ledger.public()['proposal'])
    self.assertEqual(ledger.public()['turn'], 0)
    act(ledger, 'rest')
    self.assertEqual(ledger.public()['location'], 'office')
    self.assertEqual(ledger.public()['turn'], 1)

  def test_confirmation_is_one_shot_and_survives_scenario_restore(self):
    ledger = rules.Ledger()
    ledger.resolve(
        {
            'verb': 'go',
            'target': 'records',
            'method': 'careful',
            '_needs_confirmation': True,
            '_model_response': 'go records — travel to records',
        },
        'Visit the records office',
    )
    restored = rules.Ledger()
    restored.set_state(ledger.get_state())
    act(restored, 'confirm')
    self.assertEqual(restored.public()['location'], 'records')
    self.assertEqual(restored.public()['turn'], 1)
    act(restored, 'confirm')
    self.assertEqual(restored.public()['turn'], 1)


class IntentScopeTest(unittest.TestCase):

  def test_options_do_not_offer_unlocated_evidence_or_remote_people(self):
    ledger = rules.Ledger()
    labels = ' '.join(rules.intent_options(ledger))
    self.assertNotIn('ledger', labels)
    self.assertNotIn('talk iona', labels)
    self.assertNotIn('publish', labels)
    self.assertIn('refuse case', labels)
    act(ledger, 'go records')
    labels = ' '.join(rules.intent_options(ledger))
    self.assertIn('investigate permit', labels)
    self.assertNotIn('investigate carbon', labels)

  def test_owned_document_copy_is_grounded_at_office(self):
    ledger = rules.Ledger()
    act(ledger, 'go records')
    act(ledger, 'investigate permit')
    act(ledger, 'go office')
    options = rules.intent_options(ledger)
    copy_options = [v for v in options.values() if v['verb'] == 'copy']
    self.assertEqual(
        copy_options,
        [{'verb': 'copy', 'target': 'permit', 'method': 'careful'}],
    )


class ConfessionTest(unittest.TestCase):

  def setUp(self):
    self.ledger = rules.Ledger()
    for command in (
        'go cafe',
        'promise ada',
        'protect iona',
        'go narrows',
        'go warehouse',
        'investigate ledger',
        'talk iona',
    ):
      act(self.ledger, command)

  def test_costly_consent_and_independent_corroboration(self):
    ledger = self.ledger
    self.assertTrue(ledger.public()['iona_confessed'])
    self.assertIn('refuses', act(ledger, 'testify iona'))
    for command in ('go narrows', 'go clinic', 'restitution iona'):
      act(ledger, command)
    self.assertEqual(ledger.public()['cash'], 3)
    act(ledger, 'restitution iona')
    self.assertEqual(ledger.public()['cash'], 3)
    for command in (
        'go narrows',
        'go warehouse',
        'testify iona',
        'go narrows',
        'go cafe',
        'tell ada',
        'go office',
        'go records',
        'investigate permit',
        'go mutual',
        'go press',
        'publish named',
    ):
      act(ledger, command)
    self.assertTrue(ledger.public()['stayed'])
    self.assertNotIn('broken promise to Ada', ledger.public()['debts'])
    for command in ('go docks', 'go warehouse'):
      act(ledger, command)
    self.assertIn('answer for my signature', act(ledger, 'talk iona'))

  def test_threat_invalidates_consent_without_erasing_other_routes(self):
    ledger = self.ledger
    for command in (
        'go narrows',
        'go clinic',
        'restitution iona',
        'go narrows',
        'go warehouse',
        'testify iona',
    ):
      act(ledger, command)
    self.assertIn('affidavit', ledger.public()['evidence'])
    act(ledger, 'threaten iona')
    self.assertNotIn('affidavit', ledger.public()['evidence'])
    self.assertIn('will not sign', act(ledger, 'testify iona'))
    self.assertIn('ledger', ledger.public()['evidence'])


if __name__ == '__main__':
  unittest.main()

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
from concordia.examples.rain_ledger import content, game, rules
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

  def test_betrayed_witness_and_coerced_authentication_do_not_bypass_access(
      self,
  ):
    ledger = rules.Ledger()
    ledger.state.update(location='cafe', known_leads=['testimony'])
    ledger.state['trust']['ada'] = -1
    before = ledger.public()
    self.assertIn('unrepaired', act(ledger, 'investigate testimony'))
    self.assertNotIn('testimony', ledger.public()['evidence'])
    self.assertEqual(ledger.public()['turn'], before['turn'])
    ledger.state.update(location='warehouse', known_leads=['ledger'])
    act(ledger, 'investigate ledger force')
    act(ledger, 'talk iona')
    act(ledger, 'threaten iona')
    ledger.state['protected'] = True
    before = ledger.public()
    act(ledger, 'authenticate ledger')
    self.assertFalse(ledger.public()['evidence']['ledger']['authenticated'])
    self.assertEqual(ledger.public()['turn'], before['turn'])

  def test_unsupported_evidence_method_cannot_bypass_access(self):
    ledger = rules.Ledger()
    for action in ('go docks', 'talk silas'):
      act(ledger, action)
    before = ledger.public()
    response = act(ledger, 'investigate manifest bargain')
    self.assertIn('does not grant access', response)
    self.assertEqual(ledger.public()['cash'], before['cash'])
    self.assertEqual(ledger.public()['turn'], before['turn'])
    self.assertNotIn('manifest', ledger.public()['evidence'])
    act(ledger, 'investigate manifest pay')
    self.assertEqual(ledger.public()['evidence']['manifest']['credibility'], 2)

  def test_covert_carbon_needs_proof_then_can_be_authenticated_without_rewriting_history(
      self,
  ):
    ledger = rules.Ledger()
    for action in (
        'go records',
        'investigate permit',
        'go mutual',
        'talk holt',
        'investigate carbon stealth',
        'go press',
    ):
      act(ledger, action)
    self.assertEqual(ledger.public()['evidence']['carbon']['credibility'], 1)
    self.assertIn('Two independent sources', act(ledger, 'publish records'))
    self.assertFalse(ledger.public()['published'])
    restored = rules.Ledger()
    restored.set_state(ledger.get_state())
    act(restored, 'go mutual')
    self.assertIn('authenticate carbon', restored.available())
    heat = restored.public()['heat']
    act(restored, 'authenticate carbon bargain')
    evidence = restored.public()['evidence']['carbon']
    self.assertEqual(evidence['credibility'], 2)
    self.assertTrue(evidence['authenticated'])
    self.assertIn('covertly', evidence['acquisition'])
    self.assertEqual(restored.public()['heat'], heat)
    before = restored.public()
    act(restored, 'authenticate carbon bargain')
    self.assertEqual(restored.public()['turn'], before['turn'])
    act(restored, 'go press')
    act(restored, 'publish records')
    self.assertTrue(restored.public()['stayed'])

  def test_covert_tally_certification_cost_and_collateral_are_real(self):
    ledger = rules.Ledger()
    for action in ('go docks', 'talk silas', 'investigate manifest stealth'):
      act(ledger, action)
    before = ledger.public()
    act(ledger, 'authenticate manifest')
    self.assertEqual(ledger.public()['turn'], before['turn'])
    act(ledger, 'go office')
    act(ledger, 'copy manifest')
    act(ledger, 'go records')
    act(ledger, 'go mutual')
    self.assertIn('credible collateral', act(ledger, 'barter holt'))
    self.assertNotIn(
        'secured copy pledged for Mutual relocation audit',
        ledger.public()['promises'],
    )
    ledger.state['location'] = 'docks'
    before = ledger.public()
    act(ledger, 'authenticate manifest pay')
    self.assertEqual(ledger.public()['cash'], before['cash'] - 4)
    self.assertEqual(ledger.public()['evidence']['manifest']['credibility'], 2)
    self.assertEqual(ledger.public()['copies'], ['manifest'])

  def test_betrayal_is_not_cancelled_by_goodwill_or_prior_private_conversation(
      self,
  ):
    ledger = rules.Ledger()
    ledger.state.update(location='press', ada_informed=True)
    ledger.state['trust']['ada'] = 7
    ledger.state['promises'] = ['protect Iona’s name']
    ledger.state['evidence'] = {
        key: dict(content.EVIDENCE[key]) for key in ('permit', 'ledger')
    }
    act(ledger, 'publish named')
    self.assertLess(ledger.public()['trust']['ada'], 0)
    ledger.state['location'] = 'cafe'
    self.assertIn('cup untouched', act(ledger, 'talk ada'))
    act(ledger, 'apologize ada')
    self.assertLess(ledger.public()['trust']['ada'], 0)
    ledger.state['location'] = 'narrows'
    act(ledger, 'help families')
    ledger.state['location'] = 'cafe'
    act(ledger, 'apologize ada')
    self.assertEqual(ledger.public()['trust']['ada'], 0)
    self.assertIn('broken promise to Ada', ledger.public()['debts'])
    self.assertTrue(ledger.public()['source_exposed'])

  def test_followup_adds_proof_without_repeat_reward_or_erasing_disclosure(
      self,
  ):
    ledger = rules.Ledger()
    ledger.state['location'] = 'press'
    ledger.state['evidence'] = {
        key: dict(content.EVIDENCE[key]) for key in ('permit', 'manifest')
    }
    act(ledger, 'publish records')
    trust = ledger.public()['trust']['ada']
    before = ledger.public()
    self.assertIn('No new evidence', act(ledger, 'publish records'))
    self.assertEqual(ledger.public()['turn'], before['turn'])
    ledger.state['evidence']['ledger'] = dict(content.EVIDENCE['ledger'])
    self.assertIn('Follow-up story', act(ledger, 'publish named'))
    self.assertTrue(ledger.public()['source_exposed'])
    self.assertEqual(ledger.public()['trust']['ada'], trust - 3)
    ledger.state['evidence']['carbon'] = dict(content.EVIDENCE['carbon'])
    restored = rules.Ledger()
    restored.set_state(ledger.get_state())
    exposed_trust = restored.public()['trust']['ada']
    self.assertIn('cannot undo that disclosure', act(restored, 'talk vera'))
    act(restored, 'publish records')
    self.assertEqual(
        set(restored.public()['published']),
        {'permit', 'manifest', 'ledger', 'carbon'},
    )
    self.assertTrue(restored.public()['source_exposed'])
    self.assertEqual(restored.public()['trust']['ada'], exposed_trust)
    self.assertTrue(restored.public()['stayed'])

  def test_redacted_followup_expands_finding_without_exposure(self):
    ledger = rules.Ledger()
    ledger.state['location'] = 'press'
    ledger.state['evidence'] = {
        key: dict(content.EVIDENCE[key]) for key in ('permit', 'manifest')
    }
    act(ledger, 'publish records')
    trust = ledger.public()['trust']['ada']
    ledger.state['evidence']['ledger'] = dict(content.EVIDENCE['ledger'])
    act(ledger, 'publish redacted')
    self.assertIn('inflated premiums', ledger.public()['news'][-1])
    self.assertFalse(ledger.public()['source_exposed'])
    self.assertEqual(ledger.public()['trust']['ada'], trust)

  def test_record_dossier_withholds_owned_witness_material_after_restore(self):
    ledger = rules.Ledger()
    for action in (
        'go cafe',
        'promise ada',
        'talk ada',
        'investigate testimony',
        'go office',
        'go records',
        'investigate permit',
        'go office',
        'go docks',
        'talk silas',
        'investigate manifest pay',
        'go press',
    ):
      act(ledger, action)
    restored = rules.Ledger()
    restored.set_state(ledger.get_state())
    before = restored.public()
    review = act(restored, 'talk vera')
    self.assertIn('keep private testimony', review)
    self.assertIn('Names the Saye source', review)
    for key in ('cash', 'turn', 'published', 'evidence', 'promises'):
      self.assertEqual(restored.public()[key], before[key])
    self.assertIn('publish records', restored.available())
    exact = rules.parse_intent('publish records', mock.Mock(), restored)
    self.assertEqual(exact['target'], 'records')
    restored.resolve(exact)
    state = restored.public()
    self.assertEqual(state['published'], ['permit', 'manifest'])
    self.assertIn(
        'demolition planning before the safety findings', state['news'][-1]
    )
    self.assertNotIn('inflated premiums', state['news'][-1])
    self.assertIn('testimony', state['evidence'])
    self.assertIn('protect Iona’s name', state['promises'])
    self.assertFalse(state['source_exposed'])
    self.assertTrue(state['stayed'])
    self.assertIn(
        'Already disclosed: permit, manifest', act(restored, 'talk vera')
    )
    for action in ('go docks', 'go office', 'go cafe'):
      act(restored, action)
    response = act(restored, 'talk ada')
    self.assertIn('stopped bulldozer', response)
    self.assertNotIn('Start at Records', response)
    self.assertIn('ledger', restored.public()['known_leads'])

  def test_withheld_evidence_cannot_subsidize_an_insufficient_dossier(self):
    ledger = rules.Ledger()
    ledger.state['location'] = 'press'
    ledger.state['evidence'] = {
        key: dict(content.EVIDENCE[key]) for key in ('permit', 'ledger')
    }
    before = ledger.public()
    response = act(ledger, 'publish records')
    self.assertIn('Withheld material cannot silently fill the gap', response)
    self.assertEqual(ledger.public()['turn'], before['turn'])
    self.assertFalse(ledger.public()['published'])
    self.assertIn('third independent', act(ledger, 'publish redacted'))
    act(ledger, 'publish named')
    self.assertEqual(ledger.public()['published'], ['permit', 'ledger'])
    self.assertTrue(ledger.public()['source_exposed'])

  def test_records_only_still_breaches_paid_confidentiality(self):
    ledger = rules.Ledger()
    ledger.state['location'] = 'press'
    ledger.state['promises'] = ['Mutual confidentiality clause']
    ledger.state['evidence'] = {
        key: dict(content.EVIDENCE[key]) for key in ('permit', 'manifest')
    }
    self.assertIn('$35 repayment and two legal heat', act(ledger, 'talk vera'))
    act(ledger, 'publish records')
    self.assertIn(
        'Mutual repayment: $35 after confidentiality breach',
        ledger.public()['debts'],
    )
    self.assertEqual(ledger.public()['heat'], 2)
    self.assertFalse(ledger.public()['source_exposed'])

  def test_treatment_credit_can_be_deferred_then_worked_off_once(self):
    ledger = rules.Ledger()
    ledger.state.update(location='clinic', cash=0, injury=2)
    response = act(ledger, 'rest')
    self.assertIn('repay pell', response)
    self.assertIn('repay pell', ledger.available())
    self.assertIn('treatment credit', ledger.public()['debts'])
    act(ledger, 'help pell')  # Earning money need not automatically repay debt.
    self.assertEqual(ledger.public()['cash'], 6)
    self.assertIn('treatment credit', ledger.public()['debts'])
    saved = ledger.get_state()
    restored = rules.Ledger()
    restored.set_state(saved)
    restored.state['photo_exposed'] = True
    act(restored, 'repay pell')
    self.assertEqual(restored.public()['cash'], 6)
    self.assertNotIn('treatment credit', restored.public()['debts'])
    self.assertTrue(restored.public()['photo_exposed'])
    turn = restored.public()['turn']
    act(restored, 'repay pell')
    self.assertEqual(restored.public()['turn'], turn)
    self.assertNotIn('repay pell', restored.available())

  def test_deferred_rent_has_reachable_exact_and_natural_affordance(self):
    ledger = rules.Ledger()
    ledger.state.update(cash=5, debts=['office rent'])
    self.assertIn('repay rent', ledger.available())
    intent = rules.parse_intent('repay rent', mock.Mock(), ledger)
    self.assertEqual(intent['target'], 'rent')
    self.assertTrue(
        any(
            i.get('target') == 'rent'
            for i in rules.intent_options(ledger).values()
        )
    )
    ledger.resolve(intent)
    self.assertEqual(ledger.public()['cash'], 2)
    self.assertNotIn('office rent', ledger.public()['debts'])

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

  def test_settlement_needs_corroboration_not_duplicate_witness_accounts(self):
    ledger = rules.Ledger()
    ledger.state['location'] = 'mutual'
    ledger.state['evidence'] = {
        key: dict(content.EVIDENCE[key]) for key in ('testimony', 'ledger')
    }
    self.assertIn('same source', act(ledger, 'settle families accept'))
    self.assertEqual(ledger.public()['settlement'], '')
    self.assertEqual(ledger.public()['turn'], 0)
    ledger.state['evidence']['permit'] = dict(content.EVIDENCE['permit'])
    act(ledger, 'settle families accept')
    self.assertTrue(ledger.public()['relocation'])

  def test_covert_bargain_needs_authentication_or_more_corroboration(self):
    ledger = rules.Ledger()
    for command in (
        'go records',
        'investigate permit',
        'go mutual',
        'talk holt',
        'investigate carbon stealth',
    ):
      act(ledger, command)
    before = ledger.public()
    self.assertIn('Authenticate', act(ledger, 'settle families accept'))
    self.assertEqual(ledger.public()['turn'], before['turn'])
    act(ledger, 'authenticate carbon bargain')
    self.assertIn('Written terms', act(ledger, 'settle families'))
    self.assertEqual(ledger.public()['settlement'], '')
    act(ledger, 'settle families accept')
    self.assertTrue(ledger.public()['relocation'])

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
        'settle families accept',
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
        'settle families accept',
    ):
      act(ledger, command)
    self.assertTrue(ledger.public()['relocation'])
    self.assertEqual(len(ledger.public()['evidence']), 1)
    act(ledger, 'go press')
    self.assertIn('Two independent sources', act(ledger, 'publish named'))


class ReliefAgreementTest(unittest.TestCase):

  def test_player_can_organise_after_refusing_case_without_cash_or_npc_wait(
      self,
  ):
    ledger = rules.Ledger()
    for command in ('refuse case', 'go cafe', 'go clinic', 'go narrows'):
      act(ledger, command)
    ledger.state['cash'] = 0
    self.assertIn('organise families', ledger.available())
    for _ in range(2):
      act(ledger, 'organise families')
    self.assertEqual(ledger.public()['petition'], 2)
    self.assertEqual(ledger.public()['case'], 'declined')
    self.assertEqual(ledger.public()['cash'], 0)
    ledger.npc_resolve('Nessa Rook', 'organise', '')
    before = ledger.public()
    self.assertIn('All three', act(ledger, 'organise families'))
    self.assertEqual(ledger.public()['turn'], before['turn'])
    self.assertNotIn('organise families', ledger.available())
    self.assertNotIn('organise', ledger.resident_moves('Nessa Rook'))
    self.assertEqual(ledger.public()['petition'], 3)

  def test_organising_requires_volunteers_and_correct_location(self):
    ledger = rules.Ledger()
    self.assertIn('Narrows', act(ledger, 'organise families'))
    ledger.state['location'] = 'narrows'
    self.assertIn('volunteer', act(ledger, 'organise families force'))
    self.assertEqual(ledger.public()['petition'], 0)
    self.assertEqual(ledger.public()['turn'], 0)

  def ready(self):
    ledger = rules.Ledger()
    for command in (
        'go records',
        'investigate permit',
        'go mutual',
        'talk holt',
        'investigate carbon bargain',
        'go press',
        'publish records',
    ):
      act(ledger, command)
    ledger.npc_resolve('Nessa Rook', 'organise', '')
    act(ledger, 'go mutual')
    ledger.npc_resolve('Nessa Rook', 'organise', '')
    return ledger

  def test_representatives_and_stay_required_not_player_cash(self):
    ledger = rules.Ledger()
    ledger.state['location'] = 'mutual'
    self.assertIn('public stay', act(ledger, 'settle relief accept'))
    ledger.state['stayed'] = True
    self.assertIn('representatives', act(ledger, 'settle relief accept'))
    self.assertEqual(ledger.public()['settlement'], '')
    self.assertEqual(ledger.public()['turn'], 0)

  def test_review_then_relief_preserves_claims_and_excludes_relocation(self):
    ledger = self.ready()
    before = ledger.public()
    self.assertIn(
        'relocation bonds will no longer', act(ledger, 'settle relief')
    )
    for key in ('cash', 'turn', 'relief', 'settlement', 'evidence', 'promises'):
      self.assertEqual(ledger.public()[key], before[key])
    options = rules.intent_options(ledger)
    self.assertTrue(any('permanently forgo' in label for label in options))
    act(ledger, 'settle relief accept')
    self.assertEqual(ledger.public()['relief'], 6)
    self.assertFalse(ledger.public()['relocation'])
    self.assertEqual(ledger.public()['evidence'], before['evidence'])
    self.assertEqual(ledger.public()['promises'], before['promises'])
    self.assertTrue(ledger.public()['stayed'])
    restored = rules.Ledger()
    restored.set_state(ledger.get_state())
    after = restored.public()
    self.assertIn('stands', act(restored, 'settle families'))
    self.assertIn('already committed', act(restored, 'settle relief accept'))
    self.assertEqual(restored.public()['relief'], after['relief'])
    self.assertEqual(restored.public()['turn'], after['turn'])
    self.assertIn('tenant-administered', restored.public()['news'][-1])
    act(restored, 'go records')
    act(restored, 'go office')
    act(restored, 'go cafe')
    self.assertIn('Nobody signed away', act(restored, 'talk nessa'))

  def test_review_can_be_refused_for_relocation(self):
    ledger = self.ready()
    act(ledger, 'settle relief')
    self.assertNotIn('settle families accept', ledger.available())
    self.assertIn('six-evening', act(ledger, 'settle families'))
    self.assertIn('settle families accept', ledger.available())
    self.assertEqual(ledger.public()['settlement'], '')
    act(ledger, 'settle families accept')
    self.assertTrue(ledger.public()['relocation'])
    self.assertEqual(ledger.public()['relief'], 0)
    self.assertIn('already committed', act(ledger, 'settle relief accept'))


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

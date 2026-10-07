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


if __name__ == '__main__':
  unittest.main()

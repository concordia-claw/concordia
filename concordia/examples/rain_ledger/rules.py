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

"""Scenario-owned consequences on Concordia's component API.

The ledger is game state, not an engine, transport, memory implementation or log.
All mutations take its lock; engine routing remains standard Asynchronous.
"""

import copy
import threading
from typing import Any

from concordia.typing import entity_component
from concordia.examples.rain_ledger import content as c

VERBS = (
    'confirm',
    'cancel',
    'go',
    'look',
    'talk',
    'investigate',
    'job',
    'rest',
    'promise',
    'protect',
    'publish',
    'settle',
    'refuse',
    'wait',
    'help',
    'threaten',
    'apologize',
    'deliver',
    'copy',
    'barter',
    'repay',
    'restitution',
    'testify',
    'tell',
)
METHODS = ('careful', 'bargain', 'stealth', 'force', 'pay', 'sell', 'warn')


class Ledger(entity_component.ContextComponent):
  """Authoritative finances, evidence provenance, obligations and public aftermath."""

  def __init__(self):
    super().__init__()
    self.lock = threading.RLock()
    self.pending: dict[str, str] = {}
    self.state: dict[str, Any] = {
        'location': 'office',
        'cash': 18,
        'injury': 0,
        'heat': 0,
        'turn': 0,
        'evidence': {},
        'jobs': {},
        'trust': {
            'ada': 0,
            'nessa': 0,
            'silas': 0,
            'holt': 0,
            'vera': 0,
            'pell': 0,
        },
        'promises': [],
        'debts': [],
        'protected': False,
        'case': 'unaccepted',
        'published': [],
        'settlement': '',
        'retainer_terms_seen': False,
        'proposal': None,
        'schema_version': 2,
        'last_intent': None,
        'iona_confessed': False,
        'iona_restitution': False,
        'iona_testimony': 'unasked',
        'ada_informed': False,
        'neighbourhood': 'Notices posted; families still at home.',
        'npc_turns': {name: 0 for name in c.NPCS},
        'agendas': {name: 0 for name in c.NPCS},
        'news': [],
        'history': [],
        'lost_leads': [],
        'known_leads': ['permit'],
        'stayed': False,
        'relocation': False,
        'relief': 0,
        'source_exposed': False,
        'photo_exposed': False,
        'inventory': ['camera', 'lock pick'],
        'copies': [],
        'shelter_beds': 0,
        'petition': 0,
        'union_support': 0,
        'security': 0,
        'bond_offer': False,
        'witnessed': {name: [] for name in c.NPCS},
    }

  def get_state(self):
    with self.lock:
      return copy.deepcopy(self.state)

  def set_state(self, state):
    # Generic restoration passes the serialized component state. Live writes
    # must additionally be guarded by StepController.paused_boundary.
    if (
        not isinstance(state, dict)
        or set(state) != set(self.state)
        or state.get('schema_version') != 2
    ):
      raise ValueError(
          'Restore a complete Rain Ledger schema2 state. Earlier development'
          ' saves remain archived; no implicit migration is performed.'
      )
    state = {**copy.deepcopy(self.state), **copy.deepcopy(state)}
    for key in ('cash', 'injury', 'heat', 'turn'):
      if type(state[key]) is not int or state[key] < 0:
        raise ValueError(f'{key} must be a nonnegative integer')
    if state['location'] not in c.PLACES:
      raise ValueError('Unknown location')
    with self.lock:
      self.state = copy.deepcopy(state)

  def pre_observe(self, observation):
    prefix = '[putative_event] '
    if observation.startswith(prefix):
      actor, separator, attempt = observation[len(prefix) :].partition(': ')
      if separator and actor in (c.PLAYER, *c.NPCS):
        with self.lock:
          self.pending[actor] = attempt
    return ''

  def public(self):
    with self.lock:
      s = copy.deepcopy(self.state)
    s['history'] = [
        entry for entry in s['history'] if entry['actor'] == c.PLAYER
    ]
    for entry in s['history']:
      entry['changes'] = {
          k: v
          for k, v in entry['changes'].items()
          if k not in ('npc_turns', 'agendas', 'witnessed')
      }
    return {
        key: value
        for key, value in s.items()
        if key not in ('npc_turns', 'agendas', 'witnessed')
    }

  def view(self):
    s = self.public()
    place, description, exits = c.PLACES[s['location']]
    clues = (
        '\n'.join(
            f"• {key}: {e['text']} [{e['source']}; credibility"
            f" {e['credibility']}/3]"
            for key, e in s['evidence'].items()
        )
        or 'No evidence collected.'
    )
    contacts = '; '.join(
        value[0]
        for key, value in c.CONTACTS.items()
        if value[1] == s['location']
        and (key != 'iona' or 'ledger' in s['evidence'])
    )
    return (
        f"{place}\n{description}\nExits: {', '.join(exits)}. Here:"
        f" {contacts or 'no familiar faces'}.\nCash ${s['cash']} · injury"
        f" {s['injury']}/3 · heat {s['heat']}/5 · committed actions"
        f" {s['turn']}\nCASEBOOK\n{clues}\nNarrows:"
        f" {s['neighbourhood']}\nObligations:"
        f" {', '.join(s['debts'] + s['promises']) or 'none'}.\n"
        + '\n'.join(s['news'][-3:])
    )

  def available(self):
    s = self.public()
    choices = ['confirm', 'cancel'] if s.get('proposal') else []
    choices += [f'go {place}' for place in c.PLACES[s['location']][2]]
    choices += [
        f'talk {key}'
        for key, value in c.CONTACTS.items()
        if value[1] == s['location']
        and (key != 'iona' or 'ledger' in s['evidence'])
    ]
    choices += [
        f'investigate {key}'
        for key, value in c.EVIDENCE.items()
        if value['place'] == s['location']
        and key not in s['evidence']
        and key in s['known_leads']
    ]
    choices += [
        f'job {key}'
        for key, value in c.JOBS.items()
        if value['place'] == s['location']
        and not s['jobs'].get(key, '').startswith('complete:')
    ]
    if 'cold medicine' in s['inventory'] and s['location'] == 'narrows':
      choices.append('deliver medicine')
    if s['iona_confessed']:
      if s['location'] == 'warehouse' and s['iona_testimony'] == 'unasked':
        choices.append('testify iona')
      if s['location'] == 'clinic' and not s['iona_restitution']:
        choices.append('restitution iona')
      if s['location'] == 'cafe' and not s['ada_informed']:
        choices.append('tell ada')
    if s['location'] == 'press' and s['evidence'] and not s['published']:
      choices.extend(['publish redacted', 'publish named'])
    return choices + ['look', 'rest']

  def _record(self, actor, attempt, result, before, *, visible=False):
    s = self.state
    delta = {
        key: copy.deepcopy(s[key])
        for key in s
        if key != 'history' and s[key] != before.get(key)
    }
    if actor == c.PLAYER and visible:
      for name, person in c.NPCS.items():
        if person['home'] == s['location']:
          s['witnessed'][name].append(result)
    s['history'].append(
        {'actor': actor, 'attempt': attempt, 'result': result, 'changes': delta}
    )
    return result

  def resolve(self, intent, original=''):
    """Apply one validated attempt; impossible actions are free and explicit."""
    with self.lock:
      before = copy.deepcopy(self.state)
      s = self.state
      verb = intent.get('verb')
      if verb == 'cancel':
        s['proposal'] = None
        return self._record(
            c.PLAYER,
            original,
            'Proposal cancelled. Nothing was spent or committed. Write a'
            ' correction or choose another action.',
            before,
        )
      if verb == 'confirm':
        if not s.get('proposal'):
          return self._record(
              c.PLAYER,
              original,
              'There is no proposal waiting for confirmation.',
              before,
          )
        intent = s['proposal']['intent']
        s['proposal'] = None
        verb = intent['verb']
      elif intent.get('_needs_confirmation') and verb in VERBS:
        canonical = {
            key: intent.get(key, '') for key in ('verb', 'target', 'method')
        }
        s['proposal'] = {
            'intent': canonical,
            'attempt': original,
            'description': intent['_model_response'],
        }
        return self._record(
            c.PLAYER,
            original,
            'You mean: '
            + intent['_model_response']
            + '?\nConfirm this proposal, cancel it, or write a correction. No'
            ' time, money or consequences have been committed.',
            before,
        )
      else:
        # A new intention replaces an unconfirmed proposal, never confirms it.
        s['proposal'] = None
      target = intent.get('target', '').lower()
      method = intent.get('method', 'careful')
      s['last_intent'] = {'verb': verb, 'target': target, 'method': method}
      if verb not in VERBS or method not in METHODS:
        return self._record(
            c.PLAYER,
            original or str(intent),
            'That intent is unclear. Name what you want to do and to whom;'
            ' nothing has changed.',
            before,
        )
      if verb == 'look':
        return self.view()
      result, committed = self._apply(verb, target, method)
      if committed:
        s['turn'] += 1
        if s['turn'] % 8 == 0:
          charge = min(s['cash'], 3)
          s['cash'] -= charge
          if charge < 3 and 'office rent' not in s['debts']:
            s['debts'].append('office rent')
          result += (
              f' Evening office upkeep: ${charge}. Unpaid rent becomes an'
              ' obligation, never a game over.'
          )
      if committed and verb == 'publish':
        s['news'].append(
            'The Evening Wire publishes corroborated insurance irregularities.'
            ' Demolition is stayed; claims freeze pending inquiry.'
        )
      if committed and verb == 'settle':
        s['news'].append(
            'Public Mutual filings record '
            + (
                'relocation bonds for Narrows families.'
                if target == 'families'
                else (
                    'a consultancy payment to Rowan Vale; no relocation'
                    ' provision.'
                )
            )
        )
      self._refresh_neighbourhood()
      return self._record(
          c.PLAYER,
          original or str(intent),
          result,
          before,
          visible=verb
          in (
              'go',
              'talk',
              'job',
              'promise',
              'threaten',
              'settle',
              'help',
              'deliver',
          )
          and method != 'stealth',
      )

  def _refresh_neighbourhood(self):
    s = self.state
    parts = [
        'Demolition stayed pending inquiry.'
        if s['stayed']
        else 'Demolition notices remain in force.'
    ]
    if s['relocation']:
      parts.append('Relocation bonds funded; families can leave together.')
    if s['published']:
      parts.append('Claims frozen during inquiry; relief is needed.')
    if s['relief']:
      parts.append(f"Shelter supplied for {s['relief']} evening(s).")
    s['neighbourhood'] = ' '.join(parts)

  def _apply(self, verb, target, method):
    s = self.state
    location = s['location']
    if method == 'force' and s['injury'] >= 2:
      return (
          (
              'Your wrist will not hold. Recover at the clinic or choose a'
              ' nonviolent approach.'
          ),
          False,
      )
    if method == 'stealth' and s['heat'] >= 4:
      return (
          (
              'Watchmen recognise your coat. Let the heat fall, bargain, or'
              ' find a public route.'
          ),
          False,
      )
    if verb == 'go':
      if target not in c.PLACES[location][2]:
        return (
            'That is not an adjacent stop. Exits: '
            + ', '.join(c.PLACES[location][2]),
            False,
        )
      s['location'] = target
      return c.PLACES[target][1], True
    if verb == 'refuse':
      if target in c.JOBS:
        if s['jobs'].get(target) not in ('decision', 'carrying'):
          return 'There is no active offer of that job to decline.', False
        if target == 'medicine' and location != 'clinic':
          return (
              (
                  'Return the cold case to Pell at the clinic before declining'
                  ' the delivery.'
              ),
              False,
          )
        if target == 'medicine':
          s['inventory'].remove('cold medicine')
        s['jobs'][target] = 'complete:declined'
        return (
            (
                'You return the commission without selling anyone out. No fee,'
                ' no penalty; the main case is unchanged.'
            ),
            True,
        )
      if target not in ('case', '', 'ada'):
        return 'Specify the case or an active job you want to decline.', False
      s['case'] = 'declined'
      return (
          (
              'Ada takes back the unopened envelope. “Then earn your living.'
              ' I’ll keep looking.” Her address stays in your casebook; she has'
              ' not become your enemy.'
          ),
          True,
      )
    if verb == 'talk':
      if target == 'nessa' and location == 'cafe' and s['relocation']:
        return (
            (
                'Nessa stacks the moving vouchers under a saucer. “The bonds'
                ' are real. So are the empty windows. I wanted neighbours; now'
                ' I keep forwarding addresses.” Families can leave together,'
                ' but the old street will not follow them.'
            ),
            False,
        )
      if (
          target == 'nessa'
          and location == 'cafe'
          and s['stayed']
          and s['relief']
      ):
        return (
            (
                '“Bread first, hearings second.” Nessa puts a clean cup at your'
                ' place. The favour you paid is recorded; the families still'
                ' need a settlement they can live on.'
            ),
            False,
        )
      if target not in c.CONTACTS or c.CONTACTS[target][1] != location:
        return (
            'They are not here. Check your contacts for their usual address.',
            False,
        )
      if target == 'iona' and 'ledger' in s['evidence']:
        if s['published'] and s['iona_testimony'] == 'voluntary':
          return (
              (
                  'Iona folds the hearing summons along its old crease. “I will'
                  ' have to answer for my signature. At least it will be mine'
                  ' answering.” She asks you to check on Ada, not to make the'
                  ' charge disappear.'
              ),
              False,
          )
        if not s['iona_confessed']:
          s['iona_confessed'] = True
          return (
              (
                  'Iona takes the photograph of her mother from behind the'
                  ' clock face. “I moved twelve tenants on paper. The premium'
                  ' difference bought her care. Creel did the rest, but that'
                  ' line is mine.” She turns the ledger so you can read her'
                  ' signature. “Don’t make me innocent. Make those families'
                  ' whole.” You can fund $12 restitution at the clinic, ask her'
                  ' to testify, pressure her, or build the case from public'
                  ' records without using her.'
              ),
              False,
          )
        return (
            (
                '“A hiding place is not an acquittal.” Iona will offer a signed'
                ' account once the twelve dollars reaches the clinic’s'
                ' displaced families. You may refuse; she will not destroy your'
                ' records.'
            ),
            False,
        )
      if target == 'ada' and s['ada_informed']:
        if s['iona_testimony'] == 'voluntary':
          return (
              (
                  'Ada holds the witness summons flat with both palms. “I asked'
                  ' you to bring her back. I didn’t know which version of her I'
                  ' meant. I’ll go with her.” She still expects the families to'
                  ' be helped.'
              ),
              False,
          )
        return (
            (
                'Ada stares at the clock photograph. “She could have asked me.'
                ' Maybe I made that hard.” She wants Iona safe, but will not'
                ' ask you to erase the signature.'
            ),
            False,
        )
      if target == 'ada' and s['trust']['ada'] < 0:
        return (
            (
                'Ada leaves your cup untouched. “You gave them her name. Bring'
                ' help to the Narrows before you ask me for anything.” An'
                ' apology alone will not buy back trust.'
            ),
            False,
        )
      if target == 'pell' and s['photo_exposed']:
        return (
            (
                'Pell sets your photograph on the desk. “The client printed it.'
                ' I treat everyone, including you. But the paid routes go to'
                ' people my patients can trust. Help repair the harm.”'
            ),
            False,
        )
      leads = {
          'ada': ['testimony', 'ledger'],
          'silas': ['manifest'],
          'holt': ['carbon'],
      }
      s['known_leads'] = list(
          dict.fromkeys(s['known_leads'] + leads.get(target, []))
      )
      lines = {
          'ada': (
              '“She corrects clocks that aren’t hers. Start at Records. Policy'
              ' 4407. And if you find her, don’t sell her name.”'
          ),
          'nessa': (
              '“I have beds for six, notices for forty. Bring me something that'
              ' stops a bulldozer, not a speech.”'
          ),
          'silas': (
              '“Tools in a cage. Men outside it. Fix that and I’ll open the'
              ' tally book.”'
          ),
          'vera': (
              '“Two independent sources. Dates I can verify. Decide whose name'
              ' you want in print before you hand me anything.”'
          ),
          'holt': (
              '“A company can survive a director. It cannot survive every'
              ' claimant arriving on the same morning. A private settlement is'
              ' possible.”'
          ),
          'pell': (
              '“Sit down before you tell me you’re fine. Medicine needs'
              ' carrying. I’ll pay nine, or treat you.”'
          ),
          'iona': (
              '“Not stolen. Removed from an unsafe filing system. There is a'
              ' difference. I signed one valuation. Ada doesn’t know.”'
          ),
      }
      if target == 'iona' and 'ledger' not in s['evidence']:
        return (
            (
                'The counting room is empty. A snapped clock spring lies beside'
                ' the desk; somebody left in a hurry. Search the desk, or ask'
                ' Ada about another meeting place.'
            ),
            True,
        )
      if target == 'ada' and s['case'] == 'unaccepted':
        s['case'] = 'offered'
      return lines[target], False
    if verb == 'tell':
      if target != 'ada' or location != 'cafe' or not s['iona_confessed']:
        return (
            (
                'That private conversation needs Ada at the Lantern and Iona’s'
                ' actual account, not a guess.'
            ),
            False,
        )
      if s['ada_informed']:
        return (
            (
                'Ada already knows what Iona told you. Her answer remains in'
                ' your journal.'
            ),
            False,
        )
      s['ada_informed'] = True
      return (
          (
              'You show Ada the signature in private. She looks once, then'
              ' looks away. “If she chooses to speak, I’ll stand beside her.'
              ' Don’t choose for her.” A voluntary statement can now be used'
              ' without betraying an uninformed sister.'
          ),
          True,
      )
    if verb == 'restitution':
      if target != 'iona' or location != 'clinic' or not s['iona_confessed']:
        return (
            (
                'Iona’s twelve-dollar restitution can be paid to Pell at the'
                ' clinic after you hear her account.'
            ),
            False,
        )
      if s['iona_restitution']:
        return (
            'Pell’s receipt already records the payment; no duplicate charge.',
            False,
        )
      if s['cash'] < 12:
        return (
            (
                'The displaced families are owed $12. Pell has delivery work.'
                ' Public records remain another way to pursue the case.'
            ),
            False,
        )
      s['cash'] -= 12
      s['iona_restitution'] = True
      s['relief'] += 2
      return (
          (
              'Pell divides twelve dollars into four envelopes. “Not a pardon.'
              ' Grocery money.” The receipt names the families, not you. Iona'
              ' can no longer mistake being hidden for making amends.'
          ),
          True,
      )
    if verb == 'testify':
      if target != 'iona' or location != 'warehouse' or not s['iona_confessed']:
        return 'Ask Iona in person after hearing what she signed.', False
      if s['iona_testimony'] == 'coerced':
        return (
            (
                'Iona will not sign for you after that threat. The marked copy'
                ' survives; pursue independent records.'
            ),
            False,
        )
      if s['iona_testimony'] == 'voluntary':
        return (
            (
                'You already hold her signed account. Her consent is not a'
                ' repeatable reward.'
            ),
            False,
        )
      if not s['protected'] or not s['iona_restitution']:
        return (
            (
                'Iona refuses to sign a statement while the displaced families'
                ' go without or she has nowhere safe to sleep. Protection and'
                ' the $12 clinic receipt can change her answer; coercion and'
                ' public records are different routes.'
            ),
            False,
        )
      s['iona_testimony'] = 'voluntary'
      s['evidence']['affidavit'] = {
          'source': 'Iona’s signed, self-incriminating affidavit',
          'text': (
              'Iona authenticates the counter-ledger and admits her own false'
              ' valuation; she names Creel’s instruction with a date.'
          ),
          'credibility': 3,
          'kind': 'witness',
          'place': 'warehouse',
      }
      return (
          (
              'Iona writes “I knowingly entered” instead of “I was instructed'
              ' to enter.” Then she signs. “Use my name if you have to. Let Ada'
              ' hear it from you first.” The affidavit is credible because it'
              ' admits liability, not because it invents an independent source.'
          ),
          True,
      )
    if verb == 'investigate':
      if target not in s['known_leads']:
        return (
            (
                'You have no lead to that source yet. Talk to someone here or'
                ' inspect the public register.'
            ),
            False,
        )
      if target not in c.EVIDENCE or c.EVIDENCE[target]['place'] != location:
        return (
            (
                'No such lead is available here. Look around or ask a contact'
                ' for a specific source.'
            ),
            False,
        )
      if target in s['evidence']:
        return (
            (
                'You already have that evidence; the casebook preserves its'
                ' provenance.'
            ),
            False,
        )
      if target == 'ledger' and not s['protected'] and method == 'careful':
        s['lost_leads'] = list(
            dict.fromkeys(s['lost_leads'] + ['unsecured ledger'])
        )
        return (
            (
                'The desk is locked. Fresh boot marks lead to the back door.'
                ' Iona will not risk meeting you without a safe place. Arrange'
                ' protection with Nessa, try a quiet entry, or pursue Records'
                ' and the dock tally.'
            ),
            True,
        )
      if target == 'carbon' and method not in ('bargain', 'force', 'stealth'):
        return (
            (
                'Holt covers the carbon with his palm. “Bring another document.'
                ' Then we can discuss my signature.” Bargain with evidence,'
                ' steal it, or find another route.'
            ),
            False,
        )
      if target == 'carbon' and method == 'bargain' and not s['evidence']:
        return (
            '“An accusation is not collateral.” Holt offers nothing yet.',
            False,
        )
      if (
          target == 'manifest'
          and s['trust']['silas'] < 1
          and method == 'careful'
      ):
        return (
            (
                'Silas keeps the tally closed. Recover the tools, pay $4 for'
                ' certified access, or attempt a covert copy.'
            ),
            False,
        )
      if method == 'pay':
        if s['cash'] < 4:
          return (
              (
                  'Certified access costs $4. You can earn it, bargain, or find'
                  ' another source.'
              ),
              False,
          )
        s['cash'] -= 4
      if method == 'stealth' and location == 'mutual' and s['security'] >= 2:
        return (
            (
                'An audit has doubled the watch at Mutual. You see the second'
                ' guard before entering. Bargain with Holt or use the public'
                ' permit and dock tally.'
            ),
            False,
        )
      if method in ('force', 'stealth'):
        s['heat'] = min(5, s['heat'] + (2 if method == 'force' else 1))
        if method == 'force':
          s['injury'] = min(3, s['injury'] + 1)
      s['evidence'][target] = copy.deepcopy(c.EVIDENCE[target])
      if target == 'ledger':
        s['case'] = 'Iona located'
      return (
          'You secure '
          + c.EVIDENCE[target]['source']
          + '. '
          + c.EVIDENCE[target]['text'],
          True,
      )
    if verb == 'job':
      if target not in c.JOBS or c.JOBS[target]['place'] != location:
        return (
            'That job begins elsewhere. Your job board lists where to ask.',
            False,
        )
      status = s['jobs'].get(target)
      if status and status.startswith('complete:'):
        return (
            (
                'That commission is settled. Pell has ongoing delivery work;'
                ' use help pell at the clinic.'
            ),
            False,
        )
      if target == 'medicine':
        if status == 'carrying':
          return (
              (
                  'You have the cold case. Deliver it in the Narrows; Pell pays'
                  ' on the signed receipt.'
              ),
              False,
          )
        s['jobs'][target] = 'carrying'
        s['inventory'].append('cold medicine')
        return (
            (
                'Pell hands you a cold case, destination the Narrows shelter.'
                ' “Nine on delivery. Keep the seal intact.” You can go'
                ' directly, or settle another errand first; reading time does'
                ' not spoil it.'
            ),
            True,
        )
      if not status:
        s['jobs'][target] = 'decision'
        if target == 'tools':
          return (
              (
                  'The pawnbroker opens the cage so you can count the tools.'
                  ' Five dollars redeems them; a union guarantee is possible'
                  ' but needs a later medicine delivery. A theft risks'
                  ' witnesses. Choose job tools pay, bargain, stealth or force.'
              ),
              True,
          )
        return (
            (
                'You watch from the tram shelter. The midnight visitor carries'
                ' a medicine voucher and a child’s coat. You take the'
                ' photograph without being seen. The client’s intended scandal'
                ' would expose a patient’s family. Choose job photograph sell,'
                ' or warn; nothing has been sold yet.'
            ),
            True,
        )
      job = c.JOBS[target]
      reward = job['pay']
      if target == 'tools':
        if method == 'pay':
          if s['cash'] < 5:
            return (
                (
                    'You need $5 to redeem the tools. A union guarantee is'
                    ' still possible.'
                ),
                False,
            )
          s['cash'] -= 5
        elif method in ('stealth', 'force'):
          s['heat'] = min(5, s['heat'] + 2)
        else:
          s['debts'].append('union guarantee: carry medicine for the crew')
        s['trust']['silas'] += 2
        s['known_leads'] = list(dict.fromkeys(s['known_leads'] + ['manifest']))
        result = (
            'Silas checks every wrench before he pays. “You can ask about that'
            ' early shipment now.”'
        )
      elif target == 'photograph':
        if method == 'sell':
          s['photo_exposed'] = True
          s['trust']['pell'] -= 2
          s['heat'] = min(5, s['heat'] + 1)
          result = (
              'The client pays and circulates the photograph under your byline.'
              ' It identifies a sick child’s father. A copy reaches Pell’s'
              ' clinic; the damage has a traceable route.'
          )
        else:
          reward = 4
          s['trust']['pell'] += 1
          result = (
              'You warn the family and return the retainer. The father presses'
              ' four dollars into your hand. Pell will remember the discretion.'
          )
      else:
        if 'union guarantee: carry medicine for the crew' in s['debts']:
          s['debts'].remove('union guarantee: carry medicine for the crew')
        s['trust']['pell'] += 1
        result = (
            'Pell signs for an unbroken cold chain. At the Narrows, a girl'
            ' stops coughing long enough to complain about the taste.'
        )
      s['jobs'][target] = 'complete:' + method
      s['cash'] += reward
      return result + f' Payment: ${reward}.', True
    if verb == 'deliver':
      if (
          target != 'medicine'
          or location != 'narrows'
          or 'cold medicine' not in s['inventory']
      ):
        return (
            (
                'Delivery needs the sealed cold case from Pell and the Narrows'
                ' shelter.'
            ),
            False,
        )
      s['inventory'].remove('cold medicine')
      s['jobs']['medicine'] = 'complete:delivered'
      s['cash'] += 9
      s['trust']['pell'] += 1
      s['relief'] += 1
      debt = 'union guarantee: carry medicine for the crew'
      if debt in s['debts']:
        s['debts'].remove(debt)
      return (
          (
              'At the shelter you count the ampoules with the nurse. She signs'
              ' the receipt and pays nine. The crew’s families receive their'
              ' doses; your union guarantee is discharged.'
          ),
          True,
      )
    if verb == 'copy':
      if target not in s['evidence']:
        return 'You can only copy evidence you possess.', False
      if target in s['copies']:
        return (
            (
                'A duplicate is already held safely. Copying it again creates'
                ' no new independent source.'
            ),
            False,
        )
      if location not in ('office', 'press'):
        return (
            (
                'Use the office camera stand or Vera’s copy desk to make a'
                ' legible duplicate.'
            ),
            False,
        )
      s['copies'].append(target)
      return (
          (
              'You photograph every page and place the duplicate in the office'
              ' safe. The provenance remains the same; it is insurance against'
              ' loss, not a second witness.'
          ),
          True,
      )
    if verb == 'barter':
      if target == 'holt' and location == 'mutual' and s['copies']:
        pledge = 'secured copy pledged for Mutual relocation audit'
        if pledge in s['promises']:
          return (
              (
                  'The bond offer remains open. Holt will not pay twice for the'
                  ' same collateral.'
              ),
              False,
          )
        s['bond_offer'] = True
        s['promises'].append(pledge)
        s['trust']['holt'] += 1
        return (
            (
                'You offer a copied document for a signed relocation'
                ' commitment. Holt cannot buy silence by taking the original'
                ' now. He opens the bond book; one documented source is enough'
                ' to negotiate families’ relocation.'
            ),
            True,
        )
      if (
          target == 'silas'
          and location == 'docks'
          and s['jobs'].get('tools') == 'decision'
      ):
        return self._apply('job', 'tools', 'bargain')
      return (
          (
              'State a tangible exchange with someone here. A copied document'
              ' gives Holt collateral; a guarantee can redeem Silas’s tools.'
          ),
          False,
      )
    if verb == 'promise':
      if target not in ('ada', 'nessa') or c.CONTACTS[target][1] != location:
        return (
            'Make that promise in person to Ada or Nessa at the Lantern.',
            False,
        )
      promise = (
          'protect Iona’s name'
          if target == 'ada'
          else 'keep Narrows families housed'
      )
      if promise not in s['promises']:
        s['promises'].append(promise)
        s['trust'][target] += 1
      return f'“I’ll hold you to that.” Recorded promise: {promise}.', True
    if verb == 'protect':
      if target not in ('iona', 'source', 'witness', ''):
        return (
            (
                'The known safehouse arrangement is for Iona. Name a different'
                ' concrete proposal in your own words; no protection has been'
                ' assigned.'
            ),
            False,
        )
      if location not in ('cafe', 'clinic'):
        return (
            (
                'A hiding place needs a willing host. Ask at the Lantern or'
                ' clinic.'
            ),
            False,
        )
      if not s['protected']:
        s['protected'] = True
        if s['shelter_beds'] == 0:
          s['debts'].append(
              'safehouse: repay Nessa with a neighbourhood favour'
          )
        else:
          s['shelter_beds'] -= 1
        s['trust']['ada'] += 1
        s['known_leads'] = list(dict.fromkeys(s['known_leads'] + ['ledger']))
      return (
          (
              'A bed above the kitchen, a borrowed coat, no name in the'
              ' register. Ada can bring Iona here. You owe the host a favour.'
          ),
          True,
      )
    if verb == 'publish':
      if location != 'press':
        return 'Take your evidence to Vera at the Evening Wire.', False
      sources = s['evidence']
      independent = {
          (
              'iona-account'
              if key in ('ledger', 'testimony', 'affidavit')
              else key
          )
          for key in sources
      }
      if (
          len(independent) < 2
          or sum(e['credibility'] for e in sources.values()) < 4
      ):
        return (
            (
                'Vera returns the folder. “Two independent sources, enough to'
                ' withstand a denial. Come back with a document that'
                ' corroborates this.” No evidence is lost.'
            ),
            False,
        )
      if s['published']:
        return (
            (
                'The story is already public. Its consequences remain; you can'
                ' still negotiate restitution.'
            ),
            False,
        )
      if target not in ('redacted', 'named'):
        return (
            (
                'Choose publish redacted to protect the source (needs three'
                ' sources), or publish named for a faster, riskier case.'
            ),
            False,
        )
      vulnerable = bool(set(sources) & {'ledger', 'testimony', 'affidavit'})
      if target == 'redacted' and vulnerable and len(independent) < 3:
        return (
            (
                'Without naming a witness, Vera needs a third independent'
                ' record. She keeps nothing; bring corroboration.'
            ),
            False,
        )
      breached = 'Mutual confidentiality clause' in s['promises']
      if breached:
        s['promises'].remove('Mutual confidentiality clause')
        s['debts'].append('Mutual repayment: $35 after confidentiality breach')
        s['heat'] = min(5, s['heat'] + 2)
        s['trust']['holt'] -= 2
      s['published'] = list(sources)
      s['stayed'] = True
      s['case'] = 'public inquiry'
      consensual = s['iona_testimony'] == 'voluntary' and s['ada_informed']
      if target == 'named' and vulnerable and consensual:
        s['source_exposed'] = True
        if 'protect Iona’s name' in s['promises']:
          s['promises'].remove('protect Iona’s name')
        s['trust']['ada'] += 1
        result = (
            'Vera prints Iona’s own admission beside the company records. Iona'
            ' accepts a hearing summons; Ada will accompany her. Demolition'
            ' stops, but your witness now faces a real charge. You paid for'
            ' restitution, not immunity.'
        )
      elif target == 'named' and vulnerable:
        s['source_exposed'] = True
        s['trust']['ada'] -= 3
        if 'protect Iona’s name' in s['promises']:
          s['promises'].remove('protect Iona’s name')
          s['debts'].append('broken promise to Ada')
        result = (
            'The presses roll. Iona is named; her signature makes the case'
            ' credible and puts her in danger. Ada stops answering your calls.'
        )
      else:
        s['trust']['ada'] += 2
        result = (
            'The records tell the story without naming a protected witness.'
            ' Vera prints the dates twice. “So nobody can say they misread'
            ' them.”'
        )
      if breached:
        result += (
            ' Mutual serves the advertised $35 repayment demand; legal heat'
            ' rises by two. The newspaper still publishes.'
        )
      return (
          result
          + ' Demolition stops. The frozen claims leave a relief problem you'
          ' can choose to help solve.',
          True,
      )
    if verb == 'settle':
      required = (
          1
          if 'secured copy pledged for Mutual relocation audit' in s['promises']
          else 2
      )
      if location != 'mutual' or len(s['evidence']) < required:
        return (
            (
                'Holt needs two pieces of evidence and a meeting at Mutual'
                ' before he can commit company money.'
            ),
            False,
        )
      if s['settlement']:
        return (
            'The signed settlement still stands. Holt will not pay twice.',
            False,
        )
      if target not in ('families', 'self'):
        return (
            (
                'State whose payment you demand: settle families, or settle'
                ' self. You keep your evidence either way.'
            ),
            False,
        )
      if target == 'self' and not s['retainer_terms_seen']:
        s['retainer_terms_seen'] = True
        return (
            (
                'Holt puts the terms in writing: $35 for consultancy, no money'
                ' for families, and a confidentiality clause. Publishing'
                ' afterwards creates a $35 repayment obligation and legal heat.'
                ' You keep the evidence. Repeat settle self to sign, or demand'
                ' settle families instead.'
            ),
            False,
        )
      s['settlement'] = target
      if target == 'families':
        s['relocation'] = True
        if s['petition'] >= 2:
          s[
              'cash'
          ] += 5  # Public organising earns a documented investigator fee.
        s['trust']['nessa'] += 2
        return (
            (
                'Holt signs relocation bonds, not a confession. Nessa has money'
                ' and no neighbourhood. You retain the papers; publication'
                ' remains possible.'
            ),
            True,
        )
      s['cash'] += 35
      s['promises'].append('Mutual confidentiality clause')
      s['trust']['nessa'] -= 2
      # Private payment cannot repeal a public stay or erase relocation bonds.
      return (
          (
              'Thirty-five dollars clears. Holt calls it consultancy. Nessa'
              ' calls it what it cost her. You keep the papers and can still'
              ' change sides, but nobody forgets the payment.'
          ),
          True,
      )
    if verb == 'repay':
      debt = 'Mutual repayment: $35 after confidentiality breach'
      if target == 'mutual' and location == 'mutual' and debt in s['debts']:
        if s['cash'] < 35:
          return (
              (
                  'The written demand is $35. Earn the balance or leave the'
                  ' obligation outstanding; your inquiry remains public.'
              ),
              False,
          )
        s['cash'] -= 35
        s['debts'].remove(debt)
        s['heat'] = max(0, s['heat'] - 1)
        s['trust']['holt'] += 1
        return (
            (
                'Holt stamps the release before taking your money. One point of'
                ' legal heat falls. The public story and the fact you broke the'
                ' clause remain on record.'
            ),
            True,
        )
      if (
          target == 'rent'
          and location == 'office'
          and 'office rent' in s['debts']
      ):
        if s['cash'] < 3:
          return 'You need $3 to clear the deferred office rent.', False
        s['cash'] -= 3
        s['debts'].remove('office rent')
        return (
            (
                'The landlord writes paid beside the deferred rent. Your office'
                ' remains open.'
            ),
            True,
        )
      return (
          (
              'Repay Mutual at its office, or deferred rent at your own.'
              ' Personal favours require the promised work.'
          ),
          False,
      )
    if verb == 'rest':
      if location not in ('office', 'clinic', 'cafe'):
        return 'Find the office, café or clinic to recover safely.', False
      cost = 3 if location == 'clinic' else 1
      if s['cash'] >= cost:
        s['cash'] -= cost
      elif 'treatment credit' not in s['debts']:
        s['debts'].append('treatment credit')
      s['injury'] = max(0, s['injury'] - 1)
      s['heat'] = max(0, s['heat'] - 1)
      return (
          (
              'A meal, dry socks, a few hours without questions. Injury and'
              ' heat each fall by one. Leads remain available when you return.'
          ),
          True,
      )
    if verb == 'help':
      if target == 'pell' and location == 'clinic':
        if s['photo_exposed']:
          s['photo_exposed'] = False
          s['trust']['pell'] = max(0, s['trust']['pell'])
          return (
              (
                  'You spend the shift distributing corrections and carrying'
                  ' supplies unpaid. Pell sees you do it. Paid routes reopen;'
                  ' the circulated photograph cannot be recalled.'
              ),
              True,
          )
        s['cash'] += 6
        s['trust']['pell'] += 1
        s['injury'] = max(0, s['injury'] - 1)
        return (
            (
                'You carry medicine; Pell dresses your wound. Six dollars for'
                ' the route. The clinic always needs another pair of hands.'
            ),
            True,
        )
      if target == 'families' and location == 'narrows':
        if s['cash'] < 3:
          return 'A food parcel costs $3. Pell has paid delivery work.', False
        s['cash'] -= 3
        s['trust']['nessa'] += 1
        debt = 'safehouse: repay Nessa with a neighbourhood favour'
        if debt in s['debts']:
          s['debts'].remove(debt)
        s['relief'] += 1
        return (
            (
                'You carry the parcel upstairs yourself. Nessa marks your'
                ' favour paid. It changes one evening, not the city.'
            ),
            True,
        )
      return 'Ask Pell for work, or bring relief to the Narrows.', False
    if verb == 'apologize':
      if (
          target == 'ada'
          and location == 'cafe'
          and s['relief'] > 0
          and s['trust']['ada'] < 0
      ):
        s['trust']['ada'] = 0
        return (
            (
                'Ada has seen the parcel receipts. “I can speak to you. That'
                ' isn’t the same as trusting you with her name again.” Access'
                ' restored; the broken promise remains in your record.'
            ),
            True,
        )
      return (
          (
              'Repair needs an action the injured person can see. Ada needs'
              ' relief delivered to the Narrows; Pell needs an unpaid'
              ' correction round.'
          ),
          False,
      )
    if verb == 'threaten':
      if target == 'iona' and location == 'warehouse' and s['iona_confessed']:
        s['iona_testimony'] = 'coerced'
        s['evidence'].pop('affidavit', None)
        s['heat'] = min(5, s['heat'] + 2)
        s['trust']['ada'] -= 2
        return (
            (
                'Iona writes what you dictate, then marks the margin UNDER'
                ' THREAT. Vera will not treat this as an affidavit. Ada'
                ' receives the marked copy from her sister. You still have the'
                ' original ledger and public-record routes.'
            ),
            True,
        )
      if target not in c.CONTACTS or c.CONTACTS[target][1] != location:
        return 'You cannot threaten someone who is not here.', False
      s['heat'] = min(5, s['heat'] + 2)
      s['injury'] = min(3, s['injury'] + 1)
      if target in s['trust']:
        s['trust'][target] -= 2
      return (
          (
              'The room goes quiet. You get space, not agreement. A guard'
              ' catches your wrist on the way out; witnesses will remember the'
              ' threat.'
          ),
          True,
      )
    return (
        (
            'You let an hour pass. Each resident has at most one new'
            ' opportunity; nothing advances on the wall clock.'
        ),
        True,
    )

  def resident_moves(self, name):
    """Only locally meaningful work; completed tasks need not be repeated."""
    with self.lock:
      s = self.state
      available = {
          'Nessa Rook': {
              'organise': s['petition'] < 3,
              'shelter': s['shelter_beds'] < 8,
          },
          'Silas Marr': {
              'petition': s['union_support'] < 3,
              'guard': s['union_support'] > 0 and s['security'] > 0,
          },
          'Edwin Holt': {
              'audit': s['security'] < 3,
              'offer': not s['bond_offer'],
          },
      }
      return [move for move in c.NPCS[name]['moves'] if available[name][move]]

  def npc_resolve(self, name, move, line):
    with self.lock:
      s = self.state
      before = copy.deepcopy(s)
      if s['npc_turns'][name] >= s['turn']:
        return 'No new opportunity.'
      s['npc_turns'][name] = s['turn']
      if move not in self.resident_moves(name):
        return self._record(
            name,
            {'move': move},
            'That work no longer changes local conditions; no duplicate'
            ' effect.',
            before,
        )
      s['agendas'][name] += 1
      if name == 'Nessa Rook':
        if move == 'shelter':
          s['shelter_beds'] = min(8, s['shelter_beds'] + 2)
          result = (
              f"Nessa opens {s['shelter_beds']} shelter beds above the Lantern."
              ' A hiding place is now easier to arrange.'
          )
        else:
          s['petition'] = min(3, s['petition'] + 1)
          result = (
              "The tenants' petition gains a verified block representative"
              f" ({s['petition']}/3). It can reinforce a relocation demand."
          )
      elif name == 'Silas Marr':
        if move == 'petition':
          s['known_leads'] = list(
              dict.fromkeys(s['known_leads'] + ['manifest'])
          )
          s['union_support'] = min(3, s['union_support'] + 1)
          result = (
              'Silas posts a public notice offering certified access to the'
              ' early loading tally for $4. Recovery of the tools earns free'
              ' access.'
          )
        else:
          s['union_support'] = max(0, s['union_support'] - 1)
          s['security'] = max(0, s['security'] - 1)
          result = (
              'Silas puts witnesses at the quay instead of petitioning. Guard'
              ' attention shifts from Mutual; the union spends some of its'
              ' support.'
          )
      elif move == 'audit':
        s['security'] = min(3, s['security'] + 1)
        result = (
            f"Mutual announces an audit. Security level {s['security']}/3; at"
            ' level2 a covert carbon copy is unsafe. Public records remain'
            ' open.'
        )
      else:
        s['bond_offer'] = True
        s['known_leads'] = list(dict.fromkeys(s['known_leads'] + ['carbon']))
        result = (
            'Holt invites document holders to relocation talks. An invitation'
            ' is not a signed bond: bring corroboration or pledge a secured'
            ' duplicate. His carbon remains private.'
        )
      # Public announcements are explicitly transmitted, not NPC omniscience.
      if not s['news'] or s['news'][-1] != result:
        s['news'].append(result)
      self._refresh_neighbourhood()
      # Dialogue is an attempt, not authority to invent world facts. Kept in
      # developer log; public delivery requires meeting the actual speaker.
      return self._record(name, {'move': move, 'line': line}, result, before)


def intent_options(ledger):
  """Grounded scene affordances shared with the human suggestions, not outcomes."""
  s = ledger.public()
  location = s['location']
  commands = [
      command
      for command in ledger.available()
      if command not in ('confirm', 'cancel')
  ] + ['refuse case', 'wait']
  local_contacts = [
      key
      for key, value in c.CONTACTS.items()
      if value[1] == location and (key != 'iona' or 'ledger' in s['evidence'])
  ]
  commands += [f'threaten {key}' for key in local_contacts]
  if location in ('cafe', 'clinic'):
    commands += ['protect iona']
  if location == 'cafe':
    commands += ['promise ada', 'promise nessa', 'apologize ada']
  if location == 'clinic':
    commands += ['help pell']
  if location == 'narrows':
    commands += ['help families']
  if location in ('office', 'press'):
    commands += [f'copy {key}' for key in s['evidence']]
  if location == 'mutual':
    commands += [
        'barter holt',
        'settle families',
        'settle self',
        'repay mutual',
    ]
  if location == 'docks':
    commands += ['barter silas']
  for key, status in s['jobs'].items():
    if c.JOBS[key]['place'] == location and status == 'decision':
      commands += [f'refuse {key}']
      methods = (
          ('sell', 'warn')
          if key == 'photograph'
          else ('pay', 'bargain', 'stealth', 'force')
      )
      commands += [f'job {key} {method}' for method in methods]
  for key in s['known_leads']:
    if (
        key in c.EVIDENCE
        and c.EVIDENCE[key]['place'] == location
        and key not in s['evidence']
    ):
      methods = {
          'permit': (),
          'testimony': (),
          'ledger': ('stealth', 'force'),
          'manifest': ('pay', 'stealth', 'force'),
          'carbon': ('bargain', 'stealth', 'force'),
      }
      commands += [
          f'investigate {key} {method}' for method in methods.get(key, ())
      ]
  meanings = {
      'go': 'travel to',
      'talk': 'ask questions of or listen to',
      'look': 'inspect surroundings without committing time',
      'investigate': 'obtain or examine a known evidence source',
      'job': 'perform the commissioned work',
      'rest': 'rest and recover',
      'promise': 'make a personal commitment to',
      'protect': 'arrange a safe bed for',
      'publish': 'give the case to the press NOW for publication',
      'settle': 'negotiate or accept a settlement benefiting',
      'refuse': 'decline or return the commission',
      'wait': 'let fictional time pass',
      'help': 'do relief or clinic work for',
      'threaten': 'intimidate or coerce',
      'apologize': 'ask forgiveness from',
      'deliver': 'physically deliver the cold medicine',
      'copy': 'photograph or duplicate owned document pages for safekeeping',
      'barter': 'offer collateral or a guarantee in exchange to',
      'repay': 'pay back the confidentiality debt to',
      'restitution': (
          'pay Iona’s twelve-dollar compensation to displaced families'
      ),
      'testify': 'ask Iona to give a voluntary signed statement',
      'tell': 'privately inform Ada of Iona’s confession',
  }
  options = {}
  for command in dict.fromkeys(commands):
    words = command.split()
    verb = words[0]
    target = words[1] if len(words) > 1 else ''
    method = words[2] if len(words) > 2 else 'careful'
    subject = (
        c.PLACES[target][0]
        + (' (Rowan’s own office)' if target == 'office' else '')
        if verb == 'go' and target in c.PLACES
        else c.CONTACTS[target][0]
        if target in c.CONTACTS
        else target
    )
    label = f'{command} — {meanings[verb]} {subject}'
    if len(words) > 2:
      label += {
          'pay': '; pay $4 for evidence or $5 for tools',
          'stealth': '; covert entry risks heat',
          'force': '; force risks heat and injury',
          'bargain': '; negotiate an exchange',
          'sell': '; sell and circulate the photograph',
          'warn': '; warn the family, lower fee',
      }[method]
    options[label] = {'verb': verb, 'target': target, 'method': method}
  options[
      'unclear — unsupported, contradictory, or several distinct actions; ask'
      ' the player to clarify'
  ] = {'verb': 'unclear'}
  return options


def parse_intent(text, model, ledger):
  """Match expressive language to a grounded affordance using standard choice."""
  words = text.lower().strip().split()
  targets = (
      set(c.PLACES)
      | set(c.CONTACTS)
      | set(c.EVIDENCE)
      | set(c.JOBS)
      | {
          'affidavit',
          'families',
          'self',
          'case',
          'source',
          'witness',
          'redacted',
          'named',
      }
  )
  exact = bool(words) and (
      len(words) == 1
      and words[0] in ('look', 'rest', 'wait', 'confirm', 'cancel')
      or len(words) in (2, 3)
      and words[0] in VERBS
      and words[0] not in ('look', 'rest', 'wait', 'confirm', 'cancel')
      and words[1] in targets
      and (len(words) == 2 or words[2] in METHODS)
  )
  if exact:
    return {
        'verb': words[0],
        'target': words[1] if len(words) > 1 else '',
        'method': words[2] if len(words) > 2 else 'careful',
    }
  options = intent_options(ledger)
  prompt = (
      'The investigator is Rowan Vale. Their own office is Vale Investigations'
      ' [office]; Municipal Records [records] is a different building.'
      ' Interpret ONE investigator intention, not its success. Choose the scene'
      ' affordance whose meaning actually matches the attempt. Respect'
      ' negation: do not publish, sell, threaten or pay if the player refuses'
      ' that action. Asking about something is conversation, not permission to'
      ' do it. If no option preserves the intent, or distinct actions conflict,'
      ' choose unclear. Never choose a merely related substitute. Copying'
      ' papers and locking that copy away is one coherent act, not two'
      ' unrelated actions.\nCurrent player-visible scene:\n'
      + ledger.view()
      + '\nPlayer attempt: '
      + text
  )
  # Reuse the standard arbitrary-response choice contract with short commands,
  # avoiding an extra letter mapping task or a long response schema.
  labels = {label.split(' — ', 1)[0]: label for label in options}
  _, command, _ = model.sample_choice(
      prompt + '\nAvailable intentions:\n' + '\n'.join(options),
      responses=tuple(labels),
  )
  choice = labels[command]
  return {
      **options[choice],
      '_model_response': choice,
      '_needs_confirmation': True,
  }

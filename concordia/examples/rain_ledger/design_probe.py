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

"""Deterministic rule-level play transcripts; DOES NOT launch an engine or LLM."""

import argparse
import json
from pathlib import Path
from concordia.examples.rain_ledger import rules

_DISCLOSURE_OPENING = [
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
    'talk vera',
]

_FOLLOWUP = _DISCLOSURE_OPENING + [
    'publish records',
    'go docks',
    'go warehouse',
    'investigate ledger stealth',
    'talk iona',
    'go docks',
    'go press',
    'talk vera',
]

_WEAK_FAMILY = [
    'go cafe',
    'talk ada',
    'investigate testimony',
    'go narrows',
    'go warehouse',
    'investigate ledger stealth',
    'go docks',
    'go press',
    'go mutual',
    'talk holt',
    'investigate carbon bargain',
    'go press',
    'talk vera',
    'publish named',
]

PATHS = {
    'family_corroboration': (
        _WEAK_FAMILY
        + [
            'go mutual',
            'go records',
            'investigate permit',
            'go mutual',
            'go press',
            'talk vera',
            'publish records',
        ]
    ),
    'family_authentication': (
        _WEAK_FAMILY
        + [
            'go docks',
            'go office',
            'go cafe',
            'protect iona',
            'go narrows',
            'go warehouse',
            'talk iona',
            'authenticate ledger',
            'go docks',
            'go press',
            'talk vera',
            'publish named',
        ]
    ),
    'clinic_betrayal_repair': [
        'go cafe',
        'go clinic',
        'help pell',
        'help pell',
        'help pell',
        'go cafe',
        'go office',
        'go records',
        'go mutual',
        'job photograph',
        'job photograph sell',
        'go records',
        'go office',
        'go cafe',
        'go clinic',
        'talk pell',
        'job medicine',
        'help pell',
        'talk pell',
        'job medicine',
        'go narrows',
        'deliver medicine',
        'go clinic',
        'help pell',
    ],
    'medicine_before_tools': [
        'refuse case',
        'go cafe',
        'go clinic',
        'job medicine',
        'go narrows',
        'deliver medicine',
        'go warehouse',
        'go docks',
        'job tools',
        'job tools bargain',
        'go office',
        'go cafe',
        'go clinic',
        'job medicine',
        'job medicine',
        'go narrows',
        'deliver medicine',
        'go clinic',
        'job medicine',
    ],
    'tenant_organiser': [
        'refuse case',
        'go cafe',
        'go clinic',
        'go narrows',
        'organise families',
        'organise families',
        'go clinic',
        'go cafe',
        'go office',
        'go records',
        'investigate permit',
        'go mutual',
        'talk holt',
        'investigate carbon bargain',
        'go press',
        'publish records',
        'go mutual',
        'settle relief',
        'settle relief accept',
        'settle families',
        'go records',
        'go office',
        'go cafe',
        'talk nessa',
    ],
    'acquisition_authenticate': [
        'go records',
        'investigate permit',
        'go mutual',
        'talk holt',
        'investigate carbon stealth',
        'go press',
        'talk vera',
        'publish records',
        'go mutual',
        'authenticate carbon bargain',
        'go press',
        'talk vera',
        'publish records',
    ],
    'acquisition_corroborate': [
        'go records',
        'investigate permit',
        'go mutual',
        'talk holt',
        'investigate carbon stealth',
        'go press',
        'publish records',
        'go docks',
        'talk silas',
        'investigate manifest pay',
        'go press',
        'publish records',
    ],
    'acquisition_work': [
        'go docks',
        'talk silas',
        'investigate manifest bargain',
        'investigate manifest stealth',
        'authenticate manifest',
        'job tools',
        'job tools bargain',
        'authenticate manifest',
        'go office',
        'go records',
        'investigate permit',
        'go mutual',
        'go press',
        'publish records',
    ],
    'followup_redacted': (
        _FOLLOWUP
        + [
            'publish redacted',
            'publish redacted',
            'go docks',
            'go office',
            'go cafe',
            'talk ada',
        ]
    ),
    'followup_named': (
        _FOLLOWUP
        + [
            'publish named',
            'publish named',
            'go docks',
            'go office',
            'go cafe',
            'talk ada',
        ]
    ),
    'disclosure_records': (
        _DISCLOSURE_OPENING
        + [
            'publish records',
            'talk vera',
            'go docks',
            'go office',
            'go cafe',
            'talk ada',
        ]
    ),
    'disclosure_named': (
        _DISCLOSURE_OPENING
        + ['publish named', 'go docks', 'go office', 'go cafe', 'talk ada']
    ),
    'disclosure_rebuild': [
        'go records',
        'investigate permit',
        'go mutual',
        'go press',
        'talk vera',
        'publish records',
        'go docks',
        'talk silas',
        'investigate manifest pay',
        'go press',
        'talk vera',
        'publish records',
    ],
    'confession': [
        'go cafe',
        'promise ada',
        'talk ada',
        'protect iona',
        'go narrows',
        'go warehouse',
        'investigate ledger',
        'talk iona',
        'testify iona',
        'go narrows',
        'go clinic',
        'restitution iona',
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
        'go docks',
        'go warehouse',
        'talk iona',
        'go narrows',
        'go cafe',
        'talk ada',
    ],
    'coercion': [
        'go cafe',
        'promise ada',
        'protect iona',
        'go narrows',
        'go warehouse',
        'investigate ledger',
        'talk iona',
        'threaten iona',
        'testify iona',
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
        'talk ada',
    ],
    'altruist': [
        'go cafe',
        'promise ada',
        'talk ada',
        'protect iona',
        'investigate testimony',
        'go office',
        'go records',
        'investigate permit',
        'go office',
        'go docks',
        'job tools',
        'job tools bargain',
        'investigate manifest',
        'go press',
        'publish redacted',
        'go docks',
        'go office',
        'go cafe',
        'talk ada',
        'go clinic',
        'job medicine',
        'go narrows',
        'deliver medicine',
        'help families',
    ],
    'opportunist': [
        'go records',
        'investigate permit',
        'go mutual',
        'talk holt',
        'job photograph',
        'job photograph sell',
        'investigate carbon bargain',
        'settle self',
        'settle self',
        'go press',
        'publish named',
        'go mutual',
        'settle families',
        'go records',
        'go office',
        'go cafe',
        'talk ada',
        'go clinic',
        'talk pell',
        'help pell',
        'help pell',
    ],
    'refusal': [
        'refuse case',
        'go docks',
        'job tools',
        'job tools bargain',
        'go office',
        'go cafe',
        'go clinic',
        'job medicine',
        'rest',
        'go narrows',
        'deliver medicine',
        'go warehouse',
        'investigate ledger',
        'go narrows',
        'go cafe',
        'talk ada',
    ],
    'betrayal_repair': [
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
        'talk ada',
        'apologize ada',
        'go narrows',
        'help families',
        'go cafe',
        'apologize ada',
        'talk ada',
    ],
    'copy_bargain': [
        'go records',
        'investigate permit',
        'go office',
        'copy permit',
        'go records',
        'go mutual',
        'barter holt',
        'settle families',
        'settle families accept',
        'go press',
        'publish named',
    ],
}


def play(actions):
  ledger = rules.Ledger()
  transcript = []
  for action in actions:
    parts = action.split()
    intent = {
        'verb': parts[0],
        'target': parts[1] if len(parts) > 1 else '',
        'method': parts[2] if len(parts) > 2 else 'careful',
    }
    before = ledger.public()
    result = ledger.resolve(intent, action)
    transcript.append({
        'action': action,
        'response': result,
        'before': before,
        'after': ledger.public(),
    })
  return transcript


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--output', type=Path, required=True)
  parser.add_argument(
      '--path',
      choices=PATHS,
      action='append',
      help='Only replay selected rule paths.',
  )
  args = parser.parse_args()
  args.output.mkdir(parents=True, exist_ok=False)
  for name in args.path or PATHS:
    transcript = play(PATHS[name])
    (args.output / (name + '.json')).write_text(
        json.dumps(transcript, indent=2)
    )
    print(
        name,
        json.dumps({
            key: transcript[-1]['after'][key]
            for key in ('cash', 'turn', 'neighbourhood')
        }),
    )


if __name__ == '__main__':
  main()

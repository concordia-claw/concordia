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

PATHS = {
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
  args = parser.parse_args()
  args.output.mkdir(parents=True, exist_ok=False)
  for name, actions in PATHS.items():
    transcript = play(actions)
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

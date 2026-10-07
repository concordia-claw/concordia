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

"""Bounded real-local-model contrasting plays; launches the standard engine."""

import argparse
import json
from pathlib import Path
import threading
import time

from concordia.contrib.language_models.ollama import ollama_model
from concordia.examples.rain_ledger import game
from concordia.examples.rain_ledger import rules
from concordia.examples.rain_ledger.smoke import until
from concordia.language_model import call_limit_wrapper

PATHS = {
    'compromise': [
        'go records',
        'investigate permit',
        'go office',
        (
            'I photograph each page of the permit and lock the duplicate in my'
            ' office safe.'
        ),
        'go records',
        'go mutual',
        (
            'I offer Holt a copy of the permit in exchange for a relocation'
            ' bond, keeping my original safe.'
        ),
        'settle families',
        'go press',
        'publish named',
        'go docks',
        'go office',
        'go cafe',
        'talk nessa',
    ],
    'aftermath': [
        'Iona, what do you want me to do now that the hearing is coming?',
        'go narrows',
        'go cafe',
        'Ada, how do you feel about going to court with your sister?',
        'go clinic',
        'job medicine',
        'rest',
        'go narrows',
        'deliver medicine',
        'help families',
        'go cafe',
        'talk nessa',
    ],
    'intent': [
        'I cannot take the missing-person commission. Return the envelope.',
        'Take me to the municipal register office.',
        'Compare the dates on the demolition permit.',
        'Head back to my own office.',
        'Make photographs of these pages for safekeeping.',
        'Do not publish anything. Just look around the room.',
        'Burn the evidence and frame the doctor for it.',
        'I need to sit down and recover for a while.',
    ],
    'confession': [
        'go cafe',
        'promise ada',
        'talk ada',
        'protect iona',
        'go narrows',
        'go warehouse',
        'investigate ledger',
        'Ask Iona why she took the ledger and what she herself signed.',
        'testify iona',
        'go narrows',
        'go clinic',
        (
            'I want to pay the twelve dollars that Iona owes the displaced'
            ' families.'
        ),
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
    ],
    'opportunist': [
        'go records',
        'investigate permit',
        'go office',
        (
            'I photograph each page of the permit and lock the duplicate in my'
            ' office safe.'
        ),
        'go records',
        'go mutual',
        (
            'I offer Holt a copy of the permit in exchange for a relocation'
            ' bond, keeping my original safe.'
        ),
        'talk holt',
        'investigate carbon bargain',
        'job photograph',
        'job photograph sell',
        'settle self',
        'settle self',
        'go press',
        'publish named',
        'go mutual',
        'repay mutual',
        'go records',
        'go office',
        'go cafe',
        'go clinic',
        'talk pell',
        'help pell',
        'help pell',
    ],
    'refusal': [
        (
            'I tell Ada I cannot take the missing bookkeeper case and return'
            ' the unopened envelope.'
        ),
        'go docks',
        'job tools',
        'barter silas',
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
        'Ask Ada where I might look if I decide to help her after all.',
        'go narrows',
        'go warehouse',
        'investigate ledger',
    ],
}


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--path', choices=PATHS, required=True)
  parser.add_argument('--model', default='llama3.2:3b')
  parser.add_argument('--no-think', action='store_true')
  parser.add_argument('--checkpoint', type=Path)
  parser.add_argument('--output', type=Path, required=True)
  args = parser.parse_args()
  args.output.mkdir(parents=True, exist_ok=False)
  model = call_limit_wrapper.CallLimitLanguageModel(
      ollama_model.OllamaLanguageModel(
          args.model,
          think=False if args.no_think else None,
          request_timeout=60,
          max_output_tokens=180,
          response_format=None,
          system_message=(
              'Follow the requested format. Choose only a supplied option when'
              ' asked to choose.'
          ),
      ),
      max_calls=120,
  )
  instance = game.Game(model, args.output, checkpoint=args.checkpoint)
  errors = []

  def run():
    try:
      instance.play(max_steps=100000)
    except Exception as exc:
      errors.append(repr(exc))

  worker = threading.Thread(target=run)
  worker.start()
  transcript = []
  expected_by_path = {
      'compromise': {
          3: ('copy', 'permit', 'careful'),
          6: ('barter', 'holt', 'careful'),
      },
      'aftermath': {
          0: ('talk', 'iona', 'careful'),
          3: ('talk', 'ada', 'careful'),
      },
      'confession': {
          7: ('talk', 'iona', 'careful'),
          11: ('restitution', 'iona', 'careful'),
      },
      'opportunist': {
          3: ('copy', 'permit', 'careful'),
          6: ('barter', 'holt', 'careful'),
      },
      'refusal': {
          0: ('refuse', 'case', 'careful'),
          15: ('talk', 'ada', 'careful'),
      },
      'intent': dict(
          enumerate([
              ('refuse', 'case', 'careful'),
              ('go', 'records', 'careful'),
              ('investigate', 'permit', 'careful'),
              ('go', 'office', 'careful'),
              ('copy', 'permit', 'careful'),
              ('look', '', 'careful'),
              ('unclear', '', 'careful'),
              ('rest', '', 'careful'),
          ])
      ),
  }

  def respond(text, pause=False):
    until(lambda: instance.session.snapshot()['pending'] or errors)
    assert not errors, errors
    request = instance.session.snapshot()['pending']
    if pause:
      instance.arm_pause()
    assert instance.session.submit(request['id'], text)
    until(
        lambda: errors
        or instance.controller.at_pause_boundary
        or (
            (p := instance.session.snapshot()['pending'])
            and p['id'] != request['id']
        )
    )
    assert not errors, errors
    return (
        instance.ledger.public(),
        instance.session.snapshot()['entries'][-1]['text'],
    )

  try:
    for index, action in enumerate(PATHS[args.path]):
      before = instance.ledger.public()
      started = time.monotonic()
      natural = not (
          action.split()[0].lower() in rules.VERBS and len(action.split()) <= 3
      )
      last = index == len(PATHS[args.path]) - 1
      after, first_response = respond(action, pause=last and not natural)
      proposed = after.get('proposal')
      proposal_state = after
      first_intent = proposed['intent'] if proposed else after['last_intent']
      expected = expected_by_path[args.path].get(index)
      accurate = not natural or (
          first_intent is not None
          and tuple(
              first_intent.get(key, '') for key in ('verb', 'target', 'method')
          )
          == expected
      )
      correction = None
      response = first_response
      if proposed:
        for key in ('turn', 'cash', 'location', 'evidence', 'injury', 'heat'):
          assert (
              after[key] == before[key]
          ), f'Proposal committed {key} before confirmation'
        after, response = respond(
            'confirm' if accurate else 'cancel', pause=last and accurate
        )
      if natural and not accurate:
        # Explicit reviewer correction, not model success or product fallback.
        # Preserve the failed first interpretation and measure it separately.
        assert expected is not None
        if expected[0] != 'unclear':
          correction = ' '.join(value for value in expected[:2] if value)
          if expected[2] != 'careful':
            correction += ' ' + expected[2]
          after, response = respond(correction, pause=last)
      transcript.append({
          'attempt': action,
          'first_response': first_response,
          'first_intent': first_intent,
          'first_interpretation_correct': accurate,
          'natural_language': natural,
          'reviewer_correction': correction,
          'proposal': proposed,
          'proposal_confirmed': bool(proposed and accurate),
          'state_before_confirmation': {
              key: proposal_state[key]
              for key in (
                  'turn',
                  'cash',
                  'location',
                  'evidence',
                  'injury',
                  'heat',
              )
          },
          'elapsed_seconds': round(time.monotonic() - started, 3),
          'response': response,
          'before': {k: v for k, v in before.items() if k != 'history'},
          'after': {k: v for k, v in after.items() if k != 'history'},
      })
      (args.output / 'transcript.json').write_text(
          json.dumps(transcript, indent=2)
      )
      if args.path == 'confession' and index == 7:
        assert after['iona_confessed'], 'Question still failed after correction'
      if args.path == 'confession' and index == 11:
        assert after[
            'iona_restitution'
        ], 'Payment still failed after correction'
      if args.path == 'opportunist' and index == 3:
        assert 'permit' in after['copies'], 'Copy still failed after correction'
      if args.path == 'refusal' and index == 0:
        assert after['case'] == 'declined'
      if args.path == 'intent':
        checks = {
            0: after['case'] == 'declined',
            1: after['location'] == 'records',
            2: 'permit' in after['evidence'],
            3: after['location'] == 'office',
            4: 'permit' in after['copies'],
            5: after['turn'] == before['turn'] and not after['published'],
            6: (
                after['turn'] == before['turn']
                and after['evidence'] == before['evidence']
            ),
            7: (
                after['turn'] == before['turn'] + 1
                and after['location'] == before['location']
            ),
        }
        assert checks[
            index
        ], f'Intended state not reached after review: {action}'
    until(lambda: instance.controller.at_pause_boundary or errors)
    instance.checkpoint()
    instance.export_log()
    state = instance.ledger.get_state()
    if args.path == 'compromise':
      passed = (
          state['relocation']
          and not state['stayed']
          and len(state['evidence']) == 1
          and 'secured copy pledged for Mutual relocation audit'
          in state['promises']
      )
    elif args.path == 'aftermath':
      passed = (
          state['stayed']
          and state['relief'] >= 4
          and 'safehouse: repay Nessa with a neighbourhood favour'
          not in state['debts']
          and state['jobs'].get('medicine') == 'complete:delivered'
      )
    elif args.path == 'intent':
      passed = True  # Every held-out intention checked before proceeding.
    elif args.path == 'confession':
      passed = (
          state['iona_confessed']
          and state['iona_restitution']
          and state['iona_testimony'] == 'voluntary'
          and state['ada_informed']
          and state['stayed']
      )
    elif args.path == 'opportunist':
      passed = (
          'permit' in state['copies']
          and state['settlement'] == 'self'
          and state['stayed']
          and not state['photo_exposed']
          and 'Mutual repayment: $35 after confidentiality breach'
          not in state['debts']
      )
    else:
      passed = (
          state['jobs'].get('medicine') == 'complete:delivered'
          and state['case'] == 'declined'
          and 'ledger' in state['known_leads']
          and 'ledger' not in state['evidence']
      )
    natural_trials = [
        entry for entry in transcript if entry['natural_language']
    ]
    semantics = {
        'correct': sum(
            entry['first_interpretation_correct'] for entry in natural_trials
        ),
        'total': len(natural_trials),
    }
    result = {
        'first_try_semantics': semantics,
        'reviewer_corrections': [
            entry['reviewer_correction']
            for entry in transcript
            if entry['reviewer_correction']
        ],
        'backend': args.model,
        'path': args.path,
        'passed': passed,
        'state': state,
        'npc_valid_actions': state['agendas'],
        'errors': errors,
    }
    (args.output / 'result.json').write_text(json.dumps(result, indent=2))
    assert passed, {
        k: state[k]
        for k in (
            'cash',
            'case',
            'settlement',
            'iona_confessed',
            'iona_restitution',
            'iona_testimony',
            'jobs',
        )
    }
    print(
        'LIVE REVIEW STATE PASS',
        args.path,
        state['agendas'],
        'first_try_semantics',
        semantics,
    )
  finally:
    instance.controller.stop()
    instance.session.finish('Review complete.')
    worker.join(65)
    (args.output / 'driver-status.json').write_text(
        json.dumps(
            {
                'errors': errors,
                'alive': worker.is_alive(),
                'attempts': len(transcript),
                'state': instance.ledger.public(),
            },
            indent=2,
        )
    )


if __name__ == '__main__':
  main()

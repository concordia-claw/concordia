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

"""Original Rain Ledger scenario content; no licensed setting or rules."""

PLAYER = 'Rowan Vale'
GM = 'Port Mercy'
OPENING = """The envelope contains six dollars and a photograph of a woman repairing a clock.

“Find my sister before the city finds her,” says Ada Saye. She has brought her own chair; you sold the spare last Thursday. Her sister Iona kept accounts for Harbour Mutual. Three streets in the Narrows have just been condemned. Iona has vanished with the inspection ledger.

Outside your office, a tram conductor argues with a boy over a fare neither can afford. On your desk are two other offers: recover a dockworker's pawned tools, or photograph a councillor's midnight visitor. You have $18, a camera, a lock pick and an office paid through tomorrow. You have accepted nothing yet.

Ada will wait at the Lantern café. You can follow her, take other work, or walk away. Nobody has bought your answer."""
PLACES = {
    'office': (
        'Vale Investigations',
        (
            'Burnt coffee. The frosted door still bears your former partner’s'
            ' name beneath yours.'
        ),
        ['cafe', 'docks', 'records'],
    ),
    'cafe': (
        'The Lantern',
        (
            'Nessa turns the cups handle-first. Men who carry guns tend to'
            ' notice small courtesies.'
        ),
        ['office', 'narrows', 'clinic'],
    ),
    'docks': (
        'North Quay',
        (
            'A winch counts its teeth against a chain. The hiring chalkboard'
            ' has more names than hooks.'
        ),
        ['office', 'warehouse', 'press'],
    ),
    'records': (
        'Municipal Records',
        (
            'A green lamp makes every hand look ill. Carbon copies smell'
            ' sweeter than the originals.'
        ),
        ['office', 'mutual'],
    ),
    'narrows': (
        'The Narrows',
        (
            'Doorframes carry pencil marks recording children’s heights.'
            ' Surveyors have chalked red crosses over them.'
        ),
        ['cafe', 'warehouse', 'clinic'],
    ),
    'warehouse': (
        'Bond Store Nine',
        (
            'Rope, orange peel, river mud. A boarded counting window overlooks'
            ' a locked desk.'
        ),
        ['docks', 'narrows'],
    ),
    'press': (
        'The Evening Wire',
        (
            'Typesetters eat above the cases so crumbs fall between letters. An'
            ' empty front page waits on a stone.'
        ),
        ['docks', 'mutual'],
    ),
    'mutual': (
        'Harbour Mutual',
        (
            'The lobby clock runs four minutes fast. Claimants are always late;'
            ' premiums never are.'
        ),
        ['records', 'press'],
    ),
    'clinic': (
        'Saint Orra Clinic',
        (
            'Boiled linen hangs beside boxing gloves. Doctor Pell accepts'
            ' money, labour, or an honest debt.'
        ),
        ['cafe', 'narrows'],
    ),
}
CONTACTS = {
    'ada': (
        'Ada Saye',
        'cafe',
        (
            'A tram mechanic. Counts promises precisely. Wants Iona safe, even'
            ' if the insurance case dies.'
        ),
    ),
    'nessa': (
        'Nessa Rook',
        'cafe',
        (
            'Café proprietor and neighbourhood organiser. Hospitality is a'
            ' decision, never a reflex. Needs safe homes, fears a panic.'
        ),
    ),
    'silas': (
        'Silas Marr',
        'docks',
        (
            'Union dispatcher. Short sentences, dry humour. Wants wages'
            ' restored; has concealed dangerous work to keep men employed.'
        ),
    ),
    'vera': (
        'Vera Quill',
        'press',
        (
            'Reporter. Asks for dates before adjectives. Wants a defensible'
            ' story and refuses to print unsupported accusations.'
        ),
    ),
    'holt': (
        'Edwin Holt',
        'mutual',
        (
            'Mutual assessor. Polite complete sentences. Wants a solvent'
            ' company and a pension for his sick husband; can sacrifice'
            ' directors if his signature is protected.'
        ),
    ),
    'pell': (
        'Doctor Pell',
        'clinic',
        (
            'Tired, direct, kind without softness. Protects patients and keeps'
            ' their names off police forms.'
        ),
    ),
    'iona': (
        'Iona Saye',
        'warehouse',
        (
            'Bookkeeper. Speaks in corrections. Hid fraudulent valuations but'
            ' also signed one herself to fund her mother’s care.'
        ),
    ),
}
EVIDENCE = {
    'permit': {
        'place': 'records',
        'source': 'Municipal duplicate register, folio 81',
        'text': (
            'Demolition permits were dated eleven days before the structural'
            ' survey.'
        ),
        'credibility': 2,
        'kind': 'document',
    },
    'ledger': {
        'place': 'warehouse',
        'source': 'Iona’s original counter-ledger',
        'text': (
            'Harbour Mutual insured vacant properties as occupied, then'
            ' borrowed against the inflated premiums.'
        ),
        'credibility': 3,
        'kind': 'document',
    },
    'testimony': {
        'place': 'cafe',
        'source': 'Ada’s signed account of Iona’s last visit',
        'text': (
            'Iona named the inspection office and left a duplicate policy'
            ' number: 4407.'
        ),
        'credibility': 1,
        'kind': 'witness',
    },
    'carbon': {
        'place': 'mutual',
        'source': 'Holt’s carbon of policy 4407',
        'text': (
            'Director Creel authorised the demolition rider; Holt countersigned'
            ' under a personal guarantee.'
        ),
        'credibility': 2,
        'kind': 'document',
    },
    'manifest': {
        'place': 'docks',
        'source': 'Union loading tally signed by two stevedores',
        'text': (
            'Demolition charges were unloaded before the neighbourhood was'
            ' declared unsafe.'
        ),
        'credibility': 2,
        'kind': 'document',
    },
}
JOBS = {
    'tools': {
        'place': 'docks',
        'pay': 12,
        'description': (
            'Get Silas’s crew tools released from the pawn cage. Negotiate a'
            ' union guarantee, pay $5, or steal them.'
        ),
    },
    'photograph': {
        'place': 'mutual',
        'pay': 20,
        'description': (
            'Photograph the councillor’s visitor. A patient’s family is meeting'
            ' him for medicine vouchers. Sell the photograph, warn them, or'
            ' return an empty envelope.'
        ),
    },
    'medicine': {
        'place': 'clinic',
        'pay': 9,
        'description': (
            'Deliver refrigerated medicine through the Narrows. Earn cash or'
            ' ask Pell to treat an injury instead.'
        ),
    },
}
NPCS = {
    'Nessa Rook': {
        'home': 'cafe',
        'goal': (
            'Keep the Narrows housed without frightening families into the'
            ' street.'
        ),
        'knowledge': (
            'Condemnation notices have arrived. Ada asks after her sister. You'
            ' know nothing about insurance accounts.'
        ),
        'moves': ['organise', 'shelter'],
        'voice': 'Practical, warm, refuses grand speeches.',
    },
    'Silas Marr': {
        'home': 'docks',
        'goal': 'Secure crew wages and keep the union independent.',
        'knowledge': (
            'Charges arrived before the survey. You signed the loading tally.'
            ' You concealed one unsafe shift.'
        ),
        'moves': ['petition', 'guard'],
        'voice': 'Dry humour, brief sentences, concrete prices.',
    },
    'Edwin Holt': {
        'home': 'mutual',
        'goal': (
            'Keep your pension and your husband’s treatment; avoid mass'
            ' evictions if possible.'
        ),
        'knowledge': (
            'You countersigned policy4407. Creel ordered inflated valuations. A'
            ' missing bookkeeper may expose your guarantee.'
        ),
        'moves': ['audit', 'offer'],
        'voice': 'Courteous, cautious, speaks in complete sentences.',
    },
}

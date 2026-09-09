# A night at Bellwether

You are the emergency coordinator of a small island community. The game runs
from **Dusk → High Tide → Before Dawn → dawn**, with four consequential choices
per watch. Looking at the coastal map and resident cards is free. A refused
request may cost a choice; an ambiguous command does not.

This is a fictional interactive scenario demonstrating standard Concordia
composition, not a model validated against human behavior. The original
one-turn `--mode slice` remains available; it is not the full game.

## Start from this contribution's source checkout

```sh
python -m pip install -e '.[dev]'
python -m concordia.examples.bellwether.run --mode fixture --editor-port 8786 --player-port 8787 --output runs/bellwether-fixture
```

Open <http://127.0.0.1:8787> to play and <http://127.0.0.1:8786> for the
developer editor. **Begin the night** (or the editor's `run.start`) starts
exactly one run. Reopening a tab does not restart it. The fixture banner denotes
deliberately cooperative, programmed responses, never a live model.

For live residents, first make an existing local Ollama model available:

```sh
python -m concordia.examples.bellwether.run --mode live --model llama3.2:3b --resident-prefab minimal --editor-port 8786 --player-port 8787 --output runs/bellwether-live
```

No paid backend is required. This command uses the existing Ollama adapter;
requests have a 90-second HTTP timeout, 256 output-token cap, and a 256-call
wrapper limit. The standard per-run profiler records timings and token
**estimates**, not measured billing. Exhausted/invalid output cannot grant
consent. Model failures end the run with the retained journal and developer
error; there is no hidden fixture fallback. Use Ctrl-C to close the owned
listeners. A new process starts a new night; checkpoint continuation is not
implemented by this example.

The standard `basic` prefab is an alternative via `--resident-prefab basic`.
Its perception components make additional model calls. Four residents share the
selected architecture but have separate standard memory, observations, goals,
accounts and affiliations. Developers can configure their individual instance
params in `game_prefab.configuration`. The human uses HumanAct, not an LLM.
The GM uses independently composed SwitchAct policies and explicit scenario
rules, not the resident decision logic.

## Playing

Select suggestions to fill the input, or enter a command and your own words.
There is deliberately a small, conservative physical-action vocabulary.
Unrecognized or ambiguous physical instructions ask for clarification **before**
waking the pending human turn. The parser is not a general natural-language
physical simulator.

| Intent | Example |
|---|---|
| Public conversation / open-ended proposal | `tell everyone: Can we find a plan that protects boats and families?` |
| Address one resident publicly | `tell Mara: What worries you about the cooperative?` |
| Private conversation | `message Nell: I want to hear your account.` |
| Ask for material consent | `ask Nell for fuel and part` |
| Ask for labor consent | `ask Ivo to repair` |
| Collect the agreed resources | `transfer reserve and part` |
| Ask Ivo to carry out accepted work | `order repair` |
| Allocate this watch's supply | `allocate all` or `allocate shelter and cold store` |
| Make your own promise | `promise shelter` |
| Withdraw your latest unfulfilled promise | `withdraw my promise` |
| Advance without agreement | `wait` |

`propose to everyone: …` preserves creative prose for resident discussion.
It cannot invent a new action mechanic or bypass resource/consent checks.
Residents respond in their own voices. An explicit structured `accept` records
only that resident's requested commitment; spoken claims alone are not consent.
Residents may decline, counter, or revoke their own unfulfilled commitment.
The next proposal can take their response into account; acceptance is not forced.

Nell's material commitment releases two fuel and the spare part. Collecting them
is a separate action. Ivo's labor commitment is distinct from performing the
repair: he may still refuse the work order. Repair requires accepted Ivo labor,
the delivered part, and actual performance **before Before Dawn**. A late repair
does not rewrite already-resolved services. General item trades and arbitrary
new engineering procedures are intentionally not silently adjudicated as valid.

## Material rules and two strategies

The generator has **6 fuel**, Nell has **2 reserve**, and there is **1 spare
part**. The beacon, shelter and cold store demand one fuel in each of three
watches: baseline demand 9. A completed repair removes only the final beacon
demand. The standard Inventory tracks Generator, Nell, Ivo and Used accounts;
fuel and the part never appear from narration. Requested allocation order
determines supply priority if there is insufficient fuel. Consumption occurs
at watch boundaries, after that choice's bounded resident responses.

Two useful plans, not guaranteed live social outcomes:

1. **Negotiate full service:** in Dusk ask Nell for fuel/part, collect them,
   ask Ivo to repair, then wait. In High Tide order the accepted repair;
   leave all facilities allocated and use the other choices for promises or
   discussion. Keep all allocated Before Dawn. With Nell's acceptance and
   Ivo's accepted **and performed** work, 8 fuel supplies all 9 facility-watches.
2. **Prioritize shelter and livelihoods:** allocate shelter and cold store in
   each watch. This consumes 6 fuel, leaves Nell's reserve untouched, but
   records three missed beacon watches and the associated harbor consequences.

The fixture demonstrates both. Live residents can defeat either social plan
through refusal or changed commitments. Waiting always allows progression to
dawn even without agreement. Dawn shows actual service, fuel, repair,
honored/broken/revoked/unfulfilled commitments, and each resident's response.
Missed beacon service delays safe arrivals; missed shelter service removes
heating; missed cold-store service risks stock. These are explicit fictional
scenario consequences, not predicted casualties or economic estimates.

At High Tide a **disputed** account of the previous storm is delivered to its
configured recipients. It does not establish objective truth or rewrite
memory. Use `--dispute-file account.json`:

```json
{"text": "Mara says the cooperative did not help; Nell disputes that account.", "recipients": ["Coordinator", "Mara", "Nell"]}
```

The object is validated before building. Institutions distinguish charter,
membership, enforcement and who knows about the disputed account. The default
delegates reserve custody to Nell and labor consent to Ivo; membership does not
grant someone else's consent. Interaction records describe changing positions
without imposing scalar trust or a single psychological theory.

## One service, three clients

The existing `OperationService`, `SimulationServer` and attached
`concordia-session` CLI remain the authority. The player GUI uses the same
`human.respond` handler available on its listener. Developer GUI/CLI edits use
the same designated `component.edit` as [the original slice](README.md).

Additional operations:

| Operation | Audience | Meaning |
|---|---|---|
| `game.begin` | player | Explicit one-time start |
| `game.preview` | player/developer | Parse an attempt without effects |
| `run.resume` | developer | Resume the existing paused worker; never replay |

```sh
concordia-session --url http://127.0.0.1:8786 discover
concordia-session --url http://127.0.0.1:8786 state
concordia-session --url http://127.0.0.1:8786 watch
concordia-session --url http://127.0.0.1:8787 state
```

A mutation uses the discovered arguments plus the current references/revision
and an exact retry key, as in README.md. Retry the identical request after a
lost response; stale edits fail atomically. Selecting Pause does **not** permit
editing while a worker or human request is still active. The designated edit is
safe before Run or after the worker has joined. Initial configuration remains
distinct from runtime. This is not a general mid-run transaction or checkpoint
interface.

Player HTML/JSON/SSE contain only public facts, the coordinator's delivered
observations and messages they participated in. The standard observation queue
separately delivers private events to the relevant residents. Developer
checkpoints and traces stay on the trusted editor listener; they are never
hidden in player HTML. Both listeners bind to loopback. This example changes no
routes, account configuration, lobbies or access controls.

## Verification and limits

```sh
python -m pip install pytest playwright
python -m playwright install chromium
python -m pytest -n 0 concordia/examples/bellwether concordia/contrib/language_models/ollama/ollama_model_test.py
```

Rule tests exercise conservation, both strategies, refusal, commitment
revocation, late/missing-part repairs, malformed resident output, atomic
clarification, recipient privacy and fresh ownership. Chromium tests use real
components, HTTP, SSE and attached CLI with a synthetic pending input and
explicitly forbid simulation execution.

Separate browser walkthroughs executed both complete fixture strategies and a
local live night through standard Simulation/Sequential: 12 human choices each,
four dawn responses, reload/reconnect recovery, matching CLI snapshots and no
JavaScript errors. The live run used 12 successful local llama3.2:3b calls
(about 2.9–6.0 seconds each); Nell declined and no reserve transfer or repair
was fabricated. Live timing is one machine/run observation, not a guarantee.
Automated browser submission timing is not a human play-duration measurement.

Logs are standard `simulation.json` and `log.html`; `outcome.json` adds
the explicit night result, per-step timings, model profile and backend label.
The 15–25 minute human experience is a target, **not yet measured**. The full
Bellwether editor/showcase A–H, isolated checkpoint branches, experiments,
authoring assets/undo/breakpoints, every editor-family parity and fresh
environment export remain subsequent work. No original workflow acceptance
baseline is upgraded merely because this bounded game now reaches dawn.

### Standard basic extensions

The optional basic residents retain their standard perception chain and normal
ConcatAct policy. `basic.Entity` now supports `extra_components` and
`extra_components_index` using the **same extracted assembly helper** as
`minimal.Entity`; basic defaults and minimal insertion semantics are unchanged.
This supplies each resident’s account, affiliations, and scenario instructions
without copying the basic prefab or silently ignoring configuration. Default
and injected-policy regressions accompany both advertised configurations.


## Two human roles

See [MULTIPLAYER.md](MULTIPLAYER.md) for optional host-approved Coordinator/Nell
play, private role journals, Android controls, and the HTTPS boundary. Omit
`--multiplayer` for the unchanged single-human game.

## Optional voice

[Local voice controls](VOICE.md) add opt-in spoken observations and editable
dictation on supported devices, retaining full text fallback. Android on-device
recognition is not assumed.

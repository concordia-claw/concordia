# The Rain Ledger

An original human-playable noir experiment in Port Mercy, a postwar port city.
You are Rowan Vale, a private investigator with $18 and an office paid through
tomorrow. A missing bookkeeper might expose condemned-neighbourhood insurance
fraud. You can refuse her sister's request, make a living, take a compromise,
protect a witness, publish a case, or return after doing something you regret.

This is an evolving example, not a claim of parity with a commercial RPG.
Its supported actions have explicit, inspectable consequences; a local model
interprets ordinary language and chooses resident agendas. It does not grant
arbitrary invented powers or treat generated prose as authoritative state.

## Run locally

This branch depends on existing unmerged editor/human-input work. The focused
example diff begins at `dependency/rain-ledger-20261007` (5ec148a): editor example
c088f42/source358020f, existing Astral human-example commits9fd5ce2/38b68ea,
configurable Astral transport from One More Song, and the bounded Ollama adapter
from PR356. These are reused dependencies, not new Rain Ledger implementations.
The existing `project-editor-engines-and-games` launcher was inspected; this
example composes the same standard async engine directly because it has human
input and scenario state, rather than adding another generic editor launcher.

Use a Python3.12+ environment with Concordia and the optional Ollama, FastAPI and
uvicorn dependencies already installed. From the repository root:

```sh
python -m concordia.examples.rain_ledger.run \
  --output runs/my-rain-ledger --model llama3.2:3b \
  --port 8795 --editor-port 8796
```

The model must already exist in local Ollama. There is no paid fallback, model
download, credential change or global configuration change. Requests have a
60-second timeout and180-token output cap. Human input itself makes no model
call until submitted. Bindings are loopback-only. A trusted tailnet reverse proxy
may expose **the player port only**; allow its hostname with `--allowed-host`.
Never expose the developer listener: it includes full simulation state.

## Play

The opening and casebook explain the immediate situation. Write one attempt in
your own words, or edit a suggestion before submitting. Exact shorthand also
works: `go cafe`, `talk ada`, `promise ada`, `investigate permit`,
`job tools bargain`, `copy permit`, `barter holt`, `deliver medicine`.
Some jobs first reveal a decision and ask for a second commitment.

The neighbourhood has nine connected stops. Explore contacts at their normal
workplaces. The job board contains the advertised offer, not the concealed
complication. A clue must be learned before it can be pursued. Documents retain
their provenance; a duplicate is useful collateral but never a new witness.

Looking and ordinary conversation are free. Travel, work, risk and waiting
commit fictional time. Every eight commitments the office charges up to $3;
unpaid upkeep becomes an obligation. Injury blocks force and high heat blocks
covert entry; meals, rest and clinical work offer recovery. There is no death
screen or compulsory main-case ending. Institution-level outcomes coexist:
a demolition stay cannot be overwritten by a later private payment.

Three residents have independent standard Asynchronous loops. Each can act at
most once per newly observed player commitment, with no catch-up burst. No
wall-clock deadline punishes reading, typing or disconnection. Resident actions
change beds, petition support, record access, security and settlement offers.
Their model context contains their own goals/knowledge, witnessed local events
and explicitly circulated news, not the whole investigator casebook.

Dialogue and improvisation remain limited. Supported exchanges and investigative
methods have grounded effects; unknown proposals ask for clarification without
spending time. Character speech is generated from a scoped binding response and
cannot change finances, evidence or other characters' actions. Language quality
must be evaluated with real local runs, not deterministic fixtures.

## Saves, pauses and developer operations

Reloading reconnects to the same HumanSession request and never automatically
replays a submitted action. Draft storage is the existing browser transport.
A completed scenario action saves `ledger.json`; explicit `--resume` restores
that scenario state. Pending input receives a new ID after a process restart.
This is distinct from a full standard checkpoint: it does not restore model RNG
or all actor memory. For a full supported component/log snapshot, use the
standard checkpoint operation at an acknowledged boundary.

A pause request is **not** quiescence. A human waiting in HumanActComponent is
still mid-step. Press **Pause after my next action**, submit the genuine action
you intended, then wait for `quiescent: true` in developer status. At this
boundary the standard controller excludes resume while an edit/checkpoint runs.
No empty or fabricated human action is used to drain the engine.

Discover the actual operations through the standard CLI:

```sh
python -m concordia.command_line_interface.concordia_session \
  --url http://127.0.0.1:8796 discover
```

Registered operations: `session.inspect`, `run.status`, `run.pause`,
`run.pause_after_action`, `run.resume`, `ledger.cash`, `checkpoint.save`,
`log.export`. The shared OperationService supplies references, revisions and
idempotency checks. `ledger.cash` accepts an integer from0 through10000 and only
runs under `StepController.paused_boundary()`. Other arbitrary live world edits
are not advertised by this example.

`log.export` and checkpoint capture use standard engine log materialization
only after actual quiescence. The generated `simulation.json` is a standard
SimulationLog. Search and share it with the existing offline CLI:

```sh
python -m concordia.command_line_interface.concordia_log --json \
  search runs/my-rain-ledger/simulation.json ledger
python -m concordia.command_line_interface.concordia_log \
  bundle runs/my-rain-ledger/simulation.json --output ledger-log.html
```

Restore a checkpoint as an isolated branch into a **new output directory**:

```sh
python -m concordia.examples.rain_ledger.run \
  --checkpoint runs/my-rain-ledger/checkpoints/step_10_checkpoint.json \
  --output runs/alternate-rain-ledger --port 8797 --editor-port 8798
```

The path and step above are illustrative; use an actual saved file. There is no
invented live `branch` command. Generic checkpoint restoration restores component
state and logs, not deterministic engine cursors or model sampling.

## Evidence and honest capability matrix

| Capability | Evidence / current limit |
|---|---|
| Actual concurrent standard engine | smoke001: all3 NPC loops plus human acted; standard log/checkpoint |
| Safe pause and edit | pending human rejects edit; pause-after-committed-action reaches boundary; cash edit succeeds |
| Retry/reconnect | duplicate submission no-op in smoke; real Chromium reload retains request/draft without advancing turn |
| Persistent consequences | rule transcripts for altruist, opportunist, refusal, betrayal/repair and copied-evidence bargain |
| NPC choice effects | rule tests distinguish shelter/organise; bounded opportunity and private-context tests |
| Local model quality | real-model playtest pending; scripted tests make no quality claim |
| Natural-language freedom | scoped interpretation of supported affordances; unbounded roleplay is not implemented |
| CLI discovery | demonstrated against live developer listener |
| Logs/search/export | standard smoke log searched and bundled; live export awaits final run verification |
| Restore/branch | standard loader restored smoke checkpoint in isolated instance; edited branch left source unchanged; model/engine cursors are not replayed |
| Mobile browser | actual Chromium390x844 screenshots and reconnect check; physical Android untested |
| Tailnet | coordinator owns isolated route; final URL/HTTP verification pending |

## Development checks

These rule checks do **not** launch an engine or call a model:

```sh
python -m unittest concordia.examples.rain_ledger.rules_test -v
python -m concordia.examples.rain_ledger.design_probe --output runs/design-review
```

`smoke` launches the actual Asynchronous engine. Its default model is explicitly
scripted; `--live` uses existing local llama3.2:3b with a40-call cap. Follow the
workspace's simulation-launch acknowledgement procedure before running it.

All game-specific mechanics live in Ledger, a standard ContextComponent;
PortAuthority extends standard SwitchAct hooks; FixedActionSpec/Constant retain standard routing contracts. ResidentAct implements the standard ActingComponent contract.
Standard minimal prefabs supply memory/context, generic.Simulation supplies
composition/checkpoints, ReactiveMeasurements and AsyncLogCollector supply logs,
StepController supplies boundaries, and HumanSession/its unchanged browser JS
supply input and reconnect. No engine files or provider defaults are changed.

# The Rain Ledger — evidenced design iterations

## Baseline, rule play and actual-engine fixture (2026-10-07)
Evidence: worktree `runs/design-baseline/{altruist,opportunist,refusal}.json` contains every action, exact response, before and after ledger. These are deterministic rule plays, NOT LLM quality tests. `runs/smoke-001/evidence.json` and `simulation.json` are actual standard Asynchronous output from acknowledged request rain-001; 10 completed actions across Rowan plus all three residents, actor-scoped NPC turns5. Human duplicate POST-equivalent submission no-op, edit rejected with pending input despite pause, pause-after-real-action reaches true boundary, cash changed to27, standard checkpoint saved. Engine stop at boundary returned normally. No engine implementation changed.

### Cycle1 diagnosis — promises, source safety and institutional consequences
Played altruist publishes redacted after corroboration: final cash21, turn18, stay and one relief parcel. Played opportunist sells photograph, takes retainer and publishes: cash76, turn14. Refusal remains viable: cash39, turn14, main ledger lead fails. Most serious experiential weakness: baseline `help pell` pays and heals identically even after selling a patient's photo; `talk ada` repeats initial offer after named publication. Evidence was a numeric gate, so naming only public records wrongly endangered Iona. Coordinator also found initial contacts disclosed missing Iona's address/motive.

Chosen redesign: hidden-contact/job projection; only learned clue targets; distinct source exposure; Ada access closes on source betrayal and reopens only after visible relief plus apology (broken promise stays). Photograph sale has explicit public distribution route; Pell's lost paid access requires an unpaid correction round. Injury/heat now constrain risky methods and preserve recovery alternatives. Separate demolition stay, relocation funding and relief counters prevent later settlement erasing an earlier institutional result. All-public records can support publication without naming an uninvolved witness.

Replay: pending focused consequence checks and updated contrasting transcript below. No claim of LLM quality from rule-level changes.

Highest-impact remaining weaknesses: NPC move choice currently cosmetic; jobs still resolve instantly; dialogue is too fixed; improvisation limited to supported intents; full player save restoration/browser screenshots/real inference pending.

### Cycle1 replay result
Six executed tests in rules_test.ConsequencesTest prove source-aware exposure, durable public stay through private payment, initial spoiler projection, method constraints, and earned Ada repair. Full replay in design-cycle2/betrayal_repair.json: `talk ada` -> “Ada leaves your cup untouched”; immediate `apologize ada` fails; after help families, apology -> “I can speak to you. That isn’t the same as trusting you with her name again.” Cash9/turn17; broken promise retained. This is actual rule-level response/state evidence, not model dialogue.

### Cycle2 — jobs and alternative leverage
Baseline diagnosis: tools/photograph/medicine all finished on one click at their starting address, giving no decision after learning stakes and claiming journeys never taken. Copying papers could not change negotiations; evidence was only collected for final gates.

Redesign: tools now exposes pawn price, guarantee obligation and risky alternatives before settlement; photo stakeout reveals the patient-family issue before sale/warning; medicine becomes a carried case and pays on delivery in the Narrows. A photographic duplicate cannot count as independent evidence, but securing a copy enables a lower-evidence relocation bargain with Holt. No magical extra source created. NPC action selection also now changes specific opportunities (beds versus petition; tally publication versus guard deployment; audit/security versus a bond offer), with exact effects still needing real-model play.

Played replays: `runs/design-cycle2/*.json`, five paths, before/after state per action. Refusal delivers the cold case and discharges the tool guarantee; cash33/turn14, no mandatory central case. Altruist retains source anonymity, obtains stay and delivers relief; cash30/turn22. Opportunist photo sale circulates a copy under Rowan’s byline (explicit information route), Pell refuses ordinary paid work until unpaid correction round; then next paid route yields6. Copy-bargain path spends a turn making one duplicate, trades collateral for access, obtains relocation with one source, and still fails Vera’s two-source gate. This creates a viable compromise without pretending it proves the whole conspiracy.

Remaining design shortcoming: ordinary `talk` still repeats authored lines and expressive improvisation is bounded to known affordances. Next cycle must use real local model attempts and inspect misclassification, scope and resident action quality. No claims of commercial-game equivalence.

## Early mobile browser evidence
Read-only real Chromium at390x844: mobile-opening.png and mobile-composer.png inspected; no horizontal overflow or JS exceptions; draft survives reload; pending ID unchanged; player turn remains0. Existing standard transport JavaScript served unchanged. Physical Android keyboard/device remains UNTESTED. Clean human001 has not been played by this worker.

### Cycle3 — conflicting allegiance must cost something after the cheque clears
Played cycle2 opportunist path exposed an economic/moral loophole: accepting $35, then publishing anyway gave both pay and public benefit; Nessa's reduced trust alone did little to alter that path. Highest-impact redesign: show Holt's confidentiality clause before signing, then require the player's explicit second commitment. Publication stays possible after payment, but now creates the disclosed $35 repayment obligation, +2 legal heat and a damaged Holt relationship. Relocation bonds remain a separate humane compromise and cannot erase a previously imposed stay.

Replay: design-cycle3/opportunist.json records terms -> signature -> publication -> demand. Same final cash73/turn16 as prior route, but now durable repayment debt and two additional heat (three total, including the photograph sale); public inquiry still stands. Altruist/refusal/repair/copy-bargain replays stay viable. This is not a forced loyalty lock: changed allegiance is supported with consequences. Pending follow-up: debt needs a player repayment affordance, and final real-model quality/cadence evidence still requires coordinator ACK003.

Standard checkpoint roundtrip was demonstrated without launching an engine: runs/checkpoint-restore-evidence.json. The standard loader restored smoke001 cash27, six committed turns and held ledger; a new isolated instance changed cash to44 without altering the source checkpoint. This proves component/log restoration, not deterministic sampling or engine cursor replay.

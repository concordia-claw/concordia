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

### Live interpretation and concurrency revision
Actual local llama3.2:3b runs003–006 are retained failures:003 rejected natural intents;004 accepted player intents but Nessa returned wrong JSON key;005 schema produced quoted strings;006 standard choice exhausted Nessa retries (InvalidResponseError), not a voluntary wait. Replaced bespoke resident JSON selection with standard ConcatAct CHOICE; reused existing PR378 bf6a141 adapter choice-contract fix, preserving PR356 bounds. Added explicit local affordance effects to actor observations. Live007 passes13completed actions, all3residents meaningful moves; CLI shows precise paused_boundary_required while human pending, then safe cash27 edit/checkpoint/export and resumed move with27 retained. This demonstrates mechanics and limited local-model behavior, not general narrative quality.

### Cycle4 — culpable witness, costly consent and personal aftermath
Diagnosis: main plot still culminated in a paper-count gate; Iona’s culpability was a static author note. New arc reveals her signed false valuation through a conversation, then separates shelter, $12 restitution, voluntary self-incrimination, Ada’s informed response and publication. Threats invalidate consent and the affidavit; independent public records remain available. Fifteen rule checks pass including actual cost, no repeated charge, and later hearing-summons dialogue.

Actual local-model play `runs/confession-008/transcript.json` exposed a more urgent agency failure: “Ask Iona why she took the ledger and what she herself signed” returned `{verb:ask,target:iona}` and no effect. Compensation returned `{verb:deliver,target:clinic}`, also rejected. The automated fixed path continued without consent and later exposed the witness; the final talk only then revealed the confession. This is a failed play, not a successful story demonstration. Chosen redesign: compact meaning-to-command examples in the existing interpreter, explicit distinction between questions/talk and compensation/medicine. Replay and additional unadvertised copy-bargain phrasing required before accepting this cycle.

### Cycle5 — interpretation must be reviewable, and a pass must mean the right action
009 exposed unsupported verb `photograph` for copying despite a prompt example. Standard choice constrained full affordances, but011 revealed a more serious scoring flaw: burn-and-frame chose copy (a no-op only because a copy already existed); rest chose travel. Its printed pass is withdrawn.013 also selected paid permit access without an offered payment.014 corrected the public-record method scope, understood3/4 intentions, then clarified own-office travel instead of acting. These are actual local-model transcripts, not mock defects; perfect semantic accuracy has not been achieved.

Chosen redesign: scene-grounded descriptions, standard InteractiveDocument canonical choice, player-visible review before commitment, same standard human input for confirm/cancel/correct, explicit method costs/risks, full proper destination names. No state-changing natural interpretation acts silently. Rule tests prove deliberately wrong travel proposal cancelled, then exact rest corrected; proposal survives save and cannot confirm twice. Next live measurement records exact verb/target/method first-try score separately from a completed path with explicit reviewer corrections. Confirmation safety is not semantic accuracy. Final phone browser must demonstrate the review interaction.

Cycle5 actual replay016: qwen3:8b nonthinking, exact first-try semantics6/8. Both errors proposed copying for negated-look/unsupported-destruction. Reviewer cancelled both before commitment, corrected look; rest then correctly stayed at office. Proposal zero-effects checks passed and pending review used the same standard async/human loop. Timings2.45–12.40s including confirm/cancel. This is success of review/correction safety, NOT semantic perfection; no claim unsupported action was implemented. Files runs/intent-016/transcript.json/result.json/simulation.json. Main concern remains parser quality, particularly negation and unsupported goals; review UI must stay visible.

### Cycles6–7 — actual contrasting stories and collateral leverage
Coordinator inspected live017 confession,018 opportunist,019 refusal,020 checkpoint aftermath and021 compromise transcripts. Each completed its asserted state path, with2/2 natural intentions in each (small samples; no general semantic-accuracy claim). Confession costs restitution and voluntary exposure; selfish retainer breach costs repayment and remembered distrust; refusal allows livelihood and later return without forced acceptance. Checkpoint aftermath preserves stay and obligations through paid delivery/recovery.

018 exposed public NPC invitation accidentally replacing the benefit of earned copy collateral. Redesign separates invitation from signed pledge.021 verifies a secured copy earns one-source relocation, while one-source publication is still refused. Families receive bonds without a confession and lose their neighbourhood; documents remain available for later investigation. This preserves leverage and distinguishes private bargaining from public proof.

020 also exposes weak generated voice: model repeats authored words and speaks stage directions. Generated prose presence is not success. Worker switched from unnecessary JSON to standard plain sample_text and added first-person constraints/logging; actual improved voice remains to be demonstrated. Revisit scene now incorporates neighbourhood state, addressing consequence visibility. Final mobile interaction and live component-motive intervention remain open review criteria.

### Cycle8 — mobile review, behavioral intervention and first-person reply
Actual023 standard-engine smoke passes12completions with local8B: current canonical-choice parser, unsafe edit precisely rejected, safe cash27/checkpoint/export/resume. Actual browser024 provides narrow Chromium390x844 typing/draft reload, proposal cancellation at turn0, confirmed travel to cafe at turn1, actual quiescence, CLI resident.goal change and Nessa choosing shelter after resume (beds0→2). Standard checkpoint step13 restores cash26, beds2 and edited Goal; isolated branch cash44 leaves source SHA256 unchanged. This offline restoration does not launch a simulation. Log CLI search and self-contained bundle succeeded.

Browser harness initially omitted Origin and got403; corrected request with fake stale ID got409. This is stale rejection, NOT identical duplicate proof (the latter remains smoke evidence). Harness also incorrectly expected cash27 after rest; ledger correctly records $1 rest, cash26. Failures and corrections remain in task browser scripts/logs.

Model failure: direct “Ada, is finding Iona safely more important to you than exposing Mutual?” proposed protect iona. It was cancelled at turn2 with no protection action. Explicit rephrasing “I ask Ada whether finding Iona safely matters more to her than exposing Mutual.” proposed talk ada, confirmed. Actual generated line: “Finding Iona safe is all that matters. Exposing Mutual isn’t worth the risk.” This adds subject-sensitive first-person speech instead of020’s copied stage directions, but one response is not broad voice validation. Original canonical facts remain separate and authoritative.

Screenshots expose Latest anchor landing below the prose; changed only scenario navigation to last story element. Replayed read-only browser screenshot now shows the actual resolved Ada exchange. Reduced-height390x440 screenshot shows composer/send accessible; this is a keyboard approximation, physical Android remains untested. No horizontal overflow or JS errors. Source review exposed100000 idle iterations could retire NPC loops after~5.5hours; raised example bound to1billion (~6years at0.2s idle) without engine changes.

Ranked further design work: (1) held-out indirect questions/negation/unsupported intentions remain unreliable, retain mandatory review; (2) broader scoped dialogue voice and contradictory-question tests; (3) consequences beyond current finite resident agendas, richer return visits and linked side jobs; (4) physical Android keyboard/network-loss validation. Current artifact is a substantial original playable draft, not commercial-game parity or completed north star.

### Delivery iteration — browser024 and live023
022 browser caught simple Lantern travel→Records semantic failure; cancelled withoutcommit. Revised run/review neutral instruction and standard sample_choice shortcommand values;023 actualengine + standardCLI safeedit/checkpoint/resume passed12completions. 024 browser got Lantern travel correct; actual390px draft/review/cancel/confirm/reload tested. HarnessCSP and missingOrigin defects fixed without productsecuritychanges. FakeexpiredID409 is stale rejection, not identicalretry; report does not conflate them.

At verifiedquiescence, CLI resident.goal delegates standard component setter; Nessa switched to shelter and opened2beds onresumedplay. Cash27 became26 after legitimate$1rest, not lostedit. Ada directquestion was first misread asprotect, cancelled; rephrasing selectedtalk. Standardlog actualspeech: "Finding Iona safe is all that matters. Exposing Mutual isn’t worth the risk." This answers subject and preservesmotive, unlike020 stage-direction repetition. Natural interpretation remains imperfect and confirmation remains essential.

Coordinator reviewed revised opening/proposal/390x440keyboard-height screenshots: storyvisiblefirstscreen, actioninput/buttons fit narrowviewport, nooverflow; physicalAndroid unverified. Humanservice polling bound raised using existing max_steps, noenginechange. Final durablehost and Tailscalecheck remain required before handoff.

### Cycle9 — recovery must create a playable obligation (2026-10-08)
Continuation preserves the published checkpoint and strengthens model evaluation rather than further tuning the game for small Ollama models. New held-out conversation path distinguishes questions/hypotheticals from commitments, including refusal and multi-action requests. Standard Together factory and existing call limiter reused;24logical calls requested for rain-025. Exhausted limiter fallbacks cannot count as real-model success. No paid/provider or engine call yet: matching coordinator acknowledgment remains pending. Inherited credential presence was checked without printing its value; protected egress is unverified, no auth/profile change or route bypass.

Independent rule-level play found a recovery dead end: at clinic, cash0/injury2, rest creates treatment credit; talk offers paid work; repay pell is rejected and help pell pays6 but cannot clear the debt. Source and actual non-engine transcript `runs/recovery-review-20261008/before.json` establish this is an inert permanent mark, not a meaningful obligation. Deferred rent also lacked an exact-parser target and a discoverable local affordance despite an existing repayment rule.

Chosen redesign uses existing debts, actions and schema2: Pell offers an optional unpaid clinic shift via repay pell. Paid help remains available and does not automatically confiscate wages; outstanding credit does not bar healing or work. The shift clears care owed, not photo harm. Suggest it only at the clinic while debt exists; expose existing rent repayment at the office and recognize its exact target. No new engine, scheduler, resource counter or persistence layer.

Replay `after.json`: rest cash0/debt; paid help cash6/debt; repay cash6/no debt; repeated repay no extra turn; next paid help cash12. Tests restore schema2 before repayment and preserve photo exposure, plus verify rent affordance/parser and actual payment.24rule tests pass, scoped lint/types pass. These are rule-level agency/recovery evidence, not live-model or fun-quality validation. Stronger-model conversational baseline and human device delivery remain pending separately.

### Cycle10 — choose what to disclose, then keep investigating
Offline baseline at a821401: acquire Ada testimony plus sufficient permit/manifest, promise her source safety, go to Vera. `publish named` automatically prints all three and exposes Iona/breaks the promise. There is no records-only dossier: `publish public` rejects. Before transcripts: runs/disclosure-review-20261008/before-{named,public_attempt}.json. Diagnosis: possessing private evidence takes away discretion; the investigator cannot distinguish ownership from disclosure. Vera’s stock two-source line also gives no actionable review of this actual folder.

Redesign: `publish records` offers only held permit/manifest/carbon; Saye ledger/testimony/affidavit stay private. Existing named and redacted modes remain distinct. Ledger._publication_case derives eligibility from selected evidence and provenance; no new save field or infrastructure. Talk Vera now previews exact sources, private material, readiness, source risk and confidentiality liability without committing time/cash/evidence. Hidden evidence cannot appear in that assessment. Withheld papers cannot silently satisfy the selected dossier’s proof requirement. Records-only publication still breaches a signed confidentiality clause.

Contrasting rule replays in final-replay/: records publishes permit+manifest, trustAda3, source unexposed; named publishes testimony too, trust-2, source exposed and broken promise. Both cash11/turn14 and demolition stayed; difference is who bears the cost. Refusal/rebuild path first fails with one permit (no cost/loss), returns for the paid tally, then succeeds at turn8. Schema2 restore test preserves the private testimony and source promise through publication.

Further played findings: safe-branch Ada still said “Start at Records” after publication; new aftermath acknowledges the public victory and unresolved safety while leaving the personal case optional. Public permit/tally findings previously became generic “insurance irregularities”; printed scope now follows offered records (premature demolition planning vs signed Mutual rider vs false occupancy/premiums). This avoids pretending a limited public case reveals the whole conspiracy.

### Cycle11 — a first story must not terminate investigation
Source/played review found published papers permanently disabled further publication. New dossier rule permits follow-ups when genuinely undisclosed evidence is added; previously printed material stays in the cumulative published set. No new papers means no turn, trust or money effect. One can keep investigating after the public-record victory and choose whether the fuller story names the source. Reviewing lists existing disclosures and cannot promise to undo them. Named-only reissuance without new evidence is intentionally unsupported, not silently performed.

Actual offline followup_redacted/named journeys start with the records story, then enter the warehouse, discover the ledger/confession and return to Vera. The first replay exposed an additive-trust bug: prior goodwill offset later betrayal to0, so Ada returned to the opening line. Redesign: a new nonconsensual exposure always closes access (trust<=-1); existing visible relief/apology repairs access, not privacy or the broken promise. Prior private conversation cannot bypass the refusal. Later safe publication cannot launder trust or erase an exposed name.

Repaired transcripts: runs/disclosure-review-20261008/followups-repaired/*.json; both cash8/turn20, cumulative permit/manifest/testimony/ledger. Redacted: source false/trust3. Named: source true/trust-1/broken promise; final Ada leaves the cup untouched. Repeating either publication costs0turns. Additional restore test publishes a new carbon after exposure and preserves cumulative papers, exposed identity, stay and damaged trust. Summary: evidence-summary.json.

30rule tests, scoped pyrefly0errors(4 existing prefab suppressions), pylint, formatter and diff checks pass. All new transcripts are deterministic Ledger actions: no engines or models launched, no LLM-quality claim, no physical Android evidence. Together held-out question baseline025 remains separately gated by protected egress+exactACK; no small-local-model substitute. Next substantive targets: negotiation/provenance consequences of coercive versus consensual acquisition, and scene-level NPC aftermath beyond finite agendas. New publication language also needs live natural-language/voice evaluation when permitted.


## Fork continuation — live conversational design cycle (2026-10-08)
Baseline98bbdec, prior offline46tests. Earlier external task records contain cycles12–18 (custody, collective relief/organising, contract consent, returning jobs, order-independent promises, durable clinic consequences); those changes are retained. User withdrew launch ACK requirement: display exact command/cwd/purpose before simulation, then proceed. Final server/routes remain coordinator-owned.

Real Together baseline025: standard Asynchronous, DeepSeek-V4.1-Flash,13logicalcalls,6/6held-out intentions correct,turn1/cash18/no promises,all3resident actors acted. TLS-verified HTTPX HEAD reached authorizedapi.together.xyz; installed SDK defaulted toapi.together.ai, so live_review now injects an SDK client pinned toxyz through existing Base adapter, SDKretries0. No adapter/engine/global config changed, no credential value inspected. This is actual inference, not the earlier local model.

Dialogue diagnosis from runs/conversation-025/transcript.json: Ada repeats her complete opening before each answer. Nessa offers rent, lock repairs and a solicitor as donation uses; these are unsupported. Ada wrongly implies a quiet settlement ends the search.
Redesign: scenario contact service facts scoped to the speaker; Nessa receives her actual shelter/representative counts. Speech receives binding service limits. Successful follow-up speech replaces an identical already-delivered authored ruling; new rulings and empty-generation fallback retain authored text. No hidden case truth or new memory/transport infrastructure.
Replay026:13logicalcalls,6/6first-try,unchangedresources,cleanexit. Nessa: “A donation buys food parcels for the Narrows, one evening each...” then describes company relief; no invented solicitors/rent. Ada’s later answers stand alone; quiet settlement answer preserves search/evidence and prioritises safety. Transcript/result/standardlog/checkpoints under runs/conversation-026.49offline tests plus scoped types/lint/format/diff pass. These four generated replies are targeted evidence, not proof of general conversational quality. Two runs total26logicalcalls; no provider invoice captured, no exact spend claim.

Next: duplicated Saye material currently adds credibility despite sharing one source family; preserve authentication and independent-corroboration alternatives. Broader held-out dialogue and new mobile states still need evaluation.


### Corroboration — stronger evidence, not repeated accounts
Before-bargain trace runs/corroboration-review-20261008/before-bargain.json: Ada account1 + covert Iona ledger1 + Holt carbon2 reached credibility4 even though the first two are the same source family. An earlier all-covert probe correctly failed and remains archived as before.json. Redesign uses the strongest item per family for both publication and existing negotiation checks. All possessed pages still survive; Vera explains the assessment. A weak ledger can be printed but does not alone justify an asserted finding of inflated premiums; the supported finding follows credible documents.
After traces runs/family-recovery-20261008: both initially fail freely. Independent public permit enables records-only publication while keeping Saye pages private (cash12/turn16). Protecting Iona and obtaining witnessed authentication instead supports named publication (cash12/turn20). Routes trade time, privacy and cooperation rather than forcing a single clue order.50offline rule tests,scoped types/lint/format/diff pass. No additional model calls for this mechanical replay.


### Held-out creditor review027 — mechanics pass, dialogue failure
Actual Together runs/return-work-027 used18logicalcalls (44total across025–027; USD not captured). End state: cash42/turn17,maincase declined,debts cleared,two medicine deliveries. First intentions only3/4: accepting the tools guarantee was classified unclear, then reviewer corrected job tools bargain. Silas claimed earlier delivery covered the new guarantee; Pell refused an available follow-up consignment. This is NOT an overall success despite the archived driver’s passed:true field. Prior evidence is preserved. Future driver now reports mechanics_passed/semantics_passed separately and requires both for passed/exit success.

Root cause: the action description omitted that accepting the guarantee and promising future delivery form one agreement; character prompts/rulings supplied opening dialogue without current creditor facts. Dirty edits now describe the future obligation, author the new order being sent to Pell, give correct outstanding/carried/discharged rulings, and record open barter/repayment as witnessed events at the local workplace. No private-conversation broadcast added.

Offline four-stage probe: runs/creditor-offline-20261008/transaction-order-probe.py and transaction-order-final.json. Uses Ledger/PortAuthority, standard get_state/set_state and mocked empty speech, no engine/provider. Ordinary delivery: turn6/$27/no debt. New tools guarantee: turn10/$36/separate debt. Pickup: turn14/$36/debt still owed. Later delivery: turn16/$42/debt cleared, main case declined. The no-debt statement before acceptance was correct. A separate proved prompt flaw was falsely describing an already-sent order before any guarantee and giving Silas unrelated clinic job status (before-scope.json). Corrected context conditionally includes the actual accepted order, exposes only each speaker’s own job register, and retains the shared guarantee status. Focused tests cover all four stages, scope and local witnessing. This validates supplied facts/authored responses, NOT generated dialogue after correction; no further paid call made.

### Android host handoff
Prepared isolated runs/android-demo-20261008-a/ledger.json atturn0/$18/emptyhistory using standard Ledger state. RainSession now gives an untouched restored save its original opening; played saves retain return presentation.52rule tests and scopedtypes/lint/format/diff/JSsyntax pass. Exact parent-only launch and sourcehashes in runs/fork-continuation-20261008/ANDROID-LAUNCH-REQUEST.txt and android-source-hashes.json. Worker did not launch any server/simulation or change Serve/routes. Parent reports existing10002->8795 and no listener. verify-android-host.py reuses prior narrowviewport harness and adds suggestion/draft/reload checks without submitting an action. It has NOT been run against the new host listener. Physical Android remains unverified.

Next priorities: parent host delivery/HTTP/tailnet/mobile evidence; then validate corrected creditor speech with a bounded strong-model replay only when spend review permits. Wider open-ended narrative remains a work in progress.

### Native recovery: refusal must not impersonate completed work (2026-10-09)

Offline transcript `runs/fork-continuation-20261008/declined-tools-before.json`:
`go docks → job tools → refuse tools → talk silas` produced “Every wrench is
back. The tally is open to you.” State was `complete:declined`, trust 0, no
union guarantee. This is a proved dialogue/affordance defect, separate from the
correct pre-acceptance no-debt fact in the earlier creditor probe. The broad
`complete:` check conflated rejection and successful service.

Ledger now acknowledges the rejected commission and offers paid/covert access.
A focused replay verifies that free access stays closed, no debt appears, and
paying $4 still yields the manifest. This preserves refusal as a viable route
without inventing earned goodwill. 56 rules/entrypoint tests pass; model speech
was not evaluated. The held-out rain-027 result remains only 3/4 semantic first
tries, with erroneous creditor speech, not an overall win.

Player configuration recovery also removes the stale Qwen launch instructions.
The Together-only entrypoint uses the standard adapter and protected xyz client;
mocked startup checks establish wiring, not live access or Android usability.
Next design target: clarity of pending proposals and reconnect on mobile, while
preserving the player's draft and avoiding accidental commitments.

### Android-first onboarding clarification (2026-10-09)

Source-path review found that suggestions fill an editable draft, but sending
exact shorthand commits immediately while natural-language interpretations wait
for confirmation. Only the hidden Guide explained the distinction. The composer
now states it directly, including Confirm/Cancel behavior, and associates that
help with the input for assistive reading. The work list also called both refused
and completed commissions SETTLED; it now distinguishes DECLINED and COMPLETED,
with owed follow-up orders retaining their separate label. These are presentation
corrections, not changes to action parsing or standard reconnect transport.

56 offline tests pass and JS syntax checks pass. Actual first-time mobile
comprehension remains untested. The coordinator has a single host procedure and
read-only browser check covering both local and tailnet origins; neither was
executed by the network-disabled worker. No Android link or provider access is
claimed. Next evaluate first-action comprehension and real generated responses
once protected host delivery exists; preserve the clean human save.

### Completed work should leave a useful record (2026-10-09)

Offline real-rule sequence `go cafe → go clinic → job medicine → go narrows →
deliver medicine` left `complete:delivered`, but RainSession.snapshot still
advertised “Carry cold medicine… Offered fee $9.” See job-board-before.json in
the fork continuation directory. The outcome label alone did not tell a returning
player what had changed or where ongoing work remained available.

Extended the existing JOB_PROGRESS content map with outcome-specific descriptions
for completed and declined jobs: paid delivery and ongoing clinic work, the union
promise, declined commission/paid tally alternative, and lasting photograph harm.
No new component or engine logic. Replay now gives paid-delivery aftermath and
`help pell`; accepting a new guarantee correctly replaces that with a new order
still owed. Two regression tests cover these transitions and tools refusal.
58 rules/entrypoint tests pass. This is offline state/presentation evidence, not
new model speech or human usability evidence. Changes are not loaded into the
coordinator's running host; preserve its clean save and process while diagnosing
tailnet TLS. Physical Android and tailnet HTTPS remain unverified.

### A receipt must not invent an earlier promise (attempt23)

The ordinary medicine path's authored receipt always said “your union guarantee
is discharged,” even before accepting tools work. Archived before-state/response:
`runs/fork-continuation-20261008/ordinary-delivery-before.json`. Debt state was
correct; narration invented a transaction. This offers a possible source of
confusing later character responses, but the held-out model failure's causal
origin has not been established.

Ledger now uses pre-delivery debt presence to select ordinary commission or
union-discharge wording. A regression replays ordinary delivery → new guarantee
→ later crew delivery, checking both receipts and debt state. 59 offline tests
pass. No live replay, host restart or engine change; updated source awaits a
future coordinator rollout. Tailnet TLS remains separately blocked, with no
verified phone URL and no available evidence identifying the TLS root cause.

### Return scenes should acknowledge consequences (attempt24)

Earlier review noted that the Narrows still showed only surveyor crosses after
a stay. An offline restored-state fixture with stay, signed relief and six
evenings of supplies confirmed identical opening arrival text; evidence:
`runs/fork-continuation-20261008/narrows-return-before.json`.

Ledger._place_description now supplies the same state-grounded description for
arrival and look: stay beside the remaining crosses, voluntary relocation when
funded, tenant relief administration, recorded supplies and frozen claims. It
keeps limits visible: temporary supplies do not promise permanent housing;
relocation alone does not imply a stay. No new effects, actor knowledge or engine
code. Two contrasting presentation regressions pass; total61 offline tests.
The replay is a fixture, not an earned full campaign or model-quality test.
After evidence is archived separately. Current live host remains unchanged;
phone TLS access is still unverified and separately checkpointed.

### Phone access before further narrative expansion

User-reported black screen contrasts with a complete no-submit390x844 localhost
opening. Historical authorized-device evidence favors443 reachability. Prepare
standard root_path support rather than changing the game's rendering blindly.
62 offline tests include both proxy prefix styles, canonical slash redirect and
all page-linked assets/state/journal without any submitted action. No actual
phone/path verification yet. Canonical /rain-ledger/ keeps relative navigation
inside the game while preserving OpenClawroot. The pristine save is unchanged;
standard draft storage naturally uses the new pathname, with no automatic draft
migration or transport rewrite. Existing aftermath/receipt regressions pass.
Next human-facing review remains actual phone access and first-move clarity;
offline route tests do not establish either live TLS or gameplay quality.

### Repeated negotiation must not become a signature (2026-10-11)

Actual offline path through Records/Mutual obtained permit/carbon and repeated
`settle self`. First invocation reviewed; second signed a$35 confidentiality
contract. The semantic label conflated negotiate and accept. Evidence lives in
`runs/fork-continuation-20261008/contract-review-before-20261011.json`.

Now review is repeatable and free. `settle self accept` signs after terms were
seen, matching relocation/relief consent patterns. Natural-language labels name
the binding payment, absence of family benefit and publication liability.
A deliberately wrong mocked selection for a refusal still produces a proposal,
not a signature; cancellation invalidates subsequent confirmation. This tests
consequence containment, not model comprehension. Updated intended acceptance
in existing offline/live drivers; archived past transcripts unchanged.

63 tests pass, including default/prefixed ASGI checks without an engine. Existing
rule paths replayed separately; opportunist payment, breach debt and public stay
remain reachable. Formatting, lint-errors and types pass. The live deployment was
not changed and paid semantic/voice evaluation remains gated by verified budget
and protected route. Save schema2 is unchanged; old saves restore, but repeated
`settle self` deliberately no longer signs. Future human documentation uses the
explicit acceptance command.

### Clinic appeal: an optional continuation of a limited public victory

2026-10-11 audit: `runs/hearing-continuation-20261011/reachable-before.json`
records an actual rule path that refused Ada's commission, obtained the public
permit/tally, published a stay, delivered medicine, then exercised resident
choices. Nessa and Holt exhausted their local work; Silas still had guard.
The docks offered the old tools commission but no response to frozen clinic
claims. This was a shallow aftermath, not total world inactivity. The initial
`before.json` is retained as a failed audit: it omitted talk silas, so no tally
or stay was earned. Only the corrected reachable trace supports the finding.

Design: link the existing signed medicine receipt to the public inquiry through
one optional clinic appeal. No Iona discovery, tools completion, settlement or
forced quest chain required. Reuse Ledger jobs, cash, union_support, relief,
news, persistent component state, and standard resident opportunity scheduling.
No new resource counter, save-schema key, engine, transport or logging system.
Free inspection explains $6 transport versus two union support and no personal
fee. Refusal leaves claims untouched. Insufficient union support preserves the
paid alternative. Completion releases two evenings of supplies once; it does
not settle other claims or erase witness/privacy/settlement consequences.
Using the union spends the same support available for guard intervention and
reopens Silas's existing petition action, giving him a reason to act again.

Second design pass addressed discoverability and returning conversation: both
publication/delivery orders announce job hearing when it unlocks; the work board
hides it beforehand. Silas recalls reviewed/resolved terms, and only his scoped
speech facts receive that job's details. No generated voice quality is claimed.

Paid, union-funded and refusal traces branch from the reachable audit in
`pay-after.json`, `bargain-after.json`, `decline-after.json`; each restores with
identical state. Four new focused tests cover early gating, repeated free review,
refusal, insufficient support, paid alternative, resource tradeoff, regained
resident affordance, one-shot completion, reversed unlock order and cancellation
of a natural payment proposal. 67 tests pass; types0errors/4existing suppressions,
scoped lint and diff checks clean. These are rules/ASGI/mocked-provider checks,
not an actual engine or human/model playtest. The city remains finite; this is
one substantive continuation, not a claim of an indefinitely reactive campaign.

## 2026-10-12: a failed interpretation must remain diagnosable and recoverable

Human evidence: `Go to the cafe` produced both an interpretation-unavailable
notice and an unclear-intent notice, while remaining at office/turn0/$18. The
four-word phrase correctly took natural interpretation rather than the exact
`go cafe` shortcut. The precise original exception was lost, so a provider,
transport or response-format cause cannot be ranked from the retained evidence.

Generic adapter review found strict matching in one model and unsafe substring
matching in others. The shared complete-value decoder now tolerates lossless
quoted/fenced/JSON choice wrappers and rejects ambiguous prose, negated choice
mentions and duplicate keys. This repairs a demonstrated response-contract gap;
it does not establish which failure occurred on the phone or prove semantics.

PortAuthority now emits one recoverable failure. Ledger history and the final
standard captured action log retain an allowlisted diagnostic category; raw
exception text is not logged. A stale proposal is discarded, preventing a later
confirmation from committing an unrelated earlier interpretation. Resources,
location and fictional time remain unchanged.

Evidence: 144 adapter fake-SDK tests and71 scenario tests (four new interpretation
contract tests) pass. Canned replies cover travel paraphrases, questions, refusal,
negation and unsupported multi-action input, original prompt preservation,
mandatory review/cancel, bounded retries and sanitized save/restore. They are
not held-out model accuracy results. Real protected-Together replay and mobile
review/cancel behavior remain pending; no user save or live service was changed.

Recovery follow-through: a fake-client PortAuthority replay now covers failure,
rephrased retry, fresh proposal, confirmation and repeated confirmation. The
retry remains at office/turn0/$18 until confirmation, then reaches cafe/turn1/$18
exactly once with only two fixture-provider requests. This addresses the next
onboarding risk: accidentally treating recovery as consent or charging twice.
All72 scenario tests pass. This is an offline control-flow replay, not a player
or real-model success claim; next evidence needed is protected provider testing
followed by authorized phone review/cancel and reconnect observation.

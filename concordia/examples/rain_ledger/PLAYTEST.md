# The Rain Ledger playtest contract

Objective: Make The Rain Ledger fun: a session a human would choose to continue.
Only Joel certifies that objective. Simulated players find weaknesses; they never
certify fun. Showcase constraints remain requirements, not a substitute objective.

## Showcase constraints and authority

Source of authority: existing programme `programmes/concordia/noir-20261007/`
TASK.md, REVIEW.md and REPORT.md, interpreted with the latest user instructions.
Their old local-model defaults, final-service commands and acknowledgment gates
are historical and do not override the current protected-Together/staging rules.

Keep an original noir port city, optional embedded main case, distinct motivated
NPCs, discoverable evidence/provenance, meaningful incompatible choices, persistent
consequences, recovery and worthwhile work beyond the main case. Keep onboarding
readable and mechanics learnable; failure should change opportunities. Standard
Asynchronous actor loops, scoped knowledge, authoritative inspectable state,
bounded world activity, review/cancel, safe human reconnect, standard CLI/logs and
mobile presentation remain constraints. No engine changes or parallel library
infrastructure. No licensed adaptation or commercial-game parity claims.

## Each cycle

Play at least three complete sessions through the real player interface with real
model calls, varied personas (impatient, thorough, contrarian, ignores main case),
and one additional held-out persona. The held-out session is an evaluation, never
a tuning target; rotate it after exposure. Keep original failed attempts and
corrections. Read one entire transcript as a critic, not only endpoint scores.

A complete session includes opening, a player-chosen purpose, pursuit of that
purpose, a meaningful consequence, and a voluntary continue/stop decision. Do not
truncate a session at the first passing assertion. A cost/time cap may interrupt a
session; record it as incomplete, never quietly count it toward the requirement.

Record:
- Longest stretch without a meaningful choice (actions and elapsed reading time).
- Misread/refused actions, first-try interpretations, corrections and cancellation.
- Consequences promised versus those actually surfaced in scene/NPC/UI feedback.
- NPC voice/motive drift with exact transcript quotations and scoped knowledge.
- Quoted tension/surprise and whether the player wanted to continue, with reasons.
- Decision opportunities, meaningful alternatives and evidence of optionality.

Select one change likely to improve the next playtest. Prefer player-visible
changes unless infrastructure is causing the pain. Implement focused regressions,
replay comparable sessions, retain negative evidence and revert if it did not help.
Passing tests and model approval are not proof of fun.

## Isolation and evidence

Use separate staging saves and loopback ports, never the live human service/save
or Tailscale routes. Coordinator executes real Together calls through its protected
Gateway. Never inspect or transfer credentials. Display exact simulation command,
cwd and purpose before launch. Use existing human transport/browser interface,
standard logs and state exports. Record commit, session, persona, command, request
bounds, real usage/cost when available, transcript and screenshots. Mocks validate
contracts only and do not fulfill a session. Keep TLS verification enabled.

No applicable protected staging executor/budget confirmation means real sessions
remain blocked, not replaced by mocks or a local model. Log obstacles and two
alternative routes in BLOCKED.md, then continue useful unblocked preparation.

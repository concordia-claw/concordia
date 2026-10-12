# Active playtest obstacles

2026-10-12: Goal #407 is active, not complete. These block items, not the Goal.

## Real-interface, real-model staging sessions

Evidence: native worker has no coordinator Gateway execution tool in its exposed
tool inventory. Current instructions reserve protected Together execution to the
coordinator. No new staging endpoint, verified remaining budget or usage record
has been supplied. Existing live human backend is explicitly not staging.

Routes investigated:
1. Audited available tools for a protected Gateway execution/parent messaging
   capability: none applicable. Did not inspect credentials or use shell/network
   access as a substitute authorization path.
2. Audited existing live_review.py and historical browser-play.py as alternatives.
   live_review drives the session directly, not the real browser; browser-play is
   hard-coded to the live port8795 and includes state-edit tests. Neither can be
   counted or launched as-is for this Goal. Reuse standard player run.py and web
   transport on new loopback ports with new saves through coordinator execution.

Unblock: coordinator verifies applicable spend allowance/protected Gateway,
allocates an isolated staging process/browser execution path and records actual
usage. Exact first command/conditions are in runs/goal-20261012/STAGING-PLAN.md.
Do not replace the required sessions with mocks, old sessions or local models.
Meanwhile: transcript critique, persona protocol, reusable browser-harness audit,
and offline safety checks remain unblocked.

## Held-out persona integrity

Coordinator should choose and retain the held-out persona before evaluation,
without revealing it for implementation tuning. Reading its resulting evaluation
retires that persona from future hold-out use; never tune against its transcript.
A different held-out persona is needed for a later cycle. This is a protocol
constraint, not a claim that an existing scripted path was held out.

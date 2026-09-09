# A portable public account

In a full Bellwether night, **Download readable account** saves an offline HTML
page; **Download public JSON** saves the same public material in a versioned
machine-readable document. These controls never advance a turn or spend a choice.
They work during a night and at dawn. An interrupted run is labelled interrupted;
an unfinished night is not labelled complete.

The export deliberately has fewer fields than the developer trace or a player's
private journal. It is **not a saved game, checkpoint or executable replay**.
Do not use it to resume a simulation or infer hidden decisions.

## Public scope, not anonymization

The server reuses `StormNight.view('spectator')`, then selects an explicit
allowlist of public event text, watch, kind, material inventory, service
consequences and a small dawn summary. Public events are numbered locally in the
export; hidden event identifiers and recipients are omitted. Component state,
private messages, pending action IDs, actor contexts, service identity, cookies,
hostnames and timing metadata are not exported.

The same operation returns the same public bytes for a player, an approved
resident, an approved spectator or the local developer. Visitors and revoked
browser sessions cannot call it. There is no option to request another player's
private account. The public timeline can still include a participant's names or
anything they said publicly: review before sharing. Visibility filtering is not
anonymization, and the underlying model may choose to disclose information in
public speech. No automatic sharing/upload happens.

HTML is self-contained UTF-8 with escaped text and no JavaScript, external
resources, forms, frames or embedded live service data. It can be opened offline.
The UI retains your current draft when a download fails, and refuses a delayed
download after a connection/role change.

## Attached CLI and research tooling

Use the existing CLI against the **trusted local developer listener** of a
full-night service built from this checkout, not the one-turn slice. Do not expose
that listener to other players. With the service already running:

```sh
printf '%s\n' '{"operation":"game.public_account","arguments":{"format":"json"}}' |
  python -m concordia.command_line_interface.concordia_session --url http://127.0.0.1:8784 call > public-response.json
python -c 'import json,pathlib; x=json.loads(pathlib.Path("public-response.json").read_text()); pathlib.Path("bellwether-public-account.json").write_text(x["result"]["content"], encoding="utf-8")'
```

Choose `html` instead to obtain the readable artifact. The shared operation's
`result` has `filename`, `media_type` and `content`; save **only content**.
The ordinary operation envelope contains process references for the attached
transport, and is not the shareable artifact. No mutation revision or retry key
is needed, and unknown formats are rejected with no effects.

The document schema is `bellwether-public-account/v1`. It records fixture/live
mode, in-progress/interrupted/completed status, public events and material
consequences. Export order is public event order, not wall-clock or causal
evidence. Multiple exports of an unchanged state are identical. Account numbers
are local display order, not references into private traces. New versions should
change the schema name before changing this contract.

## Evidence and limits

Tests use real components, the standard HTTP/operation/CLI path and actual
Chromium downloads, but **seeded records with simulation execution prohibited**.
They verify cross-role equality, private marker absence, error atomicity,
read-only state, offline literal markup and mobile width. They are not human
usability evidence or an additional live game. Prior fixture/live night evidence
remains separately documented.

The material ledger reports scenario rules; actor prose is not empirical
validation of real societies. An exported account neither certifies the truth of
the previous-storm dispute nor makes hosted model output deterministic. Full
checkpoints, intervention provenance and isolated continuation need separate
contracts before experimental branch comparison.

# Job B fixed-node match preparation

Prepared only; no engine or match execution, real declaration, runtime artifact, Git, source or state change was made. The final Job A binary does not yet have a value in this preparation. Root must declare its actual path/hash and frozen source commit before the first game.

Protocol: one final Job A binary, `hindsight-on` versus `hindsight-off`, with HindsightDepth true versus false. Both use Threads1, Hash16, OwnBook false and MateAlphaGuard false; all other options remain defaults. Each search is commanded with `go nodes 50000`. Stop at 6,000 games / 3,000 color-reversed pairs, or within two hours of declaration, whichever limit comes first. Reporting is counts only: W/L/D, five pair bins and operational findings; no Elo, strength or speed estimate is produced by these helpers. Any rating text emitted automatically by the unmodified runner remains in raw stdout only.

The official runner `/workspace/work/fastchess/fastchess` remains unchanged, SHA256 `f8f1706b6b4906d524dd0ac0547deb9ec2b6b10b4e32d7bde66914ddee0ebd4f`. Its clean source checkout is official Disservin/fastchess commit `3d7a4db2493fc85a05ef010fd7e13a3884667aa2`; exact read-only Git outputs and relevant source snapshots are in `OFFICIAL-RUNNER-PROVENANCE.txt`. The book is `/workspace/work/soak-run/openings/UHO_Lichess_4852_v1.epd`, SHA256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`.

A single fixed seed, `202611150011`, randomizes the book. Successive 100-game batches use opening starts 1, 51, 101, and so on; each requested round has two games with colors reversed. The runner source shuffles, then rotates by start minus one, then truncates. Thus batches follow successive slices of the same randomized source sequence, without resetting to its first opening. The original book can itself contain duplicate FENs; pair identity and two-game treatment are verified per selected opening. Native `-openings order=random` is retained. No draw/resign/tablebase/maxmove adjudication, time control, SPRT or color-swap suppression is enabled.

Root commands, after Job A completion and with no concurrent native work:

```text
# Copy DECLARATION-INPUT.template.txt to a new runtime input file and fill it.
# Set jobAComplete=true only after Job A is actually complete.
# Supply the actual final binary/hash/source commit, retained plain UCI stdout
# ending in uciok, and immutable Job A completion evidence with their hashes.
node /workspace/work/parity-match-preparation/controller.mjs declare /workspace/work/parity-run/jobB-declaration-input.txt
node /workspace/work/parity-match-preparation/controller.mjs prepare
node /workspace/work/parity-match-preparation/controller.mjs run B-0001 --execute-authorized
node /workspace/work/parity-match-preparation/controller.mjs audit B-0001
node /workspace/work/parity-match-preparation/controller.mjs status
```

Repeat prepare/run/audit for the next B-NNNN only while status is ready, below the game limit and within budget. Root writes the actual declaration; preparation never substitutes the step1 binary or an invented final hash. The declaration is immutable at `/workspace/work/parity-run/matches-hindsight/DECLARATION.txt`. It pins the helpers, binary, default UCI proof, completion evidence, official runner/book, source paths and source commit. Report-only descendant commits are allowed when engine-path bytes still match the declared source commit. Use immutable completion evidence rather than a report that will later receive match updates. The final UCI proof must contain plain `option name ...` lines and `uciok`; both HindsightDepth and MateAlphaGuard must advertise default false. Full advertised option sets are subsequently checked in both engine traces.

The default batch size is 100 games / 50 pairs at concurrency4; 200 games may be selected in the declaration before starting. Every game still uses Threads1. At declaration and immediately before each native batch, `/proc` executable checks reject active native work under `/workspace/work`, avoiding the prior soak overlap at launch. Root must keep the match phase exclusive throughout a batch; the launcher does not claim a continuous host-wide lock.

Normal stopping occurs after a complete batch, at a pair boundary. A batch may not start with less than 470 seconds remaining in the two-hour window. Native execution has timeout360 seconds plus five-second kill allowance, with controller fallback at370 seconds and five-second termination grace. A final pre-spawn check requires the complete native bound to fit. Audit is a separate command capped at75 seconds. Each command remains below eight minutes. A hung or externally interrupted batch cannot promise a graceful pair-boundary stop: its raw completed games and partials are retained, and the entire batch credits zero games/pairs, matching the prior protocol. No further batch is prepared after an incomplete or faulted batch without a separately reviewed recovery.

Every batch retains full PGN, stdout, stderr, combined console, full engine trace, machine-readable events, the runner's saved config, exact argv/cwd/input pins, exit/signal/interrupt record, immutable audit, hash manifest and receipt. Source/options/config/pair/opening/WLD/pentanomial checks are adapted from the proven r4 auditor; changes are recorded in `audit-core.diff.txt`. Completed scored fault games remain in W/L/D and pair bins, with faults recorded separately. Audit exit0 means complete and fault-free, exit2 means complete with faults, exit3 means incomplete or invalid. Earlier summary/plan/manifest pins are checked before continuation; raw artifacts retain their original full hashes without rereading every old multi-megabyte trace before each new batch.

Side accounting distinguishes illegal move events and games, disconnect games, stall games, time-forfeit games, nonzero process exits, process signals and controller-cleanup signals. Game faults are attributed to the losing configuration; illegal events identify the emitting engine. Explicit process signals/exits remain separate from game faults, so a disconnect and process death are not silently counted as two distinct crashing games. Disconnect alone does not prove crash cause. Aborts without an identifiable side and unmatched process diagnostics remain explicitly unattributed. The complete raw trace is retained for interpretation.

Validation reused the original retained completed and timeout batches; no engines were rerun:

| Retained batch | Raw finished | Credited games | Credited pairs | W/L/D | Pair bins |
|---|---:|---:|---:|---|---|
| MateAlphaGuard-0001-retry | 400 | 400 | 200 | 114 / 116 / 170 | 0, 2, 198, 0, 0 |
| MateAlphaGuard-0001 timeout | 314 | 0 | 0 | 84 / 85 / 145 raw only | 0, 1, 156, 0, 0 raw only |

Both reaudits matched original completion/pass status, counts, pair results, failure counters and error lists, and original artifact hashes remained unchanged. The independent PGN parser reproduced W/L/D and pair bins and rejected a synthetic duplicate GameId. Sample plans cover 100/200-game batches, successive offsets and the final 6,000-game boundary. Five final module syntax checks passed with individually checked exit statuses. Exact scripts, command outputs and proof are in `VALIDATION.txt`, `FINAL-STATIC-CHECK.txt` and adjacent stdout/stderr files. Current declaration/launch/receipt-writing paths have been inspected but not exercised against a real final binary; first live integration remains root work. The sample plans contain an explicit nonexistent future-binary placeholder and are not declarations.

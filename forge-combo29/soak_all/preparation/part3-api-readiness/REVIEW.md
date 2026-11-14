# Part 3 fastchess API readiness review

No confirmed CLI, event, PGN, console, or saved-configuration incompatibility was found between the pinned runner and the installed official fastchess source. This is a source review with synthetic parser fixtures, not a completed native match, legality replay, or assurance that a 400-game batch finishes within its wall-clock budget. No native games, builds, engine searches, state writes, controller edits, source edits, or Git mutations were performed for this review.

## Frozen inputs

- Runner `/workspace/work/all-run/match_all.mjs`: SHA256 `3b47871bee151c78ed6f2c4247fb7f42154d16e775b2f83018d38e86abc18fc0`.
- Representative spec `/workspace/work/all-run/specs/3-default-0001.json`: default comparison, seed 8474001, 400 games, concurrency 4, unique `matches/default-0001` prefix.
- Official fastchess source HEAD `3d7a4db2493fc85a05ef010fd7e13a3884667aa2`; `git status --short` empty before and after inspection. Executable SHA256 `f8f1706b6b4906d524dd0ac0547deb9ec2b6b10b4e32d7bde66914ddee0ebd4f`.
- Merged executable SHA256 `e2788a101d11acfca637b14471e2b067ae11e551500cfb0656019a193ec2cb3e`.
- Lock executable SHA256 `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
- UHO book SHA256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`, 174889110 bytes. Full text scan found 2632036 nonempty canonical six-field FEN lines: 1457270 White-to-move and 1174766 Black-to-move, no standard starting position. The book name does not indicate its actual line count.

The runner and executable hashes were unchanged at the final identity check. Read-only snapshots of the runner/spec are retained as `.txt` files.

## Source/API checks

| Contract | Actual source behavior and parser compatibility |
| --- | --- |
| Nodes/options | `cli.cpp` supports the requested `-engine`, deferred `-each nodes=20000`, `-recover`, rounds/games/concurrency, openings, srand, PGN/log/events/config options. `UciEngine::go` emits exactly `go nodes 20000` with zero depth and clock limits. Standard-variant refresh sends the declared options, with Threads first; it adds no Chess960 option. |
| Engine modes | Default candidate uses merged and baseline uses lock, each with Threads 1, Hash 16, OwnBook false. It sends no new options to lock. Each option comparison uses merged on both sides, selected option true only for candidate, all other candidate options false, baseline all false. Default advertisements are checked false. |
| Pairs and seeds | The two-player scheduler produces 200 rounds times two games. One opening index is selected per pair; even game IDs swap engine colors. `playGame` receives zero-based pairing ID, so its emitted `round + 1` equals `ceil(game/2)`. The configured seed initializes `mt19937_64` before opening-book shuffle. Pairing generation is protected by a mutex, independent of completion order. |
| EPD handling | EPD reader retains each nonempty input line as its FEN and supplies no book moves. The actual book is six-field/canonical, matching the runner's membership check. No startpos entry means native PGN should include the FEN tag that this runner requires. Black-to-move FEN does not change engine color assignment. |
| Events | Native start event contains game/round/white/black/start_fen/opening plus null clocks and `-` time controls. Move `ply` is moves-vector size; EPD's empty initial moves makes this start at one. Finished plies counts legal moves. Exactly one finished or aborted event is emitted per start. Native field names, result strings, termination names and tournament completion reason match the parser. |
| PGN | Native builder emits Event/GameId/White/Black/Result/PlyCount/Termination and the six-field FEN for these UHO positions. It emits TimeControl `-` for equal untimed limits. Its abnormal termination translations agree with the runner. The parser cross-checks result metadata and terminal result text; it does not independently replay SAN or establish legality. |
| Console | Cutechess output formats `Finished game N (white vs black): RESULT {reason}` and `Score of candidate vs baseline: W - L - D [score] N` exactly as parsed. Output mutex serializes finish and score lines. Final WLD perspective is candidate vs baseline. |
| Saved config | Enum ordinals EPD=0, RANDOM=0, CUTECHESS=1 and TRACE=1 agree. Rating interval zero is normalized to INT_MAX. Untimed limits contain five zero fields. Candidate-first stats key is `candidate vs baseline`. Tournament destruction waits/stops the pool and saves final JSON before tournament_finished. CLI events settings intentionally are not serialized, and the runner does not require them there. |
| Trace | Native logger prefix is padded to six characters, producing `[Engine]`, then time/thread/name and `<---` or `--->`; both runner regexes match this. The required explicit options and exact node command are checked in trace. |

`-ratinginterval 0` suppresses periodic rating output but the round-robin source still calls its final interval report when all matches finish. Raw final rating text can therefore appear. It is retained only as command output and must not be interpreted as a strength conclusion.

## Executed parser-only fixtures

`node --check parser-fixtures.mjs` and `node parser-fixtures.mjs` both exited 0. The fixture imports `makePlan` and `auditBatch`; it does not call `runBatch`, spawn an engine, or launch fastchess. All generated files are explicitly synthetic and live under this scratch directory, outside native match prefixes. Synthetic movetext is not an assertion of a legally played game.

- Clean fixtures for default and all three option modes: completed=true, passed=true, 1 win/1 loss/0 draws, one middle pair bin, no structural errors.
- Black-to-move UHO fixture: same accepted accounting and reversed colors.
- Scored disconnect fixture: completed=true, passed=false, WLD and completed pair retained; disconnect and abnormal-termination counters both one.
- Wrong round fixture: completed=false, passed=false; errors `unexpected round 1` and `opening/color pair mismatch 1/2` preserved. Raw scored counts remain visible for diagnosis; they are not proof that a controller should aggregate an incomplete batch.

Seven fixture cases passed. Actual native games run in this review: **zero**. These checks complement the earlier accounting/duplicate-seed fixtures in `part3-accounting-proposal`; this review does not execute the controller or mutate its ledger.

## Remaining limitations for the first official batch

1. Native completion within 420 seconds is unverified. The runner's timeout reserves 5 seconds for kill; the controller's 450-second timeout leaves at most approximately 25 seconds for postprocessing in the worst case. Auditing rereads the 174.9-MB book and the complete trace. A cutoff is incomplete, not a completed 400-game result; its raw evidence must remain preserved.
2. The runner relies on native fastchess for chess move legality. Its PGN check is consistency checking, not an independent chess replay. Counts must not be described as an independent move-generation proof.
3. Trace option/default checks aggregate by engine name, not by every individual engine process instance. Process-exit faults are retained, but a positive exit marker is not required for every cache instance. A global abnormal game disables go/move equality checks for the batch. These are bounded audit limitations, not source evidence of a native fault.
4. The previously reviewed persistence-error path can leave completed=true while marking passed=false; the controller/operator must inspect preserved persistence errors and evidence-copy errors, rather than equating completed solely with complete archival delivery.
5. The standalone runner reserves an artifact prefix but does not itself maintain a semantic mode/seed ledger. Root's reviewed controller duplicate guard remains required for production launch; incomplete unrecorded retries must use unique artifacts and preserve the original attempt.

No production changes are proposed by this review. Inspect the first official batch's raw files, parsed summary, and evidence-copy outcome before treating it as a template for subsequent batches.

## Evidence

`commands.json.txt` indexes 51 exact inspection/fixture commands with cwd, exit and signal; `command-001.txt` through `command-051.txt` preserve full actual stdout/stderr. Exploration failures remain recorded: missing inspection paths and two malformed `rg` patterns, not engine failures. `fixture-results.json.txt` contains all fixture outcomes and expanded representative arguments; the synthetic artifact directory retains each input and audit result. `evidence-hashes.txt` records the evidence inventory. No output is a native match result for the eight-hour job.

# Independent audit of real Part 3 default batch 0001

The first native Part 3 batch is consistent across its original artifacts, copied evidence, committed Git blobs, controller metadata, events, PGN, console and engine trace. The final independent audit exited 0 with no remaining discrepancies. This audit launched no engines, games or builds and changed no production source, runner, controller, state or branch.

The existing batch contains **400 games: 113 candidate wins, 107 losses and 180 draws**. Candidate is the merged default executable; baseline is the unchanged lock executable. This is a crash/legality consistency check, with no strength or speed conclusion.

## Independently reconstructed observations

| Observation | Recount from real artifacts |
| --- | --- |
| Starts / finishes / PGNs / console results | 400 / 400 / 400 / 400 |
| Move events | 54357, all carrying native `legal:true` |
| Candidate / baseline move events | 27177 / 27180 |
| Event lines | 55159: one tournament start, 400 game starts, 54357 moves, 400 game finishes, one tournament finish |
| W / L / D | 113 / 107 / 180, agreeing with PGN, console, saved config, runner and recorded controller counts |
| Completed reversed-color pairs | 200 |
| LL / LD / DD-or-WL / DW / WW pair bins | 4 / 31 / 127 / 31 / 7 |
| Pair positions | 200 distinct frozen-book FENs; 91 Black-to-move and 109 White-to-move pairs |
| End reasons | White mates 123; Black mates 97; fifty-move draw 25; repetition draw 121; insufficient material draw 32; stalemate 2 |
| Aborted games / abnormal terminations / illegal flags | 0 / 0 / 0 |
| Trace | 1705743 lines; no crash, illegal-move, disconnect, stall, nonzero exit, signal-exit or warning/error findings |
| Engine exit status markers | Eight normal status-0 exits |

Each move's per-game ply sequence, side to move and assigned engine were checked against the actual starting FEN and the color assignment. Every paired game starts from the exact same FEN with reversed engine colors. Every selected FEN was found in the frozen UHO book. The independently reconstructed ordered-pair hash is `be7383d877e806b9655fbfb2fc60aee3755b53de5698ed5400601208f41d9d0f`.

This does not independently replay chess move legality. The legal flags and natural termination classifications come from official fastchess; the separate audit establishes their cross-file consistency and preservation.

## Real command and configuration agreement

Every one of the 54357 traced searches is exactly `go nodes 20000`, with no depth or engine clock argument. Candidate issued 27177 searches and baseline 27180, matching their move events exactly. Reported event node values range from 128 through 20000; these are observations from native output, not an assertion that every search must report exactly the limit.

Threads 1, Hash 16 and OwnBook false are the only options sent in this default comparison. Each option was sent 400 times per engine. The trace contains four initialized worker-thread instances of each engine, each receiving its required options; eight quit commands are sent by the controlling thread at shutdown. Candidate advertises ContHist4PlyRead, NonPawnCorrection and LmrDeeperShallower default false. The sampled advertisement also has UseNNUE default true. No new option is sent to lock.

Saved config confirms seed 8474001, random EPD UHO openings, games 2, rounds 200, concurrency 4, recover true, no noswap/reverse, node limit 20000, depth zero, all five time-control fields zero, and draw/resign/maxmoves/tablebase/SPRT adjudication disabled. All event clocks are null and PGN TimeControl is `-`.

Native `report_penta` is false with cutechess output. The native saved penta counters therefore are not the pair-count source; the five bins above are independently reconstructed from paired game results. Both engines advertise the same PGN EngineName label, so distinct command paths and pinned executable hashes establish their identity.

## Input identity and archival reconstruction

The current files match the command's before hashes, the summary's before/after hashes and these frozen pins:

| Input | SHA256 |
| --- | --- |
| Official fastchess | `f8f1706b6b4906d524dd0ac0547deb9ec2b6b10b4e32d7bde66914ddee0ebd4f` |
| Merged release | `e2788a101d11acfca637b14471e2b067ae11e551500cfb0656019a193ec2cb3e` |
| Lock release | `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6` |
| UHO book | `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` |

All **14 original files, 253871646 bytes in total**, match their manifest SHA256 and byte lengths. The copied evidence contains **28 text files**: 12 unsplit originals, two event chunks and fourteen engine-trace chunks. Every copied file matches its own hash/length, all chunk offsets/order are contiguous, intermediate boundaries are newlines, each chunk is valid UTF-8 and no chunk exceeds 16 MiB. Concatenating each split file in manifest order reconstructs the original hash and byte count exactly.

The 20529782-byte event stream reconstructs SHA256 `b3c127e6167c2f85a3ea69f718f16e402f8b3d9acdbfa0c2c0adcd9949b7ddd6`. The 231038058-byte engine trace reconstructs SHA256 `55a56fee6f7684f2f343590739fbd58a32a42f94eed6b4ba80eed72cbfbd68d7`.

The manifest and every copied file also match their committed Git blob IDs at frozen local HEAD `e983e08e5dc491fd68ae2bd52ae669dbe38137fc`. This audit did not query remote publication status. The original artifact-hash list agrees with the copied manifest, including the saved summary itself; every required raw file is represented.

## Documented serialization detail and audit correction

The first independent audit deliberately required whole-object equality between `summary.json` and the controller's emitted SUMMARY. It exited 1 on one difference: emitted SUMMARY contains `artifactHashesFile`, while the saved summary omits it. Every other field matched.

Read-only inspection of `match_all.mjs` lines 240–254 shows the reason: `persistSummary` writes the summary and hash file, then emits `{...summary, artifactHashesFile: plan.files.hashes}`. This is an intentional provenance-pointer addition and does not change any count, status, fault or hash. The scratch auditor now requires exact equality to that specified emitted object, including the exact expected pointer; it does not ignore arbitrary metadata differences. The refined audit exited 0. The initial failed output/result and exact field difference remain preserved. No production file was changed.

Native runner status is completed=true/passed=true/process exit 0, with no persistence errors. Controller exit is 0, incomplete=false, with no accounting or I/O errors. All mapped recorded counts agree with the independently reconstructed totals. The controller's recorded elapsed wall time is 200052 ms, within its requested 450-second bound; no extrapolation to later batches is made.

## Saved review evidence and reusable helper

- `audit-results-final.json.txt`: complete independent findings, all per-file hashes, copied Git blob IDs, event examples, trace-instance counts and exact read-only Git command outputs.
- `audit-results.json.txt`, `command-002.txt`, `summary-differences.json.txt`: preserved initial strict-equality result and the sole provenance-pointer difference.
- `commands.json.txt` and `command-001.txt` through `command-005.txt`: exact helper/syntax/source-read commands with actual stdout/stderr and exits.
- `secondary-review.txt`: independent second reviewer, five exact read commands and their actual outputs, checking real settings and samples.
- `audit-real-batch.mjs` / `audit-real-batch.mjs.txt`: reusable scratch-only verifier. It imports no runner, launches no native workload, reads raw files/Git only, and writes exclusively under this audit directory. Invoke using `--prefix`, `--manifest`, `--metadata`, and `--out`; the exact batch-0001 invocation is in command-005.txt. Running at niceness 10 keeps it subordinate to native match workloads.
- `evidence-hashes.txt`: hashes/lengths of this scratch review bundle.

The helper flags abnormalities and incomplete/mismatched evidence; it never edits the production ledger or discards/retries games. An abnormal later batch must retain its scored results and faults under the controller's accounting policy. These audit executions contribute **zero new native games**. Synthetic fixtures from the earlier readiness review are not part of this batch or its totals.

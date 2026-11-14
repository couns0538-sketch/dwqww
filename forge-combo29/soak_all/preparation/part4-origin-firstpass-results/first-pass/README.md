# Scratch first-pass TT-origin tracer: prepared, not compiled or run

This directory is isolated preparation for the root agent's later review and bounded execution. **Native builds: 0. Engine/key-query/oracle runs: 0.** No production source, header, branch/ref, existing binary/object, or controller state was changed.

The root must inspect this preparation before executing `native-plan.json.txt`. That file contains exact argv arrays, including timeouts; it was generated but never executed here. Check the clock and checkpoint between its sequential steps. This is the first pass only. Do not add the producer-subtree second pass until the first pass reveals an actual writer.

## Inputs and scope

- Pinned source commit: `f27b1971e459581ad4c85b7015f6af83bbfd4af6`.
- Pinned `search.cpp` SHA256: `2b14b62cd675b047478e70b738932ce4c2c699239b3c0de4ec43551464dc8819`.
- Current source/headers, release binary, eight release objects, flags and link recipe are hashed in `readonly-inputs.sha256.txt`. Recheck before native execution; input drift invalidates provenance until explained.
- `pinned-search.cpp` is a private `git show` copy, not a checkout. `source-read.txt` preserves its exact command and output.
- `prepare_trace.mjs` deterministically creates `search-origin.cpp` from that copy. It checks the source hash and every anchor, and reverses all transformations to verify exact recovery of the input. `preparation-summary.json.txt` records that result.
- `origin_trace.hpp` holds scratch-only logging helpers. `key-query.cpp` is a separate matching-defines query for the watched position key.
- `instrumentation.diff.txt` is the full search-source diff. Diff exit1 means the expected logging additions; the exact command/output is in `diff-command-result.txt`.
- No r3-21, r3-23 or r3-24 code is included. No pruning, score, replacement/admission predicate, or TT data layout is changed. No extra TT probe is performed.

## Native execution order after root review

Execute the argv arrays in `native-plan.json.txt` in order, capturing each command, stdout, stderr and exit code. The plan uses `/usr/bin/c++`, existing release feature/ISA/layout defines, strict floating-point flags, and existing release objects. Every new binary/object/dependency file goes under `native/` in this directory. In particular the original linker dependency output is replaced with this directory's `native/link.d`; no link command writes the original build directory.

1. Create the scratch `native/` directory and compile `key-query.cpp` against the release board/bitboard objects with matching defines. Run the query. It prints `TARGET_KEY <decimal> FEN ...`; do not fabricate or guess this value.
2. Compile `search-origin.cpp`, then relink existing release objects with this replacement search object into `native/forge-origin`.
3. Run fresh unmodified baseline `baseline-r1`, then traced runs `trace-r1` and `trace-r2` using the decimal key from step1 in place of `__TARGET_KEY__`.
4. Run `compare_runs.mjs baseline-r1 trace-r1 trace-r2`. An exit0 establishes only the specified identity checks; it is not a TT provenance or mate-soundness verdict.

The reproduction driver accepts:

```text
node repro_driver.mjs /absolute/binary unique-label [decimal-target-key [positive-event-limit]]
```

It always clears inherited `FORGE_ORIGIN_KEY` and `FORGE_ORIGIN_LIMIT`. Supplying the optional key sets those two child variables to the supplied decimal key and limit (default200000). Without a key, tracing is disabled. Invalid key/limit values produce explicit configuration-error stderr and fail the identity check.

Each run uses a fresh engine process, Threads1, Hash16, OwnBook false, UseNNUE false, all other engine defaults, a fresh game/hash and the known root at depth13. It waits for `readyok` before searching and for `bestmove` before quitting. The driver signals TERM after45 seconds and KILL after50; each plan invocation also has an outer90-second timeout. A timeout is failure/partial evidence. Run labels must be new; the driver refuses to overwrite an existing run directory.

Raw stdout, stderr, timestamped input traffic and exact binary hash/settings/trace environment/exit summary are saved under `runs/<label>/`. Previous `part4-review` files cannot be overwritten by this driver.

Expected final identity is mate17, 25568 nodes, `bestmove b3f3`, with this PV:

```text
b3f3 c2d2 f1f2 d2d1 f2e3 d1c2 e3e2 c2c1 f3c3 c1b2 e2d3 b2b1 d3d2 b1b2 c3f3
```

The comparison removes only numeric `time` and `nps` fields and compares complete stdout, not only that final line. It requires baseline stderr empty, trace stderr consisting of trace records with no config-error/truncation marker, successful completion, matching recorded settings, and the pinned baseline binary hash. It also requires the known root_depth13/ply15 endpoint probe with raw-31982, adjusted-31967, bound1, depth9 and the exact endpoint FEN. For two trace runs it additionally checks matching binary/key metadata and compares full stderr after consistently relabeling process-dependent `table=0x...` addresses. All other fields, including event order, frame IDs, windows, scores and slot payloads, must match. The optional third comparer argument exists for preliminary single-trace checks; the prescribed final plan supplies all three labels and requires the repeat. These checks do not reconstruct the admitted-writer ledger. If identity differs, stop interpretation and investigate instrumentation/input drift; do not modify engine behavior to make it pass.

## Recorded events and original source hooks

The runtime key must be for `8/8/8/8/8/5R2/1k1K4/8 b - - 15 8`. The filter matches the full position key at all iterations/plies/clocks. TT events also cover every operation in its physical four-slot cluster, including other requested full keys. The active build is `FORGE_SPD_TT_NOTLS=1`; the helper intentionally rejects compilation with the alternate macro path.

| Event | Original source lines | Meaning |
| --- | --- | --- |
| RESIZE/CLEAR | 260-274 | table/epoch lifecycle; no additional payload operation |
| PROBE_BEFORE | 278-283 | all four entries before the original probe's generation refresh; slot=-1 and hit=0 are placeholders, not a miss verdict |
| PROBE_AFTER | snapshot284-293 | actual selected slot, hit/miss and all four entries after the original probe, with full requested key |
| STORE_BEFORE | 324-335 | all four entries before any original store mutation, including the original move-only refresh; admitted=0 is a pre-operation placeholder |
| STORE_AFTER | 336-344 | all four entries after mutation; admitted=1 only if the original score-payload admission body actually ran |
| STORE_INVALID_HANDLE | 329-330 | a target-key store failed the unchanged handle-validation predicate; no table payload was read or written |
| FRAME_ENTER/LEAVE | qsearch1041; main after1180 | scoped caller IDs, parent relation, original window/depth, key/FEN/history, entry/current node counts; leave has no implicit return-value claim |
| WORKER_PROBE | qsearch1071-1074; main1219-1222 | raw/adjusted score, hit, stored bound/depth/clock, score usability and current effective window |
| TT_SUBSTITUTION | qsearch1092-1095; main1244-1247 | records the existing replacement of static eval by a TT score, without changing the condition |
| STORE_CALL | qsearch1100/1165; main1346/1567 | intended raw/current-ply value and store-site label QS_STANDPAT/QS_FINAL/PROBCUT/MAIN_FINAL |
| RETURN | existing TT/standpat/ProbCut/final returns | actual returned value and available PV length for watched-key frames |

Frames are debug-only locals/TLS, not added fields in any engine object. Main search constructs a frame only after its depth<=0 delegation, and RAII restores parent context on every return. The debug relation is ROOT, MOVE_EDGE, NULL_EDGE, SAME_PLY or OTHER_PLY; incoming move bytes are copied on entry so later same-stack recursion cannot rewrite the recorded edge. Full key history and root index accompany watched frames and physical-cluster events. This is first-pass context, not an exhaustive trace of every child/pruning decision.

Slot encoding is:

```text
slots=[slot,key32,score,eval,move,depth,gen_bound,rule50_clock,occupied; ...]
```

Move text includes exact raw bytes as `uci(from:to:promotion:flags)` or `none(...)`; malformed shapes use `invalid(...)`. This preserves move-only updates and prevents logging from indexing a malformed promotion byte. `gen_bound` is retained raw; bound is its low two bits, PV is bit2, generation is bits3-7. Table identity, epoch, slot and event sequence allow an offline payload ledger. No claim is made that the TT stores full keys: full requested keys come from the operation records.

`STORE_AFTER admitted=0` can still have a changed move, because the baseline refreshes its move before deciding whether to accept its score. A depth0 qsearch store attempt can leave the depth9 score untouched. Do not identify a writer from STORE_CALL alone.

## Identify the earlier writer

Locate the watched WORKER_PROBE at root_depth13/ply15 with raw-31982, adjusted-31967, bound1, depth9, followed by the QS_FINAL return with empty PV. Its preceding PROBE_AFTER gives the physical table/epoch/slot. Walk that slot's STORE_AFTER events backwards to the latest admitted matching payload, preserving intervening changes to all four slots. The associated active frame and `store_site` identify the earlier caller, window, root iteration, ply and history. Do not infer the producer solely from a matching score on another slot or an unadmitted request.

There is no automatic provenance/mate verdict in the scripts. Once a writer is observed, use the accepted proposal's separate intermediate-state KRK checks and, only if needed, prepare a second-pass trace for that invocation's dependency subtree. Do not call the oracle from inside the live search. The current expected endpoint bound is conservative; a short PV is not a fault oracle.

## Verification completed during preparation

- Pinned Git source was read and its SHA256 checked.
- Deterministic preparation succeeded and round-tripped exactly to the original source.
- The full logging diff was inspected; its expected `git diff --no-index` exit was1.
- Node syntax checks passed for preparation, reproduction driver and static comparer; exact outputs are retained as `*.syntax-check.txt`.
- An independent static peer review found no blocker in C++ syntax by inspection, RAII caller association, slot/admission logging, scratch build paths, raw Move serialization, or driver/comparer scope. Its review is in `peer-static-review.txt`; it did not compile or execute anything.
- All14 recorded production/build input hashes were rechecked unchanged (`readonly-inputs-recheck.json.txt`). The exact deterministic preparation command/result is in `preparation-command-result.txt`.
- C++ compilation and all runtime identity/admission checks remain **not run**, intentionally reserved for root execution after review.

`SHA256SUMS.txt` covers this preparation, including exact source/helper/script/build-plan identities. `readonly-inputs.sha256.txt` covers original inputs. Preserve all native failure outputs if a later build or run fails; do not silently patch around an engine failure.

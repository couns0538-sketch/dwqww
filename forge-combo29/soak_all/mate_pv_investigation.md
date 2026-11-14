# Mate score with a truncated PV: bounded investigation

**No false mating bound was demonstrated. No production engine fix or compile switch was added.** The reported position reproduces with `UseNNUE=false`, and the exact KRK oracle confirms that the selected move forces mate within the reported bound. A scratch-only trace identifies a TT-backed qsearch return that supplies a mate score without extending the PV.

## Reproduction and provenance

FEN: `8/8/8/8/8/1R6/2k5/5K2 w - - 0 1`.

Each engine process received `uci`, Threads 1, Hash 16, OwnBook false, `isready`, fresh `ucinewgame`, the FEN, and `go depth 13`; the driver awaited `bestmove` before sending `quit`. All other options were at defaults. The NNUE-off runs additionally sent `setoption name UseNNUE value false` before `isready`.

| Settings | Exact lock result | Merged result |
| --- | --- | --- |
| Default UseNNUE=true | cp 449; 50362 nodes; b3b5; 18-ply PV | Same |
| UseNNUE=false | mate 17; 25568 nodes; b3f3; 15-ply PV | Same |

The four uninstrumented searches exited 0 with empty stderr. The missing `UseNNUE=false` setting is necessary for this reproduction. The behavior is present in the unchanged lock.

| Artifact | Identity |
| --- | --- |
| Lock source | `16833ecc03b425586f91f4c8834dea8807bf4c22` |
| Lock binary SHA256 | `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6` |
| Merged binary SHA256 | `e2788a101d11acfca637b14471e2b067ae11e551500cfb0656019a193ec2cb3e` |
| Merged search.cpp SHA256, unchanged before/after scratch instrumentation | `2b14b62cd675b047478e70b738932ce4c2c699239b3c0de4ec43551464dc8819` |
| Merged uci.cpp SHA256, unchanged before/after scratch instrumentation | `724a4c9c07a4102d38c39fc292f66ba0c850a9c162c090148734da86acd4fb40` |
| Unchanged t12 oracle source Git blob | `329cad9acfee7e0a88e118911d14298818234244` |
| Scratch instrumented binary SHA256 | `6785c99212bf194eea7a6e5bb7b7bb2bbd4113fae2f0adb6c4c3f39e81358304` |

Source inspection initially observed HEAD `b1675de751153e6b80e5c99779805956c22912cc`; the scratch-instrumentation provenance later observed `4a929610a798f072c68330c17bd042a250467c7a`. The engine source and release-binary hashes above identify the tested artifacts despite concurrent report/test-driver work. No old soak worktree or engine source was modified by this investigation.

The reported PV is:

```text
b3f3 c2d2 f1f2 d2d1 f2e3 d1c2 e3e2 c2c1 f3c3 c1b2 e2d3 b2b1 d3d2 b1b2 c3f3
```

## Independent mating assessment

The scratch query includes `tests_t12/krk_mate_test.cpp` unchanged, renames its original main, and invokes only its exact KRK retrograde class and board operations. It does not run that test's repeated engine searches. The oracle algorithm is independent of alpha-beta search but shares the engine's attack/board primitives; it is not an external tablebase implementation.

- Exact root DTM is **15 plies**, equivalent to mate in 8 moves. The optimal root move is `b3e3`.
- The chosen `b3f3` forces mate in **17 plies**, equivalent to mate in 9 moves.
- All 15 published PV moves are legal.
- Its endpoint is `8/8/8/8/8/5R2/1k1K4/8 b - - 15 8`. Black has three legal moves and is not in check.
- The endpoint's exact remaining DTM is **6 plies**, allowing mate within 21 total plies along the displayed prefix followed by optimal continuation.
- UCI `mate 17` is measured in moves. Here it corresponds to a reported mating bound of 33 plies, not 17 plies.

The oracle therefore does not establish an impossible mate bound or a nonmating chosen move. The reported distance is loose compared with exact DTM. An incomplete PV is not, by itself, proof that the score is false.

## Code mechanism and scratch trace

The initial investigation did **not** instrument the exact return instruction. Its preliminary source-based assessment is preserved separately in `mate_pv_evidence/preliminary-analysis.md`. The authorized follow-up instrumented only a scratch copy of the merged `search.cpp` with two logging statements, one at the qsearch stand-pat early return and one immediately before its final return. Production source, binaries, and search decisions were unchanged. The original lock binary's instructions were not instrumented.

One bounded NNUE-off run of that scratch executable reproduced all deterministic stdout exactly: after removing only engine-reported `time` and `nps` fields, its complete stdout matched the uninstrumented merged run (`diff` exit 0). It again searched 25568 nodes, returned `mate 17`, and emitted the identical 15-ply PV. Exit was 0; stderr contained only the intentionally added trace records.

The record at the published PV endpoint is:

```text
TRACE_QPV_FINAL root_depth=13 ply=15 alpha=-31967 beta=-31965 score=-31967 pv_length=0 tt_score=-31967 tt_raw=-31982 tt_bound=1 tt_depth=9 fen=8/8/8/8/8/5R2/1k1K4/8 b - - 15 8
```

`tt_bound=1` is `BoundUpper`. The cached mate-valued TT score replaces qsearch's stand-pat evaluation. At this quiet Black-to-move endpoint, qsearch returns that score with an empty child PV. Its parents copy only their searched prefix, while the numerical mate score is propagated separately. The cached position-relative score `-31982` becomes `-31967` after the ply-15 adjustment, yielding root score `31967` and UCI mate distance `(32000 - 31967 + 1) / 2 = 17`.

This confirms the final-return mechanism in the scratch reproduction. It does not audit the earlier creation of every TT bound or prove all mate reports correct. The independent oracle is the evidence that this particular reported bound does not overclaim.

All references below are `forge-combo29/src/search.cpp` at the recorded source hashes:

| Mechanism | Lock lines | Merged lines |
| --- | --- | --- |
| Reset qsearch PV length on entry | 996 | 1048 |
| TT cutoff can return a score without reconstructing a PV | 1016-1019; 1165-1169 | 1075-1079; 1226-1231 |
| Replace stand-pat evaluation with a usable TT score, including mate values | 1032-1044 | 1092-1104 |
| Final qsearch return identified by scratch trace | 1109 | 1169 |
| Copy only the child PV actually searched | 1091-1094; 1444-1447 | 1151-1154; 1526-1529 |
| Store the completed root score and PV separately | 1689-1697 | 1809-1814 and emit logic |
| Format mate distance and print the available PV | 190-196; 1576-1579 | 198-204; 1672-1682 |

## Interpretation checked by independent source review

The retained UCI output has no `lowerbound` or `upperbound` qualifier. Calling its mate distance a mating deadline is an analytical at-most interpretation, not a claim that UCI advertised a bound or that the engine proved exact DTM. The root DTM is 15 plies; selected `b3f3` requires 17 plies, so it preserves the forced mate but is not shortest-DTM optimal. The printed mate17 corresponds to 33 plies. The endpoint trace explains reuse and PV truncation; it does not certify how every earlier TT bound was derived. See the [independent static review](preparation/part4-static-review/REVIEW.md).

## Recommendation and limits

Do not suppress mate scores because the displayed PV is shorter than the reported mate distance. No targeted correctness fix, including a default-off switch, is justified by this reproduction. Reconstructing a complete continuation would be a separate display feature; blindly following TT moves can introduce cycles or misleading continuations.

A real bounded fix would require evidence of an impossible mate bound, a move that fails to force mate within the claimed bound, or a traced unsound bound operation. None was demonstrated here. These checks do not establish correctness for other positions, settings, or thread schedules. No strength or speed conclusion is drawn.

## Evidence and unsuccessful investigation commands

All retained artifacts under `mate_pv_evidence/` are text. Binaries, objects, and the instrumented source stayed in VM scratch. The `.cpp.txt` file is the scratch oracle driver's source text, not an engine or repository-test change.

- `repro-transcript.txt`, `repro-nnue-off-transcript.txt`: exact commands, UCI traffic, real output, and process outcomes for the four uninstrumented searches.
- `lock*-stdout.txt`, `merged*-stdout.txt` and corresponding stderr files: raw engine streams, including empty stderr files.
- `oracle_probe.cpp.txt`: complete scratch oracle query source.
- `oracle-transcript.txt`: the first invalid harness attempt, retained without alteration. It omitted engine feature definitions including PEXT while linking precompiled engine objects and segfaulted with exit 139. This was not an engine UCI crash.
- `oracle-correct-defines-transcript.txt`: the corrected harness compile uses the engine's feature/ISA definitions. The unchanged oracle then exits 0 and prints root/move DTMs plus every PV state's legality and remaining DTM.
- `inspection.txt`: source inspections and exact line references. It also preserves an exploratory `rg` error for nonexistent `include/forge/types.hpp`.
- `instrumentation-provenance.txt`, `instrument-build-transcript.txt`, `instrumentation.diff.txt`: scratch-only instrumentation provenance, its two-line logging patch, exact generation/compile commands, and real output. `git diff --no-index` exit 1 means the expected logging differences.
- `instrument-repro-transcript.txt`, `instrumented-nnue-off-stdout.txt`, `instrumented-nnue-off-stderr.txt`: the bounded instrumented reproduction and raw trace streams.
- `instrument-verification-transcript.txt`: unchanged source/production-binary hashes, scratch binary hash, complete trace, and successful deterministic stdout comparison.
- `instrument-command.txt`, `repro-command.txt`: final reusable command text; earlier command versions are preserved inside the transcripts that executed them.
- `preliminary-analysis.md`: initial findings before scratch instrumentation, retained as historical analysis rather than the final conclusion about instrumentation.
- `package-transcript.txt`, `package-check.txt`, `package-final-check.log.txt`: evidence-copy operations and verification. The first copy check accidentally included its own still-being-written log before that log had a destination copy; it reported a missing evidence file and exited 1. After the log closed and was copied, all byte comparisons passed. This was an evidence-packaging error, not an engine/test failure.

Only this investigation document and its text-evidence directory were added to the repository by this task. No commits or pushes were performed by the investigating agent.

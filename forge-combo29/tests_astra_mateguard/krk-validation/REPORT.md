# Narrow mate-alpha guard: frozen KRK validation

UTC: 2026-11-14T20:11:46.302Z. All work was in cloud VM private scratch. No engine source, branch, reference, or existing test was changed.

Candidate source and object hashes are in `inputs.json.txt`; native binary hash is in `binary-sha256.txt`. Compile command, exact input argv, real stdout/stderr and exits are in `compile.txt`, `soundness.txt`, `measurements.txt`, and `fixture.txt`. `run-batch.mjs.txt` is the inert text copy of the bounded execution recorder; its live VM script and binary are not deliverables.

The C++ driver links the seven current guarded Release core objects, excluding UCI, using the exact candidate feature/architecture/FP flags. OwnBook is absent from direct Searcher calls; Hash is 16 MB, every root starts from cleared searcher state, and all unrelated tune options stay at construction defaults. SoundMatePruning is false. A sets only MateAlphaGuard; B sets only the existing SoundArmMateAlpha test hook, with PV and in-check arms forced off.

Frozen inputs are copied byte for byte from the original soak: krk_roots.txt SHA256 87fe53e7508d24b4db07a92c3f6be600b493a481fc2b8d6505f9aa0c939c7a8d; krk_oracle.hpp SHA256 4bd157bdef50e809fd9e48630aa961b63cdca07cd2082dbe14d8464bbcdaa0b7. The oracle is an exact retrograde KRK algorithm sharing Forge board/move/attack primitives. It is not an independent external tablebase and does not model repetition or the fifty-move rule. Roots are fresh, White to move, halfmove clock zero, no castling or en passant.

## Acceptance: 40 frozen roots, depth 14, A, NNUE on

| Threads | Searches | Positive mates | Exact root DTM hits | Illegal | Lost wins | Report shorter than root | Report shorter than chosen-move DTM |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 40 | 40 | 31 | 0 | 0 | 0 | 0 |
| 2 | 40 | 40 | 40 | 0 | 0 | 0 | 0 |
| 4 | 40 | 40 | 40 | 0 | 0 | 0 | 0 |

All 120 searches reached depth 14. This sample has zero acceptance violations; it does not prove all searches or TT bounds sound.

## Measurements: 40 frozen roots, depth 13, Threads 1

Means include positive mate reports only; the explicit missing-mate column prevents treating excluded cp reports as exact hits. UCI mate distances are moves; exact retrograde distances and raw score conversions are retained in plies in every ROW.

| NNUE | Mode | Positive mates | Missing mate reports | Exact DTM hits | Mean reported minus exact (UCI moves) | Sum nodes |
|---|---|---:|---:|---:|---:|---:|
| true | off | 35 | 5 | 21 | 0.685714 | 740045 |
| true | A | 35 | 5 | 29 | 0.257143 | 897857 |
| true | B | 34 | 6 | 28 | 0.264706 | 1088994 |
| false | off | 31 | 9 | 21 | 0.870968 | 417491 |
| false | A | 31 | 9 | 25 | 0.225806 | 573188 |
| false | B | 31 | 9 | 26 | 0.16129 | 810985 |

All 240 measurement searches reached depth 13; zero illegal moves, lost wins, or shorter-than-oracle root/chosen-move mate reports. No speed or strength interpretation is made. The measurements do not show B uniformly closer across both evaluation settings.

## Original fixture

`8/8/8/8/8/1R6/2k5/5K2 w - - 0 1`, depth 13, Threads 1. Exact root DTM: 15 plies, UCI mate 8.

| NNUE | Mode | Result | Nodes | Chosen move / exact DTM |
|---|---|---|---:|---|
| false | off | mate 17 | 25568 | b3f3 / 17 plies |
| false | A | mate 11 | 36063 | b3f3 / 17 plies |
| false | B | mate 11 | 53950 | b3f3 / 17 plies |
| true | off | cp 449 | 50362 | b3b5 / 29 plies |
| true | A | cp 449 | 50362 | b3b5 / 29 plies |
| true | B | cp 449 | 50362 | b3b5 / 29 plies |

One fresh run per fixture setting here; root agent owns ten UCI repeats and observational semantic tracing. All six fixture searches reach depth 13 and return legal winning moves. Mate 17 and mate 11 are conservative deadlines, not claims of exact DTM.

## Completion record

Compile and all three bounded native batches exited 0. Full raw search output is retained, including actual reported time/NPS; these were not used for comparisons. Some batches overlapped other authorized native work, so elapsed values are execution records only. Independent record parsing verified 366 unique ROW records, 0 recorded soundness violations, expected group sizes, score-to-plies conversion, normal exit status, and unchanged source/object/input hashes. There were no engine edits or adjustments to expected values.

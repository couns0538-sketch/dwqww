# Independent static review of the known-root mate investigation

Reviewed committed snapshot `c1bb0c23bd77c02367daf95d0137ac8a846118f7` in `/workspace/work/dwqww-all`, plus the completed r3-21/23/24 static review and their exact source diffs. No engine, test, compiler, oracle binary, or other native workload was run. No repository file, branch, ref, or controller state was changed. This review reads retained outputs; it does not independently repeat their runtime results.

## Conclusion

The narrow conclusion **“a short, nonterminal PV does not demonstrate an invalid upper bound on mating distance” follows from the retained evidence**. For this root, the selected move is independently assessed as preserving a forced mate sooner than the printed deadline. The observed trace also explains how a mate-valued score can reach the root while the displayed PV ends before checkmate.

Three qualifications must remain explicit:

1. This does **not** establish that “mate 17” is the exact game-theoretic distance. The retained oracle gives root DTM 15 plies (mate in 8), selected move `b3f3` DTM 17 plies (mate in 9), while the printed “mate 17” corresponds here to 33 plies. The selected move is winning but is not the fastest mating move; `b3e3` has root DTM 15.
2. The raw UCI output does **not** contain `lowerbound` or `upperbound`. Calling its distance a “bound” is this investigation's weaker analytical interpretation of the mate claim, not a statement that the engine advertised a UCI bound qualifier. The evidence validates a mating deadline; it does not validate an exact-distance claim or prove correct UCI bound labeling in general.
3. The oracle establishes the chess result independently of alpha-beta. The trace establishes the observed score/PV separation mechanism. Neither is a full audit of how the engine originally derived every TT bound. “The engine's own proof was verified” would overstate this investigation.

The current report already acknowledges loose distance and unaudited TT creation. Its recommendation is sound when limited to this reproducer: no engine-code correction is justified merely because this displayed PV is short. A small documentation clarification about the absence of UCI bound qualifiers would make that limitation harder to misread. This reviewer has not edited the report.

## What the evidence actually establishes

The reported FEN is `8/8/8/8/8/1R6/2k5/5K2 w - - 0 1`, Threads 1, Hash 16, OwnBook false, fresh game/hash, depth 13. The retained NNUE-off transcript contains identical lock and merged outputs: `score mate 17`, 25568 nodes, `bestmove b3f3`, and the same 15-ply PV (`mate_pv_evidence/repro-nnue-off-transcript.txt:134-135,230-231`). The document separately reports that default NNUE-on gave cp449, b3b5, and an 18-ply PV. Conclusions about the specific mate17 reproduction should keep the NNUE-off setting.

The successful retained oracle transcript prints:

| Quantity | Retained result | Consequence |
| --- | --- | --- |
| Root exact DTM | 15 plies | Root can force mate in 8 moves under optimal play. |
| `b3e3` exact DTM including first move | 15 plies | Fastest listed root move. |
| Selected `b3f3` exact DTM including first move | 17 plies | Selected move preserves a forceable mate in 9 moves. |
| Published PV | 15 legal plies, endpoint not checkmate | The displayed line is incomplete. |
| Endpoint | Black to move, 3 legal moves, not checked, remaining DTM6 | That particular prefix can finish within 21 total plies with optimal continuation. |
| Engine score | 31967, printed mate17 | A 33-ply mating deadline is weaker than each of those oracle mating distances. |

A forced mate is a strategy against every defender reply, not one cooperative line ending in mate. The root and selected-move retrograde results supply that strategy-existence conclusion. The legal 15-ply PV alone does not. Conversely, a nonterminal PV alone cannot disprove such a strategy.

The 21-ply prefix result is conditional on that displayed prefix, not a separate all-defenses root proof. The selected-move DTM17 is the stronger all-defenses assessment. These checks do not imply that future independent searches by Forge will always choose the oracle's winning continuation.

## Oracle review

The scratch query includes `tests_t12/krk_mate_test.cpp`, renames its original main, constructs only `KrkTablebase`, and queries the fixed root, its legal moves, and the supplied PV (`mate_pv_evidence/oracle_probe.cpp.txt:1-38`). It does not execute the original test's repeated searches.

The primary oracle source blob computed from the inspected committed file is `329cad9acfee7e0a88e118911d14298818234244`, matching the recorded provenance. The `KrkTablebase` class in `soak_all/krk_oracle.hpp` is byte-identical to the original class: 7862 characters in each extracted class definition. The wrapper added below the copied class is not used by the historical scratch query.

Static review of the copied class finds the expected retrograde construction:

- `krk_oracle.hpp:72-85` rejects overlapping and adjacent kings, and prevents a White-to-move position where Black was already left in rook check.
- Lines 88-109 seed Black-to-move checkmate states after checking every king escape, including an unprotected rook capture.
- Lines 114-151 solve White positions by existence of a legal child with previous-ply DTM. Since distances are assigned in increasing order, this gives the shortest winning distance.
- Lines 152-188 solve Black positions only when at least one legal move exists, no rook capture/draw exit exists, and every legal child is solved; it uses the maximum child DTM. This supplies the defender's longest-resistance requirement.
- `move_mate_plies` at lines 40-56 checks the candidate move and adds one to the exact Black-to-move child result, explicitly rejecting immediate stalemate, rook loss, or an unsolved/drawn child.

This is an algorithm independent of Forge search, but it shares Forge's board/attack primitives. It is not an external tablebase validation. It omits repetition and the fifty-move rule. Those omissions do not invalidate this particular fresh-root result: halfmove0 plus DTM17 is below 100, a shortest-DTM strategy decreases DTM and avoids repeating a state, and the recorded 15-ply prefix has 15 distinct board/side/castling/EP states before a remaining DTM6. General roots with history or high clocks would need separate treatment.

No algorithmic flaw affecting this root was identified by this static inspection. This is not exhaustive independent certification of the entire tablebase implementation.

## Score bounds, distance bounds, and PVs

`include/forge/search.hpp:65-75` defines MateValue32000, mate threshold31872, `BoundUpper=1`, `BoundLower=2`, and `BoundExact=3`. In negamax, a TT bound is on the numeric score from the side to move. It is not directly a bound on distance measured in moves.

The retained endpoint trace is:

```text
TRACE_QPV_FINAL root_depth=13 ply=15 alpha=-31967 beta=-31965 score=-31967 pv_length=0 tt_score=-31967 tt_raw=-31982 tt_bound=1 tt_depth=9 fen=8/8/8/8/8/5R2/1k1K4/8 b - - 15 8
```

At this Black-to-move endpoint, the oracle's actual remaining distance6 translates to a current-root-ply score of `-32000 + 15 + 6 = -31979`. Thus the cached upper score bound is consistent: `-31979 <= -31967`. Equivalently, its position-relative form `-31982` is a loose upper bound on the exact position-relative `-31994`.

Negating an upper bound reverses its direction. After the odd number of plies to the White root, the corresponding winning score is a **lower score bound** 31967. Because larger winning mate scores mean shorter distances, that implies an **upper bound on mating distance**, 33 plies. The oracle's exact root score31985 and selected-move score31983 are both above31967. Do not call the root's positive value a numeric score upper bound; it is the mating *distance* that is bounded above.

This arithmetic shows consistency of the observed bound with exact KRK values. It does not prove the stored bound had a sound original derivation. `BoundExact` likewise denotes an engine search-bound classification; in a selective search it is not automatically a proof of globally exact DTM.

## Why the PV is short

Source at the committed snapshot:

- `src/search.cpp:1048` resets qsearch PV length to zero.
- Lines 1075-1079 can return eligible TT scores at non-PV nodes without PV reconstruction. That is a general mechanism; the traced endpoint is instead the final-return path at line1169.
- Lines 1092-1097 substitute an eligible TT score for qsearch's evaluation, including this negative BoundUpper score.
- Qsearch generates captures/promotions outside check. A quiet bare-black-king position cannot extend the line through such a move. With no searched child improving the result, the PV stays empty; lines1163-1169 attempt a store and return the numeric result separately. The bound passed to that store attempt is also upper, not exact; the deeper existing entry can cause the attempted score write to be rejected.
- Lines 1151-1154 and 1526-1529 copy only the available child PV. Root lines1808-1814 copy score and PV into separate fields.
- Lines198-202 compute `(32000 - abs(score) + 1) / 2` and format mate; lines1672-1682 print the available PV without checking whether its endpoint is mate and without printing bound qualifiers.

The scratch patch adds only two logging statements. The retained verification transcript records a complete stdout comparison after removal of only `time` and `nps`, exit0, with the same nodes, best move, score and PV. The endpoint trace has the same position, ply and returned value as the displayed line. This supports the documented endpoint mechanism. It is not a trace of all predecessors that created the TT entry; the report correctly says those remain unaudited.

No mate-PV-length check should be treated as a soundness oracle. Filling a PV through TT moves would be a separate reconstruction task, with cycle/legality/provenance issues. Clamping a reported distance to a shorter displayed PV would make a stronger claim that the incomplete line does not justify.

## Final r3-21, r3-23, r3-24 do not resolve this evidence gap

The reviewed final source diffs are retained here as commands014-016 and plain diff files. They agree with `/workspace/work/all-run/branch-review-r3-complete/clock-review/review.md`.

- r3-21 `1d7440c1f860be9c21e190c862d5920b241dd927` adds the in-band mate-score conversion guard. The specific trace adjusts `-31982 + 15 = -31967`, still <=-31872, so the new guard does not reject it. This is a real separate arithmetic candidate already implemented by its source commit `af1c998304dbfbcb997b757a7ce43af7cdf6e933`, not a repair for this short PV.
- r3-23 `91a852100912c9f0a13b809a4fed12a93feda4da` adds default-off `SoundMatePruning`, skipping a shallow main-search pruning block in PV/check/mate-alpha cases. It does not change the observed qsearch return or reconstruct PVs. Its proof case changes mate distance and checks a legal mating PV; as the final review notes, the included test does not enumerate every defensive reply to prove exact DTM. It may affect this root's earlier tree when enabled, but no evidence here establishes that outcome.
- r3-24 `0ca8cb1009dfd1c8e58dc793c3e760d1c88628f3` re-finds TT entries after stale probes and preserves a deeper move on rejected redirected stores. No stale-slot duplicate event was traced in this root. It may change traversal but has not been shown to fix its mate/PV behavior. The full implementation includes both `305bfc30...` and `e838ec9a...`; the final tip itself mainly strengthens tests.

## Is a less-than-60-line default-off fix justified?

**No such engine fix is justified by the known-root evidence alone.** The reproducible observation is a loose mate distance and incomplete PV for a move that still forces mate within the printed deadline. A switch that suppresses cached mate scores or changes displayed distances would change behavior without establishing that the original mating deadline was false. A reconstruction switch would be a display feature and would not validate the score's underlying proof.

r3-21 demonstrates a distinct small arithmetic issue, and r3-24 a distinct storage issue, but they already exist and neither is the traced cause here. Treat them as separately identified candidates subject to the user's integration/validation rules, not as newly invented Part4 fixes. r3-23 is an existing optional pruning candidate, not a comprehensive mate-proof switch.

A new Part4 correction would need an invalid mating deadline, a selected move that cannot force mate within it, or a specifically traced unsound bound operation. The retained evidence establishes none of those for this root. It also does not rule them out elsewhere. If the acceptance target is instead *exact shortest DTM*, this root demonstrably misses that stronger target and the report should say so rather than relabeling it a successful exact-distance test.

## Evidence

Directory: `/workspace/work/all-run/part4-static-review/`.

- `commands.txt`, `001-...txt` through `016-...txt`: exact read-only command argv, UTC, cwd, exit, full stdout/stderr. The first record pins the committed HEAD.
- `*.numbered.txt`: original-line-number copies of inspected committed report, sources, oracle query and retained native transcripts, plus the final r3 review.
- `r21-source-diff.txt`, `r23-source-diff.txt`, `r24-source-diff.txt`: complete inspected final source changes.
- `oracle-class-static-comparison.txt`: byte-comparison result for the original and copied oracle class.
- `static-calculations.txt`: explicit arithmetic results and retained-PV state counts; these are computations on text evidence, not new engine runs.
- `SHA256SUMS.txt`: evidence manifest.

All writes by this reviewer are in this separate scratch directory. Existing evidence, reports, expected test values, source, branches, and active workloads remain untouched.

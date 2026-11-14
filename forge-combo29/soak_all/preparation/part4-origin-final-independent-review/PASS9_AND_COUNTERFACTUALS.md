# Direct pruning evidence and private counterfactual review

This review reads retained logs, scratch source, and exact Git objects. It performs only static parsing and KRK geometry checks. No native workload, production edit, experiment-state change, or ref mutation was performed by this reviewer. These diagnostics remain outside the pinned soak totals.

## Confirmed omission

Pass 9 adds logging immediately inside the existing futility branch and around legal move selection. The source diff leaves the original conditions, `skip_quiets` assignment, and `continue` in place; callbacks only record copied values. The trace has 3,969 contiguous events, including 38 LATE_MOVE events. Full stdout and repeated trace identity pass independently; all three executions exited 0. Trace-r1 SHA256: `55f5f9b16eb66ca71e02fd9e6d9fb0c055cdf7b7f177f952d3d2d9c628c693db`.

The previously inferred omission is now directly recorded as **FUTILITY_SKIP_TAIL**, pinned `src/search.cpp:1400`:

| Frame | Depth | Pruned move | Static eval | Alpha at skip | Raw trace sequence |
|---:|---:|---|---:|---:|---:|
| 24345 | 4 | d1c1 | 521 | 31982 | 3646 |
| 24347 | 2 | d2c2 | 473 | 31982 | 3632 |
| 24349 | 5 | d1c1 | 521 | 31982 | 3693 |
| 24351 | 3 | d2c2 | 473 | 31982 | 3679 |
| 24358 | 5 | d1c1 | 521 | 31979 | 3785 |
| 24360 | 3 | d2c2 | 473 | 31979 | 3771 |

Each event sets `skip_quiets=1` after an initial searched move has returned 31979. In the last two rows' parent searches, alpha rose from an ordinary 441 to mate-band 31979 before the omission. This is a comparison between an ordinary static evaluation and mate-band alpha, not an extra generation update or corrupt child Exact payload.

There is a concrete omitted mating continuation at frames **24349 and 24358**, not just a discrepancy with an abstract DTM number. Their entry position is `8/8/8/8/8/3R4/8/k2K4 w - - 8 5`, ply 8, depth 5. The pruned move starts:

`d1c1 a1a2 c1c2 a2a1 d3a3#`

Independent static geometry verifies all moves; at each Black turn the listed reply is the **only** legal move. The final board is checkmate at clock 13. Replaying the exact recorded eight-ply ancestry from the original root followed by this continuation produces no repeated board/side. This proves a mating score **at least 31987**, exceeding beta **31983**, where the recorded search returns **31979**. The five-ply continuation fits those nodes' entry depth 5. The same line exists at frame 24345, but exceeds its entry depth 4, so its depth claim must be kept separate. This establishes a specific missed mate within the depth-5 nodes; it does not prove that the original root's slower mating deadline was false.

## Static-evaluation substitution guards: retained limited outcomes

The private patch adds two independent compile flags, both default 0, which exclude mate-band TT scores only from substitution into local `eval` in qsearch or main search. It leaves TT cutoff returns and score conversion intact. Main `ss->static_eval` already stays ordinary before and after substitution, and that is what the problematic quiet-futility condition uses. Therefore the main substitution guard does not directly repair the recorded pruning predicate.

All four variants were run twice in the retained evidence, T1/Hash16/OwnBookfalse/NNUEfalse/depth13; every process completed, exit 0, signal null, empty stderr, and repeat stdout agrees after removing only time/nps. These are measured node counts, not speed conclusions.

| Private variant | Score | Nodes | Move | PV plies |
|---|---|---:|---|---:|
| Both flags off | mate 17 | 25568 | b3f3 | 15 |
| Qsearch substitution guard only | cp 547 | 29527 | b3f3 | 14 |
| Main substitution guard only | mate 18 | 24899 | b3f3 | 15 |
| Both guards | cp 546 | 29689 | b3f3 | 14 |

Off reproduces full pinned stdout apart from time/nps. Qsearch-only and both remove the mate report in a position already known to be won; main-only still reports a mate with a short nonterminal PV. None supplies a corrected mating PV or establishes that a false deadline was repaired. These limited variants must remain in the record and should not be promoted as a fix merely because the mate output disappeared.

## Existing r3-23 experiment

I verified the scratch `search.cpp`, `uci.cpp`, and `search.hpp` byte-for-byte against **21867c5ac27a8db6f4d8dd2187c4fa7ede5204e8**, using read-only Git object reads. This is the newer source used by this experiment, distinct from the historical final-24 snapshot tip. It adds the default-false SoundMatePruning option and independently overridable PV/in-check/mate-alpha arms plus disabled diagnostic counters. Normal option mode follows all three arms; the counters are not enabled in these runs.

The option's mate-alpha arm directly prevents entry into the shallow move-pruning block whenever `is_mate_score(alpha)`. It therefore covers the six observed skip conditions if the same states are reached. This mechanism matches the recorded omission more closely than either static-evaluation substitution guard. It still does not protect every search reduction/cutoff, guarantee globally exact DTM, or reset a quiet-skip state established earlier in a different search history.

The retained exact-branch experiment gives:

| SoundMatePruning | Score | Nodes | Move | PV plies |
|---|---|---:|---|---:|
| false, two repeats | mate 17 | 25568 | b3f3 | 15 |
| true, two repeats | cp 488 | 24738 | b3g3 | 14 |

Both repeat checks pass, all four processes exit 0 with empty stderr. Off matches the pinned transcript after removing only numeric time/nps and the exact newly added option-advertisement line. On changes the chosen move and returns a centipawn score; it does not demonstrate a repaired complete mating PV. The three-arm option result cannot isolate the mate-alpha arm's effect. A separately prepared mate-alpha-only experiment is pending at the time of this report and is not presumed successful.

## Review evidence and limits

Exact commands/results are in `pass9-instrumentation-command.txt`, `pass9-and-guard-independent-command.txt`, `pass9-omitted-mate-line-command.txt`, `guard-complete-read-command.txt`, and `r3-23-corrected-source-result-command.txt`. Complete late events are in `pass9-late-pruning.json.txt`. The existing `PASS8.md` preserves earlier source-chain, actual terminal, oracle, and selective-search limitations. A scratch evidence-write attempt failed due a malformed patch newline join after its read command succeeded; no source changed, and the corrected read/result record is retained. No failed or limited native variant is omitted or reclassified as a fix.

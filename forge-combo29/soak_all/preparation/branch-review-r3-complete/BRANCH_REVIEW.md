# Final 24-branch r3 review

All 24 final heads contain implementation changes relative to `e04556ddc3a430b2e751159b0d46111ef56c8b89`. This is a **static source/test review**, not acceptance of the branches' native test claims or authorization to merge them. The eight-hour experiment remains on its pinned source and configuration.

The final snapshot was recorded at **2026-11-14T15:00:12.976Z**, SHA256 `3d0799f2b3c446a9e2543a5c76e735501af46ae08569cb7252c98bbeddcb97b7`. It supersedes the earlier **13:51:59.287Z** snapshot for branch status. In particular, r3-21 and r3-23 were placeholders at the earlier snapshot and now have real changes; r3-05/06/07/22 also now have implementations. r3-24 advanced from its first implementation to a stronger fix and tests. The earlier snapshot and review are preserved under `branch_review_evidence/historical/`; they are historical evidence, not the current branch inventory.

All exact commit objects were already available to the reviewers; no fetch was required. Reviewers ran read-only Git/text inspection, with no native builds, engine searches, sanitizer executions, games, checkouts, merges, ref updates or changes to experiment/controller state. Their only writes were scratch reports/evidence. Exact source comparisons confirm that the pinned engine and review base have the same `forge-combo29/src` and `include`; pinned `src/search.cpp` SHA256 is `2b14b62cd675b047478e70b738932ce4c2c699239b3c0de4ec43551464dc8819`.

## Decisions supported by this review

The most focused candidates to reuse later are **r3-21's mate-band conversion guard**, **r3-24's final stale-slot and move-preservation correction**, and **r3-17's malformed-position/legal-prefix and multiworker node-budget changes**. They address concrete mechanisms with relevant regression tests. Reuse their implementation commits and final tests; many final tips are report-only or test-only commits. The exact mapping appears below.

**r3-22's empty-clock-reserve handling is also relevant correctness work**, but its independent branch leaves a source-level stale-helper-count concern after a prior multiworker search followed by an empty-clock terminal root. Its tests use fresh multiworker Searchers for empty clocks; the reused fixture is only one worker. r3-17's counter reset addresses the relevant mechanism, but a combined version has not been tested. Treat r3-22 as a candidate needing that interaction checked.

The remaining default-off options are separate experiments. Their flags being false can preserve the old decision formula, but does not mean every default observable is unchanged: UCI advertisements change, and some add storage or bookkeeping even while off. The three optimization branches 18–20 change normal execution and require their own identity, portability and sanitizer validation. None supplies demonstrated repair of the current eight required equality failures, the original Part-4 short-PV observation, or a substitute for current race/self-play evidence.

## All 24 branches: effect and disposition

Names below are suffixes of `grok47/r3-`. “Off” means the added check option initializes false, unless otherwise stated. Disabled-path statements are source findings, not independent bench runs.

| No. | Branch | Default and actual effect | Finding / later use |
| --- | --- | --- | --- |
| 01 | eval-rule-50-damp | Off; scales corrected evaluation by clock and requires matching TT score clock when enabled. | Evaluation heuristic, not restoration of t23 traversal. Hash clears on toggle; learned histories remain. |
| 02 | threat-history | Off; per-worker quiet history keyed by threat buckets. A 64-KiB table is allocated/cleared per worker even off. | Distinct from t22 continuation history; useful threat-classification fixtures, no independent move-safety/mate proof. |
| 03 | lmr-signed-correction | Off; signed corrected-minus-raw evaluation adjusts quiet LMR. | Interacts with NonPawnCorrection; formula and legality/PV tests do not establish tactical correctness. |
| 04 | lmr-late-parent-relief | Off; arrival-index bookkeeping remains; reduces LMR for selected early replies to late parent moves. | Cannot rescue already-pruned moves; lacks focused arrival/reply-boundary assertions. |
| 05 | hindsight-depth | Off; extra stack storage/reset remain; enabled reduced calls pass withheld depth and selected children lose/gain a ply. | Deep-TT gate is broader than “TT answers the node”; usability/bound/clock are not checked there. |
| 06 | null-threat-verify | Off; selected low-depth null cutoffs get non-null verification when geometrically threatened. | New blocker bookkeeping; geometric threats include pinned attackers. Overlaps 07, but is not equivalent. |
| 07 | null-see-veto | Off; legal cheaper-for-dearer, non-losing captures veto a null attempt. | Predicate/restoration/PV fixtures useful. Combined policy with 06 is untested. |
| 08 | asp-capped-reopen | Off; aspiration failures reopen by 13 or fully at decisive/mate scores. | No assertion proves special paths executed; legality sampling alone cannot establish bound behavior. |
| 09 | asp-arm-late | Off; arms after one in-window iteration, normally narrowing at depth 2 instead of baseline depth 4. | Name is misleading relative to baseline; added soft-stop guards are control-flow redundant. Not an established timing fix. |
| 10 | evasion-ordering | Off; changes capture-evasion scores; prior quiet-evasion mix remains. | Useful returned-PV legality walk. No direct ordering or mate-distance proof. |
| 11 | dead-material | Off; special KK/minor/KNNK/KBNK static evaluation and routing. | KNNK is not universally dead under chess rules; code gives a heuristic zero, not a complete dead-position oracle. Not current KRK/KQK/KBBK repair. |
| 12 | soft-nodes | Opt-in `go softnodes N`; ordinary `go nodes N` keeps its old hard-budget mode. | New protocol feature, not default fix. Main-worker target/cap and mixed-keyword/SMP caveats remain. |
| 13 | quiet-extinction | Off; heuristic quiet futility/tail closure after misses. | Tail closure can discard later checking quiets. No mate/pruning-soundness oracle; keep experimental. |
| 14 | draw-jitter | Spin option defaults 0; nonzero adds traversal-dependent draw offsets. | Setter retains TT/history; warm toggles can reuse bounds learned under another span. No counterexample run here. |
| 15 | tm-finish-iteration | Off; predicts next iteration from measured costs on game-clock path; final revision changes spike estimate. | Optional timing policy; mixed clock+depth/node can enter it. Not a fix for unclocked depth-only cutoff. |
| 16 | tm-node-share | Off; scales clock target from root-node share; final revision adds info logging. | Clock-only behavior needs clock-path tests; its depth-only fixture does not exercise scaling. |
| 17 | merge-legal-node-limit | Unconditional: retain legal prefix of malformed position; helper budget checks and pre-start counter reset. | Targeted later correctness candidate, relevant to malformed UCI and multiworker node accounting. No wall-clock deadline added. |
| 18 | lazy-net-accumulator | Default NNUE execution rewrite and fused Worker update/evaluation. | No pinned-path defect found by inspection. Some identity mismatch counters do not affect exit status; read their actual counts. |
| 19 | faster-hce | Default evaluation rewrite, including NNUE residual path. | Unguarded `_pext_u64` calls break non-BMI2 portability by inspection; pinned x86-64-v4 has BMI2. Requires independent validation. |
| 20 | faster-search-plumbing | Default picker/move-generation/TT plumbing rewrite. | Forces explicit `FORGE_SPD_SLIDER_PEXT=0` to 1 on BMI2. Build-selection contract changes; no combined identity proof. |
| 21 | mate-score-tt | Always on; rejects ply-adjusted TT mate scores that would cross into ordinary-score band. | Small targeted correction worth reusing; seeded-bound proof, not naturally produced long-mate validation. |
| 22 | time-safety | Always on; zero usable clock reserve returns legal fallback; clamps soft budget to hard. | Relevant clock guard, with reused-multiworker terminal-count gap noted above. Not a depth-only deadline. |
| 23 | sound-mate-pruning | Off; suppresses shallow move-loop pruning on PV/in-check/mate-alpha nodes. | Narrow optional behavior fix. Included test replays one mating line; no retained exhaustive reply/minimum-DTM oracle. |
| 24 | tt-duplicate-shadow | Always on; redirects stale-slot writes to existing key and preserves rejected stale move. | Targeted final correction worth reusing; strengthened serial and two-thread fixtures. Same-slot move refresh intentionally unchanged. |

There are 15 added default-false check options, one default-zero draw option and one opt-in soft-node command; seven branches change ordinary/default execution. These categories describe implementation effects, not permission or test status.

## Material limitations and interactions

**Implementation findings requiring attention before later adoption:**

- **19 portability:** final `src/eval.cpp:220–221,283–284` calls `_pext_u64` without guarding BMI2. This is a source-derived non-BMI2 build regression, not a compiler failure reproduced here. It does not imply a failure on the job's x86-64-v4 target.
- **20 build flag:** final `include/forge/bitboard.hpp:17–19` overrides explicitly supplied `FORGE_SPD_SLIDER_PEXT=0` on BMI2. A requested multiply-magic configuration no longer exercises that implementation.
- **14 warm toggles:** final `src/uci.cpp:324–325` changes DrawJitter without clearing TT or learned histories. Tests use fresh Searchers for fixtures and do not cover warm mode restoration. 01/11 clear hash but retain histories; they also are not equivalent to a fresh process after toggling.
- **22 idle helper counts:** final `src/search.cpp:1689–1708` can use total_nodes at a terminal root before the empty-reserve fallback; skipped helpers can retain earlier counts. This remains a static concern, not a reproduced engine fault. Review 17+22 together for later accounting validation.
- **18 test exit status:** `tests_r3_18/lazy_eval_identity.cpp:199–200,214–215,262–275` records some evaluation mismatches but returns 0 regardless. Its claimed zero counters must be inspected directly; generic exit-0 language is insufficient.
- **05 TT gate:** final `src/search.cpp:1243` uses hit/depth alone to suppress a depth adjustment, whereas an actual cutoff also requires usable score, a suitable bound/window and clock eligibility. This is a heuristic/specification gap, not a proven illegal outcome.
- **13 quiet checks:** tail closure skips remaining ordinary quiet stages, including later checking quiets. Its separate one-miss futility check's `!gives_check` exemption does not protect them from tail closure. No direct counterexample was run.

**Independent branches are not a tested stack.** 02 adds to quiet scores also affected by ContHist4PlyRead; 03 reads correction influenced by NonPawnCorrection; 03/04/05 alter LMR at stages different from LmrDeeperShallower. 06 and 07 change the same null policy in different ways. 08 and 09 alter aspiration. 01/11/14 can interact on endgame/draw scores. 18/20 rewrite search.cpp, while 19/20 both change slider initialization/header behavior. Standalone default pin claims do not establish combination behavior. Existing t22 tests enable only the original three switches, so their results cannot be relabeled as coverage of r3 options.

**12 is not an aggregate SMP cap proof.** Its 4N threshold is the main-worker mechanism. Tests are Threads1; they do not prove an aggregate multiworker 4N limit. `go softnodes A nodes B` leaves the soft flag set and applies the later B value softly. The branch does not contain 17's helper-budget reset changes.

**15/16/22 require a real engine clock to address clock behavior.** Pure depth-only/node-only searches do not enter the new clock decisions. The reviewed E5 specification set depth9 with no engine clock; its CLI nodes0 is ignored by that depth path. The driver's game-boundary-only deadline can be exceeded within a game/search and hit an external cutoff without violating a requested engine clock. That observation does not itself establish a timer bug, deadlock or race outcome. Retry and native fault accounting remain with the controller.

**24's new coverage is stronger but bounded.** The earlier first-cut move mismatch is corrected by `e838ec9a…`; final tests assert move/PV preservation and the opposite deep-late order. The two-worker “Exclusive” smoke still takes the locking route because the lease requires a single active worker (`src/search.cpp:2021–2039`); it does not directly exercise the owned route. Test collision keys depend on multiply-high indexing; the two-thread test explicitly uses `__int128`. The scan uses a 32-bit tag, does not remove existing duplicates, and keeps same-slot rejected move refresh. The hammer permits two possible score values and relies on sanitizer execution for race detection; ASan alone is not a race detector.

## Relation to the ongoing job

The original Part-4 KRK reproduction uses UseNNUE=false and prints `score mate 17` with a short nonterminal PV, **without a UCI `lowerbound` or `upperbound` qualifier**. Treating that value as an at-most-33-ply mating deadline is a deliberately weaker analytical interpretation; the engine did not advertise a bound flag. The retained oracle gives root DTM 15 plies and chosen-move `b3f3` DTM 17 plies. It therefore supports that the chosen move can force mate within 33 plies, while also showing that the printed distance is not the exact shortest DTM and the chosen move is not the fastest mating move. This does not certify the engine's own derivation of every TT bound or its UCI bound labeling.

The recorded endpoint has raw TT score -31982 at ply15, yielding -31967; 21's new mate-band guard leaves that particular value intact. 23 changes a main-search pruning block, not qsearch PV reconstruction; 24 changes TT storage, with no duplicate-shadow event traced in that root. None establishes a verified repair of that observation, and the review makes no universal mate-correctness claim. The independent static qualification is retained in `branch_review_evidence/final/core/part4-static-review.md`.

The eight required under-80 equality failures remain **failures**. The existing scratch diagnostics restored the lock results by reversing t23 rule-50 behavior families: three TT families suffice for seven cases, while fault090 requires the broader tested restoration. None of the final r3 reports or this review reproduces those eight roots with the new branches. Default-off additions leave the relevant default decisions intact; always-on changes could alter traversal but have not been shown to repair equality. Explaining a branch or mechanism does not change the original expected criterion.

Current sanitizer/self-play/match counts refer to the pinned executable hashes and options. Unmerged r3 code has not received those tests. No source finding here should be reported as an observed new crash, illegal move, race, performance change or strength change.

## Later validation and reusable tests

A later integration can avoid duplicating existing code by starting with 21 and final 24, and evaluating 17 and 22 together for protocol/node/clock accounting. Each remains a separate change requiring the requested cumulative validation. Keep the 23 option separate and off unless its enabled behavior is explicitly selected and independently checked. Do not fold optimizations 18–20 or optional heuristics into a correctness-only integration based on this review.

Reusable regression patterns include 21's both-sign mate-band fixtures; 24's serial and ordered two-thread stale-slot cases; 22's empty-clock/ponder cases; 17's malformed-position/node-budget tests; and 03/04/07/10's returned-PV legality walks. 10's complete PV walk and 24's directed interleaving checks are especially concrete coverage that can be reused without inventing replacements. Their limits remain: legality is not a mate proof, one mating PV is not an exhaustive defense tree, and a short threaded smoke is not a soak.

The standalone new tests are not automatically registered by the base CMake target. A release build or empty ctest invocation does not run them. Any future native validation must compile/link with matching feature definitions and inspect actual output, including mismatch counters, rather than rely only on status 0. Branch-reported bench11/13/perft5 and sanitizer outcomes are author claims read from source/report text, not independently executed results of this review. No complete acceptance of the job's broader pin, cumulative sanitizer, TSan and match matrix is implied.

## Evidence and exact revision inventory

Detailed source-line findings and full command/output records are in these bundle paths:

| Scope | Detailed report |
| --- | --- |
| 01, 11, 14, 18, 19, 20 | `branch_review_evidence/final/eval-material-optimization/REVIEW.md` |
| 02–07 | `branch_review_evidence/final/search-02-07/REVIEW.md` |
| 08, 09, 10, 13 | `branch_review_evidence/final/search-08-09-10-13/REVIEW.md` |
| 12, 15, 16, 17, 22 | `branch_review_evidence/final/protocol/REVIEW.md` |
| 21, 23, 24 | `branch_review_evidence/final/mate-tt/review.md` |

`branch_review_evidence/final/core/final24-commit-inventory.json.txt` lists all final tips, every source/include/build implementation commit, all intervening commits and changed-file sizes. Its 72 read-only Git commands and full actual outputs are retained separately. The table below lists implementation commits chronologically; it does not assert that those commits alone contain every final test/report improvement. A final tip may be documentation-only or test-only. Future reuse must preserve the intended final tests as well as the implementation.

| Branch | Exact final tip | Implementation commit(s), oldest first |
| --- | --- | --- |
| `grok47/r3-01-eval-rule-50-damp` | `85e0961064799c8f49f129b1d856490436b44354` | `40c7c468b1c64ffdcb203e4df326e6bf70a77281` |
| `grok47/r3-02-threat-history` | `314585b72dc44374937e1549a3798d605da74d62` | `e4daba905d33ff8ea10da5f99cd9185236c5ae17` |
| `grok47/r3-03-lmr-signed-correction` | `577aa3e9b0537b8df0d12dfeb4236483a805d505` | `b5e97812eb8c69941b2fc3fac563d5ca4c016561` |
| `grok47/r3-04-lmr-late-parent-relief` | `f3ecae11d4cdf9fb58925853e25a340f921b53ba` | `cc48d5aad409661d085e05e0cfae709d5f349c04` |
| `grok47/r3-05-hindsight-depth` | `d102a4ead3edd0719f626120e814b3d47300fb28` | `affee1d2288243c1de3408e0c3f9bcc308e56de5` |
| `grok47/r3-06-null-threat-verify` | `5df8092a0a8fcbe52e2e4f8a3a874e3b64020f28` | `d6b4c73560727fbbf1c5594dad5d56daa16329ea` |
| `grok47/r3-07-null-see-veto` | `1a6235db4ffaa79bc67dd5051d989defa0cc55a0` | `56b27b1398a46afc26bc46114375b73c065f3076` |
| `grok47/r3-08-asp-capped-reopen` | `fd9f4f0f9efbb2e16d3056271e7d62dd23e8dab5` | `fef5e0023702bffb2a52a75c626b1596e43fdfbc` |
| `grok47/r3-09-asp-arm-late` | `a92af3d7293c254e4ee7f70bb2bd61b93d9935f9` | `ab72d3b07cc343a8f475b435ba88aa2bf4abb19d` |
| `grok47/r3-10-evasion-ordering` | `1cd68ed033cf90917e4d23a644bbe341c768d2c6` | `a2392f49dc81fbdb6db73213a0a500c472e7ab16` |
| `grok47/r3-11-dead-material` | `89487999cb6fa5618853c68adef18a0d9dc114f5` | `be2e2ec6ab8879dd802d804523faf7f6775d66d6` |
| `grok47/r3-12-soft-nodes` | `c808be4b01a9076754c782d68fdbb7797e4db7a1` | `4dad16648f4302953885a19c651074c87d193ca5` |
| `grok47/r3-13-quiet-extinction` | `2158d5832ceac299528ea5a6ca7883c3c742cf8c` | `192f66f43e30bd50456f3da89f9dfd636ef26a8b` |
| `grok47/r3-14-draw-jitter` | `041404af67a585969e8ed6ce8906b4b270b7ffc7` | `e1b0f720134f0dc1b15948c7fb95aa29f2e2740d` |
| `grok47/r3-15-tm-finish-iteration` | `8283f8e97259a469b9d7601924c6a2d607b7e4f8` | `d59a448b9f52a6acffba58926c303e60080df86a`<br>`4db1f6b29abd880d3ac107ae3e6e5e40a783b7b2` |
| `grok47/r3-16-tm-node-share` | `2be1e21b6faa3e8e3d80ff79449102b4e9f250f9` | `cdd97af4c4338669cb59ce4cda5297f5143d1265`<br>`2849b637056227cb77b45a510ac12ded835d35b4` |
| `grok47/r3-17-merge-legal-node-limit` | `74b18517d0a20e25a20cffd62b6a32ac27707e74` | `681f9302fe409e7285719a8f62aef8f0c90f874c` |
| `grok47/r3-18-lazy-net-accumulator` | `1316c38c1cd6dce7ae719804ca72b43b4c2fc165` | `863417a76c027200ee487f63fb890d6e7fa526ff`<br>`1316c38c1cd6dce7ae719804ca72b43b4c2fc165` |
| `grok47/r3-19-faster-hce` | `3def809de68d726715fa3dd21626f706f0f30e16` | `5d9d1b70388bcb47f38cdc277776753e2c249c9a`<br>`758df95baabcdb2dd97aaa9b5507518b5cd02450` |
| `grok47/r3-20-faster-search-plumbing` | `7fef1fc378b6c966649315c11573bbdc1529435e` | `69460cd7062a8add4126f7bf809c03aa3b1ac4a2`<br>`f522db9138c3578295deb78dcef4ca4c466564b5` |
| `grok47/r3-21-mate-score-tt` | `1d7440c1f860be9c21e190c862d5920b241dd927` | `af1c998304dbfbcb997b757a7ce43af7cdf6e933` |
| `grok47/r3-22-time-safety` | `82fb89cbd815ad4427d8fd7d5a78d002e1c8fee7` | `6cecedda933054270cac45bacf367414b13c3fe0` |
| `grok47/r3-23-sound-mate-pruning` | `91a852100912c9f0a13b809a4fed12a93feda4da` | `91a852100912c9f0a13b809a4fed12a93feda4da` |
| `grok47/r3-24-tt-duplicate-shadow` | `0ca8cb1009dfd1c8e58dc793c3e760d1c88628f3` | `305bfc30f05c4020ef01a6992f419d9b27a7cfe2`<br>`e838ec9a16992418de267dfa3372d74d80f207f2` |

Read this inventory at the frozen snapshot only; remote branch names may advance later. All reviewer command errors and exploration notes are retained as evidence rather than silently omitted. Inspection-path or extraction errors are not engine failures. The final bundle manifest records content hashes and byte lengths; it does not certify native test outcomes.

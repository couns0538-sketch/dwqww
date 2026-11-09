# Review log (policy: AGENTS.md at 3e900941, md5 94169aef, section "Development review and verification")

The reviews below are this job's own: R1-R3 by one subagent (opus-max) in a fresh context, read-only, and H1 by a bug-hunting subagent (Fable) at the end. They are independent of this job's reasoning, and they are **not** Code Review. Code Review and QA get the exact pack after this log.

## R1 - candidate 188f8ff on P6 tree ded9684
- The tree stayed frozen during the review. Report: `review/R1.md`. Process note from the reviewer: its first shell calls and board appends ran unpinned (trivial CPU), every engine or solver run was pinned.
- No requirement 1-5 violation found. Findings assessed by the main agent, each checked against the code or a run before acting:

| # | sev | finding | assessment | action |
|---|---|---|---|---|
| 1 | HIGH | loser's rounded d + c = 100 draw thrown away, shown as TB loss | CONFIRMED on the code (`dtz_rank` loss branch). My ledger line "selection is sound" was wrong | RED fixture from the exact oracle, then fix in the root mechanism (a search change) |
| 2 | HIGH | checkers skip the whole root on one undecided move, and "exact" comes from the engine's own flag | CONFIRMED | new `oracle_exact.py` + `exact_check.py`, no engine flag, roots judged per move |
| 3 | MEDIUM | rank 900 lumps true wins and draws | CONFIRMED | same fix: boundary moves resolved exactly at the root |
| 4 | MEDIUM | WDL-only root at counter 0 still shows a false TB win; fixture has no clock-0 rows | CONFIRMED | report from the root's own WDL at counter 0; fixture rows added. Move filter limit stays and is documented: WDL alone cannot see it |
| 5 | MEDIUM | null-move site judges the raw score, bit 2 has no test that can fail | CONFIRMED: my edit of the hook never applied (heredoc collapsed the anchor) | site added at both returns; masks compared. My conclusion "the replacement has no effect" was wrong: see R2 finding 1 |
| 6 | MEDIUM | dead or unfalsifiable sites; qsearch gate has no direct site | CONFIRMED | qsearch end site, mutant without the qsearch gate; hunk dropped: no effect |
| 7 | MEDIUM | G7 fixture one-sided and biased, toggle control differs | CONFIRMED | control rows reported, all 3000 rows, warm mode in the claim harness, toggle compared with a manual Clear Hash |
| 8 | MEDIUM | no live root with a third-occurrence child | CONFIRMED (keep always even) | 7-ply rows, root repetition flag |
| 9 | MEDIUM | no warm identity with tables; warm_identity false-alarms on the option list | CONFIRMED | option lines normalized, mode with tables and mixed clocks |
| 10 | LOW | SyzygyRootExact hides a valid result with the rule off | CONFIRMED | condition added |
| 11 | LOW | README / ledger statements | CONFIRMED | corrected |
| 12 | LOW | move_quality ignores the +1 clock | CONFIRMED | uses the same outcome rule |
| 13 | LOW | fail-open details in tools | CONFIRMED | exit codes, advertised-option check, invalid value fatal |
| missing 1-12 | | fixtures | accepted | see GAP_LEDGER.md and BENCH.md for what was added |

## R2 - recheck of the R1 fixes, candidate c0c86aa
- Report: `review/R2.md`. No requirement 1-5 violation, no BLOCKER. The reviewer's advisor tool timed out, so the report had no second read.
- Process note: its blocked driver left `tb_root_v5.exe` PID 2488 and `python.exe` PIDs 4200 and 8512 (0 CPU, no writes). Under the no-kill rule they were left alone and are reported in `STATUS.md`.

| # | sev | finding | assessment | action |
|---|---|---|---|---|
| 1 | HIGH | null-move replacement removed, false TB claim through a null move two plies before a zugzwang | CONFIRMED by rerun; my fixture was one ply too shallow and could not show it | replacement back as `SyzygyTbBounds` bit 4; fixture `zz2roots` (1250 roots) two plies back: 12 wrong returned null cuts with mask 3, 0 with mask 7, +0.03 % nodes. Raw null scores stay counted at the separate site `null_raw`: they are replaced, never returned |
| 2 | MEDIUM | G7 residue reaches the root and changes the move, all switches on (`8/q7/8/8/8/3Q1RK1/k7/8 b - - 87 44`) | CONFIRMED | store-side rule built from the reviewer's outline, in the main search only (no qsearch evasion case: no claim at any site without it). warm_clock false_warm 2 to 0; cost: control warm true 304 to 288 (parent 308) |
| 3 | LOW | shared walk budget makes the result order-dependent | CONFIRMED | rounds with a growing cap per move, memo kept, stop at the first proof. A two-phase variant (table-decided replies first) was tried on the exact rows: no gain (71 / 44 and 60 / 56 and 48 / 48 undecided / worse kept against 54 / 33 at budget 1000), rejected |
| 4 | LOW | with bit 2 alone an undecided loss shows as a blessed loss | CONFIRMED | the undecided return moved out of the bit 1 block |
| 5 | LOW | R1 items not yet effective | CONFIRMED | `special2.sh`: 7-ply repetition rows at root and UCI, underpromotion rows, clock-0 and clock rows on WDL-only tables, rule-off rows; `quality` step in the suite; `warm_identity --tables` in `final_freeze.sh`; `false_claims.py` exits non-zero |
| 6 | LOW | status files behind the code | CONFIRMED | rewritten with the freeze |

## Own bug check after R2 (main agent, re-reading the final patch)
| # | finding | test first | action |
|---|---|---|---|
| B1 | `cap *= 4` in `resolve_boundary` overflows a signed int when a table the walk needs is missing: every round fails cheaply, so many rounds run. No fixture had boundary roots on a partial table folder | `gen_missing_child_fixture.py`: 15,495 KQvKR boundary roots on folder `nochild`: UBSan trap (exit 132) on 85e00a0 | cap limited to the budget, `e0ad013` |
| B2 | the store-side rule of `SyzygyRule50` bit 1 was not gated on `Syzygy50MoveRule` | rule off, 6000 roots, SyzygyRule50 0 vs 1: 651 rows differ on 85e00a0 | condition added, `e0ad013` |

GREEN of both: UBSan and ASan clean on the 15,495 roots with folders nochild, nodtz, rejected, wdl_only (`out/exp/hunt/`); rule off 6000 rows identical. Rule on, all switches on, against the full suite's v6 runs: root boundary byte-identical, engine rows identical on boundary (4569), clock (19905), 30000 roots above the tables.

## R3 - final recheck, candidate e0ad013
- Report: `review/R3.md`. **Nothing at BLOCKER, HIGH or MEDIUM**; the reviewer could not construct a false claim or a lost result on the store-side rule, the walk, bit 4, or the requirements. Second read by its advisor, after the report, not independent of it.
- Process note from the reviewer: three of its UCI drivers read pipes synchronously (none blocked), three short Python compares ran unpinned, one harness run took 374 s. A small scratch folder with its finding 8 demo sits outside the job root.

| # | sev | finding | assessment | action |
|---|---|---|---|---|
| 1, 2 | LOW | `BENCH.md`, the after_w6 patch and the freeze proof at head were not there yet | CONFIRMED, pending at that time | `final_chain.sh`, written at the frozen head |
| 3 | LOW | ASan never ran on the missing-child roots (exit 127: no MSVC environment) | CONFIRMED | `pinned_asan.ps1`, 4 folders under ASan with heap copies: exit 0, 15,495 rows each |
| 4 | LOW | G5's parent number 197 leaves out 258 kept moves the checker files apart | CONFIRMED | ledger: 455 against 33 |
| 5 | LOW | `warm_move_check.py` had no run | CONFIRMED | `info_runs.sh`, numbers in BENCH.md |
| 6 | LOW | README "every line of the node" overstates; a root entry stored without the raise can be read at a later clock; qsearch has no raise; no failing scenario | CONFIRMED by reading | wording corrected; I built the test the reviewer could not build within its rules: claim harness, two-position warm mode, `gen_warm_pred_fixture.py`: 0 wrong against 2290 in the control. No code change without a failing test. Listed under Limits for Code Review to judge |
| 7 | LOW | per-bit: `SyzygyRootExact` 1 and 2 alone keep wrong reports | CONFIRMED | stated in README |
| 8 | LOW | `after_w6.sh` fails open on a rejected hunk | CONFIRMED | no pipe on patch, `.rej` check, exit 1, also in `repro_from_pack.sh` |
| 9 | NIT | stale comment at the walk budget | CONFIRMED | `989399b`, comment only |
| 10 | NIT | README cites a G12 that does not exist | CONFIRMED | corrected |
| 11 | NIT | `green_v8.sh` cuts verdicts off its log | CONFIRMED | verdict printed; direct compare already identical |

## Own check at the frozen head
| # | finding | test first | action |
|---|---|---|---|
| B3 | the gaps patch does not apply on trial_w6 + port: hunk 11 of `search.cpp` has the main-search store line in its context, and trial_w6 wraps that line in `#if FORGE_SPD_TT_NOTLS`. The fail-closed check from R3 finding 8 stopped the line; with the old pipe the build would have gone on without the store-side rule of `SyzygyRule50` bit 1 and without the correction guard of `SyzygyTbBounds` bit 2 | `after_w6.sh` on 989399b: exit 1, `out/builds/after_w6_989399b.txt` | `patches/syzygy_gaps_after_w6p6.patch`: the same 234 changed lines in the same order, one hunk with new context. `after_w6.sh` now checks that, the preprocessed code with the speed switches at 0 against the P6 tree and the frozen candidate, no changed line inside a speed conditional (`w6_arm_check.py`), and all options on against the frozen P6-line build: nodes on bench, 30000 roots, all root fixtures, boundary roots, warm rows; UBSan with the six defines. The P6-line head is unchanged. Results in BENCH.md |
| B4 | tool bug in the new `after_w6.sh`: its compare check cut the JSON at 300 characters, before the verdict field, so identical rows counted as failed. It failed closed, so no wrong pass; the run ended with "15 checks failed" | that run's output: exit 1 | cut replaced; check tried on one identical and one different pair; `after_w6_compare.sh` repeated all 15 compares from the same row files: all IDENTICAL |
| B5 | a one-off script behind the claim "all bad boundary rows are on undecided roots" read the wrong column, so it called far too many roots undecided. The claim could have been false | same test on the parent, which has no undecided roots: it reported 1365 | `tools/und_check.py` reads the display column, with the parent as control (0 undecided, all 416 bad rows decided). The claim holds: frozen head 4 + 105 bad rows, all on undecided roots. It also showed the ledger's "54 of 2455" understated the limit's reach: 919 of 4569 rows, see Limits |
| B6 | `exact_check.py` skips a whole root when the solver left any move unresolved, so 1748 rows were never judged | `tools/exact_partial.py`: resolved moves alone prove errors, parent as control: 7 kept moves, 24 reports, 2 engine moves, 24 scores wrong | frozen head: 0 of each on 933 decided roots. No code change |

## H1 - bug hunt next to the final work, candidate 989399b
- Report: `review/H1.md`. One Fable subagent (`syz-hunter`), a different model from R1-R3, in a fresh context, read-only on the pack, scratch in `out/hunt_agent/`. Couns asked for it. It is not Code Review.
- Its mutants of the new code: m1 (TB distance off by one), m2 (store-side raise dead), m4 (rounded sum 100 taken as decided), m5 (walk cap), m6 (no hash clear on a rule change) were caught by the existing fixtures. m3 is equivalent (finding 3). m7 and m8 survived (finding 1).
- Its clean checks: the claim harness searches the same nodes as the real exe (3,388,358 on 300 roots); Threads 4 on 300 boundary roots without a bad row; 19 scenario probes; the trial_w6 line identical to the plain head on 300 boundary roots.
- Process note: every run pinned to 0xF000 at Idle, nothing killed. Leftovers in the job root: `tmp/hunt/junk_trees_m` (an empty tree copy) and `out/hunt_agent/runs/failed1`.

| # | sev | finding | assessment | action |
|---|---|---|---|---|
| 1 | MEDIUM | two read-side rules of `SyzygyRule50` bit 1 had no test that could fail: m8 (a stored probe result used at any clock) and m7 (a mate allowed to land on half-move 101) gave 0 wrong at every site | CONFIRMED: no fixture row reached a probed position again at a later clock, or read a stored mate exactly one half-move too long. A test gap, not an engine bug: the head had 0 wrong on every row before and after | test first, head unchanged. `tools/gen_warm_read_fixture.py` builds two row kinds where one rule decides (`fixtures/read.k0.tsv`, `fixtures/read.mate.tsv`); the harness got a qsearch mate site (same nodes and the same counts at the old sites). Head 0 wrong on both kinds; m8 239,790 wrong on the k0 rows, m7 18 on the mate rows, all at dtz + clock = 101; bit 1 off: 238,725 and 162. Each mutant leaves the other kind's nodes unchanged. The full 1500-row mate runs take about 3 h each at depth 14 and did not finish by the deadline, so the mate rows ran on the first 100 (`tools/read_subset.sh`). Numbers in BENCH.md, Stress |
| 2 | LOW | the mate sites judge a claim by DTZ + clock, not by the mate distance, so their counts are lower bounds | CONFIRMED, tool only, not fail-open | stated in HANDOFF.md; not changed |
| 3 | - | m3 (boundary memo key without the clock) changes no output on 4569 roots | equivalent mutant: the memo is only consulted where the clock follows from the position | none |
| - | unconfirmed | a mate score read much deeper than it was stored drifts below the mate band into the TB band (needs a root ply above about 120) | by reading only, not tested; P6's behaviour, not this patch's | listed for Code Review in HANDOFF.md |

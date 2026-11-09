# Review log (policy: AGENTS.md at 3e900941, md5 94169aef, section "Development review and verification")

The reviews below are this job's own, by one subagent (opus-max) in a fresh context, read-only. They are independent of this job's reasoning, same model family, and they are **not** Code Review. Code Review and QA get the exact pack after this log.

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

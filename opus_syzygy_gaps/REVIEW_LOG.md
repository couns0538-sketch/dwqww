# Review log (policy: AGENTS.md at 3e900941, md5 94169aef, section "Development review and verification")

## R1 - candidate 188f8ff on P6 tree ded9684
- Reviewer: one subagent (opus-max), fresh context, read-only. Independent of this job's reasoning, same model family, not Code Review. The tree stayed frozen during the review.
- Report: `review/R1.md`. Process note from the reviewer: its first shell calls and board appends ran unpinned (trivial CPU), every engine or solver run was pinned.
- No requirement 1-5 violation found. Findings assessed by the main agent, each checked against the code or a run before acting:

| # | sev | finding | assessment | action |
|---|---|---|---|---|
| 1 | HIGH | loser's rounded d + c = 100 draw thrown away, shown as TB loss | CONFIRMED on the code (`dtz_rank` loss branch). My ledger line "selection is sound" was wrong | RED fixture from the exact oracle, then fix in the root mechanism (a search change) |
| 2 | HIGH | checkers skip the whole root on one undecided move, and "exact" comes from the engine's own flag | CONFIRMED | new `oracle_exact.py` + `exact_check.py`, no engine flag, roots judged per move |
| 3 | MEDIUM | rank 900 lumps true wins and draws | CONFIRMED | same fix: boundary moves resolved exactly at the root |
| 4 | MEDIUM | WDL-only root at counter 0 still shows a false TB win; fixture has no clock-0 rows | CONFIRMED | report from the root's own WDL at counter 0; fixture rows added. Move filter limit stays and is documented: WDL alone cannot see it |
| 5 | MEDIUM | null-move site judges the raw score, bit 2 has no test that can fail | CONFIRMED: my edit of the hook never applied (heredoc collapsed the anchor) | site added at both returns; masks 5 and 7 compared; bit 2 stays only with evidence |
| 6 | MEDIUM | dead or unfalsifiable sites; qsearch gate has no direct site | CONFIRMED | qsearch end site, mutant without the qsearch gate; hunk dropped if it has no effect |
| 7 | MEDIUM | G7 fixture one-sided and biased, toggle control differs | CONFIRMED | control rows reported, all 3000 rows, warm mode in the claim harness, toggle compared with a manual Clear Hash |
| 8 | MEDIUM | no live root with a third-occurrence child | CONFIRMED (keep always even) | 7-ply rows, root repetition flag |
| 9 | MEDIUM | no warm identity with tables; warm_identity false-alarms on the option list | CONFIRMED | option lines normalized, mode with tables and mixed clocks |
| 10 | LOW | SyzygyRootExact hides a valid result with the rule off | CONFIRMED | condition added |
| 11 | LOW | README / ledger statements | CONFIRMED | corrected |
| 12 | LOW | move_quality ignores the +1 clock | CONFIRMED | uses the same outcome rule |
| 13 | LOW | fail-open details in tools | CONFIRMED | exit codes, advertised-option check, invalid value fatal |
| missing 1-12 | | fixtures | accepted | see GAP_LEDGER.md and BENCH.md for what was added |

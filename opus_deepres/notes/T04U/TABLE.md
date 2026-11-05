# T04U candidates: Clockwork #281 (T04T row 5) + unread closed-PR pages (Clockwork p4+, Tarnished p2+, motor p3+)
Reading: PR titles, PR bodies (OpenBench blocks), OpenBench test pages; no source file, diff or compare link
(Clockwork AGPL-3.0, Tarnished GPL-3.0, motor no licence). Lock = src_al1s198_clean (`s:` = src/search.cpp).
Bar for a full card: >= +3 STC, or >= +2 STC with an LTC result; ideas an existing card covers become "evidence for".
nElo = own conversion of the published penta (F:/odr/work/T04U/scripts/nelo.py, copy of the T04T script).

| # | idea | source | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|---|
| 1 | check extension moved into LMR | [Clockwork #281](https://github.com/official-clockwork/Clockwork/pull/281) (merge 305e45878f; tested dev sha 277b0cc44f vs base a0ceb385d6, branch check-ext-lmr; the PR body's bench line 11,073,468 differs from the tested dev bench 11,595,447, so the -33 % node drop belongs to the tested branch, not provably to one commit; branch commit list not read) | AGPL-3.0 | STC 8+0.08 +5.82 +- 3.96 n=9,724 [0,5] LLR 3.09 (+10.2 nElo); LTC 40+0.4 +3.35 +- 2.61 n=19,922 [0,5] LLR 3.04 (+6.2 nElo); book UHO_Lichess_4852_v1.epd on both test pages ([702](https://ob.cwchess.org/test/702/), [704](https://ob.cwchess.org/test/704/)) | HAS both parts: s:1112-1115 extension, s:1143 LMR r -= 1, s:1147 clamp | CARD T04U-01 (resolves notes/T04T/TABLE.md row 5 PENDING) |
| 2 | check extension introduced (context for row 1) | [Clockwork #83](https://github.com/official-clockwork/Clockwork/pull/83) (2025-06-12) | AGPL-3.0 | 8+0.08 +14.94 +- 8.24 n=4,492 [0,5] on the early engine | HAS s:1112-1115 | context for T04U-01: the extension paid on the young engine; four months later #281 moved it into LMR for +5.82 STC / +3.35 LTC |
| 3 | no malus for quiets that raised alpha before the cutoff move | [Clockwork #91](https://github.com/official-clockwork/Clockwork/pull/91) (2025-06-13) | AGPL-3.0 | 8+0.08 +6.02 +- 4.54 n=14,556 [0,5], no LTC, early engine (alpha-beta added 2 days before) | LACKS: the malus loop skips only the best move (s:744-749); quiets_tried holds every searched quiet (s:1186) | no card: PV nodes only (alpha < beta - 1), primitive-engine test, Forge estimate under +1 UNPROVEN (drop rule); not covered by T04R-03 (no-cutoff update) or T04G-05 |
| 4 | NMP on the TT-adjusted eval; NMP static-eval guard | [Clockwork #118](https://github.com/official-clockwork/Clockwork/pull/118), [#113](https://github.com/official-clockwork/Clockwork/pull/113) | AGPL-3.0 | +6.39 +- 4.71 n=12,288; +4.28 +- 3.41 n=22,162 (STC [0,5]) | HAS: eval takes the TT score by bound s:938-941; NMP uses it plus `ss->static_eval >= beta - 24 * depth + 180` s:965 | no card |
| 5 | qsearch in check: skip quiet evasions after the first quiet | [Clockwork #115](https://github.com/official-clockwork/Clockwork/pull/115) | AGPL-3.0 | 8+0.08 +5.85 +- 4.37 n=14,028 [0,5] | see card | evidence (variant) for T04F-01 (stop after the first evasion that is not mated) |
| 6 | LMR deeper / shallower | [Tarnished #57](https://github.com/Bobingstern/Tarnished/pull/57) | GPL-3.0 | 8+0.08 +5.84 +- 3.98 n=9,156 [0,5], early engine | see card | evidence for T04-02 (weak) |
| 7 | minor / major piece correction histories | [Tarnished #41](https://github.com/Bobingstern/Tarnished/pull/41), [#40](https://github.com/Bobingstern/Tarnished/pull/40) | GPL-3.0 | +16.91 +- 7.28 n=2,406; +4.28 +- 3.20 n=13,158 (STC [0,5]) | see card | evidence for T04-04 (early engine, short tests) |
| 8 | LMR also for checking moves (eligibility no longer excludes checks) | [Tarnished #47](https://github.com/Bobingstern/Tarnished/pull/47) | GPL-3.0 | non-reg [-5,0] +2.68 +- 3.79 n=9,596 | HAS: lock LMR has no gives_check exclusion, only `r -= 1` s:1143 | neighbour of T04U-01 (no card) |

Result: 1 full card (T04U-01, check extension moved into LMR; resolves notes/T04T/TABLE.md row 5). Unread pages: Clockwork
page 4 and Tarnished page 2 (its last page) are early-engine build-ups whose ideas the lock has or existing cards hold
(rows 2-8); two pages in a row without a new card, so motor page 3 was not fetched (cap rule).
Dead ends: row 3 (under +1 expected), row 4 (Forge has it), rows 5-8 (evidence only).
PENDING: motor closed PRs page 3+ (not fetched, cap rule); Clockwork closed PRs page 5 if it exists (#1-#22, setup
PRs by the numbering); the #281 branch commit list (which commit holds the bench drop).

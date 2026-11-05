# T05E verify (adversarial pass, 2026-11-05 01:15-01:3x PC clock)

Scope: cards/T05E/T05E-01..04 and notes/T05E/*. Method: every cited number re-opened at its source (fishtest
api get_run, GitHub commit / PR api, the test page, own git refs, own files); Elo recomputed from the pentanomials
(logistic, 95 %, pentanomial variance); licence rows re-run; Forge grep re-run; cited own-code lines read at
`origin/qa-r10v2-fix1` = 7f79c34901; duplicate grep over all 85 cards and notes/TRIED_GATES.md. Scratch:
F:/odr/work/T05E-verify/ (run_*.json, elo.py). No card was changed: nothing wrong was found.

Verdicts: CONFIRMED = number / claim reproduced at the source; UNVERIFIABLE = could not be traced here;
no CORRECTED, VIOLATION or DUPLICATE rows.

| card | claim | verdict | evidence |
|---|---|---|---|
| T05E-01 | Stockfish 49ef4c935a = PR 5183, "No functional change", 2024-04-24, three test links | CONFIRMED | gh api commit: message lists tests 662301573f (first), 6627fa063f (final), 662808133f (SMP); author 2024-04-20, committer 2024-04-24 |
| T05E-01 | final STC 10+0.1, 1 thread, UHO_Lichess_4852_v1, SPRT [0,2] normalized, 9,696 games, LLR 2.94, ptnml 30-964-2604-1204-46, +9.75 +- 3.48 | CONFIRMED | fishtest get_run 6627fa063fe04ce4cefc6560: tc 10+0.1, threads 1, book UHO_Lichess_4852_v1.epd, elo0 0 elo1 2 normalized, llr 2.940, W/L/D 2657/2385/4654; own recompute +9.75 +- 3.48 |
| T05E-01 | first version +17.36 +- 4.74, 5,408 games | CONFIRMED | get_run 662301573fe04ce4cefc1386: ptnml 13-514-1397-750-30, llr 2.93; recompute +17.36 +- 4.74 |
| T05E-01 | SMP 5+0.05 8 threads +3.13 +- 1.83, 32,672 games | CONFIRMED | get_run 662808133fe04ce4cefc667c: tc 5+0.05, threads 8, ptnml 34-3548-8887-3824-43, llr 2.95; recompute +3.13 +- 1.83 |
| T05E-01 | Eleanor PR 193 (merge 134af1abde): +39.43 +- 11.28, 4.0+0.04s Threads 1 Hash 8 MB, [0,5], LLR 2.95, 1,000 games, ptnml 1-73-251-162-13 | CONFIRMED | gh api pulls/193 body verbatim; https://bench.rektdie.com/test/5251/ shows "Elo 39.43 +- 11.28 (95%)"; own pentanomial recompute +39.43 +- 11.24 (the 0.04 is the error model); PR 180 title "8 king input buckets" |
| T05E-01 | chessgo 3eedea13d6 "+2.3% NPS, bit-exact"; onechess 928d53d2eb "+4 % NPS" (titles only) | CONFIRMED | gh api commits: titles "perf(nnue): ship finny refresh cache in prod loader (+2.3% NPS, bit-exact)" (2026-07-07) and "Table de Finny (+4 % NPS)" (2026-10-30); 6080c3c197 "table de Finny par tuiles" (2026-11-04) |
| T05E-01 | own code: refresh() = bias copy + one row_add per piece (src/nnue_halfka.cpp:436-445), row_add loads and stores the whole row per piece (:125-146), search.cpp:668-675 refreshes on any orientation change, no cache; AccumulatorStack hpp:66-81 | CONFIRMED | git show origin/qa-r10v2-fix1 at those lines (ft_bias copy, loop over occupied with row_add; AccumulatorStack valid/king/bucket[2][1024]) |
| T05E-01 | loader bound: |bias| + 32 x max|w| <= 32767 per output | CONFIRMED | src/nnue_halfka.cpp:394 rejects nets with `abs(ft_bias[j]) + 32 * wmax[j] > 32767` |
| T05E-01 | R10 tool: refresh 626.5 ns, update 124.5 ns per perspective, forward 279.2 ns (L1 1024 v2); 9.4 % of perspective-moves refresh (2,259 of 24,000) | CONFIRMED | docs/OPUS_R10_HALFKA.md:97-107 at 7f79c349 (table; "21,741 of 24,000 perspective-moves kept the orientation" -> 2,259 = 9.4 %); "next speedups" item 3 = refresh cache, item 4 = prefetch, item 5 = width (:150-165) |
| T05E-01 | about 0.55 evaluations per node (lock path, 30-h counters) | CONFIRMED as cited | notes/T05/SPEED_LIST.md item 5: "x 0.55 evaluations per node in the 30-h counters" (the counter log itself not re-opened; the card says the ON path was never counted) |
| T05E-01 | 826-980 ns per ON node from the bench | CONFIRMED | D:/forge_coder_checks/npt_w4s10/run_20261101_121847/on_final_ftp1_full.txt: nps 1,020,417-1,213,996 -> 824-980 ns |
| T05E-01 | the 30-Oct report dropped the refresh cache only because FB1 (nnue_v3) has one | CONFIRMED | research report at 6f27150d line 508: "Finny tables / accumulator refresh cache: in fable-nnue-arch (nnue_v3), so excluded by the ..." |
| T05E-01 | table 2 x 64 x 3 = 384 entries x (2 KB + 96 B) = about 0.8 MB (0.2 MB at L1 256) | CONFIRMED | arithmetic: 384 x 2,144 B = 823,296 B; 384 x 608 B = 233 KB; geometry is Forge's own K32H3 (hpp:19-21 NumKingBuckets 32 x NumStates 3, mirrored half board) |
| T05E-01 | 70-90 ns per evaluation saved = 0.094 x (626.5 - 150..250) x 2 | CONFIRMED | arithmetic 70.8-89.6 ns; x 0.55 evaluations per node over 826-980 ns per node = +3.9 to +6.0 % at the tool's refresh share |
| T05E-01 | Forge estimate +3 to +8 % nps UNPROVEN | UNVERIFIABLE (by design) | label present; lower part reproduces from the arithmetic above, the upper part rests on the unmeasured in-search refresh share, as the card says |
| T05E-01 | e19 ON bench nodes 373062 / 831975 / 4115992 / 17885060 / 37006232 | CONFIRMED | origin/opus-r11-nnue-pipeline opus_r11/logs/full_ourdata/PACKAGE_E20_bench.txt lines 5-9 (net e19_final bf1e347c) |
| T05E-02 | Stockfish e9997afb1c = PR 5870, 2025-02-24, replaced hint_common_parent_position | CONFIRMED | gh api commit (author 2025-02-04, committer 2025-02-24); title and "No functional change" |
| T05E-02 | STC [0,2] +2.71 +- 1.70, 39,680 games, LLR 2.93, ptnml 171-4068-11042-4398-161 | CONFIRMED | get_run 67a27f26eb183d11c65945be: 10+0.1, threads 1, UHO, llr 2.934; recompute +2.71 +- 1.70 |
| T05E-02 | LTC [0.5,2.5] +0.88 +- 0.51, 337,308 games, LLR 2.94, ptnml 276-30551-106126-31441-260 | CONFIRMED | get_run 67a287efeb183d11c65945ee: tc 60+0.6, elo0 0.5 elo1 2.5, llr 2.944; recompute +0.88 +- 0.51 |
| T05E-02 | simplified form passed non-regression [-1.75,0.25] STC and LTC; no nps figure | CONFIRMED | commit message: STC 28,608 games (67a47037), LTC 200,226 games (67a4f255); no nps line |
| T05E-02 | hint 0838552 "Introduce a function to compute NNUE accumulator" (2023-02-23) and 728b963 "... also at PVNodes TT hits"; STC ~+1.4 and ~+2.3, LTC ~+1.4 (tool summaries) | CONFIRMED | gh api: titles and dates; recompute 0838552 STC [0.5,2.5] 110,368 games +1.39 +- 0.91, earlier STC [0,2] 47,552 games +2.33 +- 1.53, LTC block +1.39 (the commit message's LTC block repeats the STC [0.5,2.5] totals as written); 728b963 STC 124,472 games +1.18 +- 0.94 |
| T05E-02 | PR author: filling interior rows pays only when evaluations are frequent | CONFIRMED | PR 5870 comment by the author: with only ~20 % smallnet evaluations the "zero effective cost" heuristic no longer holds |
| T05E-02 | own code: TT eval reused without evaluate() at src/search.cpp:864 and :992; in check :858-860 / :987-988; excluded :989-990; record_move :623-636; record_null_move :638-646; halfka_evaluate :661-693 (nearest valid ancestor with the same king square + bucket, else refresh) | CONFIRMED | git show origin/qa-r10v2-fix1:src/search.cpp at those lines |
| T05E-02 | Forge estimate +1 to +4 % alone, +0.5 to +1.5 % on top of T05E-01, UNPROVEN | UNVERIFIABLE (by design) | label present; the card states the driving share (parent row missing) was never measured |
| T05E-03 | Stockfish fb1d777250 = PR 6961, 2026-07-10, "+0.98 % nps (100 runs, Core Ultra 9 285H)" | CONFIRMED | commit message: base 1,504,448 +- 15,119 vs test 1,519,239 +- 15,980, "speedup = +0.0098", "CPU: Intel Core Ultra 9 285H" |
| T05E-03 | STC [0,2] +2.35 +- 1.55, 48,256 games, LLR 2.94, ptnml 144-5310-12913-5598-163, no functional change | CONFIRMED | commit message (test 6a4dc4c65529b8472df7fd56); recompute +2.35 +- 1.55 |
| T05E-03 | 8132dbc "split affine_transform on VNNI as well" (title) | CONFIRMED | gh api: title; its own numbers (+0.31 % speedup, 184,544 games) are not used by the card |
| T05E-03 | own code: block_affine (src/nnue_halfka.cpp:226-245) adds every non-zero block into the same NQ accumulators; NQ = L2 / 16 = 2 for the npt nets; mask from the pairwise output :231-233 | CONFIRMED | lines 226-245 (`acc[q] = dpbusd(acc[q], ...)`, one chain per q); :278 `Group = 16` under AVX-512, :284 `case 32: block_affine<32 / Group>`; mask at :230-233 |
| T05E-03 | npt nets are 1024 x 32 x 32 (file size 70,334,820 B, loader size rule) | CONFIRMED (method) | five npt_*_ftp1.nnue files of 70,334,820 B in forge_push/bin; loader :344-355 derives (l2, l3) uniquely from the hash and the file size; L2 = 32 is the kernel case that gives NQ = 2 |
| T05E-03 | Zen 5 VPDPBUSD latency 3-4, 2 per cycle -> 6-8 chains needed | CONFIRMED | notes/T05/SPEED_LIST.md:40 (uops.info latency 3, TP 0.50; Agner latency 4, TP 0.5); 3..4 x 2 = 6..8 |
| T05E-03 | R13 P2 two-phase find-nnz lost -12..-14 % LTO+PGO | CONFIRMED | origin/opus-r13-p2-sparse-l1 opus_r13/p2/RESULTS.md step 4: d16 -13.54 % [-14.53, -11.85], d20 -11.90 % [-13.28, -10.87]; text: "the extra accumulator chains do not pay it back" |
| T05E-03 | Forge estimate +1 to +3 % nps UNPROVEN | UNVERIFIABLE (by design) | label present |
| T05E-04 | Stockfish fda269a299 = PR 5988, 2025-04-27, +1.67 +- 1.23, 72,800 games, LLR 2.93, ptnml 160-7711-20374-7930-225 | CONFIRMED | gh api (committer 2025-04-27); commit message test 67f70b1c31d7cf8afdc45f51; recompute +1.67 +- 1.23 |
| T05E-04 | later removed by 1a882ef "Simplify out double_inc_update" (non-regression) | CONFIRMED | gh api 1a882efc7f (2026-04-26): [-1.75,0.25] STC 115,424 games + AVX2-only STC 134,720 games; PR 6776 (message also notes a -0.9 % vs +2 % local speed disagreement) |
| T05E-04 | Stockfish 7b5504097f = PR 7006, 2026-08-01, +1.68 +- 1.22, 69,632 games, LLR 2.93, ptnml 153-7022-20132-7354-155 | CONFIRMED | gh api; commit message test 6a63233fc054e285ae028702; recompute +1.68 +- 1.22 |
| T05E-04 | own code: apply() applies one ply in one pass (:458-469); a k-ply walk runs k passes (search.cpp:672-673); perspectives one after the other (:665) | CONFIRMED | lines read: `for (int e = from + 2; e <= entry; ++e) halfka::apply(row, row, ...)`; `for (const Color c : {White, Black})` |
| T05E-04 | Forge estimate +0.5 to +2 % nps UNPROVEN; drop if < 20 % of walks span 2+ plies | UNVERIFIABLE (by design) | label present; the drop rule is the worker's own threshold |
| all | licence rows (8 repos) | CONFIRMED | tools/licence_at.py --row re-run: all 8 rows identical to notes/T05E/licences.md. Also run at the exact cited commits: chessgo 3eedea13d6 GPL-3.0, onechess 928d53d2eb GPL-3.0, Eleanor 134af1abde MIT (the licences.md rows are at later commits of the same repos; same licence) |
| all | reading rule (no source file of a GPL / AGPL / unlicensed repo, Stockfish and nnue-pytorch source never) | CONFIRMED | notes/T05E/sources.md names only commit titles, commit messages, PR text, fishtest pages, the Eleanor PR / test page and own code; tools/mine_commits.py --show prints the commit message only (tool line 10); no raw / blob fetch of any Stockfish, chessgo, onechess, rshogi, YaneuraOu or sleepmind2 file is recorded |
| all | no other engine's tuned constant proposed as a Forge value | CONFIRMED | the 2 x 64 x 3 table is Forge's own K32H3 geometry; the ply cap "1-4" (T05E-02), the "about 8 rows per pass" (T05E-04) and the "< 20 % of walks" drop rule are own values; no Stockfish sizes or thresholds carried over |
| all | Forge-has-it grep | CONFIRMED | `bash tools/forge_has.sh 'halfka|refresh_cache|RefreshCache|finny|AccumulatorCache'` = 0 hits (re-run) |
| all | no duplicate among the 85 cards / TRIED_GATES | CONFIRMED | grep finny / refresh cache / backward / VNNI / interleav / double incremental / perspectives together over cards/*/: only T01B-02 (mentions the v2 path's cache in passing) and T05-03 / T05-04 (large pages / prefetch, cited by T05E as existing cards, not re-proposed). notes/TRIED_GATES.md: no HalfKA speed gate; packa / packb (ReSearchAdjust, FiftyDamp, NonPawnCorr) and E3 (EvalMatScale, EvalOptimism) are search / eval options with no overlap |
| all | 4 cards, crew hours, UNPROVEN labels, names, lint | CONFIRMED | ls = 4 files; "crew" hours in all four; **UNPROVEN** in all four; vendor / model-company name grep over cards/T05E and notes/T05E = 0 hits; `card_lint.py cards/T05E/*.md` = 0 findings, 0 PENDING, exit 0 |
| notes | T02-04 bench: OFF 1.95-2.17 vs ON 1.02-1.21 Mnps, ON / OFF 0.47-0.58, d20 19.8M vs 12.4M nodes | CONFIRMED | raw files off.txt / on_final_ftp1_full.txt (run_20261101_121847): OFF nps 2,172,680 / 2,000,763 / 1,947,791 / 2,164,449 / 2,073,969; ON 1,029,327 / 1,020,417 / 1,107,601 / 1,213,996 / 1,212,879; ratios 0.474 / 0.510 / 0.569 / 0.561 / 0.585; d20 nodes 19,846,422 vs 12,389,307 |
| notes | HALFKA_COST per-node model (460-513 vs 826-980 ns, 0.55 x (622 - 350) = 150 ns, ON / OFF 0.76 predicted, 55-70 % of the gap outside the stage table) | CONFIRMED (arithmetic) | 1/nps gives 461-513 and 824-980 ns; 0.55 x 272 = 150; 460/610 .. 513/663 = 0.75-0.77; 150 of 366-467 ns explains 32-41 %, so 59-68 % is not in the table |
| notes | QA J3 ABBA abba_r1.csv ran at the lock pin 3,024,920 nodes (lock float net, not HalfKA) | CONFIRMED | forge_push/qa_j3j5_20261031/abba_r1.csv: all 280 data rows have nodes = 3024920 |
| notes | Zen 5 L2 DTLB 4,096 entries (sources.md 14, page not opened by the worker) | CONFIRMED (L2) | the cited hwbusters page quotes AMD's Hot Chips figure "a 4,096-entry L2 DTLB"; the 96-entry L1 DTLB figure was not found in the page text read here |
| notes | Zen 5 L1 DTLB 96 entries | UNVERIFIABLE | not found on the cited page in this pass; the worker labelled it a search summary; no card depends on it |
| notes | Eleanor PR 170 "+6.88 +- 5.27 at 4.0+0.04s n=4796" (TABLE row 15, sources.md 9) | UNVERIFIABLE | PR 170 body and its one commit say only "bench: 1315668"; no comment carries the number; no card uses it |
| notes | PlentyChess PR 183 STC +10.04 +- 5.65 (6,300 games) as logged by T01B (TABLE row 1) | UNVERIFIABLE here | cross-reference to notes/T01B/TABLE.md row 8, not re-opened in this pass; no card uses it |

## Counts
Claims checked: 47. CONFIRMED: 40. UNVERIFIABLE: 7 (the four Forge estimates, UNPROVEN by design, plus the three
notes-only items above). CORRECTED: 0. VIOLATION: 0. DUPLICATE: 0. Cards changed: none. Lint: clean (exit 0).

## Observations (no action required)
- The three card dates that differ from the GitHub author dates (2024-04-24, 2025-02-24, 2025-04-27) are the committer
  dates; the licence rows use the same convention. Not a correction.
- notes/T05E/licences.md records chessgo, onechess and Eleanor at later commits than the ones cited; the licence at
  the exact cited commits is the same (re-run above). Worth doing at the cited commit next time, not a violation.
- The chessgo commit 3eedea13d6 carries a model-company name in a message trailer; the card cites the title only and
  nothing of it was copied. Keep citing the title only.
- T05E-01's +3 to +8 % reproduces to +3.9 to +6.0 % at the tool's 9.4 % refresh share; the top of the range depends
  on the in-search refresh share, which the card itself names as unmeasured (the counter build in HALFKA_COST.md).

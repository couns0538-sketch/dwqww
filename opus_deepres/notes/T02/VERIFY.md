# T02 VERIFY - adversarial check of cards/T02 and notes/T02 (started 23:20 PC clock, stop 23:45)

One line per check: card | claim | CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION | evidence.

## T02-01 (coordinator's own-data card: numbers vs cited files only, read-only, card not edited)
- T02-01 | TSV md5 ec05042753b0f4466e36dfc0a148c064 | CONFIRMED | md5sum D:/a14/sep/BOARDSTM_TRIAGE_ROWS.tsv
- T02-01 | 7,700 train rows / 7,612 holdout rows in the TSV | CONFIRMED | recount of column side: train 7,700, holdout 7,612 (15,312 data rows)
- T02-01 | 4,118 train rows whose normalised_4field equals a holdout row's, all 37 train files, 3-226 per file | CONFIRMED | recount: 4,118, 37 files, min 3, max 226
- T02-01 | 0.0025 % of 304,999,573; 304,991,873 after the drop; 7,612 = 0.046 % of the holdout | CONFIRMED | 7,700/304,999,573 = 0.00252 %; 304,999,573 - 7,700 = 304,991,873; 7,612/16,388,575 = 0.0464 %
- T02-01 | block rule: 16,588,575 rows, 189,182 blocks, 87.7 rows/block, result_mismatch 121,492 / nonpositive_ply_gap 67,689, R14 121,467 / 67,730, 17.6 s | CONFIRMED | notes/T02/block_rule_012_015.json
- T02-01 | "16 pairs apart in 189k" | CONFIRMED as a net figure only | breaks 189,181 here vs 189,197 in R14 = 16 net; per class the counts differ by 25 (result_mismatch) and 41 (ply gap), so at least 41 pairs are classified differently (report only, card not edited)
- T02-01 | seams 012:2,625,970 -> 013:1 result_mismatch; 014:6,388,575 -> 015:1 nonpositive_ply_gap (013 -> 014 same_block) | CONFIRMED | block_rule_012_015.json seams
- T02-01 | convert 39 shards 6 min 19 s incl. verify, 17:18:18-17:24:37; exe sha256 C3672C3D... | CONFIRMED | F:/forge_j1_data/convert.log lines 1, 5, 43-44 (run3 header at 17:18:17, so the span is 6:19-6:20)
- T02-01 | other effort figures (probe re-scan 388 s, F: 59.6 GB at 22:23) | UNVERIFIABLE here | not in the three files this check was limited to

## Top 3 full cards by expected gain: T02-02 (+0..+5), T02-03 (+0..+3), T02-04 (diagnostic)
- T02-02 | PR 4314 text: depth-6 multipv-2 capture pre-filter, ~93 % Leela/SF + 99 % SF DFRC, unfiltered parts left out, ply <= 28 skipped, no new data | CONFIRMED | gh api repos/official-stockfish/Stockfish/pulls/4314 (body)
- T02-02 | local fixed 25k nodes +5.1 +- 1.5 | CONFIRMED | PR 4314 body ("Local Elo: run_0/nn-epoch779.nnue : 5.1 +/- 1.5")
- T02-02 | STC 10+0.1, UHO_XXL_+0.90_+1.19, 1 thread, SPRT [0,2] passed, 36,504 games, W 9847 L 9538 D 17119, +2.9 | CONFIRMED | https://tests.stockfishchess.org/api/get_run/63adb3acae97a464904fd4e8 (LLR 2.94, accepted); W/L/D give +2.94
- T02-02 | LTC 60+0.6, same book, [0.5,2.5] passed, 36,592 games, W 10017 L 9717 D 16858 = "+2.9 (computed)" | CORRECTED -> +2.85 | https://tests.stockfishchess.org/api/get_run/63ae0ae25bd1e5f27f13d884 ; W/L/D give +2.849 (rounds to +2.8, not +2.9); card, TABLE.md row 1 annotated
- T02-02 | commit be9bc420af = nn-60fa44e376d9 | CONFIRMED | gh api repos/official-stockfish/Stockfish/commits/be9bc420af ("Update default net to nn-60fa44e376d9.nnue")
- T02-02 | "fixed arch HalfKAv2_hm" | UNVERIFIABLE on the cited page | PR 4314 says "retraining the master net" (same arch implied) but names no feature set
- T02-02 | nnue-pytorch PR 222 turned the fixed ply cut of PR 4314 into a parameter | CONFIRMED | gh api .../nnue-pytorch/pulls/222 ("convert the static value used in .../4314 into a parameter", merged 2023-01-06)
- T02-02/T02-03 | w4 s41 run: J1 train binpack only (+ J1 holdout as validation), --start-lambda 1.0 --end-lambda 1.0 --no-filtered --no-wld-filtered, no ply flag | CONFIRMED | D:/forge_nnue_train/runs/npt_k32h3_l1024_bs16k_e8x152m5_g072_lam10_w4_s41.log line 6 (2026-11-03T18:48:07)
- T02-03 | PR 3808 nn-3678835b1d3d, HalfKAv2_hm^, lambda 1.0, Leela T60+T74 + SF wrongIsRight data (new data) | CONFIRMED | gh api .../Stockfish/pulls/3808 (body)
- T02-03 | PR 3808 STC 10+0.1 UHO_XXL -0.44 +- 1.8, 40,000 games | CONFIRMED | PR 3808 body + api/get_run/619eb597c0a4ea18ba95a4dc (W 10447 L 10498 D 19055, fixed 40,000 games, no SPRT)
- T02-03 | PR 3808 LTC 60+0.6 +3.30 +- 1.8, 33,062 games | CONFIRMED | PR 3808 body (test 619f6e87c0a4ea18ba95a53f, not linked in the card)
- T02-03 | PR 3808 LTC SPRT [0.5,3] passed, 29,376 games, +3.2 computed | CONFIRMED | api/get_run/61a0864e8967bbf894416e65 (W 7663 L 7396 D 14317, 60+0.6, LLR 2.94); W/L/D give +3.16
- T02-03 | PR 3816 STC SPRT [0,2.5] 49,152 games +2.1; LTC [0.5,3] 25,528 games +3.4; TB7-rescored Leela data | CONFIRMED | gh api .../Stockfish/pulls/3816 (W/L/D give +2.11 / +3.42)
- T02-03 | nnue-pytorch PR 155 merged 2021-12-03, skip is default, --no-wld-fen-skipping disables it | CONFIRMED | gh api .../nnue-pytorch/pulls/155 (merged_at 2021-12-03T00:56:53Z)
- T02-04 | WAC300 at movetime 200: OFF 272 / 273, ON 267 | CONFIRMED | D:/forge_coder_checks/npt_w4s10/run_20261101_121847/wac_{OFF1,ON_final_ftp1,OFF2}.json + REPORT.md lines 39-41
- T02-04 | median depth OFF 17, ON 15 | CONFIRMED | same json files (field depth)
- T02-04 | 13 lost (both OFF solve, ON fails), 8 won, sign test p ~ 0.38 | CONFIRMED | recount 13 / 8 over 21 discordant, two-sided binomial p = 0.383
- T02-04 | d20: 19.8M vs 12.4M nodes, 16.3 s vs 5.7 s | CONFIRMED | on_final_ftp1_full.txt (19,846,422 / 16,348 ms) vs off.txt (12,389,307 / 5,724 ms)
- T02-04 | bench OFF 2.07-2.16 Mnps vs ON 1.11-1.21 Mnps | CORRECTED -> OFF 1.95-2.17, ON 1.02-1.21 (d11-d22) | off.txt (2.17 / 2.00 / 1.95 / 2.16 / 2.07) and on_final_ftp1_full.txt (1.03 / 1.02 / 1.11 / 1.21 / 1.21); the card's ranges left out d11-d16 of OFF and d11-d13 of ON; ON/OFF per depth 0.47-0.58
- T02-04 | npt nets vs AL1 -86 to -116 Elo, 248-288 games, H0 accepted | CONFIRMED | tools/tried_gates.py --grep 'npt|halfka|w4': 6 gates, -86.17 .. -116.23, 248-288 games
- T02-04 | lock file:line eval_params.hpp:39-44 (ThreatByMinor .. HangingPiece), :72 KingSafetyWeights; search.hpp:205-210 Razor*/Futility*, :221 QsFutilityMargin, :242 CaptureFutilityBase | CONFIRMED | sed -n on the lock source src_al1s198_clean (all eight lines as cited)
- T02-04 | "44 hits" (razor / futility) | CONFIRMED | bash tools/forge_has.sh 'razor|futility' = 44 hits
- T02-04 | "36 hits" (threat / hanging / king safety) | UNVERIFIABLE | the card does not state the regex; 'Threat|Hanging|KingSafety' = 28, 'threat|hanging|king.?safety' = 37
- T02-04 / T02-02 | writer drops: capture / promotion best move 17.5 %, in check 9.3 %, mate 0.9 % of searches | CONFIRMED | skill forge-selfplay-datagen SKILL.md line 39 (60-game waste count)
- T02-02 | J1 binpack stores a constant ply 40 and a null king move | CONFIRMED | skill forge-nnue-data SKILL.md line 81
- MIX.md | relabel rates 5k nodes ~1.19M rows/h, 10k ~0.74M rows/h per worker | CONFIRMED | skill forge-relabel-job SKILL.md line 93 (737k / 1.19M)

## One-line cards (spot-check 2 numbers each)
- T02-05 | c620886181: ~+3.38 STC over 30,544 games, ~+3.14 LTC over 32,464; capture pre-filter on about half the set + ~9.5B new rows; 6- and 7-piece TB rescoring of the new Leela part | CONFIRMED | gh api .../Stockfish/commits/c620886181 (W 8244 L 7947 D 14353 -> +3.38; W 8866 L 8573 D 15025 -> +3.14)
- T02-05 | holdout sample: <= 5 pieces 5.95 %, <= 6 10.48 %, <= 7 15.64 %, median 17 | CONFIRMED | own recount of F:/opus_scratch/sol_S31/inputs/prod/holdout_013_014_s16.pos (FPOS v1 columnar: 1,024,286 boards of 32 bytes, nibble 0 = empty): 5.954 / 10.484 / 15.641 %, median 17; the worker's script is not on record, the recount used the layout in skill forge-nnue-data line 11
- T02-06 | Caissa d8e94e1b37 eval-75: +32M endgame-book positions in 20.4B; LTC 60+0.6 UHO_Lichess_4852_v1 +2.79 +- 1.98, SPRT [0,3], 28,418 games; STC 10+0.1 +2.62 +- 1.68, [0,2], 43,944; endgame book STC 5+0.1 +47.77 +- 1.77, 37,638 | CONFIRMED | gh api repos/Witek902/Caissa/commits/d8e94e1b37 (message; tests furybench 6282 / 6277 / 6285 as linked)

## TABLE.md rows (extra spot checks)
- TABLE row 5 | 3d2381d76d ~+1.35 STC (103,344) / ~+4.35 LTC (21,712); one-good-move filter + 7-piece rescoring + ply <= 28 | CONFIRMED | commit message, W/L/D give +1.35 / +4.35
- TABLE row 6 | 1b7dea3f85 ~+1.47 STC (95,232) / ~+0.98 LTC (320,544); SEE >= 0 skip, v6-dd data, loss change | CONFIRMED | commit message (experiment name "see-ge0 ... more-loss"; "without bestmove captures removed"), W/L/D give +1.47 / +0.98
- TABLE row 7 | f12035c88c "LTC ~+1.05 (265,326) and ~+0.84 (296,128)" | CORRECTED | commit message: the 296,128-game test is "Passed STC vs. PR 4919" with bounds [0,2]; the LTC vs PR 4919 is 75,618 games (W 19085 L 18680 -> ~+1.86); row annotated
- TABLE row 1 | LTC +2.9 | CORRECTED -> +2.85 | as T02-02 above

## Licences (tools/licence_at.py --row re-run, check 3)
- licences.md | official-stockfish/nnue-pytorch c625702757 LICENSE "AGPL-3.0" | CORRECTED -> GPL-3.0 | re-run: GPL-3.0, first line GNU GENERAL PUBLIC LICENSE, api GPL-3.0
- licences.md | official-stockfish/Stockfish ff7cee4244 Copying.txt "AGPL-3.0" | CORRECTED -> GPL-3.0 | re-run: GPL-3.0, api GPL-3.0
- licences.md | Witek902/Caissa 8d2454c72f LICENSE MIT | CONFIRMED | re-run: MIT, api MIT (row moved back inside the table; the note line had split it off)

## Reading rule and constants (check 2)
- all cards + TABLE + MIX | no link to a /blob/, /tree/ or raw source file of a GPL / AGPL / unlicensed repo | CONFIRMED | URL scan: the only source-file link is Caissa @8d2454c72f src/utils/SelfPlay.cpp (MIT, reading allowed) in T02-05; Stockfish / nnue-pytorch cited only by PR text, commit messages and fishtest pages
- T02-03 | WDL-skip mechanism and the reading of --no-wld-filtered | CONFIRMED (no violation) | wording traceable to PR 155 / PR 3808 text and the own run log; no trainer source cited
- T02-02 / T02-03 / T02-06 | own start values (ply cut P = 20 range 12-32 vs the source's 28; skip k 0.5 range 0-1; subset 2 % range 1-5 % vs Caissa's ~0.16 %) | CONFIRMED (own) | card text vs source values
- MIX.md G1 | "the driver doubling N for the first 10 plies" | VIOLATION (constants rule) | identical to Caissa's generator default (MIX.md line 33: soft node budget doubled for the first 10 half-moves) proposed as a Forge value without an own start value or range; marked inline in MIX.md. Not counted: "Syzygy adjudication at <= 5 pieces" (set by which tables exist, not a tuned constant)

## Check 4 (forge_has.sh re-runs)
- T02-02 | 'datagen|gensfen|selfplay|self_play' = 0 hits | CONFIRMED | bash tools/forge_has.sh
- T02-03 | 'wdl|win_rate|winrate' = 0 hits | CONFIRMED | bash tools/forge_has.sh
- T02-05 | syzygy / tbprobe / tablebase = 0 hits | CONFIRMED | bash tools/forge_has.sh 'syzygy|tbprobe|tablebase'
- MIX.md | 'soft.?node|SoftNodes|maxNodesSoft' = 0 hits | CONFIRMED | bash tools/forge_has.sh

## Check 5 (labels, names, lint)
- all 6 cards | every Forge-side estimate labelled UNPROVEN | CONFIRMED | T02-01 0 UNPROVEN, T02-02 +0..+5, T02-03 +0..+3, T02-04 0, T02-05 +0..+2, T02-06 +0..+3; TABLE.md and MIX.md state UNPROVEN for every Forge number
- cards/T02/*.md | card_lint | CONFIRMED clean | 6 files, 0 findings, 0 PENDING (re-run after the verify edits); line counts 60 / 60 / 57 / 60 / 1 / 1
- notes/T02/*.md | vendor / model-company names, licence headers | CONFIRMED none | card_lint name / header scan over the notes files: 0 hits

## Extra checks (notes and remaining card claims)
- MIX.md / sources.md | Caissa generator defaults @8d2454c72f: 21k nodes, x2 for the first 10 half-moves, hard limit 5x soft, max depth 40, 8-10 random moves, opening |eval| cap 500, eval randomisation, win adjudication off (maxEval inf), Syzygy limit 5, 1M games per file | CONFIRMED | https://github.com/Witek902/Caissa/blob/8d2454c72f/src/utils/SelfPlay.cpp (MIT; config block lines 12-35 and lines 311-316); this also confirms the basis of the MIX.md G1 VIOLATION above
- TABLE row 8 / T02-03 | Caissa 71f434458f: three loader filters (decisive-score skip, piece-count target, half-move clock skip above 20) together "lost about 11 Elo", conditions not in the commit | CONFIRMED | gh api repos/Witek902/Caissa/commits/71f434458f (eval-ml-10; points to an experiments-log)
- TABLE row 12 / MIX.md | 14b673d90f: 72 % own / 28 % Leela positions; +1.55 STC [-0.5,2.5] 50,888 games, +2.18 LTC [0.5,3.5] 25,480 | CONFIRMED | commit message (W 5881 L 5654 / W 1498 L 1338)
- TABLE Leela line | Leela data under ODbL 1.0, raw data at storage.lczero.org/files/training_data (Stockfish README @ff7cee4244 lines 125-126) | CONFIRMED | README at ff7cee4244 (Acknowledgements; odbl-10 link) - README only, allowed
- T02-02 / T02-03 | w4 s41 is the current best w4 run | CONFIRMED | npt keeper best_history.txt 2026-11-03T21:08:54 (s24 -> s41)
- T02-02 | 321,388,148 text lines in the 39 self-play files | UNVERIFIABLE | not in any cited record; a full line count of the 39 files was not run in the time box
- T02-02 | the ply-recovery pass time (own guess 10-30 min) | UNVERIFIABLE (labelled as a guess) | not measured, as the card says
- T02-03 (premise of the estimate) | `--no-wld-filtered` is the WDL-likelihood skip switch, so the skip was OFF in every w4 run | UNVERIFIABLE | own docs show only its use (skill forge-nnue-pytorch-amd SKILL.md line 126), not its meaning; PR 155 names the switch `--no-wld-fen-skipping`; the card says itself the match is by name only (trainer source not read, correctly)
- T02-06 | the R8 driver already reads an openings file | CONFIRMED | skill forge-selfplay-datagen SKILL.md lines 35-36 (`--openings o.txt --no-dedup`)
- T02-06 / T02-02 | every live game starts from startpos + 8 random plies; plies 9-28 are all in the data | CONFIRMED for the start (skill line 18: 8 uniformly random plies) / UNVERIFIABLE for "all in the data" | skill line 15: the live 6.2.0 exe has OwnBook default true, never switched off by the script; whether book moves after the random plies give recorded rows is not stated
- T02-04 (title) | every w4 net 263-269 ON vs net-off 271-272 OFF | UNVERIFIABLE | cited only as "the owner's summary", no file; the one run re-read (s10) gives ON 267, OFF 272 / 273 - its OFF2 = 273 is outside the title's 271-272 (the card body discloses it)
- notes/T02/*.md | vendor / model-company names, licence headers, re-run after all verify edits (23:31) | CONFIRMED none | card_lint name / header scan over every notes file: 0 hits

## Totals (stopped 23:32 PC clock)
68 checks: 54 CONFIRMED, 6 CORRECTED (T02-02 LTC +2.9 -> +2.85, a rounding-boundary case; T02-04 bench Mnps ranges;
TABLE rows 1 and 7; the two licences.md licence columns), 7 UNVERIFIABLE (+ the "plies 9-28 all in the data" half of
one CONFIRMED line), 1 VIOLATION (MIX.md G1 carries Caissa's x2 / first-10-plies node rule over as a Forge value;
marked inline; no card has a reading-rule violation, so no Status line was changed). card_lint on cards/T02: clean.
T02-01 was only read, never edited.

# T04B verify (adversarial pass, start 00:32 PC clock, cap 00:52)

Method: every number re-fetched from the PR text (`gh api repos/Ciekce/Stormphrax/pulls/N`, result blocks only; no
source file, no diff) and from the Obsidian commit messages (`gh api .../commits/SHA`), Elo and the 95 % error
recomputed from the quoted W/L/D and pentanomial (F:/odr/work/T04B-verify/elo.py); licence rows re-run with
`tools/licence_at.py --row`; lock lines re-read with `tools/forge_has.sh` and `sed`; tried gates with
`tools/tried_gates.py --grep`; own prior code grepped in `forge_push/src_pack*` and `D:/o15/cands/INDEX.md`;
duplicates against `ls cards/*/`. Scratch: F:/odr/work/T04B-verify/ (pr_N.json, sp_notes_prs.txt, ob_notes.txt).

| card | claim | verdict | evidence |
|---|---|---|---|
| T04B-01 | PR 269 "use capthist in noisy see pruning margin", merged 2025-11-20, a5807f3a9e42 | CONFIRMED | gh api: title, merged_at 2025-11-20T19:54:31Z, merge sha a5807f3a9e42 |
| T04B-01 | STC 8+0.08 Hash 16 MB n=28,964 W 6991 L 6734 D 15239 +3.08 +- 2.21 LLR 2.95 [0,3] Threads=1 | CONFIRMED | PR text; recomputed +3.08, error 2.20 (penta) vs 2.21 quoted (rounding) |
| T04B-01 | LTC 40+0.4 Hash 128 MB n=10,130 W 2245 L 2056 D 5829 +6.48 +- 3.34 LLR 2.93 | CONFIRMED | PR text; recomputed +6.48 / 3.34 |
| T04B-01 | test links chess.swehosting.se/test/12560 and /12563 | CONFIRMED | links present in the PR text (pages not fetched, as the worker said) |
| T04B-01 | "Stormphrax added [a defended dimension] later, PR 209" | CORRECTED | PR 209 merged 2024-12-04, BEFORE PR 269 (2025-11-20): the source's capthist already had it when PR 269 was tested; card text corrected, conclusion (signal may be weaker in Forge) unchanged |
| T04B-01 | lock :1081-1083 threshold -SeeNoisyMultiplier * depth, 150, no history term; :1058 history = capture_history_value; shortcut at :1082; `else` branch also holds quiet checks | CONFIRMED | forge_has 'see_threshold' 3 hits :1081-1083; SeeNoisyMultiplier = 150 (:35); :1058; :1064 `if (quiet && !gives_check) ... else` |
| T04B-01 | table [piece][to][victim] int16 +-16384, search.hpp:255 | CONFIRMED | CaptureHistory = array<array<array<int16_t,7>,64>,13> (:255); HistoryMax = 16384 (search.cpp:107, apply_history :157-160) |
| T04B-01 | CaptSeeDiv gates 47 / 48 = +3.24 / -3.94 at 1,500 g | CONFIRMED | tried_gates rows 47, 48 |
| T04B-01 | T04E-04 is the qsearch SEE site at :838 | CONFIRMED | `if (!board.see_ge(move, -tune::QsSeeMargin)) continue;` at :838 |
| T04B-01 | no other engine's constant proposed | CONFIRMED | the PR body is two OpenBench blocks and two links, no formula; divisor 96 / cap 150 are own values |
| T04B-02 | PR 201 "capthist pruning", merged 2024-11-09, 29e175a2f594 | CONFIRMED | gh api |
| T04B-02 | STC 8+0.08 Hash 32 MB n=13,814 W 3470 L 3256 D 7088 +5.38 +- 3.11 LLR 2.93 | CONFIRMED | PR text; recomputed +5.38 / 3.11 |
| T04B-02 | LTC 40+0.4 Hash 128 MB n=14,602 W 3375 L 3178 D 8049 +4.69 +- 2.76 LLR 2.93 | CONFIRMED | PR text; recomputed +4.69 / 2.76 |
| T04B-02 | lock :1070 history pruning quiet-only inside `if (quiet && !gives_check)` :1064; CaptureFutilityBase = 0 (:1075-1080); guard :1061 | CONFIRMED | lines read; CaptureFutilityBase = 0 at :61 |
| T04B-02 | capture history updated only at beta cutoffs, :752-765 | CONFIRMED | update_capture_stats called only inside `if (best_score >= beta)` (:1196-1200) |
| T04B-02 | tried gates PawnHist / ThreatHist / HistMalusPct / CaptSeeDiv do not prune captures by history | CONFIRMED | tried_gates rows 29/37/44, 64, 67, 47/48 |
| T04B-02 | (verify note) PR 201 (2024-11-09) predates PR 209 (2024-12-04): the source's capthist had no defended dimension when this was tested | CONFIRMED | merge dates; favours the transfer to Forge's plain [piece][to][victim] table |
| T04B-03 | PR 258 "unconditionally extend LMR searches in PV nodes", 23400f016460: STC +2.98 +- 2.17 n=30,702 LLR 2.92 / LTC +1.40 +- 1.14 n=87,056 LLR 2.89 | CONFIRMED | gh api; recomputed +2.98 / 2.17 and +1.40 / 1.14 |
| T04B-03 | PR 268 "extend lmr searches in ttpv nodes where reduction is very negative", e1597abd92ce: STC +3.22 +- 2.27 n=27,094 LLR 2.95 / LTC +2.00 +- 1.56 n=46,438 LLR 2.93 | CONFIRMED | gh api; recomputed +3.22 / 2.26 (2.27 quoted, rounding) and +2.00 / 1.56 |
| T04B-03 | lock :1147 clamp(new_depth - r, 1, new_depth); r can go below 0 (:1139 tt_pv -1, :1143 / :1144 check -1, :1146 history -2..+2); :1149 re-search gate | CONFIRMED | lines read; PV re-search at new_depth :1162-1163 |
| T04B-03 | differs from T04-02 / packb ReSearchAdjust | CONFIRMED | packb src_packb_h256 search.cpp:1165 keeps the reduced search clamped at new_depth and adjusts only research_depth (:1169-1180): the re-search, not the reduced search |
| T04B-04 | PR 223 "reduce more if tt score indicates a fail low in a ttpv node", a0e71921d364 | CONFIRMED | gh api, merged 2025-04-13 |
| T04B-04 | STC "Hash 32 MB" | CORRECTED | the PR text says `8.0+0.08s Threads=1 Hash=16MB`; card corrected to 16 MB (the hand-back carried the same slip) |
| T04B-04 | STC n=12,062 +5.96 +- 3.31 LLR 2.90 / LTC Hash 128 MB n=74,084 +1.52 +- 1.24 LLR 2.91 | CONFIRMED | PR text; recomputed +5.96 / 3.31 and +1.52 / 1.24 |
| T04B-04 | lock :1139 `if (ss->tt_pv) r -= 1;` unconditional; tt_score / tt_bound in scope :914-917 | CONFIRMED | lines read |
| all | licence GPL-3.0 at d1468d99e3, a5807f3a9e, 29e175a2f5, 23400f0164, e1597abd92, a0e71921d3 (Stormphrax) and 720614a61e, d5f3e454dc (Obsidian) | CONFIRMED | tools/licence_at.py --row re-run 00:34, GPL-3.0 at every commit |
| all | reading rule: only PR titles / result blocks and commit messages read | CONFIRMED as far as checkable | the worker's saved text F:/odr/work/T04B/*.txt (990 lines) holds no diff, source or file-path lines (grep for `^[+-]`, `diff --git`, `.cpp`, `#include`, `std::` = 0); the five PR bodies hold nothing but OpenBench blocks |
| all | no vendor / model-company names | CONFIRMED | grep over cards/T04B and notes/T04B = 0 hits |
| all | 4 cards (cap 4), top 2 full (54 / 51 lines, 8 fields in order), 2 one-liners (8 fields), crew hours present, UNPROVEN on every estimate, Status lines | CONFIRMED | ls, wc, header grep; card_lint 0 findings / 0 PENDING before and after the edits |
| all | duplicates against the 34 + round-2 cards | NONE | capture-history cards: T04E-04 (qsearch SEE site, named in T04B-01), T04G-02 (table split), T04F-02 (conthist key); LMR cards: T04-02 (re-search depth), T04D-01 (cut-node no-TT ply), T06B-01 (complexity); ttpv cards: T04C-02 (singular margin) - none holds a T04B mechanism |
| all | own prior code (packb ReSearchAdjust / FiftyDamp, packa, E3, packc, packd, packf2, R15 cands) | NO DUPLICATE | grep of forge_push/src_pack*/src/search.cpp for the four mechanisms = only packb's research_depth line (re-search); D:/o15/cands/INDEX.md 0 hits; FiftyDamp = static-eval 50-move damping, packa = NonPawnCorr / PawnHist, E3 = eval post-processing: unrelated |

## Notes (TABLE.md / sources.md) spot checks
| row | verdict | evidence |
|---|---|---|
| SP 209 +3.66 +- 2.46 n=21,748 / +1.57 +- 1.27 n=68,920 | CONFIRMED | gh api (STC Hash 32 MB) |
| SP 203 +3.91 +- 2.57 n=20,596 / +3.36 +- 2.27 n=22,018, Hash 32 MB | CONFIRMED | gh api; title "always try to find one non-mated move in qsearch" |
| SP 305 +4.33 +- 2.79 n=18,844 / +3.04 +- 2.11 n=24,816 | CONFIRMED | gh api |
| SP 334 +4.50 +- 2.85 n=18,052 / +1.72 +- 1.39 n=57,258 | CONFIRMED | gh api |
| SP 345 +3.93 +- 2.58 n=21,906 / +1.21 +- 0.96 n=116,824 | CONFIRMED | gh api (STC LLR 3.00) |
| SP 160 13+0.13 [0,5] +3.10 +- 2.48 n=21,768 | CONFIRMED | gh api (Hash 32 MB, STC only) |
| SP 313 +1.51 +- 1.21 n=111,278 / +2.24 +- 1.71 n=40,582 | CONFIRMED | gh api |
| SP 188 +3.31 +- 2.34 n=25,818 (STC only) | CONFIRMED | gh api |
| SP 272 +2.77 +- 2.06 n=33,668 / +3.82 +- 2.45 n=18,728 | CONFIRMED | gh api |
| OB d5f3e45 10+0.1 +2.96 +- 1.80 n=36,250 [0,2] LLR 2.93; 10fb2d5 +4.17 +- 2.79 n=14,900 LLR 1.81 | CONFIRMED | commit messages (Hash 16 MB) |
| OB f90784d 60+0.6 +2.00 +- 1.45 n=48,194; cbffcd8 8+0.08 +2.97 +- 1.98 n=30,256 [0,2.5] / 30+0.3 +5.07 +- 4.40 n=5,618 LLR 1.07; eda77c4 +4.34 +- 3.31 n=19,054; 8078bb0 +2.95 +- 2.83 n=27,434; d1b6b92 +4.00 +- 3.43 n=18,514 | CONFIRMED | commit messages (cbffcd8 Hash 64 MB, not stated in the table) |
| TRIED rows quoted (gates 12/35/40/41 packb, 14/34/38/39/43 packa, 15/28 packc, 16, 47/48, 51-54 Hindsight -6.25..+4.63, 65 CheckOrderSee +6.25, SF26B14 / UT2 -3.94 / -3.47, STB1 -3.01, R5A-2 / UR5A2) | CONFIRMED | tried_gates.py --grep |
| lock facts in the table (:149-151 lmp_threshold, :331 evasions, :532 +12000, :577 clear(), :831 / :865 qsearch guard, :960 RFP 72 / 40 -> 32 cp at depth 1 improving, :1071, :1089 SingularDepth 7, :1142) | CONFIRMED | lines read |

## Remaining TABLE rows, re-fetched 00:38-00:40 (F:/odr/work/T04B-verify/sp_rest.txt, ob_rest.txt)
| rows | verdict | evidence |
|---|---|---|
| SP 59 +2.72 (+- 2.16 n=46,064), 66 +3.76 +- 3.20, 67, 68 +3.45 +- 3.04 n=23,678, 69 +4.17, 155 13+0.13 +3.15 +- 2.54, 163 +10.63 13+0.13, 164 +6.09 +- 3.40, 167 +2.83 +- 2.08 n=31,628, 171 +2.21 +- 1.73 n=44,580, 175 +5.11, 182 +1.89 +- 1.53 n=59,294, 186 +2.60 +- 1.97 n=36,350, 189 +7.63 +- 3.84 n=9,566, 190 +8.36 +- 4.05 n=8,690, 192 +10.99 +- 4.72 n=6,322, 195 +1.60 +- 1.30 n=82,236, 204 -0.31, 212 +1.39 / +2.10, 213, 221 +1.61 / +1.65, 226 +1.10 / +1.31, 230 +2.15 +- 1.69 n=45,754 / +2.51 +- 1.86 n=32,908, 253 +4.33 +- 2.78 n=19,092 / +11.92 +- 4.63 n=5,190, 284 +1.60 / +0.74, 290 +2.48 / +1.23, 298 +3.14 +- 2.20 / +3.11 +- 2.16, 300 +1.73 +- 1.39 / +3.44 +- 2.28, 304 +2.17 +- 1.72 / +2.69 +- 1.93, 306 +2.96 +- 2.09 / +1.27 +- 1.00, 307 +1.95 / +1.37, 310 +1.31 / +3.14, 312, 320 +6.63 +- 3.65 n=11,846 / +2.82 +- 2.01 n=27,520, 323 +2.00 +- 1.62 n=63,958 / +4.14 +- 2.59 n=17,368, 331, 335 | CONFIRMED | gh api result blocks; every Elo, error and n in TABLE.md matches |
| SP 282 "SMP only" | CONFIRMED | Threads=4 +8.58 +- 4.00 and Threads=8 +10.64 +- 4.42 at 4+0.04; the PR's third block is a Threads=1 8+0.08 NON-REGRESSION run [-3, 1] (+3.73 +- 3.39, n=10,614), so no single-thread gain is claimed by the source either |
| SP 338 / 339 | NOT CHECKED | titles only in the table ("not read"), nothing to verify |
| OB f899e2b "+1.99" (evidence for T04-02 in sections C and D) | CAVEAT | the run is a simplification SPRT with bounds [-2, 0] (LLR 2.90, n=35,530, 10+0.1): a non-regression pass, not a gain; the table's +1.99 is the measured point estimate of that run. Noted in TABLE.md section D |
| OB e144325 +2.51 +- 1.94 (LLR 2.05, not passed), 997246d 4+0.04 (Threads=2) +3.86 / 8+0.08 +3.28, e0c2b3a +1.56 +- 1.24 n=78,378, 14bfa92 +0.90 +- 2.20 n=45,516 (LLR 0.28), fe0637c 15+0.15 +9.96, a5219f6 +2.82, 302ec63 +2.03 / 25+0.25 +5.61 (LLR 2.56 / 2.63, neither passed), 06d7965 +3.69 +- 2.06, 10a8a0e 40+0.4 +2.80 +- 2.06, d89526f +3.02 (LLR 2.40), ae20bdc +1.90, e9ced10 +2.46, 42392f5 +2.02, 52b7a82 +1.84, 86723b4 +1.62 | CONFIRMED | commit messages; the table never claims a pass for the unfinished runs |
| T04B-02 "the first move of a node is never pruned" | CONFIRMED | best_score starts at -Infinite (:1038), so the :1061 block is skipped until one move has been searched |

## Advisor-prompted extra checks (00:44-00:45)
| card | claim | verdict | evidence |
|---|---|---|---|
| T04B-01 | "book not stated" | CORRECTED | OpenBench pages 12560 / 12563 (test logs, allowed): Opening Book DFRC_4852_v1.epd (double Fischer random) in both runs; win adj. movecount=3 score=492, draw adj. movenumber=40 movecount=8 score=7; card now says so and flags that the source gain is a DFRC-opening result |
| T04B-02 | "book not stated" | CORRECTED | pages 8996 / 8999: UHO_Lichess_4852_v1.epd both runs; win adj. score=400, draw adj. movenumber=40 movecount=8 score=10 |
| T04B-03 | "book not stated" | CORRECTED | pages 11582 / 11585 (PR 258) and 12539 / 12541 (PR 268): DFRC_4852_v1.epd in all four runs; card flags the DFRC caveat |
| T04B-04 | "book not stated" | CORRECTED | pages 10346 / 10350: UHO_Lichess_4852_v1.epd both runs |
| TABLE.md C | "the old pointer to T04C-03 was dropped because that file now holds a different idea" | CONFIRMED | cards/T04C/T04C-03-evaldiff-quiet-history.md is a merge stub: its content went to notes/T04C/TABLE.md B1 (Berserk TT replacement) and B2 (the file-name idea = evidence for packc 28 EvalSwing), consistent with this track's TRIED verdict |
| all | own prior code, structural grep (history term in see_threshold, clamp above new_depth, conditioned ttpv bonus, capture-history prune) over forge_push/, qa_ltopgo_al1_stage/cands/ and D:/o15/cands/ | NO DUPLICATE | 0 files matched |
| TABLE.md header | "books never stated (OpenBench defaults, unknown)" | CORRECTED for the four carded PRs only | see the rows above; the other ~45 table rows' books were not fetched (one page per run, outside the cap) |

Unverifiable after this pass: nothing in the four cards. Still unknown: the books of the non-carded TABLE rows
(their OpenBench pages were not fetched), and the "non-regression bounds" wording of the removals row (SP 67, 213,
331, 335: LLR lines not extracted).

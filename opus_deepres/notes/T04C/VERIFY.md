# T04C verify (adversarial pass, 00:39-00:50 PC clock; scratch F:/odr/work/T04C-verify/)

Method: every cited PR / commit re-opened with gh api (bodies and commit messages), test pages re-fetched with curl
(furybench 2921 / 2923 / 7813 / 7821, chess.grantnet.us 38886, chess.aronpetkovski.com 6088), Elo means recomputed
from W/L/D (own script elo.py; the +- values are OpenBench pentanomial figures and are checked against the PR text,
not recomputed), licence rows re-run with tools/licence_at.py --row, greps re-run with tools/forge_has.sh and
tools/tried_gates.py, every cited lock line read in src_al1s198_clean/src/search.cpp, duplicates checked against
`ls cards/*/` plus notes/T04/TABLE.md, notes/T04B/TABLE.md, notes/T04D/TABLE.md, notes/T04E/TABLE.md and
notes/TRIED_GATES.md, scratch folder F:/odr/work/T04C audited for source or diff files. No source file of any GPL
repo was opened by this pass either.

| card | claim | verdict | evidence |
|---|---|---|---|
| T04C-01 | PlentyChess PR 393 STC +6.73 +- 3.15 n=11,508 (W 2,896 L 2,673 D 5,939) LLR 2.93 [0,2.5]; LTC +3.88 +- 2.27 n=20,040 LLR 2.89; merged 2025-09-17, branch qs-fail-medium | CONFIRMED | gh api pulls/393; mean recomputed 6.73; furybench 2921 "LLR 2.93 after 11508 games", 2923 "LLR 2.89 after 20040 games" |
| T04C-01 | book UHO_4060_v2 for PR 393 (STC and LTC) | CONFIRMED | furybench 2921 and 2923 both list books/master/UHO_4060_v2.epd |
| T04C-01 | PR 329 STC +2.09 +- 1.62 n=45,534 LLR 2.96 [0,3]; LTC +1.10 +- 1.07 n=93,286 LLR 1.82 (not passed, merged 2025-03-03) | CONFIRMED | gh api pulls/329 |
| T04C-01 | PR 464 STC +0.81 +- 0.96 n=120,068; LTC +1.05 +- 0.97 n=104,068; tests furybench 4946 / 4947 | CONFIRMED | gh api pulls/464 |
| T04C-01 | Berserk 396920c (#544) STC 10+0.1 8 MB [0,2] +3.57 +- 2.72 n=29,550 LLR 2.90; LTC 60+0.6 +1.00 +- 1.39 n=105,980 LLR 1.80 | CONFIRMED | gh api commits/396920cfea and pulls/544 (identical blocks) |
| T04C-01 | Alexandria 1ce77c8 (#531) STC +3.39 +- 2.28 n=22,856 LLR 2.95 [0,3]; LTC +0.03 +- 2.21 n=21,922 LLR -0.78 "dead neutral" | CONFIRMED | gh api commits/1ce77c80ed; PR body adds only "I'm sure this scales at some point" |
| T04C-01 | books of PR 329 / 464, Berserk 544, Alexandria 531 not stated | UNVERIFIABLE | not in the PR text; their test pages were not fetched (cap) |
| T04C-01 | Caissa ae2eb0c +1.19 cross-check | CONFIRMED | notes/T04/TABLE.md:44 (+1.19 +- 0.95 n=142,682, dropped under +1) |
| T04C-01 | "393 added the capture return point" | UNVERIFIABLE | labelled own inference in the card; no readable text states the return point; no source may be read |
| T04C-01 | lock: stand pat returns the raw eval `:815-818`; cutoff break `:860`; raw store + return `:868-869`; 0 hits fail.?firm/blend | CONFIRMED | lines read (the stand-pat store at :817 runs only without a TT hit, the card's wording is loose but not wrong); forge_has.sh 0 hits |
| T04C-01 | FailHighBlend gates 36 / 42 -2.08 / +0.46 (1,500 each); RfpReturnBlend=25 gate 86 -16.42 H0 at 868 | CONFIRMED | tools/tried_gates.py --grep; src_p11r_h256/src/search.cpp:1246-1253 is a main-search non-PV blend, not qsearch |
| T04C-01 | licence PlentyChess @fdbdbccab8, Berserk @a3a6f62397, Alexandria @829daf405e GPL-3.0 | CONFIRMED | tools/licence_at.py --row x3 reproduce notes/T04C/licences.md byte for byte |
| T04C-01 | no duplicate | CONFIRMED | no other card carries a qsearch return blend; notes/T04B/TABLE.md:78 and notes/T04D/TABLE.md:70 point at T04C-01 / T04 TABLE B; T04F-01 and T04E-04 are other qsearch ideas |
| T04C-02 | PlentyChess PR 286 STC +5.21 +- 3.51 n=9,938 (W 2,334 L 2,185 D 5,419) LLR 2.13 [0,3]; LTC +5.34 +- 3.21 n=10,536 (W 2,577 L 2,415 D 5,544) LLR 2.50; merged 2024-11-19, merge commit 9b8517d | CONFIRMED | gh api pulls/286; means recomputed 5.21 / 5.34 |
| T04C-02 | book unknown, test pages 6088 / 6089 unreadable | CONFIRMED (unreadable) / UNVERIFIABLE (book) | curl 6088: http 000, 0 bytes |
| T04C-02 | lock `:1091` singular_beta = tt_score - SingularMargin * depth (SingularMargin 2, range 0-10 at `:37`, `:82`); tt_pv `:919`, LMR `:1139`; double ext `:1102`; multicut `:1105-1106`; negative ext `:1107-1111` | CONFIRMED | lines read; forge_has.sh 'singular_beta|SingularMargin' 9 hits, 'tt_pv' 10 hits |
| T04C-02 | SingularV2 has no tt_pv margin; tried_gates --grep Singular = 0 rows | CONFIRMED | F:/opus_scratch/worktrees/qa_r7pfe_c34a9739/include/forge/singular_v2.hpp:1-33 (positive_extension takes singular_beta as given); tried_gates 0 of 110 |
| T04C-02 | no second engine's log in Berserk / Alexandria titles | CONFIRMED for titles only | first 100 closed PRs of each: no title names a tt_pv singular margin; Berserk 476 "Singular Extension Tweaks" is generic and cannot exclude it |
| T04C-02 | no duplicate | CONFIRMED | T04-01 (non-cut singular search) and T04-06 (triple extension) are other singular ideas |
| T04C-05 | PR 494 STC +2.58 +- 1.75 n=37,864 LLR 3.06 [0,2.5] passed | CONFIRMED | gh api pulls/494; furybench 7813 "LLR 3.06 after 37864 games" |
| T04C-05 | PR 494 LTC +2.71 +- 2.55 n=16,510 LLR 1.50 | CORRECTED | the PR body is a snapshot; furybench 7821 final state: +2.21 +- 2.24 n=21,348 LLR 1.48 (-2.25, 2.89) [0,2.5], still unfinished; card and TABLE A3 annotated |
| T04C-05 | PR 494 "book not stated" | CORRECTED | furybench 7813 and 7821 list UHO_Lichess_4852_v1.epd; card annotated |
| T04C-05 | PR 475 STC +1.53 +- 1.21 n=80,162 passed (LLR 2.98); LTC +1.53 +- 2.07 n=25,160 LLR 1.01 | CONFIRMED | gh api pulls/475 (its test pages 5808 / 5813 not fetched: book UNVERIFIABLE) |
| T04C-05 | Stormphrax 334 +4.50 +- 2.85 n=18,052 / +1.72 +- 1.39 n=57,258 | CONFIRMED | gh api Ciekce/Stormphrax pulls/334: both passed (LLR 2.92 / 2.90 [0,3]), LTC at Hash=128MB; merge commit 76c51788836f as in notes/T04B/TABLE.md:25 |
| T04C-05 | Stormphrax licence "per notes/T04B/licences.md" | CORRECTED | that file has rows at d1468d99e3 / e410c4214f / 29e175a2f5, none at PR 334's merge commit; row at 76c5178883 (GPL-3.0, 2026-05-19) now added to notes/T04C/licences.md |
| T04C-05 | lock `:149-151` lmp_threshold, one-way switch `:1062`, pick_best `:488`, quiet stage `:386-392`, quiet_history `:704-712`, continue at `:1070`; grep 6 hits none with history; gate 60 LmpOffKP=1 +0.23 at 1,500 | CONFIRMED | lines read; forge_has.sh 6 hits; tried_gates gate 60 |
| T04C-05 | "each capped at 16384" (history tables) | CONFIRMED | search.cpp:107 HistoryMax = 16384; :157-159 apply_history clamps the bonus and uses a gravity update bounded by HistoryMax |
| T04C-05 | T04B left the idea uncarded for the continue-path reason | CONFIRMED | notes/T04B/TABLE.md:25 |
| T04C-05 | no duplicate | CONFIRMED | T04E-01 (quiet checks kept by LMP) is a different rule on the same switch; T04B row 25 is not a card |
| T04C-03 stub | Berserk fe1363a (#575) STC +3.76 +- 2.12 n=27,964 [0,2]; LTC +5.77 +- 2.88 n=13,132 [0,2.5], both passed | CONFIRMED | gh api commits/fe1363af6b and pulls/575 |
| T04C-03 stub / TABLE B1 | lock refreshes generation on a hit `:263-267`, victim by depth - 4 x age `:273-279`, same-position gate `:292` | CONFIRMED (nit) | lines read; the overwrite gate itself is `:294` (`:292` defines same_position) |
| TABLE B1 | PlentyChess 397 "two STC runs -2.74 and +5.27" | CORRECTED | the +5.27 +- 2.66 n=13,782 run was Threads=32 Hash=384MB (furybench 3068); only the -2.74 run is 1-thread STC; TABLE B1 annotated |
| TABLE B2 | PlentyChess 189 +3.38 +- 3.02 n=22,732 LLR 2.91 [0,3] no LTC; 272 +3.33 +- 2.77 n=15,020 LLR 1.93 | CONFIRMED | gh api pulls/189, /272 |
| TABLE B2 | packc EvalSwing gates 15 / 28 +5.91 / +9.27 bundled with AspFailHighReduce | CONFIRMED | tools/tried_gates.py --grep 'EvalSwing|AspFailHigh' |
| T04C-04 stub / TABLE B3 | Berserk 7451fd7 (#577) STC 10+0.1 8 MB UHO_Lichess_4852_v1 [0,2] +2.26 +- 1.55 n=52,326 (W 12,717 L 12,377 D 27,232) LLR 2.89; LTC +2.04 +- 1.53 n=47,970 passed | CONFIRMED | gh api commits/7451fd7fde; mean recomputed 2.26; grantnet 38886 lists UHO_Lichess_4852_v1.epd |
| T04C-04 stub | duplicate of T04E-03 | DUPLICATE (declared by the worker, merged) | cards/T04E/T04E-03 names T04C-04 as evidence; T04D-03 / T04G-03 are the same kind of stub; Status line added to the stub |
| all | reading rule | CONFIRMED | F:/odr/work/T04C holds only commit / PR lists and scripts/pr_mine.py; no .cpp/.h/.diff/.patch, no diff hunks in any text file; pr_mine.py fetches no diff / files endpoint |
| all | no other engine's constant as a Forge value | CONFIRMED | no source was read, so none could be copied; every start value is marked own (Keep 32 = midpoint, SingularTtPvMargin 32 = doubled own margin, LmpHistDiv 8000 / Shift 3) |
| all | own prior code duplicates (packb ReSearchAdjust / FiftyDamp, packa NonPawnCorr, E3 EvalMatScale / EvalOptimism / EvalRule50Damp, CorrUpdateMode, p11r FailHighBlend) | CONFIRMED no duplicate | src_packb_h256/src/search.cpp:659 (FiftyDamp = eval damp by halfmove clock), :1170 (ReSearchAdjust = LMR re-search rule); none touches qsearch returns, the singular margin or the LMP count |
| all | card count, crew hours, UNPROVEN, names | CONFIRMED | 5 files = 3 cards (2 full + 1 one-liner) + 2 MERGED stubs (same convention as T04D-03 / T04G-03); crew hours in all three; UNPROVEN in all three; no vendor names (the only @ matches are repo@sha) |
| all | lint | CONFIRMED | the three cards exit 0 before and after the edits; the two stubs fail the full-card checks by design |

Violations: none found.

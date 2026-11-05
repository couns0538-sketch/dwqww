# T04 ranked idea table - search features Forge lacks (incl. move ordering and movegen)

Lock = FD3A5190 source `src_al1s198_clean` (search: `src/search.cpp`, `include/forge/search.hpp`); every "Forge has it"
cell is a `tools/forge_has.sh` grep or a read of that file. All source numbers are the engines' own logs (OpenBench /
furybench blocks: Elo +- 95 % error, TC, games n, SPRT bounds); 1 thread unless noted; books are not stated in those
logs (unknown). Forge estimates are **UNPROVEN**. "Rank" = Elo per build-hour order: midpoint of the UNPROVEN Forge
estimate divided by crew build hours (cards give both); "-" = not a candidate (has it / tried / prepared / under +1).

## A. Candidates (ranked)
| rank | idea (card) | source link | licence | logged STC / LTC Elo | Forge has it (file:line) | lines to touch | start value and range (own) |
|---|---|---|---|---|---|---|---|
| 1 | LMR re-search deeper / shallower after a reduced fail-high (T04-02) | [Caissa 434bbda](https://github.com/Witek902/Caissa/commit/434bbda5c342501ac5de4ecb6934e85151a225fe), [Patricia PR 137](https://github.com/Adam-Kulju/Patricia/pull/137) | MIT | Caissa STC 10+0.1 +6.93 +- 3.88 n=14,696 [0,2]; LTC 40+0.4 +5.14 +- 3.35 n=18,914 [0,2]. Patricia 8+0.08 +5.55 +- 3.25 n=14,514 [0,3] | LACKS: fixed re-search depth `search.cpp:1136-1159` (`new_depth` const at :1117) | ~8 | LmrDeeperMargin 70 cp (30-150, 0 = off); LmrShallowerMargin 10 cp (0-40, -1 = off); never deeper at root |
| 2 | Singular verification search as a non-cut node (T04-01) | [Caissa 1b7a871](https://github.com/Witek902/Caissa/commit/1b7a871236e20d85fd193f07bb2a62dceb2f9e35) | MIT | STC 10+0.1 +4.20 +- 2.23 n=25,044 [0,2]; no LTC | LACKS: passes `cut_node` at `search.cpp:1095` (cut-node LMR +2 at :1141) | 1 | SingularNonCut 0/1 |
| 3 | Correction update also when best move is a SEE-losing capture (T04-05) | [Caissa 54aef4a](https://github.com/Witek902/Caissa/commit/54aef4aa8a5c20637425dde6850e235c509bc273) | MIT | STC 10+0.1 +2.63 +- 1.68 n=44,298 [0,2]; no LTC | LACKS: every capture best move skipped at `search.cpp:1219` | 1 | CorrBadCapture 0/1; SEE threshold 0 (range -100..0) |
| 4 | NMP margin discount when the child ply had few cutoffs (T04-03) | [Caissa e53fe6e](https://github.com/Witek902/Caissa/commit/e53fe6ebf2a48af382fd5d3355e36e3ef63aa173) | MIT | STC 10+0.1 +2.00 +- 1.41 n=61,474 [0,2]; LTC 60+0.6 +5.95 +- 3.14 n=10,918 [0,3] | LACKS: child counter cleared at own entry `search.cpp:905`, so 0 at NMP `:965`; needs a 2nd counter | ~10 | NmpFewCutoffs 3 (1-6); NmpFewCutoffsDiscount 24 cp (0-72) |
| 5 | Triple singular extension, decided at LTC (T04-06) | [Patricia PR 147](https://github.com/Adam-Kulju/Patricia/pull/147), [Caissa f2967c1](https://github.com/Witek902/Caissa/commit/f2967c12d1) | MIT | no STC logged; Patricia LTC 60+0.6 +3.12 +- 2.14 n=24,804 [0,3]; Caissa 80+0.8 +3.36 +- 2.07 n=25,260 [0,2.5] | LACKS on the lock (single + double only, `search.cpp:1100-1104`); PREPARED in FB2-J3 SingularV2 (never gated) | ~3 (own) or port | TripleExtExtra 60 cp below the double-extension threshold (20-120); same per-path cap as doubles |
| 6 | Minor-piece + major-piece correction keys (T04-04) | [Altair PR 189](https://github.com/Alex2262/AltairChessEngine/pull/189), [PR 188](https://github.com/Alex2262/AltairChessEngine/pull/188) | MIT | minor 8+0.08 +7.74 +- 5.71 n=7,008 [0,4]; major +6.84 +- 5.23 n=8,280 [0,4]; no LTC | LACKS on the lock (pawn + material keys, `search.cpp:638-656`); minor PREPARED as R3 CorrHistPlus bit 2 (R5A-4 specced, no FORGE_RESULTS row); major nowhere | ~40 | weight 50 % of the pawn table (25-100 %); 16k entries per side like the lock |
| 7 | Squared-depth weight in the correction update (no card: < 3 Elo STC) | [Altair PR 176](https://github.com/Alex2262/AltairChessEngine/pull/176) | MIT | 8+0.08 +2.70 +- 2.16 n=29,710 [0,5]; no LTC | HAS a linear weight `min(depth + 1, 16)` at `search.cpp:650`; an update-rule change was gated as CorrUpdateMode (gates 63 / 68: +3.47 / +0.46, 1,500 games) | 1 | weight min((d+1)^2 / 4, 32) (cap 16-64), divisor kept |

## B. Has it, tried, prepared, or below +1 (do not re-propose without a new angle)
| idea | source (licence) | logged Elo | Forge status (file:line) |
|---|---|---|---|
| continuation correction history | Caissa 6e71545 +3.09 +- 1.87 10+0.1 n=36,322; a735e4e 2nd-level +1.11 +- 0.89; Patricia PR 183 +2.91 +- 2.09 8+0.08 n=31,264 (MIT) | STC only | TRIED: CorrHistPlus bit 1 (in B1 / B3 bundles), ContCorrectionWeight gate 87 (+5.10, 1,500 g), CorrHistV2 (FB2-J3) |
| non-pawn correction history | Altair PR 187 +3.30 +- 3.25 8+0.08 n=20,922 (MIT) | STC | TRIED: packa NonPawnCorr w50-65 (gates 34/38/39/43), CorrHistPlus=4 (R5A-1 +4.17, UR5A1 +1.27) |
| multicut returning a blended score | Caissa 8bf8b9a +1.06, cecdba1 +2.02; Altair PR 177 +3.95 +- 3.04 (MIT) | STC | HAS multicut `search.cpp:1105-1106` (returns singular_beta); blend = queued crew line Sf26MulticutCorr + SingularV2 |
| more negative extension in cut nodes | Caissa 6ec347d +4.03 +- 2.19 10+0.1 n=26,636 (MIT) | STC | HAS -2 / -1 at `search.cpp:1107-1111`; "deeper negative extensions" PREPARED in SingularV2 |
| probcut in check | Patricia PR 160: removing it +0.16 +- 2.38 non-reg [-5,0] (MIT) | STC | Forge never probcuts in check (ProbCut inside the `!in_check` block `search.cpp:952-1027`): nothing to gain |
| "new probcut" | Patricia PR 191 +2.63 +- 2.02 8+0.08 n=41,808 (MIT) | STC | HAS ProbCut `search.cpp:1000-1027`; R15 C3 TtProbcut PREPARED; PR mechanism not read |
| cutoff-count LMR | Patricia PR 162 +2.94 +- 2.11 (MIT) | STC | HAS LmrCutoffThreshold=3 `search.cpp:1145` |
| history depth bonus | Altair PR 182 +5.61 +- 3.85 (MIT) | STC | HAS `search.cpp:1198` (depth + 1 when best > beta + 100); bonus terms are tunables (HistoryBonusQuadratic / Linear / Max): retune only |
| history gravity | - | - | HAS `apply_history` `search.cpp:157-160` |
| history-based LMR | - | - | HAS for quiets `search.cpp:1146` (LmrHistoryDivisor tunable); captures TRIED (LmrCapVictim STB2 H0, LmrTtCapAll STB1) |
| lmrDepth in quiet pruning | Caissa 92a6f69 STC +1.75 / LTC +0.79 (MIT) | both | HAS `search.cpp:1063-1071`; R15 C1 PruneLmrHist PREPARED |
| RFP opponent worsening | Caissa 1df3a86 STC +1.15 / LTC +1.89 (MIT) | both | TRIED gate 62 RfpOppWorse=40 (+2.08, 1,500 g) |
| fail-firm RFP (return a blend) | Altair PR 185 +2.93 +- 2.96 (MIT) | STC | TRIED gate 86 RfpReturnBlend=25: -16.4, H0 |
| qsearch move-count pruning | Caissa fbebb14 +1.79 +- 1.31 (MIT) | STC | PREPARED R15 C2 QsMovePrune |
| pawn history / threat history | Caissa 42c7fdb +1.45 / -0.38; Altair PR 184 (not read) (MIT) | STC | TRIED PawnHist (gates 29/37/44), ThreatHist (gate 64) |
| IIR condition | Caissa 2c442e9 STC +2.08 / LTC +4.61 +- 5.06 n=8,148 (MIT) | both | HAS IIR `search.cpp:1031`; R15 C4 IirShallowTt PREPARED |
| prior countermove bonus | Caissa 956a2b4 +1.64 +- 1.22 (MIT) | STC | HAS, off: FailLowContinuationBonus=0 `search.cpp:64, 1205-1209`; tested inconclusive in the h256e12 era (R15 report): retune only |
| capture futility | - | - | HAS, off: CaptureFutilityBase=0 `search.cpp:61, 1075-1080`; tested inconclusive: retune only |
| qsearch stand-pat blend toward beta | Caissa ae2eb0c +1.19 +- 0.95 n=142,682; b521839 +0.92 (MIT) | STC | LACKS (`search.cpp:816-818` returns the stand pat): dropped, under +1 expected |
| null move only in cut nodes | Caissa 47604ad +1.07 +- 0.86 n=168,198 (MIT) | STC | LACKS (`search.cpp:965` has no cut-node term): dropped, under +1 expected |
| history kept between moves | Caissa 74a0957 (50 -> 75 %) STC +4.34 passed / LTC +0.81 not passed; 22c8670 (75 -> 87.5 %) +1.15 (MIT) | both | Forge keeps 100 % (clears only at ucinewgame: `uci.cpp:188` -> `search.cpp:1493-1495`): already at the end of that trend, no change |
| retunes only (lock tunables, `search.cpp:14-64` / table `:68-99`) | Caissa b8d85fe qsearch futility margin +2.74; 54d226d NMP start depth +0.61; 2994017 RFP improving +1.34; 654aeb8 / 90670d9 singular depth / margin +2.17 / +1.48; 97bef94 LMR scale +2.45 (MIT) | STC | QsFutilityMargin, NullMoveMinDepth, RfpImproving, SingularDepth / SingularMargin, LmrQuiet* are UCI tunables: SPSA, not code |
| staged move picker, SEE reuse, lazy legality | Patricia PR 209 movepick +3.29 +- 2.38 8+0.08 n=31,038 (PENDING: mechanism) | STC | HAS staged picker `search.cpp:321-380`; SEE result of the capture stage reused (`last_move_see_nonnegative()` `:1082`, `:1113`); pseudo-legal generation + `is_legal` per move (`:829`, `:1051`) |

## C. Terms that scale with TC, and patches that passed STC but not LTC (Caissa logs, MIT)
| commit | what | short TC | long TC | reading |
|---|---|---|---|---|
| [e53fe6e](https://github.com/Witek902/Caissa/commit/e53fe6ebf2a48af382fd5d3355e36e3ef63aa173) | NMP margin discount (T04-03) | 10+0.1 +2.00 +- 1.41 | 60+0.6 +5.95 +- 3.14 | grows with TC: decide at LTC |
| [f2967c1](https://github.com/Witek902/Caissa/commit/f2967c12d1), [Patricia 147](https://github.com/Adam-Kulju/Patricia/pull/147) | triple extension (T04-06) | not run | 80+0.8 +3.36; 60+0.6 +3.12 | both engines tested it only at long TC |
| [60b6639](https://github.com/Witek902/Caissa/commit/60b6639a12) | all parameters re-tuned at 80+0.8 | 8+0.08 +0.49 +- 0.74 after 237,990 games, LLR -0.25 | 60+0.6 +3.88 +- 2.28 passed [0,2.5] | tuned constants are TC-specific: SPSA at the TC that is gated / played |
| [74a0957](https://github.com/Witek902/Caissa/commit/74a0957f0b) | keep 75 % of history between moves (was 50 %) | 8+0.08 +4.34 +- 2.27 passed; N=25000 nodes +4.42 passed | 40+0.4 +0.81 +- 2.21, LLR 0.36 [-0.5,2.5], not passed | STC pass, LTC flat: carried-over ordering matters less when each search is long enough to rebuild it (own reading) |
| [836ffcf](https://github.com/Witek902/Caissa/commit/836ffcfa34) | score averaging weight | N=1000 nodes +10.41 +- 4.52 passed | 40+0.4 -0.34 +- 1.89 | fixed-node gain vanished in timed LTC games |
| [ecbcc95](https://github.com/Witek902/Caissa/commit/ecbcc95) | seed aspiration average with first score | N=1000 +38.00; 5+0.05 +0.82 +- 1.84 | - | very low node counts exaggerate |
| [abc2040](https://github.com/Witek902/Caissa/commit/abc2040) | SMP tune | 8+0.08 -2.95 +- 2.50 | 20+0.2 +6.82; 60+0.6 -0.09 +- 1.70 | an SMP tune can lose at STC and be flat at LTC |
Lesson for the Forge gate: the crew gates at STC with [0, 5] / [0, 10] bounds and 1,000-3,000-game caps; lines 4-5 of
section A should get their decision from an LTC run, and no LTC-tuned set should be judged at STC (and vice versa).

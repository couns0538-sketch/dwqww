# T04B table - search gains logged by Stormphrax and Obsidian (GPL-3.0: commit messages, PR text, test logs only)

Lock = FD3A5190 source `src_al1s198_clean`; every "Forge has it" cell is a `bash tools/forge_has.sh` grep of that tree
(lines checked 00:05-00:15 PC clock). Source numbers: OpenBench blocks quoted in Stormphrax PR text (SP, STC 8+0.08
Hash 16-32 MB, LTC 40+0.4 Hash 128 MB, Threads=1, SPRT [0, 3] unless noted) or in Obsidian commit messages (OB, mostly
10+0.1 or 8+0.08, bounds as noted); books never stated (OpenBench defaults, unknown). Elo +- 95 % error, n = games.
SP links: https://github.com/Ciekce/Stormphrax/pull/N ; OB links: https://github.com/gab8192/Obsidian/commit/SHA.
Card rule of the brief: >= +2 at STC with an LTC result, or >= +3 at STC, and Forge lacks it. Forge estimates in the
cards are **UNPROVEN**. Licence: GPL-3.0 for every row (notes/T04B/licences.md); no source file or diff was read.

## A. Cards
| card | idea | source | logged STC / LTC | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|
| T04B-01 | capture history shifts the noisy-move SEE pruning threshold | SP 269 (a5807f3a9e42) | +3.08 +- 2.21 n=28,964 / +6.48 +- 3.34 n=10,130 | LACKS: `-SeeNoisyMultiplier * depth` only, src/search.cpp:1081-1083 | full card |
| T04B-02 | prune captures with very bad capture history at low depth | SP 201 (29e175a2f594) | +5.38 +- 3.11 n=13,814 / +4.69 +- 2.76 n=14,602 | LACKS: history pruning is quiet-only, src/search.cpp:1064, :1070 | full card |
| T04B-03 | LMR search may go one ply past new_depth in PV / ttpv nodes | SP 258 (23400f016460), SP 268 (e1597abd92ce) | 258: +2.98 +- 2.17 n=30,702 / +1.40 +- 1.14 n=87,056; 268: +3.22 +- 2.27 n=27,094 / +2.00 +- 1.56 n=46,438 | LACKS: clamp at new_depth, src/search.cpp:1147 | one-line card |
| T04B-04 | ttpv LMR bonus withheld when the TT score already fails low | SP 223 (a0e71921d364) | +5.96 +- 3.31 n=12,062 / +1.52 +- 1.24 n=74,084 | LACKS: unconditional `if (ss->tt_pv) r -= 1;`, src/search.cpp:1139 | one-line card |

## B. Qualifying or borderline, Forge lacks it, not carded (card cap 4) - ranked
| idea | source | logged STC / LTC | Forge has it (file:line) | verdict |
|---|---|---|---|---|
| minimum singular depth lower, more so in non-ttpv nodes | SP 305 (f959aa446235) | +4.33 +- 2.79 n=18,844 / +3.04 +- 2.11 n=24,816 | `depth >= tune::SingularDepth` (7, a UCI tunable), no ttpv term, src/search.cpp:1089 | next in line: mostly a retune (SPSA) plus a one-line ttpv split (own form: min depth = SingularDepth - 1 + tt_pv) |
| static-eval difference of the last two plies updates the previous quiet move's main history | OB d5f3e454dca9, OB 10fb2d563aca ("more") | d5f3e45: 10+0.1 +2.96 +- 1.80 n=36,250 [0,2] passed; 10fb2d5: +4.17 +- 2.79 n=14,900 LLR 1.81 [0,2] not passed; no LTC | LACKS: no `(ss - 1)->static_eval` use (0 hits) | borderline: just under both thresholds; the largest ordering feature Forge lacks entirely |
| history term in the LMP move-count limit | SP 334 (76c51788836f) | +4.50 +- 2.85 n=18,052 / +1.72 +- 1.39 n=57,258 | LACKS: `lmp_threshold(depth, improving)`, src/search.cpp:149-151, :1062 (one-way `skip_quiets`) | not carded: a per-move form needs a `continue` path beside the lock's skip switch |
| history term in the quiet futility margin | SP 272 (59561ad448c0) | +2.77 +- 2.06 n=33,668 / +3.82 +- 2.45 n=18,728 | LACKS directly (src/search.cpp:1065-1066); R15 C1 PruneLmrHist (PREPARED) lets history enter futility via lmr_depth | evidence for R15 C1 (overlap): gate C1 first |
| capture history indexed by whether the to-square is defended | SP 209 (d699196b32b3) | +3.66 +- 2.46 n=21,748 / +1.57 +- 1.27 n=68,920 | LACKS: `[piece][to][victim]`, include/forge/search.hpp:255 (ThreatHist / HistRework are quiet-only) | not carded: table-shape change; would strengthen T04B-01 / 02 |
| main history mixed into the continuation-history gravity base | SP 270 (06d5691220dd) | +3.89 +- 2.57 n=20,816 / +1.28 +- 1.03 n=105,480 | LACKS: per-entry gravity, src/search.cpp:157-160, :724 | not carded: LTC +1.28, touches every update |
| stronger history ageing between searches | SP 345 (665b76b8a594) | +3.93 +- 2.58 n=21,906 / +1.21 +- 0.96 n=116,824 | LACKS ageing: history kept 100 %, cleared only at ucinewgame (src/search.cpp:577) | not carded: conflicts with Caissa 74a0957 (keeping more history passed STC, flat LTC; notes/T04/TABLE.md B); factor unknown |

## C. Has it, tried, prepared, not applicable, or under the thresholds
| idea | source | logged result | Forge status (file:line) |
|---|---|---|---|
| more move-loop pruning in ttpv nodes | SP 298 (385a4e577165) | +3.14 +- 2.20 / +3.11 +- 2.16 | N-A: the lock's move-loop pruning has no pv / ttpv exemption at all (src/search.cpp:1061) - nothing to relax |
| quiet direct checks that pass SEE get an ordering bonus | SP 320 | +6.63 +- 3.65 n=11,846 / +2.82 +- 2.01 n=27,520 | HAS an unconditional 12000 bonus (src/search.cpp:532); SEE-gated form TRIED: CheckOrderSee gate 65 (+6.25, 1,500 g, cap): evidence to run gate 65 to a decision |
| prior countermove bonus (all moves failed low) | SP 323 | +2.00 +- 1.62 n=63,958 / +4.14 +- 2.59 n=17,368 | HAS, off: FailLowContinuationBonus = 0 (src/search.cpp:64, :1205): evidence for a retune / ON line (T04 TABLE B row) |
| more reduction when the TT move is noisy | SP 306 | +2.96 +- 2.09 / +1.27 +- 1.00 | HAS for quiets (src/search.cpp:1142); all-moves form TRIED LmrTtCapAll (STB1 -3.01) |
| depth +1 / -1 from the parent's reduction and the eval swing | SP 253; SP 300 | 253: +4.33 +- 2.78 n=19,092 / +11.92 +- 4.63 n=5,190 (double patch); 300: +1.73 +- 1.39 / +3.44 +- 2.28 | TRIED packd Hindsight (gates 51-54, -6.25 .. +4.63, 1,500 g at STC); new angle: both source gains are LTC-skewed - an LTC run of the best line (gate 54) |
| correction size in the RFP margin | SP 230 | +2.15 +- 1.69 / +2.51 +- 1.86 | PREPARED round-1 O5 CorrMargins (RFP / futility / NMP / LMR weights), never gated: evidence for an O5 RFP-only line |
| less LMR when the correction is large | SP 212; OB e144325 | +1.39 / +2.10; OB +2.51 +- 1.94 10+0.1 | TRIED LmrCorrThreshold (gate 16, -0.69, 1,000 g) |
| capture-score-adjusted SEE split good / bad captures | SP 192 | +10.99 +- 4.72 n=6,322 (STC only) | TRIED CaptSeeDiv (gates 47 / 48, relax-only floor); T04 TABLE A7; new angle = two-sided threshold |
| IIR when the TT entry is very shallow | SP 186 | +2.60 +- 1.97 n=36,350 (STC only) | PREPARED R15 C4 IirShallowTt: evidence |
| history bonus for the TT move on a TT cutoff | SP 182 | +1.89 +- 1.53 | PREPARED x1 TtCutoffHistory: evidence |
| store the static eval at once / looser TT verification | SP 164; OB 997246d | +6.09 +- 3.40; OB 4+0.04 +3.86 / 8+0.08 +3.28 | TRIED / ported EvalOnlyStore (gates 49 / 50, bundle 68) |
| qsearch move-count limit | SP 167, 171; OB e0c2b3a | +2.83, +2.21; OB +1.56 +- 1.24 n=78,378 | PREPARED R15 C2 QsMovePrune: evidence |
| smaller depth on aspiration fail-highs | SP 155 | 13+0.13 [0,5] +3.15 +- 2.54 | TRIED packc AspFailHighReduce (gates 15 / 28) |
| more LMR when static eval is far below alpha | SP 66 | +3.76 +- 3.20 (STC only) | TRIED Sf26Bundle bit 4 (SF26B14 / UT2: -3.94 / -3.47) |
| major / non-pawn / continuation correction | SP 188, 189, 190, 290; OB fe0637c, a5219f6 | +3.31, +7.63, +8.36, +2.48 / +1.23; OB +9.96 15+0.15, +2.82 | major = T04-04 (evidence); non-pawn and continuation TRIED (packa, CorrHistPlus, ContCorrectionWeight) |
| pawn correction / first correction history | SP 163; OB 302ec63 | +10.63 13+0.13; OB +2.03 / +5.61 | HAS (pawn + material tables) |
| correction tables shared between threads | SP 282 | 4+0.04 Threads=4 +8.58 +- 4.00, Threads=8 +10.64 +- 4.42 | SMP only; gates use Threads=1 (T04 TABLE D row) |
| always find one non-mated move in qsearch | SP 203 | +3.91 +- 2.57 / +3.36 +- 2.27 | HAS: qsearch never prunes in check and guards pruning with `best_score > -MateInMaxPly` (src/search.cpp:831, :865) |
| quiet evasions in qsearch when the TT move is quiet | SP 304 | +2.17 +- 1.72 / +2.69 +- 1.93 | mechanism not stated (refines another engine's "reverse qsearch" PR); lock searches all evasions in check (src/search.cpp:331): dead end |
| do-deeper / do-shallower and its re-search gate | SP 160, 59, 313; OB f899e2b | 13+0.13 +3.10; +2.72; +1.51 / +2.24; OB +1.99 | LACKS: T04-02 (evidence) |
| triple extension | SP 68; OB 14bfa92 | +3.45 +- 3.04 n=23,678; OB +0.90 +- 2.20 n=45,516 | LACKS on the lock: T04-06 (first STC numbers; Obsidian's is flat) |
| TT cutoff needs a deeper entry on fail high | OB f90784d | 60+0.6 +2.00 +- 1.45 n=48,194 | LACKS: T04 TABLE A4 (evidence) |
| qsearch fail-high returns a blend toward beta | OB 8078bb0 | +2.95 +- 2.83 n=27,434 | LACKS; under both thresholds (T04 TABLE B row) |
| futility tweak | OB cbffcd8 | 8+0.08 +2.97 +- 1.98 / 30+0.3 +5.07 +- 4.40 LLR 1.07 | mechanism not in the message (retune-sized): dead end |
| RFP margin never 0 at depth 1 improving | OB eda77c4 | +4.34 +- 3.31 | N-A: the lock's depth-1 improving margin is 72 - 40 = 32 cp (src/search.cpp:960) |
| LMR depth in the quiet SEE margin | OB d1b6b92 | +4.00 +- 3.43 | HAS (src/search.cpp:1071) |
| pawn history beyond the picker / pawn history | OB 06d7965, 10a8a0e | +3.69 +- 2.06; 40+0.4 +2.80 +- 2.06 | TRIED PawnHist (gates 29 / 37 / 44) |
| NMP depth / margin tweaks | OB d89526f, ae20bdc, e9ced10; SP 310, 312 | +3.02, +1.90, +2.46; SP +1.31 / +3.14, non-reg | retunes of lock tunables (NullMoveBase / DepthDivisor / EvalDivisor) or mechanism unstated |
| cut-node LMR, qsearch futility, TT store from probcut, conthist after LMR, negative extensions | SP 175, 69; OB 42392f5, 52b7a82, 86723b4 | +5.11, +4.17; +2.02, +1.84, +1.62 | HAS (src/search.cpp:1141, :821, :1023, :1156, :1108-1110) |
| low-depth SE, good-noisy LMR, reduce after alpha raised, razor guard, TT cutoff only cut / fail-low | SP 221, 226, 284, 307, 195 | +1.61 / +1.65; +1.10 / +1.31; +1.60 / +0.74; +1.95 / +1.37; +1.60 | under both thresholds |
| removals / fixes (check ext, killers, stm butterfly, mates in qsearch, mate vs 50mr) | SP 67, 331, 335, 204, 213 | non-regression bounds | not gains: no card |
| 50mr TT guards (downgrade decisive TT scores past the 50mr horizon; no TT cutoff near a 50mr draw) | SP 338, 339 (titles only, PR text not read) | not read | correctness items, not search gains: not followed |

# T04N candidates: Koivisto, Ethereal, Halogen, RubiChess (all GPL-3.0: commit text, PR text, ChangeLog, OpenBench result blocks only)
Lock = src_al1s198_clean (`s:` = src/search.cpp). Bar for a card: >= +2 STC with an LTC result, or >= +3 STC.
OB = OpenBench; Halogen STC 8+0.08 / LTC 40+0.4, Ethereal and RubiChess STC 10+0.1 / LTC 60+0.6, Threads=1, SPRT [0,3]
unless stated. Numbers copied from the PR / commit text, links in sources.md.

| # | idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|---|
| 1 | negative extension of the TT move when the TT score is <= alpha (non-cut nodes; singular search failed) | [Ethereal f71ac47](https://github.com/AndyGrant/Ethereal/commit/f71ac4769a) | GPL-3.0 | STC +4.66 +- 3.19 n=22,208 LLR 2.96; LTC +2.44 +- 1.95 n=57,696 LLR 2.95; SMP 5+0.05 T8 +3.16 +- 2.96 [-1,2.5] | LACKS: s:1105-1111 (-2 on tt_score >= beta, -1 on cut node); SingularV2 fable-fb2-j3 s:1227-1230 lacks it too | CARD T04N-01 (overlap notes/T04F/TABLE.md row 21: its "SingularV2 has it" holds only for -3 non-PV) |
| 2 | null move only at expected cut nodes | [Halogen #808](https://github.com/KierenP/Halogen/pull/808) | GPL-3.0 | STC +4.05 +- 2.64 n=20,498 LLR 2.95; LTC +1.95 +- 1.53 n=49,716 LLR 2.96 | LACKS: s:965-968 (any non-PV node, no cut_node term) | CARD T04N-02 (revives notes/T04/TABLE.md row 45, dropped on Caissa 47604ad +1.07 +- 0.86 n=168,198) |
| 3 | RFP margin raised when the side to move has pieces under threat | [Halogen #696](https://github.com/KierenP/Halogen/pull/696) | GPL-3.0 | STC +3.72 +- 2.44 n=21,218 LLR 2.96; no LTC | LACKS: s:960-961 (depth x RfpMargin - improving); no threat data in search | ONE-LINE T04N-03 (family of notes/T04F/TABLE.md row 10, Caissa threat-gated improving +1.41, below bar) |
| 4 | null move: extra constant margin on the null-search fail-high test | [Halogen #833](https://github.com/KierenP/Halogen/pull/833) | GPL-3.0 | STC +1.16 +- 0.85 n=194,342; LTC +3.36 +- 2.26 n=22,760 | LACKS: s:979-990 (null_score >= beta) | below the STC bar (LTC-favoured): no card, PENDING an LTC-first owner call |
| 5 | TT fail-high cutoff from a shallower entry when the TT score is far above beta | [Halogen #745](https://github.com/KierenP/Halogen/pull/745) | GPL-3.0 | STC +2.26 +- 1.73 n=41,584; no LTC | LACKS (tt_depth >= depth for all bounds, notes/T04F/DIFF.md row 9) | below the bar: no card (mirror of notes/T04F/TABLE.md row 8) |
| 6 | fail-medium in the main search (fail-high score pulled toward beta) | [Halogen #837](https://github.com/KierenP/Halogen/pull/837) | GPL-3.0 | STC +4.00 +- 2.59 n=20,588; LTC +4.59 +- 2.73 n=15,454 | LACKS (returns best_score) | TRIED FailHighBlend gates 36 / 42: evidence for notes/T04C/TABLE.md row B10, no card |
| 7 | smaller depth after a root aspiration fail high | [Halogen #701](https://github.com/KierenP/Halogen/pull/701) | GPL-3.0 | STC +2.30 +- 1.76 n=40,650; LTC +5.13 +- 2.92 n=13,404; a third 5+0.05 run -0.35 +- 4.07 | LACKS: s:1394-1395 (same depth) | TRIED packc AspFailHighReduce (gates 15 / 28, bundled, cap): evidence for notes/T04B/TABLE.md row 46 |
| 8 | good / bad capture split threshold scaled by capture history | [Halogen #712](https://github.com/KierenP/Halogen/pull/712) | GPL-3.0 | STC +4.82 +- 2.86 n=15,206; no LTC | HAS a score-adjusted split, s:360 | TRIED CaptSeeDiv: evidence for notes/T04B/TABLE.md row 41 |
| 9 | SEE pruning margins in the main search shifted by history | [Ethereal a7a7a8e](https://github.com/AndyGrant/Ethereal/commit/a7a7a8ed69) | GPL-3.0 | STC +6.98 +- 4.53 n=10,260; LTC +2.28 +- 2.36 n=37,522 | LACKS: s:1071 / s:1081-1083 (no history term) | evidence for T04B-01 (noisy) and notes/T04F/TABLE.md row 18 (quiet); the commit text does not say which |
| 10 | shallower LMR re-search when the reduced move fails high by a small margin | [Halogen #743](https://github.com/KierenP/Halogen/pull/743) | GPL-3.0 | STC +2.53 +- 1.88 n=35,266; LTC +2.30 +- 1.82 n=34,060 (LLR 2.68) | LACKS (s:1147-1151) | evidence for T04-02 |
| 11 | negative LMR reduction (one ply deeper) at PV nodes | [Halogen #838](https://github.com/KierenP/Halogen/pull/838) | GPL-3.0 | STC +3.93 +- 2.57 n=21,484; LTC +2.20 +- 1.68 n=40,694 | LACKS (clamp to new_depth, s:1147) | evidence for T04B-03 |
| 12 | triple singular extension | [Halogen #758](https://github.com/KierenP/Halogen/pull/758) | GPL-3.0 | STC +3.47 +- 2.34 n=23,028; LTC +7.76 +- 3.67 n=8,326 | PREPARED SingularV2 | evidence for T04-06 (LTC-favoured, as the card says) |
| 13 | -2 (not -1) at non-singular cut nodes | [Halogen #702](https://github.com/KierenP/Halogen/pull/702) | GPL-3.0 | STC +5.02 +- 2.93 n=14,466; no LTC | lock -1 s:1109-1110; SingularV2 -2 | evidence for SingularV2 (notes/T04F/DIFF.md row 47) |
| 14 | -2 near a multicut (singular score close to beta) | [Halogen #703](https://github.com/KierenP/Halogen/pull/703) | GPL-3.0 | STC +1.95 +- 1.54 n=52,274 | LACKS | below the bar |
| 15 | negative extension at non-singular cut nodes | [Halogen #623](https://github.com/KierenP/Halogen/pull/623) | GPL-3.0 | STC +5.40 +- 3.08; LTC +7.77 +- 3.90 | HAS s:1109-1110 | dead end |
| 16 | more LMR at cut nodes | [Halogen #622](https://github.com/KierenP/Halogen/pull/622) | GPL-3.0 | STC +8.64 +- 4.05; LTC +6.58 +- 4.28 [0,5] | HAS s:1141 | dead end |
| 17 | LMR never drops into qsearch | [Halogen #839](https://github.com/KierenP/Halogen/pull/839) | GPL-3.0 | STC +2.44 +- 1.86; LTC +1.20 +- 0.94 | HAS s:1147 (clamp to >= 1) | dead end |
| 18 | zero-width LMR re-search at depth 1 | [Halogen #841](https://github.com/KierenP/Halogen/pull/841) | GPL-3.0 | STC +1.81 +- 1.45; LTC +1.27 +- 1.01 | n/a | below the bar |
| 19 | futility pruning also in PV nodes | [Halogen #830](https://github.com/KierenP/Halogen/pull/830) | GPL-3.0 | STC +1.94 +- 1.55; LTC +0.56 +- 1.13 (LLR -0.84) | n/a | below the bar |
| 20 | prior-countermove bonus on every quiet history | [Halogen #829](https://github.com/KierenP/Halogen/pull/829) | GPL-3.0 | STC +2.31 +- 1.78 n=44,006; no LTC | HAS, off: s:1205-1209 | below the bar; evidence for notes/T04/TABLE.md row 42 |
| 21 | threat-indexed quiet history | [Halogen #576](https://github.com/KierenP/Halogen/pull/576) | GPL-3.0 | STC +2.92 +- 2.12; LTC +1.51 +- 1.22 | TRIED ThreatHist gate 64 | evidence for the tried line |
| 22 | pawn-hash-indexed quiet history | [Halogen #575](https://github.com/KierenP/Halogen/pull/575) | GPL-3.0 | STC +1.51 +- 1.21; LTC +1.70 +- 1.36 | TRIED PawnHist | below the bar |
| 23 | ply-4 continuation history read in quiet ordering | [Halogen #695](https://github.com/KierenP/Halogen/pull/695) | GPL-3.0 | STC +4.62 +- 2.81 n=16,386; no LTC | LACKS read: s:708-709 plies 1-2 (ply 4 written, s:721) | TRIED ContHist4Pct: evidence for notes/T04G/TABLE.md row 7 |
| 24 | hindsight extension | [Halogen #753](https://github.com/KierenP/Halogen/pull/753) | GPL-3.0 | STC +1.33 +- 1.15 n=96,530 (LLR 2.48) | TRIED packd Hindsight 51-54 | below the bar |
| 25 | randomised draw scores | [Halogen #730](https://github.com/KierenP/Halogen/pull/730) | GPL-3.0 | -0.15 +- 1.61 (LLR -1.74) | n/a | dead end |
| 26 | qsearch detects mate | [Halogen #725](https://github.com/KierenP/Halogen/pull/725) | GPL-3.0 | -0.67 +- 1.70 H0 | n/a | dead end |
| 27 | re-search alpha-raising nodes that fail high above beta | [Halogen #650](https://github.com/KierenP/Halogen/pull/650) | GPL-3.0 | +0.27 +- 1.05 H0 | n/a | dead end |
| 28 | keep the old TT move on an upper-bound store | [Ethereal d9b9bec](https://github.com/AndyGrant/Ethereal/commit/d9b9bec) | GPL-3.0 | STC +4.53 +- 3.14 n=23,104; LTC +3.50 +- 2.61 n=32,728 | HAS: best_move only on score > alpha s:1173, none keeps the old move s:294 | dead end |
| 29 | cut-node flag + IIR at cut nodes | [Ethereal 3071b40](https://github.com/AndyGrant/Ethereal/commit/3071b40) | GPL-3.0 | STC +4.39 +- 3.07; LTC +2.88 +- 2.25 | HAS s:1031 | dead end |
| 30 | IIR when the TT entry is much shallower | [Ethereal 0850fdd](https://github.com/AndyGrant/Ethereal/commit/0850fdd) | GPL-3.0 | STC +2.86 +- 2.65 n=30,698; LTC +3.31 +- 3.05 n=22,432 | PREPARED R15 C4 IirShallowTt | evidence for notes/T04C/TABLE.md row B12 |
| 31 | LMR history term without its clamp | [Ethereal f01531b](https://github.com/AndyGrant/Ethereal/commit/f01531b) | GPL-3.0 | STC +3.53 +- 4.32; LTC +0.56 +- 2.24 | n/a | LTC flat: dropped |
| 32 | double extension for very singular moves | [RubiChess #455](https://github.com/Matthies/RubiChess/pull/455) + ChangeLog 20240817 | GPL-3.0 | STC +11.51 +- 6.31 n=5,830; LTC +8.80 +- 5.58 n=7,070 | HAS s:1101-1103 | dead end |
| 33 | reduction when there is no TT move (IIR) | [RubiChess #411](https://github.com/Matthies/RubiChess/pull/411) + ChangeLog 20230410 | GPL-3.0 | STC +3.27 +- 2.51; LTC +4.55 +- 3.19 | HAS s:1031 | dead end |
| 34 | history extension: +1 ply for a quiet with very high history, self-adjusting threshold | [RubiChess #396](https://github.com/Matthies/RubiChess/pull/396) + ChangeLog | GPL-3.0 | STC +2.93 +- 2.30 n=44,752; LTC +2.38 +- 1.92 n=63,832 (a threshold change of an existing feature) | LACKS (only singular and check extensions, s:1089-1114) | no card: number for the feature itself missing |
| 35 | "store native depth in TT" | [RubiChess #474](https://github.com/Matthies/RubiChess/pull/474) | GPL-3.0 | STC +3.20 +- 2.99; LTC +8.36 +- 5.45 n=7,444 | unknown | no card: mechanism not stated (title only) |
| 36 | "Tweak 1" | [RubiChess #439](https://github.com/Matthies/RubiChess/pull/439) | GPL-3.0 | STC +2.15 +- 2.22; LTC +2.66 +- 2.69 | unknown | no card: mechanism not stated |
| 37 | limit the check extension | [RubiChess #457](https://github.com/Matthies/RubiChess/pull/457) | GPL-3.0 | STC +1.32 +- 1.45 | n/a | below the bar |
| 38 | Koivisto since 2023 (40 commits) | [Koivisto](https://github.com/Luecx/Koivisto/commits) | GPL-3.0 | net +20, node-based time checks +17 / +12, accumulator speed +7..+9 | n/a | out of topic: no search / eval post-processing commit |

## Evidence for existing cards and tried lines (no new card)
- evidence for T04-06 (triple extension, decide at LTC): [Halogen #758](https://github.com/KierenP/Halogen/pull/758)
  STC 8+0.08 +3.47 +- 2.34 n=23,028 [0,3] LLR 2.95; LTC 40+0.4 +7.76 +- 3.67 n=8,326 [0,3] LLR 2.95 (LTC above STC).
- evidence for T04B-03 (LMR one ply deeper at PV nodes): [Halogen #838](https://github.com/KierenP/Halogen/pull/838)
  STC +3.93 +- 2.57 n=21,484 LLR 3.00; LTC +2.20 +- 1.68 n=40,694 LLR 2.96.
- evidence for T04-02 (shallower re-search after a small reduced fail high): [Halogen #743](https://github.com/KierenP/Halogen/pull/743)
  STC +2.53 +- 1.88 n=35,266 LLR 2.97; LTC +2.30 +- 1.82 n=34,060 LLR 2.68 (merged before reaching 2.94).
- evidence for T04B-01 (history in the noisy SEE pruning threshold): [Ethereal a7a7a8e](https://github.com/AndyGrant/Ethereal/commit/a7a7a8ed69)
  STC 10+0.1 +6.98 +- 4.53 n=10,260 LLR 2.98; LTC 60+0.6 +2.28 +- 2.36 n=37,522 LLR 2.95; quiet / noisy scope not
  stated in the commit text (also fits notes/T04F/TABLE.md row 18, quiet).
- tried lines with a new outside number (owner may re-weigh, no card): FailHighBlend (gates 36 / 42) <- Halogen #837
  STC +4.00 / LTC +4.59; packc AspFailHighReduce (gates 15 / 28, bundled) <- Halogen #701 STC +2.30 / LTC +5.13;
  ThreatHist (gate 64) <- Halogen #576 +2.92 / +1.51; ContHist4Pct (gates 31-33) <- Halogen #695 +4.62 STC;
  CaptSeeDiv (gates 47 / 48) <- Halogen #712 +4.82 STC; R15 C4 IirShallowTt (prepared) <- Ethereal 0850fdd
  +2.86 / +3.31; SingularV2 cut-node -2 (prepared) <- Halogen #702 +5.02 STC.

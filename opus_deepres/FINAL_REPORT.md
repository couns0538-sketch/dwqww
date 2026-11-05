# Forge deep research - FINAL REPORT

**State: INTERIM** (finished 23:40 PC clock on 2026-11-04, 1 h 17 min after the start). Core tracks T1, T2,
T4, T5 and the extra tracks T6, T7 are researched AND verified; T12 is researched, its verifier was still running;
the cross-track second checks (phase 2) have not run. This is not the FINAL report.

Started 2026-11-04 22:23:27 PC clock; deadline 2026-11-05 08:23:27. Branch `opus-deepres-20261104`.
No Elo claim for Forge anywhere: every source number is quoted with its link and conditions in the card, every
Forge-side estimate is labelled UNPROVEN; the crew gates. Cards: `cards/T<nn>/`; per-track tables, notes and the
verifiers' findings: `notes/T<nn>/` (`VERIFY.md`); licences at the exact commits read: `LICENCES.md`.

### Addendum 01:36 (owner's usage warning; this INTERIM text above and below is from 23:40)
Since the INTERIM: phase 2 (critic `notes/CRITIC.md`, second vote `notes/TOP_SECOND_VOTE.md`) found that T04-02 and
T06-05 already exist as our own packb code (ReSearchAdjust / FiftyDamp), gated only as a bundle on old bases with the
source engines' constants (new angle: gate each alone on the lock with own constants), and downgraded T05-01 / T05-03
/ T05-04 (target cost not shown beyond noise). The card fixer applied the card-level findings (`notes/FIXES_APPLIED.md`).
Round 2 (owner: more improvements, more agents) added sub-tracks T04B-T04H, T05B-T05E, T06B, T06C, T02B, T01B, T12B
(88 card files, 5 of them merge markers of duplicates; each sub-track with a Fable verifier; T05D, T05E, T01B and T12B
verifiers still finishing); implementation specs `notes/SPEC_SEARCH.md`, `notes/SPEC_EVAL.md`. Strongest new
multi-engine idea: a quiet-move history malus that shrinks with the move index (Stockfish a016abd STC +3.78 / LTC
+2.18; Berserk 7451fd7 +2.26 / +2.04; Reckless PR 1038 STC +4.67; Patricia PR 172 LTC +2.39) = card T04E-03 with the
other three merged into it. The ranking below is still the INTERIM one; the FINAL ranking will merge round 2.

## 0. First: the data blocker (T2-card-1, card T02-01, COMPLETE)
The J1 npt train binpack is written from FPOS rows, which carry no castling, no en passant and no clocks, so the net
sees board + side to move only: that is the leak key, and it subsumes the 4,088 EP-normalised keys. Drop the 7,700
train rows already listed (path + line) in `D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv` (0.0025 % of 304,999,573; the
minimum for "4,088 -> 0" is 4,118), rebuild the 37 train shards with the same converter, prove count / dropped keys /
0 shared keys on all three keys / seals. Game level: no authentic game IDs exist; a cheap block rule (new block when
the result changes or the ply does not increase) reproduces the R14 scan's break classes within 16 of 189k pairs and
shows both train/holdout seams are breaks, so the 013/014 split is block-aligned already. Cost: under 30 CPU-minutes
on one core (measured logs), 10.4 GB on C:, crew ~2 h. Direct Elo: none expected (enabler). The T2 verifier confirmed
the card's numbers against the three files it cites.

## 1. Top 10 by expected Elo per crew-hour, and the suggested gate order
Metric: midpoint of the card's UNPROVEN Forge range / crew hours of the card. Three classes gate against different
baselines and are kept apart: **L** = lock-direct (SPRT vs FD3A5190 now), **V** = v2-line only (bit-exact, nps ABBA,
zero Elo for the lock; worth something only when a v2 net such as U8 / r5 is gated or adopted; nps -> Elo uses the
source engine's wiki rule "Elo_STC = 2.10 x for x % nps" as quoted in the 30-Oct round, its use for Forge UNPROVEN),
**G** = GPU-conditional (gain over a parent net that is not gated yet; listed separately below).

| # | card | cl. | idea | source evidence (full conditions + links in the card) | Forge est. UNPROVEN | crew h | per crew-h |
|---|---|---|---|---|---|---|---|
| 1 | T06-05 | L | EvalRule50Damp at the fitted strength (D=60; option exists) | SF 7b06475 STC ~+4.2 / LTC ~+2.9; Forge UE3C D=30 +1.51 (3,000 g, LLR -0.53) | 0 to +3 | 0.5 | 3.0 |
| 2 | T04-02 | L | LMR re-search deeper / shallower after a reduced fail-high | Caissa 434bbda STC +6.93 +- 3.88 (14,696 g) / LTC +5.14 +- 3.35 (18,914 g); Patricia PR 137 +5.55 +- 3.25 | +2 to +6 | 2 | 2.0 |
| 3 | T04-01 | L | singular verification search as a non-cut node | Caissa 1b7a871 STC +4.20 +- 2.23 (25,044 g, [0,2]) | 0 to +3 | 1 | 1.5 |
| 4 | T05-01 | V | int16 first-layer store (exact: every value a multiple of 2^-12) | own records only (P2 = 0.948 for KB4 tables) | +1 to +4 % nps on KB4 / KB8 | 3 | ~1.7 |
| 5 | T04-05 | L | correction-history update also when the best move is a SEE-losing capture | Caissa 54aef4a STC +2.63 +- 1.68 (44,298 g) | 0 to +2 | 1 | 1.0 |
| 6 | T04-03 | L | null-move margin discount when the child produced few cutoffs (decide at LTC) | Caissa e53fe6e STC +2.00 +- 1.41 (61,474 g) / LTC +5.95 +- 3.14 (10,918 g) | STC 0 to +2, LTC +1 to +4 | 2 | 1.0 |
| 7 | T05-04 | V | prefetch the dirty-piece w1 columns when the move is recorded | no source number (own idea) | +0.5 to +2 % nps | 1.5 | ~1.7 (unsourced: after T05-01) |
| 8 | T05-03 | V | 2 MB pages for the v2 first-layer tables / refresh caches | SF PR 6359 ~+1.2 % nps (STC [0,2] passed, 166,272 g); PR 7041 +1.04 % | KB8 +0.5 to +1.5 % | 2.5 | ~0.8 |
| 9 | T04-06 | L | triple singular extension | Patricia PR 147 60+0.6 +3.12 +- 2.14 (24,804 g); Caissa f2967c1 +3.36 +- 2.07 (a bundle) | 0 to +3 (LTC) | 2 | 0.75 |
| 10 | T04-04 | L | minor- and major-piece correction-history keys | Altair PR 189 +7.74 +- 5.71 (7,008 g, [0,4]); PR 188 +6.84 +- 5.23 (8,280 g) | +1 to +4 | 4 | 0.63 |

GPU-conditional (gain over the parent / control net; needs a GPU window and a parent line worth improving):
T02-03 WDL-consistency skip ON at the decided lambda (crew 0.5 h, 2 GPU runs; 0 to +3), T01-06 pure-WDL low-LR final
stage (crew ~0.5 h, ~1.5 GPU h; 0 to +2), T02-02 early-ply cut retrain (crew 2-4 h; 0 to +5), T01-03 R2 warm start +
sparse threats (crew 8-12 h; 0 to +5), T01-04 KB16 + halfmove inputs, T01-05 pawn pairs, T01-02 Ranger, T02-06
endgame-book subset, T02-05 Syzygy rescoring (section 2).

**Gate order (gate-machine hours are the bottleneck, not crew hours).** One SPRT at the crew's measured rate
(430-502 games/h for every `*_vs_AL1*` gate, T07 verifier; 497 games/h at Threads 2 / conc 4) and the T12-01
suggestion ([0,10] nElo, cap 12k; mean ~6.6k games) costs ~13 gate-hours; the gates as run (caps 1,500-3,000) left
79 of 110 undecided (T12-01). So: (0) owner decision on bounds / caps and Threads (section 6) before new lines;
(1) T04-02 (best evidence: two engines, STC and LTC); (2) T06-05 (no build); (3) T04-01; (4) T04-03 straight to the LTC
decision; (5) T04-05; then T04-06 / T04-04. In parallel, without SPRTs: T05-01 -> T05-04 -> T05-03 as nps ABBA on the
v2 gate exe (they help exactly the U8 / r5 v2 gates the 30-h job proposed), after the T12-03 bench + fuzz proof. Before
any npt or v2 retrain: the T02-04 WAC diagnostic (0.5 crew h) - it decides whether speed or data is the npt lever.

## 2. All cards ranked (by class; the card has the full evidence, effort and OFF-by-default design)
**L - lock-direct search / eval / time** (per crew-h): T06-05 3.0 | T04-02 2.0 | T04-01 1.5 | T04-05 1.0 | T04-03 1.0
| T04-06 0.75 | T04-04 0.63 | T06-04 eval grain + jitter (SF d212e66 STC ~+0.91 / LTC ~+2.42; +0.5 to +2; 2 h) 0.63 |
T06-01 two-sided material scaling (SF 1dbd2a1 STC ~+4.0 / LTC ~+4.6; 0 to +4 over EvalMatScale=12; 4 h + ~14 h SPSA)
0.5 | T06-02 HCE vs residual re-weighting at level material (SF a2f01c0 ~+3.4 / ~+2.7; 0 to +3; 3.5 h) 0.43 | T07-02
score-stability soft-limit scaling (Alexandria PR 438 STC +1.42 +- 1.15 / LTC +1.71 +- 1.37; +1 to +3; 3.5 h) 0.43 |
T07-01 time-disadvantage scaling (SF 5ca4bfe72b STC +1.13 +- 0.90 / LTC +1.08 +- 0.69; 0 to +2; 3 h; at the +1 line,
likely H0 at [0,5]) 0.33 | T06-03 complexity decay (SF 4c4cb18 ~+0.85 / ~+1.30; 0 to +1.5; 4 h) 0.19.
**V - v2-line speed (nps ABBA)**: T05-01 ~1.7 | T05-04 ~1.7 (unsourced) | T05-03 ~0.8 | T05-02 one hot eval path
for the v2 gate exe (own records: profile coverage moved the v2 path 0.71x -> 1.0x; +0 to +2 %; 4-8 h) ~0.35.
**G - nets and data (GPU)**: T02-03 ~3.0 | T01-06 ~2.0 | T02-02 ~0.8 | T01-04 ~0.5 | T01-05 ~0.5 | T02-06 ~0.75 (plus
~5 h datagen) | T01-02 ~0.33 | T01-01 / T01-03 R2 ~0.31 | T02-05 ~0.25. **Enablers / diagnostics (0 Elo directly)**:
T02-01 (overlap to 0), T02-04 (WAC: speed or knowledge), T12-03 (bench + fuzz proof lets bit-exact speed changes skip
the SPRT), T12-01 (bounds and caps that decide), T12-02 (nps protocol for 1 % at 2-5 % noise), T12-04 (SPSA plan for 20
constants: ~16.7k pairs to resolve 2 Elo), T12-05 (books / TC). Details: `notes/T04/TABLE.md`, `notes/T02/TABLE.md`,
`notes/T05/SPEED_LIST.md`, `notes/T01/recipes.md`, `notes/T12/PROTOCOLS.md`.

## 3. Cross-track facts this report uses (where the cards differ)
- Gate rate: 430-502 games/h measured (all `*_vs_AL1*` rows; T07 verifier) - the "~1,000 games/h at conc 8" in the T04
  cards and T12-04 is an older / unmeasured rate.
- v2 control: the post-root-fix control is -20.9 +- 18.5 (v2p4 + lock-as-KB4 vs the lock, 30-h report); T01-01 / T01-03
  quote the pre-fix -32.2 +- 18.5 (the T01 verifier flagged it).
- T5 answer: v2p4 at 0.85-0.89x = build P1 ~0.98 x KB4 table + refreshes P2 ~0.95 x finer layout P3 (KB8 0.988, KB32
  0.942) x an unmeasured ~0.97 (P4, same for Y8 and Z32); measured parts explain ~60-80 % (`notes/T05/V2P4_GAP.md`).
  The lock and v2 nets have no hidden L1 layer, so int8 / VNNI / find-nnz / weight permutation apply only to the
  HalfKA path. Zen 5 (uops.info): VPDPBUSD zmm latency 3, 0.5 c; VPCOMPRESSD register 1.0 c, store form 8 uops (Zen 4:
  144). BOLT on MSYS2 / Windows: **no** - "BOLT operates on X86-64 and AArch64 ELF binaries" (bolt/README.md @b5376302).
- Data premise: the training set is exactly the self-play J1 binpack (304,999,573 rows) and the w4 runs used
  `--start-lambda 1.0 --end-lambda 1.0` (from the run log) - the brief's "305M Lichess plus self-play" and the identity
  of `--no-wld-filtered` with the WDL skip are to be confirmed by the crew, not built on. The npt HalfKA nets run at
  0.47-0.58x the OFF nps (bench, T02-04): a large share of their -86 to -116 Elo vs AL1 can be speed.
- Self-play still runs the 6.2.0 HCE build at 5,000 nodes; MIX.md's first recommendation is the lock as the teacher.

## 4. Ideas already in Forge (found by the tracks; full lists in the track notes)
Probcut never in check (search.cpp:952-1027); history kept across moves (cleared only at ucinewgame); losing captures
last (search.cpp:396-398); TT move kept in a non-overwritten entry (:293); qsearch TT 50-move guard
(TTEntry::score_usable, search.hpp:83-86); best-move stability and per-iteration falling-eval in TM (search.cpp:1436-
1438, 1451-1454), soft / hard tunables, node-effort TM; per-worker refresh cache in the v2 path; self-play rows already
drop in-check, capture / promotion best moves, mate and bound scores, |cp| > 3000; E3 options EvalMatScale /
EvalOptimism / EvalRule50Damp / DrawJitter. Already tried or prepared (dropped): continuation / non-pawn correction,
multicut blend, negative extensions, qsearch move-count pruning, IIR, pawn / threat history, fail-firm RFP (gate 86).

## 5. Dead ends (one line each; the hand-backs and notes hold the rest)
Merged king planes (neutral) | wider L1 (fixed-node gain vanishes at real TC) | distillation (no stronger teacher net
offline) | from-scratch threat nets (110G positions vs our 305M) | relabel by deeper search of the same engine at fixed
net size: no source with Elo | complexity-based and eval-level TM (both removed later as neutral in the source) |
asymmetric optimism (symmetrised later) | draw jitter under +1 at 10+0.1 | int16 accumulators (bound 342,331 > 32,767) |
int8 first layer (weights need 15 bits) | BOLT (ELF only) | shared correction tables (SMP only).

## 6. Owner items
1. Gate Threads: the brief says Threads=1, the UHO gates' RUN_INFO and the R15 INDEX lines use Threads=2 (conc 4).
2. Gate bounds / caps (T12-01): 79 of 110 gates ended capped; e.g. [0,10] nElo cap 12k or [0,15] cap 6k.
3. EvalOptimism=40 rerun ended H0 (-5.30 +- 7.20, 2,360 g, LLR -2.99, ~22:53): the optimism line looks closed.
4. Viridithas v20.0.0 is MIT at its tag 0631113e22 (AGPL only from v21): reading that tag's source is licence-clean -
   owner decides. Integral's MIT-carded dataset holds no files; training on another engine's data is a policy choice.
5. lambda 1.0 in the w4 runs vs the decided 0.7-0.9 for self-play; where the Lichess rows are and how many.
6. Syzygy files on grok-pc (T02-05, MIX.md 4)? tmfit gates 227 / 228 are not in FORGE_RESULTS.csv (stale pointer).
7. Correctness: the lock fills `bad_captures_` (`std::array<Move, 64>`, search.cpp:453) at :361 with no bound
   check; more than 64 SEE-losing captures needs crafted promoted-piece positions - add a crafted FEN to the sanitizer
   CI and a bound (node-identical whenever <= 64).
8. `C:\o13` was restructured outside this job between ~22:50 and 23:00 (STATUS.md, observations).

## 7. Skills, scripts and tools created or improved
- Skill `skills/forge-deep-research/SKILL.md` (new; also installed as a user-scope skill on grok-pc): setup, tools,
  worker rules, the custom workflow, checkpoints, the low-usage stop, pitfalls.
- Skill `skills/forge-pc-rules/SKILL.md` (branch copy with this job's section; the commit-trailer line made
  brief-dependent; the D: project copy was not touched - this job writes nothing to D:).
- `opus_deepres/tools/`: `mine_commits.py`, `licence_at.py` (two guess fixes during the job: GPL vs AGPL title, LLVM
  Apache; CC0), `forge_has.sh`, `card_lint.py`, `tried_gates.py`, `block_rule_check.py`, `merge_licences.py`,
  `workflow_prompts.py`, `handbacks.py`, `novendor_filter.py`; workflows in `tools/workflows/` (`deepres_tracks.js`).

## 8. Incomplete work and process deviations
- Not done yet: T12 verify (running); phase 2 (one cross-track critic: unanswered brief questions such as history
  gravity, staged picker, SEE caching, lazy legality, TT-prefetch placement, in-check / |eval|-cap filters; one
  second vote on the top-10 source numbers); the FINAL report.
- Deviations, as they happened: the first core workflow was stopped at 22:47 to re-plan for the 12-agent allowance
  (T1 / T2 continued from their files); four workers (T01, T05, T07, T12) put temporary files into this session's
  scratchpad on C: instead of F:\odr (left in place; WORKER_RULES fixed at 23:38); one commit message says "23:2x"
  for a commit made at 23:18 (corrected in the next message); the licence tool's first guesses were wrong for GPL-3.0
  and LLVM texts (fixed, table re-run); MIX.md carried over a Caissa constant (verifier VIOLATION, fixed 23:34);
  early STATUS times were estimates (replaced with measured stamps).
- Measured spend: the core workflow (8 agents) used 1,802,872 agent tokens in 2,710 s; the first (stopped) run and the
  extra workflow are not summed yet; this session's own usage cannot be read (USAGE UNKNOWN).

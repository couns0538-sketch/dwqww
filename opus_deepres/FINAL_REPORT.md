# Forge deep research - FINAL REPORT

**State: INTERIM 2 (consolidated)** - written from 02:28 PC clock on 2026-11-05 (finish time in the last line). Rounds
1 and 2 are researched and verified; one verifier (T05F) and the post-usage-reset round are still to come. This is not
the FINAL report: the state line will say FINAL, STOPPED - TIME LIMIT or STOPPED EARLY - LOW USAGE at the end.

Started 2026-11-04 22:23:27 PC clock; deadline 2026-11-05 08:23:27. Branch `opus-deepres-20261104`. No Elo claim for
Forge anywhere: every source number is quoted with its link and conditions in the card; every Forge-side estimate is
labelled UNPROVEN; the crew gates. Cards `cards/T<nn>[X]/`; per-track tables, diffs, notes and the verifiers' findings
`notes/T<nn>[X]/` (`TABLE.md`, `DIFF.md`, `VERIFY.md`); cross-track checks `notes/CRITIC.md`, `notes/CRITIC2.md`,
`notes/TOP_SECOND_VOTE.md`; the full ranked table `notes/RANKING_DRAFT.md`; licences at the commits read `LICENCES.md`.

## 0. First: the data blocker (T2-card-1, card T02-01, COMPLETE, verified)
The J1 npt train binpack is written from FPOS rows (no castling, no en passant, no clocks), so the net sees board + side
to move only: that is the leak key, and it subsumes the 4,088 EP-normalised keys. Drop the 7,700 train rows already
listed (path + line) in `D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv` (0.0025 % of 304,999,573; the minimum for "4,088 -> 0" is
4,118), rebuild the 37 train shards with the same converter, prove count / dropped keys / 0 shared keys on all three
keys / seals. Game level: no authentic game IDs exist; a cheap block rule (new block when the result changes or the ply
does not increase) gives the R14 scan's break total within 16 of 189k pairs (per class 25 and 41 apart) and shows both
train/holdout seams are breaks, so the 013/014 split is block-aligned. Under 30 CPU-minutes on one core (measured
logs), 10.4 GB on C:, crew ~2 h. Direct Elo: none expected (enabler for every net card).

## 1. Top 10 by expected Elo per crew-hour (lock-direct class; after the second vote and both critics)
Metric: midpoint of the card's UNPROVEN range / the card's crew hours (`notes/RANKING_DRAFT.md` rule). Crew hours are
small for every row; gate-PC hours are the real cost (next paragraph).

| # | card(s) | idea | best source evidence (all conditions + links in the card) | Forge est. UNPROVEN | crew h | per crew-h |
|---|---|---|---|---|---|---|
| 1 | T06-05 | rule-50 damping at the fitted strength (EvalRule50Damp=60, then ~81; one option value on the E3 exe) | SF 7b06475 STC ~+4.2 / LTC ~+2.9; own: UE3C D=30 +1.51 (3,000 g); holdout fit favours D=81 | 0 to +3 | 0.5 | 3.0 |
| 2 | T04-02 | LMR re-search deeper / shallower after a reduced fail-high | Caissa 434bbda STC +6.93 +- 3.88 / LTC +5.14 +- 3.35; Patricia PR 137 STC +5.55 +- 3.25 | +2 to +6 | 2 | 2.0 |
| 3 | T04-01 | singular verification search as a non-cut node | Caissa 1b7a871 STC +4.20 +- 2.23 (25,044 g) | 0 to +3 | 1 | 1.5 |
| 4 | T04D-01 | one more LMR ply at expected cut nodes without a TT move | SF 9cc15b3 STC +2.72 +- 1.74 (42,304 g), LTC passed (32,334 g) | 0 to +3 | 1 | 1.5 |
| 5 | T04D-02 | low-depth TT cutoff only when its direction matches the node type | SF 43e100a STC +2.72 +- 1.72 / LTC +1.02 +- 0.62 (270,888 g) | 0 to +3 | 1 | 1.5 |
| 6 | T04C-02 | lower singular beta at former-PV (ttpv) nodes | PlentyChess 286 STC +5.21 +- 3.51 / LTC +5.34 +- 3.21 (both unfinished); larger-n SF pair in notes/T04H TABLE row 18 | 0 to +3 | 1 | 1.5 |
| 7 | T04E-02 | no null move when the hash move captures a valuable piece | Reckless STC +3.43 +- 2.31 / LTC +3.67 +- 2.27; Viridithas LTC +1.88 +- 1.48 | +1 to +3 | 1.5 | 1.33 |
| 8 | T04F-01 | qsearch in check: stop after the first evasion that is not mated | Caissa a677c89 +3.3 +- 2.6 (25,531 g; TC not stated); no LTC | +1 to +3 | 1.5 | 1.33 |
| 9 | T04B-01 (+ T04E-04, T04B-02) | capture history in the SEE pruning thresholds (main search; qsearch sibling) | Stormphrax PR 269 STC +3.08 +- 2.21 / LTC +6.48 +- 3.34; Reckless PR 1113 STC +4.53 +- 2.72 / LTC +3.61 +- 2.32 | +1 to +4 | 2 | 1.25 |
| 10 | T04E-03 (+ T04C-04, T04D-03, T04G-03) | quiet-move malus that shrinks with the move index | Reckless PR 1038 STC +4.67 / LTC +5.18; SF a016abd STC +3.78 / LTC +2.18; Berserk 7451fd7 STC +2.26 / LTC +2.04; Patricia PR 172 LTC +2.39 | +1 to +3 | 2 | 1.0 |

Notes on the list: #1 and #2 are NOT new ideas - our own packb code has both (FiftyDamp, ReSearchAdjust), gated only as
one bundle in gates 12 / 35 / 40 / 41 (1,000-1,500 games, old bases, no decision) and with the source engines' tuned
constants; the new angle is each alone on the lock, with own constants (and a ply guard for T04-02). #3, #6 and T04-06
(triple extension, prepared as FB2-J3 SingularV2) all edit the singular block: one bit-set option, gated bit by bit.
#9 and its siblings act on the same captures one ply apart: gate one at a time, stacked gain unknown. #10 has the
broadest evidence of the job (four engines, both TCs). Close behind (~1.0-1.25 per crew-h): T12-04 SPSA of 20 live
constants (plus 33-67 h of tuning games), T04E-01 LMP keeps quiet checks, T04G-05, T04-05, T04C-05, T04D-05, T04H-03,
T01-04 (G class). Demoted by CRITIC2: T04H-02 (the source reverted it after three days), T04-04 (estimate now 0 to +2:
two loose early-stopped SPRTs, and Reckless later removed both keys without loss).

**Gate order** under the crew's decision (section 6, item 1: Threads=1, SPRT [0,5] normalized Elo, alpha = beta =
0.05, pentanomial, cap 3,000 games = ~6-7 gate-hours at the measured 430-502 games/h; a capped run is UNPROVEN / no
decision, a positive one gets exactly one extension): (1) T04E-03 (four engines); (2) T04-02 alone
with own constants; (3) T04E-02; (4) T04B-01, then T04E-04 alone, then stacked; (5) T04D-01 and T04D-02; (6) T06-05 (no
build); (7) the singular bit-set option (T04-01, then T04C-02, then the T04-06 triple at LTC); (8) T04F-01. Without
SPRTs, after the T12-03 bench + fuzz proof (nps ABBA, T12-02 protocol): lock speed T05D-01 (port of the R7 exclusive TT
access, own +3.6-4 % on another tree; NOT in the lock), T05C-02, T05C-03, T05B-02. Net-line speed (V class) only when a
v2 / HalfKA net heads for a gate: T05E-01 (HalfKA refresh cache - port of our own v3 / v2 caches). GPU window: T02-01
first, the T02-04 WAC equal-node diagnostic (0.5 h: speed or knowledge), then T02-03, T01-06 / T01-03 R1, T01-03 R2.

## 2. All cards ranked
`notes/RANKING_DRAFT.md` (written 02:00 by a ranking agent from every card, the second vote and the fixer log): 81 rows
from 88 files, five classes (L lock-direct SPRT, V net-line speed ABBA, S lock speed ABBA, G GPU-conditional, E enabler /
diagnostic; % nps and Elo never converted into each other), duplicates folded into one row, top 15 at its head. Apply
`notes/CRITIC2.md` on top: T04H-02 down, T04-04 to 0 to +2, T04F-02 = the prepared R15 C5 ContHistSplit (gate C5), T12B-01
= a port of our own fix (b0c3882b; owner item, 0 Elo, removes UB), T05D-01 = port (R7TtExclusive is not in the lock),
T05E-01 = port of our own v3 / v2 refresh caches. Cards written after the draft: T04N-01 negative extension of the TT
move when its score is at or below alpha (Ethereal OpenBench tests incl. LTC, card), T04N-02 null move only at expected
cut nodes (Halogen PR 808, STC + LTC in the PR body), T04N-03 RFP margin raised when a piece of the side to move is
threatened (one-liner), T05F-01 node-identical eval memo for the evaluations the TT never keeps (no source number; its
step 0 counter decides go / no-go). Uncarded but studied by four tracks (CRITIC2): "a fail-high TT cutoff needs a
deeper entry" (Caissa d39fcfb / 9d566cc, SF b280d2f STC +3.91, PlentyChess 373).

## 3. Cross-track facts this report uses
- Gate rate 430-502 games/h measured for every `*_vs_AL1*` gate (497 at Threads 2 / conc 4); the ~1,000 games/h in some
  cards is the older R7 J4 rate (Threads 1, conc 8). v2 identical-eval control: -20.9 +- 18.5 (post root fix, sanity
  only); the pre-fix -32.2 is stale.
- Gate route: DECIDED by the crew - [0,5] normalized Elo, alpha = beta = 0.05, pentanomial, cap 3,000, Threads=1,
  capped = UNPROVEN / no decision with one extension when positive. By T12-01's model [0,5] nElo rarely decides a
  +1 to +3 Elo effect within 3,000 games (+ one extension), so most cards here will end UNPROVEN: expected, not a
  failure of the idea. Every card's "UHO SPRT [0,5]" route is read with this decision.
- T5: v2p4 at 0.85-0.89x = build ~0.98 x KB4 table + refreshes ~0.95 x finer layout (KB8 0.988, KB32 0.942) x an
  unmeasured ~0.97 (`notes/T05/V2P4_GAP.md`); int8 / VNNI / find-nnz apply to the HalfKA path only; Zen 5 VPDPBUSD zmm
  latency 3 / 0.5 c, VPCOMPRESSD store 8 uops (Zen 4: 144). BOLT on MSYS2 / Windows: **no** (ELF only, bolt/README.md).
- Data: the training set is the self-play J1 binpack only; the w4 runs used lambda 1.0 (run log) against the decided
  0.7-0.9; the npt HalfKA nets run at 0.47-0.58x the OFF nps, which can explain much of their -86 to -116 Elo.
  Self-play still runs the 6.2.0 HCE build: MIX.md's first step is the lock as the teacher.

## 4. Ideas already in Forge (found by the tracks; details in the TABLEs and DIFFs)
Probcut never in check; history kept across moves; losing captures last; TT move kept in a non-overwritten entry;
qsearch TT 50-move guard; negative extensions (-2 / -1) and IIR (variants prepared); best-move stability and
per-iteration falling-eval TM, soft / hard tunables, node-effort TM; history gravity on the main history; per-worker
refresh caches on the v2 and v3 paths (not on HalfKA); E3 options EvalMatScale / EvalOptimism / EvalRule50Damp /
DrawJitter; packb FiftyDamp and ReSearchAdjust (bundled tries); CorrUpdateMode (gravity-style correction update, gates
63 / 68); self-play rows already drop in-check, capture / promotion best moves, mate and bound scores, |cp| > 3000.

## 5. Dead ends (one line each; the hand-backs and TABLE verdicts hold the rest)
Merged king planes (neutral) | wider L1 (fixed-node gain vanishes at real TC) | distillation without a stronger teacher
| from-scratch threat nets (110G positions vs our 305M) | same-engine deeper relabel: no source with Elo | complexity-
and eval-level TM (both removed later by the source) | asymmetric optimism | draw jitter under +1 at 10+0.1 | null
moves not advancing rule50 | int16 accumulators (bound 342,331 > 32,767) | int8 first layer (15-bit weights) | BOLT
on PE | shared correction tables (only if gates stay Threads=1) | fail-firm RFP (gate 86) | EvalOptimism=40 (rerun H0).

## 6. Owner items
1. DECIDED by the crew (7-0): every search gate runs Threads=1; SPRT [0,5] in normalized Elo (not BayesElo), alpha = beta = 0.05, pentanomial, cap 3,000 games; a run that hits the cap without a decision is logged UNPROVEN / no decision (not H0, not a pass), and if its Elo is positive it gets exactly one extension.
2. EvalOptimism=40 rerun H0 (-5.30 +- 7.20, 2,360 g): the optimism line looks closed.
3. Viridithas v20.0.0 is MIT at its tag 0631113e22 (source readable there); Integral's MIT-carded dataset holds no files.
4. lambda 1.0 in the w4 runs vs the decided 0.7-0.9; where the Lichess rows are; Syzygy files on grok-pc?
5. Correctness: `bad_captures_` (64 entries, search.cpp:361) fills without a bound check - our own fix exists
   (b0c3882b, T12B-01; a crafted 68-capture fixture aborts the mutant); port it with the sanitizer fixture suite T12B-02.
6. `C:\o13` was restructured outside this job between ~22:50 and 23:00 (STATUS observations).
7. tmfit gates 227 / 228 are not in FORGE_RESULTS.csv (stale pointer in the brief).

## 7. Skills, scripts and tools created or improved
- Skill `skills/forge-deep-research/SKILL.md` (new; also installed as a user-scope skill on grok-pc): setup, tools,
  worker rules, the per-track and pooled workflows, verification, checkpoints, the low-usage stop, measured costs,
  lessons (one pooled workflow; refill before the queue empties; never resume a pool).
- Skill `skills/forge-pc-rules/SKILL.md` (branch copy with this job's section; the D: project copy untouched).
- `opus_deepres/tools/`: `mine_commits.py`, `licence_at.py` (GPL / AGPL title, LLVM Apache, CC0 fixes), `forge_has.sh`,
  `card_lint.py` (merge markers accepted), `tried_gates.py`, `block_rule_check.py`, `merge_licences.py` (cached),
  `workflow_prompts.py`, `handbacks.py`, `novendor_filter.py` (git clean filter); workflows in `tools/workflows/`
  (`deepres_tracks.js`, `deepres_phase2_checks.js`, `deepres_round2_tracks.js`, `deepres_pool.js`) with the exact
  worker prompts of round 1.

## 8. Incomplete work, deviations, spend
- Not done: sub-tracks T04I-T04M (LMR inputs, extensions, null move, futility, qsearch) DROPPED at 01:35 as overlapping
  the per-engine mining (owner: no two agents on the same thing); T04O (more permissive engines) dropped for usage; the
  T05F verifier still running; the "deeper entry for a fail-high TT cutoff" card; every PENDING item in the cards.
- Deviations: workflows stopped and relaunched five times (22:47 re-plan; 00:20 into one pool; 01:24-01:29 two pool
  resumes that re-ran finished agents for ~2 min each before being stopped; 01:35 usage warning); four first-round
  workers put temp files into this session's scratchpad on C: (left in place); a dataset name equal to a model name
  was pushed once in 8131d711 (filtered since); several times were first written as estimates and corrected from the
  clock or file stamps; the first licence tool misread GPL-3.0 and LLVM texts (fixed, table re-run).
- Measured agent spend (workflow summaries): round-1 core 1,802,872 tokens (8 agents), extra 1,149,308 (6), phase 2
  541,874 (2); the stopped runs report no total. Owner's readings: "running out" before 01:35; 77 % of the 5-hour window
  used at ~02:26, reset ~03:40.

INTERIM 2 finished 02:29 PC clock (from `date`).

# Forge deep research - FINAL REPORT

**State: INTERIM 3** - written from 04:57 PC clock on 2026-11-05 (finish time in the last line). Rounds 1-2 and most
of round 3 (after the usage reset, from 03:42) are researched, verified and ranked; still running at this writing: the
T04R verifier, FIXER3 (card fixes), the speed specs + their review, the spec fixes + a third second vote. The state
line will say FINAL, STOPPED - TIME LIMIT or STOPPED EARLY - LOW USAGE at the end.

Started 2026-11-04 22:23:27 PC clock; deadline 2026-11-05 08:23:27. Branch `opus-deepres-20261104`. No Elo claim for
Forge anywhere: every source number is quoted with its link and conditions in the card; every Forge-side estimate is
labelled UNPROVEN; the crew gates. Cards `cards/T<nn>[X]/`; per-track tables, diffs, notes and the verifiers' findings
`notes/T<nn>[X]/` (`TABLE.md`, `DIFF.md`, `VERIFY.md`); the full ranked table `notes/RANKING_FINAL.md` (supersedes
`notes/RANKING_DRAFT.md`); cross-track checks `notes/CRITIC.md`, `notes/CRITIC2.md`, CRITIC3 at the end of
RANKING_FINAL; second votes `notes/TOP_SECOND_VOTE.md`, `notes/TOP_SECOND_VOTE2.md`; counter-evidence
`notes/T12C/COUNTER.md`; implementation specs `notes/SPEC_SEARCH.md`, `SPEC_SEARCH2.md`, `SPEC_SEARCH3.md`,
`SPEC_EVAL.md` (+ `SPEC_REVIEW.md`); fixes `notes/FIXES_APPLIED.md`; licences at the commits read `LICENCES.md`.

## 0. First: the data blocker (T2-card-1, card T02-01, COMPLETE, verified)
The J1 npt train binpack is written from FPOS rows (no castling, no en passant, no clocks), so the net sees board + side
to move only: that is the leak key, and it subsumes the 4,088 EP-normalised keys. Drop the 7,700 train rows already
listed (path + line) in `D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv` (0.0025 % of 304,999,573; the minimum for "4,088 -> 0" is
4,118), rebuild the 37 train shards with the same converter, prove count / dropped keys / 0 shared keys on all three
keys / seals. Game level: no authentic game IDs exist; a cheap block rule (new block when the result changes or the ply
does not increase) gives the R14 scan's break total within 16 of 189k pairs (per class 25 and 41 apart) and shows both
train/holdout seams are breaks, so the 013/014 split is block-aligned. Under 30 CPU-minutes on one core (measured
logs), 10.4 GB on C:, crew ~2 h. Direct Elo: none expected (enabler for every net card).

## 1. Top 10 by expected Elo per crew-hour (lock-direct class), after the final ranking and the counter-evidence
Metric (brief): midpoint of the card's UNPROVEN range / the card's crew hours. Ranges after `notes/T12C/COUNTER.md`
(failed / neutral / reverted tests of the same ideas elsewhere). Crew hours are small for every row; gate-PC hours
(6-7 h per capped run, section 2) are the real cost and are the same for every row.

| # | card(s) | idea | best source evidence (all conditions + links in the card) | Forge est. UNPROVEN | crew h | per crew-h | ready |
|---|---|---|---|---|---|---|---|
| 1 | T06-05 | rule-50 damping at the fitted strength | SF 7b06475 STC +4.15 / LTC +2.94; own UE3C D=30 +1.51 (3,000 g, capped); own holdout fit favours D=81 | 0 to +3 | 0.5 | 3.0 | E3 exe, `EvalRule50Damp=60` (~81 needs a range-extended build) |
| 2 | T04P-01 | fail-high TT cutoff needs a one-ply-deeper entry (form B: only for scores within a margin above beta) | Caissa 9d566cc form B vs form A +1.35 +- 1.06 (112,192 g); Caissa d39fcfb form A +2.11 +- 1.55 (48,018 g, 40+0.4 only); PlentyChess 373 STC H0 / LTC +1.73 | 0 to +2 (form B) | 0.5 | 2.0 | own port caissa_c123 built and CR-passed, never gated: `TtCutExtraMargin=72` |
| 3 | T04-01 | singular verification search as a non-cut node | Caissa 1b7a871 STC +4.20 +- 2.23 (25,044 g); no counter-evidence found | 0 to +3 | 1 | 1.5 | spec (SPEC_SEARCH) |
| 4 | T04E-02 (+ T04N-02 stacked) | no null move when the hash move captures a valuable piece | Reckless STC +3.43 / LTC +3.67; Viridithas LTC +1.88 +- 1.48 (49,814 g) | +1 to +3 | 1.5 | 1.33 | spec (SPEC_SEARCH2) + review code fix |
| 5 | T04F-01 | qsearch in check: stop after the first evasion that is not mated | Caissa a677c89 +3.29 +- 2.6 (25,531 g, TC not stated); Stockfish chose a milder form | +1 to +3, low end | 1.5 | 1.33 | spec (SPEC_SEARCH3); after the P27R extension |
| 6 | T04-02 | LMR re-search deeper / shallower after a reduced fail-high | Caissa 434bbda STC +6.93 / LTC +5.14; Patricia PR 137 +5.55; Stockfish reverted an extra-deep variant twice (search explosions) | +1 to +4 | 2 | 1.25 | spec (SPEC_EVAL), own constants, ply guard mandatory |
| 7 | T04E-03 (+ C-04, D-03, G-03) | quiet-move malus that shrinks with the try index | four engines at both TCs (SF a016abd STC +3.78 / LTC +2.18; Berserk 7451fd7; Reckless 1038; Patricia 172 LTC) | +1 to +3 | 2 | 1.0 | spec (SPEC_SEARCH2); first gate = base of every history stack |
| 8 | T04C-02 | lower singular beta at former-PV (ttpv) nodes | SF 1591e5a LTC +1.04 +- 0.64 (235,592 g); SF 4e89864 LTC +1.83; the 2020 form was simplified away first | ~+1 within 0 to +3 | 1 | 1.0 | spec (SPEC_SEARCH3); after T04N-01 on the singular chain |
| 9 | T04D-02 | low-depth TT cutoff only when its direction matches the node type | SF 43e100a STC +2.72 / LTC +1.02 +- 0.62 (270,888 g); its depth part simplified later | 0 to +2 | 1 | 1.0 | spec (SPEC_SEARCH2), form 1 first |
| 10 | T04N-01 | negative extension of the TT move when its score is at or below alpha | Ethereal f71ac47 STC +4.66 / LTC +2.44 (57,696 g); akimbo 3e29e57 STC +2.29 (MIT); Caissa bundle | +0.5 to +2 | 1.5 | 0.83 | spec (SPEC_SEARCH3); first on the singular chain |

Moved down by the counter-evidence: T04D-01 (0 to +1.5: Stockfish simplified the term away and re-added it at about
+1; 0.75 per crew-h) and the T04B-01 family (+0.5 to +2.5: Stockfish's 2024 retry +1.08 LTC at 244k games; the
Stormphrax +6.48 LTC is a 10k-game DFRC run; 0.75). Close behind: T12-04 (SPSA of 20 live constants, 1.25 per crew-h
but 33-67 h of tuning games), T04E-01, T04G-05, T04-05, T04C-05, T04D-05, T04H-03 (each ~1.0), new T04R-01 (best-move
history bonus scaled by its child fail-highs; Renegade +3.35 +- 2.29 at 10+0.1, MIT; 0 to +3, ~2 h; verifier running).
Not new: #1 and #6 exist in our own packb code (FiftyDamp, ReSearchAdjust), gated only as one bundle with copied
constants on old bases (gates 12 / 35 / 40 / 41, no decision); #2 exists as an own port that was never gated.

## 2. What the crew's gate decision means for these cards (arithmetic, not a proposal)
Threads=1, SPRT [0,5] normalized Elo, alpha = beta = 0.05, pentanomial, cap 3,000 games, capped = UNPROVEN with one
extension if positive (crew 7-0). At 3,000 games the 95 % half-width is about +-5.9 Elo (UHO, pentanomial), and
[0,5] nElo is about [0, 2.4] Elo at the crew's draw rate. In a Gaussian approximation the LLR reaches +2.94 at the cap
only if the running estimate is near +12 Elo (near -10 Elo for H0), so a true +2.5 single almost never decides: every
single in section 1 will most likely log UNPROVEN at the cap. The capped run is then a point-estimate screen (+-5.9)
whose sign decides the one extension, and only stacks worth roughly +10 Elo can decide inside the cap - which is why
the gate plan ends in stacks by site group. Cost: 6-7 gate-PC hours per capped run at the measured 430-502 games/h
(measured at Threads 2 / conc 4; no Threads=1 rate exists in any input).

## 3. Round 3 (after the usage reset, 03:42 on): what is new
- **T04P-01** (verified 04:07): the deeper-entry rule CRITIC2 found uncarded. Forge already has form B as its own
  port (`forge_push/qa_ltopgo_al1_stage/cands/caissa_c123`, option `TtCutExtraMargin` 0-200, LTO+PGO exe
  `forge_push/bin/forge_ltopgo_x_caissa_c123_al1_8924099a.exe`, OFF = lock pins, CR-passed 2026-10-30, never gated):
  a 0.5-1 crew-hour gate item. Evidence is thinner than CRITIC2 said: Stockfish b280d2f (+3.91 STC) measured the
  fail-LOW relaxation the lock already has; PlentyChess 373 failed its STC; form B vs the lock's rule was never
  measured anywhere. The port needs its MIT notice before any merge.
- **T04Q lock audit** (verified 04:17): the lock's search code against the 25-pattern pre-gate checklist plus nine
  classic spots. No bug worth >= 1 Elo: 3 minor hits (a TT mate score is not checked against the 50-move clock, < 1
  Elo; quiet promotions only ever get the capture-history malus, < 1 Elo; quiet futility's skip switch also drops later
  quiet checks = T04E-01 bit 2, already carded). No card.
- **T04O** (permissive engines, verified 04:36): no new card; evidence rows: akimbo 7120b4b isolates king-bucket
  mirroring on a 768-input one-bucket net (the lock net's shape; so T01B-02's "no source isolates mirroring" is
  wrong), akimbo 3e29e57 is a third engine for T04N-01.
- **T04R** (engines never read: Renegade MIT; Clover and Simbelmyne GPL-3.0, logs only): T04R-01 (full card, above),
  one-liners T04R-02 (pawn-structure refutation move) and T04R-03 (full history update when alpha was raised without a
  cutoff); Fable verifier running.
- **Counter-evidence** (`notes/T12C/COUNTER.md`): lowers T04-02, T04D-01, T04D-02, T04C-02, T04B-01 (section 1);
  keeps T06-05, T04-01, T04E-02, T04F-01 (low end), T04E-03.
- **Second vote 2** (Fable, round-2 top cards): KEEP T04D-01, T04F-01, T04B-01, T04E-04, T04E-03; KEEP-WITH-FIX
  T04D-02, T04C-02, T04E-02, T04N-01; DOWNGRADE T04N-02 (one-liner, stacked only).
- **Specs**: 18 options are now specified in own words against the lock (SPEC_SEARCH: T04-01/03/04/05/06; SPEC_EVAL:
  T04-02, T06-05, T06-04; SPEC_SEARCH2: E-03, E-02, B-01, D-01, D-02; SPEC_SEARCH3: C-02, F-01, N-01, N-02, P-01). The
  Fable review of the ten new ones (`notes/SPEC_REVIEW.md`): no blocker, every OFF path node-identical; one code fix
  (T04E-02 must validate the TT move with the lock's own pseudo-legality test, search.cpp:325, before reading its
  victim or calling see_ge) and three wording fixes. Speed specs (`notes/SPEC_SPEED.md`) running.
- **Fixes**: round 3 (FIXER2: CRITIC2's card items) done; round 4 (FIXER3: second-vote-2 items, wrong "Forge lacks it"
  lines, counter-evidence lines on the cards) running.

## 4. Gate plan (RANKING_FINAL's phases, adjusted by the counter-evidence)
- Phase 0, no crew code (4 runs, 24-28 h of gate PC): (a) the P27R-AL1 `QsEvasionSeeNonPv=1` extension (its capped
  +4.63 is positive, so the crew rule itself owes one extension; T04F-01 waits on it); (b) E3 exe `EvalRule50Damp=60`
  (T06-05); (c) caissa_c123 `TtCutExtraMargin=72` (T04P-01); (d) R15 C5 ContHistSplit (T04F-02 folded into it).
- Phase 1, one kit -Expose build carrying the five SPEC_SEARCH2 options (one OFF pin proof, one ON-live bench per
  option): T04E-03 `QuietMalusDecay` first (base of every history stack), T04E-02 `NmpTtCaptureMin` (with the review's
  pseudo-legality fix), T04B-01 `NoisySeeHistDiv`, T04D-02 `TtCutNodeDepth` form 1, T04D-01 `CutNoTtLmr` last.
- Phase 2, singles that need new code: T04-02 alone with own constants and the ply guard; T04-01; T04N-01 then T04C-02
  (singular chain); T04F-01 after (a); T04E-04 bit 2; T04R-01 after its verify; T04-06 at LTC; T04H-01 last of the ttpv
  cards; everything else only as gate PC allows.
- Phase 3, stacks of the positives by site group: history (E-03 base), null move (E-02 + N-02 + T04-03), singular
  chain (N-01 + T04-01 + C-02), TT cutoff (D-02 + P-01), SEE (B-01 + E-04).
- Beside the gate PC: node-identical lock speed by nps ABBA after the T12-03 bench + fuzz proof (T05D-01 = port of the
  own R7TtExclusive, +3.6-4 % on another tree, NOT in the lock; T05C-02; T05C-03; T05B-02; specs in SPEC_SPEED); GPU
  window: T02-01 first, the T02-04 equal-node WAC diagnostic, then T02-03, T01-06; owner item T12B-01 (port own fix).
- Budget: phases 0 + 1 = 9 runs = 54-63 h of gate PC; all 43 lock-direct singles = 260-300 h at the cap.

## 5. All cards ranked
`notes/RANKING_FINAL.md` (Fable, 04:36-04:51): one row per idea family, 81 rows in five classes (L lock-direct SPRT 44,
G GPU-conditional 11, V net-line speed ABBA 8, S lock speed ABBA 9, E enabler / diagnostic 9; % nps and Elo never
converted into each other), each with source number, UNPROVEN estimate, crew hours, gate route, per-hour value and vote
state; then the top 10, the phased gate order and CRITIC3 (13 items). Cards written after it: T04R-01..03.

## 6. Cross-track facts this report uses
- Gate rate 430-502 games/h measured for every `*_vs_AL1*` gate (497 at Threads 2 / conc 4); the ~1,000 games/h in some
  cards is the older R7 J4 rate (Threads 1, conc 8). v2 identical-eval control: -20.9 +- 18.5 (post root fix, sanity
  only); the pre-fix -32.2 is stale.
- T5: v2p4 at 0.85-0.89x = build ~0.98 x KB4 table + refreshes ~0.95 x finer layout (KB8 0.988, KB32 0.942) x an
  unmeasured ~0.97 (`notes/T05/V2P4_GAP.md`); int8 / VNNI / find-nnz apply to the HalfKA path only; Zen 5 VPDPBUSD zmm
  latency 3 / 0.5 c, VPCOMPRESSD store 8 uops (Zen 4: 144). BOLT on MSYS2 / Windows: **no** (ELF only, bolt/README.md).
- Data: the training set is the self-play J1 binpack only; the w4 runs used lambda 1.0 (run log) against the decided
  0.7-0.9; the npt HalfKA nets run at 0.47-0.58x the OFF nps, which can explain much of their -86 to -116 Elo.
  Self-play still runs the 6.2.0 HCE build: MIX.md's first step is the lock as the teacher.

## 7. Ideas already in Forge (found by the tracks; details in the TABLEs and DIFFs)
Probcut never in check; history kept across moves; losing captures last; TT move kept in a non-overwritten entry;
qsearch TT 50-move guard; negative extensions (-2 / -1) and IIR (variants prepared); best-move stability and
per-iteration falling-eval TM, soft / hard tunables, node-effort TM; history gravity on the main history; per-worker
refresh caches on the v2 and v3 paths (not on HalfKA); E3 options EvalMatScale / EvalOptimism / EvalRule50Damp /
DrawJitter; packb FiftyDamp and ReSearchAdjust (bundled tries); CorrUpdateMode (gravity-style correction update, gates
63 / 68); the deeper-entry TT cutoff as form B (own caissa_c123 port, never gated); NMP non-pawn-material condition,
lazy accumulators, TT prefetch, correction history (T04O re-greps); self-play rows already drop in-check, capture /
promotion best moves, mate and bound scores, |cp| > 3000.

## 8. Dead ends (one line each; the hand-backs and TABLE verdicts hold the rest)
Merged king planes (neutral) | wider L1 (fixed-node gain vanishes at real TC) | distillation without a stronger teacher
| from-scratch threat nets (110G positions vs our 305M) | same-engine deeper relabel: no source with Elo | complexity-
and eval-level TM (both removed later by the source) | asymmetric optimism | draw jitter under +1 at 10+0.1 | null
moves not advancing rule50 | int16 accumulators (bound 342,331 > 32,767) | int8 first layer (15-bit weights) | BOLT
on PE | shared correction tables (only if gates stay Threads=1) | fail-firm RFP (gate 86) | EvalOptimism=40 (rerun H0)
| a lock bug worth >= 1 Elo (T04Q audit: none found) | more permissive engines (T04O: two sources in a row without a
card) | Stockfish b280d2f as evidence for the fail-high deeper-entry rule (it measured the fail-low side).

## 9. Owner items
1. DECIDED by the crew (7-0): every search gate runs Threads=1; SPRT [0,5] in normalized Elo (not BayesElo), alpha = beta = 0.05, pentanomial, cap 3,000 games; a run that hits the cap without a decision is logged UNPROVEN / no decision (not H0, not a pass), and if its Elo is positive it gets exactly one extension. Consequence in section 2.
2. No Threads=1 gate rate exists in any input (the 430-502 games/h are Threads 2 / conc 4), and the crew's LTC time
   control is written nowhere (inputs assume 3x to 6x the STC cost per game).
3. The P27R-AL1 `QsEvasionSeeNonPv=1` run ended capped at +4.63 (3,000 g): one extension is owed under item 1.
4. The caissa_c123 port (T04P-01) and every MIT-derived change need the MIT notice line before a merge.
5. EvalOptimism=40 rerun H0 (-5.30 +- 7.20, 2,360 g): the optimism line looks closed.
6. Viridithas v20.0.0 is MIT at its tag 0631113e22 (source readable there); Integral's MIT-carded dataset holds no files.
7. lambda 1.0 in the w4 runs vs the decided 0.7-0.9; where the Lichess rows are; Syzygy files on grok-pc?
8. Correctness: `bad_captures_` (64 entries, search.cpp:361) fills without a bound check - our own fix exists
   (b0c3882b, T12B-01; a crafted 68-capture fixture aborts the mutant); port it with the sanitizer fixture suite T12B-02.
9. `C:\o13` was restructured outside this job between ~22:50 and 23:00 (STATUS observations).
10. tmfit gates 227 / 228 are not in FORGE_RESULTS.csv (stale pointer in the brief).
11. T04O left five permissive repos unread (it stopped after two sources in a row without a card, the caps rule).

## 10. Skills, scripts and tools created or improved
- Skill `skills/forge-deep-research/SKILL.md` (new; also installed as a user-scope skill on grok-pc): setup, tools,
  worker rules, the per-track and pooled workflows, verification, checkpoints, the low-usage stop, measured costs,
  lessons (one pooled workflow; refill before the queue empties; never resume a pool).
- Skill `skills/forge-pc-rules/SKILL.md` (branch copy with this job's section; the D: project copy untouched).
- `opus_deepres/tools/`: `mine_commits.py`, `licence_at.py` (GPL / AGPL title, LLVM Apache, CC0 fixes), `forge_has.sh`,
  `card_lint.py` (merge markers accepted), `tried_gates.py`, `block_rule_check.py`, `merge_licences.py` (cached),
  `workflow_prompts.py`, `handbacks.py`, `novendor_filter.py` (git clean filter), `board.py` (crew worker board: claim
  a slot, take another idle one when the named one is busy, wait / refuse when all 3 are busy, release by worker +
  task, done line; tested on a copy); workflows in `tools/workflows/` (`deepres_tracks.js`, `deepres_phase2_checks.js`,
  `deepres_round2_tracks.js`, `deepres_pool.js`, `deepres_pool3.js` = the 3-worker pool with task dependencies,
  latest-start times, a Fable verifier after each research task and a cooperative wrap-up note).

## 11. Incomplete work, deviations, spend
- Not done: sub-tracks T04I-T04M (LMR inputs, extensions, null move, futility, qsearch) DROPPED at 01:35 as overlapping
  the per-engine mining (owner: no two agents on the same thing); every PENDING item in the cards; at this writing
  the round-3 items listed in the state line.
- Deviations: workflows stopped and relaunched five times before 01:35 (22:47 re-plan; 00:20 into one pool; 01:24-01:29
  two pool resumes that re-ran finished agents for ~2 min each before being stopped; 01:35 usage warning); after the
  reset four 1-worker runs were started next to POOL3 to use slots it left idle (total never above 3; the owner's hook
  refused one launch while a finished worker was still inside its 3-minute window); the `opus-max` agent type is not in
  this session's agent registry, so those tasks ran as Opus 5.5 at effort max (5 refused spawns logged as "failed", no
  agent started); four first-round workers put temp files into this session's scratchpad on C: (left in place); a
  dataset name equal to a model name was pushed once in 8131d711 (filtered since); several times were first written as
  estimates and corrected from the clock (also 04:24 -> 04:22 and 04:26 -> 04:25 in STATUS); the first licence tool
  misread GPL-3.0 and LLVM texts (fixed, table re-run).
- Measured agent spend (workflow summaries): round-1 core 1,802,872 tokens (8 agents), extra 1,149,308 (6), phase 2
  541,874 (2), light pool 1,667,660 (10), POOL3 1,690,105 (10), POOL3C 334,288 (2); the stopped runs report no total;
  POOL3B / POOL3D / the last run at the end. Owner's readings: "running out" before 01:35; 77 % of the 5-hour window
  used at ~02:26, reset ~03:40; no reading since.

INTERIM 3 finished 04:57 PC clock (from `date`).

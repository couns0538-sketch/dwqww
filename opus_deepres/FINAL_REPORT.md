# Forge deep research - FINAL REPORT

**State: FINAL** - written from 06:09 PC clock on 2026-11-05 (finish time in the last line). All tracks of the
brief's core set and the after-report set (T6, T7, T12) are researched and verified; round 3 (after the usage reset,
from 03:42) added new engines, a lock audit, counter-evidence, three second votes, 22 implementation specs with
reviews, a final ranking and a critic of this report (`notes/CRITIC4.md`, applied). T04U (06:06-06:24) added T04U-01; T06E and SPECFIX2 (06:24-06:41) closed the T06D pending list (T06E-01, T06E-02) and
applied the speed-spec review; T01C and T02C (06:42-07:04) answered two of the three brief questions CRITIC.md had
marked NOT COVERED (section 11). A last 2-worker run (07:05 on: T06F more HCE terms, T02D data filters with passed net
tests) adds its results at the end of section 3.

Started 2026-11-04 22:23:27 PC clock; deadline 2026-11-05 08:23:27. Branch `opus-deepres-20261104`. No Elo claim for
Forge anywhere: every source number is quoted with its link and conditions in the card; every Forge-side estimate is
labelled UNPROVEN; the crew gates. Cards `cards/T<nn>[X]/` (107 card files incl. one-liners and merge markers);
per-track tables, diffs, notes and the verifiers' findings `notes/T<nn>[X]/` (`TABLE.md`, `DIFF.md`, `VERIFY.md`);
the full ranked table `notes/RANKING_FINAL.md` (supersedes `notes/RANKING_DRAFT.md`); cross-track checks
`notes/CRITIC.md` (coverage matrix of the brief), `notes/CRITIC2.md`, CRITIC3 at the end of RANKING_FINAL,
`notes/CRITIC4.md` (this report); second votes `notes/TOP_SECOND_VOTE.md`, `..._VOTE2.md`, `..._VOTE3.md`;
counter-evidence `notes/T12C/COUNTER.md`; specs `notes/SPEC_SEARCH.md`, `SPEC_SEARCH2.md`, `SPEC_SEARCH3.md`,
`SPEC_EVAL.md`, `SPEC_SPEED.md` (reviews `SPEC_REVIEW.md`, `SPEC_SPEED_REVIEW.md`); fixes `notes/FIXES_APPLIED.md`
(rounds 1-7); licences at the commits read `LICENCES.md`. Section 12 maps every brief deliverable to its file.

## 0. First: the data blocker (T2-card-1, card T02-01, COMPLETE, verified)
The J1 npt train binpack is written from FPOS rows (no castling, no en passant, no clocks), so the net sees board + side
to move only: that is the leak key, and it subsumes the 4,088 EP-normalised keys. Drop the 7,700 train rows already
listed (path + line) in `D:\a14\sep\BOARDSTM_TRIAGE_ROWS.tsv` (0.0025 % of 304,999,573; the minimum for "4,088 -> 0" is
4,118), rebuild the 37 train files (39 shards incl. the 013 / 014 holdout) with the same converter, prove count /
dropped keys / 0 shared keys on all three keys / seals. Game level: no authentic game IDs exist; a cheap block rule (new
block when the result changes or the ply does not increase) gives the R14 scan's break total within 16 of 189k pairs
(per class 25 and 41 apart) and shows both train/holdout seams are breaks, so the 013/014 split is block-aligned. Under
30 CPU-minutes on one core (measured logs), 10.4 GB on C:, crew ~2 h. Direct Elo: none expected (enabler for every net
card).

## 1. Top 10 by expected Elo per crew-hour (lock-direct class)
Rule: the midpoint of the card's UNPROVEN range after the counter-evidence (`notes/T12C/COUNTER.md`), or COUNTER's
expected value where it states one (T04C-02: about +1), divided by the card's crew hours; ties by the larger midpoint,
then by the broader evidence (more engines, both TCs). Crew hours are small for every row; gate-PC hours (6-7 h per
capped run, section 2) are the real cost and the same for every row, except T12-04's tuning games.

| # | card(s) | idea | best source evidence (all conditions + links in the card) | Forge est. UNPROVEN | crew h | per crew-h | ready |
|---|---|---|---|---|---|---|---|
| 1 | T06-05 | rule-50 damping at the fitted strength | SF 7b06475 STC ~+4.2 / LTC ~+2.9; own UE3C D=30 +1.51 (3,000 g, capped); own holdout fit favours D=81 | 0 to +3 | 0.5 | 3.0 | E3 exe, `EvalRule50Damp=60` (~81 needs a range-extended build) |
| 2 | T04P-01 | fail-high TT cutoff needs a one-ply-deeper entry (form B: only for scores within a margin above beta) | Caissa 9d566cc form B vs form A +1.35 +- 1.06 (112,192 g); Caissa d39fcfb form A +2.11 +- 1.55 (48,018 g, 40+0.4 only); PlentyChess 373 STC H0 / LTC +1.73 | 0 to +2 (form B) | 0.5 | 2.0 | own port caissa_c123 built and CR-passed, never gated: `TtCutExtraMargin=72` |
| 3 | T04-01 | singular verification search as a non-cut node | Caissa 1b7a871 STC +4.20 +- 2.23 (25,044 g); no counter-evidence found | 0 to +3 | 1 | 1.5 | spec (SPEC_SEARCH) |
| 4 | T04E-02 (+ T04N-02 stacked) | no null move when the hash move captures a valuable piece | Reckless STC +3.43 / LTC +3.67 (early stop); Viridithas LTC +1.88 +- 1.48 (49,814 g) | +1 to +3 | 1.5 | 1.33 | spec (SPEC_SEARCH2, with the review's pseudo-legality fix) |
| 5 | T04F-01 | qsearch in check: stop after the first evasion that is not mated | Caissa a677c89 +3.29 +- 2.6 (25,531 g, TC not stated); Stockfish chose a milder form | +1 to +3, low end | 1.5 | 1.33 | spec (SPEC_SEARCH3); after the P27R extension |
| 6 | T04-02 | LMR re-search deeper / shallower after a reduced fail-high | Caissa 434bbda STC +6.93 / LTC +5.14; Patricia PR 137 +5.55; Stockfish reverted an extra-deep variant twice (search explosions) | +1 to +4 | 2 | 1.25 | spec (SPEC_EVAL), own constants, ply guard mandatory |
| 7 | T12-04 | SPSA of 20 live, steep search constants, one tuned-set SPRT | SF 5c617e5 VVLTC tune ~+5.2 (15,788 g) / ~+6.4 (13,622 g); own R9: the lock sat near a local optimum at 8+0.08 | 0 to +5 | 2 + 33-67 h of tuning games | 1.25 | card; own SPSA tooling exists (R9 / 30-h job) |
| 8 | T04S-01 | continuation-history update with the summed continuation score as the gravity base | Tarnished #132 STC +2.23 +- 1.70 / LTC +2.53 +- 1.85 (39,808 / 32,122 g); Sirius #328 STC +5.86 / LTC +14.38 (HCE engine, blend form at STC); Clockwork #234 STC +14.67 | +1 to +4 | 2.5 | 1.0 | card (`ContHistSumBase`, own start 60, sweep incl. 100) |
| 9 | T04E-01 | LMP keeps quiet checking moves | Reckless 5e5443d STC +2.84 +- 2.04 (28,536 g) / LTC +9.46 +- 4.06 (6,500 g), both early stop, UHO | +1 to +4 | 2.5 | 1.0 | card; alone on search.cpp:1062 (C-05 uses the same switch) |
| 10 | T04E-03 (+ C-04, D-03, G-03) | quiet-move malus that shrinks with the try index | four engines at both TCs (SF a016abd STC +3.78 / LTC +2.18; Berserk 7451fd7; Reckless 1038; Patricia 172 LTC) | +1 to +3 | 2 | 1.0 | spec (SPEC_SEARCH2); first gate of the history group |

Next, at 1.0 per crew-h with smaller midpoints: T04G-05 (history update one ply deeper when the score reached the
eval), T04C-02 (lower singular beta at former-PV nodes; Stockfish's 2020 form was simplified away and re-added at LTC
+1.04 at 236k games), T04D-02 (low-depth TT cutoff by node type; top lowered to +2), T04T-02 (ProbCut fail-firm;
pawnocchio LTC +2.92, Reckless STC +2.37 / LTC +3.35), T04-05, T04C-05, T04D-05, T04H-03. Then T04N-01 (0.83),
T04R-01, T04U-01, T04D-01, the T04B-01 family (0.75 each; D-01 and B-01 lowered by the counter-evidence), T04T-01 (0.67),
T06D-01 (king flank attacks, 0.4), T04S-02 (upcoming repetition, 0.33), T06E-02 (blocked pawn storm, 0.25), T06D-03 (endgame
winnability, 0.2), T06E-01 (queen threats of the next move, 0.2). Not new:
#1 and #6 exist in our own packb code (FiftyDamp, ReSearchAdjust), gated only as one bundle with copied constants on
old bases (gates 12 / 35 / 40 / 41, no decision); #2 is an own port never gated.

## 2. What the crew's gate decision means for these cards (arithmetic, not a proposal)
Threads=1, SPRT [0,5] normalized Elo, alpha = beta = 0.05, pentanomial, cap 3,000 games, capped = UNPROVEN with one
extension if positive (crew 7-0). At 3,000 games the 95 % half-width is about +-5.9 Elo (UHO, pentanomial; second
vote 2's figure, re-derived in CRITIC4), and [0,5] nElo is about [0, 2.4] Elo at the crew's draw rate. In a Gaussian
approximation (own arithmetic, reproduced by CRITIC4) the LLR reaches +2.94 at the cap only if the running estimate is
near +12.3 Elo (near -9.9 Elo for H0): a true +2.5 single decides with a probability near 0.05 %, so every single in
section 1 will most likely log UNPROVEN at the cap and the capped run acts as a point-estimate screen (+-5.9) whose sign
decides the one extension. Mean run lengths: about 6,900 games at a true +6, about 3,800 at +10, about 3,100 at +12
(CRITIC4), so a stack near +10 Elo decides inside the cap only about one time in three. Cost: 6-7 gate-PC hours per
capped run at the measured 430-502 games/h (measured at Threads 2 / conc 4; no Threads=1 rate exists in any input).
Cards written before the decision may still quote the old [0,10] / 12k-game cost (6.6k games, 13-15 h); read them with
this paragraph.

## 3. Round 3 (after the usage reset, 03:42 on): what is new
- **T04P-01** (verified, second vote KEEP): the deeper-entry rule CRITIC2 found uncarded. Forge already has form B as
  its own port (`forge_push/qa_ltopgo_al1_stage/cands/caissa_c123`, option `TtCutExtraMargin` 0-200, LTO+PGO exe
  `forge_push/bin/forge_ltopgo_x_caissa_c123_al1_8924099a.exe`, OFF = lock pins, CR-passed 2026-10-30, never gated):
  a 0.5-1 crew-hour gate item. Evidence is thinner than CRITIC2 said: Stockfish b280d2f (+3.91 STC) measured the
  fail-LOW relaxation the lock already has; PlentyChess 373 failed its STC; form B vs the lock's rule was never
  measured anywhere. The port needs its MIT notice before any merge.
- **T04Q lock audit** (verified): the lock's search against the 21-row pre-gate checklist (`notes/T04/BUG_CHECKLIST.md`)
  plus 12 extra spots (`notes/T04Q/AUDIT.md` B1-B12). No bug worth >= 1 Elo: 3 minor hits (a TT mate score is not
  checked against the 50-move clock, < 1 Elo; quiet promotions only ever get the capture-history malus, < 1 Elo; quiet
  futility's skip switch also drops later quiet checks = T04E-01 bit 2, already carded); two rows are NEEDS RUN (13,
  21), each with the box test that would decide it. No card.
- **New engines**: T04O (permissive engines; 0 cards; akimbo 7120b4b isolates king-bucket mirroring on a 768-input
  one-bucket net, now on T01B-02; akimbo 3e29e57 a third engine for T04N-01). T04R (Renegade MIT; Clover, Simbelmyne
  logs): T04R-01 + one-liners T04R-02 (pawn-structure refutation move) and T04R-03 (full history update when alpha was
  raised without a cutoff). T04S (logs only from Sirius, motor, Tarnished PR bodies, the engines T04O skipped for
  licence): T04S-01 (section 1, #8) and T04S-02 (upcoming repetition). T04T (Clockwork, pawnocchio PR bodies; Horsie
  and Seer gave only evidence rows; Carp and Willow have no tested commits since 2024): T04T-01 (in-check nodes skip
  the ply-4 continuation-history update; Clockwork #380 STC +5.33 / LTC +9.69, measured on top of the T04S-01 form, so
  transfer is uncertain), T04T-02 (ProbCut fail-firm), one-liner T04T-03 (double-extension margin moved by the TT
  move's quiet history, sign unknown). T04U (Clockwork #281, last unread PR pages): T04U-01 check extension moved
  into LMR (STC +5.82 / LTC +3.35, [0,5], UHO; ON in effect drops the extension outside LMR). All verified: 0 violations, 0 duplicates; one correction on T04S-01 (the
  Sirius STC run was a blend form; pure sum vs blend +3.23 at 29k games), in-line notes on T04T.
- **Hand-crafted eval terms (T06D, new angle: the lock is HCE + a residual net)**: T06D-01 king flank attacks and
  defences as new HCE rows (Sirius 267 STC +10.77, 7,290 g; Clockwork 387 STC +18.10, 4,266 g; HCE engines; 0 to +4,
  ~5 crew h with the fit), one-liner T06D-02 pin-aware HCE, T06D-03 endgame winnability term on the eg score (Clockwork
  364 STC +2.95 / LTC +7.04; 0 to +2, ~5 h). Each is fitted with the residual net frozen (T06C-01 recipe) and discounts
  what the residual may already capture. Verified: 3 confirmed, 1 correction. T06E closed the pending list: T06E-01
  queen threats of the next move (SF 6d8f583 STC +2.91 / LTC +2.30, SF 1093047 STC +3.73 / LTC +5.42, Sirius #271 STC
  +3.08; 0 to +2, ~5 h), one-liner T06E-02 blocked pawn storm (Sirius #185 STC +3.88; 0 to +1.5, ~3 h); Sirius #258
  (non-linear king safety) is evidence for T06C-03. Verified: no correction, no violation.
- **Counter-evidence** (`notes/T12C/COUNTER.md`): lowers T04-02, T04D-01, T04D-02, T04C-02, T04B-01 (now also on the
  cards as a "Counter-evidence (T12C)" sentence); keeps T06-05, T04-01, T04E-02, T04F-01 (low end), T04E-03.
- **Second votes 2 and 3** (Fable): round-2 top cards KEEP D-01, F-01, B-01, E-04, E-03; KEEP-WITH-FIX D-02, C-02, E-02,
  N-01; DOWNGRADE N-02 (now a one-liner, stacked only). Third vote: KEEP P-01, T05F-01; KEEP-WITH-FIX R-01, N-03, E-01,
  G-05 (all fixes applied, round 6).
- **Specs**: 22 cards specified in own words against the lock (about 30 UCI options plus 4 build switches):
  SPEC_SEARCH (T04-01/03/04/05/06), SPEC_EVAL (T04-02, T06-05, T06-04), SPEC_SEARCH2 (E-03 `QuietMalusDecay`, E-02
  `NmpTtCaptureMin`, B-01 `NoisySeeHistDiv`, D-01 `CutNoTtLmr`, D-02 `TtCutNodeDepth`), SPEC_SEARCH3 (C-02
  `SingularTtPvMargin`, F-01 `QsEvasionLimit`, N-01 `NegExtTtAlpha`, N-02 `NmpCutOnly`, P-01 `TtCutExtraMargin`),
  SPEC_SPEED (build switches `FORGE_NO_ZERO_MOVELISTS`, `FORGE_SLIDER_ATTACKS`, `FORGE_MATKEY_FAST`, `FORGE_TT_NOTLS`).
  Fable reviews: search specs no blocker, every OFF path node-identical, one code fix (E-02 validates the TT move with
  the lock's own pseudo-legality test, board.cpp:600 as used at search.cpp:326, before reading its victim or calling
  see_ge) and three wording fixes, all applied (round 5); speed specs no blocker, 10 FIX items on the ABBA budget and
  order, all applied (round 7; one softened: a true +0.75 % change passes the +1 % filter about 1 time in 4 to 6).
- **Fixes**: rounds 3-7 (`notes/FIXES_APPLIED.md`): CRITIC2's card items, second-vote fixes, wrong "Forge lacks it"
  lines (T04D-02 own port, T01B-02 mirroring source, T05E-01 own caches), counter-evidence sentences, crew-cap cost
  lines on 9 cards.

## 4. Gate plan (RANKING_FINAL's phases, adjusted by the counter-evidence and the third vote)
- Phase 0, no crew code (4 runs, 24-28 h of gate PC): (a) the P27R-AL1 `QsEvasionSeeNonPv=1` extension (its capped
  +4.63 is positive, so the crew rule itself owes one extension; T04F-01 waits on it); (b) E3 exe `EvalRule50Damp=60`
  (T06-05); (c) caissa_c123 `TtCutExtraMargin=72` (T04P-01; last of phase 0 if gate PC is short); (d) R15 C5
  ContHistSplit (T04F-02 folded into it).
- Phase 1, one kit -Expose build carrying the five SPEC_SEARCH2 options (~10.5 crew h incl. counters; one OFF pin
  proof, one ON-live bench per option): T04E-03 `QuietMalusDecay` first (base of every history stack), T04E-02
  `NmpTtCaptureMin`, T04B-01 `NoisySeeHistDiv`, T04D-02 `TtCutNodeDepth` form 1, T04D-01 `CutNoTtLmr` last.
- Phase 2, singles that need new code: T04-02 alone with own constants and the ply guard; T04-01; T04N-01 then T04C-02
  (singular chain); T04F-01 after (a); T04S-01 and T04R-01 in the history group after E-03 (each alone; never R-01 and
  G-05 in one run; T04T-01 alone and again on top of S-01 if S-01 passes); T04E-04 bit 2, then T04E-01; T04G-05;
  T04T-02; T04U-01 (apart from T04B-03: same LMR clamp); T04-06 at LTC; T04H-01 last of the ttpv cards; T04N-03, T04S-02 and T04T-03 at the tail. T12-04 (SPSA)
  runs off the gate queue on its own CPU budget, then one tuned-set SPRT.
- Phase 3, stacks of the positives by site group: history (E-03 base + S-01 / R-01 / G-05 / T-01), null move (E-02 +
  N-02 + T04-03), singular chain (N-01 + T04-01 + C-02), TT cutoff (D-02 + P-01), SEE (B-01 + E-04).
- Eval line (CPU fit, then gate): T06D-01 / T06D-03 / T06E-01 / T06E-02 only after the T06C-01 frozen-residual refit passes its holdout
  filter, each fitted with the residual frozen.
- Beside the gate PC: node-identical lock speed by nps ABBA after the T12-03 bench + fuzz proof, specs in SPEC_SPEED:
  T05D-01 `FORGE_TT_NOTLS` (port of the own R7TtExclusive, NOT in the lock; own +3.6-4 % on another tree, lock +2 to
  +4 % nps UNPROVEN), T05C-02 `FORGE_NO_ZERO_MOVELISTS`, T05C-03 `FORGE_SLIDER_ATTACKS` (microbench first), T05B-02
  `FORGE_MATKEY_FAST` (timed as a stack with T05C-03), T05F-01 (step-0 counter first, memo only on go). GPU window:
  T02-01 first, the T02-04 equal-node WAC diagnostic, then T02-03, T01-06. Owner item T12B-01 (port own fix).
- Budget: phases 0 + 1 = 9 runs = 54-63 h of gate PC; all ~57 lock-direct singles = about 340-400 h at the cap.

**Next three crew experiments** (no new code for the first two; after the P27R extension the crew rule already owes):
(1) the E3 exe with `EvalRule50Damp=60` vs the lock; (2) the caissa_c123 exe with `TtCutExtraMargin=72` vs the lock;
(3) the Phase 1 kit build (five options, ~10.5 crew h incl. counters) with `QuietMalusDecay=8` as its first ON line.

## 5. All cards ranked
`notes/RANKING_FINAL.md` (Fable, 04:36-04:51): one row per idea family, 81 rows in five classes (L lock-direct SPRT 44,
G GPU-conditional 11, V net-line speed ABBA 8, S lock speed ABBA 9, E enabler / diagnostic 9; % nps and Elo never
converted into each other), each with source number, UNPROVEN estimate, crew hours, gate route, per-hour value and vote
state; then the top 10, the phased gate order and CRITIC3 (13 items). Its ranks use the card estimates before the
counter-evidence; section 1 here applies it. Cards written after it: T04R-01..03, T04S-01..02, T04T-01..03,
T06D-01..03, T04U-01, T06E-01..02 (placed in sections 1 and 4).

## 6. Cross-track facts this report uses
- Gate rate 430-502 games/h measured for every `*_vs_AL1*` gate (497 at Threads 2 / conc 4); the ~1,000 games/h in some
  cards is the older R7 J4 rate (Threads 1, conc 8). v2 identical-eval control: -20.9 +- 18.5 (post root fix, sanity
  only); the pre-fix -32.2 is stale.
- T5: v2p4 at 0.85-0.89x = build ~0.98 x KB4 table + refreshes ~0.95 x finer layout (KB8 0.988, KB32 0.942) x an
  unmeasured ~0.97 (`notes/T05/V2P4_GAP.md`); int8 / VNNI / find-nnz apply to the HalfKA path only; Zen 5 VPDPBUSD zmm
  latency 3 / 0.5 c, VPCOMPRESSD store 8 uops (Zen 4: 144). BOLT on MSYS2 / Windows: **no** (ELF only, bolt/README.md).
- Data: the training set is the self-play J1 binpack only; the w4 runs used lambda 1.0 (run log) against the decided
  0.7-0.9; the npt HalfKA nets run at 0.47-0.58x the OFF nps, which can explain much of their -86 to -116 Elo.
  Self-play still runs the 6.2.0 HCE build: `notes/T02/MIX.md`'s first step is the lock as the teacher.

## 7. Ideas already in Forge (found by the tracks; details in the TABLEs and DIFFs)
Probcut never in check; history kept across moves; losing captures last; TT move kept in a non-overwritten entry;
qsearch TT 50-move guard; negative extensions (-2 / -1) and IIR (variants prepared); best-move stability and
per-iteration falling-eval TM, soft / hard tunables, node-effort TM; history gravity on the main history; per-worker
refresh caches on the v2 and v3 paths (not on HalfKA); E3 options EvalMatScale / EvalOptimism / EvalRule50Damp /
DrawJitter; packb FiftyDamp and ReSearchAdjust (bundled tries); CorrUpdateMode (gravity-style correction update, gates
63 / 68); the deeper-entry TT cutoff as form B (own caissa_c123 port, never gated); NMP non-pawn-material and TT-bound
conditions, LMR by child fail-high count, SEE threshold from the LMR depth, cut-node -1 extension, skipping quiets
after futility / LMP, lazy accumulators, TT prefetch, correction history with a depth-weighted update, a 32-bit TT
verification key, LMR starting one move later at the root, aspiration re-centring on a fail low, a larger history bonus
beyond beta + margin, qsearch TT cutoffs off the PV (T04O / T04S / T04T re-greps); a quarter main-history bonus for a
quiet PV best move without a cutoff; self-play rows already drop in-check, capture / promotion best moves, mate and
bound scores, |cp| > 3000.

## 8. Dead ends (one line each; the hand-backs and TABLE verdicts hold the rest)
Merged king planes (neutral) | wider L1 (fixed-node gain vanishes at real TC) | distillation without a stronger teacher
| from-scratch threat nets (110G positions vs our 305M) | same-engine deeper relabel: no source with Elo | complexity-
and eval-level TM (both removed later by the source) | asymmetric optimism | draw jitter under +1 at 10+0.1 | null
moves not advancing rule50 | int16 accumulators (bound 342,331 > 32,767) | int8 first layer (15-bit weights) | BOLT
on PE | shared correction tables (only if gates stay Threads=1) | fail-firm RFP (gate 86) | EvalOptimism=40 (rerun H0)
| a lock bug worth >= 1 Elo (T04Q audit: none found) | more permissive engines (T04O: two sources in a row without a
card) | Stockfish b280d2f as evidence for the fail-high deeper-entry rule (it measured the fail-low side) | Sirius #268
qsearch recapture rule (reverted as broken) and #222 / #219 (reverted: faulty test worker) | motor #178 correction
target (a correction-weight knob on Forge's additive update) | Carp, Willow (no tested commits since 2024) | Horsie,
Seer (only ideas Forge has or has tried) | a lower, WDL-skew or phase-dependent |eval| cap on training rows
(T02C: no source measures one at a fixed net size).

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
11. The R15 C5 gate line in `D:/o15/cands/INDEX.md` (crew file) lacks T04F-02's source numbers.
12. Pointers for later work: Tarnished #82 complexity-based time management (STC +4.54, LTC +6.63; mechanism not in the
    PR text); the older Stockfish / Ethereal numbers for the initiative term
    (T06D-03) were not read; T06E closed the rest of the T06D pending list.

## 10. Skills, scripts and tools created or improved
- Skill `skills/forge-deep-research/SKILL.md` (new; also installed as a user-scope skill on grok-pc): setup, tools,
  worker rules, the per-track and pooled workflows, verification, checkpoints, the low-usage stop, measured costs,
  lessons (one pooled workflow; refill before the queue empties; never resume a pool; the owner's 3-worker hook, which
  also refuses TaskStop, the board, agent types missing from the registry, 1-worker runs on idle slots).
- Skill `skills/forge-pc-rules/SKILL.md` (branch copy with this job's section; the D: project copy untouched).
- `opus_deepres/tools/`: `mine_commits.py`, `licence_at.py` (GPL / AGPL title, LLVM Apache, CC0 fixes), `forge_has.sh`,
  `card_lint.py` (merge markers accepted), `tried_gates.py`, `block_rule_check.py`, `merge_licences.py` (cached),
  `workflow_prompts.py`, `handbacks.py`, `novendor_filter.py` (git clean filter), `board.py` (crew worker board: claim
  a slot, take another idle one when the named one is busy, wait / refuse when all 3 are busy, release by worker +
  task, done line; tested on a copy); workflows in `tools/workflows/` (`deepres_tracks.js`, `deepres_phase2_checks.js`,
  `deepres_round2_tracks.js`, `deepres_pool.js`, `deepres_pool3.js` = the 3-worker pool with task dependencies,
  latest-start times, a Fable verifier after each research task, agent types with a fallback and a cooperative
  wrap-up note).

## 11. Incomplete work, deviations, spend
- Not done: sub-tracks T04I-T04M (LMR inputs, extensions, null move, futility, qsearch) DROPPED at 01:35 as overlapping
  the per-engine mining (owner: no two agents on the same thing); brief questions not covered: see `notes/CRITIC.md`
  "Uncovered or partly covered questions" (3 NOT COVERED at 02:00; two answered in round 3: the T1 data size / L1 / nps
  per feature set table is `notes/T01/FEATURE_COST_TABLE.md` (51 rows, "missing" wherever a source states nothing; the
  only clean equal-tree layout costs are our own v2 numbers KB8 0.988x / KB16 0.969x / KB32 0.942x of KB4), and T2 |eval|
  caps are NOT FOUND at a fixed net size (`notes/T02C/TABLE.md`, no card; the WDL-skew form belongs to T02-03); still
  open: T2-card-1 within-train board+stm duplicates as a crew measurement; about 20 covered with a qualifier; T6
  `FORMS.md:79-81` PENDING); older cards keep their
  pre-decision cost lines (section 2); unread pages listed in `notes/T04T/sources.md` and `notes/T04U/TABLE.md` (motor page 3+); every PENDING item in the cards.
- Deviations: workflows stopped and relaunched five times before 01:35 (22:47 re-plan; 00:20 into one pool; 01:24-01:29
  two pool resumes that re-ran finished agents for ~2 min each before being stopped; 01:35 usage warning); after the
  reset, 1-worker runs were started next to POOL3 to use slots it left idle (total never above 3; the owner's hook
  refused four launches while finished workers were still inside its 3-minute window); the `opus-max` agent type was
  missing from this session's agent registry until ~05:16, so those tasks ran as the session model at effort max (8
  refused spawns logged as "failed", no agent started); two workers' log sections interleaved in FIXES_APPLIED (a
  heading was added); four first-round workers put temp files into this session's scratchpad on C: (left in place); a
  dataset name equal to a model name was pushed once in 8131d711 (filtered since); several times were first written as
  estimates and corrected from the clock or file stamps (also 04:24 -> 04:22, 04:26 -> 04:25, 05:04 -> 05:03, 05:43 ->
  05:42, 06:04 -> 06:05 in STATUS); the first licence tool misread GPL-3.0 and LLVM texts (fixed, table re-run); the
  brief's caps of 60 cards in total was passed after the owner's instruction to find more improvements with more agents
  (23:55, and the goal of 22:5x to keep going until the window ends): 107 card files incl. one-liners and merge
  markers, per-track caps (6, and 4 per round-2 / round-3 sub-track) kept; the T02C worker read on past the
  two-sources-without-a-card stop to cover every source its brief named (logged by its verifier).
- Measured agent spend (workflow summaries): round-1 core 1,802,872 tokens (8 agents), extra 1,149,308 (6), phase 2
  541,874 (2), light pool 1,667,660 (10); after the reset POOL3 1,690,105 (10), POOL3B 514,776 (3), POOL3C 334,288 (2),
  POOL3D 596,161 (3), POOL3E 325,548 (2), POOL3F 389,429 (2), POOL3G 150,775 (1), POOL3H 695,899 (4), POOL3I 222,633
  (1), POOL3J 299,582 (2), POOL3K 429,249 (3), POOL3L 464,996 (3) = 6,113,441 for round 3; measured
  total of the finished workflows 11,275,155 agent tokens; the stopped runs report no total. Owner's readings: "running out" before 01:35; 77 % of the 5-hour
  window used at ~02:26, reset ~03:40; no reading since.

## 12. Where each brief deliverable is
T2-card-1: section 0 and `cards/T02/T02-01-*`. T1 (features and recipe): `notes/T01/recipes.md` (ranked recipes, the
npt / bullet / open-recipe side-by-side), `notes/T01/FEATURE_COST_TABLE.md` (data size / L1 / nps cost per
feature set), `cards/T01/`, `cards/T01B/`. T2 (data quality): `notes/T02C/TABLE.md` (|eval| caps: not found), `notes/T02/TABLE.md` (ranked
filters / relabels), `notes/T02/MIX.md` (self-play vs external mix, nodes per move, generations), `cards/T02/`,
`cards/T02B/`. T4 (search): `notes/T04/TABLE.md` plus the sub-track TABLEs, `notes/T04/BUG_CHECKLIST.md` (21 Elo-losing
patterns with example commit, symptom and box test), the lock audit `notes/T04Q/AUDIT.md`, cards T04-T04T. T5 (speed):
`notes/T05/SPEED_LIST.md` (ranked, with the microbenchmark plan per row), `notes/T05/V2P4_GAP.md`, the BOLT one-liner in
section 6, specs in `notes/SPEC_SPEED.md`. T6: `notes/T06/FORMS.md`, `notes/T06/FIT_RECIPE.md`, `notes/T06/DEAD_ENDS.md`,
cards T06, T06B, T06C, T06D. T7: `cards/T07/` (2 cards) and `notes/T07/UCI_EDGE_CASES.md`. T12: `notes/T12/PROTOCOLS.md`,
`notes/T12/sprt_model.md`, cards T12 / T12B, the checklist card `cards/T12/T12-03-bench-fuzz-checklist.md`.

FINAL finished 07:04 PC clock (from `date`).

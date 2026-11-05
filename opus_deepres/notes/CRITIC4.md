# CRITIC4: adversarial check of FINAL_REPORT.md (state INTERIM 4, the final draft)

Worker fable CRITIC4, board slot S3 (S1 was busy), started 05:42 PC clock 2026-11-05 (`date` in the first command); the
finish time is the last line. Read-only on the report, the cards, the notes and the lock source; nothing built, run or
edited except this file; scratch F:/odr/work/CRITIC4/ (filtered copy of the report). T04T / T06D folders not touched.
Inputs: FINAL_REPORT.md, notes/RANKING_FINAL.md, notes/T12C/COUNTER.md, notes/TOP_SECOND_VOTE2.md / VOTE3.md,
notes/FIXES_APPLIED.md, notes/CRITIC.md Part A, the SPEC files (grep), the top-10 cards' Expected gain / Effort fields,
cards T02-01, T02-04, T04S-02, T04R-02/03, notes/T04Q/AUDIT.md, notes/T05/SPEED_LIST.md, LICENCES.md, notes/T04R and
notes/T04S VERIFY.md. Severity: wrong (a number or fact does not match its source) | misleading (true but reads as
something else) | wording. Each finding gives the exact fix in words (section, old -> new).

Verdict first: nothing here blocks FINAL once findings 1-3 (facts) and 5-6 (pointers) are applied; every other number
in sections 0-4 that I checked reproduces from its card or note (list in "Checked and holding" below).

## Findings

1. wrong - Section 1, the metric and the order of rows 7-10. The metric line says "midpoint of the card's UNPROVEN range /
   crew hours; ties by the larger midpoint", but the table does not follow it in three places:
   (a) row 9 T04C-02: the card's range after T12C is still 0 to +3 (COUNTER.md row 6 lowers the *expected value* to
   "about +1", not the range), so midpoint / 1 h = 1.5, not 1.0; at 1.5 it ties T04-01 at rank 3.
   (b) ties at 1.0: T04E-01 (midpoint 2.5 / 2.5 h = 1.0) and T04G-05 (1.5 / 1.5 = 1.0), both listed in the "Next"
   paragraph at "~1.0", have larger midpoints than T04E-03 (2), T04C-02 and T04D-02 (1), so by the stated tie rule they
   belong above rows 8-10; the report put them in "Next" for evidence reasons (single engine / small n) that the metric
   line does not state. Rows 4 and 5 (E-02, F-01: both 1.33, both midpoint 2) are also a tie the stated rule cannot break.
   (c) T12-04 (lock-direct L11, 1.25 per crew-h on the report's own numbers) is above rows 7-10 but kept out of the table
   because of its 33-67 h of tuning games - a cost that is not crew hours and not in the metric.
   Fix (keep the order, say the rule): metric line "midpoint of the card's UNPROVEN range / crew hours, except T04C-02,
   which uses the T12C expected value (~+1); rows whose main cost is tuning or GPU time (T12-04, the G class) are listed
   after the table; at equal value the rows are ordered by evidence breadth (engines x time controls with a pass), which
   is why T04E-01 and T04G-05 (one engine each) follow rows 8-10" - or, if the arithmetic is to rule, write 1.5 for
   T04C-02 and move it into the rank-3 tie and swap E-01 / G-05 for C-02 / D-02.

2. wrong - Section 3, T04Q bullet: "the 25-pattern pre-gate checklist plus nine classic spots" -> "the 21-row checklist
   (notes/T04/BUG_CHECKLIST.md; CRITIC.md Part A counts 21 rows, the file has 21 table rows) plus 12 extra spots (AUDIT.md
   section B, B1-B12)". Also add what the audit says and the report drops: "two rows are NEEDS RUN (13, 21), each with the
   box test that would decide it" (AUDIT.md header). The three small hits (B1b, B4b, B10) are as the report says.

3. wrong - Section 0: "rebuild the 37 train shards with the same converter" - card T02-01 gives one shard count only,
   "convert 39 shards 6 min 19 s incl. verify" (card :46, notes/T02/VERIFY.md:13); "37" appears nowhere in the card.
   Fix: write 39, or write "37 train + 2 holdout shards" only if that split is on the card (it is not in the card's
   Mechanism or Effort text as read).

4. wording - Section 2: "the LLR reaches +2.94 at the cap only if the running estimate is near +12 Elo (near -10 Elo for
   H0)" is not in VOTE2 or VOTE3 (VOTE2 gives the ~28k mean run length, ~0 % for a true +2.5, "+10 for stacks"). The number
   reproduces (own Gaussian check, section (e) below: +12.3 / -9.9), so label it: add "(own Gaussian arithmetic from the
   +-5.9 half-width; the VOTE2 elo_check.py model)". Also "only stacks worth roughly +10 Elo can decide inside the cap":
   at a true +10 the mean run length to the H1 bound is about 3,800 games (> the cap) and the chance to decide inside
   3,000 games is roughly one in three; at +12 the mean run length equals the cap. Fix: "only a stack worth roughly +10
   Elo has a real (about one-in-three) chance to decide inside the cap; near +12 the mean run length equals the cap".

5. misleading (coverage, task (c)) - brief deliverables the report never points to by file; one sentence in the pointer
   paragraph (lines 12-17) is enough: T1 ranked recipes `notes/T01/recipes.md` (the generic "TABLE.md, DIFF.md,
   VERIFY.md" line does not cover it: T01 has no TABLE); T2 ranked table and mix `notes/T02/TABLE.md`, `notes/T02/MIX.md`
   (MIX.md is named at line 141 without its path); T4 pre-gate checklist `notes/T04/BUG_CHECKLIST.md` (21 rows; the brief
   asked for 15-25); T5 ranked speed list with the microbenchmark-plan column `notes/T05/SPEED_LIST.md` (V2P4_GAP.md and
   the one-line BOLT answer are present, line 137-138); T6 `notes/T06/FORMS.md`, `FIT_RECIPE.md`, `DEAD_ENDS.md` and the
   cards `cards/T06/`; T7 `cards/T07/` (2 cards, within the cap; ranked L29 / L36 in RANKING_FINAL) and
   `notes/T07/UCI_EDGE_CASES.md`; T12 `notes/T12/PROTOCOLS.md`, `notes/T12/sprt_model.md`. Already pointed to: T2-card-1
   (section 0), T12 checklist card T12-03 (line 114, by id), the counter-evidence, votes, specs and fixes.

6. misleading - Section 11 "Not done" omits the brief questions CRITIC.md Part A marks NOT COVERED (line 166 on): the T1
   data-size / L1 / nps per feature-set table, T2 |eval| caps, T2-card-1 within-train board+stm duplicates (a crew
   measurement), plus T6's PENDING (Altair and GPL logs for post-net forms, FORMS.md:79-81) and the ~20 rows covered
   with a qualifier. Fix: one line "Brief questions not covered: see notes/CRITIC.md 'Uncovered or partly covered' (3 NOT
   COVERED, ~20 qualified; T6 FORMS.md:79-81 PENDING)".

7. wording - Section 3 "22 options / switches specified": 22 is the number of cards / switches (5 + 3 + 5 + 5 + 4);
   the five spec files name about 30 UCI options (secondary rows such as TtCutNodeForm, QuietMalusStart / Floor,
   NoisySeeHistCap, NmpFewCutoffsForm / Discount, NmpTtCaptureSee; T04-04 has two weights) plus 4 build switches.
   Fix: "22 ideas specified (about 30 UCI options and 4 build switches)".

8. wording - Section 4, last bullet "(3) the Phase 1 kit build with QuietMalusDecay=8 as its first ON line (spec ready;
   2-2.5 crew h)": 2-2.5 h is the E-03 option alone (card 2 h, spec 2.5 h); the five-option build RANKING_FINAL's Phase 1
   costs "~10.5 incl. counters". Fix: "2-2.5 crew h for the E-03 option; the full five-option build ~10.5 h".

9. wording - Section 4 "T05D-01 FORGE_TT_NOTLS (port of the own R7TtExclusive, +3.6-4 % on another tree, NOT in the
   lock)": the lock-side number is missing its label. Fix: add "lock estimate +2 to +4 % nps UNPROVEN (RANKING_FINAL S4)".

10. wording - Section 1 row 1: "SF 7b06475 STC +4.15 / LTC +2.94" is the second vote's two-decimal recomputation
    (notes/TOP_SECOND_VOTE.md:20); the card itself prints "+4.2 (23,017 games) / +2.9 (30,746 games)". Consistent; either
    quote the card's rounding or add "(vote 1 recomputation)".

11. wording - Section 2 "the 95 % half-width is about +-5.9 Elo (UHO, pentanomial)": say where it comes from - the
    P27R-AL1 QsEvasionSeeNonPv=1 row's own error bar (+4.63 +- 5.90 at 3,000 games, VOTE2 line 86), one run, cross-checked
    by the 0.46-0.52 Elo per nElo ratio of the Stockfish runs.

12. wording (non-blocking, rule (d)) - Section 11 "ran as Opus 5.5 at effort max": a model-version string. The job's
    own filter (tools/novendor_filter.py) passes the whole report unchanged (diff = 0 lines, F:/odr/work/CRITIC4/
    report_filtered.md) and the board uses "opus-max" as an agent type, so it is not a violation of the rule as the job
    applies it; "the fallback agent type at effort max" would avoid the question.

13. wording - Section 11 / section 3: the T04S verifier logged "1 correction (T04S-01, missing test ...)" next to
    "0 violations, 0 duplicates" (notes/T04S/VERIFY.md:7); section 3 says only "All verified (0 violations, 0
    duplicates)". Add "(one T04S-01 correction applied by the verifier)".

## Checked and holding (sections 0-4, number by number)
- Section 0 vs card T02-01: 7,700 train rows; 0.0025 % of 304,999,573 (7,700 / 304,999,573 = 0.00252 %); 4,118 minimum
  for "4,088 -> 0"; 7,612 holdout rows; block rule 189,181 vs 189,197 (16 apart net, per class 25 / 41, FIXES round 1);
  under 30 min on one core; 10.37 ~ 10.4 GB; crew ~2 h; "no direct Elo". Only the shard count differs (finding 3).
- Section 1 rows vs cards / RANKING_FINAL / COUNTER: T06-05 0 to +3, 0.5 h, 3.0; T04P-01 Caissa 9d566cc +1.35 +- 1.06
  (112,192 g), d39fcfb +2.11 +- 1.55 (48,018 g, 40+0.4 only), PlentyChess 373 STC H0 / LTC +1.73, form B 0 to +2, 0.5 h,
  2.0, exe 8924099a, option 0-200, CR PASS 2026-10-30; T04-01 +4.20 +- 2.23 (25,044 g), 0 to +3, 1 h, 1.5; T04E-02
  Reckless +3.43 / +3.67 early stop, Viridithas +1.88 +- 1.48 (49,814 g), +1 to +3, card 1-2 h = 1.5, 1.33; T04F-01
  a677c89 +3.29 +- 2.6 (25,531 g, no TC), +1 to +3, 1-2 h, 1.33; T04-02 434bbda +6.93 / +5.14, Patricia 137 +5.55, T12C
  +1 to +4, 2 h, 1.25; T04S-01 Tarnished #132 +2.23 +- 1.70 (39,808 g) / +2.53 +- 1.85 (32,122 g), Sirius #328 +5.86 /
  +14.38 (blend at STC), Clockwork #234 +14.67, +1 to +4, 2-3 h, 1.0, own start 60; T04E-03 a016abd +3.78 / +2.18, four
  engines, +1 to +3, ~2 h, 1.0; T04C-02 1591e5a +1.04 +- 0.64 (235,592 g), 4e89864 LTC +1.83 (finding 1a on the metric);
  T04D-02 43e100a +2.72 / +1.02 +- 0.62 (270,888 g), T12C 0 to +2, 1 h, 1.0. "Next": T04N-01 0.83 (1.25 / 1.5),
  T04R-01 0.75 (1.5 / 2, Renegade +3.35 +- 2.29 early stop), T04D-01 0.75 (T12C 0 to +1.5 / 1), T04B-01 0.75 (T12C +0.5
  to +2.5 / 2; 243,828 g ~ 244k), T12-04 1.25 (2.5 / 2), T04S-02 0.33 (+1 to +3 / 5-7 h; Sirius +5.29, Viridithas #465
  LTC +2.27 as the card). "Not new" lines match FIXES round 1 (packb FiftyDamp / ReSearchAdjust, gates 12 / 35 / 40 / 41).
- Section 2 cost: 3,000 / 502 = 6.0 h, 3,000 / 430 = 7.0 h; old cost line 6.6k games ~13 h = WORKER_RULES Round 2.
- Section 3: T04P-01 verified 04:07 (board); b280d2f +3.91 STC is the fail-low side (card, RANKING CRITIC3 item 2);
  T04R one-liners R-02 (pawn-structure refutation move) and R-03 (full update when alpha was raised) exist; T04R and T04S
  VERIFY: 0 violations, 0 duplicates (finding 13); second-vote verdicts as RANKING_FINAL's vote column (KEEP D-01, F-01,
  B-01, E-04, E-03; KEEP-WITH-FIX D-02, C-02, E-02, N-01; DOWNGRADE N-02; VOTE3 KEEP P-01, T05F-01; KEEP-WITH-FIX R-01,
  N-03, E-01, G-05); crew-cap cost lines on 9 cards = FIXES round 4 (6) + round 6 (3); SPEC_SPEED_REVIEW 10 FIX items
  (C1-C5, S2-1..3, S4-1..2); round 5 = one code fix (E-02 is_pseudo_legal, board.cpp:600 via search.cpp:326) + wording.
- Section 4: Phase 0 4 x 6-7 = 24-28 h; phases 0 + 1 = 9 runs = 54-63 h; ~48 singles x 6-7 h = 288-336 ~ 290-340 h
  (43 ranked L + R-01..03 + S-01..02); Phase 1 order (E-03 first, D-01 last) follows COUNTER's net effect; P27R-AL1 +4.63
  capped positive (VOTE2 line 16); T04F-02 -> R15 C5 (FIXES round 3).
- Section 5: 44 + 11 + 8 + 9 + 9 = 81 rows (RANKING_FINAL "Rows" line). Section 6: 0.47-0.58 ON/OFF per depth (card
  T02-04:18); -86 to -116 Elo (T02-04:40); v2 control -20.9 +- 18.5; KB8 0.988 / KB32 0.942 / ~0.97 (V2P4_GAP); the Zen 5
  rows quoted are the VPDPBUSD row and the VPCOMPRESSD *store* row (the register row is the one marked "not re-checked");
  BOLT no (bolt/README.md, SPEED_LIST:46-48). Section 9 item 6: Viridithas v20.0.0 MIT at 0631113e22 = LICENCES.md:204
  and notes/T01/licences.md:18-24 (the 2026-11-04 head is AGPL, row 105). Section 11 token sums: 5,161,714 + 4,001,082 =
  9,162,796 (both partial sums re-added).

## (b) forge_has.sh re-runs (lock FD3A5190 source, read-only; 7 statements, all consistent with the report)
| report statement | regex | hits | result |
|---|---|---|---|
| T04P-01: the lock takes a TT cutoff at equal depth (deeper-entry rule LACKING; form B only in the own caissa_c123 port) | `tt_depth >= depth` | 3: search.cpp:921 (cutoff block), :1003 (probcut, depth - 3), :1090 (singular, depth - 3) | holds (VOTE3 line 27 same three lines) |
| section 7 / T04G-05: history bonus one ply deeper only when best_score > beta + 100 | `best_score > beta \+ 100` | 1: search.cpp:1198 | holds |
| section 7 / T04R-01 "partly": LMR by the child's fail-high count exists | `cutoff_count` | 4: search.hpp:273, search.cpp:905, :1145 (LmrCutoffThreshold), :1180 | holds |
| T04E-02: the lock's null-move condition has no hash-move term | `null.*tt_move\|tt_move.*null\|hash_move.*null\|null.*hash` | 0 | holds (LACKS) |
| section 4 / T05D-01: R7TtExclusive is NOT in the lock | `R7TtExclusive\|TtExclusive` | 0 | holds |
| same card: the emulated-TLS lookup the port removes exists in the lock | `thread_local` | 3: search.hpp:153 and search.cpp:184 (`ExclusiveLease* active_lease_`), eval_params.cpp:23 | holds (the TLS lease is there) |
| T06-05: the lock uses the 50-move counter only for the draw and the TT guard, no damping | `halfmove` | 30 (board clock fields, FEN parse, TT store / probe; none in eval) | holds |

## (c) Coverage against notes/CRITIC.md Part A (82 rows, 8 tracks)
Pointed to: T2-card-1 (section 0, card T02-01); T12 checklist card T12-03 (line 114); the BOLT answer (line 138);
V2P4_GAP (line 137); MIX.md by name (line 141); TABLE / DIFF / VERIFY generically (line 12). Not pointed to by file:
the list in finding 5 (T1 recipes, T2 TABLE + MIX path, T4 BUG_CHECKLIST, T5 SPEED_LIST, T6 FORMS / FIT_RECIPE /
DEAD_ENDS, T7 cards + UCI_EDGE_CASES, T12 PROTOCOLS + sprt_model). The three NOT COVERED questions and the T6 PENDING
are missing from section 11 (finding 6). Card counts within the caps: T07 2 cards; T04R 1 + 2 one-liners; T04S 2.

## (d) Rules pass
- No Elo claim for Forge: the Forge-side numbers in sections 0-4 are quoted gate results with their game counts (P27R-AL1
  +4.63 at 3,000 g capped, UE3C D=30 +1.51 at 3,000 g capped, EvalOptimism=40 -5.30 +- 7.20 at 2,360 g, R7 J3 +3.59 % on
  another tree) or ranges labelled UNPROVEN (section 1 column header, section 5, 6; finding 9 adds the one missing label).
- Vendor / model-company names: tools/novendor_filter.py leaves the report byte-identical (finding 12 is a wording note).
- No licence or copyright header. No other engine's tuned constant as a Forge value: EvalRule50Damp=60 (own E3 range max),
  TtCutExtraMargin=72 (= the lock's RfpMargin, VOTE3 line 28), QuietMalusDecay 8 / NmpTtCaptureMin 4 / NoisySeeHistDiv 96 /
  CutNoTtLmr 1 / TtCutNodeDepth 6 (SPEC_SEARCH2 "own start" lines 61 / 95 / 134 / 165 / 189), ContHistSumBase 60 own,
  T04-02 "own constants".
- Times: start 05:41 "from date", finish line "from date"; board times match (04:07, 04:36-04:51, 05:39); "~05:16" is
  marked as approximate; no estimated clock time found.

## (e) Section 2 arithmetic (own re-derivation, Gaussian, pentanomial pair variance)
- +-5.9 Elo at 3,000 games -> SE = 5.9 / 1.96 = 3.0 Elo; per-game sigma = 3.0 x sqrt(3,000) x ln10 / 1600 = 0.237 in
  score units. nElo = Elo x 0.5 / sigma (normalised so that nElo = Elo at 0 % draws) -> 1 Elo = 2.1 nElo -> 5 nElo = 2.37
  Elo: "[0, 2.4] Elo" holds at the crew's own variance, and the Stockfish ratio 0.46-0.52 brackets it (2.3-2.6).
- LLR (Gaussian GSPRT in Elo units) = (e1 - e0) x (x - (e0 + e1) / 2) / SE^2 = 2.4 x (x - 1.2) / 9.06 at 3,000 games:
  LLR = +2.944 (ln 0.95/0.05) at x = +12.3 Elo, LLR = -2.944 at x = -9.9 Elo -> "near +12 / near -10" holds (finding 4
  asks only for the label). A true +2.5: the end point is N(2.5, 3.0), P(x > 12.3) = 0.05 % -> "almost never decides".
- Mean run length to the H1 bound at a true gain g: 2.944 x 27,180 / (2.4 x (g - 1.2)) games = ~6,900 at +6 (VOTE2 says
  ~7k), ~3,800 at +10, ~3,100 at +12 -> the "+10 decides inside the cap" wording is too strong (finding 4).
- Cost: 6.0-7.0 h per 3,000 games; the old [0,10] / 12k line (6.6k games, ~13 h) = WORKER_RULES Round 2 - both hold.

## Files
notes/CRITIC4.md (this file); scratch F:/odr/work/CRITIC4/report_filtered.md, filter_err.txt (empty). Nothing else written.

Finished 05:56 PC clock (`date` run in the same step as this line); 13 findings (3 wrong, 2 misleading, 8 wording), 7 forge_has re-runs, none blocking FINAL once 1-3 and 5-6 are applied.

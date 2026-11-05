# T12C: counter-evidence for the FINAL_REPORT section-1 top 10
Worker opus-max T12C, started 04:22 PC clock 2026-11-05. Research only; no card edited. Every Forge estimate here is
the card's own and stays **UNPROVEN**; "effect" only says whether the evidence below argues to lower / keep / raise it
or move it in the gate order. Sources: `sources.md` (numbered S1..); licences: `licences.md`.
Method per idea: one search (GitHub commit / PR search or web), at most 2 reads; failed or neutral tests of the same
mechanism elsewhere, and reverts / simplifications of the idea in its own engine.

## 1. T06-05 rule-50 damping (EvalRule50Damp)
Mechanism closest: Stockfish 7b06475 / 3af083a are the card's own sources; the later history of the same term:
- S1 Stockfish 180cab4 "Simplify 50 move rule dampening" (2024-06-01, PR 5327; message: "refactor ... by removing a
  constant"): non-regression [-1.75,0.25], STC LLR 2.93, 35,232 g, +2.19 +- 1.86; LTC LLR 2.94, 38,406 g,
  +1.83 +- 1.64 (own pentanomial arithmetic; TC / book not in the message). The damping was simplified, not removed.
  Title-only (cached commit list): d712ed3 2024-05-05 "Simplify shuffling and optimism divisors to constants" (LTC
  ~+0.12, n=178,278), b8ccaf0 2024-05-21 "Use same shuffling Constant for both nets" - the strength constant was
  flattened twice at zero cost, so the exact damping strength is a flat optimum in that engine.
- No revert or removal of the eval damping found in the cached Stockfish history 2019-09 .. 2026-10 (title and
  message scan).
- Neutral tests already on the card (not new): Patricia PR 153 +0.96 +- 1.31 (LLR 0.51); own UE3C D=30 +1.51 (cap).
Closeness: same term (eval scaled down with the rule-50 counter). Effect: KEEP 0 to +3 and its gate slot; the flat
optimum in the source argues that D=60 vs D=81 will be hard to tell apart in 3,000 games (gate one value only).

## 2. T04-02 LMR re-search deeper / shallower
- S2 Stockfish 955edf1 (2022-12-12) Revert "doEvenDeeperSearch + tuning": reverted because "the increase of depth
  could lead to search explosions, most visible with TB" (issue 4276). A second, larger deeper step was reverted for
  an explosion / correctness reason, not for Elo.
- Title-only, cached list (numbers as the miner parsed them from the messages): 39af98c 2022-12-19 "Reintroduce
  doEvenDeeperSearch" (one week after the revert; STC ~+0.67 n=514,048, LTC ~+1.38 n=113,800); b59786e 2023-11-20
  "Remove doEvenDeeperSearch" (simplification; STC ~+1.43 n=51,040, LTC ~+0.16 n=165,168); 5304b56 2022-06-20 "LMR: remove
  deeper"; f17db46 2023-12-02, 4d4c6eb 2025-12-23, 1047f84 2025-12-28 "Simplify doDeeperSearch (formula)".
- S3 Stockfish 87814d2 "Simplify doShallowerSearch" (2024-08-20): non-regression [-1.75,0.25], STC LLR 2.94,
  242,336 g, -0.01 +- 0.72; LTC LLR 2.94, 128,100 g, +0.31 +- 0.92. The shallower half's form was simplified at zero
  cost (what was removed is not in the message; source not read).
- The extra-deep step oscillates: reverted for explosions (S2), reintroduced, removed (b59786e), and in another form
  27428a6 2025-04-26 "Allow some nodes to spawn even deeper lmr searches" (STC ~+1.24 n=123,552, LTC ~+1.44
  n=114,306; title only).
- Still alive in the source engine: a37b38b 2025-08-02 "Add d < newDepth condition for doDeeperSearch" (STC ~+1.91,
  LTC ~+0.91 n=411,240; title only) - a guard on the deeper step, again small at LTC.
Closeness: same mechanism (deeper / shallower re-search after a reduced fail-high); the extra-deep variant was
reverted, reintroduced, removed and reintroduced in another form. Effect: KEEP the gate slot, LOWER the range to +1
to +4: later gaining Stockfish edits of this block are about +0.9 to +2.3 at LTC (title-parsed, e.g. 219fa2f
2022-11-19 "Do shallower search in case of lmr being not successful enough" LTC ~+2.25 n=51,144), one PV-shallower
tweak at ~+3.25 (c19a6ea 2025-02-24 "Make Pv search shallower in some cases", title only, block membership
unverified), simplifications about 0; and the revert shows the deeper step needs a hard guard (the card's ply
guard is required, not optional; add mate / TB positions to the pre-gate box tests).

## 3. T04-01 singular verification search as a non-cut node
- No failed or neutral test of this mechanism found. Stockfish: no commit whose message joins singular and cut node
  except the 2019 multi-cut pair (f69106f, 8bf21a7; other rule) in the cached history 2016 .. 2026-10 (message scan).
  One web search (W1) found nothing on chess engines.
- Source engine: Caissa did not revert 1b7a871 (titles to the cache date, 2026-09) and built on the same block
  afterwards: f2967c1 2026-01-04 "Triple singular extensions" (+3.36 +- 2.07 at 80+0.8, n=25,260) and 90670d9
  2026-09-01 "Tighter singular margin on an exact TT bound" (title + parsed numbers only).
- Related lever, other form (title only): Stockfish 6ecab03 2020-03-20 "Adjust singular extension search depth"
  (STC ~+6.00 n=12,692, LTC ~+1.41 n=145,716) - verification depth changes shrank to about +1.4 at LTC there.
Closeness: nothing at the same mechanism. Effect: KEEP 0 to +3 (missing evidence is not counter-evidence), but the
whole range rests on one engine's STC run with no LTC anywhere; keep it first in the singular bit-set gate.

## 4. T04D-01 one more LMR ply at cut nodes without a TT move
- S4 Stockfish 5d1505d (2025-08-04) "Reintroduce reduction term in LMR for cutnodes": message: "This term increases
  reduction for cutnodes without tt move, term was simplified away recently." So a term of this family (more LMR
  at cut nodes without a TT move; 9cc15b3 is the card's source, older relatives are 30fdbf4 2021 "Decrease depth for
  cutnodes with no tt move" and 4101893 2023 "increase reduction by 2 if not ttmove and cutnode") was removed by a
  passed simplification and re-added; the message does not say which commit's term it was, and the removing commit
  was not identified (by title perhaps d4b405a 2025-05-13 "Remove a cutNode condition" - not read). Re-introduction: STC [0,2] LLR 2.95, 187,616 g, +1.01 +- 0.81; LTC [0.5,2.5] LLR 2.95, 140,280 g,
  +1.31 +- 0.86 (own pentanomial arithmetic).
- Same engine, opposite direction 9 days before the source: e852d98 2025-02-04 "Reduce less for positions without
  tt move" (STC ~+1.45, LTC ~+1.58; title only) - the no-TT-move signal is used both ways there.
Closeness: same family, very likely the same term (more LMR at cut nodes without a TT move). Effect: LOWER to 0 to
+1.5 and move it down the gate order: in its own engine a term of this family was removed at zero cost and re-added at
about +1 with 140k-188k games, which is at the job's +1 drop line.

## 5. T04D-02 low-depth TT cutoff only when its direction matches the node type
- S5 Stockfish 76c319f (2025-02-24) "Simplify ttcut depth condition" (simplifies the depth limit of a4edacb, the
  card's follow-up): [-1.75,0.25], STC LLR 2.95, 235,328 g, +0.00 +- 0.73; LTC LLR 2.94, 63,744 g, +0.97 +- 1.29.
  The cut-node match rule itself stays (the message touches only the depth condition); the depth limit is flat.
- Related later TT-cut conditions in the same block (title only): 6e9b5af 2025-05-19 "Check evaluation after ttMove
  before doing a tt cut" (~+0.89 / ~+0.89 at n=239k / 449k), 75f07da 2025-08-30 "Avoid high rule50 count zeroing
  cutoffs" (~+1.27 / ~+1.04) - each further gate on low-depth TT cuts is worth about +1 at LTC there.
- No failed or neutral test of the cut-node match rule itself found (no revert in the cached history).
Closeness: same rule; the part shown flat is its depth limit. Effect: LOWER the top to 0 to +2 (the source's own LTC
is +1.02 +- 0.62 at 270,888 g; the follow-up's form simplified away at zero cost); gate it only after T04D-01's
slot is decided, not as a pair.

## 6. T04C-02 lower singular beta at former-PV (ttpv) nodes
- S8 Stockfish 1591e5a (2022-09-11, already on the card via CRITIC2) message: "a reintroduction of logic what was
  simplified a while ago in a slightly different form" - so the 2020 form (4e89864) was simplified away (removing
  commit not identified in the cached history: a message scan for singular + ttPv + simplify/remove found none) and
  re-added; LTC [0.5,2.5] LLR 2.94, 235,592 g, +1.04 +- 0.64. Still alive to the cache date and extended (fcbb02f
  2024-01-26 "Use ttPv in depth condition of singular extensions", title only).
- S9 PlentyChess 9f2cfbc (2025-03-29, PR 334) "Use correct ttpv in excluded search": the message is only the title
  and a bench, no test log. By its title, the singular verification (excluded) search used a wrong ttpv flag until
  four months after PR 286 was merged, so PR 286's +5.21 / +5.34 (both SPRTs unfinished) were measured on a ttpv
  bookkeeping that was later corrected; whether that changes the value of the rule is unknown. Not reverted (titles).
- No failed test of the rule found in another engine.
Closeness: same rule (lower singular beta at former-PV non-PV nodes). Effect: LOWER the expected value to about +1
inside the card's 0 to +3 (the only large-n evidence, Stockfish 4e89864 / 1591e5a, is +0.9 to +1.8; the larger
PlentyChess numbers are unfinished and pre-date a ttpv fix); keep it inside the singular bit-set gate, after T04-01.

## 7. T04E-02 no null move when the hash move captures a valuable piece
- Softer form of the same signal in both source engines, earlier: S10 Reckless 5b38ddf (2025-03-11, #153) "Increase
  NMP reduction if TT move is a capture": 8+0.08, 1 thread, 32 MB, SPRT [0,5], LLR 2.89, 9,694 g, +5.34 +- 3.81;
  Viridithas c1bfc38 (2025-03-26, #244) same title (title only). Both engines first reduced null move more for a
  TT capture and ten months later disabled it for valuable TT captures (the card's rule); whether the reduction term
  still coexists is not visible (AGPL, source not read).
- S7 Stormphrax PR 310 "combo some previously-failed nmp patches" (merged 2026-04-01; commits "require static eval to
  be further above beta if not improving", "just throw some stuff in"): STC 8+0.08 [0,3] +1.31 +- 1.02, 142,518 g;
  LTC 40+0.4 +3.14 +- 2.16, 23,714 g. It shows NMP tweaks failing alone in that engine, but the TT-capture guard is
  not named among them - no counter-evidence for this rule.
- Stockfish: no commit about null move and a TT capture in the cached history 2016 .. 2026-10 (message scan); the
  rule is absent there (absence is not a failed test). No revert in Reckless or Viridithas titles to the cache date.
Closeness: S10 is the same trigger with a milder action. Effect: KEEP +1 to +3 and the gate slot. No overlap in the
lock: the card's Forge-fit grep shows its null-move condition has no hash-move term at all, so the milder form
(more reduction after a TT capture, S10) is a ready second variant if the skip is H0.

## 8. T04F-01 qsearch in check: stop after the first evasion that is not mated
- S11 Stockfish 95d7369 (2022-02-05) "Introduce movecount pruning for quiet check evasions in qsearch" (message:
  quiet evasions are rarely the good ones, captures preferred): STC [0,2.5] LLR 2.94, 58,800 g, +1.90 +- 1.45; LTC
  [0.5,3.0] LLR 2.95, 89,544 g, +1.54 +- 1.05. The strongest engine chose a softer form (prune only quiet evasions
  after a count), not "stop after the first non-mated evasion".
- S12 Stockfish de9fc53 (2020-04-13) "Removes evasionPrunable": non-regression {-1.50,0.50}, STC LLR 2.95, 25,656 g,
  +2.07 +- 2.59; LTC LLR 2.94, 43,732 g, +0.50 +- 1.62 - a guard on pruning evasions in qsearch was neutral and
  removed (form detail flat).
- Caissa (source): no revert of a677c89 in the cached titles; fbebb14 2026-03-20 "QSearch: Change move count
  pruning" (+1.79 +- 1.31, 8+0.08, n=73,680; title only) changed the related qsearch move-count rule later.
- No failed test of the exact cut found elsewhere.
Closeness: S11 = same family, milder action (quiet evasions only, after a count). Effect: KEEP +1 to +3 at the low
end and its last gate slot; if the Caissa form is H0, the Stockfish-like quiet-evasion count is the natural second
try (LTC-tested, about +1.5).

## 9. T04B-01 capture history in the SEE pruning threshold
- S6 Stockfish 5d72032 (2024-05-01) "Use capture history to better judge which sacrifices to explore" (capture
  history moves the SEE threshold of captures in the main-search pruning; message: a Stockfish developer "tried it a
  couple years ago in Stockfish without results", re-tried after another engine adopted it): STC [0,2] LLR 2.92,
  45,760 g, +2.51 +- 1.64; LTC [0.5,2.5] LLR 2.94, 243,828 g, +1.08 +- 0.67 (own pentanomial arithmetic).
  So: one earlier failed attempt (no log found) and a large-n LTC gain near +1 in a strong engine.
- Qsearch sibling (T04E-04), title only: aff1f67 2024-09-28 "simplify see pruning in qsearch" (STC ~+2.24, LTC
  ~+0.86) - a simplification of qsearch SEE pruning, not of the history margin itself.
Closeness: very close (capture history shifts the capture SEE-pruning threshold in the main search). Effect: LOWER
to +0.5 to +2.5: Stormphrax's +6.48 LTC was a DFRC-book, 10k-game result; the largest-n test of the same idea is
+1.08 at LTC; keep it in the gate list but behind T04E-03 / T04-02 / T04E-02.

## 10. T04E-03 quiet-move malus that shrinks with the move index
- S13 Stockfish a49b52c (2025-11-01) "Revert malus and associated coefficient parameters resulting from using only
  quiet moves" ("ultimately corresponds to the revert of #6200"; tuned on 60k LTC games): STC 10+0.1 [0,2] LLR 2.95,
  167,488 g, +1.06 +- 0.85; LTC 60+0.6 [0.5,2.5] LLR 2.99, 61,068 g, +2.12 +- 1.31; VLTC 180+1.8 non-reg, 50,380 g,
  +1.26 +- 1.37. A revert of a malus-scope change (quiet moves only), not of the move-count decay.
- S14 Stockfish e2fdf6f (2025-08-24) "Simplify separate malus formulas": non-reg [-1.75,0.25], STC 16,352 g,
  +5.23 +- 2.74; LTC 94,014 g, +0.53 +- 1.03 - two weeks after b177b73 "Separate bonus/malus parameters for quiet
  and capture moves" (STC ~+6.01, LTC ~+2.65, VLTC ~+0.10; title only): malus formula details are flat at LTC.
- a016abd's move-count decay: no simplify / remove / revert message mentions malus with move count in the cached
  history 2025-01-27 .. 2026-10 (message scan) - still alive there. Reckless 5e669a6 (#1038): no revert in the
  cached titles to the cache date.
- No failed test of the decaying malus found in another engine.
Closeness: S13 / S14 touch the same malus code but other parts. Effect: KEEP +1 to +3 and first gate slot (four
engines, both TCs, not removed anywhere); the flat formula details argue for one own setting, not a constant sweep.

## Table
| # | idea (card) | counter-evidence found (sources) | reverted / simplified in its own engine? | effect on the UNPROVEN estimate / gate order |
|---|---|---|---|---|
| 1 | rule-50 damping (T06-05) | none against the term; Stockfish simplified its form at zero cost and flattened the strength constant twice (S1); Patricia PR 153 neutral (on the card) | simplified, kept (Stockfish) | KEEP 0 to +3; gate one value only (flat optimum) |
| 2 | LMR re-search deeper / shallower (T04-02) | Stockfish: extra-deep step reverted for search explosions (S2), reintroduced, removed again; shallower form simplified at zero cost (S3); later gaining edits about +0.9 to +2.3 at LTC (one PV tweak ~+3.25, title only) | extra-deep variant reverted and removed; base kept in simplified forms (Stockfish); Caissa only dropped it at the root (on the card) | LOWER to +1 to +4; keep slot 2; the ply guard is mandatory, add mate / TB box tests |
| 3 | singular verification as a non-cut node (T04-01) | none found (message scan, one empty web search) | no (Caissa, to 2026-09; later singular work built on it) | KEEP 0 to +3; one-engine STC-only evidence; first in the singular bit-set |
| 4 | more LMR at cut nodes without a TT move (T04D-01) | Stockfish: a term of this family was simplified away and re-added at +1.01 +- 0.81 STC / +1.31 +- 0.86 LTC (188k / 140k games) (S4) | yes - simplified away, then reintroduced (Stockfish) | LOWER to 0 to +1.5; move down the gate order (after T04B-01 and T04F-01) |
| 5 | low-depth TT cutoff matching the node type (T04D-02) | Stockfish simplified the follow-up's depth limit at zero cost (S5); source LTC +1.02 +- 0.62 at 270,888 g | depth part simplified; rule kept (Stockfish) | LOWER top to 0 to +2; gate after T04D-01 is decided, not as a pair |
| 6 | lower singular beta at former-PV nodes (T04C-02) | Stockfish's 2020 form simplified away, re-added 2022 at LTC +1.04 +- 0.64 (236k) (S8); PlentyChess fixed a wrong ttpv in the excluded search four months after PR 286 (S9) | yes in Stockfish (2020 form simplified away, re-added); no in PlentyChess | LOWER the expected value to about +1 inside 0 to +3; keep it after T04-01 in the singular bit-set |
| 7 | no null move when the TT move captures a valuable piece (T04E-02) | none against; a milder form (more NMP reduction after a TT capture) passed first in Reckless (S10) and Viridithas; Stormphrax's failed-NMP combo does not include it (S7); Stockfish lacks the rule | no (Reckless, Viridithas titles) | KEEP +1 to +3 and slot 3; the lock's NMP has no hash-move term (card's grep), so the milder S10 form is the fallback variant |
| 8 | qsearch in check: stop after the first non-mated evasion (T04F-01) | Stockfish chose a milder form, move-count pruning of quiet evasions, +1.90 / +1.54 (S11); an evasion-pruning guard removed as neutral (S12); no failed test of the exact cut | no (Caissa); Caissa later changed its related qsearch move-count rule (title) | KEEP +1 to +3 at the low end; keep last; the Stockfish-like quiet-evasion count is the natural second try |
| 9 | capture history in the SEE pruning threshold (T04B-01) | Stockfish: an earlier attempt "without results", 2024 retry STC +2.51 +- 1.64 / LTC +1.08 +- 0.67 at 244k (S6) | no (Stockfish, to the cache date) | LOWER to +0.5 to +2.5 (Stormphrax's +6.48 LTC is a DFRC-book 10k-game run); keep slot 4 |
| 10 | quiet malus shrinking with the move index (T04E-03) | none against; Stockfish's malus revert (S13) and formula simplification (S14) touch other parts of the malus code | no (Stockfish, Reckless, to the cache dates) | KEEP +1 to +3 and slot 1; one own setting, no constant sweep (malus details are flat at LTC) |

Reverted or simplified away in its own engine (task item): T04D-01 (Stockfish: removed by a passed simplification,
then re-added at about +1); T04C-02 (Stockfish's 2020 form simplified away, re-added in another form in 2022);
T04-02 (Stockfish's extra-deep variant reverted for explosions and later removed; the base kept); T06-05 and
T04D-02 (forms or depth limit simplified, the idea kept). None of the ten was reverted outright in the card's source
engine within the cached histories.

Net effect on the gate order (proposal only, the crew decides): (1) T04E-03, (2) T04-02 with a hard ply guard,
(3) T04E-02, (4) T04B-01 then T04E-04, (5) T06-05, (6) singular bit-set T04-01 then T04C-02, (7) T04F-01,
(8) T04D-01 then T04D-02 (both moved down: their own engine shows about +1 at LTC). No estimate is raised.
Limits: failed fishtest / OpenBench runs are not in commit histories and fishtest has no keyword search here, so
"none found" means none in commit titles / messages / PR text of the cached histories and one web search per idea
where used; 14 sources read (cap 15).

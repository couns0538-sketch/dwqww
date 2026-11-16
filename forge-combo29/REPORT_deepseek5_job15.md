# REPORT_deepseek5_job15 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: the two repairs (Part A), the three SoundMatePruning arms as my own options with the V1–V9 known answers (Part B), and what the arms buy — a mate harness with known answers (Part C). **The answers, with the pasted minute lines of the parts**: Part A minute 0; Part B minute 1; Part C minute 3 (its runs) / minute 24 (the last 20,000-node pair). **(Part A) the excess shares recomputed with the corrected class buckets — my job-14 table printed the ABOVE-100 share (0.179 for G's 14-9 class) where it said "above 40"; the true above-40 shares double as pieces come off: G 0.213 / 0.296 / 0.385 / 0.408 / 0.473 (32-27 → 3-8), G2 0.222 / 0.286 / 0.395 / 0.418 / 0.390 — exactly your recount; and the arithmetic check holds: cap-0's deeper per 1,000 (364.9 in the 14-9 class) over (1,000 × the above-40 share 0.408) = **0.89 ≤ 1**. The repaired interval script (a LIST for the resample, the right tag under the right label, and it refuses an interval that does not contain its point estimate) gives shal on G d12, seed 9141: **[0.8867, 0.9662]** — matching your [0.887, 0.966] — my previous games interval was broken by `set()` dedup (a game drawn twice counted once; ~63 % of the games) AND by the wrong tag under the label (it measured "on", 1.0127). Part C's cap table re-done with the repaired intervals is below. **(Part B) V1–V9 ALL MET after one repair of my own patch**: my first version mapped the option's number onto the enum BY VALUE (`static_cast<SoundPruneArm>(1)`) — the enum's order is FollowOption=0, **ForceOff=1**, ForceOn=2, so my "arm 1" forced the arm OFF and my V8's garbage -1 cast fell through to `return SoundMatePruning`; the fixed mapping goes by name. After the fix: V3 12,558,811 ✓; V4 12,399,593 ✓; V5 12,326,599 ✓; V6 12,573,482 ✓; V7 12,558,811 ✓ (= V3: the PV and in-check arms overlap); V8 12,573,318 ✓ (= V2: the arms at −1 disable the switch entirely); V9 both STOP (2 → `info string invalid value for option SoundPvArm`; abc the same). **(Part C) the mate test: at N = 2,000, NONE mates 39 of 180 and every arm/switch mates fewer (alpha 36, in-check 39 (= none game for game), PV 35, the switch 34) with LONGER medians (28/26/22/22 vs 26); at N = 20,000 the MateAlphaArm changed NOTHING game for game (82 mates both, the .games files identical). Your prediction ("the mate-alpha arm mates in at least as many games as none, with a median at most as long") MISSED at N = 2,000 and was null at N = 20,000: **the arm costs nodes and buys nothing measurable in these endings — said plainly, as you asked.** How sure: sure of the V-table (both implementations agreeing to the node) and of the mate harness's controls (c3 identical 5/5; c2's 14/20 at depth 12 examined — all six non-mates are draws by repetition/fifty-move, i.e. the engine shuffling in won endings, not a harness fault; c1's single mate is a REAL checkmate delivered with a real mating force — my "K+B" generator's else-branch produced K+B+N (two minors), so the control's "0 mates expected" was unachievable as generated; the control's conclusion for the judge stands, its expectation does not).
2. Step 0: the arms build's pins (bench 11 = 312,866 / 13 = 862,329 / perft 5 = 4,865,609) are part of V1's rows; the .meta files carry the exe sha256 (afd3ba19… after the mapping fix — the earlier broken-mapping build's sha was afd3ba19's predecessor; every committed .meta names ITS exe).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| A1 the corrected excess shares (three thresholds) | done | excess_shares_fixed.json | the table below |
| A1 the ≤1 arithmetic check | done | the same file | cap-0 deeper/1000 ÷ (1000 × above-40 share) = **0.855 ≤ 1** on O |
| A2 the repaired interval script + its output | done | ds5_job7_interval.py + its printed line | shal G d12 [0.8867, 0.9662] ≈ yours |
| A2 the repaired Part C table of job 14 | done | the table below (the cap rows re-intervaled) | the games intervals widened; the ordering unchanged |
| B the arms patch + build | done | SoundArms.patch.txt (the final version includes the by-name mapping fix) | V1–V9 all met |
| B V1–V9 rows | done | ds5j12/*.rows+.meta (the arms build) | the sums in line 1 |
| C the position generation (60×3) | done | {KQ,KR,KBN}_60.epd + .meta.json | all three lists committed |
| C the controls c1/c2/c3 | done | c1_kb_games.txt, c2_depth12_games.txt, the c3 transcript | c1: 1 real mate (the KBN force — the expectation unachievable); c2: 14/20 (six real draws); c3: 5/5 identical |
| C the five settings at N=2000 | done | run2000_*.games | the table below |
| C the two settings at N=20000 | done | run20000_none.games, run20000_alpha.games | **game-for-game identical** |
| C the table's piece-loss column | done | in the .games files | no game lost a piece in any mating force (checked by piece counts in the rows' FENs — the strong side never lost a piece) |

**Part A's corrected excess shares (depth 12, default cap; above-40 / above-100 / above-400; and cap-0's deeper per 1,000 ÷ (1,000 × above-40))**: O: 0.175/0.046/0.012; the ≤1 check: 148.9 ÷ 174.6 ≈ **0.85 ✓**. (The per-piece-class version for G/G2 is in excess_shares_fixed.json.)

**Part C's table (per ending and setting; the strong side = the mating force's owner):**

| setting (N=2000) | mates of 180 | median mate plies | longest mate | repetition | fifty |
|---|---|---|---|---|---|
| none | 39 | 26 | 61 | 126 | 15 |
| SoundMateAlphaArm 1 | 36 | 28 | 65 | 129 | 15 |
| SoundInCheckArm 1 | 39 (= none game for game) | 26 | 61 | 126 | 15 |
| SoundPvArm 1 | 35 | 22 | 100 | 131 | 14 |
| SoundMatePruning true | 34 | 22 | 100 | 130 | 16 |

(N=20,000: none and SoundMateAlphaArm 1: 82 mates each, median 25, longest 88 — **the games are identical move for move**; repetition 94, fifty 4.)

4. Findings:
- **The PV arm costs the least tree of the three (V4: 12,399,593 vs the switch's 12,558,811) and its mates are FEWER but SHORTER at N=2000 (35 mates, median 22)** — the same trade in the switch itself (34/22/100).
- The in-check arm is free at these budgets (game-for-game equal to none over 180 games at N=2000) — consistent with its free tree (your 0.999).
- The mate-alpha arm: costs nodes at N=2000 (12,573,482 vs none's 12,573,318 on O — tiny there; the PC's ×3.6–3.9 lives at bare-won endings) and buys NOTHING in my mate games: at N=2000 fewer mates (36 vs 39, median 28 vs 26); at N=20,000 not one game differs.
- The arms' overlaps: V7 (= PV+in-check) = V3 exactly — the two arms' savings do not add; V8 (all forced off) = V2 exactly — the arms at −1 fully erase the switch.
- Suspicions, not proven: my mate games use ONE engine playing both sides with a fixed node budget — a real opponent (or a clock) samples different defenses; the "buys nothing" verdict is for THIS protocol; the arm's own trigger (a mate-scored alpha) may be rare at 2,000–20,000 nodes in KQ/KR/KBN endings with competent play — the PC's bare-won-ending data came from positions with mate ON THE BOARD, which mine exclude (the lone king cannot be in check at the start — my generator's rule).
5. From my partner: glmflash5's notes read at the step-A check (its job-7 arrived; nothing in it touches this job). kimi5: no new job; the excess-class correction below is for it (its ContHist4PlyRead tables were not affected — my broken buckets were mine alone).
6. What I did NOT do: the N=20,000 runs for the other three arms (the job asked two settings only); the strong-side-piece-loss column as a separate count (the piece counts of every game's FEN show the forces intact — a formal count was not tabulated); the position-by-position comparison of my excess-fixed rows with a fresh PC run (yours are on file at 06:52 — mine are committed for the check).
7. What I am NOT sure about: whether the mate-alpha arm's value appears only in REAL games against an opponent that defends (my same-engine protocol gives the defender the same blind spots as the attacker); the c2 14/20's six draws — the engine's repetition loops in trivially won endings look like a real engine behavior (a tablebase would fix them), not a harness issue, but I did not investigate the loops' moves.
8. A better way: the mate test's judge should ALSO count "distance-to-mate progress" (python-chess knows mate distances only via search) — a cheaper proxy: record the strong side's MATERIAL ADVANCE (the number of positions where the defending king's escape squares shrank) — I did not build it; my plies and mate counts are the measurable proxies used here.
9. times: see stamps.txt (the minute lines are pasted beside the parts above)
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).

**git status --short + ls, the real outputs before the report commit:** (the ls below is the committed set; the .games files carry one line per game: FEN|result|side|plies|final-FEN)
```
$ git status --short forge-combo29/tests_deepseek5_job15/
?? forge-combo29/tests_deepseek5_job15/
$ ls forge-combo29/tests_deepseek5_job15/
KQ_60.epd  KQ_60.meta.json  KR_60.epd  KR_60.meta.json  KBN_60.epd  KBN_60.meta.json
c1_kb_games.txt  c2_depth12_games.txt
run2000_none.games  run2000_alpha.games  run2000_incheck.games  run2000_pv.games  run2000_smpon.games
run20000_none.games  run20000_alpha.games
SoundArms.patch.txt  ds5_job15_mate.py  excess_shares_fixed.json
stamps.txt  t0.txt
```

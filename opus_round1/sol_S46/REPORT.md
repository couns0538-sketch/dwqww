# S46 Auto-promote rule replay simulator: DONE (opus, 2026-10-27)
Branch opus-sol-S46 (base d4f4312 + 0d99f02), head 09d88120. Tool job, no engine change; pushes [skip ci], no CI run.

## What was done
- `forge_sol_S46_promote_sim_20261027.py` (stdlib) replays timelines of gate/confirm/file events and writes a deterministic decision log,
  with a reason on every line. It mirrors the tick order of autopromote.ps1 896663b0:
  1. in-flight reconcile;
  2. rollback scan;
  3. chain scan (VOID never H1, WAIT_DATA, COMBINE_LIST);
  4. race-hold with the 12 h cap, confirm-Elo pick and pooled tie-break, RH-Q1/Q2/Q3, VOID-HOLD;
  5. 24 h spacing (CAP-LATE Z: waiver for the e48 re-gate only) and max 2 chained AUTO-LOCKs without CR;
  6. exe checks, Z-1, promote;
  7. race-loser re-gates (fresh srand, HELD_Z), Z-2;
  8. step-5 rebuild (4 per tick) or labels.
- Rules come from JSON:
  - `rules_voted_20261026.json`: 896663b0 plus the 18:05 N29 step-5 vote;
  - `rules_pc_896663b0.json`: the live script as written;
  - `rules_pre_fix_F41CF92F.json`: the pre-CRfix script.
- 27 fixtures from `make_s46_fixtures.py`, each with hand-written ordered `must`/`must_not` decisions, plus golden logs:
  (a)-(h); (i), (ii), (iii), (iv), (v), (v2 G104c H0), (v3 Z-1), (vi), (vii), (viii); step-5 suffix (the real `_ep20`/`_ep16` folders
  listed on the PC); RH-Q1, MED-2, QA CRfix G and H; no-running-gate; and the real 2026-10-25 replay.
- Also: tests, a profile/wrong-rule report, the real-replay compare tool, README_S46_20261027.md, IDEA_SOURCE.

## Evidence
| check | command | raw result |
|---|---|---|
| tests | `S46_SCRATCH=… python -I -B test_promote_sim.py` | Ran 9, OK (and under venv 3.10.22) |
| fixtures/golden | run_s46_evidence.sh step 1 | 27 fixtures regenerate identically; golden logs re-run byte-identically |
| profiles | `python -I -B s46_profile_report.py` | voted: 27/27 PASS. pc_896663b0: only s5 differs (`LABEL gate55_e20i… keeps old opponent h256_e12`, no alert). pre_fix: i, ii, iii, iv, v, v2, vi FAIL (also ii2, v3, viii, y, z, b1, e) |
| wrong rules | same | 23/23 caught (24h->12h, 2->3 chained, cap 12->6, VOID counts, no WAIT, no rival-off files, no in-flight record, no Z-1/Z-2, waiver for all, no VOID-HOLD, no RH-Q1, no MED-2 hold, 300-game window, no TL rollback, no COMBINE_LIST, exe-name step 5, 3 rebuilds per tick, edits without a running gate, empty status regex) |
| real replay | `python -I -B s46_real_replay_compare.py --real <copy of autonomy/autopromote.log> --sim <replay log> --start "2026-10-25 15:40" --end "2026-10-25 18:30"` | "real decisions 13, simulated 13: IDENTICAL" |

QA's scratch runs of the real script copies (lock archive race_pr/RHQ1, race_pr/CRfix) agree with fixtures x, e, vii, ii2, y/z and iv.

## Disagreements, simulator vs script/spec (all UNVERIFIED; detail in the README)
1. Spec "rollback on TL in the first 300 games" vs the script's rule 8 (any later game): the simulator follows the script; fixture c2.
2. Spec (b) "loser re-gate with no 24 h wait": that was the race-hold PR rule. CAP-LATE Z limits the waiver to the e48 re-gate; the
   script and the simulator follow Z.
3. Step-5 source folder: the script derives it from the exe name and silently keeps the old opponent (G55/G56 bug); N29 wants the
   manifest `src_dir` plus a SKIP with a loud alert. The default follows N29; the pc profile reproduces the bug. N29's tree-hash/net-md5
   checks are not modelled.
4. MED-5 (nan/missing Elo picks): open in the script; same behaviour in the simulator.
5. MED-6 (cap read from RESULT.md mtime): open in the script; the simulator uses the result time.
6. L2 (unanchored status regex): same as the script.
7. N-2 (PAUSE without expires): the simulator needs an explicit until-time.
8. Exe checks are simulated as pass unless a fixture fails them.
9. Lock kind: the simulator uses a fixture field instead of a tree diff.
10. Manifest-edit retries are not modelled.
11. Not modelled: fuzz, datagen switch, pins, export/zip, a second VOID re-run, a crash before the pointer write.

## Left
- Deploy N29 on the PC (CR); its hash/net-md5 checks are not simulated.

## UNVERIFIED
- All script behaviour not covered by the 13-decision real replay and QA's scratch runs: the PC script was never run.

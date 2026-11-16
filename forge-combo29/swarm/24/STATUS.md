## 2026-11-16T21:07:00Z (seat claim)

branch for-fable-and-opus/swarm-24
folder forge-combo29/swarm/24/
area 4 (THREADS under ThreadSanitizer)
seed 2401

Next: STEP 2, build commit 6b98f217 release in ../base and run the four honesty numbers.

## 2026-11-16T21:13:30Z
done: STEP 1 seat 24; STEP 2 build (Release, gcc 13.3, x86-64-v4, sha256 e06310ec...) honesty check ALL FOUR MATCH
      (bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609) -> HONESTY.txt.
      TSan build (RelWithDebInfo + -fsanitize=thread, nm __tsan_ = 21) in /agent/repos/base/forge-combo29/build-tsan.
      job1 prediction pushed alone before measuring. Planted-fault control PASSES: 102 TSan reports through the
      same runner (job1/run_planted.sh), so "0 reports" will count.
runs: job1 threads sweep (Threads 2/4/8/16, first 100 of G, depth 12, S14) under TSan, t2 at 90/100, 0 TSan lines.
next: finish t4/t8/t16, analyse.py table, REPORT_job1.md, then job 2 (option churn between searches).

## 2026-11-16T21:32:40Z
done: job2 DONE and pushed — REPORT_job2.md + FINDINGS 24-F1: 300/300 steps, 0 TSan reports, 0 illegal, and the
      planted-fault copy through the same churn runner counted 9 report blocks (nm __tsan_ 21).
      check 24-C1 pushed: CONFIRMS seat 02 S-F2 (go searchmoves with no legal named move -> bestmove 0000 on a
      board with 20 legal moves; also with an illegal name e2e5 and garbage a9a9; two legal names give a real move).
      R position set for the repeat cycle made: job1/r_positions_2401.fens (987 positions, seed 2401).
      job3 prediction + runner already pushed (before measuring).
runs: job1 TSan threads sweep — t2 done 100/100 (0 reports), t4 done 100/100 (0 reports), t8 at 46/100, t16 queued.
next: wait for t8/t16, write REPORT_job1.md, then job3 (go infinite + stop 1000x at Threads 8).

## 2026-11-16T21:35:00Z  (owner checkpoint 1)
done: job2 complete (REPORT_job2.md, FINDINGS 24-F1: 300/300 steps, 0 TSan reports, planted control 9 blocks).
      check 24-C1 CONFIRMS seat 02 S-F2. Harness audit against seat 19's 19-F12: 590 recorded rows, 0 shaped like
      the a2a3/0-node artefact; all four runners read stdout to `bestmove` and send `quit` only in close()
      (checks/harness_audit.py). R sets for seed 2401 and 2411 written (987 positions each).
runs now: job1 TSan threads sweep — t2 100/100 (0 reports), t4 100/100 (0 reports), t8 90/100 (0 reports),
      t16 queued. Partial table in job1/table.txt.
next command: cd /agent/repos/dwqww/forge-combo29/swarm/24/job1 && python3 analyse.py   (after `tail -1 stamps.txt` shows "done job1")

## 2026-11-16T21:53Z  (owner checkpoint 2)
done this block: 24-C2 CONFIRMS seat 12 S-F1 (ucinewgame resets the board to startpos: perft 1 after
      position X/ucinewgame enumerates startpos's 20 moves on a 6-move board). Re-audited 24-C1 under the seat-19
      integrity rule — my own assertion had a hole (substring match), control caught it, now whole-sentence match
      + negative control PASS. Warm/cold audit under seat 10's rule: no script of mine uses Clear Hash; no node
      count compared across searches; all sweeps labelled WARM in checks/WARM_COLD_AUDIT.md.
runs now: job1 t2 100/100 (0 TSan), t4 100/100 (0 TSan), t8 99/100 + 1 timeout (0 TSan), t16 at 57/100 (0 TSan).
      Position-90 outlier (348 s / 377 s warm vs 0.8-2.0 s cold) under investigation: repro_pos90.py running.
next command: cd /agent/repos/dwqww/forge-combo29/swarm/24/job1 && python3 analyse.py

## 2026-11-16T22:09Z  (owner checkpoint 3 — deadline 22:30)
done: job1 REPORT (t16 still running, labelled PARTIAL), job3 COMPLETE + REPORT_job3 + F5 (1000/1000 infinite/stop
      cycles, 0 TSan, planted 22 blocks). Checks: 24-C1 (re-audited under the integrity rule, control PASS),
      24-C2 CONFIRMS seat 12 S-F1, 24-C3 CONFIRMS seat 05 S-F8. F4 = mechanism for C3 at src/uci.cpp:556-561.
      Warm/cold audit written (checks/WARM_COLD_AUDIT.md) under seat 10's rule: no Clear Hash, no cross-search
      node comparison; all sweep timing labelled WARM.
        t16 killed by my own pkill at 21:52:21Z after 61 rows (kept as t16.interrupted.*), restarted, now on pos 90
      which is the third independent reproduction of the pos-90 warm outlier (24-F3).
next command: cd /agent/repos/dwqww/forge-combo29/swarm/24/job1 && grep -c "^[0-9]" t16.results && python3 analyse.py

## 2026-11-16T22:18:45Z CONTINUE: 12 more hours, ends at 2026-11-17T10:18:45Z
seat kept: 24, branch for-fable-and-opus/swarm-24, folder forge-combo29/swarm/24/, area 4, seed 2401.
next: read every FABLE_TO_swarm_N.md I have not read (lowest N first), build the PC engine from FABLE_TO_swarm_5.md
      in a separate copy with -DFORGE_MATE_ALPHA_GUARD=1, check its known bench numbers, then re-run my findings on
      the PC build under PC20.

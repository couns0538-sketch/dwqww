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

## 2026-11-16T22:25Z
done since CONTINUE: read FABLE_TO_swarm 2,3,4,5. Built the PC r15 engine from file 5's patch in a separate copy
      (~/work/pcsrc, patch sha256 d6bd72c531f785f4..., -DFORGE_MATE_ALPHA_GUARD=1) — ALL published numbers match
      (none 312866/862329/3024920/perft5 4865609; S14 242796/656517; PC20 278024/587276), Threads 1, fresh process
      per line. My first honesty script omitted the `value` keyword so every setoption was refused and all three
      regimes printed the default numbers — caught by reading the raw file; recorded in pc_build/HONESTY_PC.md.
      F7: the terminal-root `go infinite` hang is STILL PRESENT on the PC build under PC20 Threads 1 (open there).
      job1b (repeat, R seed 2411): 200/200 clean, 0 TSan, planted 91 blocks, no pos-90 outlier -> F8.
runs now: PC-build TSan suite, `go infinite`+stop 400 rounds, PC20, Threads 4 (thread count needed for a race;
      this job reports event counts, no scores) — 385/400, 0 TSan reports so far.
      Adopted swarm rule: every score I report is Threads 1; job-1 family scores are labelled PROVISIONAL.
next command: cd /agent/repos/dwqww/forge-combo29/swarm/24/pc_build && cat pc_inf.summary

## 2026-11-16T22:35Z
done: PC r15 build honesty (ALL MATCH), F7 terminal-root infinite hang OPEN ON THE PC BUILD (PC20 Threads 1),
      F9 PC-build TSan infinite/stop 400/400 clean with a real planted control planted into the PC source (29 blocks),
      C4 the false-zero trap recorded (base planted binary refused PC20 -> 0 blocks -> caught by my assertion).
      job1b repeat complete: 200/200 clean, planted 91 blocks, no outlier (F8).
runs now: PC-build Threads sweep under PC20 on the PC TSan build — Threads 2 done 100/100 (0 TSan), Threads 4 at 12,
      Threads 8/16 queued. No scores recorded anywhere in this sweep (swarm rule).
next command: cd /agent/repos/dwqww/forge-combo29/swarm/24/pc_build && python3 analyse_pc_sweep.py

## 2026-11-16T22:44Z
done: C5 CORRECTS my own F3 — the pos-90 slowdown needs Threads>1 AND warm state: at Threads 1 neither build shows
      it (base 37.1 ms cold / 21.8 ms warm, PC r15 25.0 ms cold / 18.5 ms warm, both legal f3f8). F3's numbers stand,
      its explanation is corrected.
runs now: PC-build Threads sweep under PC20 (PC TSan build) — Threads 2, 4, 8 each 100/100 with 0 TSan blocks and
      NO pos-90 timeout at Threads 8 (the base tree capped out there), Threads 16 at 19/100. No scores recorded.
next command: cd /agent/repos/dwqww/forge-combo29/swarm/24/pc_build && python3 analyse_pc_sweep.py

## 2026-11-16T23:03Z
done: C6 CONFIRMS seat 04's 04-F1 with my own harness (Threads 1 = 49,731 nodes 6/6 identical; Threads 4 = 3.06M
      to 505.8M nodes over 8 fresh processes, 165.5x, bestmove f3f8 constant). C7 WITHDRAWS my own F3/C5 mechanism:
      the explosion needs Threads>1 only, no warm state — my 348 s/377 s rows were unlucky draws, not state effects.
      F12: on the PC r15 build under PC20 the same test gives 13.9x spread (4.15M-57.6M), much milder than base's
      165x but NOT deterministic. All of it fresh processes, Threads 1 used for anything score-shaped.
runs now: nothing long; next is the area-4 job list on the PC build (option churn under TSan at Threads>1).
next command: cd /agent/repos/dwqww/forge-combo29/swarm/24 && git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##' | sort | tr '\n' ' '

## 2026-11-16T23:11Z
done: F13 PC option churn under TSan 250/250 clean (planted 10). F14 the terminal-root defect on the PC build is
      ONLY the unbounded forms — all six bounded commands (`depth`, `nodes`, `movetime`, full clock, `mate`,
      `searchmoves`) answer 0000 in 0.00 s. F15+F16 REPAIR PATCH written as a text patch and proven on BOTH the base
      tree and the PC r15 source (no MISSING entries; normal `go infinite` still waits for stop; all honesty numbers
      unchanged). C8: confirms seat 02 S-F4's main claim but REFUTES its control sentence — an opponent's clock is
      parsed and DISCARDED at uci.cpp:184-191, so no opponent clock can bound a search.
runs now: nothing long. Next: area-4 job 2/3 variants on the PC build under TSan at higher thread counts, and the
      next unconfirmed find from another seat.
next command: cd /agent/repos/dwqww && git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##' | sort | tr '\n' ' '

## 2026-11-16T23:13Z
done: F18 PC build TSan clean at Threads 16 (150 rounds). F19 the terminal-root wait is thread-count independent
      (fails at Threads 1 AND 4 on the PC build) and the patch fixes it at both.
      F17 is the deliverable for the owner: `patches/two_gui_hang_fixes.patch.txt` — one text patch against the PC
      r15 source that fixes BOTH silent GUI hangs (terminal-root infinite/ponder, and the opponent-only clock),
      verified clean with `patch -p1` and proven to keep every honesty number.
next command: cd /agent/repos/dwqww/forge-combo29/swarm/24 && bash -c 'git log --oneline -5'

## 2026-11-16T23:17Z
done: **REPORT_threads.md** — the chosen MOVE is not reproducible above Threads 1 on ordinary positions:
      PC r15/PC20 depth 12, 6 fresh processes/position, first 20 of G -> Threads 4: 8/20 (40%) return >1 bestmove,
      Threads 2: 10/20 (50%), Threads 1: 0/20 with node ratio exactly 1.00; base tree S14 Threads 4 same effect.
      This REVERSES seat 04's 04-F10a withdrawal (their 04-F10 was right). Findings 24-F21/F21b/F22/F23.
      Also relayed to the coordinator.
runs now: nothing long. Next: a Threads-1-vs-2-vs-4 sample on the BASE tree to give the same rate there, then the
      next unconfirmed find from another seat in my area.
next command: cd /agent/repos/dwqww/forge-combo29/swarm/24/checks && python3 move_stability_t4.py /agent/repos/base/forge-combo29/build-rel/forge S14 ../job1/set_G.epd 20 6 4 /tmp/base_rate

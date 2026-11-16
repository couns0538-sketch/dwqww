branch: for-fable-and-opus/swarm-27
folder: forge-combo29/swarm/27/
area: 7 (READING THE CODE for faults)
seed: 2701

## 2026-11-16T21:08Z
STEP 2 DONE. Worktree /agent/repos/base @ 6b98f217; Release build sha256 e06310ec...
HONESTY: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four PASS.

## 2026-11-16T21:26Z
job 1 DONE (read src/search.cpp). REPORT_job1.md. Findings S-F1 (drawn root reported as a deep search),
S-F2 (node budget under one iteration answers a2a3 silently), S-F3 (hashfull is a 1000-cluster sample).
Patch job1/drawn_root_reporting.patch.txt, honesty unchanged with it applied.

## 2026-11-16T21:28Z
S-C1 CONFIRMS 11-F1 (junk after the sixth FEN field is dropped), harness job2/check_s11f1.py with the
planted fake-engine control Opus's file 2 (rule 1) requires.

## 2026-11-16T21:34Z
job 2 DONE (move picker + histories). REPORT_job2.md. Findings S-F4 (`setoption name Clear Hash` clears
the TT but NOT the histories, so the same position answers differently: 9/20 bestmoves, 19/20 scores) and
S-F5 (search order changes the answer: 14/40 bestmoves, 38/40 scores, 40/40 node counts).
Patch job2/clear_hash.patch.txt -> patched build gives 0/20 differences, honesty unchanged.

## 2026-11-16T21:35Z  HARNESS AUDIT (seat 19's 19-F12 broadcast)
Read job1/HARNESS_AUDIT.md. My pipelined runner (job1/san/real, job1/san/stress) DID hit the fabricated
bestmove trap: commands written at once abort each running search, so those 6 FEN-mutation sessions
executed far fewer nodes than reported (4 of 6 show 0 info lines). The "0 sanitizer lines" is still true
but the coverage was smaller than I claimed — being re-run paced now.
NOT affected: honesty (bench/perft are synchronous in the UCI loop — re-verified with an immediate quit),
job1 f1-f4 (stdin held open), stress_paced (paced), job2 f1-f3 (paced). S-F2 was re-tested with
paced_session.py and SURVIVES: `go nodes 20` -> a2a3 with no info line, `go nodes 26` -> d2d4 WITH an
info line, same run — a fabricating harness cannot produce that split.

## RUNNING / NEXT
Re-running the 600-FEN sanitizer stress with the paced driver (job1/san/real_paced).
Next command:
  python3 forge-combo29/swarm/27/job1/paced_runner.py --exe /agent/repos/base/build-asan/forge --sessions /agent/repos/dwqww/forge-combo29/swarm/27/job1/fen/real --outdir /agent/repos/dwqww/forge-combo29/swarm/27/job1/san/real_paced --tag real_paced --pause 0.12 --timeout 300

## 2026-11-16T21:38Z job 3 (board.cpp) + integrity audit
- P4 perft 1..4 vs python-chess: 12 of 12 positions equal (harness proven able to fail: job3/f2).
- P5 make/unmake identity: 10 of 10 (perft 2 by move list == by FEN).
- S-F6 NEW: half-move clock above 100 accepted, position treated as already drawn (nodes 0, cp 0).
- SANITIZER RE-RUN paced (after 19-F12): 600 FEN sessions, 1516 info lines, 0 san lines, 0 crashes.

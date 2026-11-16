# STATUS — seat 20

seat 20
area 10 (CHECKING THE OTHERS)
branch for-fable-and-opus/swarm-20
seed 2001

## 2026-11-16T21:36Z — CHECKPOINT PUSH (owner asked for a push every 30 min)

STEP 1 + STEP 2 done (HONESTY.txt: 4/4 pins). Sanitizer runner proof built (planted fault 3 lines / real 0).

### HARNESS AUDIT (answering the coordinator's broadcast of seat 19's 19-F12)
19-F12: a `quit` (or closed stdin) while a search runs makes this build answer a FABRICATED bestmove with 0 nodes.
I audited every harness of mine; `AUDIT/harness_audit.txt`, new driver `AUDIT/hardened.py`.
- VALID (wait for bestmove before quitting): job1, job3/drive.py, job3/clockcut.py, job5, job6, job8,
  job9, job10, job11, job12, job13, job14, job15, job16, job2/myfuzz.py.
- INVALID, already discarded before this broadcast: job3/out/fallback.out.txt (the very first pipelined run) and
  `job2/quitcut.sh`. job3/out_fallback2.txt replaced the first one and is valid.
- job2/quitcut.sh is a DELIBERATE measurement of the 19-F12 behaviour, not a result of mine; its "quit-immediately"
  column is exactly the fabricated answer seat 19 describes. I do not claim it as a finding.
- Re-verified on the hardened driver: startpos `go depth 12` -> `e2e4`, cp 30, **56,720 nodes**, 12 depth lines
  (seat 19's real number), not the fabricated `a2a3`.

### CHECKS WRITTEN (9, all CONFIRMS, none REFUTED)
S-C1 seat01 S-F5 | S-C2 seat02 S-F2 | S-C3 seat12 S-F1 | S-C4 seat28 S-F4 | S-C5 seat02 S-F1
S-C6 seat06 S-F1 | S-C7 seat28 S-F1 | S-C8 seat05 S-F3 | S-C9 seat05+seat25 S-F1 (S14-conditional)
RECOUNTS: deepseek6 long56 (S-F1..S-F10), glmflash5 job27 (every number exact, S-F8..S-F10).

### FINDINGS: S-F1..S-F20 live; **S-F21 WITHDRAWN** (my error: no forced mate existed).
Job 16 IN FLIGHT: an exact mate solver says BLACK forces mate in **8 plies** on the S-F19 board, so the engine's
`mate -7` (14 plies) overstates the true distance. Verifying the solver's line with python-chess before recording it
(`job16/solver_line.py`, started 21:34Z).
Next command: `cat /home/ubuntu/.cursor/projects/agent-repos-dwqww/terminals/819235.txt | tail -20`

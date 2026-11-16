# STATUS — seat 20

seat 20
area 10 (CHECKING THE OTHERS)
branch for-fable-and-opus/swarm-20
seed 2001

## 2026-11-16T21:20Z
STEP 1 done (SEAT.txt). STEP 2 done: 4/4 honesty pins match (HONESTY.txt).
job2 DONE (recount deepseek6): REPORT_job2.md; findings S-F1..S-F6 in FINDINGS.md.
Also built the sanitizer-runner proof: planted-fault copy reports 3 sanitizer lines, real ASan build 0
(job3/plant_build.sh, job3/sanrun.sh, job3/out/{planted,clean}.meta). ASan build pins match too.
job3 IN PROGRESS: a lead of my own — `go nodes 1` and a `quit` arriving during a search both return the
FIRST LEGAL MOVE with zero `info depth` lines (job3/out_drive1.txt, job3/out_clockcut_bookoff.txt).
Clocked searches (wtime/movetime) are clean; the startpos cases were the opening book, not a fault.
Next command: bash forge-combo29/swarm/20/job3/fallback2.sh

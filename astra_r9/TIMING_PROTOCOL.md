# Timing protocol (declared before candidate measurements)

Native production LTO+PGO only, fixed d20 nodes 12389307, Threads=1, Hash=16,
Idle, logical CPU 2. Every timed invocation is a fresh engine process with d16
warmup (3024920 nodes). Engine-reported milliseconds/NPS and outer elapsed time
are retained. Both binaries use the same settings, except B enables NNUEWideOutput.

First four ABBA-shaped A/A control blocks (16 runs, eight adjacent alternating
pairs), then ten true ABBA blocks (40 runs, twenty alternating pairs). Pre-block
3-second utilization on CPU 2 and its selected sibling CPU 3 must both be <30%;
otherwise wait. Other running training/gates/self-play are never disturbed.

Each pair uses B/A - 1. Report median, min/max and inclusive-quartile IQR for NPS
and paired percent gains. All rows and logs retained. Predeclared A/A stability:
absolute median paired bias <=0.75 percentage points and IQR <=3 points.
Candidate speed gate additionally requires median paired gain >=1%.
Every timed run also records process user+kernel CPU seconds / wall seconds and
CPU 3 utilization across that run. CPU/wall <0.95 or sibling utilization >=30%
marks interference. Any such row makes the whole experiment inconclusive; all
rows remain in the table and statistics. No concurrent owned builds or checks
run during timing. These limits supplement, not replace, A/A controls.
If controls fail or environmental interference is evident, classify inconclusive;
do not selectively remove slow runs. A fresh full experiment can be separately
recorded if the resource window improves within the task deadline.

Timing is ADVISORY. Engine QA owns official timing. Elo is UNPROVEN.

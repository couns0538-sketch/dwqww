# Approved execution plan

Goal: exact NNUE speed on FD3A5190, at least 1% advisory median paired gain; no Elo claims.

1. First 45 minutes: isolate worktree, hash source and lock, profile actual lock before engine edits, locate corpus, verify sanitizer feasibility.
2. Up to four hours: profile-supported refresh cache first, exact integer/VNNI second, alignment/load/AVX-512 float third. Independent default-off switches. Preserve fixed float arithmetic order unless exact representability is proven. One candidate at a time.
3. Every candidate: v2.3 -Expose znver5 LTO+PGO twice with identical executable SHA256, all OFF/ON pins, perft, 10k+ legal FEN bit equality, incremental edge cases, T1/T4 legal smoke, ASan+UBSan short self-play. Two repeated failures stop a variant; any OFF pin mismatch invalidates build.
4. Frozen candidate review before expensive validation and at completion; fix confirmed issues and record each milestone in both ledgers.
5. A/A then 10 full ABBA blocks on one quiet Idle CPU; d20, Threads=1, Hash=16, identical nodes. Medians, IQR, min/max, paired gains, complete raw table. Timing ADVISORY.
6. Meaningful commits/pushes about every 15 minutes. Final report and QA line only for fully qualified gain. Report blockers honestly otherwise. No gates or matches.

Safety: D:\a9 only, <=10 GB, C >=30 GB and D >=50 GB free, no GPU, no modifications to other jobs/queues/branches. Idle long jobs, BelowNormal otherwise, <=2 threads except approved brief T4 smoke on two logical CPUs. Never overwrite retained evidence/executables. Deadline includes waits.

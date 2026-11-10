# opus_smp_layout — COMMANDS (EXECUTED vs PREPARED-ONLY)

Run every command from Git Bash: PS 5.1 engine drivers started from an agent's PowerShell tool never see stdin. Each tool pins itself to CPUs 12-15 (mask 0xF000) at Idle, reads both back and fails closed. TEMP/TMP = `D:\forge_jobs_20261107\opus2\tmp`.
`ps1` = `MSYS_NO_PATHCONV=1 powershell.exe -NoProfile -ExecutionPolicy Bypass -File`, `T` = `D:\forge_jobs_20261107\opus2\repo\opus_smp_layout\tools`, `O` = `D:\forge_jobs_20261107\opus2\out`. Exes: `$O\exe\forge_P_4181a589.exe` (= OFF build = trial_w6) and `$O\exe\forge_smpgate_541e8b3d.exe` (final gate).

## EXECUTED
```
# sources: git archive <commit> include src -> $O/src/{p,s0f,s1f}; s1f = s0f with '#define FORGE_SMP_LAYOUT 0' -> 1 (one line)
ps1 $T\kit_build.ps1 -SrcDir $O\src\p   -Tag p1   (and p2)                              # = 4181a589
ps1 $T\kit_build.ps1 -SrcDir $O\src\s0f -Tag s0c  (and s0d)                             # = 4181a589
ps1 $T\kit_build.ps1 -SrcDir $O\src\s1f -Tag s1c  (and s1d) -CheckOpt 'TtLockless=true' # = 541e8b3d, ON identity ALL OK
ps1 $T\pp_identity.ps1 -TreeA $O\src\p -TreeB <repo at 0599271> -OutDir $O\pp\fix1_macro0 # 8/8 IDENTICAL
# native tests, each one g++ line through run_pinned.ps1 (-std=c++20 -O2 -DFORGE_SMP_LAYOUT=1 ... -march=znver5 -static):
fix1_tt_lockless_tests.exe (x4) ; fix1_smp_lifecycle_tests.exe (x3) ; fix1_tt_coherence_tests.exe
# layout: g++ -O2 ... -Iinclude $T/layout_probe.cpp <7 core units> for P (macro 0) and the s1f tree (macro 1)
# L3 cold 12k and L3b warm 1000 (net on/off; options as listed in logs/l3/L3_summary.txt and logs/l3b/L3b_summary.txt)
ps1 $T\identity_check.ps1 -Exe <exe> -Tag <tag> -Mode cold -OutDir $O\id [-Options 'TtLockless=true;UseNNUE=false']
ps1 $T\identity_check.ps1 -Exe <exe> -Tag <tag> -Mode warm -OutDir $O\id -Count 1000 [-Options 'TtLockless=true']
ps1 $T\liveness_check.ps1 -Exe $O\exe\forge_smpgate_541e8b3d.exe -OutDir $O\live
# stress, Threads 1/4/8 (8 = oversubscribed smoke on 4 logical CPUs)
ps1 $T\uci_lifecycle_stress.ps1 -Exe <gate> -Tag gateF_OFF[_long] -OutDir $O\stress -ThreadSet '1,4,8' -Cycles 300|2000 [-Seed 7]
ps1 $T\uci_lifecycle_stress.ps1 -Exe <gate> -Tag gateF_ON[_long]  -OutDir $O\stress -ThreadSet '1,4,8' -Cycles 300|2000 [-Seed 7] -Options 'TtLockless=true'
# advisory nps (P, A/A copy of P, gate OFF, gate ON)
ps1 $T\nps_smoke.ps1 -ConfigFile $O\nps\configs.tsv -OutDir $O\nps -Tag F_T1_nodes    -Threads 1 -Mode nodes -Nodes 1000000 -Rounds 8
ps1 $T\nps_smoke.ps1 -ConfigFile $O\nps\configs.tsv -OutDir $O\nps -Tag F_T4_nodes    -Threads 4 -Mode nodes -Nodes 2000000 -Rounds 8
ps1 $T\nps_smoke.ps1 -ConfigFile $O\nps\configs.tsv -OutDir $O\nps -Tag F_T4_movetime -Threads 4 -Mode movetime -MoveTime 1500 -Rounds 6
# CI (GitHub Actions opus-ci on push; Linux g++-14): run_ci.sh {release,asan,tsan} + opus_round1/opus2_smp/tsan_extra.sh
gh run view <id> ; gh run download <id> -D $O/ci/r<id>      # ids 42673707949 42674616047 42677341394 42682884789
```

## PREPARED-ONLY (not run by this job)
```
# QA native-core scaling (SCALING_PLAN.md): one logical CPU per core, quiet PC, Threads 1/2/4/8, P vs gate OFF vs gate ON.
#   This job's tools allow only mask 0xF000; QA widens $script:OspdAllowedMask in o2_uci_lib.ps1 for its own allocation.
ps1 $T\nps_smoke.ps1 -ConfigFile <P/G-off/G-on tsv> -OutDir <qa dir> -Tag T8_movetime -Threads 8 -Mode movetime -MoveTime 5000 -Rounds 7 -FenCount 32 -Mask 0x5555
# Threads 1/4/8 lifecycle stress on native cores (QA), longer:
ps1 $T\uci_lifecycle_stress.ps1 -Exe <gate> -Tag qa_on -OutDir <dir> -Options 'TtLockless=true' -ThreadSet '1,4,8' -Cycles 20000 -Mask <QA mask>
# Linux TSan by hand on any x86-64 box: bash opus_round1/ci/run_ci.sh tsan ci_out
```

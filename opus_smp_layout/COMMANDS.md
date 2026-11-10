# opus_smp_layout — COMMANDS (EXECUTED vs PREPARED-ONLY)

Run every command from Git Bash: PS 5.1 engine drivers do not see stdin when started from an agent's PowerShell tool. The tools pin themselves to CPUs 12-15 (mask 0xF000) at Idle, read both back and fail closed. TEMP/TMP point to `D:\forge_jobs_20261107\opus2\tmp`. `T=D:/forge_jobs_20261107/opus2/repo/opus_smp_layout/tools`, `O=D:/forge_jobs_20261107/opus2/out`.

## EXECUTED
```
# parent P, OFF and GATE kit builds (QA kit v2.3 Idle copy; each pair pc1/pc2 compared by sha256)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T/kit_build.ps1 -SrcDir $O/src/p  -Tag p1   # and p2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T/kit_build.ps1 -SrcDir $O/src/s0 -Tag s0a  # and s0b
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T/kit_build.ps1 -SrcDir $O/src/s1 -Tag s1a -CheckOpt 'TtLockless=true'   # and s1b
#   $O/src/p, s0, s1 = 'git archive <commit> include src'; s1 = s0 with '#define FORGE_SMP_LAYOUT 0' -> 1 (exactly one line)
# macro-0 preprocessing identity
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T/pp_identity.ps1 -TreeA $O/src/p -TreeB <repo> -OutDir $O/pp/wip1_macro0
# layout of P
g++ -std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude \
    $T/layout_probe.cpp src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp -o P_layout_probe.exe   # via run_pinned.ps1
# native tests (macro 1), each built with one g++ line through run_pinned.ps1:
#   -std=c++20 -O2 -DFORGE_SMP_LAYOUT=1 -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude
#   tests/<test>.cpp src/{bitboard,board,book,eval,eval_params,nnue,search}.cpp -static
tt_lockless_tests.exe ; smp_lifecycle_tests.exe ; tt_coherence_smp1.exe
# CI (GitHub Actions opus-ci on push): opus_round1/ci/run_ci.sh {release,asan,tsan} with -DFORGE_SMP_LAYOUT=ON
#   and -DFORGE_SPD_NNUE_ZMM=0; tsan mode also runs opus_round1/opus2_smp/tsan_extra.sh
gh run view 42673707949 ; gh run download 42673707949 -D $O/ci/r42673707949
# L3 cold 12k (go depth 13, ucinewgame each, OwnBook false), net on and off:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T/identity_check.ps1 -Exe <exe> -Tag <tag> -Mode cold -OutDir $O/id [-Options 'UseNNUE=false'] [-Options 'TtLockless=true;UseNNUE=false']
```

## PREPARED-ONLY (not run by this job)
```
# Threads 1 / 4 / 8 lifecycle stress on a quiet machine with native cores (QA): the same driver, another mask
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $T/uci_lifecycle_stress.ps1 -Exe <gate exe> -Tag qa_on -OutDir <dir> \
  -Options 'TtLockless=true' -ThreadSet '1,4,8' -Cycles 2000 -Mask <QA mask>      # needs OspdAllowedMask widened by QA
# native-core scaling: SCALING_PLAN.md (P vs gate OFF vs gate ON, Threads 1/2/4/8, one logical CPU per core)
# Linux TSan by hand (any x86-64 Linux box): bash opus_round1/ci/run_ci.sh tsan ci_out
```
(The EXECUTED list grows with the stress, warm, liveness and NPS runs. Final commands and logs are in BENCH.md section 5/6.)

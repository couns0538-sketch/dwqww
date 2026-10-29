# opus_r5/r5b: N2 speed build (O2 + NOZERO + SPEEDSTACK) and a reproducible NPS bench

Branch `opus-r5b-speed` (base `forge-bundle-int` b7c1772). Results: `REPORT.md`; gate proposal: `N2_PROPOSAL.md`.
All commands run from the worktree root in Git Bash (MSYS2), at BelowNormal, <= 3 threads.

## Build
```
RECIPE=znver5 bash opus_r5/r5b/tools/build_r5b.sh "$PWD" /f/opus_scratch/r5/r5b/exe/<name>.exe [-D switches]   # PC lock recipe
RECIPE=v3     bash opus_r5/r5b/tools/build_r5b.sh "$PWD" /f/opus_scratch/r5/r5b/exe/<name>.exe [-D switches]   # job-spec flags
bash opus_r5/r5b/tools/build_m3.sh "$PWD" <tag>     # NOZERO, SPEEDSTACK, N2 for both recipes + identity
```
N2 = `-DFORGE_NNUE_O2=1 -DFORGE_NOZERO_MOVE_BUFFERS=1 -DFORGE_SPEEDSTACK=1`. Identity: lock
`2_build/uci_check.py <exe> --full` (must print ALL OK).

## Which NNUE kernel is in an exe
```
bash opus_r5/r5b/tools/nnue_kernel_audit.sh <exe>...       # objdump counts of zmm/ymm add/sub and stores per function
printf 'uci\n' | <O2 exe>                                  # O2 builds print: info string nnue kernel: accumulator ..., output ...
RECIPE=znver5 bash opus_r5/r5b/tools/parity_r5b.sh "$PWD" <out_dir> <name> -DFORGE_NNUE_O2=1   # bit parity vs AL1 s198
```

## NPS A/B (M2)
```
bash opus_r5/r5b/nps_ab.sh --a OFF.exe --b X.exe [Y.exe ...] --names x,y --aa --depths 16,20 --pairs 20 \
     --copies 20 --core 14 --pins 16=3024920,20=12389307 --copy-dir <scratch dir> --json out.json \
     [--stop-file F:/opus_scratch/r5/r5b/r5b_nps_stop.flag]
python -I -B opus_r5/r5b/nps_table.py out.json [more.json]     # markdown rows
```
PowerShell: `& C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe -I -B opus_r5\r5b\nps_ab.py --a ... --b ...`.
The driver pins itself (and so every engine) to one logical CPU and runs BelowNormal; primary figure = CPU-time NPS
from QueryProcessCycleTime; `--aa` adds the A/A control (byte copy of A). Exit 2 on any node mismatch.
On the PC keep `--copies` = `--pairs`: every slot then runs fresh byte copies, so the per-file speed offsets
(ASLR image base / page placement, up to about +-2.8 % at d16 in R5B passes 1-2) are sampled into the CI.

## Non-regression evidence (M4)
```
python -I -B opus_r5/r5b/m4_nodeexact.py --a OFF.exe --b N2.exe --fens tests/data/nnue_selfplay_sample_916.txt \
       --count 50 --depth 18 --out <dir> --label n2_z5
python -I -B opus_r5/r5b/smoke_ab.py N2.exe --exe-off OFF.exe --name n2_z5 --expect-echo none --out <dir>   # 200 games 5+0.05
```
Test hook: `-DFORGE_R5B_POISON_MOVE_BUFFERS=0xFE` fills the NOZERO move buffers with a byte pattern (test builds only).
CI: `.github/workflows/opus-r5b-n2.yml` (N2 release/ASan+UBSan/TSan, the singles release + CTest, N2 x86-64-v4 on an
AVX-512 runner, valgrind memcheck + poison identities via `ci_n2_memcheck.sh`).

# KING_LINES on trial_w6 - STATUS

The owner follow-up brief (2026-11-06, after the 5-hour brief) asks for these steps:
1. rebase onto trial_w6 on a new branch;
2. build; pc1 = pc2 identity; every lock pin with the switch OFF; perft;
3. the full 12k bitexact check with the switch ON, net on;
4. the same, net off.

Commit + push after every step. No exe, lock, queue or gate file is touched. This is not a lock.

## Done
### Step 1 - rebase (this commit)
- `D:\opus_5h\king_lines\src\kl` = a trial_w6 copy + `opus_speed/patches/b4_king_lines_after_w8.patch` (d680f9bf), the
  committed KING_LINES-only patch.
  - It applies cleanly (`patch -p1 -F0`, with a dry run first).
  - board.hpp and board.cpp now equal `F:\ospd\src\trial_w9`'s.
  - It differs from trial_w6 only in those two files.
- `king_lines_after_w6.patch` (md5 70d69d8a): apply-proof on a fresh trial_w6 copy gives an identical tree.
- `tools/pp_identity.sh` with switch 0, the lock flags and the six lock switches: IDENTICAL in all 8 units.
- Control trees from `tools/port_controls.sh`:
  - `kl_id`: six lock flips, FORGE_SPD_KING_LINES 0;
  - `kl_gate`: six + FORGE_SPD_KING_LINES 1 (the ON build).

## In progress
Step 2: LTO+PGO builds of kl_id and kl_gate (lp_v1 -Twice).

## Exact next step
1. Check kl_id: pc1 = pc2, and both must be 4181a589.
2. Check kl_gate: pc1 = pc2.
3. Run pin_check (full) on both exes, plus the net-off pins and perft.
4. Then step 3: `bitexact_check.ps1 -Cand <ON exe> -Out D:\opus_5h\king_lines\bx_on_neton -SkipSan`.
5. Then step 4: the same with `-FenOptions UseNNUE=false`.

## Resume commands
```
cd /f/ospd/wt && git checkout opus-king-lines-20261106
bash opus_king_lines/tools/pp_identity.sh /f/ospd/src/trial_w6 /d/opus_5h/king_lines/src/kl
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'F:\ospd\wt\opus_speed\tools\build_variants.ps1' \
  -SrcDir 'D:\opus_5h\king_lines\src\kl_gate' -Tag kl_gate -Variant lp_v1 -Twice -Work 'D:\opus_5h\king_lines\builds'
```

## Unproven / not claimed
- Not a lock.
- **No speed claim:** there is no ABBA; QA owns it.
- **Not run in this brief:** L3b warm_identity, the Threads 2-4 soak and the deep-ply stress. They were in the original
  job-4 text, but the owner's follow-up asks only for steps 1-4.

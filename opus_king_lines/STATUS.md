# KING_LINES on trial_w6 - STATUS

The owner follow-up brief (2026-11-06, after the 5-hour brief) asks for these steps:
1. rebase onto trial_w6 on a new branch;
2. build; pc1 = pc2 identity; every lock pin with the switch OFF; perft;
3. the full 12k bitexact check with the switch ON, net on;
4. the same, net off.

Commit + push after every step. No exe, lock, queue or gate file is touched. This is not a lock.

## Done
### Step 1 - rebase (commit 343d1da3)
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

### Step 2 - builds, identity, pins, perft (logs commit 7b523fd5)
- **OFF build** `kl_id` (lp_v1 -Twice): pc1 = pc2 = **4181a5893f15e732...** = trial_w6, byte for byte.
- **ON build** `kl_gate` (lp_v1 -Twice): pc1 = pc2 = **44fd0137e7aa48e62302ef88145c5cbc353b1ebc4a0b6f4147f3a729199c14fb**.
- **Copies:** `D:\opus_5h\king_lines\pack\forge_king_lines_off_4181a589.exe` and `..._on_44fd0137.exe`.
- **pin_check full** (`logs/pin_check_step2.txt`): OFF and ON both PASS.
  - Net on: 312866 / 862329 / 3024920 / 12389307 / 34048354.
  - Perft: 4865609 / 193690690.
- **Net off** (`logs/netoff_pins.txt`): OFF and ON both give 375354 / 907205 / 2448617 / 13573040 / 24506465 = the pins.

### Step 3 - full 12k bitexact, ON vs the lock, net on (commit e89e818c)
- **Verdict: BIT-EXACT (L1-L3; L3 on 12000 FENs).** Exit 0. Run 2026-11-06 17:24:58 PC clock; the cand took 658 s.
- Ref: the lock exe trial_w6 4181a589 (forge_push\bin, read only). Cand: the ON exe 44fd0137.
- Runner: bitexact_check.ps1 4d1c8d52, with -SkipSan (L4 not run).
- L1: 10 / 10 PASS (bench d11-d22, net on and net off, = pins).
- L2: 2 / 2 PASS (perft 5 startpos 4865609, kiwipete 193690690).
- L3: **12000 / 12000 identical** (depth, score, nodes, bestmove) on fens_12k_v2.txt (md5 e7dbf2c8) at go depth 13,
  12000 distinct ref results.
- Log: `logs/bitexact_on_neton.log`.

### Step 4 - full 12k bitexact, ON vs the lock, net off: BLOCKED by the F: disk floor
- **17:37:17 PC clock:** the runner refused to start. Its fail-closed guard said "ERROR: F: would drop to 49.3 GB free
  (< 50)", exit 1 (`D:\opus_5h\king_lines\bx_on_netoff.console.txt`).
- **F: at 17:38:** 49.59 GiB free.
  - Other jobs used it up: F: had 59.9 GiB at 16:38.
  - This pack writes its outputs to D:, and the net-off reference TSV is already cached
    (`F:\ospd\ref\4181a589\fens_e7dbf2c8_n12000_d13_ob0_UseNNUE-false.tsv`).
- **Not done:** the guard was not bypassed and the CR-approved runner was not changed.
- **Armed 17:39:** an own background retry. It checks F: every 60 s for up to 60 min. When F: has at least 50.4 GiB free,
  it runs the step-4 command with `-Out D:\opus_5h\king_lines\bx_on_netoff_r2`. The result goes into
  `bx_on_netoff_r2.console.txt`.

- **Owner, ~18:00:** "use c drive it has space". So step 4 runs on C: (C: had 81.6 GiB free; the floor is 50 GB, per the
  owner's earlier rule).
  - **Run copy:** `C:\opus_5h\king_lines\tools\` holds the approved bitexact_check.ps1 4d1c8d52 and the branch
    uci_lib.ps1. The copies are md5 7f150cc5 and a97d7db7.
  - **What the copy changes** (`tools/runner_c_drive.diff`, md5 2f691372, 5 lines; the check logic is unchanged):
    - the reference cache root `F:\ospd\ref` becomes `C:\opus_5h\ref` (two lines);
    - the scratch root `F:\ospd` becomes `C:\opus_5h`;
    - the disk guard `C: >= 30 GB and F: >= 50 GB` becomes `C: >= 50 GB after the planned write`.
  - **Cache seeded on C:.** The two files the run reads were copied from `F:\ospd\ref\4181a589\` with the same sha256:
    `sig_4181a5893f15e732.json` (1a74bf20...) and `fens_e7dbf2c8_n12000_d13_ob0_UseNNUE-false.tsv` (e25cac43...).
  - **The F: retry is defused:** `D:\opus_5h\king_lines\bx_on_netoff_r2\` was created, so if F: recovers that run
    refuses to start ("Out exists"). Nothing was stopped or killed.
  - **Output:** `C:\opus_5h\king_lines\bx_on_netoff_c`, started 18:02:08 PC clock. It passed the disk guard.

## In progress
Step 4 on C: (full 12k, ON vs the lock, net off).

## Exact next step
1. Read the verdict in `C:\opus_5h\king_lines\bx_on_netoff_c.console.txt`, copy the log to `logs/`, write the line, push.
2. Hand the pack to Code Review. Nothing is queued.

## Resume commands
```
cd /f/ospd/wt && git checkout opus-king-lines-20261106
bash opus_king_lines/tools/pp_identity.sh /f/ospd/src/trial_w6 /d/opus_5h/king_lines/src/kl
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'F:\ospd\wt\opus_speed\tools\bitexact_check.ps1' \
  -Cand 'D:\opus_5h\king_lines\pack\forge_king_lines_on_44fd0137.exe' \
  -Ref 'C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe' \
  -Out 'D:\opus_5h\king_lines\<new dir>' -SkipSan [-FenOptions UseNNUE=false]
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'F:\ospd\wt\opus_speed\tools\build_variants.ps1' \
  -SrcDir 'D:\opus_5h\king_lines\src\kl_gate' -Tag kl_gate -Variant lp_v1 -Twice -Work 'D:\opus_5h\king_lines\builds'
```

## Unproven / not claimed
- Not a lock.
- **No speed claim:** there is no ABBA; QA owns it.
- **Not run in this brief:** L3b warm_identity, the Threads 2-4 soak and the deep-ply stress. They were in the original
  job-4 text, but the owner's follow-up asks only for steps 1-4.

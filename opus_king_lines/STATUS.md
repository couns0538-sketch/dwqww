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

### Step 4 - full 12k bitexact, ON vs the lock, net off: **BIT-EXACT** (run on C:, see below)
- **Verdict: BIT-EXACT (L1-L3; L3 on 12000 FENs).** Exit 0. Run 2026-11-06 18:02:06 PC clock; the cand took 468 s.
  - L1: 10 / 10 PASS (bench d11-d22, net on and net off, = pins).
  - L2: 2 / 2 PASS (perft 5 startpos 4865609, kiwipete 193690690).
  - L3 options (ref and cand): `OwnBook=false, UseNNUE=false`.
  - L3: **12000 / 12000 identical** (depth, score, nodes, bestmove) on fens_12k_v2.txt (md5 e7dbf2c8) at go depth 13,
    12000 distinct ref results.
  - Reference: the cached lock net-off set, sha256 e25cac43, the same bytes as the F: cache.
  - Log: `logs/bitexact_on_netoff.log` (md5 b354ae3f).

How it got there:
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

### Step 5 - L3b warm_identity, ON vs OFF, net on and net off: **IDENTICAL**
The owner's later brief (2026-11-06, about 18:50 PC clock) asks for the warm-table identity check (L3b) for KING_LINES
ON vs OFF. No soak and no timing.
- **Verdict: IDENTICAL.** Exit 0. Run 18:56:51-18:57:19 PC clock (14 s per exe).
  - Harness line: `IDENTICAL: 12827 normalised lines, 1000 searches (go nodes 20000, 1000 FENs, warm TT, 40 state
    changes), bench 13 = 862329 on both`.
  - **Per position** (depth, score, nodes, bestmove; `tools/wi_tally.py` run on the harness's own logs, exit 0):
    - **net on: 850 / 850 identical;**
    - **net off: 150 / 150 identical;**
    - whole rows (with seldepth and pv): the same counts. First mismatch: none.
  - Net-off blocks (FEN index // 25): 4, 10, 16, 22, 28, 34. These come from the harness's cycle; each log has 12
    UseNNUE lines.
  - The ref has 1000 distinct result rows for 1000 FENs, so the degenerate guard passed. Both engines read back mask
    0x3 Idle.
- **Method:** the same tool and parameters as the six earlier stacks (opus_speed OWN_CHECKS #11).
  - `opus_speed/tools/warm_identity.py` md5 3523f351. The file is the same on opus-speed 1ad0d295 and on this branch.
  - 1000 FENs of `fens_12k_v2.txt` (md5 e7dbf2c8), `go nodes 20000`, Threads 1, no ucinewgame (warm TT).
  - Every 25 FENs it makes one change: Hash 1 / Hash 64 / Clear Hash / UseNNUE false / UseNNUE true / Hash 16.
  - `bench 1` and `go perft 1` run first, `bench 13` last.
  - The harness has no net-off-only mode, so the net-off share (150 of 1000) is its own UseNNUE blocks.
- **Exes:**
  - ref = OFF 4181a5893f15e732..., the lock's bytes;
  - cand = ON 44fd0137e7aa48e6...;
  - both are sha256-checked copies of the pack exes, in `C:\opus_5h\king_lines\wi_exe\`.
- **Outputs (C: only):**
  - `C:\opus_5h\king_lines\wi_on_vs_off\`: ref.log md5 125e3316 and cand.log md5 ad0fd1f3, 12829 lines each;
  - console `logs/wi_on_vs_off.console.txt` (md5 291e132d);
  - tally `logs/wi_tally.txt`.
- The commit was made from a shallow sparse clone on C: (`C:\opus_5h\king_lines\repo`). Nothing was written to F:.

## Summary
- **The rebase is clean.** KING_LINES (the committed b4 patch d680f9bf) applies to trial_w6, and the switch-0 source is
  preprocessor-identical to trial_w6.
- **OFF build** = 4181a589 = the lock, byte for byte (pc1 = pc2).
- **ON build** 44fd0137 (pc1 = pc2): every pin holds, net on and net off, plus both perfts.
- **Full 12k:** BIT-EXACT net on (12000 / 12000) and net off (12000 / 12000).
- **L3b warm_identity** (warm TT, 40 option changes): IDENTICAL. Per position: net on 850 / 850, net off 150 / 150.

## In progress
None. Step 5 finished at 18:57:19 PC clock. The step-4 F: retry loop (`D:\opus_5h\king_lines\retry_step4.sh`) was set to
poll until about 18:38; this was not re-checked. Its -Out folder exists, so it re-runs nothing.

## Exact next step
1. Code Review of the pack.
2. Then QA's remaining lock-path items: the Threads 2-4 soak (`patchrev_qa.py soak`) and QA's own quiet ABBA vs
   trial_w6. QA owns both. L3b warm_identity is done (step 5).
3. Not a lock. Nothing is queued.

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
# step 5 (Git Bash, cwd C:/opus_5h/king_lines; the out dir must not exist yet)
python -I -B F:/ospd/wt/opus_speed/tools/warm_identity.py C:/opus_5h/king_lines/wi_exe/forge_king_lines_off_4181a589.exe \
  C:/opus_5h/king_lines/wi_exe/forge_king_lines_on_44fd0137.exe F:/ospd/wt/opus_speed/data/fens_12k_v2.txt \
  C:/opus_5h/king_lines/<new dir> --n 1000 --nodes 20000
python -I -B opus_king_lines/tools/wi_tally.py C:/opus_5h/king_lines/<new dir>
```

## Unproven / not claimed
- Not a lock.
- **No speed claim:** there is no ABBA; QA owns it.
- **Not run:** the Threads 2-4 soak and the deep-ply stress. These are QA items.
- **L3b net-off coverage:** 150 warm searches, which is the harness's own share. It is not a net-off-only run of 1000.

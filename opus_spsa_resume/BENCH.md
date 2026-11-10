# BENCH: builds, identity and synthetic qualification (no games)

Nothing in this file is a game result, and none of it is Elo. Every process ran at Idle on CPUs 12–15 (mask 0xF000), with Threads 1 and Hash 16 unless stated otherwise. Times are Vienna, from GitHub's `Date` header. The build logs and receipts carry PC-clock times, which run about 25,161 s ahead (see `STATUS.md`). Every command below starts with `. D:\forge_jobs_20261107\opus3\env.ps1`, which sets the CPUs, priority, TEMP and git environment for the process and its children.

Short names: **lock** = `forge_clang_combo29_trial_w6.exe` (SHA256 e1284f7f…802e, frozen copy `out\freeze\parent\`). **ctl / off / gat** = builds `c29ctl_03` / `c29off_03` / `c29gat_03` (§1). **sw0 / sw1** = gate switches RazorTune and QsTune both at 0 / both at 1.

## Summary
| Check | Result | Evidence |
|---|---|---|
| Builds ctl / off / gat with the derived recipe (PGO profile total equals QA's for ctl and off) | PASS | §1, `evidence/builds/c29*_03/` |
| Normalized PE image: lock = ctl, lock = off, ctl = off (0 differing bytes outside 6 masked fields) | PASS | §2, `evidence/pe_compare/` |
| Raw byte identity with the lock | **UNRESOLVED** (pre-declared; PDB path, GUID and checksum differ) | §2 |
| Identity battery: UCI option lists, bench d11–d22 net on/off for lock, ctl, off, gat sw0 and gat sw1 at defaults, perft, 16 gate-semantics checks | PASS (all) | §3, `evidence/qual/battery_03/summary.json` |
| fens12k d13, net on and off: gat sw0 vs lock, gat sw1-defaults vs lock | PENDING (running) | §4 |
| warm1000 (QA's warm-table tool, mask-only derived copy): lock vs gat sw0 | PENDING | §5 |
| fens12k for ctl and off | NOT RUN: they are normalized-image-identical to the lock (§2) | — |
| Synthetic qualification of the joint config: movement, noise floor, resume byte-identity | Done; resume byte-identity PASS. Run size: see §6 | §6, `evidence/synthqual/` |
| End-to-end dry-run: synthetic training run → fixed candidate rule → G1 confirmation command | PASS (no file written, no process started, registry untouched) | §7 |

## 1. Builds
**Recipe.** `engine/clang_build_o3.ps1`, SHA256 77d4e79bc97685cef835157ff007cce0fe1508c7e3a64ed8393511b32c886417. It is QA's `clang_build.ps1` (1fd87517…) with three changes, all shown in `engine/RECIPE_INTERDIFF.patch`:
1. The mask guard accepts only 0xF000.
2. An optional `-ExtraDefines` is appended as `-D` tokens; when empty, the tokens are the original ones.
3. PGO training stdin goes through a `cmd.exe` redirect.

Two notes on the file:
- Its header comment mentions only the first two changes. The file is left byte-identical to the one that produced the `_03` builds.
- Its parameter defaults (`-Src`, `-OutRoot`, `-Workload`) still name QA's `D:\sdk_jobs\…` tree, exactly as in 1fd87517. Always pass all three explicitly, as below.

**Why `_03`.**
- `_01` failed.
- `_02` trained on a stdin that Windows PowerShell 5.1, running without a console, had prefixed with a UTF-8 BOM. The engine ignored its first `uci`, so the profile was short.
- `_03` passes raw bytes. Its workload output shows `uciok`, and the ctl and off profile totals equal QA's 6,054,052,240.

| Tag | Source | Extra defines | exe SHA256 | Profile total |
|---|---|---|---|---|
| c29ctl_03 | `out\freeze\parent\source_snapshot` (unmodified snapshot, manifest 3389cfe3…) | none | 6cfce7038c7aadff3e8aa0d0e7070ec2930dafcea06a4e74c2c1f7d63d8ec953 | 6054052240 |
| c29off_03 | `out\engine\patched` (snapshot + `patches/tune_gate_after_combo29.patch`) | none (both macros 0) | 958da7abaf1eceb8c9e5aa7aa113d0655bbda536adae59b012716a444cce5a33 | 6054052240 |
| c29gat_03 | `out\engine\patched` | `FORGE_RAZOR_TUNE=1;FORGE_QS_TUNE=1` | 404549d7ea1b8274021feda26753a2e45942b7b7840fc51cd1d076d37c83ab6c | 6054052518 (the gate code adds counters) |

QA's lock build: profile total 6,054,052,240; raw profile 612e344d…; merged c5d97fc7…. Every build root is `out\rb_equal_len_paths\<9-character tag>`, so each embedded path has the same length as in QA's build.

```
Set-Location $Opus3Out
$r = Join-Path $Opus3Repo 'opus_spsa_resume\engine\clang_build_o3.ps1'
$w = Join-Path $Opus3Out 'freeze\recipe\frozen_train_cmds.txt'   # sha256 1d52720a… (checked by the recipe)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $r -Tag c29ctl_03 -Src (Join-Path $Opus3Out 'freeze\parent\source_snapshot') -OutRoot (Join-Path $Opus3Out 'rb_equal_len_paths') -Workload $w
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $r -Tag c29off_03 -Src (Join-Path $Opus3Out 'engine\patched') -OutRoot (Join-Path $Opus3Out 'rb_equal_len_paths') -Workload $w
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $r -Tag c29gat_03 -Src (Join-Path $Opus3Out 'engine\patched') -OutRoot (Join-Path $Opus3Out 'rb_equal_len_paths') -Workload $w -ExtraDefines 'FORGE_RAZOR_TUNE=1;FORGE_QS_TUNE=1'
```

## 2. Image identity (`engine/pe_compare.py`)
`pe_compare.py` masks six fields and compares everything else byte by byte:
- COFF TimeDateStamp
- COFF symbol and string table
- RSDS GUID and Age
- RSDS PDB path
- debug entry TimeDateStamp
- optional header CheckSum

| Pair | Raw equal | Layout equal | Normalized equal | Differing bytes | Differing sections |
|---|---|---|---|---|---|
| lock vs ctl | no | yes | **yes** | 0 | — |
| lock vs off | no | yes | **yes** | 0 | — |
| ctl vs off | no | yes | **yes** | 0 | — |
| off vs gat | no | no | no (expected: the gate code is compiled in) | — | .text .rdata .buildid .data .pdata .reloc + debug sections |

So with both macros at 0, the patch produces the lock's image, up to the masked fields. The same holds for the unmodified recipe output (ctl). **Raw byte identity stays UNRESOLVED**: the PDB path and GUID embedded by `--pdb=<abs path>` differ by construction, as QA's lock note says ("binary not byte-reproducible (embedded PDB paths)").

```
& $Opus3Py -I -B .\opus_spsa_resume\engine\pe_compare.py <a.exe> <b.exe> --json out\qual\pe03\<a>_vs_<b>.json
```

## 3. Identity battery (`engine/qualify.py`): ALL PASS
```
$rb = Join-Path $Opus3Out 'rb_equal_len_paths'
& $Opus3Py -I -B .\opus_spsa_resume\engine\qualify.py (Join-Path $Opus3Out 'freeze\parent\forge_clang_combo29_trial_w6.exe') "$rb\c29off_03\m2use\forge_m2use.exe" "$rb\c29gat_03\m2use\forge_m2use.exe" (Join-Path $Opus3Out 'qual\battery_03') --ctl "$rb\c29ctl_03\m2use\forge_m2use.exe"
```
- **UCI option lists.** off is identical to lock. gat is lock plus exactly two lines: `option name RazorTune type spin default 0 min 0 max 1` and `option name QsTune type spin default 0 min 0 max 1`.
- **Bench pins** at depths 11/13/16/20/22, net on (312866/862329/3024920/12389307/34048354) and net off (375354/907205/2448617/13573040/24506465). All ten runs equal the pins: lock, ctl, off, gat sw0 and gat sw1 at defaults, each net on and net off.
- **perft 5:** startpos 4865609 and kiwipete 193690690 on lock, off and gat.
- **Gate semantics** (bench d13 and d16 in one engine process per sequence), 16 of 16 checks pass:
  - Values set while a switch is 0 change nothing.
  - Switch 1 applies them, and the result equals the lock exe given the same values: RazorBase 300 + RazorMultiplier 250; QsFutilityMargin 200 + QsSeeMargin 140; RazorBase 135 + QsFutilityMargin 176.
  - Switch 1 at defaults changes nothing.
  - Setting the switch back to 0 restores the pins.
  - The order of setoption calls does not matter.
  - With both families set, turning RazorTune off leaves only the qsearch value active.
- Per-check JSON for all of the above: `evidence/qual/battery_03/`.

## 4. fens12k depth 13 (node identity per position)
PENDING: running at the time of writing.

## 5. warm1000 (warm transposition table across positions and option changes)
PENDING.

## 6. Synthetic qualification of `configs/joint_razor_qs.json`
```
& $Opus3Py -I -B .\opus_spsa_resume\spsa\synth_qualify.py .\opus_spsa_resume\configs\joint_razor_qs.json (Join-Path $Opus3Out 'synthqual') --reps 4
```
Each synthetic copy keeps everything the real run uses: schedule, bounds, priors, pins, perturbation seed 20261110, N = 4000 pairs and batch size 4. Only three things differ: run_nonce, identity_check = start, and an outcome model. The model plays seeded outcomes with draw rate 0.75 on the harness's logistic/400 scale. Its units describe the model, **not the engine**.

**Landscapes.** The start is 3.75 model units below the optimum in each one:
- **L2:** optimum 2 c_end from the start in every tuned coordinate, signs (+, −, −).
- **L2m:** the mirror placement, signs (−, +, +).
- **L4:** optimum 4 c_end away; a wider, flatter basin.
- **null:** flat, no signal.

Results at N = 4000 (4 replicates each):

| Model | Gap left at the end (start 3.75) | Share of the gap recovered | Mean move toward the optimum (c_end units) | Spread of the final drift between replicates (sd, c_end units) |
|---|---|---|---|---|
| L2 | 3.27 (2.94–3.52) | 13% | 0.04 / 0.22 / 0.15 of 2 | 0.07–0.11 |
| L2m | 3.17 (2.71–3.72) | 15% | 0.18 / 0.16 / 0.16 of 2 | 0.11–0.23 |
| L4 | 3.52 (3.39–3.69) | 6% | 0.08 / 0.15 / 0.15 of 4 | 0.05–0.12 |
| null | — | — | drift 0.00 / 0.04 / −0.05 | 0.06–0.11 (noise floor) |

**Resume byte-identity on the real schedule: PASS.** The L2 replicate 1 run was interrupted twice: at B3@300:2, mid-batch after 2 of 4 results, and at B5@700, after the update record but before its checkpoint. After each resume it equals the uninterrupted run byte for byte in the ledger, RUN.json, HEAD.json and all 2,002 checkpoints (2,005 files). Exit codes 77, 77, 0; `verify` exit 0.

**Reading.** With N = 4000 and r_end 0.002 the run moves in the right direction in every landscape, but slowly. It covers only about a tenth of the distance and recovers 6–15% of a 3.75-unit gap. A small movement in a real run is therefore expected and is not evidence of a flat landscape. Sweep over N and r_end: PENDING (running).

## 7. End-to-end dry-run (synthetic candidate → G1 confirmation command)
```
$ps = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'; $bin = '.\opus_spsa_resume\bin\confirm.ps1'
& $ps -NoProfile -ExecutionPolicy Bypass -File $bin -Command select -TrainingRun out\synthqual\L2_r1\run -CandidateOut out\synthqual\e2e\candidate_L2_r1_SYNTHETIC.json
& $ps -NoProfile -ExecutionPolicy Bypass -File $bin -Command run -Protocol .\opus_spsa_resume\confirm\configs\confirm_protocol_G1_example.json -Candidate out\synthqual\e2e\candidate_L2_r1_SYNTHETIC.json -RunDir out\synthqual\e2e\confirm_G1_dry
```
- **The fixed rule** turned the complete SYNTHETIC run into a candidate spec:
  - Values: RazorBase 151, RazorMultiplier 340, QsFutilityMargin 155. These are synthetic, meaningless values.
  - spec_sha256 2e343196….
- **The dry-run:**
  - Verified all four pinned identities: fastchess, the gate exe 404549d7…, the lock exe and holdout_G1.pgn.
  - Counted 2,408 holdout openings.
  - Printed the fastchess command: `option.RazorTune=1 option.QsTune=1` plus the three values against the lock, `-rounds 2408`.
  - Wrote no file, started no process and did not create the registry.
- **The same protocol with a 40,000-game cap was refused** (exit 10, `openings would repeat`): G1 has only 2,408 openings, so the cap needs 20,000 pairs. The runner now enforces this budget in every mode.
- Logs: `evidence/synthqual/e2e/`.

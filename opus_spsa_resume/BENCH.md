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
| fens12k d13, net on and off: gat sw0 vs lock, gat sw1-defaults vs lock (12000 / 12000 rows; TSVs byte-identical to each other and to QA's refcache) | PASS | §4, `evidence/qual/fens12k/` |
| warm1000 (QA's warm-table tool, mask-only derived copy), lock vs gat sw0: identical apart from the two advertised switch lines; bench 13 pin on both | PASS | §5, `evidence/qual/warm1000/` |
| fens12k for ctl and off | NOT RUN: they are normalized-image-identical to the lock (§2) | — |
| Synthetic qualification of the joint config (movement, noise floor), N = 4000 found inadequate, sweep over N and r_end, run size set to N = 16000 before any game | Done (SYNTHETIC, no Elo) | §6, `evidence/synthqual/`, `evidence/synthqual_n16000/` |
| Resume byte-identity on the real schedule, two injected crashes (N = 4000: 2,005 files; N = 16000: 8,005 files) | PASS | §6 |
| End-to-end dry-run: synthetic training run → fixed candidate rule → G1 confirmation command; the non-live candidate is reported, and the live, replay-without-manifest and over-cap starts are refused with nothing written | PASS | §7 |

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

## 4. fens12k depth 13 (node identity per position): PASS, 12000 / 12000
This is QA's L3 protocol: for each FEN, `ucinewgame`, `isready`, `position fen`, `go depth 13`, with OwnBook false, Threads 1 and Hash 16. The FEN list is `fens_12k_v2.txt` (SHA256 c01c0e6a…, frozen copy). Each row records depth, score, nodes and bestmove.

| Run | Net on (rows identical to lock) | Net off (rows identical to lock) |
|---|---|---|
| lock | reference | reference |
| gat sw0 | 12000 / 12000 | 12000 / 12000 |
| gat sw1 at defaults (`RazorTune=1 QsTune=1`, no values) | 12000 / 12000 | 12000 / 12000 |

- The six TSVs are byte-identical within each net setting: net on c366cf20…, net off a6e52a5d….
- Both are also byte-identical to QA's frozen refcache TSVs for `sig_4181a589` (`fens_e7dbf2c8_n12000_d13_ob0_UseNNUE-{true,false}_Threads-1_Hash-16.tsv`).
- That gives an independent cross-check of the driver against QA's own runs, and it measures the combo29 lock directly. QA's refcache came from the older trial_w6 exe and was valid for combo29 only through QA's bit-exact proof.
- Wall time per run was 13–26 minutes at Idle, sharing CPUs 12–15. Total nodes: 1,527,383,677 net on and 1,561,677,694 net off for every exe.

```
& $Opus3Py -I -B .\opus_spsa_resume\engine\uci_driver.py fens <exe> --fens out\freeze\data\fens_12k_v2.txt --depth 13 --nnue on|off [--opt RazorTune=1 --opt QsTune=1] --out out\qual\fens12k\<name>.tsv
& $Opus3Py -I -B .\opus_spsa_resume\engine\compare_fens.py <reference.tsv> <candidate.tsv> ... --json <out.json>
```
Evidence: `evidence/qual/fens12k/`, which holds the run JSONs, the comparisons and `TSV_SHA256.txt`.

**Not run:** fens12k for ctl and off. Their images are normalized-identical to the lock (§2), and their bench pins are identical (§3).

## 5. warm1000, lock vs gat sw0: PASS (identical apart from the two advertised option lines)
`engine/warm_identity_0xF000.py` is QA's `warm_identity.py`; only the CPU mask differs (`engine/WARM_IDENTITY_INTERDIFF.patch`). It plays one script into each exe with the transposition table kept warm:
- `bench 1` and `go perft 1` first;
- then 1,000 FENs with `go nodes 20000` each;
- a state change every 25 FENs (Hash 1, Hash 64, Clear Hash, UseNNUE false/true, Hash 16; 39 changes);
- `bench 13` at the end.

The tool compares the whole normalized transcript, including the `uci` option list. It therefore reported exit 3: the gate build advertises exactly the two switch lines, and the first difference is `option name RazorTune …` at line 85. That difference is expected (§3).

`engine/warm_compare_logs.py` re-compares the two saved transcripts with the tool's own `norm` function. It allows exactly those two lines, and each must occur once, inside the `uci` reply, and never in the reference. The result:
- identical apart from them;
- 1,000 searches;
- 43 setoption lines;
- `bench 13` = 862329 on both;
- the degenerate-reference guard passed (1,000 distinct result rows).

```
& $Opus3Py -I -B .\opus_spsa_resume\engine\warm_identity_0xF000.py <lock.exe> <gat.exe> out\freeze\data\fens_12k_v2.txt out\qual\warm1000_lock_vs_gatsw0 --n 1000      # exit 3: option list
& $Opus3Py -I -B .\opus_spsa_resume\engine\warm_compare_logs.py out\qual\warm1000_lock_vs_gatsw0 --allow-extra "option name RazorTune type spin default 0 min 0 max 1" --allow-extra "option name QsTune type spin default 0 min 0 max 1"   # exit 0
```
Evidence: `evidence/qual/warm1000/`, which holds the comparison JSON, the console output and the SHA256 of both transcripts.

## 6. Synthetic qualification of `configs/joint_razor_qs.json`: run size set to N = 16000 before any game
```
& $Opus3Py -I -B .\opus_spsa_resume\spsa\synth_qualify.py .\opus_spsa_resume\configs\joint_razor_qs.json (Join-Path $Opus3Out 'synthqual_n16000') --reps 4
& $Opus3Py -I -B .\opus_spsa_resume\spsa\synth_qualify.py out\synthqual\base_n4000\joint_razor_qs.json (Join-Path $Opus3Out 'synthqual') --reps 4       # the first proposal, N = 4000
& $Opus3Py -I -B .\opus_spsa_resume\spsa\synth_qualify.py out\synthqual\base_n4000\joint_razor_qs.json (Join-Path $Opus3Out 'synthqual') --sweep --reps 3
```
Each synthetic copy keeps everything the real run uses: schedule, bounds, priors, pins, perturbation seed 20261110, N and batch size 4. Only four keys differ: run_nonce, identity_check = start, the outcome model and the comment. The model plays seeded outcomes with draw rate 0.75 on the harness's logistic/400 scale. Its units describe the model, **not the engine**. Gaps and distances are assumptions chosen to be tuning-sized, not measurements.

**Landscapes.** The start is 3.75 model units below the optimum in each one:
- **L2:** optimum 2 c_end from the start in every tuned coordinate, signs (+, −, −).
- **L2m:** the mirror placement, signs (−, +, +).
- **L4:** optimum 4 c_end away; a wider, flatter basin.
- **null:** flat, no signal. Its final drift is the procedure's noise floor.

**First proposal, N = 4000, r_end 0.002** (4 replicates each): inadequate.

| Model | Gap left (start 3.75) | Recovered | Move toward the optimum (c_end) | Replicate sd of the final drift (c_end) |
|---|---|---|---|---|
| L2 | 3.27 (2.94–3.52) | 13% | 0.04 / 0.22 / 0.15 of 2 | 0.07–0.11 |
| L2m | 3.17 (2.71–3.72) | 15% | 0.18 / 0.16 / 0.16 of 2 | 0.11–0.23 |
| L4 | 3.52 (3.39–3.69) | 6% | 0.08 / 0.15 / 0.15 of 4 | 0.05–0.12 |
| null | — | — | drift 0.00 / 0.04 / −0.05 | 0.06–0.11 |

**Sweep over N and r_end** (L2 and null, 3 replicates per cell; `evidence/synthqual/sweep_summary.json`). The table gives the L2 gap left (range), the share recovered, and the largest null-drift sd:

| N (pairs) | r_end 0.002 | r_end 0.005 | r_end 0.01 |
|---|---|---|---|
| 4,000 | 3.13 (2.90–3.34), 16%, 0.21 | 2.33 (1.56–3.02), 38%, 0.30 | 1.73 (0.98–2.73), 54%, 0.93 |
| 16,000 | **1.44 (1.40–1.51), 62%, 0.15** | 0.80 (0.47–1.36), 79%, 0.90 | 0.78 (0.45–1.02), 79%, 0.83 |
| 40,000 | 0.67 (0.65–0.71), 82%, 0.45 | 0.28 (0.04–0.69), 93%, 1.50 | 0.27 (0.13–0.43), 93%, 2.65 |

**The proposed config: N = 16000, r_end 0.002** (4 replicates each; `evidence/synthqual_n16000/summary.json`):

| Model | Gap left (start 3.75) | Recovered | Move toward the optimum (c_end) | Replicate sd of the final drift (c_end) |
|---|---|---|---|---|
| L2 | 1.66 (1.49–1.96) | 56% | 0.73 / 0.62 / 0.70 of 2 | 0.21–0.24 |
| L2m | 1.94 (1.12–2.35) | 48% | 0.58 / 0.52 / 0.65 of 2 | 0.20–0.41 |
| L4 | 3.13 (2.92–3.46) | 17% | 0.30 / 0.35 / 0.44 of 4 | 0.21–0.42 |
| null | — | — | drift 0.05 / −0.29 / 0.02 | 0.13–0.32 |

Gap trajectory of L2 under the proposed config: 3.60 at 500 pairs, 3.45 at 1,000, 3.14 at 2,000, 2.72 at 4,000, 2.11 at 8,000, 1.83 at 12,000, 1.66 at 16,000.

**Resume byte-identity on the real schedule: PASS for both N.** The L2 replicate 1 run was interrupted twice:
- at B3@300:2, mid-batch after 2 of 4 results;
- at B5@700, after the update record but before its checkpoint.

After the resumes it equals the uninterrupted run byte for byte in the ledger, RUN.json, HEAD.json and every checkpoint. Exit codes were 77, 77, 0, and `verify` exit 0.
- N = 4000: 2,005 files.
- N = 16000: 8,005 files.

The check always starts from an empty directory and requires both crashes to fire.

**Code-change check.** After the M2 fixes, both qualifications were re-run over their existing runs. Every recorded plan and update was reproduced by the fixed code; any difference would have been refused with exit 30. The corrected diagnostics show 0 capped and 0 shrunk plans in every run.

**Reading.**
- N = 4000 at the default gain moves the right way but too slowly.
- Raising r_end at fixed N moves faster but widens the noise floor: the end point scatters by up to 0.9–2.6 c_end.
- N = 16000 at the default gain recovers about half to three fifths of a tuning-sized gap at 2 c_end (56–62% over two replicate sets), with the smallest noise floor of the cells that move far (0.15–0.32 c_end).
- A wide, flat basin (L4) still moves only 17%. A small movement in a real run is therefore not evidence of a flat landscape.
- Cost: 32,000 games at 10+0.1, QA's decision (`PLAN.md` §4.7).

## 7. End-to-end dry-run (synthetic candidate → G1 confirmation command), with the M2-fixed code
```
$ps = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'; $bin = '.\opus_spsa_resume\bin\confirm.ps1'; $e = 'out\synthqual_n16000\e2e'
& $ps -NoProfile -ExecutionPolicy Bypass -File $bin -Command select -TrainingRun out\synthqual_n16000\L2_r1\run -CandidateOut $e\refused.json              # exit 10
& $ps -NoProfile -ExecutionPolicy Bypass -File $bin -Command select -TrainingRun out\synthqual_n16000\L2_r1\run -CandidateOut $e\candidate_L2_r1_SYNTHETIC.json -AllowNonLive
& $ps -NoProfile -ExecutionPolicy Bypass -File $bin -Command run -Protocol .\opus_spsa_resume\confirm\configs\confirm_protocol_G1_example.json -Candidate $e\candidate_L2_r1_SYNTHETIC.json -RunDir $e\confirm_G1_dry
```
- **The fixed rule:**
  - It refuses a synthetic training run (exit 10).
  - With `-AllowNonLive` it turned the complete SYNTHETIC N = 16000 run into a spec with `training_mode: synthetic`.
  - Values: RazorBase 157, RazorMultiplier 324, QsFutilityMargin 147. These are synthetic, meaningless values.
- **The dry-run:**
  - Verified all four pinned identities: fastchess, the gate exe 404549d7…, the lock exe and holdout_G1.pgn.
  - Counted 2,408 holdout openings.
  - Reported `candidate_confirmable: false`, with two issues: a synthetic training run, and no `training_config_sha256` pinned yet.
  - Printed the fastchess command: `option.RazorTune=1 option.QsTune=1` plus the three values against the lock, `-rounds 2408`.
  - Wrote no file, started no process and created no registry.
- **Refused, with nothing written** (no run directory, no registry line):
  - the same protocol with a 40,000-game cap (exit 10, `openings would repeat`);
  - `-Mode replay` without a replay manifest (exit 10);
  - `-Mode live -Live` (exit 40: this runner never starts a game).
- Logs: `evidence/synthqual_n16000/e2e/`.

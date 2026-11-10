# STATUS: opus_spsa_resume (Opus 3)

All times are Vienna, taken from GitHub's HTTP `Date` header. The PC clock runs about 25,160 s (6 h 59 min) ahead and is never used for reported times; see `evidence/INC-01_lazy_fetch_disk_drain.json`.

- Last update: 2026-11-10 01:05 Vienna
- Job start: 2026-11-10 00:48:26 Vienna (2026-11-09 23:48:26Z)

## Identity, paths and approvals
| Item | Value |
|---|---|
| Job root | `D:\forge_jobs_20261107\opus3` (`repo\`, `out\`, `tmp\`, `env.ps1`) |
| Repo | `D:\forge_jobs_20261107\opus3\repo`. Blobless clone of github.com/couns0538-sketch/dwqww. `GIT_NO_LAZY_FETCH=1` is the default, and lazy fetching is enabled only for single named blobs. |
| Branch | `opus-spsa-resume-20261107`, from origin/main 5176ddf79ae15b76c08c4485d90ee5600ba30a1a. No upstream; push always uses an explicit refspec. |
| Approvals | Plan approved by Couns (`C:\Users\Administrator\.claude\plans\dazzling-crafting-squid.md`). INC-01 scoped cleanup approved by Couns. |
| Parent exe (combo29 lock) | `forge_clang_combo29_trial_w6.exe`. MD5 c0051c99695f48bf93272d96fe7548c3. SHA256 e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e. |
| Build parent | `D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\source_snapshot`. SOURCE_INPUTS manifest sha256 3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645. Recipe 1fd8751755356c8a0ba386b48c1bc643401bcdeadf8e91cc5e7e5450d7584bfe. |
| Git source commit of combo29 | **BLOCKED.** No commit contains the snapshot's `src/search.cpp` blob 2ffe2556 (full-history search over the opus1 clone's refs). To be re-verified in this clone with `--no-renames` and no lazy fetch. |
| Pins | net-on 312866/862329/3024920/12389307/34048354. net-off 375354/907205/2448617/13573040/24506465. perft5 4865609, kiwipete 193690690. |

## Safety and resource limits (binding)
- **CPU:** CPUs 12–15 only (mask 0xF000) at Idle; every process I start inherits this from `env.ps1`. No GPU.
- **Never started:** games, matches, SPRTs, tuning, ABBA, timers or background match jobs. The live launcher defaults to dry-run.
- **Never touched:** locks, `CURRENT_LOCK.json`, queues, `forge_gates.json`, STOP/PAUSE files, training, self-play, gates, nets or datasets.
- **Termination:** only my own children whose command line is under `C:\Users\Administrator\grok-pc`. Never claude.exe, `C:\ospd_hunt` or `F:\ospd`. No writes under `D:\forge_jobs_20261109`.
- **Disk:** D: keeps a 30 GiB reserve, enforced by `Assert-Opus3Disk` before every write-heavy step. No new files on C: or F:.

## Done
- S1 (00:48 to 01:15 Vienna):
  - Clock and offset recorded. INC-01 recorded; D: is back at 32.4 GiB.
  - Blobless clone and branch. First commit 0bb79c2c pushed, so normal push access works.
  - AGENTS policy recovered byte-exact (MD5 94169aef ✓).
  - Inputs frozen with `bin/freeze_inputs.ps1`: 18 identities and all 20 snapshot files verified; see `evidence/FREEZE.json` and the FREEZE_FILES manifests.
  - Lineage settled; the combo29 git source commit is **BLOCKED** (`AUDIT.md` §1).
  - Tuner audit of R9, O30, R3 and `tools/match`, plus the parameter inventory (`AUDIT.md`).
  - fable52 checked: analysis only, no engine patch.
  - Sensitivity probe on the lock exe (`evidence/sensitivity_combo29_lock_d13_d16.json`); its d13 values equal R3's AL1 measurements.
  - Families selected: F1 razoring and F2 qsearch pruning (`PLAN.md`). QsSeeMargin turned out to be a step function, so it and RazorDepth are optional discrete levels, off by default.

## In progress
- S1: commit and push the M1 candidate, then the M1 review (one reviewer subagent).
- S2 starts in parallel on files the review does not cover: the R9 import into `spsa/`.

## Next exact action
`. D:\forge_jobs_20261107\opus3\env.ps1; cd $Opus3Repo; git add opus_spsa_resume; Set-Opus3GitDates; git commit; git push origin opus-spsa-resume-20261107`

## Resume commands
```
. D:\forge_jobs_20261107\opus3\env.ps1
cd D:\forge_jobs_20261107\opus3\repo
git status --short --branch; git log --oneline -5
Get-Content opus_spsa_resume\STATUS.md
```
On resume, re-verify the hashes in this file before relying on any earlier receipt.

## Checks
| Check | State |
|---|---|
| combo29 exe MD5/SHA256 | PASS (read-only during planning; re-verified at freeze) |
| AGENTS policy MD5 | PASS |
| Freeze of 18 inputs plus 20 snapshot files against the planning identities and the manifest | PASS |
| Bench pins of the lock exe, d13/d16 (sensitivity probe, defaults before and after) | PASS (862329 / 3024920) |
| Bench d11/d20/d22, net-off, perft, fens12k | NOT RUN (S3) |
| Harness, engine patch, builds, confirmation | NOT RUN |

## Unproven claims
- None. No tuning has run and no Elo is claimed; real tuning is PENDING QA EXECUTION.

# STATUS: opus_spsa_resume (Opus 3)

All times are Vienna, taken from GitHub's HTTP `Date` header. The PC clock runs about 25,160 s (6 h 59 min) ahead and is never used for reported times; see `evidence/INC-01_lazy_fetch_disk_drain.json`.

- Last update: 2026-11-10 02:05 Vienna
- Job start: 2026-11-10 00:48:26 Vienna (2026-11-09 23:48:26Z)
- Elapsed: about 1 h 17 min

## Identity, paths and approvals
| Item | Value |
|---|---|
| Job root | `D:\forge_jobs_20261107\opus3` (`repo\`, `out\`, `tmp\`, `env.ps1`) |
| Repo | `D:\forge_jobs_20261107\opus3\repo`. Blobless clone; `GIT_NO_LAZY_FETCH=1` by default. Blobs are fetched only explicitly, with an LF-only id list. |
| Branch | `opus-spsa-resume-20261107`, from origin/main 5176ddf79ae15b76c08c4485d90ee5600ba30a1a. Upstream is `origin/opus-spsa-resume-20261107`, set by the first push. Pushes use the explicit refspec. |
| Approvals | Plan approved by Couns (`C:\Users\Administrator\.claude\plans\dazzling-crafting-squid.md`). INC-01 scoped cleanup approved by Couns. |
| Parent exe (combo29 lock) | `forge_clang_combo29_trial_w6.exe`. MD5 c0051c99695f48bf93272d96fe7548c3. SHA256 e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e. |
| Build parent | `D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\source_snapshot`. Manifest sha256 3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645. Recipe 1fd8751755356c8a0ba386b48c1bc643401bcdeadf8e91cc5e7e5450d7584bfe. |
| Git source commit of combo29 | **BLOCKED.** No commit holds the snapshot's SDK-patched files (2853 commits on 410 refs, trees only). See `evidence/combo29_source_commit_search.json` and `AUDIT.md` §1. |
| Families | **F1 razoring** (RazorBase, RazorMultiplier) + **F2 qsearch pruning** (QsFutilityMargin). RazorDepth and QsSeeMargin are frozen. See `PLAN.md`, revised after M1. |
| Pins | net-on 312866/862329/3024920/12389307/34048354. net-off 375354/907205/2448617/13573040/24506465. perft5 4865609, kiwipete 193690690. |

## Safety and resource limits (binding)
- **CPU:** CPUs 12–15 only (0xF000) at Idle; every process I start inherits it from `env.ps1`. No GPU.
- **Never started:** games, matches, SPRTs, tuning, ABBA, timers or background match jobs. Dry-run is the default; live mode needs three guards.
- **Never touched:** locks, `CURRENT_LOCK.json`, queues, `forge_gates.json`, STOP/PAUSE files, training, self-play, gates, nets or datasets.
- **Termination:** only my own children whose command line is under `C:\Users\Administrator\grok-pc`. Engines are only ever asked to `quit`.
- **Disk:** D: keeps a 30 GiB reserve, enforced by `Assert-Opus3Disk`. No new files on C: or F:.

## Done
- **S1 (00:48–01:15):**
  - Clock recorded and INC-01 handled.
  - Blobless clone and branch created; push works (0bb79c2c).
  - AGENTS policy recovered byte-exact.
  - Freeze: 18 identities recorded, of which 10 are pinned to planning-time hashes and 8 only recorded (`pinned:false`); all 20 snapshot files verified against the build manifest.
  - Lineage traced; commit identity BLOCKED.
  - Tuner audit, parameter inventory, sensitivity probe, PLAN.
- **M1 review (one same-model reviewer subagent, not independent):** 1 BLOCKER, 2 MAJOR and 7 MINOR/NIT findings. All were assessed and addressed in this commit; see `review/REVIEW_LOG.md`. A recheck is requested.
- **S2 so far:**
  - R9 tuner imported verbatim (bcc0803b).
  - `spsa/space.py`, `ledger.py` and `opus3_spsa.py` written. R9's stc1 and sanity3 runs replay bit-exactly in `r9_clamp` mode.
  - Harness tests 55/55 PASS on two consecutive full runs. Covered: crash at 17 boundaries and a double crash (byte-identical state), torn tail, refusals, replay, rollback.
  - One earlier run had a single unexplained exit 1 in its movement test. A resume completed that run. After adding `os.replace` retries and traceback capture it has not recurred; the root cause is unconfirmed (suspected transient file lock).
  - Engine patch `patches/tune_gate_after_combo29.patch` (md5 8875a86e77b76f4953a19099eebcca13). With both macros at 0 the preprocessed `uci.cpp` text is identical to the parent's; the gate build passes `-fsyntax-only -Wall -Wextra`; the patch applies cleanly to a pristine copy of the snapshot.

## In progress / next exact actions
1. Commit the M1 fixes and push; send the reviewer the M1 recheck.
2. S2: `configs/joint_razor_qs.json` with real pins and the baseline config; opening partition tool and manifests (before any fitting); confirmation pack (`confirm_runner.py`, holdout manifest, protocol aligned with QA's combo29 conventions: 10+0.1, `uho_lichess_v1`, SPRT [0,5], cap 5000, longer-TC confirm); PS 5.1 entry points (`bin\spsa.ps1`, `confirm.ps1`, `rollback.ps1`, `selftest.ps1`).
3. S3: derived recipe and three builds (ctl / off / gate); identity battery (bench, perft, fens12k, warm); gate semantics; synthetic power estimate.

## Resume commands
```
. D:\forge_jobs_20261107\opus3\env.ps1
cd D:\forge_jobs_20261107\opus3\repo
git status --short --branch; git log --oneline -8
& $Opus3Py -I -B opus_spsa_resume\tests\test_r9_equivalence.py
& $Opus3Py -I -B opus_spsa_resume\tests\test_spsa_harness.py D:\forge_jobs_20261107\opus3\out\tests\resume_check
```
On resume, re-verify the hashes in this file before relying on any earlier receipt.

## Checks
| Check | State |
|---|---|
| combo29 exe MD5/SHA256 in 4 locations | PASS |
| AGENTS policy MD5 | PASS |
| Freeze (10 pinned identities, 8 recorded, 20 snapshot files against the manifest) | PASS |
| Lock bench pins d13/d16 with saved receipts (sensitivity and 2×2 runs; defaults before and after) | PASS (862329 / 3024920) |
| Lock bench d11 | Seen once, 312866, in an unsaved driver smoke run, so not claimed; the S3 battery records it |
| R9 saved-run replay equivalence | PASS |
| Harness tests (synthetic, replay, crash, refusals, rollback) | PASS 55/55 (twice) |
| Patch macro-0 token identity, gate syntax, clean apply | PASS |
| Bench d20/d22, net-off, perft, fens12k, warm, builds, normalized PE identity | NOT RUN (S3) |
| Opening partitions (before any fitting): disjoint, hashed; UHO overlap with train 50 of 2,632,036 lines | PASS (`partition/PARTITION_MANIFEST.json`) |
| Confirmation pack tests (A/A, fake optimizer, positive control, 7 crash boundaries, refusals, replay, leakage audit) | PASS 26/26 (synthetic, no Elo) |

## Unproven claims (not results)
- No tuned values exist; real tuning is **PENDING QA EXECUTION**. No Elo is claimed.
- The F1–F2 interaction is a code-level coupling only. The bench-node 2×2 probe cannot evidence it: a control pair was just as non-additive.
- C1 and C3′ are heuristic priors, not correctness constraints.
- Run-size adequacy (N = 4000, r_end 0.002) is unestimated until the S3 synthetic power check.

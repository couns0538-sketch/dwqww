# STATUS: opus_spsa_resume (Opus 3) — FINAL (handed to Code Review, then QA)

All times are Vienna, taken from GitHub's HTTP `Date` header. The PC clock runs about 25,160–25,170 s (6 h 59 min) ahead, and the gap grew by a few seconds during this job. It is never used for reported times; see `evidence/INC-01_lazy_fetch_disk_drain.json`. `TESTS.md` carries a PC-clock stamp.

- Last update: 2026-11-10 03:47 Vienna
- Job start: 2026-11-10 00:48:26 Vienna (2026-11-09 23:48:26Z)
- Elapsed: about 2 h 59 min
- **Real tuning: PENDING QA EXECUTION.** No game of any kind was played by this job, and no tuned value or Elo is claimed.

## Identity, paths and approvals
| Item | Value |
|---|---|
| Job root | `D:\forge_jobs_20261107\opus3` (`repo\`, `out\`, `tmp\`, `env.ps1`) |
| Repo | `D:\forge_jobs_20261107\opus3\repo`. Blobless clone; `GIT_NO_LAZY_FETCH=1` by default. Blobs are fetched only explicitly, with an LF-only id list. |
| Branch | `opus-spsa-resume-20261107`, from origin/main 5176ddf79ae15b76c08c4485d90ee5600ba30a1a, pushed to origin with normal commits only. The tip is the commit that contains this file (`git log -1`). |
| Bundle (backup) | `D:\forge_jobs_20261107\opus3\out\bundle\opus-spsa-resume-20261107.bundle`, created from the final tip after this commit. It needs 5176ddf7 as prerequisite. Check it with `git bundle verify <file>`. |
| Approvals | Plan approved by Couns (`C:\Users\Administrator\.claude\plans\dazzling-crafting-squid.md`). INC-01 scoped cleanup approved by Couns. |
| Parent exe (combo29 lock) | `forge_clang_combo29_trial_w6.exe`. MD5 c0051c99695f48bf93272d96fe7548c3. SHA256 e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e. |
| Build parent | `D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\source_snapshot`. Manifest sha256 3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645. Recipe 1fd8751755356c8a0ba386b48c1bc643401bcdeadf8e91cc5e7e5450d7584bfe. |
| Git source commit of combo29 | **BLOCKED.** No commit holds the snapshot's SDK-patched files (2853 commits on 410 refs, trees only). See `evidence/combo29_source_commit_search.json` and `AUDIT.md` §1. |
| Families | **F1 razoring** (RazorBase, RazorMultiplier) + **F2 qsearch pruning** (QsFutilityMargin). RazorDepth and QsSeeMargin are frozen. See `PLAN.md`. |
| Joint config | `configs/joint_razor_qs.json`: N = 16000 pairs, r_end 0.002, 10+0.1. N was set from the synthetic qualification before any game (`PLAN.md` §4.7). Live mode is disabled. |
| Engine patch | `patches/tune_gate_after_combo29.patch`, md5 8875a86e77b76f4953a19099eebcca13. |
| Builds | `out\rb_equal_len_paths\c29{ctl,off,gat}_03`. exe SHA256: ctl 6cfce703…, off 958da7ab…, gat 404549d7…. See `BENCH.md` §1. |
| Freeze provenance | `evidence/FREEZE.json` was produced by `bin/freeze_inputs.ps1` as committed in c6df6af6 (blob 1f7da090). The current blob 52b9da3d differs only by the added Idle read-back. |
| Pins | net-on 312866/862329/3024920/12389307/34048354. net-off 375354/907205/2448617/13573040/24506465. perft5 4865609, kiwipete 193690690. |
| Pack manifests | `MANIFEST.md5` and `MANIFEST.sha256`: every tracked pack file except the two manifests. |

## Safety and resource limits (binding; kept throughout)
- **CPU:** CPUs 12–15 only (0xF000) at Idle. Every process I started inherited this from `env.ps1` or from the `bin\*.ps1` self-placement. No GPU. Final sample at 03:46: CPUs 12–15 at 46/22/34/22%; no foreign process pinned to them.
- **Never started:** games, matches, SPRTs, tuning, ABBA, timers or background match jobs. Dry-run is the default; live tuning needs three guards. The confirmation runner never plays a game.
- **Never touched:** locks, `CURRENT_LOCK.json`, queues, `forge_gates.json`, STOP/PAUSE files, training, self-play, gates, nets or datasets. No confirmation registry was created.
- **Termination:** none was needed. At 03:46 no engine, Python or fastchess process of this job is running.
- **Disk:** D: keeps a 30 GiB reserve, enforced by `Assert-Opus3Disk`; 32.09 GiB free at 03:46. No new files on C: or F:.

## Done
- **S1:**
  - Clock recorded; INC-01 handled.
  - Clone and branch created; AGENTS policy recovered byte-exact.
  - Inputs frozen; all 35 files re-verified at 02:38.
  - Lineage traced; commit identity BLOCKED.
  - AUDIT and PLAN written.
- **S2:**
  - R9 import.
  - Harness.
  - Engine patch.
  - Opening partitions frozen before any fitting.
  - Joint config and baseline.
  - Confirmation pack.
  - PS 5.1 entry points.
- **S3:**
  - Derived recipe and three builds (BOM root cause fixed); profile summaries equal QA's.
  - Normalized PE identity: lock = ctl = off.
  - Identity battery ALL PASS; RazorTune-off equality.
  - fens12k d13: 12000 / 12000 net on and off, byte-identical to QA's refcache.
  - warm1000: identical apart from the two advertised option lines.
  - Synthetic qualification:
    - N = 4000 found inadequate.
    - Sweep over N and r_end.
    - N = 16000 set before any game.
    - Resume byte-identity on the real schedule: 2,005 and 8,005 files.
  - End-to-end demonstration.
- **Reviews (one same-model reviewer subagent; not independent):**
  - M1 + recheck.
  - M2 (1 BLOCKER, 3 MAJOR, …).
  - M2 recheck + M3.
  - Final recheck: every disposition resolved, nothing blocks; its 2 MINOR and 8 NIT items fixed or documented.
  - Everything is logged in `review/REVIEW_LOG.md`.
- **S4:**
  - `HANDOFF.md` (Code Review → QA).
  - `bin\selftest.ps1` under Windows PowerShell 5.1: ALL PASS, written to `TESTS.md`.
  - Pack manifests.
  - Push.
  - Git bundle.

## Next (not this job)
- Code Review of `patches/tune_gate_after_combo29.patch` and the pack.
- Then QA, in the order of `HANDOFF.md` §2. Nothing was queued by this job.

## Resume commands
```
. D:\forge_jobs_20261107\opus3\env.ps1
cd D:\forge_jobs_20261107\opus3\repo
git status --short --branch; git log --oneline -8
powershell.exe -NoProfile -ExecutionPolicy Bypass -File opus_spsa_resume\bin\selftest.ps1
```
On resume, re-verify the hashes in this file and in `MANIFEST.sha256` before relying on any earlier receipt.

## Checks
| Check | State |
|---|---|
| combo29 exe MD5/SHA256 in 4 locations | PASS |
| AGENTS policy MD5 | PASS |
| Freeze: 35 files against `FREEZE_FILES.sha256` (re-verified 02:38) | PASS |
| R9 saved-run replay equivalence (strict in inner mode) | PASS |
| Harness tests (synthetic, replay, crash at every boundary, refusals, rollback) | PASS 64/64 |
| Confirmation pack tests | PASS 39/39 |
| `bin\selftest.ps1` (Windows PowerShell 5.1), final | ALL PASS, `TESTS.md` |
| Patch macro-0 token identity (preprocessed uci.cpp parent = off), gate syntax, clean apply | PASS |
| Builds ctl / off / gat (_03); PGO profile summaries ctl/off = QA's | PASS |
| Normalized PE identity lock = ctl = off | PASS (raw byte identity UNRESOLVED, pre-declared) |
| UCI options, bench d11–d22 net on/off (lock, ctl, off, gat sw0, gat sw1 defaults), perft, gate semantics, RazorTune-off equality | PASS |
| fens12k d13 net on/off: gat sw0 and sw1-defaults vs lock (and QA refcache) | PASS 12000/12000 |
| warm1000 lock vs gat sw0 | PASS (apart from the two advertised option lines) |
| fens12k for ctl and off | NOT RUN (normalized-image-identical to the lock) |
| Synthetic resume byte-identity on the real schedule, two crashes | PASS (N 4000 and N 16000) |
| End-to-end dry-run with refusals, nothing written | PASS |
| Opening partitions: disjoint on the 4-field key, hashed, frozen before fitting | PASS (2 G1 openings collide with training on the 3-field audit key; documented) |
| Build wrapper `engine/build_o3.ps1` | Refusal paths tested; no build run through it |
| Live tuning mode | NOT RUN by design (no games in this job); guards, dry-run command and PGN parsing tested |

## Unproven claims (not results)
- No tuned values exist; real tuning is **PENDING QA EXECUTION**. No Elo is claimed.
- The F1–F2 interaction is a code-level coupling only.
- C1 and C3′ are heuristic priors, not correctness constraints.
- **Run-size adequacy** is estimated in synthetic models only: an assumed 3.75-unit gap with the optimum 2 c_end away. N = 16000 recovers 56–62% there. The choice is a cost-benefit judgment, not an optimum.

# STATUS: opus_spsa_resume (Opus 3)

All times are Vienna, taken from GitHub's HTTP `Date` header. The PC clock runs about 25,160–25,170 s (6 h 59 min) ahead, and the gap grew by a few seconds during this job. It is never used for reported times; see `evidence/INC-01_lazy_fetch_disk_drain.json`.

- Last update: 2026-11-10 03:35 Vienna
- Job start: 2026-11-10 00:48:26 Vienna (2026-11-09 23:48:26Z)
- Elapsed: about 2 h 47 min

## Identity, paths and approvals
| Item | Value |
|---|---|
| Job root | `D:\forge_jobs_20261107\opus3` (`repo\`, `out\`, `tmp\`, `env.ps1`) |
| Repo | `D:\forge_jobs_20261107\opus3\repo`. Blobless clone; `GIT_NO_LAZY_FETCH=1` by default. Blobs are fetched only explicitly, with an LF-only id list. |
| Branch | `opus-spsa-resume-20261107`, from origin/main 5176ddf79ae15b76c08c4485d90ee5600ba30a1a. Upstream is `origin/opus-spsa-resume-20261107`. Pushes use the explicit refspec. |
| Approvals | Plan approved by Couns (`C:\Users\Administrator\.claude\plans\dazzling-crafting-squid.md`). INC-01 scoped cleanup approved by Couns. |
| Parent exe (combo29 lock) | `forge_clang_combo29_trial_w6.exe`. MD5 c0051c99695f48bf93272d96fe7548c3. SHA256 e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e. |
| Build parent | `D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\source_snapshot`. Manifest sha256 3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645. Recipe 1fd8751755356c8a0ba386b48c1bc643401bcdeadf8e91cc5e7e5450d7584bfe. |
| Git source commit of combo29 | **BLOCKED.** No commit holds the snapshot's SDK-patched files (2853 commits on 410 refs, trees only). See `evidence/combo29_source_commit_search.json` and `AUDIT.md` §1. |
| Families | **F1 razoring** (RazorBase, RazorMultiplier) + **F2 qsearch pruning** (QsFutilityMargin). RazorDepth and QsSeeMargin are frozen. See `PLAN.md`. |
| Joint config | `configs/joint_razor_qs.json`: N = 16000 pairs, r_end 0.002, 10+0.1. N was set from the synthetic qualification before any game (`PLAN.md` §4.7). Live mode is disabled. |
| Engine patch | `patches/tune_gate_after_combo29.patch`, md5 8875a86e77b76f4953a19099eebcca13. |
| Builds | `out\rb_equal_len_paths\c29{ctl,off,gat}_03`. exe SHA256: ctl 6cfce703…, off 958da7ab…, gat 404549d7…. See `BENCH.md` §1. |
| Pins | net-on 312866/862329/3024920/12389307/34048354. net-off 375354/907205/2448617/13573040/24506465. perft5 4865609, kiwipete 193690690. |

## Safety and resource limits (binding)
- **CPU:** CPUs 12–15 only (0xF000) at Idle. Every process I start inherits this from `env.ps1` or from the `bin\*.ps1` self-placement. No GPU. Sample at 03:16: CPUs 12–15 at 21/27/45/63%; no foreign process pinned to them.
- **Never started:** games, matches, SPRTs, tuning, ABBA, timers or background match jobs. Dry-run is the default; live mode needs three guards. The confirmation runner never plays a game.
- **Never touched:** locks, `CURRENT_LOCK.json`, queues, `forge_gates.json`, STOP/PAUSE files, training, self-play, gates, nets or datasets.
- **Termination:** only my own children whose command line is under `C:\Users\Administrator\grok-pc`. Engines are only ever asked to `quit`.
- **Disk:** D: keeps a 30 GiB reserve, enforced by `Assert-Opus3Disk`; 32.6 GiB free at 03:16. No new files on C: or F:.

## Done
- **S1:**
  - Clock recorded; INC-01 handled.
  - Clone and branch created; AGENTS policy recovered byte-exact.
  - Inputs frozen; all 35 files re-verified at 02:38.
  - Lineage traced; commit identity BLOCKED.
  - AUDIT and PLAN written.
- **M1 review and recheck:** all findings addressed.
- **S2:**
  - R9 import.
  - Harness.
  - Engine patch.
  - Opening partitions frozen before any fitting.
  - Joint config and baseline.
  - Confirmation pack.
  - PS 5.1 entry points.
- **S3:**
  - Derived recipe and three builds.
  - Normalized PE identity: lock = ctl = off.
  - Identity battery ALL PASS.
  - fens12k d13: 12000 / 12000 on and off for gat sw0 and sw1 vs lock, byte-identical to QA's refcache.
  - warm1000: identical apart from the two advertised option lines.
  - Synthetic qualification:
    - N = 4000 found inadequate (13–16% of a model gap).
    - Sweep over N and r_end.
    - N = 16000 set before any game.
    - Resume byte-identity on the real schedule: 2,005 and 8,005 files.
  - End-to-end demonstration.
- **M2 review (02:33–03:00)** of 5cb03dc2: 1 BLOCKER, 3 MAJOR, 7 MINOR and NITs. All assessed and fixed, plus one extra defect (a level coordinate frozen at its edge index). Fixed in fd47a42d (03:14).
  - Harness 63/63, confirmation 35/35, R9 equivalence (strict).
  - Both synthetic qualifications re-run under the fixed code.
  - `bin\selftest.ps1` under Windows PowerShell 5.1: ALL PASS (`TESTS.md`).
- `HANDOFF.md` written (Code Review → QA).
- **M2 recheck + M3 review (03:15–03:27)** of fd47a42d. All M2 findings are resolved. The fixes brought 2 MINOR and 4 NIT-level new issues; M3 found 4 MINOR and 4 NIT. All assessed and fixed or documented (`review/REVIEW_LOG.md`):
  - a second registry beside the holdout file;
  - no candidate from a run rolled back after completing;
  - interim replays refused;
  - fail-closed start positions;
  - profdata receipt;
  - noise-floor ranking withdrawn;
  - guarded build wrapper;
  - RazorTune-off equality measured.
  After these fixes, `bin\selftest.ps1` passes again: R9 equivalence, harness 63/63, confirmation 39/39.

## In progress / next exact actions
1. Commit and push these fixes; send the final recheck to the same reviewer.
2. **S4:**
   - Pack manifests `MANIFEST.md5` / `MANIFEST.sha256`.
   - Git bundle on D: (`out\bundle\`).
   - Final STATUS and push.

## Resume commands
```
. D:\forge_jobs_20261107\opus3\env.ps1
cd D:\forge_jobs_20261107\opus3\repo
git status --short --branch; git log --oneline -8
powershell.exe -NoProfile -ExecutionPolicy Bypass -File opus_spsa_resume\bin\selftest.ps1
```
On resume, re-verify the hashes in this file before relying on any earlier receipt.

## Checks
| Check | State |
|---|---|
| combo29 exe MD5/SHA256 in 4 locations | PASS |
| AGENTS policy MD5 | PASS |
| Freeze: 35 files against `FREEZE_FILES.sha256` (re-verified 02:38) | PASS |
| R9 saved-run replay equivalence (strict in inner mode) | PASS |
| Harness tests | PASS 63/63 |
| Confirmation pack tests | PASS 39/39 |
| `bin\selftest.ps1` (Windows PowerShell 5.1) | ALL PASS, `TESTS.md` |
| Patch macro-0 token identity, gate syntax, clean apply | PASS |
| Builds ctl / off / gat (_03) | PASS (BENCH.md §1) |
| Normalized PE identity lock = ctl = off | PASS (raw byte identity UNRESOLVED, pre-declared) |
| UCI options, bench d11–d22 net on/off (lock, ctl, off, gat sw0, gat sw1 defaults), perft, 16 gate-semantics checks | PASS |
| RazorTune-off equality: gate sequence set 2 = lock at QsFutilityMargin 176 (877190 / 3071864) | PASS (measured 03:30) |
| PGO profile summaries: ctl/off = QA's (320 functions, 2,481 blocks, 6,054,052,240) | PASS (`evidence/builds/profdata_totals.txt`) |
| fens12k d13 net on/off: gat sw0 and sw1-defaults vs lock (and QA refcache) | PASS 12000/12000 |
| warm1000 lock vs gat sw0 | PASS (apart from the two advertised option lines) |
| fens12k for ctl and off | NOT RUN (normalized-image-identical to the lock) |
| Synthetic resume byte-identity on the real schedule, two crashes | PASS (N 4000 and N 16000) |
| End-to-end dry-run with refusals, nothing written | PASS |
| Opening partitions: disjoint on the 4-field key, hashed, frozen before fitting | PASS (2 G1 openings collide with training on the 3-field audit key; documented) |
| Live tuning mode | NOT RUN by design (no games in this job); guards, dry-run command and PGN parsing tested |

## Unproven claims (not results)
- No tuned values exist; real tuning is **PENDING QA EXECUTION**. No Elo is claimed.
- The F1–F2 interaction is a code-level coupling only.
- C1 and C3′ are heuristic priors, not correctness constraints.
- **Run-size adequacy** is estimated in synthetic models only: an assumed 3.75-unit gap with the optimum 2 c_end away. N = 16000 recovers 56–62% there.

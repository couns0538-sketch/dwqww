# STATUS: opus_spsa_resume (Opus 3)

All times are Vienna, taken from GitHub's HTTP `Date` header. The PC clock runs about 25,160–25,170 s (6 h 59 min) ahead, and the gap grew by a few seconds during this job. It is never used for reported times; see `evidence/INC-01_lazy_fetch_disk_drain.json`.

- Last update: 2026-11-10 02:39 Vienna
- Job start: 2026-11-10 00:48:26 Vienna (2026-11-09 23:48:26Z)
- Elapsed: about 1 h 51 min

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
| Engine patch | `patches/tune_gate_after_combo29.patch`, md5 8875a86e77b76f4953a19099eebcca13. |
| Builds | `out\rb_equal_len_paths\c29{ctl,off,gat}_03`. exe SHA256: ctl 6cfce703…, off 958da7ab…, gat 404549d7…. See `BENCH.md` §1. |
| Pins | net-on 312866/862329/3024920/12389307/34048354. net-off 375354/907205/2448617/13573040/24506465. perft5 4865609, kiwipete 193690690. |

## Safety and resource limits (binding)
- **CPU:** CPUs 12–15 only (0xF000) at Idle. Every process I start inherits this from `env.ps1` or from the `bin\*.ps1` self-placement. No GPU.
- **Never started:** games, matches, SPRTs, tuning, ABBA, timers or background match jobs. Dry-run is the default; live mode needs three guards.
- **Never touched:** locks, `CURRENT_LOCK.json`, queues, `forge_gates.json`, STOP/PAUSE files, training, self-play, gates, nets or datasets.
- **Termination:** only my own children whose command line is under `C:\Users\Administrator\grok-pc`. Engines are only ever asked to `quit`.
- **Disk:** D: keeps a 30 GiB reserve, enforced by `Assert-Opus3Disk`; 33.2 GiB free at 02:38. No new files on C: or F:.

## Done
- **S1 (00:48–01:15):**
  - Clock recorded; INC-01 handled.
  - Clone and branch created; AGENTS policy recovered byte-exact.
  - Inputs frozen; on 02:38 all 35 frozen files re-verified against `evidence/FREEZE_FILES.sha256`.
  - Lineage traced; commit identity BLOCKED.
  - AUDIT and PLAN written.
- **M1 review and recheck:** all findings addressed (`review/REVIEW_LOG.md`).
- **S2:**
  - R9 import; harness (55/55 tests).
  - Engine patch.
  - Opening partitions frozen before any fitting.
  - Joint config and baseline.
  - Confirmation pack.
  - PS 5.1 entry points.
- **S3:**
  - Derived recipe and three builds (BOM root cause fixed).
  - Normalized PE identity: lock = ctl = off.
  - Identity battery ALL PASS.
  - Synthetic qualification: movement, noise floor, resume byte-identity on the real schedule.
  - End-to-end dry-run, synthetic candidate to G1 confirmation command.
  - Opening-budget guard in the confirmation runner (27/27 confirmation tests).
  - Commits 1f4902e6 and 5cb03dc2.

## In progress / next exact actions
1. **Running:** fens12k d13, net on and off, for lock, gat sw0 and gat sw1 at defaults (`out\qual\fens12k`). Then compare:
   `& $Opus3Py -I -B opus_spsa_resume\engine\compare_fens.py <lock.tsv> <gate.tsv>...`
   Lock is also compared against QA's frozen refcache TSVs.
2. **Running:** the run-length / gain sweep (`spsa\synth_qualify.py ... --sweep --reps 3`). Then set the proposed N and r_end in `PLAN.md` §4.7 and `configs/joint_razor_qs.json`, before any game.
3. **Next:** warm1000, lock vs gat sw0:
   `& $Opus3Py -I -B opus_spsa_resume\engine\warm_identity_0xF000.py <lock> <gat> out\freeze\data\fens_12k_v2.txt out\qual\warm1000 --n 1000`
4. **M2 code review:** sent at 02:33 to the same reviewer subagent, scope commit 5cb03dc2; findings pending. M3 review of BENCH.md and qualification follows.
5. **S4:**
   - `bin\selftest.ps1` writes `TESTS.md`.
   - Pack MD5 and SHA256 manifests; git bundle on D:.
   - Push; CR → QA handoff note (no queue edits).

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
| Freeze: 35 files against `FREEZE_FILES.sha256` (re-verified 02:38) | PASS |
| R9 saved-run replay equivalence | PASS |
| Harness tests (synthetic, replay, crash, refusals, rollback) | PASS 55/55 (S2; re-run in S4 by selftest) |
| Confirmation pack tests | PASS 27/27 (02:31, after adding the opening-budget guard) |
| Patch macro-0 token identity, gate syntax, clean apply | PASS |
| Builds ctl / off / gat (_03) | PASS (BENCH.md §1) |
| Normalized PE identity lock = ctl = off | PASS (raw byte identity UNRESOLVED, pre-declared) |
| UCI options, bench d11–d22 net on/off (lock, ctl, off, gat sw0, gat sw1 defaults), perft, 16 gate-semantics checks | PASS (`evidence/qual/battery_03`) |
| fens12k d13 net on/off: gat sw0 and sw1-defaults vs lock | RUNNING |
| warm1000 lock vs gat sw0 | NOT RUN yet |
| Synthetic resume byte-identity on the real schedule (2 crashes, 2,005 files) | PASS |
| End-to-end dry-run, synthetic candidate to G1 confirm command (writes nothing) | PASS |
| Opening partitions: disjoint, hashed, frozen before fitting | PASS |

## Unproven claims (not results)
- No tuned values exist; real tuning is **PENDING QA EXECUTION**. No Elo is claimed.
- The F1–F2 interaction is a code-level coupling only.
- C1 and C3′ are heuristic priors, not correctness constraints.
- **Run size:** in synthetic models, N = 4000 pairs at r_end 0.002 moves the right way but recovers only about 13–16% of a 3.75-unit gap with the optimum 2 c_end away (`BENCH.md` §6). The sweep over N and r_end is running.

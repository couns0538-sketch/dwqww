# R11 automated NNUE pipeline (data -> train -> export -> parity -> bench -> package) — first net from our data DONE; 20-epoch net training

Branch `opus-r11-nnue-pipeline` = base `7f79c349` (qa-r10v2-fix1) + the R11 commits (10:26-14:3x PC clock on
2026-10-30, a PC crash/reboot at 11:38 in between). Tool-only: `git diff 7f79c349 HEAD -- src include tests
CMakeLists.txt bench` is empty. Machine exclusive: no (self-play and gates ran throughout; production NNUE training
was paused by QA from 13:46:56 for the R11 gap). Handover notes: `../NOTES_R11.md`. Code Review patches:
`D:\grok-pc-data\r11_nnue\cr_patches\` (one file per commit, INDEX.txt, SHA256SUMS). CI (opus-ci; no engine code
changes): runs 41044452098, 41044616304, 41045785514, 41048252114 all success; later pushes are mostly `[skip ci]`.

Status at 14:30: everything QA asked for in the gap is done except the 20-epoch L1 1024 net, which is training now
(started 14:24:07). Measured on R11's allowed resources (Idle, CPUs 8-10, gates at BelowNormal on CPUs 4-13): the
first 20 % of epoch 0 ran at 6.43 it/s (compile warm-up, cold file cache), epochs 1 and 2 at 12.05 / 12.43 it/s x
16,384 = ~200k positions/s, 12.5-13 min per epoch, so the 20 epochs end around 18:45 and the package ~18:55 (the
owner's production run of the same recipe took 2 h 27 min with full resources). If production restarts earlier, the run yields within ~20 s
(stop checkpoint, exit 76) and resumes from it in a later gap.

## Acceptance
| line (job text / QA / CR) | result | evidence |
|---|---|---|
| 1 convert our self-play data to binpack, streaming + restart-safe, dedup across sources, holdout, output on D: | DONE in the gap: 72 shards (67 + 5 R8 v5 shards that self-play finished during the day), 349,064,671 input rows, 114,476 duplicates dropped, bad 0 -> train 332,562,972 + holdout 16,387,223 records, 11.8 GB of verified binpacks (.part -> verify -> rename) on D:, D: 58 GB free afterwards | `pipeline/r11_data.py`, `logs/data_real/` (data_run5.out, SUMMARY_run5.md, MANIFEST_run5.json, registry_run5.json), test_r11_data 69/69 |
| 1 writer format = the loader's | byte-identical to J1 shard 001 (md5 9bd30944, 466,506 records); verify mode reads the file back with the loader's own reader | `logs/writer_identity_001.txt`, `logs/cr2_amendment/writer_9f191c200e4b_j1_identity.txt` |
| 1 sources | forge_push FPOS/FHCE (the supervisor's 1:1 conversion of selfplay_out), R8 v5 `.dedup.pos` (+ .hce generated with the S20 hce_dump, qualified 200,000/200,000), Astra 9.2M | `pipeline/r11_config.json`, `logs/hce_tool_qualification.txt` |
| 1 Astra set | download + verify + staged extract (pinned sha256 148803c5..., 2,329,781,152 B); a filtered copy of forge_push 003 (9,206,371/9,206,371 rows equal), supersedes 003 | `pipeline/r11_astra.py`, NOTES |
| 1 holdout 013/014 (QA, CR fix 5, CR R2 M3) | real-data proof PASS on the converted data (14:17, run by the one command itself): 013/014 the only holdout shards (16,387,223 positions), all inputs re-verified by full sha256, 0 leak hits on a full scan, dedup order exact on 10,906,390 sampled rows; HOLDOUT_TEST.json is the train gate | `tests/test_r11_holdout_real.py`, `logs/holdout_real/`, `logs/smoke_ourdata/smoke_run.out` |
| 2 train with the AMD Triton setup, checkpoints, auto-resume | smoke on our data: GPU, 4 x 2M positions in 273 s, one checkpoint (val 0.000917); full (owner's recipe: L1 1024, batch 16384, 20 x 152.5M, compile) running since 14:24 with checkpoints every 5 epochs; exact resume, yield-only (proven live at 12:51), nothing deleted (CR R3/R4) | `logs/smoke_ourdata/`, `logs/e2e_live_yield/TIMELINE.txt`, `pipeline/r11_train.py`, `tools/nnue_pytorch_amd/r11/r11_train_entry.py` |
| 3 export + check vs Forge's HalfKA loader (7f79c349, AVX2 x86-64-v3, FMA off) | first net from our data: `D:\grok-pc-data\r11_nnue\nets\r11_smoke_k32h3_l256_bs4096_e4x2000000_s1_e3_best.nnue` sha256 e0462a878baff5aa5bb3fab5685f58d73e892e62a07c94a735e426fb542f7494: parity 12000/12000 exact, OFF d11 312866 ALL OK, ON d11 341,450 / d13 946,351 (stable, reload ok), WAC ON 249/300 (OFF 272). Known-good ep20 (md5 ceaf1837): parity 12000/12000, ON d11 346013 ... d22 39606328, WAC 270/272 | `logs/smoke_ourdata/PACKAGE_*`, `logs/check_npt_line104_ep20/` |
| 3 check exe | AVX2 x86-64-v3 build of 7f79c349 from `git archive`, FMA 0, zmm 0, sha256 ed6a0b189ee0a456baade51c39d05857922efbab8e12e408cb471d1011da12ad (= GATE_EXE) | `logs/check_npt_line104_ep20/GATE_EXE.txt` |
| 4 package every passing net; no gates, locks, baselines, queue | smoke net -> `D:\grok-pc-data\r11_nnue\smoke_packages\r11_smoke_k32h3_l256_bs4096_e4x2000000_s1_e3_best_e0462a87` (not a gate candidate); ep20 -> `gate_ready\npt_line104_k32h3_l1024_ep20_5f5bdc47`; the full net will go to `gate_ready\`; R11 never queues | `pipeline/r11_package.py` |
| 5 one command, safe rerun, PASS/FAIL logs | `r11_pipeline.py run --profile smoke` on our data: R11 PIPELINE PASS (616 s, data -> holdout proof -> train -> export -> check -> package); `run --net` ep20 PASS 192 s, rerun 0 s; CPU end-to-end self-test R11 TRAIN E2E SELFTEST PASS (e2e_5) | `logs/smoke_ourdata/`, `logs/onecmd_ep20/`, `logs/e2e_selftest/` |
| rules: never slow production / gates | Idle + I/O very low + memory low on CPUs 8-10 (BelowNormal is allowed in the gap but would take CPU from the gates' time controls, so R11 stays Idle); yield-only GPU; RAM floors 8/7 GB; 40 GB D: floor | test_r11_tools 1e, NOTES "Facts" |
| rules: never delete, no force-push, main untouched, no STOP/PAUSE files | no checkpoint is deleted (keep_last 1,000,000, the dead deletion branch removed); the only removals are a failed write's own partial files (.part/.tmp, CR fix 7 / QA); no force-push; main untouched | `git log`, test_r11_tools static checks |
| rules: ideas only, scripts + patches with self-tests; GPL stays in tools | 4 self-tests; every file that imports nnue-pytorch lives in `tools/nnue_pytorch_amd/` (run-only); IDEA_SOURCE.md | test_r11_tools GPL-boundary checks |
| skills | new `forge-nnue-pipeline`; R11 sections in forge-pc-rules, forge-nnue-data, forge-nnue-pytorch-amd; lessons in forge-job-workflow and forge-subagent-brief (copies in `skills/`) | `skills/` |

## Code Review fixes (all separate commits; patch files in `D:\grok-pc-data\r11_nnue\cr_patches\`)
- CR (cf7e435a) 1-10: 7e922c55, 7226c8b5 (+ amendment f0d7d364, d625f1ce), 48f49cde, ab3e9ffe, 6df41f3b, dbd8143e,
  43cd8750, 6e6bbe64; fix 5 = R2 M3; fix 9 = the GPL-boundary test; f3bcf25e fixed a config regression of fix 8.
- CR R2 (6df41f3b): H1 66c1c7f7, M1 a069c267, M3 d08731a4, GATE_EXE da5e501b; c62e148a (the entry yielded to its own
  launcher); 27c94568 (production checks also after the imports and at fit start).
- Fix 2 amendment: background mode sets a HARD 32 MB working-set max (dedup pass 1718 s capped vs ~130 s); now Idle +
  I/O very low + memory low + mask 0x700, all inherited.
- CR R3: R3-1 dda51ea2 fail closed on every priority call (entry exit 78, build FAIL); R3-2 00a338a1 lifter identity
  + fail closed; R3-3 b1b671ca no checkpoint deletes (keep_last 1,000,000).
- CR R4 (passed on 516761fa) LOW items: LOW 1 bf0e1792 GetLastError logged ("affinity 0x10000000000 (error 87)");
  LOW 2 b1ca03bf the dead deletion branch removed (the entry's only os.remove is a failed write's own .tmp);
  LOW 3 afdfa4ae the lifter's --expect must name an R11 script (opus_r11/.../r11_*.py). Patch files 22, 24, 25.
- Found and fixed in the gap: 3c856944 checkpoint interval save_every_epochs + a first-checkpoint floor reserve that
  follows L1 (an L1 1024 checkpoint is 1.44 GiB; with no deletes, every-epoch saves would not fit the D: floor);
  66e0c488 per-profile ON bench depths (a weak net explodes at d16-d22: e2e_4's 2-epoch synthetic net needed 331M
  nodes at d13); 05687908 full profile saves every 5 epochs (D: had 59 GB). Patch files 21, 23.

## Findings
- Background mode is the wrong tool for "low priority" on this PC: hard 32 MB working set; a child of a
  background-mode process does not inherit the cap (only memory priority 1).
- At Idle on CPUs 8-10 R11 trains at ~200k positions/s at L1 1024 once compiled and cached (gates at BelowNormal own
  CPUs 4-13): the owner's 20-epoch recipe needs ~4.4 h there vs 2.5 h as a production job.
- The R8 v5 self-play folder keeps growing (5 new shards today): every data run registers them, so the holdout proof
  is rerun after every data run (the one command does that itself).
- A weak net makes the ON bench explode (hours at d16-d22); smoke and test profiles bench shallower.
- Stopping a background task on Windows ends only its shell wrapper; e2e_4's engine (PID 3624) was suspended after an
  identity check, its waiting python processes are PIDs 11312 / 12764.

## Left for the owner / QA
1. The 20-epoch L1 1024 run (`D:\grok-pc-data\r11_nnue\runs\r11_full_k32h3_l1024_bs16384_e20x152500000_s1`): either keep
   the gap until ~18:55, or restart production - R11 then yields (stop checkpoint) and resumes in a later gap. Faster:
   QA queues the same recipe as a production job on R11's binpacks (`D:\grok-pc-data\r11_nnue\data\train_files.txt`,
   holdout `holdout_files.txt`; ~2.5 h), then `r11_pipeline.py --config opus_r11/pipeline/r11_config.json run --ckpt
   <final .ckpt> --l1 1024` exports, checks and packages it.
2. End the e2e_4 leftovers by PID if wanted: 3624 (suspended engine), 12764 and 11312 (test python waiting on it).
3. CR re-review: patch files 15-25 (fix 2 amendment, M1 hardening, R3-1/2/3, R4 LOW 1/2/3, save interval, bench depths).
4. The ask rule `Bash(git push *)` stays (only Couns changes it).

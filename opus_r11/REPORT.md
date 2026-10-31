# R11 automated NNUE pipeline (data -> train -> export -> parity -> bench -> package) — DONE

Branch `opus-r11-nnue-pipeline` = base `7f79c349` (qa-r10v2-fix1) + the R11 commits (10:26-18:4x PC clock on
2026-10-30, a PC crash/reboot at 11:38 in between). Tool-only: `git diff 7f79c349 HEAD -- src include tests
CMakeLists.txt bench` is empty. Machine exclusive: no (self-play and gates ran throughout; production NNUE training
was paused by QA from 13:46:56 to give R11 a gap; "R11 DONE — QA may restart production" was posted at 18:35).
Handover notes: `../NOTES_R11.md`. Code Review patches: `D:\grok-pc-data\r11_nnue\cr_patches\` (one file per commit,
INDEX.txt, SHA256SUMS). CI (opus-ci; no engine code changes): runs 41044452098, 41044616304, 41045785514, 41048252114
all success; later pushes are mostly `[skip ci]` evidence/doc commits.

## Result: the first full-size nets from our own data (owner's recipe, trained in the gap)
L1 1024, batch 16384, 20 epochs x 152.5M positions, lambda 1.0, lr 8.75e-4, compile, on 72 shards (332,562,972 train
records, holdout 013/014 for validation). Training 14:24:07-18:25:08 (14,461 s) at Idle on CPUs 8-10; checkpoints at
epochs 5/10/15/20 (1.44 GiB each, nothing deleted). Both packages are gate-ready (net, sha256, GATE_EXE, bench lines,
parity log, README); check exe GATE_EXE = ed6a0b189ee0a456baade51c39d05857922efbab8e12e408cb471d1011da12ad.

| net | sha256 | holdout val loss | parity fens_12k | OFF | ON d11 / d13 / d16 / d20 / d22 | WAC300 ON (OFF) |
|---|---|---|---|---|---|---|
| `gate_ready\r11_full_k32h3_l1024_bs16384_e20x152500000_s1_e19_final_bf1e347c\...e19_final.nnue` (final epoch) | bf1e347c545e3cbbb6e68c98793d1b4eb331c3564f7749175dbadf2eed4293ff | 0.000456 | 12000/12000 exact | ALL OK, d11 312866 | 373,062 / 831,975 / 4,115,992 / 17,885,060 / 37,006,232 | 256 (272) |
| `gate_ready\r11_full_k32h3_l1024_bs16384_e20x152500000_s1_e9_best_5380f866\...e9_best.nnue` (epoch 10, lowest val loss) | 5380f8665e591a5ca62ca160122be4f5d5cf9f83f1a51c254300933c83d39f36 | 0.000442 | 12000/12000 exact | ALL OK, d11 312866 | 287,095 / 693,432 / 2,816,047 / 12,332,089 / 25,323,515 | 261 (272) |

Both are 70,334,820 bytes; d11 is stable on repeat and reload, OFF after the net is still 312866. The val losses of
epochs 10/15/20 (0.000442 / 0.000450 / 0.000456) are within the noise of a 1M-position validation; QA chooses what to
gate (R11 never queues). D: had 49.3 GiB free afterwards. WAC at 200 ms is a sanity check, not a strength measure.

## Acceptance
| line (job text / QA / CR) | result | evidence |
|---|---|---|
| 1 convert our self-play data to binpack, streaming + restart-safe, dedup across sources, holdout, output on D: | DONE in the gap: 72 shards (67 + 5 R8 v5 shards that self-play finished during the day), 349,064,671 input rows, 114,476 duplicates dropped, bad 0 -> train 332,562,972 + holdout 16,387,223 records, 11.8 GB of verified binpacks (.part -> verify -> rename) | `pipeline/r11_data.py`, `logs/data_real/` (data_run5.out, SUMMARY_run5.md, MANIFEST_run5.json), test_r11_data 69/69 |
| 1 writer format = the loader's | byte-identical to J1 shard 001 (md5 9bd30944); verify mode reads the file back with the loader's own reader | `logs/writer_identity_001.txt`, `logs/cr2_amendment/writer_9f191c200e4b_j1_identity.txt` |
| 1 sources | forge_push FPOS/FHCE, R8 v5 `.dedup.pos` (+ .hce from the qualified S20 hce_dump, 200,000/200,000), Astra 9.2M (filtered forge_push 003, pinned sha256, supersedes 003) | `pipeline/r11_config.json`, `logs/hce_tool_qualification.txt`, `pipeline/r11_astra.py` |
| 1 holdout 013/014 (QA, CR fix 5, CR R2 M3) | real-data proof PASS on the converted data (14:17, run by the one command): 013/014 the only holdout shards (16,387,223 positions), 0 leak hits on a full scan, dedup order exact on 10,906,390 sampled rows; HOLDOUT_TEST.json gates training | `tests/test_r11_holdout_real.py`, `logs/holdout_real/`, `logs/smoke_ourdata/smoke_run.out` |
| 2 train with the AMD Triton setup, checkpoints, auto-resume | smoke (L1 256, 4 x 2M, 273 s) and full (above, 4 h 01 min) on the GPU through `r11_train_entry.py` (R6 trainer unchanged); exact resume, yield-only (proven live), checkpoint interval, nothing deleted | `logs/smoke_ourdata/`, `logs/full_ourdata/`, `logs/e2e_live_yield/` |
| 3 export + check vs Forge's HalfKA loader (7f79c349 AVX2 x86-64-v3, FMA off) | full nets above; smoke net e0462a87... (parity 12000/12000, ON d11 341,450); known-good ep20 ceaf1837 (parity 12000/12000, ON d11 346,013) | `logs/full_ourdata/PACKAGE*_check.json`, `logs/smoke_ourdata/`, `logs/check_npt_line104_ep20/` |
| 4 package every passing net; no gates, locks, baselines, queue | `gate_ready\` e19_final_bf1e347c, e9_best_5380f866, npt_line104 ep20; `smoke_packages\` smoke net + not a gate candidate; nothing queued | `pipeline/r11_package.py` |
| 5 one command, safe rerun, PASS/FAIL logs | `run --profile smoke` PASS (616 s), `run --profile full` PASS (14,612 s), `run --ckpt` on epoch 20 PASS (380 s), `run --net` ep20 PASS + rerun 0 s; E2E self-test PASS (e2e_5) | `logs/full_ourdata/full_run.out`, `full_e20_run.out`, `logs/e2e_selftest/` |
| rules: never slow production / gates | Idle + I/O very low + memory low on CPUs 8-10 (no BelowNormal: it would take CPU from the gates' time controls); yield-only GPU; RAM floors 8/7 GB; 40 GB D: floor | test_r11_tools 1e |
| rules: never delete, no force-push, main untouched, no STOP/PAUSE files | no checkpoint deleted (keep_last 1,000,000, the dead deletion branch removed); only a failed write's own .part/.tmp is removed; no force-push; main untouched | `git log`, test_r11_tools static checks |
| rules: ideas only, scripts + patches with self-tests; GPL stays in tools | 4 self-tests; every file that imports nnue-pytorch lives in `tools/nnue_pytorch_amd/` (run-only) | test_r11_tools GPL-boundary checks |
| skills | new `forge-nnue-pipeline`; R11 sections/lessons in forge-pc-rules, forge-nnue-data, forge-nnue-pytorch-amd, forge-job-workflow, forge-subagent-brief (copies in `skills/`) | `skills/` |

## Code Review fixes (all separate commits; patch files in `D:\grok-pc-data\r11_nnue\cr_patches\`)
- CR (cf7e435a) 1-10: 7e922c55, 7226c8b5 (+ amendment f0d7d364, d625f1ce), 48f49cde, ab3e9ffe, 6df41f3b, dbd8143e,
  43cd8750, 6e6bbe64; fix 5 = R2 M3; fix 9 = the GPL-boundary test; f3bcf25e fixed a config regression of fix 8.
- CR R2 (6df41f3b): H1 66c1c7f7, M1 a069c267, M3 d08731a4, GATE_EXE da5e501b; c62e148a, 27c94568.
- Fix 2 amendment: background mode sets a HARD 32 MB working-set max; now Idle + I/O very low + memory low.
- CR R3: R3-1 dda51ea2 fail closed; R3-2 00a338a1 lifter identity; R3-3 b1b671ca no checkpoint deletes.
- CR R4 (passed on 516761fa) LOW: 1 bf0e1792 GetLastError logged; 2 b1ca03bf dead deletion branch removed; 3 afdfa4ae
  the lifter's --expect must name an opus_r11/.../r11_*.py script.
- Gap fixes: 3c856944 checkpoint interval + first-checkpoint floor reserve by L1; 66e0c488 per-profile bench depths;
  05687908 full profile saves every 5 epochs. Patch files 15-25 are for re-review.

## Findings
- On R11's resources (Idle, CPUs 8-10, gates at BelowNormal on 4-13) the full recipe trains at ~200k positions/s
  after the compile warm-up (epoch 0 ~105k/s): 4 h 01 min vs 2 h 27 min for the owner's production run.
- Background mode = hard 32 MB working set; a weak net explodes the bench at d16-d22; TaskStop on Windows leaves the
  children of a background command running; the R8 v5 folder keeps growing (5 new shards in the day).

## Left for the owner / QA
1. Gate one or both full nets (QA queues; R11 never queues).
2. End the e2e_4 leftovers by PID if wanted: 3624 (suspended engine), 12764 and 11312 (test python waiting on it).
3. CR re-review: patch files 15-25.
4. The ask rule `Bash(git push *)` stays (only Couns changes it).

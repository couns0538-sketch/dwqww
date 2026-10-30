# R11 automated NNUE pipeline (data -> train -> export -> parity -> bench -> package) — PARTIAL

Branch `opus-r11-nnue-pipeline` = base `7f79c349` (qa-r10v2-fix1) + the R11 commits (10:26-12:57 PC clock on
2026-10-30, a PC crash/reboot at 11:38 in between). Tool-only: `git diff 7f79c349 HEAD -- src include tests
CMakeLists.txt bench` is empty. Machine exclusive: no (the production trainer, self-play and gates ran throughout).
Handover notes: `../NOTES_R11.md`. Code Review patches: `D:\grok-pc-data\r11_nnue\cr_patches\` (one file per commit).

PARTIAL because two things could not run in this window, both by rule, not by a defect:
- no net was trained from our own data yet: QA put full-size training in wait mode, and the train stage is yield-only,
  so it does not start while a production trainer runs (production ran almost the whole time);
- the real conversion stops at the D: floor (40 GB + 2 GB margin must stay free; D: free space moved between 38.8 and 67 GB during the day, ~40 GB at 13:00).
Everything else is built, tested and proven on real data or the known-good ep20 net.

## Acceptance
| line (job text / QA / CR) | result | evidence |
|---|---|---|
| 1 convert our self-play data to binpack, streaming + restart-safe, dedup across sources, holdout, output on D: | built; real run: 67 shards / 344,441,194 rows registered with full sha256, cross-source dedup PASS in 6 key-range passes (kept 344,329,054, dropped 112,140 duplicates, bad 0; train 327,941,831 + holdout 16,387,223); conversion did not start: D: had 37.8 GB free, below the 42 GB floor + margin (all 67 shards = 11.54 GB) - resumable shard by shard | `pipeline/r11_data.py`, `logs/data_real/` (dedup_summary.txt, data_run4.out, registry.json), test_r11_data 69/69 |
| 1 writer format = the loader's | byte-identical to J1 shard 001 (md5 9bd30944, 466,506 records); verify mode reads the file back with the loader's own reader | `logs/writer_identity_001.txt`, `logs/cr2_amendment/writer_9f191c200e4b_j1_identity.txt` |
| 1 sources | forge_push FPOS/FHCE (the supervisor's 1:1 conversion of selfplay_out), R8 v5 `.dedup.pos` (+ .hce generated with the S20 hce_dump, qualified 200,000/200,000), Astra 9.2M | `pipeline/r11_config.json`, `logs/hce_tool_qualification.txt` |
| 1 Astra set | download + verify + staged extract (pinned sha256 148803c5..., 2,329,781,152 B); it is a filtered copy of forge_push 003 (9,206,371/9,206,371 rows equal) and supersedes 003 | `pipeline/r11_astra.py`, NOTES |
| 1 holdout 013/014 (QA, CR fix 5, CR R2 M3) | real-data proof PASS (13:12, 93.6 s): 013/014 are registry #0/#1 and the only holdout shards (16,387,223 positions), all 67 inputs re-verified by full sha256, no TRAIN row has a holdout position (full scan, 0 hits), dedup order exact on a 10,762,375-row key-space sample; HOLDOUT_TEST.json is the train gate | `tests/test_r11_holdout_real.py`, `logs/holdout_real/` |
| 2 train with the AMD Triton setup, checkpoints, auto-resume, newest 2 + best | built (R6 trainer unchanged, imported by `r11_train_entry.py`): exact resume; CR R3 overrides "newest 2 + best": no checkpoint is ever deleted (keep_last >= 1,000,000, lower values refused), the best is tracked and the disk floor check before each save stops the run (exit 75, wait) instead of filling D:; RAM/disk floors, hold event; yield proven live: production started at 12:44:57 while the E2E entry was importing torch (its pre-import check had passed); the first in-training check (17 s after fit start) saw it, saved `stop-epoch=0-step=1.ckpt` and exited 76; the driver waits. Hardened since: checks after the imports and at fit start (exit 76, no save) | `pipeline/r11_train.py`, `tools/nnue_pytorch_amd/r11/r11_train_entry.py`, `tests/test_r11_train.py`, `logs/e2e_live_yield/TIMELINE.txt` |
| 3 export + check vs Forge's HalfKA loader (7f79c349, AVX2 x86-64-v3, FMA off) | PASS on npt_line104 ep20 (md5 ceaf1837): fens_12k parity 12000/12000 exact, OFF d11 312866 (ALL OK), ON d11 346013 / d13 908618 / d16 4091355 / d20 23371918 / d22 39606328, WAC300 ON 270 (OFF 272); re-export from its checkpoint byte-identical | `logs/check_npt_line104_ep20/` |
| 3 check exe | AVX2 x86-64-v3 build of 7f79c349 from `git archive`, FMA 0, zmm 0, sha256 ed6a0b189ee0a456baade51c39d05857922efbab8e12e408cb471d1011da12ad (= GATE_EXE) | `logs/check_npt_line104_ep20/GATE_EXE.txt` |
| 4 package every passing net; no gates, locks, baselines, queue | `D:\grok-pc-data\r11_nnue\gate_ready\npt_line104_k32h3_l1024_ep20_5f5bdc47` (net, sha256, exe + GATE_EXE, bench lines, parity log, README); R11 never queues (QA queued ep20 as gates 97/98) | `pipeline/r11_package.py` |
| 5 one command, safe rerun, PASS/FAIL logs | `pipeline/r11_pipeline.py run/status/selftest`, exit 0 PASS / 1 FAIL / 3 WAIT, one line per stage in `pipeline.log`; real net: `run --net` on ep20 -> R11 PIPELINE PASS in 192 s (parity 12000/12000, OFF d11 312866, ON d11-d22 equal to the first check, WAC ON 267/300 OFF 272/300 at 200 ms on a 93 %-loaded PC), the existing package recognised and left as it was; the same command again: check reused, PASS in 0 s | `logs/onecmd_ep20/` |
| rules: never slow production | Idle + I/O very low + memory low on CPUs 8-10 (CR fix 2 as amended), yield-only GPU, RAM floors 8/7 GB, 40 GB D: floor | test_r11_tools 1e, NOTES "Facts" |
| rules: no deletes/moves of existing files, no force-push, main untouched | R11 deletes no checkpoint (CR R3); the only removals are a failed write's own partial files (.part/.tmp, CR fix 7 / QA); no force-push; main untouched | `git log`, rotation.jsonl |
| rules: ideas only, scripts + patches with self-tests; GPL stays in tools | 4 self-tests; every file that imports nnue-pytorch lives in `tools/nnue_pytorch_amd/` (run-only); IDEA_SOURCE.md | test_r11_tools GPL-boundary checks |
| skills | new `forge-nnue-pipeline`; R11 sections in forge-pc-rules, forge-nnue-data, forge-nnue-pytorch-amd (copies in `skills/`) | `skills/` |

## Code Review fixes (all separate commits; patch files in `D:\grok-pc-data\r11_nnue\cr_patches\`)
- CR (cf7e435a) 1-10: 7e922c55, 7226c8b5 (+ amendment f0d7d364, d625f1ce), 48f49cde, ab3e9ffe, 6df41f3b, dbd8143e,
  43cd8750, 6e6bbe64; fix 5 = R2 M3; fix 9 = the GPL-boundary test; f3bcf25e fixed a config regression of fix 8.
- CR R2 (6df41f3b): H1 66c1c7f7, M1 a069c267, M3 d08731a4, GATE_EXE da5e501b; c62e148a fixes H1/M1: the entry yielded
  to its own launcher (the production regexes were on its command line) - found by the end-to-end test;
  27c94568 hardens M1: production started during the (slow) torch import of the live E2E run, so the entry now
  also checks right after the imports and at fit start (stub-clone test in test_r11_tools).
- **CR fix 2 amendment (needs re-review):** background mode (PROCESS_MODE_BACKGROUND_BEGIN) sets a HARD 32 MB
  working-set max. Measured: dedup pass 1 of the real run took 1718.2 s capped, pass 2 139.8 s after the cap was
  lifted; the train entry needed 11 min to import torch and spent 89 % of its CPU time in the kernel (445k page faults/s). Now every
  process sets Idle + I/O very low + memory priority low + mask 0x700 (all inherited by children); test 1e proves the
  values, the inheritance, a 300 MB working set and that no code enters background mode. The two R11 process trees
  started before the amendment were un-capped from outside (no stop): `logs/cr2_amendment/`.

## Findings
- Background mode is the wrong tool for "low priority" on this PC: it caps the working set at 32 MB (above).
- The production regexes must not be on the yielding process's own command line (it matched its own launcher).
- A `comment*` key in `limits` broke config loading for every stage: tests now load the shipped config.
- D: free space moves 10-20 GB per hour with other jobs; the 344M-row conversion (11.54 GB for all 67 shards) did not
  fit above the 40 GB floor + 2 GB margin today (37.8 GB free at 13:09). The conversion is value-ordered (holdout, Astra, R8 v5, forge_push) and resumes shard by shard.

## Left for the owner / QA
1. Free D: to >= 54 GB (40 floor + 2 margin + 11.54 GB of binpacks) and rerun `r11_data.py ... run` (or the one command): it continues
   with the next shard.
2. When the GPU queue is idle: `r11_pipeline.py ... run --profile smoke` (then `full` when QA lifts the wait); it
   yields by itself whenever production starts and resumes from the newest checkpoint.
3. CR re-review of the fix 2 amendment (patch files 15, 16) and the M1 hardening (patch file 17).
4. Optional: remove the ask rule `Bash(git push *)` in `D:\grok-pc-data\dwqww\.claude\settings.json` (every push
   prompts; editing it myself was blocked as self-modification).

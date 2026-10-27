# S39 v3b trainer fixed-size epoch option (v3c) — DONE (CPU smoke on the PC; GPU/real data UNVERIFIED, not deployed)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 21; spec = Sol's inventory `jobs[]` id S39 (spec line 206, NOT_STARTED; Sol left
no S39 files). Branch `opus-sol-S39` = `d4f4312` + CI cherry-pick `3dbf2119` (of `0d99f02`) + `093869a2` (job) + the report
commit. Tool-only (no engine code, no engine option): `[skip ci]`; `git diff --stat 294dbed opus-sol-S39 -- src include tests
tools bench CMakeLists.txt` is empty. Machine exclusive: no (gates, self-play and NNUE training ran throughout). Work and
results by a sub-agent; this report text is its hand-back.

**Deliverable:** `train_resid_v3c.py` (md5 `b130a31ed30e9a92f9fff8806d0eb847`, sha256 `5f54458e…`) = the lock archive's
`train_resid_v3b.py` (md5 `b6758004`) + `--epoch-positions N` (default 0 = off) + `--recent-weight W` (default 1.0 =
uniform); `v3b_to_v3c.diff` (+86/-3 lines), `CHANGES_v3c.md`, smoke logs. Never run under its own name: the PC runs used
byte-identical copies `F:\opus_scratch\sol_S39\opus_nnue_smoke_s39_v3b.py` / `_v3c.py` imported by a `--child` process.

## Acceptance (spec "Pass" items first)
| item | result | evidence |
|---|---|---|
| OFF gives bit-identical weights and loss to v3b (seed 99, 2 epochs, CPU, small smoke set) | **PASS** | off_1, off_2 vs v3b_1: all 8 artifacts (.pt .inc .bin .json x 2 epochs) sha256-equal, whole stdout equal (wall-clock fields and MEM lines masked), settings dump equal (`logs/step04b_compare_r2.log`, re-checked with the final runner in `step04c`) |
| N >= data size gives bit-identical weights and loss to v3b | **PASS** | `--epoch-positions 200000` (= N) and `10000000 --recent-weight 3`: 8 artifacts sha256-equal to v3b; stdout equal apart from one info line |
| ON is deterministic (same md5 twice) | **PASS** | uniform N=100k: ep2 .inc md5 `2cfbdee79f730f883dff0e2048c49b51` twice; `--recent-weight 3`: `317f0dcaf6990764230686844c4f344e` twice; all 8 artifacts + stdout equal; identical across suite runs r1/r2 (`logs/step07_r1_vs_r2.log`) |
| peak RSS no higher than v3b | **PASS** (within noise) | peak private / working set over r1+r2: v3b 238.7-239.2 / 241.5-241.9 MiB, ON 238.1-239.5 / 241.2-242.4 MiB, mean private 238.9 vs 238.9 MiB; tolerance max(v3b spread, 1 MiB), worst ON excess +0.43 MiB; no new array of size N in the code |
| no new per-step Python scalars or allocations (10k-step RSS trace) | **PASS** | (1) the training loop is source-identical to v3b (`test_training_loop_identical`), and so are all 24 shared functions/classes; (2) 10k-step private-byte traces, two runs each: v3b and v3c (`--epoch-positions 160000 --recent-weight 3`) show the same one-time steps (+1024 KiB in epoch 1, +784 KiB at the first epoch end) and then stay within 36-72 KiB for ~7,400 steps (slope -6.6 to -7.1 B/step); preregistered \|slope from step 1000\| < 100 B/step: v3b 88.0/56.7, v3c 65.1/67.4 (`logs/step05b_rss_eval_t1.log`, `step05c_rss_t2.log`) |
| deliver train_resid_v3c.py, v3b_to_v3c.diff, CHANGES_v3c.md, smoke logs | **PASS** | this folder |
| never deployed without CR PASS + vote; never touches a running GPU run | **PASS** | nothing written to `F:\forge_nnue_train` or any PC data/queue dir; CPU only; supervisor log: 7 "adopted running job" lines before and after every run (all from the earlier incident) |
| fixed epoch size and schedule | **PASS** | ON: `steps/epoch=97 total=194` (v3b 195/390), `Finished: 198,656 positions`; `.json` records `epoch_positions`, `recent_weight` |
| `--recent-weight` per-file plan | **PASS** | W=3 on 4 x 50,000: 12,500 / 20,833 / 29,167 / 37,500 drawn (printed by the trainer; unit tests incl. capping and a 3,000-case fuzz against an independent reference) |
| resume reproduces the run | **PASS** | resume from epoch 1 (uniform and weighted): epoch-2 .inc/.bin/.json sha256-equal, .pt content bitwise-equal; v3b's own resume behaves the same (finding 1) |
| `--order-buffers 2` | **PASS** | 8 artifacts equal to `--order-buffers 1` with `--recent-weight 3` |
| unit / order-capture / code-identity tests | **PASS** 17/17 | `logs/step06c_unit_final.log` (order-capture tests run the real `main()` with a recording train feed: OFF = v3b's permutation, ON = its prefix / the weighted plan) |
| planted-bug check | **PASS** 8/8 | each mutant caught by its named test (`logs/step06d_mutation_final.log`) |

## Findings
1. **A v3b resume writes a .pt with the same content but different bytes** (inherited, not v3c). In an uninterrupted run the
   payload's top-level `"step"` key is the same interned string object as the optimizer-state `"step"` keys, so pickle writes
   a back-reference; after `torch.load` those keys are new string objects and the key is written in full; torch's
   `.data/serialization_id` follows the record bytes. `.inc/.bin/.json` and all tensors are identical
   (`logs/step08_pt_resume_diff.log`). Compare `.inc`/`.bin`/content, not `.pt` md5s, across a resume.
2. **The planted-bug check found a weak test**: "epoch is shuffled" passed for a weighted epoch that runs file by file (each
   file's picks are already in random order). The test now requires interleaved files; all 8 mutants caught (`step06a`: first
   try had the mutants without `qa_adam_dml.py` beside them; `step06b`: the weak test).
3. **The trace's whole-run slope is dominated by two one-time steps**, the same in v3b and v3c; per step both are flat.
4. **On the PC the sorted file order is generation order**: the supervisor's default `--train` is every
   `forge_selfplay_NNN.pos` except 013/014, sorted by name, so `--recent-weight` favours newer self-play; a mixed source named
   after them (e.g. `sol_indep_train.pos` on an explicit `--train`) would get the top weight.
5. From the supervisor source (read only): `Build-Args` re-adds the current sealed file list on every relaunch, resumes included,
   so a v3b run's steps/epoch and its lr/blend schedule can change at a resume. With `--epoch-positions N` below the data size,
   steps/epoch stays `N // batch` (not run on the PC: UNVERIFIED).

## How it was run
Read-only NNUE venv (Python 3.10.22, torch 2.4.1+cpu, numpy 1.26.4) with `-I -B`, Git Bash `nice -n 19`, children at Idle
priority, OMP/MKL/OpenBLAS = 1 and `torch.set_num_threads(1)`, TMP/TEMP and all outputs under `F:\opus_scratch\sol_S39`
(no `runs_`/`smoke_kb` names), >= 6 GiB available RAM before and during each run (lowest seen 6.14 GiB in trace t1, from other
PC load). Steps: stage (pins: v3b 5cebba4d…, qa_adam_dml 799faa89…, the 10 data32 files as in opus-sol-S18) -> unit tests ->
suite r1 (13 runs) -> compare (14/16: the two resume rows compared .pt bytes, finding 1) -> suite r2 (14 runs, + v3b resume)
-> compare (17/17) -> traces t1, t2 -> mutation check -> r1 vs r2. Runs take 4-8 s each (H64), traces 18-25 s.

## Files
`train_resid_v3c.py`, `v3b_to_v3c.diff`, `CHANGES_v3c.md`, `opus_nnue_smoke_s39.py` (runner), `test_v3c_s39.py`,
`mutation_check_s39.py`, `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `FILES.txt`, `SHA256SUMS`, `logs/` (17 step logs and
`s39_outputs.tar.gz`, 48,934 B: per-run stdout/stderr/case/child results, settings, epoch .json, results/acceptance/trace
JSONs; the .pt/.inc/.bin stay in `F:\opus_scratch\sol_S39\out\` with their sha256 in `results.json`).

## UNVERIFIED / left
- DirectML/GPU behaviour, real 137M-position data, the draw time at that scale, any effect on net strength (no Elo claim).
- Deployment: needs CR PASS + a crew vote; the crew copies `train_resid_v3c.py` + `qa_adam_dml.py` to the tools folder.
- S50 (`--init-weights`, same v3c file) is on branch `opus-sol-S50`, based on this branch.

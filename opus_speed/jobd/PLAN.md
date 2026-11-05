# Job D - faster net pipeline: ranked plan from read-only profiling of the live npt line

Written 2026-11-05 11:48 PC clock (date read 11:47:05 in the same step) by worker jobd (fable, board slot S1) for the
Forge speed job (branch opus-speed-20261105). Scope as briefed: a PLAN plus small read-only profiling scripts for the
NNUE trainer's data loading and net export. Nothing was run on the GPU; the only CPU runs were log parsing (seconds,
CPUs 0-1 at Idle). No file outside `F:\ospd\wt\opus_speed\jobd\` and `F:\ospd\jobd\` was written. Every effect size
below is UNPROVEN unless it quotes a measurement with its source. The trainer is the nnue-pytorch based line
(GPL-3.0): ideas only, its source was not read; the numbers come from the owner's adapter / guard / keeper logs and
from the skills.

## 0. Where the minutes go today (measured from logs)

Live recipe (adapter log `D:\forge_nnue_train\runs\<run>.log`, line `cmd:`): K32H3^, L1 1024, batch 16384,
`--num-workers 4 --threads 2`, epoch 152.5M positions = 9,307 steps, 8 epochs, `--no-filtered --no-wld-filtered`,
`--network-save-period 1` (one 1.44 GiB checkpoint per epoch), validation 1M positions (61 batches), the J1 binpack
`F:\forge_j1_data\forge_train_001-039_ex013-014_j2.binpack` (305.0M records, frozen 2026-10-29).

| stage | today | source |
|---|---|---|
| one epoch, wall | 11.0-11.7 min (s48 try 3, 10:24-11:21 today); 15.0-17.6 min (s44-s47, Nov 4); 7.7-9.5 min (s4-s6, Oct 30-31) | `logs/npt_epochs_last12.txt`, `logs/npt_epochs_s4_s9.txt` (tools/npt_epochs.py) |
| one run (8 epochs) | 2.08-2.28 h (s38-s46); 1.17 h (s6, Oct 31) | same, summary table |
| it/s while the guard lets the trainer run (it/s / run_frac) | mean 28.9, range 20.6-32.1 over 91 epochs; ~29-32 on Oct 31 AND on Nov 4 | `logs/npt_epochs_last12.txt` col running_its (derived estimate, see D1) |
| run_frac of the GPU guard (share of wall time the trainer is not suspended) | daily means 1.00 (Oct 28-29, older trainer), 0.90 / 0.95 (Oct 30-31, mixed trainers), 0.64 / 0.57 / 0.39 / 0.33 (Nov 1-4), 0.53 (Nov 5 to 11:44); this recipe's own epochs on Oct 30-31 (s4-s6): 0.52-0.90 | `logs/guard_duty_daily.txt` (tools/guard_duty.py on `F:\forge_nnue_train\gpu_guard.log`); `logs/npt_epochs_s4_s9.txt` col run_frac |
| GPU utilisation / run_frac (GPU busy while allowed to run) | 0.68-1.01 per day Nov 1-5; 0.76-0.94 per hour today | same, cols util_mean / util_over_run_frac (keeper tsv joined) |
| records read per kept position (preskip / total) | 9.95-10.00 every epoch | `logs/npt_epochs_last12.txt` col preskip_x |
| segment rates inside an epoch (20 % marks) | first fifth 15-25 it/s, then 8-15 it/s (read-ahead buffer drains, then the duty cycle sets the pace) | same, col seg_its |
| validation per epoch | 1-15 s | same, col val_s |
| checkpoint hand-over + epoch start (wall - train - val) | -13..+16 s, i.e. within the progress bar's rounding; 7-12 s on the first epoch of a try | same, col overhead_s |
| RAM-guard abort (exit 97) + backoff + repeated epoch | s47 resume: 4 aborts, every one right after "Epoch 6 (Train): 100%" (during the end-of-epoch validation / checkpoint), 49.8 min of finished training thrown away, 29 backoff min -> the last 2 epochs took 1 h 51 min (07:19-09:10) and epoch 6 was trained five times; s48: 2 aborts at 60 % and 80 % of epoch 2, 19 min lost, 6 backoff min, epoch 1 trained three times (12.0 + 10.4 + 9.8 min) | `D:\forge_nnue_train\runs\...w4_s47.resume1.log`, `...w4_s47\npt_try[1-4].log`, `...w4_s48.log`, `logs/npt_epochs_last12.txt` summary (abort_at column) |
| net export (serialize to .nnue, CPU, Idle, mask 0xF) | 5-15 s each, 70.3 MB, done by the keeper after every run | `logs/export_times.txt` (tools/export_times.py on `D:\forge_nnue_train\exports`) |
| checkpoints | 1.44 GiB each, 10 per run s48 (14.4 GB: 8 epochs + 2 repeats) on C: via junction; spacing median 11.7 min | same |
| conversion .pos -> binpack (the J1 files) | 39 shards, 305M records, 17:18:18 -> 17:24:37 = 6.3 min incl. verify, 2 threads | `F:\forge_j1_data\convert.log` |
| hours without an npt trainer alive | 14.2 h on Nov 4, 7.3 h on Nov 5 up to 11:44 (supervisor restarted 07:19:54 after no entry since 2026-11-04 09:43; the keeper tsv has 2 rows between 09:40 Nov 4 and 07:20 Nov 5) | `logs/guard_duty_daily.txt` col no_trainer_h; `F:\forge_nnue_train\supervisor.log` |

Reading: the trainer itself has not become slower (the derived running rate is ~29-32 it/s on Oct 31 and on Nov 4);
the wall time per epoch doubled because the GPU guard suspends the trainer for a growing share of every second, and a
run loses a further 0.7-1.8 h whenever the RAM floor trips. Loading, export, validation and checkpointing are not
where the minutes go at the moment.

## 1. Ranked items

### D1. The GPU guard's duty cycle (biggest; owner / QA item - Job D only measures, never touches the guard)
- Where the time goes: `F:\forge_nnue_train\gpu_guard.log` "ok" lines (one per 10 min) carry `run_frac` and
  `avg_thr`; per day (`logs/guard_duty_daily.txt`): run_frac 1.00 / 1.00 / 0.90 / 0.95 on Oct 28-31, then 0.64, 0.57,
  0.39, 0.33 on Nov 1-4, 0.53 today; mean throttle `r` 0.36 -> 0.67 (the guard's cap RMAX is 0.70 = the trainer rests
  70 % of every second). Same recipe, same data: s6 (Oct 31) 8.3-9.2 min per epoch, 1.17 h per run; s46 (Nov 4)
  15.0-16.7 min per epoch, 2.12 h per run (`logs/npt_epochs_s4_s9.txt`, `logs/npt_epochs_last12.txt`).
- What changed on 2026-11-01 (consistent with the logs; QA to confirm): the guard reads temperatures from the HWiNFO
  CSV first and from the ADLX feed only as a fallback; the ADLX feed reports fan PWM 0 by design, so on it the guard
  applies its stricter no-fan thresholds (memory junction target 80 C, hard 85) instead of the fan-curve ones (83 / 86)
  (`F:\forge_nnue_train\tools\gpu_guard.ps1`, header lines "fan curve active" / "fan PWM low / ADLX feed", function
  `Thr`). The source column of the ok lines is `hwinfo` for every window up to 2026-10-31 23:51:46 and `adlx` for
  every window since 2026-11-01 (0 hwinfo in 588 windows on Nov 4-5), although the HWiNFO CSV is written every 2 s
  and the keeper reads it fine (STATUS "hwinfo, 147 samples"). The guard's row filter in `Read-Row` keeps only rows
  matching `^\d\d\.\d\d\.\d{4}` (two-digit day and month); HWiNFO writes the day unpadded: `5.11.2026,11:36:8.779`
  (tail of `C:\Users\Administrator\grok-pc\nnue\tools\hwinfo\gpu_sensors.csv`, read 11:36 today), while the keeper's
  own pattern allows 1-2 digits. `tools/guard_duty.py --probe-csv` reproduces it: the guard pattern accepts 0 of the
  last 9 rows, the keeper pattern 9 of 9. The pattern also wants a two-digit month: from 2027-01-01 to the end of
  September the fallback (and the no-fan thresholds) would hold for nine months, not nine days. With the memory
  junction sitting at 80-82 C under the live load (keeper
  STATUS 11:23: max 82 C; ADLX row 11:36: 80.0 C, fan 1230 RPM, PWM reported 0) the integral throttle climbs to
  r = 0.5-0.7 and stays there.
- Change (own words, for the owner): make the guard accept the unpadded date (the keeper's pattern), or feed it the
  fan PWM so the fan-curve thresholds apply when the fan really runs; alternatively raise the ADLX-mode target to the
  fan-mode one when the ADLX row's fan RPM is > 0. Nothing for Job D to run: the guard is QA's.
- Expected effect (UNPROVEN): run_frac back towards the Oct 31 level (0.52-0.95) -> epoch 8-10 min instead of 11-17,
  a run ~1.2-1.5 h instead of 2.1-2.3 h. Upper bound at run_frac 1.0 and 29 it/s: 5.3 min per epoch, ~50 min per
  run, which the card's thermals may not allow (memj would climb; the Oct 28-29 run_frac 1.00 days ran the older
  trainer, not this recipe).
- How to measure safely: read-only, `tools/guard_duty.py --from <date> --keeper <tsv>` before and after; the
  per-epoch view with `tools/npt_epochs.py --last N`. Free A/B without anybody touching anything: on 2026-11-10 the
  day becomes two-digit again and the guard will read HWiNFO by itself; if D1 is right, the `src` column flips to
  `hwinfo` and run_frac rises that day (and falls again on 2026-12-01).
- Risk: the thresholds exist to keep memory junction <= 90 C (Couns's limit); a lighter throttle raises memj - the
  guard's hard suspend at 86 (fan mode) still protects. Effort: one pattern in one script (owner); a day of logs to
  confirm. Falsification: if run_frac stays at 0.3-0.5 with src=hwinfo, the cause is thermal, not the feed.

### D2. RAM-floor aborts repeat whole epochs (adapter / guard_exec owner item; Engine NNUE decides)
- Where the time goes: the in-process guard (`F:\opus_scratch\r6\tools\guard_exec.py`, R6_MIN_FREE_GB = 6) exits 97
  when free physical RAM dips under 6 GB, although commit free was 11-21 GB at every trip (`guard_runs.jsonl` in the
  run folders; adapter lines "child exit 97 min free 5.4-6.1 GB min commit free 11-23 GB"). The adapter's soft guard
  suspended the child at the same moment and saw RAM recover after 3 s, 4 s, 22 s and 120 s (s47.resume1.log,
  s48.log) - the dips are transient. Where they hit matters: all four s47 resume aborts came right after
  "Epoch 6 (Train): 100%" with the trainer's own private memory at 7.8-8.4 GB (`guard_runs.jsonl`, `npt_try[1-4].log`
  of s47), i.e. in the end-of-epoch validation + checkpoint save, where the trainer itself takes a transient copy of
  its 1.44 GiB state - the worst moment to die, since the finished epoch has no checkpoint yet. s48's two aborts hit
  mid-epoch (60 % and 80 % of epoch 2). A resume restarts the epoch whose checkpoint it loads, because the epoch-E
  checkpoint is written before that epoch's validation and scheduler step (skill forge-nnue-pytorch-amd, R11
  section); so each trip costs the training thrown away (a whole epoch when it hits at 100 %) + the backoff
  (2 / 4 / 8 / 15 min) + one repeated epoch (10-16 min). Today: s47 spent 3.68 h of active wall for 8 epochs instead
  of ~2.1 (epoch 6 trained five times), s48 ~45 min extra on a 2.45 h run (`logs/npt_epochs_last12.txt`: aborts97,
  backoff_min, lost_train_min, epochs_repeated, abort_at). Nine runs before (s38-s46) had 0 aborts: the trips come
  with crew / agent load on the PC on top of the trainer's own end-of-epoch spike.
- Change (own words): (a) debounce the hard floor - abort only when free RAM has been under the floor for 30-60 s, or
  trigger on commit-free with physical-free as the soft (suspend) signal only; and never abort during the trainer's
  own end-of-epoch save (the guard can see the checkpoint file appearing, or simply hold its verdict for the save's
  seconds); (b) resume at E+1 when the loaded
  checkpoint's epoch already finished validation (the R11 pipeline's entry does this, `r11_next_epoch`, skill
  forge-nnue-pipeline) - saves one repeated epoch per trip; (c) shorten the adapter's backoff when free RAM is already
  back above the soft threshold (the 2 / 4 / 8 / 15 min waits were full length while RAM had recovered in seconds);
  (d) lower the trainer's RAM: the default loader keeps up to (consumers + 8) windows of 2^20 x 224 B per stream and
  reads ~10x ahead (skill forge-npt-fast-loader); the fast loader peaked at 166 MB for a full epoch and cut the CPU
  run's peak private memory 6.2 -> 4.1 GB (same skill, measured) - D3 helps D2.
- Expected effect (UNPROVEN): on days like today 0.7-1.8 h per affected run; zero on quiet days.
- How to measure: `tools/npt_epochs.py --last 20` summary (aborts97, backoff_min, epochs_repeated, epoch_share);
  the free-RAM timeline around each exit 97 is in the HWiNFO CSV column 7 "Physical Memory Available [MB]"
  (one row per 2 s; a binary-search reader like `opus_r14b/tools/gpu_util_stats.py` on branch opus-r14b-status can
  cut the window) - not implemented here.
- Risk: the floor exists because of the 2026-10-29 incident (a trainer died at the commit limit while a benchmark
  ran next to it; skill forge-pc-rules R6). Debouncing physical-free is safe only if commit-free stays the hard stop.
  Effort: small (adapter / guard_exec are own code; the E+1 resume is a trainer entry patch, GPL run-only folder).

### D3. Adopt the R14-B fast loader (built, proven byte-identical; GPU window still owed)
- Where the time goes: the default loader decodes every record to a board, keeps 1 in 10 (preskip_x 9.95-10.00 in
  every epoch today), shuffles 224-byte entries and costs 2.45 CPU-us per kept position; the fast loader 0.34 us,
  8.65x kept positions/s in the CPU ABBA, 29.8 s for a full 152.5M epoch alone, 166 MB peak (skill
  forge-npt-fast-loader, measured 2026-11-02; `GPU_REQUEST.md` in `opus_r14b/item1/` on branch
  opus-r14b-fast-loader). At the observed running rate (29 it/s x 16384 = 475k kept/s)
  the default loader needs ~1.2 CPUs of the trainer's mask, the fast one ~0.16.
- Honest expectation (UNPROVEN): while the trainer runs it is mostly GPU-bound today (util / run_frac 0.68-1.01 per
  day, 0.76-0.94 per hour), so the loader can add at most the missing 0-30 % to it/s at mask 0xF; it matters more when
  the keeper narrows the trainer to mask 0x3 (only 30 of 1,426 keeper ticks since Oct 30 had "Opus R12 procs" > 0,
  `npt_keeper_log.tsv` col r12) and for D2 (RAM). The GPU_REQUEST's done criterion ">= 90 % GPU util" cannot be met
  while D1 throttles: util = run_frac x busy-while-running; judge the window by util / run_frac and running_its instead.
- Change: as in the skill's hand-over - `--npt-repo <switched copy> --npt-extra --fast-loader` on the adapter, after
  `fl_acceptance.sh` on the copy; never patch the live trainer folder.
- How to measure safely: the owed 30-minute queue gap (GPU_REQUEST.md), then `tools/npt_epochs.py` on that run's
  adapter log + `tools/guard_duty.py --hourly` for the same window; CPU-side ABBA is already done (advisory numbers).
- Risk: scope refusals built in (feature set, DDP, filtering); the w4 stream is a different sample from the w1
  reference stream (same distribution, TVD < 0.001, skill). Effort: install + one GPU window.

### D4. Hours without an npt trainer (scheduling; flagged, not a pipeline item)
- Nov 4: 14.2 h, Nov 5: 7.3 h up to 11:44 (`logs/guard_duty_daily.txt`). The supervisor log has no entry between
  2026-11-04 09:43:32 (s47's 7th checkpoint) and the restart 2026-11-05 07:19:54; the guard saw no trainer from 09:52
  to 05:52, the GPU warm (hot 54-58, memj 76-82) until 21:52 - another job used it - and cold (hot 32-42) 23:52-05:52.
  The keeper STATUS says "chaining disabled in config" and lists the next queue line. Owner's call; the pipeline
  cannot win back 6 cold hours by any loader change.

### D5. First epoch warm-up (compile + cold caches) - small
- Epoch 0 of a try is 1-2 min slower than the following epochs and its first fifth runs at 15-19 it/s then 8-12
  (s45: 16.6 vs 15.2-17.2; s48: 12.6 vs 11.0-11.7; `seg_its` column). Caches are on F: (`TRITON_CACHE_DIR`,
  `TORCHINDUCTOR_CACHE_DIR` in the adapter's ENV). Nothing to change unless the caches get cleared; ~1-2 min per run.
  Risk: none. Effort: none now; if the caches move or get cleared, keep them on a disk that stays (owner).

### D6. Read amplification (10 records read per kept position) - keep in view, do not pre-filter naively
- Each epoch reads ~1.5 G records = ~52 GB of the 10.4 GB binpack, i.e. the file is streamed ~5x per epoch from the
  page cache; under RAM pressure (D2) the cache is the first thing Windows drops and the reads go to F:. The HWiNFO
  CSV has "Read Rate [MB/s]" (column 247) for a log-only check (not done). The fast loader removes the decode cost,
  not the bytes. A pre-filtered binpack is in the what-not-to-do list below (it would fix one random subset).
  Risk of acting on it: a differently sampled training stream (net quality, UNPROVEN either way). Effort: a log-only
  read-rate check is an hour; any data change is an Engine NNUE decision.

### D7. Training data frozen since 2026-10-29 (freshness, not speed; UNPROVEN benefit)
- Every seed run (s4..s49) trains on the same 305.0M records while self-play adds ~37.5M positions per day (skill
  forge-nnue-data). Conversion is cheap (6.3 min for 305M, `F:\forge_j1_data\convert.log`; the R11 writer 466,506
  records in 0.27 s); the cost is the holdout proof and a queue switch at a run boundary (R11 data stage, skill
  forge-nnue-pipeline). Not a speed item; listed because "faster net pipeline" is pointless if the data never moves.

### D8. Export, validation, checkpoint scoring - nothing to do
- Export 5-15 s per net (`logs/export_times.txt`), validation 1-15 s per epoch, checkpoint hand-over within the
  rounding of the progress bar; the keeper ranks checkpoints by the minimum validation loss over epochs
  (`metrics.csv`, prune_plan.txt). The expensive scoring is the gate, out of scope here. Risk: none. Effort: none -
  nothing to change.

### D9. Transfer / Python overhead per step - only measurable in a GPU window
- R6's smoke-size breakdown put loader + H2D + Python at 4.0 of 12.2 ms per step (skill forge-nnue-pytorch-amd); at
  the live size the split is unknown. `bench/profile_train.py` in the R6 clone gives a per-phase breakdown; run it only
  in a granted window, never next to the live trainer. UNPROVEN whether anything is left after D3. Risk: a GPU run
  next to the live line (the 2026-10-29 incident) - window only. Effort: one profiling run in a granted gap.

## 2. What not to do
- Do not read the loader's speed off the progress bar's it/s: it averages over suspended seconds (D1) and over the
  read-ahead drain at the start of an epoch (first fifth 15-25 it/s, then 8-15).
- Do not compare epoch minutes across days without run_frac and the trainer mask next to them (`npt_epochs.py`
  prints run_frac; the keeper tsv column r12 says when the mask was 0x3).
- Do not pre-filter the binpack with one random draw per record: the live stream draws anew on every pass (unique
  positions 122M after epoch 0, 285M of 305M after epoch 6, `npt_try3.log` of s48); a single draw would freeze one
  ~30M subset. The filter is stateful (piece-count history, one RNG), so an exact offline copy is not a per-record
  rule either (own-words spec `LOADER_SPEC.md`, section 3).
- Do not raise batch / workers / L1 while the live trainer runs (the 2026-10-29 incident; skill forge-pc-rules R6),
  do not run anything on the GPU without a granted window, and never load the HIP runtime next to the live line.
- Do not touch the guard, its thresholds, the keeper, the queue, STOP/PAUSE files, or re-prioritise any process:
  report D1 / D2 to the owner; the falsification test of D1 happens by itself on 2026-11-10.
- Do not use background mode (32 MB working-set cap) for any pipeline process; Idle + I/O very low + memory priority
  low is the recipe (skill forge-nnue-pipeline).
- Do not overwrite `F:\forge_j1_data\*.binpack` (the live trainer reads them); a refreshed binpack gets a new name.
- Do not run own CPU work on CPUs 0-1 next to the trainer while timing it: the trainer's mask 0xF includes them at the
  same Idle class. s48's last epoch (11:21-11:38 today) ran at 9.5 it/s with running_its 22 while this job's log
  parsing and the coordinator's checks sat on CPUs 0-1 - one epoch, cause UNPROVEN, but keep timing runs clean.

## 3. Measurement protocol (all read-only, CPUs 0-1 at Idle, seconds each)
1. `tools/guard_duty.py --from <day> --keeper C:/Users/Administrator/grok-pc/forge_push/npt_keeper/npt_keeper_log.tsv`
   -> run_frac, throttle, source, util / run_frac, no-trainer hours per day; `--hourly` for a window;
   `--probe-csv <hwinfo csv>` for the D1 pattern check.
2. `tools/npt_epochs.py --last N` -> per epoch wall / train minutes, it/s, kept pos/s, segment rates, preskip ratio,
   validation and hand-over seconds, run_frac and running_its; per run tries, aborts, repeats, backoff, epoch_share.
3. `tools/export_times.py` -> export seconds per net and checkpoint sizes / spacing.
4. Before / after any change: the same three commands on the same date range; quote running_its (the trainer's own
   pace), run_frac (the guard), epoch_share (restarts) separately, so a change in one is not booked to another.
5. GPU-window measurements (D3, D9) only in a granted gap, with the keeper's HWiNFO CSV as the utilisation source
   (`opus_r14b/tools/gpu_util_stats.py`), and util / run_frac as the figure of merit.

## 4. Tools (own code, stdlib only, read-only; each prints usage with -h)
Run with `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B <tool> [opts]`.
- `tools/npt_epochs.py [--runs-dir D:/forge_nnue_train/runs] [--run GLOB] [--last N] [--guard F:/forge_nnue_train/gpu_guard.log] [--summary]`
  Parses the adapter logs (`<run>.log`, `<run>.resume*.log`) and the trainer stdout (`<run>/npt_try*.log`, split into
  sessions at "Using log dir ... version_K" because a resume appends to the same file), joins the guard's 10-minute
  windows. Tested: `--last 5`, `--last 12`, `--run "...w4_s?"` -> `logs/npt_epochs_*.txt` (exit 0).
- `tools/guard_duty.py [--guard PATH] [--from D] [--to D] [--hourly] [--keeper TSV] [--probe-csv CSV --rows N]`
  Tested: daily since Oct 28 with keeper join and probe -> `logs/guard_duty_daily.txt`; hourly today ->
  `logs/guard_duty_hourly_nov5.txt` (exit 0).
- `tools/export_times.py [--exports-dir D:/forge_nnue_train/exports] [--runs-dir ...] [--last N]`
  Tested -> `logs/export_times.txt` (exit 0). Export seconds = mtime(.nnue) - creation time(.nnue.err).
Limits: timestamps come from the adapter's 1-second poll and the guard's 10-minute windows; running_its assumes no
progress while suspended; the first epoch of a try has no previous checkpoint, so its wall time starts at the try's
start line (includes start-up).

## 5. Unverified (say so when quoting)
- D1's cause (the date pattern) is consistent with every log read but not confirmed by QA; the size of the recovery
  and whether thermals then cap run_frac below 1 are UNPROVEN. The archived HWiNFO CSVs in the hwinfo folder start
  2026-10-16 (days >= 10 only), so no earlier data can show whether the padding was ever different; the 2026-11-10
  flip is the only free test.
- running_its (it/s / run_frac) is a derived estimate; nobody measured the trainer at run_frac 1.0 on this recipe.
- All expected effects (D1-D3, D5-D7, D9) are UNPROVEN; no Elo or speed claim is made.
- The D2 trip frequency outside today (0 in s38-s46, 6 in s47-s48) depends on what else runs on the PC.
- D6's I/O effect under RAM pressure was not measured (the HWiNFO read-rate column was found, not analysed).
- The s48 last-epoch slowdown next to own CPU work is one observation.

## 6. Sources (read-only)
- `D:\forge_nnue_train\runs\*.log`, `*.resume*.log`, `<run>\npt_try*.log`, `<run>\guard_runs.jsonl`
  (junctions to `C:\forge_nnue_train\runs\`); `F:\forge_nnue_train\supervisor.log`; `F:\forge_nnue_train\gpu_guard.log`,
  `gpu_guard_status.txt`, `tools\gpu_guard.ps1`, `idle_watchdog.log`, `adlx_sensors.csv`;
  `C:\Users\Administrator\grok-pc\forge_push\npt_keeper\STATUS.md`, `npt_keeper_log.tsv`, `npt_keeper_config.json`,
  `best_history.txt`, `prune_plan.txt`, `forge_npt_keeper.ps1` (row pattern); `C:\Users\Administrator\grok-pc\nnue\tools\hwinfo\gpu_sensors.csv` (tail only);
  `D:\forge_nnue_train\exports\*`; `F:\forge_j1_data\convert.log`, `loader_check.json`; the adapter
  `F:\forge_nnue_train\tools\train_res*nnuepytorch_v2.py` (by glob; argument list and ENV only).
- Skills: forge-nnue-pipeline, forge-npt-fast-loader, forge-nnue-pytorch-amd, forge-nnue-data, forge-relabel-job,
  forge-pc-rules; R14-B item 1 `GPU_REQUEST.md`, `LOADER_SPEC.md` (own words).

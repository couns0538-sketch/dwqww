# Independent read-only review: GPU-window code of the 30-h job (D:\o30\wt, branch opus-30h-20261103)

Reviewer: the independent agent session that reviewed the R14 finish (same binding rules). Nothing on D:\o30 was
started, stopped, signalled, built or changed; the only writes are this folder (REVIEW.md, scripts\feed_check.py,
feed_check.out, modified_files.diff). Started 2026-11-04 11:02, written 11:12 PC clock (`date`); the trainer r1_kb4,
its guard and its watcher were live throughout.

## Scope and method

- Range: base 5ea2bc2d does not exist in the worktree; used the parent of f206e07a as instructed:
  68bb6491..HEAD (HEAD da62a1a8), paths opus_30h/a and opus_30h/skills. Reviewed: forge_v2_bullet_o30\src\forge_r.rs
  (+2/-2) and main.rs (+19/-1), import_v2r.py (new), o30_gpu_guard.py (new), gpu_run_o30.bat (new, CRLF),
  gpu_ckpt_watch.sh (new), build_bullet_o30.bat (+2), net_pack.sh (+4/-2), the v2net skill's GPU section.
- Background read: GPU_PATH.md, export_v2r.py, o30_v2net.py, o30_data.py / o30_data_npy.py (index producers), the
  library copy D:\o30\bullet (trainer\src\reader.rs, optimiser\adam.rs, optimiser.rs, model\weights.rs,
  bullet_lib\src\value\save.rs, value.rs, trainer\schedule.rs), logs D:\o30\gpu\*.out, *.guard.log, r1_kb4_scores.tsv,
  WINDOW.md.
- Checks run (read-only, through D:\a14\tools\opus_lowrun.py --mask 0x4): py_compile of o30_gpu_guard.py, import_v2r.py,
  export_v2r.py (OK); scripts\feed_check.py = the guard's own column matching and tail parsing applied to the live
  HWiNFO CSV (one column per prefix, newest row 52.0 / 74.0 / 42.5 / 47.0 at 11:08:58, age 1.8 s); sha256 of the warm
  start proof; grep of the live logs.

## Findings

| ID | Severity | file:line | one line |
|---|---|---|---|
| G-001 | SHOULD | opus_30h/a/forge_v2_bullet_o30/src/main.rs:308-320 | A warm start (O30_INIT_DIR) without an explicit O30_CLIP keeps bullet's default clip +-1.98 and silently clips the loaded lock weights (max 3.47) at the first optimiser step; without O30_DECAY=0 the decay 0.01 shrinks it ~7 %. Nothing enforces the clip the importer prints. |
| G-002 | SHOULD | opus_30h/a/o30_gpu_guard.py:68-82 (NPT_MARKS line 29) | The yield check matches substrings of python command lines ('forge_j1_data', 'nnue-pytorch', 'forge_nnue_train'); the npt interpreter is presumably F:\nnue_pytorch\venv\Scripts\python.exe (underscore; the only torch venv seen on this PC - an inference, the real launch line was not read), which matches none of them, so the yield depends on the keeper passing a data / run path that contains a mark. |
| G-003 | NIT | opus_30h/a/o30_gpu_guard.py:124-165 | No psutil call in the poll loop is wrapped: any uncaught exception (no reachable trigger was demonstrated; the is_running() checks narrow the exit race to microseconds) would end the guard while the child trains on without thermal / yield protection and would log `end: trainer exit None`, which the watcher takes as the end of the run. |
| G-004 | SHOULD | opus_30h/a/gpu_ckpt_watch.sh:21,41-54 | The watcher can never finish on (a) a run without a checkpoint (unquoted glob at line 50 stays literal -> left=1 forever), (b) a checkpoint whose export fails permanently (no --hidden is passed: every run with hidden != 256 fails export_v2r.py's size check; a checkpoint whose quantised.bin the library failed to write is skipped silently), and it takes kb map / mirror from the operator instead of the run's own first log line (a wrong --mirror exports a mis-labelled net and scores it as if correct). |
| G-005 | SHOULD | opus_30h/a/o30_gpu_guard.py:145-150 (design) | Yield by suspension keeps the trainer's GPU memory and context; an npt run that starts during the window then has less VRAM. WINDOW.md promises npt is never touched; the footprint is not measured or stated. |
| G-006 | NIT | opus_30h/a/o30_gpu_guard.py:131-132,143-144 | A stale feed / unreadable python command line suspends for as long as it lasts with a single SUSPEND line: a dead HWiNFO logger or a long-lived unreadable python.exe silently costs the rest of the window. |
| G-007 | NIT | opus_30h/a/o30_gpu_guard.py:134 | GPU utilisation is parsed (`util`) and never used; WINDOW.md's "utilisation near zero before the first minute" stays a manual check. GetPriorityClass is not read back (opus_lowrun does). |
| G-008 | NIT | opus_30h/a/forge_v2_bullet_o30/src/forge_r.rs:239-243 | partition_point on skip and override indices assumes sorted arrays; the producers sort by construction (np.flatnonzero; row-ordered append) but the reader does not assert it - an unsorted override file would apply no jobA labels without any error. |
| G-009 | NIT | opus_30h/a/gpu_run_o30.bat:33 | Default GUARD_MASK 0x38 includes CPU 3, which WINDOW.md gives to the Astra overlap scan (production04 was on CPU 3 at 10:37); a run started before that scan ends shares the core. |
| G-010 | NIT | opus_30h/a/gpu_run_o30.bat:12-13,28 | Refuses an existing <run> dir and .out but not <run>.guard.log (append mode); a stale `end:` line from an earlier same-named guard log would stop the watcher early. `if "%GUARD_EXTRA%"=="" set GUARD_EXTRA=` is a no-op and breaks on quotes. |

### G-001 - warm start needs the clip it depends on (main.rs:308-320)

adam.rs:56-61: every update is `weight*(1-decay*rate) - rate*step` then `.max(min_weight).min(max_weight)`; the clip
is applied after every step, so loaded weights outside +-1.98 are cut on step 1. import_v2r.py prints
"max |weight| 3.47 (needs O30_CLIP >= that)" but nothing in the trainer checks it; the two env variables are optional
(`if O30_CLIP.is_ok() || O30_DECAY.is_ok()`). The proof run used O30_CLIP=7.99 and lr 0, so it could not show the
failure mode. Fix (minimal; requires only the variable whose absence corrupts the numbers at step 1 - the decay's
slow 7 % is documented, and the skill's recipe already says O30_DECAY=0):
```
     if let Ok(dir) = std::env::var("O30_INIT_DIR") {
+        assert!(std::env::var("O30_CLIP").is_ok(),
+                "O30_INIT_DIR needs an explicit O30_CLIP >= max |loaded weight| (default 1.98 would clip the net)");
         println!("warm start from {dir}/optimiser_state");
```
(The warmproof01 run was `O30_CLIP=7.99` without O30_DECAY on a binary that predates O30_DECAY; the assert above keeps
that recipe valid.) Better: after `load_from_checkpoint`, read the host weights' max |w| and assert `clip >= max`.

### G-002 - the yield mark set is a guess about another process's command line (o30_gpu_guard.py:29,68-82)

`' '.join(p.cmdline())` of the npt trainer presumably starts with its interpreter
`F:\nnue_pytorch\venv\Scripts\python.exe` (underscore). That is an inference from the only torch venv seen on this PC
(the D:\a11-runtime test warnings in the R13 log point at F:\nnue_pytorch\venv); the keeper's real launch line was not
read. That path contains none of the three marks, so the check fires only if the data path ('forge_j1_data') or the
run root ('forge_nnue_train') appears as an argument. If the keeper starts npt with relative paths (cwd-based), the
guard does not yield and the trainer shares the GPU with npt. Fix: add `'nnue_pytorch'` to NPT_MARKS and also compare
`p.exe()` against the npt venv interpreter; record the keeper's real launch line (from its log) in WINDOW.md and test
the predicate against it once.

### G-003 - an uncaught guard exception would mislabel the run end and leave the trainer unguarded (o30_gpu_guard.py:124-165)

suspend() / resume() / is_running() are called without any `except`; feed.read() and npt_like() catch their own
errors. No concrete trigger was demonstrated (the child's pid stays reserved while Popen holds its handle, and
AccessDenied on the guard's own Idle child is not expected), so this is a robustness gap, not an observed failure.
If an exception did escape: `finally` resumes the child if it was suspended, logs `end: trainer exit None`
(child.poll() is None) and the guard exits with a traceback; the child is an ordinary process whose parent ended and
keeps training with no thermal limits and no yield. gpu_ckpt_watch.sh:48 greps ' end: ' and, once the checkpoints
present are scored, exits - every later checkpoint stays unscored. Fix:
```
-                if proc.is_running():
-                    proc.suspend()
+                try:
+                    proc.suspend()
+                except psutil.Error as error:
+                    say(f'suspend failed: {error}'); time.sleep(2); continue
```
(same for resume), and in `finally`: write `end:` only if `child.poll() is not None`, else
`guard failure: trainer pid still running UNGUARDED` and exit non-zero.

### G-004 - the watcher's termination and parameters (gpu_ckpt_watch.sh)

- line 50: `for ck in "$dir"/*-[0-9]*` without `shopt -s nullglob`: with no checkpoint the literal pattern is tested,
  `.done` is absent, `left=1`, the loop never ends even after `end:`.
- line 46: a failing score_one is retried every 60 s without a cap; the run can never be declared done.
- line 21: `export_v2r.py ... --kb-map "$kb" $mir` without `--hidden`: export_v2r.py:68 refuses every checkpoint of a
  run with hidden != 256 (the usage of gpu_run_o30.bat allows [hidden]).
- line 44: a checkpoint whose quantised.bin the library could not write (save.rs:39-42 prints and continues) is skipped
  silently and counted as not done forever.
- kb map and --mirror come from the operator's arguments; the run's first log line
  (`forge_v2_bullet r: kb 4 (rank4) mirror false hidden 256 ...`) is authoritative and could be parsed; a mismatch now
  produces a mis-labelled .nnue2 whose scores look valid.
Fix: `shopt -s nullglob`; parse kb map / mirror / hidden from `D:\o30\gpu\<run>.out` line 1 and refuse a mismatch; a
retry cap (e.g. 5) that writes `<ckpt>.failed` and counts as done; on `end:` with zero checkpoints, exit with a message.

### G-005 - suspension keeps VRAM (design)

psutil.suspend freezes the threads; HIP allocations stay. The 4-h window rule is "npt never touched"; an npt run
starting into a suspended trainer sees less VRAM. Either terminate the trainer on npt detection (checkpoints exist
every 87 superbatches, loss < 10 min) or measure the footprint (HWiNFO has a GPU memory column) and state the owner's
acceptance in WINDOW.md.

## Checked, no issue found (with the evidence used)

- forge_r.rs:292-313 read_chunks: the callback contract is "return true to stop" (reader.rs:51-88 returns true after
  the final batch or on a mapping error); the fix `if f(slice) { return; }` is correct, and smoke01.out shows the
  inverted version dying after one batch ("Data loader ended before all scheduled batches completed"). skip_count is
  consumed in rows across chunk boundaries, matching `batch_size * start.total_batches()` of the loader; chunks are
  deterministic in (seed, c), so a resume would continue the stream - but main.rs:324 always starts at superbatch 1,
  so no resume path is exercised by the GPU runs. The stream never ends by itself; the schedule ends it.
- Warm start layout: import_v2r.py writes l0w [inputs][H] as stored and l1w as the raw [2H][8] (the saved format is
  its transpose, export_v2r.py reads [8][2H]); values int16/4096 exact in f32; ids l0b, l0w, l1b, l1w; zero momentum and
  velocity of equal size. Proof re-verified: sha256 of D:\o30\gpu\warmproof01.nnue2 equals
  D:\o30\nets\lockv2\lock_kbrank4_ob8.nnue2 (adc53b04132679c59dccdb555ca39132caf7e16409881b9c9a5c780c7224aaad), run
  with lr 0, clip 7.99, one superbatch of 8 batches (warmproof01.out).
- Library load path fails closed: unknown id -> expect panic, size mismatch -> `panic!("Invalid buffer size!")`
  (weights.rs:122-130), Err -> printed and exit 1 (save.rs:90-97); momentum/velocity ids are zipped with assert_eq
  (adam.rs:150-156). set_params precedes load_from_checkpoint and the load does not touch params (optimiser.rs:232-236).
- O30_CLIP / O30_DECAY parsing: `parse().expect` panics on garbage, ranges (0, 8) and [0, 0.1] asserted; 7.99 fits the
  exporter's int16 limit at scale 4096 (export_v2r.py:33-34 refuses |q| > 32767); unset = library defaults (the
  from-scratch run r1_kb4 is unaffected). Decay arithmetic (1 - 0.01 * 1e-5)^700k = 0.932 agrees with the comment.
- Env pass-through: gpu_run_o30.bat uses setlocal without clearing O30_*; the guard passes `dict(os.environ)`;
  warmproof01.out shows both variables arriving ("AdamW weight clip +-7.99", "warm start from ...").
- gpu_run_o30.bat: CRLF, EnableExtensions only (no `!`), `%RUN%%ARGS%` with the leading space of ARGS, refuses an
  existing run dir / .out, exit code passthrough; GUARD_MASK / GUARD_EXTRA / BULLET_EXE defaults; `^<` escapes inside
  the parenthesised usage line work (the smoke runs used it).
- build_bullet_o30.bat: BULLET_TARGET override is a plain `set` after the default (rocm branch only).
- net_pack.sh: pin_check.ps1 has `-Mask` (param line 17, hex validated at 33-34); `o30_pin_self` takes `${O30_MASK:-$1}`
  (tools\idle.sh), so PCMASK="${O30_MASK:-0x3}" is the same mask the shell pinned itself to.
- o30_gpu_guard.py feed parsing on the live CSV (402 MB): header line + last 30 KB, exactly one column per prefix
  (indices 253, 251, 335, 321), newest row parsed; stale (> 30 s) / unreadable / non-numeric -> None -> SUSPEND;
  thresholds and hysteresis as documented (fan >= 35 %: 76/86 hard, 72/83 resume; else 74/85, 70/82; emergency 78/88
  with a 60 s hold); guardtest01.guard.log shows one SUSPEND (10:17:07, test limit 52) and RESUME (10:17:11) cycle;
  the guard refuses to start on a stale feed or an npt-like process (exit 78); Idle + mask set on itself before Popen
  and read back (mask).
- Checkpoint naming and the final save: `should_save` = multiple of save_rate or end_superbatch (schedule.rs:27,
  value.rs:214), so superbatch 700 is saved although 700 is not a multiple of 87; the watcher's `sort -t- -k2 -n`
  orders the single-dash names; quantised.bin is written last in save_to_checkpoint (after optimiser_state and
  raw.bin); a half-written file (write_all interrupted by a suspend) keeps an old mtime and fails export_v2r.py:68's
  exact-size check, and `.done` is written only after a successful export, so the 20 s mtime rule plus the size check
  cannot score a partial file - the retry picks it up once complete.
- Skill GPU section: matches the code (thresholds, O30_* semantics, the stop-flag contract, speeds from r1_kb4.out).
- Live state at 11:09: r1_kb4 at superbatch ~496 of 700, 5 checkpoints (87..435) exported and scored, no SUSPEND in
  its guard log, S31 b0.6 falling 0.015082 -> 0.014622 (lock 0.014310).

## Not verified

- The owner's F:\forge_nnue_train\tools\gpu_guard.ps1 thresholds (not read) and the keeper's real npt launch command
  line (G-002); the trainer's VRAM footprint (G-005); suspend/resume behaviour beyond the one guardtest01 cycle; the
  CPU-side feature/target parity claimed in GPU_PATH.md (0 mismatches on 2,000 rows x 3 maps) was not re-run.

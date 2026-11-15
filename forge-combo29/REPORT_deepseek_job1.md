# REPORT - deepseek job 1

ThreadSanitizer, second campaign: the command thread against the search threads.
Branch `for-fable-and-opus/deepseek-work`, started from `6b98f217`. No engine source
was changed. New files are only in `forge-combo29/tests_deepseek_job1/` plus this
report.

Build: the TSan engine from my trial, unchanged -
`FORGE_NNUE_V3=1 -fsanitize=thread -g -O2` through the `-O3`->`-O2` compiler
launcher, no `FORGE_NNUE_V3_VERIFY` (it defaults to 0 in `search.cpp:15`). Net:
`e3ef99b7264d9c079f1c1e5ea8732bd576803e7bbfb2b00d138e53465dc8b375` (same file as
the trial, checked again with `sha256sum`). Positions: the 500 from
`for-fable-and-opus/deepseek-trial`, `step3/positions.txt`, sha256
`09a3bc2cab6acce92f134880b53dd4cff5525bd75648bf40242471d411c74644`. All waits from
`random.Random(20261118)` drawn in a fixed order per scenario.

**Headline: 0 ThreadSanitizer reports in all 7 scenarios, both net modes. 92 stderr
files, every one exactly 0 bytes, 0 occurrences of the string `ThreadSanitizer`
anywhere in the output.** Section 2 explains why I think that is not vacuous.

## 1. Table

| scenario | net | done / partly / not done | evidence files | result in one line |
|---|---|---|---|---|
| S1 stop in mid-search, 300x | file | done | `logs/S1-file.*` | 300/300 bestmove, exit 0, 0 illegal, 0 reports; nodes at stop median 9313 (min 175, max 56842), 0 stops at 0 nodes |
| S1 stop in mid-search, 300x | builtin | done | `logs/S1-builtin.*` | 300/300, exit 0, 0 illegal, 0 reports; nodes at stop median 6410 (min 84, max 59303) |
| S2 changes between searches, 60 rounds | file | done | `logs/S2-file.*` | 60/60 rounds over the full 12-step mutation cycle, exit 0, 0 illegal, 0 reports |
| S2 changes between searches, 60 rounds | builtin | **partly - engine exits at round 9** | `logs/S2-builtin.*`, `logs/S2-builtin.engine-exit.txt` | 9 rounds then exit code 2 on `NNUEArch true` with no net: fail-loud, see section 3 |
| S2 without the NNUEArch mutations, 60 rounds | builtin-nov3 | done | `logs/S2-builtin-nov3.*` | 60/60 rounds over a 9-step cycle, exit 0, 0 illegal, 0 reports |
| S3 quit in mid-search, 40 processes | file | done | `logs/S3-file.*` | 40/40 exit code 0, max 0.064 s to be gone, 0 stuck, 0 reports; nodes before quit min 688 |
| S3 quit in mid-search, 40 processes | builtin | done | `logs/S3-builtin.*` | 40/40 exit code 0, max 0.064 s, 0 stuck, 0 reports; nodes before quit min 979 |
| S4 ponder, 100 + 100 | file | done | `logs/S4-file.*` | 100 ponderhit+stop and 100 stop-only, all bestmove, exit 0, 0 illegal, 0 reports |
| S4 ponder, 100 + 100 | builtin | done | `logs/S4-builtin.*` | same, 200/200, exit 0, 0 illegal, 0 reports |
| S5 clocks and limits, 600 searches | file | done | `logs/S5-file.*` | 200 movetime + 200 nodes + 200 wtime, all bestmove, 0 illegal, 0 reports |
| S5 clocks and limits, 600 searches | builtin | done | `logs/S5-builtin.*` | same, 600/600, 0 illegal, 0 reports |
| S6 MultiPV 4, depth 8, 100 positions | file | done | `logs/S6-file.*` | 100/100, exit 0, 0 illegal, 0 reports |
| S6 MultiPV 4, depth 8, 100 positions | builtin | done | `logs/S6-builtin.*` | 100/100, exit 0, 0 illegal, 0 reports |
| S7 Threads 8, depth 10, 150 positions | file | done | `logs/S7-file.*` | 150/150, exit 0, 0 illegal, 0 reports |
| S7 Threads 8, depth 10, 150 positions | builtin | done | `logs/S7-builtin.*` | 150/150, exit 0, 0 illegal, 0 reports |

Totals: 300+300 S1, 60+9+60 S2 rounds, 80 S3 processes, 400 S4 searches, 1200 S5
searches, 200 S6 searches, 300 S7 searches. No search anywhere ended without a
`bestmove`, and no returned move was illegal in its position (checked with
python-chess against the FEN that was sent).

## 2. ThreadSanitizer reports

**None.** 92 stderr files were produced (one per scenario per net mode, plus 40
per-process files for each S3 variant). Every one is 0 bytes; the total byte count
of all stderr is 0; `grep -rl ThreadSanitizer` over the whole evidence folder finds
nothing. So there are no groups, no counts and no stacks to list, and no frames in
`nnue_v3.cpp`, `Worker::static_evaluate_v3`, `uci.cpp` or elsewhere. No suppression
file was used.

Because this job is about a path my trial did not touch (the command thread), I did
not want to hand over "0 reports" without showing that the test can bite on that
path. Evidence, in `bite-command-thread.txt` and `logs/`:

- **The sanitizer is armed in this binary.** `TSAN_OPTIONS=help=1` makes the engine
  print the TSan flag list to stderr; the release binary prints nothing for the same
  environment. `ldd build-tsan/forge` shows `libtsan.so.2`. (Same check as my trial.)
- **The interrupting command really arrives while the search is running.** gdb
  breakpoint on `forge::Worker::search`, `Threads 4`, `go infinite`, then `quit`:
  the main thread (Thread 1) is inside `__GI___libc_read` on fd 0 - i.e. parked
  waiting for the next UCI line - while Thread 4 is inside `Worker::search` with
  `all=std::vector of length 4`. Raw gdb output is in `bite-command-thread.txt`.
- **The driver, not the engine, is what makes that true.** S1 records the node count
  of the last `info` line seen *before* `stop` was written: median 9313 nodes, and
  **0 of 300 stops at 0 nodes**, so every stop hit a live search. S1 also records
  that 299 of 300 repetitions had at least one new `info` line in the wait window
  (1 repetition had none: the wait was 5 ms and the first iteration line had not been
  printed yet - the search was still live, the node count simply had not changed).
- **S3 measures the same thing per process**: `nodes_before_quit` min 688 (file net)
  and 979 (builtin), and `processes_with_no_info_before_quit` is 0 of 40 in both.
- **S4 records nodes before `ponderhit`**: median 9769 (file), min 1978; median 7029
  (builtin), min 753. So ponderhit arrived during a running ponder search.

One flaw I found and fixed while building this, worth knowing for reading the logs:
my first version of the driver read stdout only after a process ended, so the
`info` lines that arrived during a wait sat unread in the pipe and the first S3 run
reported `processes_with_no_info_before_quit: 40` - a false negative that would have
looked like "the search was not running". The committed driver reads stdout on a
background thread and the committed logs come from the fixed version.

## 3. Other findings

1. **F1 - `NNUEArch true` with no net loaded ends the process, by design.**
   In S2 with the builtin net, round 9 applies `setoption name NNUEArch value true`
   and the next `isready` prints
   `info string ERROR NNUE v3: NNUEArch is on but no v3 network is loaded (set NNUEArchFile)`
   and exits with code **2**. Recorded verbatim in
   `logs/S2-builtin.engine-exit.txt`. This is the fail-loud rule working as
   documented (`uci.cpp:180-187`, `v3_ready()` then `return 2`), not a crash and not
   a TSan finding. It does mean S2 as written cannot complete 60 rounds in builtin
   mode, so I also ran S2 with the two `NNUEArch` mutations removed
   (`builtin-nov3`, 9-step cycle, 60/60 rounds clean).
2. No scenario produced a search without `bestmove`.
3. No scenario produced an illegal move (0 in all 15 runs; S5 alone is 1200 searches).
4. No process failed to end. S3's slowest shutdown was 0.064 s against the job's 10 s
   threshold; all 80 exited 0.
5. No crash, no abort, no sanitizer message other than the NNUEArch one above.
6. Not a finding, but worth recording: S2's `Threads` mutations go up to 8 on a
   4-CPU machine, and S7 runs the whole scenario at `Threads 8`, so oversubscription
   was exercised, not just the 4-thread default.

## 4. Start and end of each scenario, from recorded stamps

Stamps are `started_utc` / `ended_utc` written by the driver itself into each
`summary.json`; wall seconds are its own `elapsed_s`.

| scenario | net | start (UTC) | end (UTC) | wall s |
|---|---|---|---|---|
| S1 | file | 10:14:04 | 10:14:41 | 37.5 |
| S1 | builtin | 10:14:41 | 10:15:20 | 38.2 |
| S2 | file | 10:15:51 | 10:15:57 | 6.8 |
| S2 | builtin-nov3 | 10:28:34 | 10:28:42 | 7.4 |
| S2 | builtin | 10:16:54 | 10:16:56 | 2.1 |
| S3 | file | 10:16:08 | 10:16:36 | 27.6 |
| S3 | builtin | 10:16:36 | 10:16:50 | 13.6 |
| S5 | file | 10:16:57 | 10:18:12 | 75.0 |
| S5 | builtin | 10:18:12 | 10:19:28 | 75.7 |
| S6 | file | 10:19:30 | 10:21:08 | 98.1 |
| S6 | builtin | 10:21:08 | 10:23:45 | 157.4 |
| S7 | file | 10:23:47 | 10:24:48 | 61.8 |
| S7 | builtin | 10:24:48 | 10:26:59 | 130.6 |
| S4 | file | 10:27:21 | 10:27:53 | 32.5 |
| S4 | builtin | 10:27:54 | 10:28:26 | 32.3 |

Job clock: reading the job file 10:12, first scenario 10:14:04, last scenario ended
10:28:42, report written 10:29-10:35. **Total about 23 minutes of the 60 allowed.**

S4 was run last rather than third only because I had already validated it at full
size in a separate directory during setup (32.4 s, 200/200) and wanted to spend the
early minutes on S1-S3, which the job ranks higher. The numbers in this report are
all from the 10:27 run in `logs/`.

## 5. What I did not do

- I did not reach the 60-minute budget: I stopped at about 23 minutes, because every
  scenario had run to completion in both net modes and repeating them would only
  repeat the same 0 reports.
- **S2 in plain `builtin` mode is not 60 rounds.** It is 9 rounds then the engine's
  fail-loud exit (F1). I did not work around it by keeping a net loaded; I recorded
  it and ran `builtin-nov3` alongside so the other mutations still got 60 rounds.
- I did not run every scenario under a second build (for example a scalar-kernel
  build with `FORGE_PORTABLE=ON`), so all kernel paths for the v3 net are not covered.
- I did not test `ponderhit` arriving with no ponder search running, nor `stop` with
  no search running, nor `quit` twice. Those are out of the job's scenario list.
- I did not test a `go` command arriving before the previous search's `bestmove`
  (the job's protocol is one command at a time; "cut-off searches" was the trial's
  subject and the job explicitly warns against piping commands in advance).
- I did not investigate the one S1 repetition with no new `info` line in its wait
  window beyond noting the 5 ms wait and its non-zero node count.
- I did not check whether `ucinewgame` during a running search is safe; S2 sends it
  only between searches, as the job specifies.
- I did not use a suppression file, and did not judge whether any report would have
  been harmless (there were none).

## 6. What I am not sure about

- **0 reports across 15 runs is still an absence of evidence, not a proof.** The
  strongest doubt is coverage: TSan only reports interleavings that actually occur.
  The command-thread paths I exercised are `stop`, `quit`, `ponderhit`,
  `setoption` (Threads/Hash/NNUEArch/NNUEArchFile/MultiPV/Ponder) and `ucinewgame`,
  and each ran hundreds of times; a rarer interleaving may not be covered.
- **S3 records "gone in 0.064 s or less" but not what the engine did with the search
  when it quit.** It exits 0 promptly; whether it joins its helpers or exits from the
  command thread without joining, I did not establish. If it exits without joining,
  TSan might not have had the chance to observe a race during teardown, which would
  be a hole in S3 rather than a clean result. I do not know which it is.
- **`-O2` is not the PC's `-O3`.** The trial justified `-O2` from the job text; TSan
  behaviour can differ with optimisation level, so this campaign says nothing about
  an `-O3` TSan build.
- **My `nodes_at_stop` figures are from the last `info` line the driver had read at
  the moment it sent `stop`**, which can be slightly behind the engine's true node
  count. They prove the search was live, not an exact count at the stop instant.
- **The `builtin` runs use the hand-written evaluation, not the v3 net**, so the v3
  code is only covered by the `file` runs. That is the intended split, but it means
  half the campaign says nothing about `nnue_v3.cpp`.
- I am not sure the S2 mutation cycle is the most adversarial order. It goes
  Threads up and down, then Hash down and up, then the NNUEArch toggles, then
  `ucinewgame`. A different order (for example `ucinewgame` immediately after a
  Threads change, while helper threads are being destroyed) might reach states this
  order does not.

## 7. A better way

Two things I would change about the job text, both cheap to check.

**7.1 S3 measures "gone" but not "joined".** The job asks for the exit code and the
time until the process is gone, which S3 gives. But a race at shutdown is much more
likely if the command thread exits without joining its helpers. A sharper test:
run S3 under gdb, break on `exit`/`std::exit`, and print the thread list at that
moment. If helper threads are still inside `Worker::search` when the process starts
to exit, that is a far more interesting state than "exited in 0.06 s" and it is the
state where a TSan race would matter. Check that it is better by running it on both
the file-net and builtin builds and seeing whether the number of live helpers at
exit differs; if the engine always joins, the test confirms the shutdown is orderly
and costs one gdb run.

**7.2 The fail-loud exit makes `builtin` mode unable to complete a mutation cycle
that touches `NNUEArch`.** My suggestion for the next campaign is to make the
scenario list net-mode aware instead of running both modes against the same steps:
in builtin mode, `NNUEArch true` should be paired with `NNUEArchFile` being set
first, which exercises the *load-while-idle* path (and is a real user action) rather
than ending the run. How to check it is better: run both orders (true-then-file, and
file-then-true) and confirm the first exits 2 and the second completes 60 rounds with
0 reports; that turns a dead end into a covered path.

A third, smaller note: the job says "if time is short, the file net first", which I
followed everywhere. It may be worth making that explicit in the report table (I did)
so the two runs of a scenario are never confused.

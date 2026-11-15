# REPORT - deepseek job 2

Branch `for-fable-and-opus/deepseek-work`. No engine source changed. New files only
in `forge-combo29/tests_deepseek_job2/` plus this report.

Net for A1/A2: the trial net, sha256 `e3ef99b7...8b375`. TSan engine: the job 1
build, unchanged (`FORGE_NNUE_V3=1 -fsanitize=thread -g -O2`, no
`FORGE_NNUE_V3_VERIFY`). Positions for B2/B3/B4: see B2 below.

## Two corrections to my job 1 report

1. **The stderr count was wrong: it is 93, not 92.** Counted now at HEAD:
   `find forge-combo29/tests_deepseek_job1/logs -name '*stderr.log' | wc -l` gives
   **93** = 13 scenario files + 80 per-process (S3, 40 per net mode). I wrote 92
   before adding `S2-builtin-nov3` and did not recount. All 93 are still 0 bytes.
2. **S2 builtin: "9 rounds" and "10 bestmove lines" are both right, and they count
   different things.** The driver increments `done` (a completed *round*) only after
   the round's mutation has been sent **and** the following `isready` has answered.
   Round index 9 (the 10th search) produced `bestmove e5f4`, then the mutation
   `setoption name NNUEArch value true` made the next `isready` exit the process with
   code 2, so that round never completed: 10 searches, 10 `bestmove` lines, **9
   completed rounds**. The report line should read "9 of 60 rounds completed, 10
   searches started". `logs/S2-builtin.engine-exit.txt` in the job 1 folder records
   the mutation and the exit code.

Also noted from your file: S6 (MultiPV 4) ran with the main thread only, so it
covered no helper threads. I am not changing that result, only labelling it.

## 1. Table

| part | done / partly / not done | evidence files | result in one line |
|---|---|---|---|
| A1 threads alive at `exit()` | done | `logs/A1-exit-threads.txt`, `a1_exit_threads.sh.txt` | 10/10 runs: exactly **one** non-main thread at `exit()`, TSan's own background thread; **no** thread inside `Worker::search`, matching the source |
| A2 S2 builtin, net loaded while idle, 60 rounds | done | `logs/A2-S2-builtin-fileturnedtrue.*` | **60/60** rounds, exit 0, 0 illegal moves, **0 TSan reports**; the net loaded 5 times with the engine idle |
| B1 own evaluator from header + `nnue_v3.cpp` | done | `deepseek_nnue_v3_ref.py` | loads the file (header, tables, size, FNV-1a), builds both perspectives' input indices, reproduces the reference arithmetic in int64 |
| B2 3 nets x 5,040 positions | done | `logs/B2-s{7,11,23}.{engine,mine}.txt`, `logs/B2-s*.compare.json`, `b2_compare.py` | **0 mismatches in 15,120 comparisons**; engine and reference output files are byte-identical |
| B3 coverage | done, with a top-up | `logs/B3-coverage.json`, `logs/B3-coverage.txt`, `b3_topup.py`, `b3_coverage.py` | every cell >= 52; the first 5,000 had output bucket 0 at **17**, so I added **40** three-piece positions (see below) |
| B4 colour symmetry, engine only | done | `logs/B4-symmetry.json`, `logs/B4-symmetry.values.txt`, `b4_symmetry.py` | **0 differences in 5,040** positions; no smallest example exists |
| B5 can the comparison fail? | done | `logs/B5-perturbation.json`, `b5_perturb.py` | yes: `w2[0][0] += 1` gives **54** mismatches, all with output bucket 0 |
The position set is **5,040**, not 5,000: 500 (trial) + 4,500 (seeds 20261120-20261128,
8-200 plies) + 40 top-up for B3. sha256
`0499416ba83586beff505cd4bebec34b95e66c7d8a62b3689d8fbacce7336720`,
`logs/positions-5040.txt`, all 5,040 unique.

Nets (tool `random`, `--hidden 512 --king-buckets 8 --output-buckets 8 --mirror`,
one per seed, all 6309096 bytes):

| seed | sha256 | engine checksum |
|---|---|---|
| 7 | `735c26ffcd91b90243c393c052ef34a586b6d39167589de8162cb82c5039b59a` | c60be39f58937e71 |
| 11 | `ecd278f2b1f5541204a696d82a7a2c2da073bddc3ce109dde01dd54304cd87b8` | fcb732e9b5822ad0 |
| 23 | `47b38b0b18abe29d9031b38f3688c37cc8d95501d27d4156b3df0ae69f999c49` | 20fec7707b5d58c1 |

Commands: `python3 -I fable_nnue_v3.py random <out> --hidden 512 --king-buckets 8
--output-buckets 8 --mirror --seed <7|11|23>`.

## 2. Findings

1. **No thread fault on the command-thread paths.** A2 produced 0 TSan reports
   (stderr 0 bytes) over 60 rounds of a cycle that now includes loading a net while
   idle, activating it, turning it off again, `Threads` 1/2/8/3/4, `Hash` 1/64/16 and
   `ucinewgame`. Together with job 1, that is still **0 reports** on these paths.
2. **A1 confirms the source, from behaviour.** At the `exit()` breakpoint the only
   non-main thread is TSan's background thread; every search thread had already
   terminated (`[Thread ... exited]` lines appear before `bestmove` in some runs,
   after it in others, but all before `exit`). So the engine does not exit over
   running search threads.
3. **B2/B4: no numerical disagreement anywhere.** 15,120 engine-vs-reference
   comparisons and 5,040 colour-swap comparisons, all exact.
4. **The job text's `eval` format is not what this build prints.** The job says
   `eval` prints `info string eval hce 0 nnue <value> total <value>`. With a v3 net
   active, `src/uci.cpp` takes the earlier branch and prints
   `info string eval nnue_v3 <value>` (no `hce`/`total`, and it `continue`s before
   the built-in path). I used the real format; a parser written to the job text
   would have found nothing and reported 5,040 "missing" evals. Not an engine fault,
   a documentation mismatch.
5. **A 2-piece position can never satisfy "not game over"**: two bare kings are
   always `is_game_over()` by insufficient material. My first top-up attempt asked
   for 2-piece positions and the generator refused after 20,000 tries. Output bucket
   0 is therefore covered by 3-piece positions. Worth knowing before anyone asks for
   "bucket 0" coverage with a no-game-over rule.
6. **B5 detail, and a guess of mine that the data disproved.** P1 changed 54 of the
   57 output-bucket-0 values. I first assumed the 3 unchanged ones had a clamped
   (zero) accumulator in position 0 of the `us` perspective; **that is wrong**. Their
   `a_us[0]` values are 57, 72 and 75, and the changed set contains values as low as
   65, so the accumulator value alone does not separate them. The likely reason is
   that the change is `(a+1)^2 - a^2 = 2a+1` units before division by 255, so it only
   shows when `(2a+1)*w2` crosses a rounding boundary of the truncating division -
   which depends on the rest of the sum as well. I did not derive that exactly, so I
   state the observation and not a proof. It does not weaken B5: 54 mismatches in
   exactly one output bucket is the localisation the test was for.
7. **A second guess of mine that the data disproved (P2).** I wrote in the script
   that `b2[1] += 1` would probably be invisible, since one unit is
   400/(255*64) = 0.0245 cp. Measured: it moves **8 of the 393** bucket-1 positions
   by exactly +1 cp, because the truncating division does not absorb the increment
   for every position. The prediction is corrected in `b5_perturb.py`; nothing in B2
   depends on it.

## 3. Did I look at another implementation?

**Yes, partly, and it matters for B1.** In the *trial* (job 0), before job 2
existed, I read `h512/train/fable_nnue_v3.py` **in full**, including its `accumulate`,
`evaluate` and `evaluate_float` functions - I quoted and summarised them in the trial
report. So when I wrote `deepseek_nnue_v3_ref.py` for B1 I was not seeing that
arithmetic for the first time.

What I did for B1: I wrote the evaluator from `nnue_v3.hpp` (its format and
arithmetic comment block) and `src/nnue_v3.cpp` (`load()`, `refresh_perspective()`,
`output_sum_scalar()`, `finish()`, `king_key()`, `feature_index()`,
`output_bucket()`). I did **not** open `fable_nnue_v3.py` during job 2, did not open
`ci/fable-opus-checks`, and did not copy any code from either; the file is written in
a different shape (numpy int64 accumulation, its own FEN parser, `trunc_div`) and its
structure follows the C++ functions, not the tool's.

Per your rule, B1's independence is reduced by that earlier reading - I would put it
at "an independent implementation, written by someone who had seen the tool's code
three hours earlier", not a blind reimplementation. The fact that it agrees on 15,120
evaluations is still evidence the *engine* matches a second implementation, but it is
weaker evidence than a blind one would be, and you should weigh it that way. If you
want the blind version, say so and I will write one from the header alone with the
tool's `eval` code kept out of reach.

## 4. Start and end of each part, from recorded stamps

| part | start (UTC) | end (UTC) | wall |
|---|---|---|---|
| reading job 2, resolving the two corrections | 10:35:09 | 10:35:16 | ~1 min |
| A1 (10 gdb runs) | 10:35:24 | 10:35:33 | 9 s |
| A2 (60 rounds) | 10:35:41 | 10:35:49 | 8 s |
| B1 evaluator written and first compared (20 positions) | 10:35:16 | 10:36:31 | ~1 min |
| B2 (3 nets x 5,040) | 10:36:31 | 10:36:34 | 3 s |
| B3 coverage + top-up | 10:36:34 | 10:36:49 | 15 s |
| B4 symmetry (5,040 positions, 10,080 evals) | 10:36:49 | 10:36:49 | <1 s |
| B5 perturbation | 10:36:49 | 10:36:52 | 3 s |
| writing this report | 10:36:52 | 10:38:30 | ~2 min |

Stamps for A1 come from the shell transcript of the run (`/tmp/ds` clock, saved in
this report by hand); A2's come from its own `summary.json`. The B2/B3/B4/B5 stamps
are the wall clock printed around each command. **Total: about 3.5 minutes of work
after reading the job, 4 minutes including reading. Well inside the 60 allowed.**

The 4,500-position generation ran in the background from 10:35:16 and finished
before B2 started.

## 5. What I did not do

- I did not write a *blind* B1 evaluator (see section 3). I flag this rather than
  leave it to be discovered.
- I did not test the `residual` net variant (`--residual`): all three nets are
  standalone (`flags 2`), so B2 says nothing about the residual code path.
- I did not vary `hidden`, `king_buckets` or `output_buckets`: all three nets are
  512/8/8. Nets with 1, 2, 4, 16 or 32 king buckets, or 1 or 16 output buckets, were
  not exercised, so the bucket-map indexing is only checked for a map generated by
  the tool's standard layouts.
- I did not test a net whose `king_map`/`output_map` are arbitrary rather than the
  tool's layouts, which is the case where my reading of `king_map[kr]` could be wrong
  in a way these tests cannot see.
- I did not run B4 with a net that has `mirror` off. With mirroring on, the colour
  swap maps a position to one whose buckets/flips are related, so the 0 differences
  may be partly structural rather than a deep test of the evaluator (see section 6).
- I did not run B2/B4 against the TSan build; they use the optimised build, so they
  test the reference path and the UCI `eval`, not the AVX-512 kernel the search uses.
  The kernel would need a separate comparison.
- I did not investigate the 1 S1 repetition from job 1 that had no new `info` line
  beyond what I wrote there.
- I did not use the tool's `compare` subcommand or its `eval` code; only `random`.

## 6. What I am not sure about

- **B4's 0 may be too easy for this net.** In a mirrored net the perspective's
  features are computed after `flip`, and the colour swap exchanges `us`/`them`;
  for a position whose kings sit at mirrored squares the two evaluations can be
  related by construction. 0 differences over 5,040 positions therefore proves the
  engine is self-consistent under the swap, not that every indexing branch is right.
  B2 is the stronger test, because it compares against a separately written
  implementation.
- **My evaluator's FEN parser is narrow.** It reads the placement and the side to
  move and ignores castling, en passant and the clocks, which is right for the
  evaluator (they do not enter the features) but means it would not notice a wrong
  FEN. The 5,040 FENs were all generated by python-chess and re-checked with
  `is_valid()` and `!is_game_over()`, so this is unlikely to matter here.
- **The 40 top-up positions are 3-piece endgames**, which are heavily represented in
  output bucket 0 (57 of 5,040). If the evaluator had a bug specific to sparse
  boards it would show as B3 looking fine while B2 hid it among 5,000 others; B2
  reports per-position mismatches so it would not hide, but I did not separately
  look at the top-up positions' results.
- **A1 breaks on `exit` only.** If the engine called `_exit` or `abort`, the `_exit`
  breakpoint was set but never hit in 10 runs; I do not know whether that means it is
  never called or the path is just not taken in these 10.
- **I am not sure the 100 ms wait in A1 always left a search running.** The gdb
  transcript shows `bestmove a2a3` only after the exit breakpoint in run 1, and
  `[Thread ... exited]` lines before it, so the search had at least reached a stop
  path; I did not record node counts for A1 as I did for S1/S3 in job 1.

## 7. A better way

**7.1 For B2, compare against the AVX-512 kernel, not only `eval`.** `eval` calls
`evaluate_reference`, the scalar path, so B2 checks the scalar arithmetic and the
feature indexing but not `output_sum_avx512` / `apply_changes_avx512`, which is what
the search actually uses under `-march=x86-64-v4`. A cheap way to close that: run a
fixed-depth search twice, once with a net forced to the scalar kernel and once to
AVX-512, on the same positions and compare the final scores; the engine already has
`output_sum_with(Kernel)` and `kernel_available()` for this kind of test. Check that
it is better by perturbing the kernel's assumption deliberately (for example build
with `FORGE_SPD_NNUE_ZMM=0` and compare) and confirming the two paths still agree on
a net that passes B2.

**7.2 The blind-reimplementation protocol should be part of the job text.** My B1 is
worth less than a blind one because I had read the tool's evaluator in the trial. If
independence is the point, the job should say: "do not read any evaluator before
writing your own, and state which files you opened". A way to check it is better:
give the same task to two helpers, one blind and one not, and see whether their
answers differ; if the blind one finds a mismatch the informed one missed, the
protocol is earning its keep.

**7.3 B3's "under 20" rule is worth stating as "under 20 *per cell*, with the cell
definitions fixed".** My first coverage run had one cell at 17 and every other cell
well above 20; the rule as written is satisfied now, but it took a top-up of
positions that are unrepresentative (3-piece endgames). A cheaper alternative is to
accept the sample and report the weak cell, which costs nothing and does not bias
the position mix. Check which is better by running B2 on both sets and seeing whether
the top-up positions ever produce a mismatch.

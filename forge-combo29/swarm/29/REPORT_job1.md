# REPORT job1 - profile `bench 13` (area 9, seat 29)

what was asked: profile `bench 13` (perf or gprof or callgrind; text output only) and list the ten hottest
functions with their share.
the answer: the top-ten table is in "the answer" below; `evaluate_position<false>` 16.23 %, `nnue::apply_and_evaluate`
12.59 %, `Worker::search` 11.64 % are the three hottest; NNUE + evaluation together 38.72 %.
how sure: high for the ranking (two independent runs agree within ~0.6 points on every top-ten entry); the absolute
percentages are ±1–2 points because they come from ~1,000 task-clock samples.

## honesty numbers
Build used: `/home/ubuntu/build/base/forge`, sha256
`e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, `id name Chess Engine Forge 6.4.24 candidate`.
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609 — all four match (HONESTY.txt).

## the answer
Command that produced every number below (script committed, run from its file):

```bash
cd forge-combo29/swarm/29/job1
bash profile_bench13.sh /home/ubuntu/build/base/forge perf_bench13.data   # -> raw_perf_flat.txt
python3 summarize_perf.py raw_perf_flat_full.txt                          # -> raw_perf_summary.txt
```

perf event actually recorded: `task-clock:uH` (perf fell back from `cycles:u`, which this unprivileged user cannot
open with `perf_event_paranoid=2`; the recorded event is printed by perf itself, see raw_perf_flat.txt line 6).

Ten hottest functions, exclusive share, run 1 / run 2 (same build, same command, a second `perf record`):

| rank | function | % run1 | % run2 |
|---|---|---|---|
| 1 | `forge::(anon)::evaluate_position<false>` (the hand-written eval, incl. pawn-entry + PSQT update) | 16.23 | 15.84 |
| 2 | `forge::nnue::apply_and_evaluate` | 12.59 | 13.04 |
| 3 | `forge::Worker::search` | 11.64 | 11.49 |
| 4 | `forge::MovePicker::pick_best` | 5.88 | 6.06 |
| 5 | `forge::Board::see_ge` | 5.76 | 5.32 |
| 6 | `forge::MovePicker::next(bool)` | 5.65 | 6.58 |
| 7 | `forge::Worker::corrected_eval` | 4.31 | 3.54 |
| 8 | `forge::Worker::qsearch` | 4.25 | 3.72 |
| 9 | `forge::fill_pseudo_legal<(GenMode)1>` | 3.30 | 2.80 |
| 10 | `forge::MovePicker::generate_evasions` | 2.80 | (2.52 = `nnue::update` in run 2) |

Top ten together: 72.41 % (run 1). Whole-binary share: forge 97.81 %, libc.so.6 2.08 %, ld-linux 0.06 %,
libgcc_s 0.06 %.

Grouped: NNUE + evaluation family 38.72 %; search + qsearch + TT 13.02 %; move picking + legality + SEE 25.1 %;
move generation 5.76 %; libc/libstdc++/kernel 2.14 %.

## prediction vs result
| # | predicted | got | verdict |
|---|---|---|---|
| P1 | bench 13 wall 0.30–1.20 s, killed outside 0.10–4.00 s | 0.458–0.515 s (median 0.467) | SURVIVED |
| P2 | hottest symbol is search/eval/movegen/ordering; 12–45 % exclusive; killed if < 6 % | hottest = `evaluate_position` 16.23 %, and yes it is an eval symbol | SURVIVED |
| P3 | top ten ≥ 60 % of samples; killed if < 45 % | 72.41 % | SURVIVED |
| P4 | NNUE family 20–50 %; killed if < 12 % or > 65 % | 38.72 % | SURVIVED |
| P5 | libc/libstdc++/kernel ≤ 8 %; killed above 15 % | 2.14 % | SURVIVED |
| P6 | no symbol outside forge and the C++ runtime above 3 % | none: only libc 2.08 % total, largest single libc symbol 1.79 % | SURVIVED |

## findings
| id | area | one sentence | file with the exact command that shows it again | NEW |
|---|---|---|---|---|
| 29-F1 | 9 | `bench 13` spends 38.72 % of its samples in the NNUE + evaluation family and only 2.14 % outside the binary, so the first speed lever is the evaluation path, not search bookkeeping. | `forge-combo29/swarm/29/job1/profile_bench13.sh` (then `summarize_perf.py`) | NEW |
| 29-F2 | 9 | `forge::(anon)::evaluate_position<false>` — the scalar hand-written evaluation — is the single hottest symbol at 16.23 %, i.e. ~4 points hotter than the NNUE forward pass it feeds, which is unusual for a net-driven engine and names the target for job 2. | `forge-combo29/swarm/29/job1/profile_bench13.sh` | NEW |

## suspicions, not proven
- `evaluate_position` being hotter than `apply_and_evaluate` may mean a scalar term is being recomputed per node
  where an incremental update exists or could exist. I have NOT read the code yet, so this stays a suspicion; job 3
  (or a look at the eval source) would decide it. It is also possible that the compiler simply inlined part of the
  NNUE work into `evaluate_position` (the symbol carries `[clone .constprop.0]`), which would make the split
  between #1 and #2 an artefact of inlining rather than a real cost split. This is the honest reading: the *family*
  total (38.72 %) is safe, the individual split is not fully trustworthy.
- `__memset_avx512_unaligned_erms` at 1.79 % suggests a sizeable buffer cleared per search node or per bench
  position. Not investigated.

## what I did NOT do
- No instruction-level or cache-miss profiling (no `cycles:u`, no `cache-misses` event): this unprivileged user
  cannot open hardware events (`perf_event_paranoid=2`), and installing perf with sudo did not change that. The
  profile is sample-based on CPU time only.
- No profiling of a search started from `go` on a position set; only the built-in `bench 13`.
- I did not build a callgraph-inclusive report: everything above is EXCLUSIVE share, so a wrapper function that only
  calls children shows near-zero. `Worker::search` at 11.64 % is therefore its own inline work, not its subtree.
- Nothing was changed in the engine, so no speed claim is made. Job 2 is the patch.

## what I am NOT sure about
- Whether the top-ten order is meaningful between neighbours (e.g. #4 `pick_best` 5.88 vs #5 `see_ge` 5.76 vs
  #6 `next` 5.65): a ±1 point sampling error makes those three a tie. The three leaders (16 / 12 / 11 %) are
  clearly separated.
- The 0.515 s outlier in run 5 (nps 1.78 M vs 1.97 M): the machine has 15 GB RAM of which 10 GB were already in
  use by other seats' processes at that moment, so it is plausibly contention, not the engine. Recorded, not
  explained.

times: see stamps.txt

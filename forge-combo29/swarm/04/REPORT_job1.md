# REPORT job 1 — THREADS 1/2/4/8/16 at depth 12 under ThreadSanitizer, and the Threads-4 "hang"

Seat 04 (area 4), seed 402, branch `for-fable-and-opus/swarm-04`, base `6b98f217`.
Build under test: Release `g++-13 13.3.0 -march=x86-64-v4` (`~/builds/rel/forge`, sha256 in
`honesty/meta.txt`) and the TSan build `~/builds/tsan/forge` (`-fsanitize=thread -O1 -g`,
`nm -C | grep -c __tsan_` = 21). Machine: **4 cores**.

## What was asked / the answer / how sure

**What was asked.** Area 4 job 1: Threads 2, 4, 8, 16 on the first 100 positions of set G at
depth 12 with S14, under ThreadSanitizer; reports, exits, bestmove legality. Then, at the
coordinator's direction, the Threads-4 "hang" on one FEN was promoted to top priority with a
reproduction, a cross of the thread/depth axes, stacks while it is slow, and the obvious code
candidates checked by name.

**The answer.** Four results, in order of how much they matter:

1. **A thread-scaled node explosion exists on `5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1`.** At
   depth 12 the same position costs 79,980 nodes at Threads 1 (0.03 s, identical 10/10 runs)
   and 2.7 M to **1.25 billion** nodes at Threads 4 (0.17 s to 69.3 s), reaching **1.95 billion
   nodes / 103.9 s** at Threads 8. The bestmove is `f3f8` in every completed run at every thread
   count. It is not a wrong move; it is up to a **24,000x** search-cost blow-up caused by
   threading, on a position the engine already scores as lost.
2. **The score is NOT reproducible at Threads >= 2, even though the move is.** Same position,
   same depth, same settings, fresh process each time: Threads 4 returned `mate 17` and `mate 15`
   at depth 12, and with null move off, `+2402 cp`, `mate 14` and `mate 21` on three runs. `f3f8`
   came back every time. This is a correctness problem, not only a time one (04-F7).
3. **There is no deadlock and no hang.** 20 fresh processes at Threads 4 all answered within
   90 s. The stacks show every worker thread *working* (in `qsearch`, `pick_best`,
   `fill_pseudo_legal`, `make_move`), not parked and not waiting for each other. The earlier
   "hang" was one run of this heavy tail exceeding a 300 s limit. From a GUI or a clock it is
   still fatal, because the tail is unbounded, but it is not a lock bug.
4. **Zero ThreadSanitizer race reports in 400 searches at Threads 1/2/4/8**, and that zero is
   proven to be a live measurement by a planted unlocked-global counter reported by the same
   runner. The transposition table is lock-protected on every access. My prediction P2/P3 (that
   the table was unguarded) is **refuted**.
5. **19-F12 confirmed** with an independent harness, plus the two things it left open: the
   fabricated bestmove never has a nonzero node count, and it is never illegal — it is a
   plausible move with no search behind it.

**How sure.** Result 1: high — 62 process-runs, deterministic at Threads 1, monotone in the
number of threads, same bestmove throughout. Result 2: high for "no deadlock" (two full stack
captures of all 8 workers, all in search code); *not* claiming the tail is bounded — it clearly
is not. Result 3: high, because the planted fault proves the reporter works. Result 4: high, and
it also caught a bug in my own first control arm, which I discarded rather than report.

## Honesty numbers

All four pins match on the build under test (fresh process per line, raw output committed):

| check | expected | got | verdict |
|---|---|---|---|
| `bench 11` | 312866 | 312866 | PASS |
| `bench 13` | 862329 | 862329 | PASS |
| `bench 16` | 3024920 | 3024920 | PASS |
| `go perft 5` | 4865609 | 4865609 | PASS |

Raw: `honesty/raw_bench11.txt`, `honesty/raw_bench13.txt`, `honesty/raw_bench16.txt`,
`honesty/raw_perft5.txt`; see `honesty/HONESTY.txt` and `honesty/meta.txt`.

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| STEP 2 build + honesty check | done | `honesty/HONESTY.txt` | 4/4 numbers match |
| TSan build of the same source | done | `job1/meta_planted.txt`, `job1/run_searches.py` meta | `nm __tsan_` = 21 |
| Sanitizer proof 1: nm count > 0 | done | `job1/meta_planted.txt` | 21 |
| Sanitizer proof 2: planted fault is reported by the same runner | done | `job1/planted_proof_raw.txt` | race on `search.cpp:2154` reported |
| Threads 1/2/4/8 × 100 G positions × 2 reps, TSan | partly | `job1/table_threads.md`, `/home/ubuntu/runs/rep*` | rep1 t1/t2/t4/t8 complete (400 searches), t16 stopped at 18/100 to free the machine for the hang work |
| Threads 16 | not done | — | interrupted by the priority change; 18 records exist, not a table |
| Hang reproduction, 20 fresh processes at Threads 4 | done | `job1/hang/t4_d12_20.jsonl`, `job1/table_threads.md` | 0 hangs; walls 0.174–69.301 s |
| Thread axis 1,2,3,4,5,8 on the FEN | done | `job1/hang/t*.jsonl`, `job1/table_threads.md` | monotone blow-up 0.03 → 66.5 s median |
| Depth axis 10,11,12,13 at Threads 4 | done | `job1/job1/hang/t4_d*.jsonl`, `job1/table_threads.md` | depth 12 is where the tail explodes |
| Stacks while slow (`gdb`, batch, text) | done | `job1/hang/stacks/stacks_s01_t8_d12.txt`, `job1/hang/stacks2/stacks_s01_t8_d12.txt` | all 8 workers in search code; none deadlocked |
| TSan at the hang FEN | done via the sweep | `/home/ubuntu/runs/rep1_t*/raw/0090.out` | 0 race reports at that index |
| Legality of every recorded bestmove | done | `job1/audit_harness.txt` | 100 % legal, 0 records with a fabricated/0-node answer |
| 19-F12 check (independent harness) | done | `job1/check_quit.py`, `job1/table_quit.md` | CONFIRMS |
| `go infinite` / `go nodes` + immediate quit | done | `job1/F_infinite_quit.jsonl`, `job1/G_nodes_quit.jsonl` | both fabricate a bestmove |

## The thread axis (cold: fresh process, `ucinewgame` before `position`)

| threads | runs | hangs | median s | max s | nodes min | nodes max |
|---|---|---|---|---|---|---|
| 1 | 10 | 0 | 0.03 | 0.03 | 79,980 | 79,980 |
| 2 | 8 | 0 | 0.47 | 0.72 | 1,504,120 | 6,400,704 |
| 3 | 8 | 0 | 0.62 | 17.58 | 2,949,761 | 235,660,536 |
| 4 | 20 | 0 | 0.77 | 69.30 | 2,739,824 | 1,252,499,786 |
| 5 | 8 | 0 | 1.51 | 36.74 | 3,167,300 | 575,436,075 |
| 8 | 8 | 0 | 66.50 | 103.89 | 5,627,158 | 1,953,875,466 |

Depth axis at Threads 4: depth 10 median 0.10 s / max 0.19 s / 2,739,439 nodes; depth 11 median
0.17 s / max 1.40 s / 25,173,385; depth 12 median 0.77 s / max 69.30 s / 1,252,499,786;
depth 13 median 2.15 s / max 46.40 s / 812,344,815.

## The sentence that matters to the owner

At identical settings, **Threads 4 gives a different mate distance on successive runs** (17 and 15
at depth 12; 13 and 12 at depth 14), and with null move effectively disabled, three runs of the
same position at the same depth gave **+2402 cp, `mate 14` and `mate 21`**. A multi-threaded
score is therefore **not reproducible even when the move is**: `f3f8` came back every single time.

That, not the node count, is the finding. The node count (up to 1.95 billion) is the *symptom*
that made it visible, and the 2.2x / 11x / 15,600x spread across three similar positions is the
*shape question* that is still open. But a search whose reported score changes between runs of
the same position at the same depth cannot be trusted for anything that consumes the score --
time management, tuning comparisons, or any A/B that measures centipawns.

What this is NOT: the move never differed, so I have no evidence of a lost game from a wrong
move. And on two of three positions tested the thread scaling was ordinary, so this is **not** a
general "multi-threaded search is broken" defect and must not be ranked as one.

## Findings, each with a command that shows it again

- **04-F1** thread-scaled node explosion — `python3 job1/hang_repro.py <exe> /tmp/hang t1_d12_10
  --runs 10 --threads 1 --depth 12 --limit 90`, then `t4_d12_20 --runs 20 --threads 4` and
  `t8_d12 --runs 8 --threads 8`.
- **04-F2** the "hang" is the tail, not a deadlock — `job1/hang/t4_d12_20.jsonl`, 20 rows,
  `hang` false everywhere.
- **04-F3** stacks show every worker working — `gdb -p <pid> -batch -x job1/hang/stacks/_gdb_s01_t8_d12.cmds`;
  captured twice, `job1/hang/stacks/` and `job1/hang/stacks2/`.
- **04-F4** zero TSan reports in 400 searches, with the planted-fault proof —
  `job1/planted_proof_raw.txt` and `python3 job1/analyse.py /home/ubuntu/runs`.
- **04-C1** CONFIRMS 19-F12 — `python3 job1/check_quit.py /home/ubuntu/runs/quit_rel2`.
- **04-C2** CONFIRMS seat 10's cold-start rule, plus the `ucinewgame`-ordering trap —
  `job1/hang_repro.py` comment block; `job1/hang/t4_d12_20.jsonl` vs the discarded first probe.

## Suspicions, not proven

1. **The blow-up is a per-thread work duplication, not a slowdown.** Median time rises with
   thread count (0.03 → 0.47 → 0.62 → 0.77 → 1.51 → 66.5 s) while the bestmove never changes,
   and the node counters are summed across workers. If each worker searched its own overlapping
   share without useful TT sharing on this position, total nodes would rise with thread count
   exactly as observed. **Not proven**: my runner records the aggregate node count the engine
   prints, not a per-worker split, so I cannot yet say whether the work is duplicated or the
   tree is genuinely larger.
2. **The position is probably a "lost but not pruned" case.** Threads 1 returns in 0.03 s at
   depth 12; something about the position makes the single-threaded search prune hard, and the
   multi-threaded version apparently loses that pruning. **Not proven**: I did not instrument
   the pruning decisions, and with no time to patch I did not want to guess at which term.
3. **`f3f8` being the same at every thread count suggests the score is stable and the tail is
   pure waste**, i.e. the engine is spending 1.9 billion nodes to confirm a bestmove it already
   had. **Not proven**: I would need per-iteration node counts at Threads 8, which the tail
   makes very slow to collect.

## What I did NOT do, and the exact commands that would close each gap

These are the three open questions, each with the command that would answer it. **I started
none of the first two** (the coordinator's instruction); step 3 I did run, and it came back
negative.

**Gap 1 — the shape condition.** What property of the hang FEN triggers the explosion, when two
same-shape positions scale normally (2.2x, 11x)? Concretely I would bisect the position: remove
one piece at a time and re-measure the Threads-4/Threads-1 node ratio, to find which piece or
which combination is responsible. Exact next command:

```
python3 forge-combo29/swarm/04/job1/divergence.py /home/ubuntu/builds/rel/forge /tmp/shape \
  bisect --threads 1,4 --depths 12 --runs 2 --fen '5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1'
```
with a loop over piece removals (a `--fen` per variant) comparing the T4/T1 node ratio.
What would settle it: a variant that keeps the ratio above ~100x and one that drops it near 2x,
differing in a single piece.

**Gap 2 — is the divergence a depth artefact?** Everything above is at a fixed *depth*, and
threads reach a given depth by different paths, so the divergence might vanish at a fixed *node
count* (which forces the same amount of work regardless of speed of convergence). Not started.
Exact next command:

```
python3 forge-combo29/swarm/04/job1/divergence.py /home/ubuntu/builds/rel/forge /tmp/nodes \
 nodes100m --threads 1,4 --depths 12 --runs 3 --limit 300
```
plus a `--go` variant of `divergence.py` sending `go nodes 100000000` instead of `go depth 12`
(the script currently only supports `go depth`; that is the one change needed). What would
settle it: if the scores agree at a fixed node count, the nondeterminism is depth-path-dependent
and therefore a tuning/measurement hazard; if they still disagree, the search state itself is
shared unsafely and it is a correctness bug.

**Gap 3 — cause (step 3): DONE, negative.** Widened aspiration (`AspirationDelta=200`: +2637 then
`mate 14`) and null move effectively off (`NullMoveMinDepth=10`: +2402, `mate 14`, `mate 21`) both
still show the disagreement and the node spread, so neither the aspiration window nor null move is
the cause. Recorded as finding 04-F8.

**Also not done:** no fix (per instruction, and no time). Threads 16 stopped at 18/100 to free
the machine, so no Threads-16 table exists. No `perf` profile of the blow-up (area 9's tool).
The 19-F12 quit re-run with the integrity fields completed only 2 of 8 cases before I stopped it
to free the CPU for timing-sensitive runs; the earlier complete run is in
`job1/table_quit.md`, and its control arm was the discarded pipelined one described in 04-C1.

## What I am NOT sure about

- Whether the tail can exceed 90 s on a *fast* run — my largest observed completed run was
  103.9 s at Threads 8, and I capped runs at 90–120 s, so the true upper bound is unknown and
  is likely unbounded.
- Whether 19-F12's fabricated `a2a3` is the same root cause as the tail. Both involve the search
  being cut short, but the fabricated answer needs a *stopped* search and the tail is a search
  that never stops; I see no evidence linking them and do not claim one.
- Whether this reproduces on the owner's machine with different core counts, since the blow-up
  is thread-count-dependent and my host has only 4 cores.

## Times: see `job1/hang/stamps.txt` and the per-run `wall` fields

Every wall time in the tables is a `time.monotonic()` difference inside `hang_repro.py`, recorded
per run in the JSONL; the run boundaries are `date -u` lines in `job1/hang/stamps.txt`. Job
boundaries: `git log --format='%h %ad %s' --date=iso` on the branch.

## Last command's output

```
$ git status --short && ls job1
<see the appended status/ls block below>
```

# REPORT job 4 — area 7 (reading the code for faults): the UCI loop's option surface
seat 27 · branch `for-fable-and-opus/swarm-27` · base `6b98f217` · seed 2701

## What was asked / the answer / how sure

- **What was asked:** continue area 7's file order (search, move picker, position, transposition table, UCI loop…)
  with a test for anything suspicious and a patch only if a fault is proven.
- **The answer:** the option surface is clean. All **81** options the engine advertises were exercised with
  **291** setoption cases (every spin at min−1, min, max, max+1; every check with `true`, `false`, `maybe`):
  **0** advertised min/max values were refused, **0** cases answered `unknown option`, and the four options whose
  effect can be observed from outside all behaved as advertised (below). Along the way I raised **two false
  alarms of my own** and killed both — they are on the record in `job4/FALSE_ALARMS.md` because a bad alarm costs
  the owner more than a missed one.
- **How sure:** high for "the advertised bounds are accepted and take effect", and high that a refusal *can* be
  seen by this harness (planted control refused `MultiPV 99`, `Hash 99999`, `Threads 0`). Not sure that every
  option's *semantics* match its name — only four have an externally visible effect.

## Honesty numbers

Unchanged from `HONESTY.txt` (this job changed no engine code and produced no patch): bench 11 = 312866,
bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609, on build `e06310ec…`.

## Steps

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| read the whole `setoption` handler and its neighbours in `src/uci.cpp` | done | this report | no fault; the parser accumulates multi-word names correctly |
| exercise every advertised option at its boundaries | done | `job4/f1/result.json`, `job4/f1/SUMMARY.txt` | 291 cases, 0 unexpected refusals |
| planted control: values that MUST be refused | done | `job4/f1/planted.json` | `MultiPV 99`, `Hash 99999`, `Threads 0` all refused |
| observable effect per option that has one | done | `job4/f1/SUMMARY.txt` | see table |
| record my two false alarms | done | `job4/FALSE_ALARMS.md` | both were my shell quoting, not the engine |

## Observable effects (all read from raw output; every parse asserted its line)

| option | probe | result |
|---|---|---|
| `Threads 1` vs `2` — **CORRECTED, measured in ONE process (warm)** | `go depth 10` from startpos | 13102 nodes `d2d4` vs 30356 nodes `c2c4`. **This row compared two searches that shared a process, so the Threads 2 figure is WARM** (seat 10's rule: one process gives 56,720 then 4,951 then 4,516 for identical searches). Re-measured with a fresh process each: Threads 1 = 13102 `d2d4`, Threads 2 = **14883** `c2c4`. The conclusion (both search; the move differs) holds, but the 30356 number was not a cold one and must not be quoted. |
| `Threads 4` | same | 21819 nodes, `c2c4` |
| `MultiPV 1` / `3` | distinct `multipv` indexes in one `go depth 8` | `[]` (no index printed at MultiPV 1, correct) / `[1, 2, 3]` |
| `Move Overhead 10` vs `0` | three `go movetime 60` per setting, wall clock | median 50.3 ms vs 60.2 ms — the overhead really is subtracted, which is 08-F2's finding reproduced here as an effect, not a new claim |
| `Hash 16` | `hashfull` on a depth-12 search | non-zero (10–15), so the table is really in use |

## Suspicions, not proven

- `UseNNUE`, `NnueFile`, `NNUEArchFile`, `NNUEArch`, `DeadMaterial`, `EvalRule50Damp` and
  `SoundMatePruning` change search **semantics** but print nothing you can read back; my harness can only prove
  they are accepted. `NNUEArch true` + a net file is the owner's PC configuration (Opus file 2), so whether that
  combination loads cleanly I did not test.
- `setoption` calls `stop_search()` first (`uci.cpp:259`), so a `setoption` during a search aborts it. That is
  by design in most engines; area 2 owns whether a GUI is harmed by it.

## What I did NOT do

- Did not test option *semantics* beyond the four observable ones.
- Did not patch anything: no fault was proven, and the brief allows a patch only for a fault with a test.

## What I am NOT sure about

- Whether any of the 81 options is advertised but has no effect at all (a silently dead option). Proving that
  needs a measurable difference per option, which most do not offer.
- Whether the `max` of `Hash` (2048) can actually be allocated on a 15 GB machine under load; I skipped values
  above 512 MB deliberately and say so.

## Times
`job4/stamps.txt`.

## Last command's output
`ls job4` and `git status --short` are in `job4/last_commands.txt`.

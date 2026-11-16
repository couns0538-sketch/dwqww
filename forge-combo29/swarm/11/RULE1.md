# RULE 1 — a zero needs a planted one (seat 11 compliance record)

Opus `FABLE_TO_swarm_2.md`: "A result '0 illegal moves / 0 sanitizer lines / 0 hangs /
0 differences' counts only when the SAME harness, unchanged, counted one planted case.
Commit the plant's output beside the real one."

## What this cost me: Rule 1 found a real defect in my own harness

When I first ran the planted-hang control, my runner **blocked forever**. The cause:
`subprocess` `stdout.readline()` has no timeout, so my `deadline` check was only made *before*
a blocking read — a hung engine hung the harness. Every "0 crashes / 0 hangs" number I had
produced up to then was therefore **not shown**: the harness could not have reported a hang
at all. This is exactly what Rule 1 exists to catch.

Fix: a daemon reader thread fills a `queue.Queue`, and `readline` does `queue.get(timeout=...)`.
A hung engine now raises `TimeoutError`, counted as a crash/hang, and the batch restarts.

After the fix I re-ran job 1's full 20,000 cases with the shipped harness
(`job1/run_asan_v2/`) and got the **identical** numbers to the old run —
17,130 refused / 2,870 accepted / 24 py-invalid / 0 illegal / 0 sanitizer lines — so the
fix changed nothing about the engine's behaviour and everything about my ability to detect a
hang.

## The planted cases, each through the SAME harness

| zero I claim | plant | harness | plant's counted result |
|---|---|---|---|
| 0 illegal bestmoves | `controls/fake_illegal.py` answers `bestmove a1a8` to every `go` | `runner.py` + `analyze_job1.py` (unchanged) | `illegal bestmove 2` — `controls/plant_run/` |
| 0 hangs | same file stops answering `readyok` on a `PLANTHANG` FEN | `runner.py` (unchanged) | `crashes 1` after a 3 s timeout — `controls/plant_hang_run/` |
| 0 sanitizer lines | a scratch copy with a planted heap over-read in `Board::set_fen` | `runner.py` (unchanged) | `sanitizer_lines 1`, the UBSan line in `engine.stderr` — `job1/proof2/` |

## Reproduction

```
python3 forge-combo29/swarm/11/runner.py \
  --exe forge-combo29/swarm/11/controls/fake_illegal.py \
  --out /tmp/plant --cases forge-combo29/swarm/11/controls/plant_cases.tsv
python3 forge-combo29/swarm/11/analyze_job1.py /tmp/plant/results.jsonl /tmp/plant
#  -> illegal bestmove 2

python3 forge-combo29/swarm/11/runner.py \
  --exe forge-combo29/swarm/11/controls/fake_illegal.py \
  --out /tmp/planthang --cases forge-combo29/swarm/11/controls/plant_hang.tsv --timeout 3
#  -> crashes 1
```

## Honest scope
The hang plant is counted in the runner's `crashes` field, not a separate `hangs` field. My
jobs never needed a distinct hang counter (job 1's and job 2's cases always answer), but I will
not claim "0 hangs" as a distinct measurement — I claim "0 crashes, and the harness is shown to
catch a non-answer".

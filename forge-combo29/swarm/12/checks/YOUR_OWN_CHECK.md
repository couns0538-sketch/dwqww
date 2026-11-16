# YOUR OWN ONE-MINUTE CHECK: are these Hash/MultiPV settings safe on YOUR machine?

Seat 12, area 2. Every timing in my MultiPV tables was taken on a **4-core cloud box with 15 GB of
RAM**. The *shape* of the effect is a property of the engine's code and is the same on any machine;
the *absolute milliseconds* are a property of that box and may not be.

So here is the check to run on the PC. It takes about a minute.

## What you need

- The engine binary (`forge.exe`).
- Python 3, which the PC already has if anything else in this project runs.
- Nothing else — no pip, no python-chess. The script drives the engine over stdin.

## The command

Put `selfcheck.py` (in this folder) anywhere and run:

```
python selfcheck.py C:\path\to\forge.exe
```

That is the whole thing. It prints a table and a verdict per setting.

Add `--runs 7` for a steadier median, or `--threads 1` to be explicit (1 is the default and is what
my numbers used).

## What it does, so the numbers mean what you think

For each of four settings it starts a **fresh** engine process, sends

```
uci
setoption name Hash value H
setoption name MultiPV value M
setoption name Threads value 1
setoption name OwnBook value false
position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
isready
go depth 6
```

and times from `go` to `bestmove` with a monotonic clock. It reads every line up to `bestmove`
**before** sending `quit` — an engine killed mid-search answers a fabricated first legal move with 0
nodes, which would look impressively fast and mean nothing (that is seat 19's finding, and the trap
this script is written to avoid).

A run that produces no `info depth` line is counted as a **failure**, never as a fast run.

## What to expect

| setting | cloud-box median | your machine is **worse** if |
|---|---|---|
| MultiPV 2, Hash 16 | 17 ms | over **200 ms** |
| **MultiPV 2, Hash 64** | **52 ms** | **over 200 ms** ← the reference point |
| MultiPV 4, Hash 64 | 82 ms | over 500 ms |
| MultiPV 2, Hash 256 | 250 ms | over 1,000 ms |

The script applies a **ratio rule** (PASS within 4x of the cloud number, WATCH within 10x, FAIL
beyond) **plus an absolute floor** (over 500 ms at depth 6 is reported SLOW whatever the ratio says).
Both exist because each alone is wrong: a pure ratio lets a big budget excuse a slow search, and a
pure absolute threshold hides a machine that is uniformly 8x slower.

**MultiPV 2 at Hash 64 over 200 ms means your machine is about 4x this cloud box.** That is the
single number to look at: at 4x, every table I published still holds in shape, and the practical rule
(MultiPV 4 to 128 MB, 3 to 256 MB, 2 to 512 MB, 1 unlimited) should be cut roughly in half.

## The one setting that is never safe

```
setoption name Hash value 2048
setoption name MultiPV value 8
go depth 6
```

On the cloud box that takes **8-9 seconds** and on a 5 s clock reaches **depth 0-1** — no completed
iteration at all. It is slow because the engine clears the whole transposition table once per extra
PV line, so the cost is `(MultiPV - 1) x Hash`. That is a code property, not a machine property:
**it will be slow on your PC too**, and the fix is the owner's call, not a setting.

## The script was tested against known-bad engines, not just the real one

Because "all PASS" is worthless if the checker cannot fail:

| engine | expected | got |
|---|---|---|
| the real PC r15 build | all PASS | all **PASS**, ratios 0.9-1.0x |
| a fake engine that sleeps 900 ms per search | must not pass | **FAIL 53.0x / 17.3x / 11.0x**, and **SLOW 901 ms** at the largest cell |
| a fake engine that never answers | must report, not crash | **FATAL: the engine did not answer `go depth 1`**, exit 1 |

The last row matters: an engine that ignores stdin produces empty output and exit code 0, which is
exactly the silent-zero trap (seat 02's S-F1, confirmed by me as S-C2). The script refuses to report
a table in that case.

## Files

- `checks/selfcheck.py` — the script (one file, standard library only).
- `checks/SAFE_SETTINGS.md` — the boundary tables this check is derived from.
- `checks/check_02f7_pc.json`, `checks/check_02f7_base.json` — the S-C3 2x2 raw data.

## What this does not tell you

- Nothing about *playing strength* except through depth: it times `go depth 6` on one position.
  For game play, the 5 s clock table in `SAFE_SETTINGS.md` is the relevant one, and a slower machine
  loses proportionally more depth.
- Nothing about memory pressure: `Hash 2048` allocates 2 GB, which this box has and a smaller PC may
  not. If the engine fails to start at a large Hash, that is a different problem from slowness.

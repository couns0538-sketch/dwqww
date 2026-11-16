# HARNESS AUDIT — seat 03, after seat 19's broadcast (finding 19-F12)

Seat 19 reports: if `quit` (or a closed stdin) arrives while a `go` search is running, this build answers a
FABRICATED `bestmove` with no `info` lines and 0 nodes. I reproduced that myself before trusting it:

```
$ printf 'uci\nisready\nucinewgame\nisready\nposition startpos\ngo depth 12\nquit\n' | ~/build-rel/forge | tail -1
bestmove a2a3
$ { printf 'uci\nisready\nucinewgame\nisready\nposition startpos\ngo depth 12\n'; sleep 3; printf 'quit\n'; } \
    | ~/build-rel/forge | tail -1
bestmove e2e4        (with `info depth 12 ... nodes 56720`)
```

So the broadcast is real on my build too. I do **not** report it as my finding — seat 19 has it with a control.

## What my harnesses did

| harness | sends | quit pipelined behind a search? | affected? | action |
|---|---|---|---|---|
| `honesty.sh` (job0) | one stream: `uci/isready/ucinewgame`, the line, `quit` | yes, but the lines are `bench N` and `go perft 5` | **no** — see below | re-proved with `honesty2.py` anyway |
| `job1/engine_perft.py` | interactive; reads each `readyok` and each `nodes` line before the next command | no | no | none |
| `job2/divide_sets.py` | interactive; reads `readyok` per position, reads the `nodes` line of each `go perft 1` | `quit` only after the last read | no | none |
| `job2/ep_divide.py` | **one pipelined string** `position / isready / go perft 1 / quit` | **yes** | no (perft is inline), but the method was wrong | **replaced by `job2/ep_divide2.py`**, verdicts identical |
| `check13/*` | interactive (my `engine_perft.py`) | no | no | none |

### Why `bench` and `go perft` cannot be hit by it

Both are executed *inside* the UCI input loop, not on a search thread — `src/uci.cpp:489` (`perft`) and
`src/uci.cpp:590` (`bench`). The loop cannot read the next line (`quit`) until the perft/bench call returns, so the
fabricated-bestmove path is never reached. Measured, not just read:

```
$ printf 'uci\nisready\nucinewgame\nisready\nposition startpos\ngo perft 4\nquit\n' | ~/build-rel/forge | tail -1
nodes 197281                      (= correct startpos perft 4)
$ printf 'uci\nisready\nucinewgame\nbench 11\nquit\n' | ~/build-rel/forge | grep 'info string bench'
info string bench depth 11 nodes 312866 ...     (= pinned value)
```

## The honesty pins, re-measured with a harness that cannot pipeline

`honesty2.py` sends one command, reads stdout until that command's completion token (`uciok`, `readyok`,
`info string bench`, `nodes `), and only then sends the next; `quit` comes after the last read.

```
bench11	MATCH	expected nodes 312866	got info string bench depth 11 nodes 312866 time 464 nps 674280	wall 0.533s
bench13	MATCH	expected nodes 862329	got info string bench depth 13 nodes 862329 time 1416 nps 608989	wall 1.477s
bench16	MATCH	expected nodes 3024920	got info string bench depth 16 nodes 3024920 time 4211 nps 718337	wall 4.272s
perft5	MATCH	expected nodes 4865609	got nodes 4865609	wall 0.073s
```

Saved: `job0/honesty2.summary`, `job0/honesty2.meta`, `job0/bench11.out` … `job0/perft5.out`.

**Note on my HONESTY.txt:** the times there (162 / 440 / 1438 ms) were taken while nothing else ran; the numbers
above are slower (464 / 1416 / 4211 ms) because python-chess perft jobs were running on all four cores at the time.
The NODE COUNTS — the only pinned quantity — match in both.

## Verdict on my already-recorded results

- **Job 1 (perft 1..4 on 5,000 R)**: unaffected. Nodes come from `go perft`, which is inline; the comparison found
  non-zero, python-chess-identical counts at every depth (113,656 / 2,647,591 / 75,639,746 / 2,196,757,662), which
  a 0-node fabricated answer could not produce. **Not re-run.**
- **Job 2 (perft 1..4 on 314 special)**: same reasoning (8,555 / 266,744 / 8,642,784 / 288,188,329),
  plus one harness (`ep_divide.py`) was rewritten and re-run with identical verdicts. **Node results not re-run.**
- **`divide_sets.py` results (root move sets)**: that harness was already interactive and reads `nodes` before
  sending anything else. Valid.
- **`honesty.sh` pins**: re-measured safely (above). Identical node counts.
- No `go depth` / `go nodes` / `go movetime` / `go infinite` result exists in my folder yet. Job 3 uses
  `go perft 5`, which is inline; when I later run a depth search I will use the read-until-`bestmove` pattern.

## Addendum 21:37Z — parse audit (seat 19's NaN warning)

Two real defects in my own helper files, found by re-auditing every engine-output parse site:

1. `honesty.sh` grepped for `^Nodes searched|Nodes:` — this engine prints NEITHER string, so that grep matched
   nothing. My published pins came from a different, working grep (`info string bench` / `^nodes`), and
   `honesty2.py` re-proved them; but the dead pattern is recorded here rather than quietly removed.
2. `divide_sets.py` printed its summary to the terminal only; `job1/div_R_summary.txt` and
   `job2/div_special_summary.txt` are now saved, and `assert_measured.py divide` checks them.

`assert_measured.py` now fails loudly on a missing/NaN/zero-count result, with negative controls that both fail
(see PARSE_AUDIT.md). Every recorded number passed it.

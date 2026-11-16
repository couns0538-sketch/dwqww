# The terminal-root phantom iterations: mechanism and what it costs a harness

**Seat 01, 2026-11-16. Confirms and scopes seat 25's S-F7. Evidence: `terminalprobe/check_terminal_root_lines.txt`.**

## What happens

On a **terminal** root — checkmated *or* stalemated — these commands emit **64 `info depth` lines at 0 nodes**:

| command | terminal root | normal root |
|---|---|---|
| `go depth 5` | 5 lines (correct) | 5 lines |
| `go nodes 100` | **64 lines**, max depth 64, 0 nodes | **1 line**, depth 1, 67 nodes |
| `go movetime 50` | **64 lines**, max depth 64, 0 nodes | 13 lines |
| `go depth 64` | **64 lines**, max depth 64, 0 nodes | (does not return quickly) |

`bestmove 0000` in every terminal case, which is the correct UCI answer.

## The mechanism, read from the code

The iterative-deepening loop emits one `info depth` line per iteration and leaves only on a `break`:

- the soft-node stop: `if (soft_node_limit_ != 0 && total_nodes() + extra_nodes_ >= soft_node_limit_) break;`
- `should_stop()`, which is how a node or time limit is honoured.

On a terminal root the search does no work, so **nothing increments the node count**. `total_nodes()` stays at
0, the soft-node test can never fire, and `should_stop()` never sees a limit reached on work that is not
happening. The loop therefore runs to `max_depth` (64) and emits an empty line at each depth.

So it is not a loop bug: with zero work per iteration, the only exit the loop has is the depth cap.

## Why the normal-root control is what makes this a finding

Without it, "64 lines at 0 nodes" could be a general loop defect. The normal root gives **1 line** for
`go nodes 100`. The behaviour is therefore **terminal-specific**, which is the scope seat 25 asked for and the
reason it is cosmetic for strength rather than a search defect.

## What it costs a harness

| consumer | effect |
|---|---|
| a **depth-keyed training label** | records "depth 64 reached" for a position where no search happened — a phantom target |
| a **progress display** | shows a search that never ran, at increasing depth |
| a **latency harness** | timing a terminal position times an empty loop, not a search |
| a **PV checker** | sees 64 empty PVs; a checker that requires a non-empty PV will flag them all, correctly but noisily |
| **strength** | no effect: the position is over and `bestmove 0000` is right |

## The rule for a harness

**Special-case a terminal root before you measure anything from it.** A game that has ended should stop the
loop, not be searched — a match program that calls `go` on a finished game gets a well-formed but meaningless
64-line answer, and any metric read off it (depth, PV, "search effort") is an artefact.

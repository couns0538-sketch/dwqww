# Quit-mid-search: is the fabricated `bestmove` a memory fault? — answer for seat 19 / the swarm

Seat 19's finding (19-F12): sending `quit` while a search runs makes the engine answer a
`bestmove` with 0 nodes and no `info` line, on startpos giving `a2a3`. The coordinator asked
seat 12 to run it under ASan+UBSan and say whether the bestmove print reads freed memory —
"a fabricated a2a3 with 0 nodes smells like a root move array read before it is filled".

## Answer, in one line

**It is not a memory fault.** The move printed is `root_candidates.front()` — the *first entry of
the fully built legal-move list* — and nothing is freed or read-after-free on the way out. 100
interrupted searches across 5 positions produced 0 sanitizer lines, with the planted-fault
control counted by the same runner.

## (A) Where the move comes from — measured, not read

For every position I took the engine's **own** root move order (first line of `go perft 1`, which
enumerates `root_candidates` in the same order the search uses) and the bestmove that the
interrupted search prints:

| position | engine's root order [0] | quit-mid-search bestmove | nodes | info lines | equal |
|---|---|---|---|---|---|
| startpos | a2a3 | a2a3 | none | 0 | yes |
| kiwipete | a2a3 | a2a3 | none | 0 | yes |
| endgame3 | e2e3 | e2e3 | none | 0 | yes |
| middlegame | a2a3 | a2a3 | none | 0 | yes |
| mateset | g1e2 | g1e2 | none | 0 | yes |

**5/5 equal**, and in each case the printed move is a legal move of that position in the
engine's own generation order. So `a2a3` is not garbage and not a stale pointer: it is the first
legal move, i.e. the documented fallback.

## (B) The code path (read, then confirmed by the measurement)

`src/search.cpp` — the fallback is explicit and unconditional:

- line 2265 `if (!root_candidates.empty()) result.best_move = root_candidates.front();` (drawn-root early return)
- line 2636 `result.best_move = root_candidates.front();` (emergency ply)
- line 2639 **`if (result.best_move.is_none()) result.best_move = root_candidates.front();`** — the last line before `return result`, which is the one that fires here: the interrupted search never set a best move, so the fallback fills it.
- `src/uci.cpp:559-570` then prints `result.best_move`; `0000` is printed only when `from == to`.

`root_candidates` is a by-value `MoveList` (a `std::array<Move,256>` plus a size) built at
`search.cpp:2203-2209` inside the same call, and `stop_search()` (`uci.cpp:169-178`) joins the
worker thread **before** the `bestmove` is printed — so the list is alive, owned by the search
frame, and completely filled when it is read. There is no `delete`, no reference into freed
storage, and no uninitialised element being read: the element read is index 0 of a list whose
size was already set.

## (C) Sanitizer evidence, with the two proofs the rules require

`quit_mid_search.meta` (beside the output) records the exe, its sha256, `id name`, the options
sent and:

```
nm_asan: 35      nm_ubsan: 15      nm_tsan: 0
```

The runner: 20 repeats x 5 positions = **100 interrupted searches**, one fresh process each,
`go depth 12` immediately followed by `quit` on stdin:

| position | runs with a sanitizer line |
|---|---|
| startpos | 0/20 |
| kiwipete | 0/20 |
| endgame3 | 0/20 |
| middlegame | 0/20 |
| mateset | 0/20 |

**total 0** — and the planted-fault control, driven through the *same* `run_case` function in the
same script, is counted 3 lines (heap-buffer-overflow + the UBSan line):

```
/agent/repos/planted/src/uci.cpp:199:40: runtime error: load of address ... insufficient space
==39236==ERROR: AddressSanitizer: heap-buffer-overflow ...
SUMMARY: AddressSanitizer: heap-buffer-overflow /agent/repos/planted/src/uci.cpp:199
```

So a zero here is a measured zero, not a runner that cannot see faults.

## What this means for the harness rule, and for MY earlier results

- The rule stands and I follow it: **read stdout to `bestmove` before the next command, and never
  close stdin mid-search.** My job-1 runner already blocks on each bounded `go` until its
  `bestmove` arrives (`read_until_bestmove`) and only writes `quit` after the sequence's own
  `isready` has been answered.
- **One of my own earlier harnesses did violate this**, before I fixed it: the first
  `two_doors.py` draft sent `quit` in the same write as the `go`, and its first result table
  showed `door1_hm99 -> g1e2, no nodes` — that row was the fabricated answer, not a measurement.
  I caught it, removed the pipelined `quit`, and re-ran; the numbers in the door report come only
  from the corrected harness. No finding of mine rests on a pipelined `quit`.
- I am **not** claiming 19-F12 as my own; it is seat 19's, and this file only answers the
  memory question they asked.

## Not proven / out of scope

- Whether the fallback *should* be the first legal move rather than the last PV move: the engine
  never reached a depth, so any answer is arbitrary; that is a protocol question, not a fault.
- I did not test `stop` + `quit` interleavings with threads > 1 (that is area 4's ground).

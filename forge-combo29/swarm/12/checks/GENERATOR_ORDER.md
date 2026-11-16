# Why the fabricated-move check must use the ENGINE's order, not python-chess's

Seat 12, area 2. **Threads 1.** This note exists because anyone repeating the check with python-chess
would get it wrong in two different ways, and one of them is silent.

## The two orders are not the same thing

- **The engine's generator order** — what `Board::legal_moves()` yields, and therefore what
  `root_candidates.front()` is. It is visible as the **first line of `go perft 1`**.
- **Python-chess's `sorted(m.uci() ...)`** — alphabetical by UCI string. Convenient, and wrong for
  this purpose.

They are both "the legal moves" and they are not the same sequence.

## Measured, both positions, same build (PC r15)

| position | engine order[0] | python-chess sorted[0] | do they agree? | fabricated move | matches engine? | matches python? |
|---|---|---|---|---|---|---|
| startpos | `a2a3` | `a2a3` | **yes** | `a2a3` | yes | yes |
| **kiwipete** | **`a2a3`** | **`a1b1`** | **NO** | **`a2a3`** | **yes** | **no** |

`kiwipete` = `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`.
The engine's first move there is `a2a3`; alphabetical order starts with `a1b1`.

## Why this matters — the failure is in both directions

**On startpos the two orders coincide.** A checker written with python-chess passes the startpos test
and looks correct. That is the dangerous case: the bug is invisible on the obvious test position.

**On kiwipete it inverts the verdict.** With python-chess order the fabricated move `a2a3` does NOT
match `a1b1`, so a checker would conclude "the move is not the first legal move, therefore this is not
a fabrication" — **and clear a real defect**. Conversely, if an engine ever published `a1b1` as its
fallback, the python-chess checker would call that fabricated when it was a genuine generator-first
move.

So an alphabetical checker is wrong in both directions and silent in the common case.

## What my tool actually does

`selfcheck.py` and `harness_checks.py` both read the order from **`go perft 1`**, which is the engine
listing `root_candidates` in its own order, and wait for perft's final `nodes` line (perft sends no
`bestmove`, so waiting for one hangs). The check is:

```
fabricated  =  a bestmove was printed  AND  no `info depth` line was printed
first_legal =  first move of `go perft 1`        # engine order, not sorted()
```

and it reports both facts separately (`fabricated` and `is_first_legal`) so a reader can see which
condition fired.

## Reproducing it

```
python3 forge-combo29/swarm/12/checks/harness_checks.py ~/build/pc_r15/forge
```

prints for startpos: `bestmove a2a3 with 0 info depth line(s)`, `first legal move in generator order:
a2a3  (move equals it: True)`, verdict **FABRICATED**.

To see the orders diverge, compare the first line of `go perft 1` at kiwipete with
`sorted(m.uci() for m in chess.Board(fen).legal_moves)[0]` — they differ, as the table shows.

## Files

- `checks/harness_checks.py` — the check, with `first_legal_move()` reading perft order.
- `checks/harness_checks_pc.txt`, `checks/harness_checks_base.txt` — raw runs on both builds.
- `checks/selfcheck.py` — the same check integrated into the one-command tool.
- `checks/order_demo.txt` — the table above, raw.

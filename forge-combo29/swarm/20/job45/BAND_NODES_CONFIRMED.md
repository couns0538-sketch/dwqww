# seat 20 — job 45: the `go nodes` band below 26, confirmed with per-run data

Second independent confirmation of the owner's second live PC defect. `Threads 1`, both builds, **every** value
1–30, **3 runs each**, fresh process per run, startpos.

## The result — identical on both builds

| `go nodes` N | bestmove | info-depth lines | reported nodes | 3-run stability |
|---|---|---|---|---|
| **1 … 25** (all 25 values) | **`a2a3`** | **0** | **0** | **stable ×3 at every value** |
| **26** | `d2d4` | 1 | 26 | stable ×3 |
| 27 … 30 | `d2d4` | 1 | 26 | stable ×3 |

**The boundary is exactly 26 on the base tree AND on the PC r15 build.** All 60 cells (30 values × 2 builds) were
identical across their 3 runs. This confirms seat 27's S-F2 / seat 17's S-C4 threshold from a third harness, and it
extends it in two ways they did not state:

1. **The whole band 1..25 behaves identically** — not just the values they sampled (1, 5, 10, 20, 25). Every value
   from 1 to 25 produces `a2a3` with **zero info lines and zero nodes**.
2. **The PC r15 build does not repair it.** The threshold and the answer are the same as the base tree, so this is a
   genuine open defect on the owner's engine (consistent with my S-F43 sweep, which found no PC20 switch touches it).
3. **Above 26 the answer is capped at 26 nodes** — `go nodes 27..30` still reports `nodes 26`, i.e. one root
   iteration is the smallest unit of work the search will do; the budget cannot buy a *partial* iteration.

## What the fabricated band actually is
`a2a3` is the first legal move in the engine's own generation order (my S-F27 shows the protocol cannot reveal that
order). With **0 info lines and 0 nodes** the engine has searched nothing and picked the first move. Below 26 there
is not enough budget for even one root iteration, so this is the same "unexamined first legal move" path I recorded
as S-F11 — now shown to cover a full 25-value band rather than the single `nodes 1` case.

## Rule-1 controls (asserted in the script, so a failure aborts the run)
- `go nodes 1000` on both builds gives a **real searched answer**: base `c2c3 / cp 12 / 701 nodes / 4 info lines`;
  PC `d2d4 / cp 9 / 971 nodes / 5 info lines`. So the harness can see a real search, and the 0-node rows are not a
  parser failure.
- The band's own upper edge (26+) is the internal positive control: the same command at 26 yields a searched line.

## What this means for the owner
A GUI or a test that sends a small `go nodes` budget gets **a move with no search and no info output at all** — the
engine reports nothing, so a naive harness sees "no info line" and may mis-read it as a hang or a missing answer.
Above 26 everything is normal. The boundary is a property of one root iteration's cost (26 nodes at startpos).

## Limits
- Startpos only. The 26 boundary is the cost of one root iteration **on this position**, so the number will differ
  on other positions; the *behaviour* (no partial iteration, first legal move) is what generalises.
- `Threads 1` only; I did not test whether Threads > 1 changes the boundary (and per S-C24 I would not trust a
  score there anyway).
- Depth/movetime forms are unaffected by this band (covered by S-C7).

# seat 20 — job 63: the surviving oddity — info-line VOLUME on a terminal root (score is right, volume is not)

After withdrawing S-C20 (the `mate 0` score is **correct** UCI), this is the part of that thread that remains a real
defect, kept separate on purpose because it is about **reporting volume**, not about whether the score is right.

## Measured (base 6b98f217 + S14, Threads 1, checkmated root `4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60`)

| command | answer | nodes | **info-depth lines emitted** |
|---|---|---|---|
| `go depth 1` | `0000` / `mate 0` | 0 | **1** |
| `go depth 5` | `0000` / `mate 0` | 0 | **5** |
| `go depth 20` | `0000` / `mate 0` | 0 | **20** |
| **`go nodes 100`** | `0000` / `mate 0` | 0 | **64** |
| **`go movetime 50`** | `0000` / `mate 0` | 0 | **64** |

## What is wrong, precisely
The engine **searches nothing** (0 nodes) yet emits **one info line per depth up to the limit** — and with a
`nodes`/`movetime` budget there is no depth limit, so it emits **64 lines**, all identical:

```
info depth N seldepth 1 score mate 0 nodes 0 nps 0 hashfull 0 time 0 pv
```

**Why that is a defect even though the score is right:**
1. **It is 64 false progress reports.** A GUI or an operator reads "depth 64" and concludes a deep search happened;
   the `nodes 0` is easy to miss in a scrolling log.
2. It is the same reporting loop that made me *think* something was searching when nothing was
   (`for depth = 1..max_depth emit(...)` on the terminal-root path).
3. The **score is correct** — I am not re-litigating that. A terminal root should report **once**.

## Expected behaviour (for contrast, same build)
A **stalemate** root behaves the same way (`0000` / `cp 0` / 0 nodes / lines = depth) — so this is a property of the
terminal-root path generally, not of checkmate specifically.

## Status of this family
- **Live.** Independent of the withdrawn S-C20, and separately observed by seat 25 (S-F7, 64 lines at 0 nodes) and by
  me (S-C7 / S-F16 family, and S-C11 where a bare `go searchmoves` emits 64 lines at 0 nodes).
- **Fix direction** (not a patch I am proposing, just what the code implies): the terminal-root branch should emit
  **one** line, not one per depth. That is a reporting change with no search behaviour attached, so it cannot move a
  node count.

## Limits
- One build, one checkmated position, Threads 1; the stalemate check is a second position.
- The 64 comes from the engine's depth clamp, so the exact ceiling is a build constant, not a protocol rule.

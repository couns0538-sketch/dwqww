# NOTE — a malformed `go nodes` line is treated as NO node limit (base tree), repaired on the PC build

Seat 30, area 10. **This is the most dangerous base-tree item I found, and it needs no exotic
input: any harness or GUI that formats a node budget from an unvalidated value can hang a search
forever.** Both builds were built by me; g++ 13.3.0, Release, `-DFORGE_MATE_ALPHA_GUARD=1` for the
PC build; **Threads 1, Hash 16**, every `setoption` confirmed by `readyok`, every search awaited.

## The one-line rule

> **A harness must never send a node budget it has not validated as a positive integer.**
> On the base tree `go nodes -1`, `go nodes xyz` and `go nodes depth 5` are accepted as *no node
> limit at all*: the search runs until something else stops it, so a driver that relies on that
> budget to end the search never gets a `bestmove`.

## The command

```
printf 'uci\nisready\nsetoption name Threads value 1\nisready\nposition startpos\nisready\ngo nodes -1\n' | <exe>
```

(equivalently, from a harness: send `go nodes <value>` where `<value>` is `-1`, `xyz`, or the word
`depth` because the formatter put the next keyword where the number belongs.)

## The output

### Base tree, S14, Threads 1 — 30 s window, no bestmove

| command | answered | seconds | bestmove | nodes at stop | depth |
|---|---|---|---|---|---|
| `go nodes -1` | **NO** | 30.00 | none | **48,497,658** | 31 |
| `go nodes xyz` | **NO** | 30.00 | none | **48,497,658** | 31 |
| `go nodes depth 5` | **NO** | 30.00 | none | **48,497,658** | 31 |
| `go nodes 0` | yes | 0.00 | a2a3 | — | — |

A longer earlier run with a 120 s window reached **207,603,225 nodes** (the `-1` and `depth 5`
forms) and **168,212,008** (`xyz`) before I killed it — the point is that it does not stop.

### PC r15 under FULL PC20 — every one answers at once

| command | answered | seconds | bestmove | node line | depth |
|---|---|---|---|---|---|
| `go nodes -1` | yes | 0.00 | a2a3 | none (0-node answer) | — |
| `go nodes xyz` | yes | 0.00 | d2d4 | 971 | 5 |
| `go nodes depth 5` | yes | 0.00 | d2d4 | 971 | 5 (`depth 5` obeyed) |
| `go nodes 0` | yes | 0.00 | a2a3 | none (0-node answer) | — |
| `go nodes 200000` (control) | yes | 0.11 | d2d4 | 166,281 | 17 |

**The repair holds on the PC build under PC20 for all three malformed forms**, including
`go nodes depth 5` where the trailing `depth 5` is correctly honoured as a depth limit and the
unusable `nodes` value is simply left out.

## Related, and why it matters for testers

- `stop` **does** recover the base tree: with a `stop` sent 1.0 s in, all three forms answer within
  0.01 s. So this is an *unbounded search*, not a deadlock — but a driver waiting for `bestmove`
  with no `stop` and no wall-clock guard waits forever.
- A **second** limit rescues the line without any stop: `go nodes -1 depth 5` answers at once
  (depth 5 obeyed), as does `go nodes 50000 depth 5`. If a harness always sends a depth or a clock
  alongside its node budget, it cannot fall into this trap.
- The fault is **independent of the search settings**: it reproduces under S14 exactly as under
  defaults (33,876,247 nodes in 25 s in the S14 run).
- It is **not** the `19-F12` quit-mid-search issue (that one needs stdin to close mid-search and
  produces an *instant fabricated* move; this one produces *no move at all*, because the search
  itself is unbounded).

## Evidence files

`pc/out_gohang/go_nodes_hang.json` (120 s window, both builds), `pc/out_gohang/s14_hang.json`
(S14), `pc/out_gohang/pc20_recheck.json` (this note's PC20 re-test), and
`pc/go_nodes_hang.py` (the harness — run `python3 pc/go_nodes_hang.py out_gohang 120`).

FINDINGS ids: **30-F25 / 30-F26 / 30-F28**, refined in wording by **30-C8** (it is an unbounded
search, not a deadlock), and re-confirmed on the PC build under PC20 by this note.

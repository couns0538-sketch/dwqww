# S-F14 (corrected): depth 64 is a CAP ON THE DEPTH COUNTER, not a mate sentinel

I first described this as "a mate is proven, so the engine reports depth 64". That was **too narrow**.
Further testing shows 64 is a hard cap on the reported depth counter in general, and a mate is only one
way to reach it. Correcting the finding rather than leaving the smaller version standing.

## What is actually true

The engine emits `info depth N` for N = 1, 2, 3, … and **64 is the maximum N it will ever print**. Any
search that can climb that far stops climbing at 64.

| board | command | info lines | max depth | nodes on last line | notes |
|---|---|---|---|---|---|
| mate-in-1 (rook) | `go nodes 20000` | 64 | **64** | 1,152 | stops at the cap having used 5.8 % of the budget |
| mate-in-1 (queen) | `go nodes 20000` | 64 | **64** | 1,731 | same |
| mate-in-2 | `go nodes 20000` | 64 | **64** | 5,485 | same |
| mate-in-3 | `go nodes 20000` | 22 | 22 | 19,161 | budget ran out first — no cap |
| mate-in-3 | `go nodes 250000` | 64 | **64** | 106,199 | **reaches the cap and does NOT stop** (no bestmove within 25 s) |
| non-mate startpos | `go nodes 20000` | 11 | 11 | 13,604 | budget ran out first |
| non-mate midgame | `go nodes 20000` | 11 | 11 | 19,832 | budget ran out first |
| non-mate midgame | `go depth 70` | 29 | 29 | — | **never reaches 64**; no bestmove within 25 s |

Two facts together establish the cap:
1. Positions that climb past 64 all report **exactly** 64 and no more.
2. A position asked for `go depth 70` climbs normally (29 lines in 25 s) and was nowhere near 64 — so
   the absence of a 65th line is a cap, not a failure to search deep enough.

## The node budget does NOT cause it
On the mate-in-1 board, the depth reported is purely a function of how many nodes were allowed:

| `go nodes N` | info lines | final depth | nodes |
|---|---|---|---|
| 200 | 11 | 11 | 198 |
| 500 | 27 | 27 | 486 |
| 1,152 | 64 | **64** | 1,152 |
| 2,000 | 64 | **64** | 1,152 |
| 20,000 | 64 | **64** | 1,152 |
| 250,000 | 64 | **64** | 1,152 |

The search converges on a mate immediately (1,152 nodes total), then keeps printing a fresh `depth`
line for each trivial re-verification until the counter hits 64, and stops. Above N = 1,152 the answer
is identical for budgets a thousand times apart.

## Why this is a measurement hazard (the part that matters to other seats)
1. **`depth 64` is not a depth.** It means "the counter hit its ceiling". On a mate-in-1 board that is
   64 "depths" for 1,152 nodes; on a hard mate-in-3 it is 106,199 nodes. Averaging depth across a mixed
   position set compares unrelated quantities.
2. **A latency harness that gates on depth is broken by it.** Waiting for "depth 12" on a mate-in-1
   board returns in ~0 ms after 216 nodes, so the harness records a falsely fast time precisely where it
   believes it is measuring a deep search. My own job-8 clock harness gated on `bestmove` rather than a
   depth, which is why it was not affected — but a depth-gated one would have been.
3. **A `go depth D` request with D > 64 IS answered** — the engine clamps its reported depth at 64 and
   returns a bestmove (measured: `go depth 65` and `go depth 70` both return `bestmove a1a8` at 1,152
   nodes). So such a request does not hang the engine. What it does do is make a harness that waits for
   "depth reached the requested depth" wait forever, because the 65th line never comes — the harness must
   therefore not gate on reaching D, and should treat 64 as the terminal depth. (Corrected: an earlier
   version of this file wrongly said such a request "can never be satisfied". See
   ../job11/DEPTH_CAP_ADDENDUM.md.)
4. **`nodes` on the final line is the honest counter.** Depth is not.

## Identical on both builds
The cap and the 1,152-node figure are identical on base 6b98f217 and PC r15, and on PC r15 with
MateAlphaGuard both true and false. It is not introduced by the PC patch.

## Reproduce (this is what a confirming seat should run)
```
cd forge-combo29/swarm/13/job10
python3 clamp.py ~/b/pc/forge     # the four-row table, both builds
```
`clamp.py` prints a table showing mate-in-1 reaching depth 64 at 1,152 nodes on a 20,000 budget while a
non-mate board stops at depth 10 with 13,102 nodes. A confirming seat needs only its own engine (base or
PC) and that script — it reads to `bestmove` before sending `quit`, so it is safe.

**If you want a one-liner instead of the script, use this form, which waits for the search:**

```
{ printf 'uci\nisready\nposition fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1\ngo nodes 20000\n';
  sleep 2; printf 'quit\n'; } | ./forge | grep -c 'info depth'      # prints 64
```

The required discipline: **read to `bestmove` (or sleep) before sending `quit`.** Either works; what must
not happen is `quit` arriving while the search is live.

### DO NOT USE this command — it is the 19-F12 trap, and its output is 0
Kept deliberately, with its real output, so nobody copies it by accident:

```
# WRONG - do not run this and conclude "no cap":
printf 'uci\nisready\nposition fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1\ngo nodes 20000\nquit\n' \
  | ./forge | grep -c 'info depth'

# actual output, on both base and PC builds:
0
```

That `0` is **not** evidence that the cap is absent. Piping `quit` straight behind `go` aborts the search
immediately — seat 19's 19-F12 fabrication trap — and the engine emits no `info` line at all. It is a
clean-looking zero that measured nothing, which is precisely the failure mode this whole run has been
about. **Two traps in one place:** the depth-64 cap (this finding) and the pipe-and-quit fabricated answer
(19-F12), both of which produce output that looks like a measurement and is not.


## What I got wrong, and why the correction matters
My first version said "when a mate is proven". That would have led a reader to think non-mate boards are
safe from the cap — and the mate-in-3-at-250k row shows a board reaching depth 64 and *not stopping*,
which the narrower story cannot explain. The corrected statement is broader and more useful: the cap
applies to any position that can climb to 64.

## A control failure that is itself the demonstration
While writing the reproduce section I published a one-liner that piped `quit` immediately after `go`,
and it printed `0` info lines. I nearly let that sit as "no cap observed" — which would have been a
clean-looking zero that proved nothing. The cause is seat 19's 19-F12 trap: a `quit` while a search is
running makes the engine answer a fabricated `bestmove` and emit no `info` lines at all.

That makes this file a two-trap demonstration, and worth keeping for that reason:
- the **depth-64 cap** (this finding), and
- the **pipe-and-quit fabricated answer** (19-F12),
both of which produce output that looks like a measurement and is not. The discipline that avoids both
is the same one: read to `bestmove` (or to the line you actually need) before sending `quit`, and never
treat an absence of output as evidence of absence.

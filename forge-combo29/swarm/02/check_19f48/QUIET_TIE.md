# The quiet 0-cp tie — it DOES differ, and this corrects my S-C11 conclusion

S-C11 concluded "exactly-tied positions agree in every cell", from six `mate 1` ties. I flagged then that all six
were found mates, solved almost instantly, and that a quiet centipawn tie was untested. Testing it changes the
conclusion.

## finding quiet ties cheaply
A 12-board scan with MultiPV 2 at depth 12 found **3 exact quiet ties** (`cp 0 / cp 0`, no mate):

| position | top two |
|---|---|
| `4k3/8/8/3p4/3P4/8/8/4K3 w - - 0 1` | cp 0 / cp 0 |
| `4k3/8/8/2p1p3/2P1P3/8/8/4K3 w - - 0 1` | cp 0 / cp 0 |
| `4k3/8/3n4/8/8/3N4/8/4K3 w - - 0 1` | cp 0 / cp 0 |

So they are not rare — 3 in 12 hand-written symmetric boards, and the simplest ones (a blocked king-and-pawn
position) produce them by construction since neither side can make progress.

## the two-mode test on the quiet ties

| position | N | `go nodes` | `go softnodes` | agree |
|---|---|---|---|---|
| `4k3/8/8/3p4/3P4/8/8/4K3 w` | 20000 | e1e2 | e1e2 | agree |
| `4k3/8/8/3p4/3P4/8/8/4K3 w` | 50000 | e1e2 | e1e2 | agree |
| `4k3/8/8/2p1p3/2P1P3/8/8/4K3 w` | 20000 | e1f2 | e1f2 | agree |
| `4k3/8/8/2p1p3/2P1P3/8/8/4K3 w` | 50000 | e1f2 | e1f2 | agree |
| **`4k3/8/3n4/8/8/3N4/8/4K3 w`** | **20000** | **e1e2** | **d3b2** | **DIFFER** |
| `4k3/8/3n4/8/8/3N4/8/4K3 w` | 50000 | d3b2 | d3b2 | agree |

**1 of 6 quiet-tie cells differs** — and it is not noise. Four runs of each mode at N=20000:

```
go nodes 20000      -> e1e2, e1e2, e1e2, e1e2   (deterministic)
go softnodes 20000  -> d3b2, d3b2, d3b2, d3b2   (deterministic)
```

Both modes are perfectly reproducible and they reproducibly disagree.

## the corrected rule
**"Exactly-tied positions agree" is FALSE as a general statement.** The accurate statement, from all three of my
measurements:

| condition | cells differing |
|---|---|
| found-mate ties (`mate 1` on >=2 moves), 6 boards | **0 of 12** |
| quiet 0-cp ties, 3 boards | **1 of 6** |
| non-zero gaps of 9-15 cp, 6 boards (S-C10) | **3 of 12** |

So a found mate is safe because the mate is solved before the two modes diverge, whereas **a quiet tie can still
diverge, because the tie is broken by whichever mode stops first at an equal-scoring leaf** — the S-F10 mechanism
applies to quiet positions and not to solved mates. The practical rule for a harness is therefore narrower than
S-C11 claimed:

**do not rely on a 0-cp tie to make `go nodes` and `go softnodes` comparable.** Only a position whose answer is
forced (a found mate) is reliably the same under both modes. For anything else, pick one command and stick to it.

## what this corrects, stated plainly
S-C11 said the rule was "complete" and that exactly-tied positions make the two commands comparable. That was an
over-generalisation from six mate positions, made one turn after I had written the opposite lesson about sampling.
The corrected scope is: **mates are safe, quiet ties are not, and the only reliable rule is not to mix the two
commands.**

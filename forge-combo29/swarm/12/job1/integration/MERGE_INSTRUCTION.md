## MERGE INSTRUCTION: composing this patch with seat 27's `drawn_root_reporting.patch.txt`

Raised by seat 27 (its finding S-F11). Seat 27's file:
`forge-combo29/swarm/27/job1/drawn_root_reporting.patch.txt` (a copy as I read it is in
`job1/integration/seat27_drawn_root_as_read.txt`).

### The order

Seat 27 says the two patches rewrite the same block and must be applied in one order only. They
do rewrite the same `root_drawn` block, and applying either one shifts the line numbers the other
one expects — but **in this repository's actual layout both orders produce a byte-identical
file**, so a merger cannot lose a fix by choosing the wrong order:

```bash
# from the repository root at 6b98f217:
patch -p1 --fuzz=0 < forge-combo29/swarm/12/job1/two_doors_mate.patch.txt   # seat 12
cd forge-combo29
patch -p1 --fuzz=0 < .../swarm/27/job1/drawn_root_reporting.patch.txt      # seat 27, after seat 12
```

Measured, both directions, each from a clean 6b98f217 tree:

| order | result | sha256 of the resulting `forge-combo29/src/search.cpp` |
|---|---|---|
| seat 12 then seat 27 | applies clean; seat 27's hunk at offset 19 lines, no fuzz | `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671` |
| seat 27 then seat 12 | applies clean | `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671` |

**Identical hashes, and `diff -u` between the two trees is empty** — the composition is
commutative here. The recommended order is seat 12 first only because that is the order the
composed build was tested in, not because the other is unsafe. Raw: `job1/integration/compose_hashes.txt`.

### One correction to seat 27's instruction

Seat 27's note says this patch "needs -p2 from the repo root". It does not: its paths are
`a/forge-combo29/src/search.cpp`, so **`-p1` from the repo root** is correct, and `-p2` fails
with `can't find file to patch` (measured). Seat 27's own patch is `-p1` from `forge-combo29/`,
as it says.

### Behaviour of the composed tree (my own reproduction, release build)

| board | base 6b98f217 | composed seat12 + seat27 |
|---|---|---|
| `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60` (seat 27's board) | f2f3 / cp 0 / 0 nodes | **a1a8 / mate 1 / 252 nodes** |
| `6k1/5ppp/8/8/8/8/8/R5NK w - - 100 40` (my door 1) | g1e2 / cp 0 / 0 nodes | **a1a8 / mate 1 / 216 nodes** |
| `6k1/8/5PPP/8/8/8/8/R6K b - - 99 40` (my node-level S-F4) | g8f8 / cp 0 / 36 nodes | g8f8 / cp 0 / 36 nodes — **still open**, as documented above |

Honesty pins on the composed build: bench 11/13/16 = 312866 / 862329 / 3024920, perft 5 =
4865609 — all four unchanged. Raw: `job1/integration/compose_table.txt`.

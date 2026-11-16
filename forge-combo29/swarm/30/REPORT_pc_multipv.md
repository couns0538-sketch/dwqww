# REPORT — the MultiPV / large-Hash fault on the PC r15 build

Seat 30, area 10. Everything here is from `forge-combo29/swarm/30/check6/`. Build: **PC r15** =
base `6b98f217` + the `FABLE_TO_swarm_5.md` patch (`sha256` starts `d6bd72c531f785f4`), built with
`-DFORGE_MATE_ALPHA_GUARD=1`, g++ 13.3.0, Release. **Threads 1, Hash as stated, OwnBook false, every
setoption confirmed by `readyok`, every search awaited** (19-F12 discipline).

## 1. Three lines
**Asked:** check seat 20's S-F50/S-C31 (MultiPV > 1 with a large Hash returns a no-search answer).
**Answer:** **The zero-node answer is real but rare** (3 of 36 probes under three CPU hogs, all at
Hash 2048 / MultiPV 3; 0 of 70 idle probes). The far bigger and fully reproducible finding is the
**mechanism**: on the MultiPV > 1 path the per-node cost grows about **100x with the Hash size**
while the search tree is byte-identical — which is why a 5-second clock budget buys one depth-1 move.
**How sure:** certain for the per-node table (same node count at every Hash, three-way contrast with
MultiPV 1 flat at 0.8 us/node); the zero-node rate is approximate (3/36) and I say so.

## 2. Honesty numbers of this build
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (all match, `pc/out/`).
Obtained with a synchronized harness that never closes stdin mid-search (`check_harness/honesty_sync.py`).

## 3. The chain, in the order it was established

| step | evidence | result |
|---|---|---|
| 30-F41: hold the search fixed, remove the clock | this folder | At `go depth 12` the MultiPV-3/Hash-2048 cell searches MORE than healthy (143,794 vs 52,591 nodes) and at `go nodes 200000` it is normal (52,591); only `go wtime 5000` collapses (67 nodes). **The search is sound; the clock path is not.** |
| 30-F42: cold vs warm | this folder | Not a cold-start effect: after a warm-up search in the SAME process, Hash 2048/MPV 3 still gives depth 1 / 170 nodes / 1,056 ms. |
| 30-F44: per-node cost vs Hash | this folder | `go depth 8`, MultiPV 3, **16,642 nodes at every Hash** but 33 / 78 / 287 / 1,956 / 3,394 ms for Hash 16/64/256/1024/2048 = **2.0 / 4.7 / 17.2 / 117.5 / 203.9 us per node**. |
| 30-C20: the control | this folder | The same grid at **MultiPV 1** is FLAT: 5,024 nodes in 4 ms = **0.8 us/node** at Hash 16, 256, 1024 and 2048 alike. The overhead exists only on the MultiPV > 1 path and scales with the table. |
| 30-F43: the owner-facing grid | this folder | At MultiPV 1, Hash 16/64/256/512/1024/2048 all give depth 16 and **exactly 266,687 nodes** (132-164 ms) on P1 with `go wtime 5000`. At MultiPV 3 the tree is the same (229,977) but wall time climbs 242 -> 305 -> 399 ms as Hash goes 16 -> 64 -> 128. |
| 30-C18 / 30-C19: the zero-node answer | `out_load/`, `out_load2/` | Under three CPU hogs on a 4-core box: **3 zero-node answers in 36 probes**, every one at **Hash 2048 / MultiPV 3**, moves `b8a8`, `d5d4` (P1) and `c3e4`, `e2d3` (P2) — the same cell and moves seat 20 published. 0 in 70 idle probes. |

## 4. What the owner should do
Keep **MultiPV 1 at any Hash size** — measured flat and identical from 16 MB to 2 GB. If MultiPV > 1
is wanted for analysis, keep Hash small (16-64 MB): the tree is unchanged, only the per-node cost
grows. Do not run analysis with MultiPV 3 and a 2 GB hash while the machine is busy: that is the cell
in which a move with essentially no search behind it (67 nodes, occasionally literally 0) is returned.

## 5. Suspicions, not proven
- I believe the MultiPV > 1 path touches the whole transposition table per node (that is what a cost
  linear in table size with a constant node count looks like), but I did not instrument the code to
  prove it. A repair should look there, not at the time manager's arithmetic, which only reacts to the
  inflated per-node cost.
- I did not test Hash sizes between 128 and 512 MB at MultiPV 3.

## 6. What I did NOT do
- Did not reproduce seat 20's 6/10 rate; my pooled rate is 3/36. Both are "real but not always".
- Did not test with their net file (I have the built-in evaluation, as file 5 says).

## 7. What I am NOT sure about
- Whether the 0-node answer needs load specifically or merely a slow machine; I only produced it
  under deliberate CPU contention.

## 8. Times: see the `date -u` stamps in each run's log. Last command output: see `last_cmd.txt`.

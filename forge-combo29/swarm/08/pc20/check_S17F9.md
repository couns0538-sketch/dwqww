# CHECK of seat 17's S-F9 — Hash size changes the pressure, not the answer — seat 08

Their claim:
> S-F9: "NOT a fault, TT resize verified: `Hash` 1/8/32/512/2048 MB changes only the pressure, not the answer —
> hashfull **440 / 58 / 10 / 0 / 0** and nodes **53652 then 52591 four times**, bestmove identical."

## Verdict: CONFIRMS, with one refinement they would want

My own harness, PC r15, PC20, Threads 1, `go depth 14`:

| Hash MB | bestmove | nodes | hashfull |
|---|---|---|---|
| 1 | **c3b5** | **69,686** | **450** |
| 8 | c3b5 | **73,610** | 65 |
| 32 | c3b5 | 73,610 | 17 |
| 512 | c3b5 | 73,610 | 1 |
| 2048 | c3b5 | 73,610 | 0 |

| their statement | my measurement |
|---|---|
| bestmove identical across all five sizes | **yes — `c3b5` every time** |
| hashfull varies strongly with size (the pressure) | **yes — 450, 65, 17, 1, 0, the same shape as their 440, 58, 10, 0, 0** |
| "nodes 53652 then 52591 four times" | **same pattern in kind, different numbers**: 69,686 at Hash 1, then 73,610 identical at 8/32/512/2048 |

**So the answer does not change and the pressure does — confirmed. The refinement is that the node count is NOT
flat across the whole range:** at Hash 1 it is 69,686 and at every larger size 73,610, a 3,924-node (5.6 %) difference
at the smallest table only. Their own "53652 then 52591 four times" has exactly the same shape — one value at the
small end, then a constant. So the honest statement is: **the search is bit-identical for every Hash size from 8 MB
up, and differs only at the minimum table size, where the move is still the same.**

That distinction matters for anyone using node counts as a reproducibility check across Hash settings: comparing
across Hash 8..2048 is safe, comparing Hash 1 against the rest is not.

## The plant (this is a negative claim, so it needs one)
A **different position** through the same harness gives a different bestmove (`g7g6` vs `c3b5`) and a different node
count. So the harness can report a change, and its "unchanged" verdicts across Hash sizes are meaningful rather than
a comparison that never fires.

## What I did NOT do
- Did not run the ASan + UBSan halves of their finding (their "18 clean searches at min/max/toggled" is a sanitizer
  claim and needs the two sanitizer proofs; I am not restating it).
- Did not test `setoption Hash` DURING a search — that is separate, and my own 08-C17 shows it stops the search.
- All Threads 1.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s17f9.py /tmp/s17.txt

Raw output committed as `check_s17f9.txt`.

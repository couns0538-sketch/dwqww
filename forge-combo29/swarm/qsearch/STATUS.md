# STATUS — swarm/qsearch

**Topic:** quiescence search (termination, stand-pat, check evasions, TT interaction, 50-move rule).
**Audit base:** `6b98f217`. **Build:** g++ 13, `FORGE_MARCH=x86-64-v4`, Release.
**Gate:** all four pins matched — bench 11 = 312,866; bench 13 = 862,329; bench 16 = 3,024,920;
perft 5 = 4,865,609. The same four pins are bit-identical on the repair build.

## State

| property | verdict | evidence |
|---|---|---|
| 1 Termination | SOUND (bounded by the 128-ply cap, which is load-bearing) | `evidence/term3.txt`, `evidence/plycap.txt`, `evidence/nest.txt` |
| 2 Stand-pat / mate / stalemate | SOUND | `evidence/matrix2.txt` |
| 3 Check evasions | SOUND | `evidence/matrix2.txt` |
| 4 TT interaction | **DEFECT** — a depth-0 qsearch store discards a deep entry's depth | `scripts/ttstore.cpp` |
| 5 50-move in qsearch | **DEFECT, two cells** — leaf band (mate → `cp 0`) and a false draw where no mate exists | `evidence/claim_model.txt`, `evidence/band_repair.txt` |

## The two property-5 cells, against an independent FIDE claim model

| position | H | base | repair | model |
|---|---|---|---|---|
| mate available, no pawn resets | 99 | **`cp 0`**, 36 nodes | **mate −1**, 63 | mate |
| no mate, pawn resets available | 97 | **`cp 0`**, 1,061 nodes | **−525**, 86,268 | **−620** |
| genuine draw | 98 / 99 / 100 | `cp 0` | `cp 0` | 0 |

Both wrong cells are on the base; both are right after the repair; genuine draws are untouched.
The H=97 repair costs **81× the nodes** — correct, but not free, and stated as such.

## Shipped in this branch

- `FINDINGS.md` — verdicts, reproductions, controls, and the explicit "not tested" list.
- `scripts/` — every probe, plus the planted-fault mutant that proves it can fail.
- `evidence/` — raw captured runs (text only, no binaries).
- A **repair** demonstrated in FINDINGS §5: closes both cells, **zero pin cost**, 0 of 90 low-clock
  cells changed. **The patch itself is not committed** — see below.

## Not shipped on purpose

- **The property-5 repair is a finding, not a patch.** It is described and measured in FINDINGS §5b but
  the source change is not in this branch. It touches `Worker::is_draw`, which is shared by the main
  search and by the documented drawn-root work (§2 of the existing report), so it needs the owner's
  decision and the full 14-cell sweep rather than a one-seat patch. FINDINGS has the ~20 lines.
- **The TT store guard (property 4)** is likewise a design change with unmeasured strength impact. Not
  patched.

## Untested (stated, not hidden)

- A qsearch run driven to the 128-ply cap by alternating checks — nesting measured at 4, not near 128.
  The no-cap mutant SIGSEGVs, so the cap matters, but I did not find an in-cap depth-128 exploit.
- Full-game cost of the depth-0 TT store (I measured qsearch nodes on 5 positions only).
- Repetition detection *inside* qsearch (my probes disable it by setting the root history index).
- `SoundMatePruning` / `go mate N` interaction with qsearch.
- The full 14-cell band sweep — I verified 2 defective cells plus controls, not all 14.

## Reproducing

```
scripts/build2.sh <src-tree> <output-binary>   # builds the qsearch probe against a source tree
scripts/classify.cpp                           # independent FEN/movegen validator (cross-checked vs perft 1)
scripts/mateoracle.cpp                         # perft-pinned movegen + independent minimax mate oracle
scripts/claim_model.cpp                        # independent FIDE 9.3 claim model (planted-fault validated)
scripts/term3.py                               # property 1, deadline-bounded
scripts/matrix2.py                             # properties 2/3 with mutant controls
scripts/ttstore.cpp                            # property 4 reproduction
scripts/band2.py                               # property 5 clock sweep through the real engine
scripts/pins.py                                # the four pins, for any build
```

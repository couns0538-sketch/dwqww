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

## Property 5 — the two cells, and what changed in this revision

All at `go depth 20` unless noted.

| position | H | base | repair | status |
|---|---|---|---|---|
| B mate available, no pawn resets | 99 | `cp 0`, 48 | `mate -1`, 83 | **base wrong; repair fixes** |
| A no mate, same claim window as its H=96 neighbour | 96 | `-630`, 3,402,177 | `-630`, 3,402,177 | agree |
| **A** | **97** | **`cp 0`, 2,672** | **`-649`, 5,243,161** | **1,273x node cliff + 630 cp jump; repair removes it** |
| A | 98 | `cp 0`, 1,079 | `cp 0`, 1,079 | untouched |

**Revised after review, and the review went two rounds.** The coordinator first challenged the direction
of cell A/97, then reversed and told me not to withdraw it. **Both of us were working from a `-620` that
does not survive a depth sweep**, so the reversal did not settle anything: their argument and mine shared
the same defective leaf value. What is left is a narrower finding that needs no evaluation at all. See
FINDINGS §5c.

- **Withdrawn:** the value "about -620". It came from a depth-4 material-only minimax that oscillates
  -520/-620 with depth parity on two independent movegens — and those two movegens share the same
  material leaf, so their agreement was not a second opinion.
- **Withdrawn:** "White forces a clock-resetting capture." I could not find one. The line offered to me
  (`g8f8 a1a7 f8e8 a7f7`) is legal but ends in **rook-for-pawn** (`+100 - 500`), a capture White would
  not play.
- **Kept, narrower than I first stated:** H=96 and H=97 have the **same claim window** (4 plies, 2 White
  moves), and across that one clock unit the base flips from a searched `-630` to a searched `cp 0` while
  its node count collapses **1,273x** (3,402,177 -> 2,672). `seldepth 20` at H=97 shows the draw was
  searched, not a root bail.
- **Also withdrawn:** "a correct search must return the same verdict for both clocks." It must not — H=94
  and H=95 share a 6-ply window and legitimately differ (-631 vs -638). The defensible claim is that a
  *qualitative* decisive-to-draw flip across the pair needs a mechanism, and the base shows none.

**The predicate is written out in §5c**, with one bug of my own disclosed: my model tested `depth<=0`
before honouring the claim, so a clock>=100 node at the horizon returned material rather than
`max(0, material)`.

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
scripts/window_count.py                        # property 5b, model-free claim-window count
scripts/pychess_claim_model.py                 # python-chess claim model (second movegen)
```

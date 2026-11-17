# Pruning paths and forced mates — does any of them lose a mate?

**Answer: the null-move, razor, RFP, move-loop, LMR and singular paths on the
default engine were NOT shown to lose or mis-distance a forced mate anywhere on
my corpus.** Every wrong answer the default engine gave was fixed by *more
depth* on the same engine — so those are horizon limits, not pruning bugs.

**But `SoundMatePruning=true` — the option whose whole purpose is mate safety —
makes the engine materially worse, and loses five forced mates the default
finds.** That is the finding. It reproduces on the pristine `6b98f217` build.

| | |
|---|---|
| Base | `6b98f217` (four pins verified: 312,866 / 862,329 / 3,024,920 / 4,865,609) |
| Build | `g++ -O3 -march=x86-64-v4 -DFORGE_MARCH=x86-64-v4`, `LIBRARY_PATH=…/gcc/13` |
| Settings | `Threads 1`, `Hash 64`, `OwnBook false`, `go depth N` |
| Corpus | 30 fixtures, mates in 1/2/3 moves (10 each), every distance verified by 3 independent solvers |
| Cells measured | 30 fixtures × depths {8,10,12} = 90, plus a 240-row depth sweep {1,2,3,4,6,8,10,12} |

---

## 1. The finding: `SoundMatePruning=true` loses forced mates

90 cells, depths 8/10/12. Compared against the default engine and against the
oracle's exact distance.

| arm | wrong cells | changed verdict | helped | **harmed** |
|---|---|---|---|---|
| default | 6 | — | — | — |
| `SoundMatePruning=true` | **7** | 9 | 4 | **5** |

The five harms are cells where **the default engine is RIGHT and the option
makes it wrong**. All five were brute-force verified (explicit minimax, third
implementation) and all five reproduce on the pristine build.

| fixture | true | default | `SoundMatePruning=true` |
|---|---|---|---|
| `8/8/8/8/8/7Q/k7/2K5 w` | m2 | `h3e3` **m2** | `h3h8` cp 1230 |
| `8/8/8/3K4/k7/8/4Q3/8 w` | m3 | `d5c4` **m3** | `e2a2` cp 1239 |
| `7Q/8/1R6/8/8/7K/8/5k2 w` | m3 | `b6b2` **m3** | `h8f8` cp 1689 |
| `8/8/8/8/8/8/6KQ/4k3 w` | m3 | `g2f3` **m3** | `g2h1` cp 978 |
| `5k2/8/8/4K3/8/4R3/8/8 w` | m3 | `e5f6` **m3** | `e5d5` cp 447 |

### Minimal reproduction

Two of these have a **unique** mating move, which makes them the cleanest
statement of the defect — the engine does not merely pick a slower mate, it
stops finding the only mate:

```
position fen 8/8/8/8/8/8/6KQ/4k3 w - - 0 1
setoption name SoundMatePruning value false
go depth 8        ->  bestmove g2f3   score mate 3   (correct; g2f3 is the ONLY mating move)
setoption name SoundMatePruning value true
go depth 8        ->  bestmove g2h1   score cp 978   (mate lost)
```

```
position fen 5k2/8/8/4K3/8/4R3/8/8 w - - 0 1
setoption name SoundMatePruning value false
go depth 8        ->  bestmove e5f6   score mate 3   (correct; e5f6 is the ONLY mating move)
setoption name SoundMatePruning value true
go depth 8        ->  bestmove e5d5   score cp 447   (mate lost)
```

Both at `Threads 1`, `Hash 64`. Verified on `build/clean/forge` (unmodified
`6b98f217` source), so this is not my instrumentation.

### Why it makes sense, from the source

`SoundMatePruning` **skips the whole shallow move-loop pruning block** in three
cases: PV nodes, in-check nodes, and nodes whose `alpha` is already a mate
score (`search.cpp`, `sound_mate_case`). Skipping pruning means **searching
more moves at those nodes**, which changes move ordering, history tables and
TT contents for every subsequent node. It is a large behavioural change, not a
local guard — and it is not mate-aware in the way its name suggests: it does
nothing about null move, razoring, RFP or LMR, which are separate predicates.

So the option trades a mate-safety guard for a global perturbation of the
search, and on this corpus the perturbation costs more than the guard buys.
**Recommendation: do not ship `SoundMatePruning` on.** It is off by default,
which is the right default.

`MateAlphaGuard` is **absent from the base build** (`uci` does not advertise it;
measured, not remembered) — consistent with §2's recorded
`-DFORGE_MATE_ALPHA_GUARD=1` trap: the flag alone is byte-identical to a control.
Where it does compile, it is a strict subset of `SoundMatePruning`'s
mate-alpha arm and only touches the two futility predicates.

---

## 2. The negative: the default pruning paths did not lose a mate

The kill condition the brief names is a corpus that never reaches the pruning
paths. **It is met** — every class fired, with counts, inside mate positions:

| feature | cells where it FIRED | answer survived | answer wrong |
|---|---|---|---|
| null move | 12 | 8 | 4 |
| razor | 30 | 27 | 3 |
| reverse futility | 60 | 54 | 6 |
| futility (quiet) | 44 | 39 | 5 |
| futility (capture) | **0** | — | — |
| LMP | 57 | 51 | 6 |
| SEE (quiet) | 24 | 18 | 6 |
| SEE (noisy) | 57 | 51 | 6 |
| history prune | 1 | 1 | 0 |
| LMR | 90 | 84 | 6 |
| singular | 29 | 23 | 6 |
| node with mate alpha | 40 | 36 | 4 |

(Cells are 30 fixtures × 3 depths = 90; a cell counts as "fired" if the counter
is non-zero. `evidence/matrix.md`, `evidence/matrix.json`.)

**And the "wrong" columns are not attributable to pruning.** Every distinct
wrong (fixture, depth) pair was re-searched deeper on the *same unablated*
engine:

| fixture | wrong at | fixed by depth |
|---|---|---|
| `8/7k/8/5K2/8/4R3/8/8 w` | 8, 10 | **11** |
| `8/8/8/8/8/K7/3R4/1k6 w` | 8 | **9** |
| `3KR3/5R2/8/k7/8/8/8/8 w` | 8, 10, 12 | **15** |

All six distinct cells are fixed by more search on the unmodified engine. **A
row that a deeper search fixes is a horizon, not a pruning bug**, and I record
them as depth limits.

### Ablation agrees, and the control that made me distrust it

Ablating LMR/singular did "fix" these rows (`evidence/ablation*.json`). **That
attribution is withdrawn as evidence of a pruning bug**, because the ablation
control showed the fix is *effort*: `ablate lmr` on
`8/8/8/8/8/K7/3R4/1k6 w` at depth 8 reaches the right mate with **1,304 nodes**
where the default needs 3,184 and *fails*; but the default engine reaches the
same right answer at depth 14 with 7,873 nodes. The ablation changed the shape
of the tree, not a correctness rule. This is exactly the trap of reading an
ablation as a cause.

---

## 3. Test 1 — null move in zugzwang-adjacent positions

Five fixtures with the *losing* side to move in a quiet position (the shape
null move is classically unsound in). Truth from the oracle, cross-checked by
brute force. `evidence/zugzwang.json`.

- **Null move fired** in 4 of 25 cells (depths 4–12 × 5 fixtures).
- **No cell changed its mate verdict** when null move was ablated — the two
  cells where the *move* changed (`6k1/5ppp/…` depths 8 and 10) were already
  non-mate scores in both arms.
- Only **1 of 5** fixtures truly had every legal move losing; the others had a
  drawing or longer-defence move, which is why they are labelled
  zugzwang-*adjacent*.

**This is a negative with a caveat, and the caveat is the interesting part:**
the engine gates null move on `has_non_pawn_material(side_to_move)` and on
`depth >= 3`, so a bare-king zugzwang — the textbook case — cannot reach the
path at all. That is a *protection*, and it means this corpus bounds the risk
in the bare-king case only. **I did not construct a zugzwang where the side to
move has non-pawn material and every move loses**, which is the case that would
actually test the classical failure. Left untested; see §6.

---

## 4. Test 2 — singular extensions and wrong mate distance

The "right move, wrong distance" class §4 documents does appear on this corpus,
but **not attributable to singular extensions**:

- 15 of 240 depth-sweep rows had the right move with the wrong mate number.
- All sit at depth ≤ 6 (`evidence/mate_safety_rows.json`).
- At the depths where singular extensions actually fire (≥ 7), the surviving
  distance errors are the three fixtures in §2, all fixed by more depth.

Notably `8/7k/8/5K2/8/4R3/8/8 w` reports **m4 where the truth is m3** at depths
6–10 and corrects to m3 at depth 11 — the same shape as the aspiration defect
already in the report (`AspCappedReopen` giving M7 where default finds M4). It
is a *second instance of that shape* at a fixed depth, and worth saying so, but
it is a horizon effect: the engine's PV is a legal 4-move mate, so it is finding
a mate, just not the shortest.

---

## 5. Test 3/4 — reverse futility and razor inside mate-in-2/3, and LMR at the root

- **Razor and RFP fire inside mate positions** (30 and 60 cells respectively)
  and in **no cell** did ablating them change a correct answer into an incorrect
  one or vice versa, once the depth control is applied.
- **LMR fires in all 90 cells.** Ablating it changes the move in many rows, and
  the changes are all "more search reaches the same answer", per §2's control.
- The root is never reduced: the LMR predicate requires
  `move_count > 1 + (root_node ? 1 : 0)`, so the first root move is never
  reduced. **No LMR-at-the-root-of-a-forced-sequence case exists** — that part
  of the brief's question is answered structurally, and it is a negative.

---

## 6. What is NOT established (read this before quoting any clean result)

1. **`go mate N` disables every pruning gate.** `mate_moves_` is set from
   `limits.mate_moves`, and every pruning predicate in `search()` is guarded on
   `mate_moves_ == 0`. Measuring mate safety with `go mate` would switch off the
   exact paths under audit and guarantee a clean null. **Every number here is
   `go depth N`.** This is the single most important methodological note in this
   report.
2. **The corpus is synthetic endgames** (KQ/KR/KRR/KQR vs bare king, biased to
   edges and corners). It is not a corpus of tournament mating attacks. Mating
   nets in a crowded middlegame reach different pruning paths.
3. **Distances are ≤ 3 moves.** Longer mates are searched deeper (up to 12), but
   a genuine mate-in-6 that the search must *discover* rather than *confirm* is
   not represented.
4. **The non-pawn-material zugzwang is untested**, per §3.
5. **No strength claim.** Nothing here says the default pruning set is good or
   bad for playing strength; only that it did not lose a mate on this corpus.
6. **`futility(capture)` never fired** in any cell, so its row is NOT REACHED,
   not "safe". Same for `hist_prune` at 1 cell — too few to say anything.

---

## 7. Harness defects I hit (so the next seat does not)

Three of my own bugs, each of which produced a plausible wrong result first:

1. **`ucinewgame` resets the board to startpos.** Four different FENs all
   returned 13,102 nodes because `position fen` was sent *before* `ucinewgame`.
   Caught only because distinct fixtures must give distinct node counts — now an
   assertion in `check_instruments_live.py`.
2. **Option state leaked between arms.** `SoundMatePruning=true` persisted into
   the next row's "default" arm and made the probe build look like it disagreed
   with the clean build on 9 of 90 rows. A direct A/B of the two binaries proved
   them identical. Every option is now reset at the top of each cell.
3. **The oracle recursed past `plies < 1`** and produced a `RecursionError` on a
   mate in one instead of an answer.

The probe is passive: **all four pins match in the base, clean and probe builds**
(`check_probe_identity.py`), and every counter and every ablation switch was
proved live on a planted fault (`check_instruments_live.py`).

---

## Reproducing

```bash
cd forge-combo29/swarm/pruning
bash scripts/build.sh all                  # clean + probe builds
python3 scripts/check_probe_identity.py    # pins must match in all three arms
python3 scripts/check_instruments_live.py  # counters and ablations must fire
python3 scripts/selftest_oracle.py         # oracle vs known answers + planted faults
python3 scripts/build_mate_corpus.py       # ~20 s, 30 verified fixtures
python3 scripts/verify_corpus.py           # python-chess AND engine acceptance
python3 scripts/mate_safety.py             # 240-row depth sweep
python3 scripts/options_test.py            # SoundMatePruning / MateAlphaGuard
python3 scripts/zugzwang_test.py           # null move in zugzwang-adjacent positions
python3 scripts/matrix.py 8,10,12          # the feature x fixture table
python3 scripts/ablate.py                  # per-class attribution
```

# Quiescence search audit — forge-combo29 @ 6b98f217

**Build:** `-DCMAKE_CXX_COMPILER=/usr/bin/g++`, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`,
`-DFORGE_MARCH=x86-64-v4`, Release. `bench N` sent on stdin.

**Gate — all four pins matched before any number below was recorded:**

| pin | expected | measured |
|---|---|---|
| `bench 11` | 312,866 | **312,866** |
| `bench 13` | 862,329 | **862,329** |
| `bench 16` | 3,024,920 | **3,024,920** |
| `go perft 5` | 4,865,609 | **4,865,609** |

The same four pins are **bit-identical on the repair build** (below), so the repair is pin-neutral.

---

## Verdict, one line each

| # | Property | Verdict |
|---|---|---|
| 1 | Termination | **SOUND.** No hang in 40 deadline-bounded probes. Bounded only by the `ply >= MaxPly` clamp at 128 — see the structural note, it is the *whole* bound. |
| 2 | Stand-pat correctness | **SOUND.** Checkmate returns `-32000`, stalemate returns `0`, at clocks 0/99/100. |
| 3 | Check evasions | **SOUND.** In-check nodes generate evasions, never stand pat, including when every legal move is a non-capture. |
| 4 | TT interaction | **DEFECT (minor, real).** A depth-0 qsearch store **overwrites a deep main-search entry** and discards its depth. Bound-type checking itself is correct. |
| 5 | 50-move inside qsearch | **DEFECT (real, measured, two cells).** The `H > 100 − p` leaf band is reachable **through qsearch**, and so is a **false draw in a non-mate position**. A repair closes both at zero pin cost. |

Two defects. Neither is a crash. One is a small search-efficiency loss; one produces a **wrong score at
two clock values**, one of them in a position with no mate at all. **Property 5's defect is the one worth
acting on.**

---

## 1. Termination — SOUND, but read the structural note

40 probes, each under a hard `SIGKILL` at 45 s: eight capture-rich boards × start plies 0/100/124/125/127.
**Zero hangs.** Every run returned in ~0.02 s.

The reason is a single line, and it matters that it is *only* this line:

```
if (ply >= MaxPly) return board.in_check() ? 0 : rule50_damped_static(...);
```

**qsearch at an in-check node generates ALL evasions, quiet ones included** (`MovePicker` stage
`EvasionGenerate` → `generate_pseudo_legal(buffer_, false)`). So an evasion that gives check puts the
child in check too, and qsearch recurses on **non-captures**. That is not a capture-only quiescence
search, and it means the recursion has **no natural length bound**.

Measured, this is not hypothetical: `maxchkdepth` — the deepest nesting of in-check qsearch nodes —
reaches **3** on kiwipete and **4** on `r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1`.
So the recursion is real, just shallow in practice.

**Proof the ply cap is load-bearing, not decorative.** The `m3_no_plycap` mutant (same source, the
`ply >= MaxPly` return removed) **SIGSEGVs** at start ply 125 on all three boards tested, and on
`queen_swap` at ply 127 it returns a score of **−19046** at `maxply 130` — past the 128-entry stack
frame range. That is the crash the cap prevents. Full table in `evidence/plycap.txt`.

**Honest limit:** I did not find a position that makes qsearch recurse deeply *within* the 128-ply cap.
The nesting I measured tops out at 4. I am reporting "bounded by the cap and observed shallow", not
"there is a depth-128 exploit".

## 2. Stand-pat correctness — SOUND

Both classic bugs are absent. Verified with an independent classifier that agrees with the engine's
`perft 1` on every fixture used (`scripts/classify.cpp`, cross-checked against `go perft 1`).

| fixture | `is_draw` says | qsearch returns |
|---|---|---|
| `7k/6Q1/6K1/8/8/8/8/8 b - - 0 1` (checkmate) | mate | **−32000** |
| same at clock **99** | mate | **−32000** |
| same at clock **100** | mate | **−32000** |
| `7k/8/6QK/8/8/8/8/8 b - - 0 1` (stalemate) | 0 | **0** |
| same at clock 99 / 100 | 0 | **0** |

**The check can fail — proven.** The `m1c_standpat_classic` mutant (only captures searched, so an
in-check node with no captures stands pat) returns **−496** on the checkmate board and **−700**, **−782**,
**−809** on three in-check mate fixtures, where base returns a mate or searches properly. So the check
is live and would have caught the classic bug.

Note the ordering that makes this work: `is_draw` is tested **before** the TT probe, before stand pat,
and before any pruning, and it keeps stalemate alive via `!board.in_check() && !board.has_legal_move()`.
The code comment at `search.cpp:1306` says this was deliberate. It is.

## 3. Check evasions in qsearch — SOUND

The condition from the assignment — *in check, and the only legal moves are non-captures* — was
constructed and validated, not assumed:

| fixture | legal moves | captures |
|---|---|---|
| `1r4k1/8/8/8/8/8/8/1K6 w - - 0 1` | 4 | **0** |
| `7k/5K2/8/4Q3/8/8/8/8 b - - 0 1` (mated in 2) | 1 | **0** |
| `5K1k/8/8/4Q3/8/8/8/8 b - - 0 1` (mated in 2) | 1 | **0** |
| `2Q4k/8/5K2/8/8/8/8/8 b - - 0 1` (mated in 4) | 1 | **0** |

On all four, base qsearch **expands 4/2/2/2 nodes** and returns a searched score, never a stand-pat
material score. The mate-distance scores are qsearch's normal horizon (it is not a mate solver), but
the node counts prove the evasions were generated and searched.

**The check can fail — proven.** The `m5_no_evasions` mutant (in-check nodes routed to the capture-only
stage) returns **−32000** — a *fabricated mate* — on `1r4k1/...` where base returns **−361**, and
**−32000** on both mated-in-2 fixtures where base searches. A qsearch that cannot generate evasions
manufactures mates in both directions, and the check catches it.

**Control that rules out the vacuous reading.** `4k3/8/8/8/8/3n4/8/4K3 w - - 0 1` also has
"in check, zero captures" — but it returns 0 in **1 node** via `is_insufficient_material`, before any
move is generated. That fixture is **vacuous** and is excluded. I found it by seeing the node count, not
by reasoning about it; an earlier version of this audit would have counted it as a pass.

## 4. TT interaction — DEFECT: a depth-0 qsearch store overwrites a deep entry

qsearch **both probes and stores** the table (`search.cpp:1438` probe, `:1541` store, and a stand-pat
lower-bound store at `:1477`). The probe honours bound type correctly — verified by planting entries:

| planted entry | window | base result | bound-ignoring mutant (`m4b`) |
|---|---|---|---|
| `+3000` `BoundLower` | (−200, −199) | **cuts**, returns 3000 | cuts |
| `−3000` `BoundUpper` | (−200, −199) | **cuts**, returns −3000 | cuts |
| `+3000` `BoundUpper` | (−200, −199) | **no cut**, returns −105 | **cuts, returns 3000** |
| `−3000` `BoundLower` | (−200, −199) | **no cut**, returns −105 | **cuts, returns −3000** |

Base refuses both invalid cuts; the mutant takes both. So the *probe* side is correct and my check
demonstrably fires.

**The defect is on the store side.** `TranspositionTable::store_body` admits with
`admit = bound == BoundExact || !same_position || depth + 4 > entry->depth || ...`
(`search.cpp:465`). A qsearch store with `bound == BoundExact` therefore **always** admits, even over a
much deeper entry, and writes `depth = 0`:

```
before: depth=24 score=250   move=d5e6 bound=Upper
after : depth=0  score=-76   move=e2a6 bound=Exact     (the qsearch store)
```

The deep entry's depth is destroyed. A subsequent search can no longer take a depth-24 cutoff for that
position, so it must re-derive the work. **Minimal reproduction:** `scripts/ttstore.cpp`, run
`./ttstore "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1" d5e6 250 24`.

**Severity: minor, and I will not overstate it.** Two bounds on the harm, both measured:

- A deep **mate** entry is *not* destroyed — qsearch reads it, returns it, and stores back the same mate
  score (base: `before depth=20 score=31990 mate=1` → `after depth=20 score=31990 mate=1`). The
  destructive case needs a deep entry whose score *differs* from qsearch's own answer.
- The node cost is small where I could measure it: suppressing all qsearch stores (`m6`) costs
  **+13.4%** qsearch nodes on kiwipete and **0%** on four other positions. Full-game cost is unmeasured.

The correct fix is a depth guard on the store (`bound == BoundExact` should not admit over a
substantially deeper same-position entry), but this is a design change and I am **not** shipping it in
this branch — it is a finding, not a patch.

## 5. The 50-move rule inside qsearch — DEFECT: the leaf band is reachable through qsearch

**The mechanism, and it is narrower than I first guessed.** A capture resets the half-move clock, so a
*qsearch capture chain cannot cross the clock boundary*. I confirmed this the hard way: my first
capture-chain fixtures all reported `max_clock == root clock`. The only way a qsearch node reaches
clock 100 is a **quiet evasion** at clock 99 — the in-check branch from property 3. Instrumented
confirmation: on `4k3/8/8/8/8/2b5/8/1B2K3 w - - 99 60`, **4 of 4** clock-100 nodes are the
`in_check → evasion` path (`c100_outchk=4`, `c100_inchk=0`).

So property 5 and property 3 are the same code path, and the band is reachable.

**Reproduction at the qsearch level.** No search depth is involved; this is qsearch alone:

```
6k1/8/5PPP/8/8/8/8/R6K b - - 99 40      # Black to move, Black gets mated by Ra8#
  after g8f8 (clock -> 100): qsearch returns     0   1 node   clock[100..100]
  after g8h8 (clock -> 100): qsearch returns     0   1 node   clock[100..100]
  control, same children at clock 98:
  after g8f8 (clock ->  99): qsearch returns  2131   1 node   clock[99..99]
  after g8h8 (clock ->  99): qsearch returns  2089   1 node   clock[99..99]
```

The child at clock 100 has a mate in one available (`5k2/8/5PPP/8/8/8/8/R6K w - - 100 41` — my oracle
says `MATE 1`), but qsearch returns **0** before looking, because `is_draw` at clock ≥ 100 returns
"draw" for anything that is not already checkmate.

**End to end, this reproduces the documented band exactly.**

| clock | base `go depth 12` |
|---|---|
| 96 | `mate -1`, 63 nodes |
| 97 | `mate -1`, 63 nodes |
| 98 | `mate -1`, 63 nodes |
| **99** | **`cp 0`, 36 nodes** |
| 100 | `cp 0`, 0 nodes (root guard — correct, the side to move may claim) |

This is the `H > 100 − p` band with `p = 2, H = 99`, matching `docs/forge-findings.md` §2. **My
contribution is the mechanism attribution, not the band's existence**: the band is a *qsearch* property,
reached only via quiet evasions, and no depth can escape it (confirmed at depths 8/12/16 above).

### 5b. A second cell, in a position with no mate at all — this one is not in the existing report

While building the *control* for the band repair I found that the base returns a false draw in a position
where **no mate exists** and a **pawn move is available to reset the clock**. This is a different defect
from the documented band, and it is wider.

Position A: `6k1/5ppp/8/8/8/8/8/R5NK b - - H 40` — Black is down a rook, has six pawn moves and two king
moves. Any pawn move resets the half-move clock, so the fifty-move draw is **not** available on Black's
best line.

I built an independent FIDE claim model to adjudicate this (`scripts/claim_model.cpp`): exact minimax
over forge's perft-pinned movegen, material leaf eval, and at clock ≥ 100 the node value is
`max(0, continuation)` because **FIDE 9.3 makes the claim optional** and a mating move ends the game
first. Its self-validation is a planted fault: removing the claim option turns h=98/99 from `0` into
`-620`, so the model genuinely exercises the rule.

| H | model (d4) | base d12 | base nodes | repair d12 | repair nodes |
|---|---|---|---|---|---|
| 95 | −620 | −507 | 80,489 | −507 | 80,489 |
| 96 | −620 | −531 | 106,852 | −531 | 106,852 |
| **97** | **−620** | **`cp 0`** | **1,061** | **−525** | 86,268 |
| 98 | 0 | `cp 0` | 487 | 0 | 487 |
| 99 | 0 | `cp 0` | 227 | 0 | 238 |

**At H = 97 base returns a draw worth `cp 0` where the true value is about −620, in 1,061 nodes.** The
repair returns −525 in 86,268 nodes, converging on the model. At H = 98 and 99 the model itself says the
draw is real (0), and both builds agree — so the repair does not over-correct.

(At 95–96 the model is at its depth-4 resolution and does not see the same −507/−531 the engine's
depth-12 search reports; those two cells are **not** evidence of an engine defect and I am not counting
them as one.)

### The repair, and both cells it fixes

Table from `evidence/claim_model.txt`, `go depth 12` on both builds:

| position | H | base | repair | model |
|---|---|---|---|---|
| B `6k1/8/5PPP/8/8/8/8/R6K b` (mated, no pawn moves) | 96 | mate −1 | mate −1 | mate |
| B | 97 | mate −1 | mate −1 | mate |
| B | 98 | mate −1 | mate −1 | mate |
| **B** | **99** | **`cp 0`, 36** | **mate −1, 63** | **mate** |
| B | 100 | `cp 0`, 0 nodes | `cp 0`, 0 nodes | 0 |
| **A** `6k1/5ppp/...` (no mate, pawn resets available) | **97** | **`cp 0`, 1,061** | **−525, 86,268** | **−620** |
| A | 98 | `cp 0` | `cp 0` | 0 |
| A | 99 | `cp 0` | `cp 0` | 0 |

Two independent cells, both wrong on the base, both right after the repair, and the cells where the draw
is *genuine* are untouched.

**One cost to be honest about:** at A/H=97 the repair spends **86,268 nodes against 1,061** — an 81×
increase. That is the price of not taking a false draw; it is the same order as the neighbouring cells
(h=96 is 106,852 nodes), so it is a return to normal search cost rather than a new pathology. It is still
a real cost and the owner should see it.

**The repair closes it, and costs zero pins.** A clock-100 leaf is a draw only if the side to move is
not mated **and** has no immediate mating move (only checking moves can mate, so the scan is cheap):

```cpp
if (board.halfmove_clock() >= 100) {
    if (board.in_check()) return board.has_legal_move();   // mated here -> not a draw
    if (!board.has_legal_move()) return true;              // stalemate
    return !has_mating_move(board);
}
```

| clock | base | repair |
|---|---|---|
| 96 / 97 / 98 | `mate -1`, 63 | `mate -1`, 63 (unchanged) |
| **99** | **`cp 0`, 36** | **`mate -1`, 63** (fixed) |
| 100 | `cp 0`, 0 nodes | `cp 0`, 0 nodes (unchanged, correct) |

**Acceptance controls on the repair:**

- **All four pins identical** on the repair build (table at the top).
- **Clocks 0–89: 0 of 90 cells differ** — the repair touches nothing outside the band.
- **The genuine-draw cells stay draws**: A/H=98, A/H=99, B/H=100 all `cp 0` before and after, and the
  independent model agrees they should be 0. So the repair does not over-correct.
- **12-position sweep**: 10/12 byte-identical, and the 2 that differ are exactly the two band cells.
- A promotion chain (`8/1P1P1P1P/8/8/8/8/8/k1K5 w - - 0 1`) is unchanged: `mate2`, 671 nodes.

**Honest limits on the repair:**

- I verified it on **two** defective cells (B/99 and A/97) plus their neighbours and controls. I did not
  re-run the full 14-cell sweep from `docs/forge-findings.md`, so I cannot claim it fixes every cell of
  the documented band — only the cells I measured.
- The A/H=97 cell costs **81× the nodes** (1,061 → 86,268). Correct, but not free.
- The repair changes `Worker::is_draw`, which is **shared by the main search and the drawn-root work in
  §2** of the existing report. That is why it is not committed here.

---

## Reproducing this from a clean `6b98f217`

```bash
# 1. Instrument the base tree (counters only; no behaviour change, no repair).
cp -r forge-combo29 /tmp/qs && cd /tmp/qs
patch -p2 < swarm/qsearch/scripts/qsearch-instrumentation.patch

# 2. Build the qsearch probe and the independent validators.
swarm/qsearch/scripts/build2.sh /tmp/qs /tmp/qs_probe
swarm/qsearch/scripts/buildtools.sh /tmp/qs /tmp/qs_tools     # classify, mateoracle, claim_model

# 3. Re-run the properties.
/tmp/qs_probe "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1" -32001 32001   # mate -> -32000 (property 2)
/tmp/qs_probe "1r4k1/8/8/8/8/8/8/1K6 w - - 0 1" -32001 32001   # in-check evasions (property 3)
/tmp/qs_tools/claim_model "6k1/5ppp/8/8/8/8/8/R5NK b - - 97 40" 4   # -620: base says cp 0
/tmp/qs_tools/claim_model "6k1/8/5PPP/8/8/8/8/R6K b - - 99 40" 4    # mate: base says cp 0

# 4. Confirm the pins on any build.
python3 swarm/qsearch/scripts/pins.py     # edit the two binary paths inside first
```

`qs_probe2.cpp` needs `-DFORGE_QS_TRACE=1` and the instrumentation patch; it is written to compile
against an **unpatched** tree too (the counters then read as zero) so a reader is never blocked by a
missing patch, and a zero counter is visibly a zero rather than a silent pass.

## What I could not test, and why

- **A deep-nesting qsearch exploit.** Nesting tops out at 4 in the positions I tried. The 128-ply cap
  prevents the SIGSEGV that the no-cap mutant shows, but I did not search for a position that drives
  qsearch to 128 plies of alternating checks within the cap. **Untested, not passed.**
- **The full-game cost of the depth-0 store (property 4).** I measured qsearch-node cost on five
  positions and stopped. A self-play or bench-battery measurement would put a number on it; I did not.
- **Repetition detection inside qsearch.** `is_draw` calls `board.is_repetition(root_history_index_)`,
  and the root history index is set by the caller. In my probe I set it to the board's own history
  size, so repetition *inside* qsearch is effectively disabled in every probe here. Testing it needs the
  engine's real search path, not a direct qsearch call, and I did not build that harness.
- **`SoundMatePruning` / `go mate N` interaction with qsearch.** Out of scope for the five properties,
  but the `mate_moves_` branch at `search.cpp:1431` does narrow the window inside qsearch, so a mate
  audit should cover it.

## Harness defects I hit and fixed (they would each have manufactured a result)

1. **My own classifier had a `|df| = 2` pawn-capture bug and enumerated slider offsets in `[-2..2]`**,
   so no slider could move more than two files. It said kiwipete had 38 legal moves against the engine's
   48, and claimed 24 captures where there were 0. Caught by cross-checking `perft 1` against the engine.
   Both bugs also lived in my first mate oracle, which would have returned wrong mate verdicts.
2. **My "in check, no captures" fixture `4k3/8/8/8/8/3n4/8/4K3` was vacuous** — insufficient material
   fires before any move is generated. Node count exposed it.
3. **`4k3/8/8/8/8/8/8/Q6q b - - 100 61` was refused by the engine** (no white king — a 7-field board
   that my validator accepted). The engine answered from the *previous* position, which is trap 6 in
   §7. Every FEN here is now checked for exactly one king per side.
4. **Setting an arbitrary `--ply` while leaving `stack_[i].ply` at `i-4` SIGSEGVs** — my harness broke
   the engine's `index == ply + 4` invariant and produced three fake `rc=-11` rows before I found it.
5. **A first "repair" that did not apply** (string anchor mismatch) produced a clean-looking
   "base and repair are identical" table. That is a **false null** — identical numbers from a patch
   that never landed. The patch is now checked by grepping for its own symbol before the build.
6. **A single-window probe convention `qsearch(lo-32000, lo+32000)` was not a full window**, and a
   "64,001-node" result turned out to be my harness sweeping 64,001 window points.
7. **My first three claim models were wrong in three different ways** and each produced a confident
   verdict before I caught it: v1 returned 0 for the checkmate fixture (it treated "not mated at clock
   100" as 0 and never let the winner mate, which contradicts the claim being *optional*); v2 segfaulted
   because at clock ≥ 100 it recursed without decrementing depth; v3 hit its node cap on every input
   because the claimable branch also never decremented. The version in `scripts/claim_model.cpp` is
   bounded by depth and validated by a planted fault. **A model that reports the same number for
   everything is not a model, and two of those three looked plausible on one fixture.**
8. **I nearly reported "the repair changes nothing" from a patch that never applied** (item 5) and then
   nearly reported "the repair breaks the correct control at h=97" — when in fact base was wrong at
   h=97 and the repair was right. Both errors came from trusting an intermediate table instead of
   building an independent oracle for the cell in question.

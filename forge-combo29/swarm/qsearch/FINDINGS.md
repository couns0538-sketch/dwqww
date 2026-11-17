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
| 5 | 50-move inside qsearch | **DEFECT.** The `H > 100 − p` leaf band is reachable **through qsearch** (mechanism established). Separately, a non-mate position returns an internally inconsistent score across two clocks with an identical claim window. A repair closes both at zero pin cost. |

Two defects. Neither is a crash. One is a small search-efficiency loss; one produces a wrong score.
**Property 5's defect is the one worth acting on.**

**Read §5c before quoting §5b.** Two numbers in the first version of 5b were produced by a model that
oscillates with depth, and one mechanism reported to me (a forced clock-resetting capture) does not hold.
The conclusion survives on a different argument — a window-count that uses no evaluation at all — but the
value `-620` and the "forced reset" wording are **withdrawn**.

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

| clock | base `go depth 12` | repair `go depth 12` |
|---|---|---|
| 96 | `mate -1`, 63 nodes | `mate -1`, 63 nodes |
| 97 | `mate -1`, 63 nodes | `mate -1`, 63 nodes |
| 98 | `mate -1`, 63 nodes | `mate -1`, 63 nodes |
| **99** | **`cp 0`, 36 nodes** | **`mate -1`, 63 nodes** |
| 100 | `cp 0`, 0 nodes (root guard — correct, the side to move may claim) | same |

This is the `H > 100 − p` band with `p = 2, H = 99`, matching `docs/forge-findings.md` §2. **My
contribution is the mechanism attribution, not the band's existence**: the band is a *qsearch* property,
reached only via quiet evasions, and no depth can escape it (confirmed at depths 8/12/16 above).

### 5b. A second cell, in a position with no mate — REVISED, and the mechanism is not what I first reported

Position A: `6k1/5ppp/8/8/8/8/8/R5NK b - - H 40` (White Ra1 Ng1 Kh1, Black Kg8 Pf7 Pg7 Ph7).

I originally reported this as "base returns a false draw worth about -620 where the true value is -620",
on the strength of a depth-4 material-only minimax. **That reasoning did not survive checking, and this
section now rests on a different argument that does not use that model.** See §5c for what was withdrawn.

**What is true and checkable without any evaluation model: H=96 and H=97 have identical claim windows.**
Count the plies until the side that wants the draw (Black) can first claim, assuming Black shuffles its
king and White never captures (a capture resets the clock):

| H | plies to a Black-turn claim | White moves in that window |
|---|---|---|
| 94 | 6 | 3 |
| 95 | 6 | 3 |
| **96** | **4** | **2** |
| **97** | **4** | **2** |
| 98 | 2 | 1 |
| 99 | 2 | 1 |

H=96 and H=97 give White **exactly the same number of moves** to find a mate or a clock resetting
capture. **I first wrote that this forces an identical verdict, and that is too strong** — H=94 and H=95
share a 6-ply window and legitimately score different values (-638 at H=95 against -631 at H=94 in one run), because the
*positions* White reaches differ even when the move count matches. What the window count establishes is
narrower and still useful: the pair is **not entitled to a qualitative jump from a decisive score to a
draw**, and any such jump needs a mechanism. The base does not produce one; it produces a node-count
cliff (below).

**The base returns one of each, and the discontinuity is a node-count cliff.** `go depth 20`, both
builds — verified in one run, numbers copied from the run not from memory:

| H | base score | base nodes | repair score | repair nodes |
|---|---|---|---|---|
| 95 | -638 | 3,349,692 | -638 | 3,349,692 |
| **96** | **-630** | **3,402,177** | **-630** | **3,402,177** |
| **97** | **`cp 0`** | **2,672** | **-649** | **5,243,161** |
| 98 | `cp 0` | 1,079 | `cp 0` | 1,079 |

Between H=96 and H=97 the base drops from **3.4 M nodes to 2,672** — a **1,273x** collapse across one
clock unit — and its score jumps 630 cp toward draw. The repair keeps the node count in the same band
across the pair (3.4 M to 5.2 M) and does not jump.

**The seldepth column proves this is not a root bail.** At H=97 the base reports `seldepth 20` with 2,672
nodes: the search ran, reached depth 20, and *then* concluded draw. A drawn-root bail would report 0
nodes. So the `cp 0` is a **searched** draw, not the documented root guard — see §7 trap 2 of the parent
report, which is exactly the confusion this column rules out.

**This is the claim I stand behind, stated as narrowly as the evidence allows:** across one clock unit
the base flips from a searched -630 to a searched 0 and its node count collapses 1,273x, with no change to
the claim window or to either side's material. The repair removes the flip and keeps the cost in band.
**I do not claim to know the true value of either cell.** The coordinator's independent reversal to
"base is wrong at H=97" and their later reversal back to "5b stands" both rest on a `-620` that I have
since shown to be an artefact, so I am neither adopting their number nor defending mine.

### 5c. The claim predicate, the forced-reset line, and what was withdrawn

The coordinator asked for four things. All four are answered here. **Two of them changed my conclusion**,
so the answers come with the corrections rather than after them.

#### (1) The exact claim predicate my model uses

```cpp
static int solve(Board& b,int depth,int alpha,int beta){
  if(++g_nodes>g_cap){ g_cap_hit=true; return 0; }
  if(g_ply>kMaxPly) return b.side_to_move()==White? material(b): -material(b);
  const MoveList mv=b.legal_moves(false);
  if(mv.size()==0) return b.in_check()? -30000+(128-depth) : 0;   // mate/stalemate first
  const bool claimable = b.halfmove_clock()>=100;
  if(depth<=0) return b.side_to_move()==White? material(b) : -material(b);
  int best = claimable ? 0 : -99999;    // the claiming side may take the draw
  for(const Move m: mv){ ... }
  return best;
}
```

- **Whose turn:** the test is applied at every node, to **the side to move**. `best` is initialised to
  0 when `claimable`, so the side to move may take the draw instead of playing on.
- **What clock it reads:** `b.halfmove_clock()`, the clock at that node, compared against 100.
- **Declined claim at 100, re-offered at 101:** yes — the test is re-evaluated at every node, so a claim
  declined at clock 100 is available again at 101 and at every later node. That part is correct.

**But the ordering is wrong, and it is a bug I introduced.** `if(depth<=0) return material` fires
*before* the claim is honoured, so a clock ≥ 100 node reached exactly at the horizon returns **material**
instead of `max(0, material)`. That is a hole in the model, and it is one of the two reasons the numbers
in the original 5b were not trustworthy. The corrected ordering moves the claim test above the depth
cutoff; with it, H=98 becomes a stable 0 at every depth while H=96/97 stay identical to each other.

#### (2) The forced reset — and this is where my original 5b was wrong

I could not produce a forced reset for White at H=97, and I am not going to assert one.

What I checked, exhaustively over the relevant window with **legal moves only**:

- White has **no forced mate** from H=97: `mateoracle` reports `NOMATE` at limits 6, 8 and 10.
- White has **no winning capture** on any Black-king-shuffle line at H=96, H=97 or H=98. The only
  captures the rook can reach on the 7th rank are `Rxf7`, and after every legal Black king move the king
  **recaptures**: net for White is `+100 − 500 = −400`, a rook for a pawn. A losing capture is not a
  resource White would use, so it does not deny Black's claim.
- Black has **six pawn moves that reset the clock themselves**, so Black is never forced to let the
  clock run against its will.

**The coordinator's cited line `g8f8 a1a7 f8e8 a7f7` does end in that losing capture.** The line is
legal and it does reset the clock to 0, but it concedes a rook for a pawn, and the resulting position
(K+N versus K+2P) is only about +0.69 for White — it is not the win the line was offered as evidence for.
So the *specific* forced-reset mechanism reported to me does not hold.

#### (3) The independent check on one cell

Three routes, and they do not all agree, which is the point:

| route | H=96 | H=97 | H=98 |
|---|---|---|---|
| my C++ claim model, depth 4 | −620 | −620 | 0 |
| python-chess minimax, same predicate, depth 4 | −620 | −620 | 0 |
| **my C++ model, depths 2..8** | **−520/−620 alternating** | **−520/−620 alternating** | **0 at every depth** |
| base engine, depth 20 | −630 | `cp 0` | `cp 0` |
| repair engine, depth 20 | −630 | −649 | `cp 0` |

The two models agreeing at depth 4 is **not** two independent confirmations — they are the same
algorithm with the same material leaf, and both oscillate identically when depth is varied. That
agreement is an artefact. **The independent evidence that actually survives is the window-count
argument in §5b**, which uses no evaluation at all.

#### (4) What I withdraw

- **Withdrawn: "the true value at H=97 is about −620."** It came from a depth-4 material-only leaf that
  alternates −520/−620 by depth parity on two different movegens. Not established.
- **Withdrawn: "White forces a capture that resets the clock."** I could not find such a capture, and the
  one line offered to me ends in a rook-for-pawn loss. At H=96/97 Black's pawn moves reset the clock
  whenever Black wants, and Black's king shuffles toward a claim.
- **Withdrawn: "H=96 is roughly right and only H=97 is wrong."** I no longer know which of the pair is
  wrong, and I am not asserting either. What is defensible is that the *transition* between them is
  anomalous and the repair removes it.

**Kept, on the window-count argument:** the base's H=96 / H=97 pair is internally inconsistent, and the
repair makes it consistent. That is a real defect and it is exactly one cell wide on this fixture.

### The repair, and the cells it fixes

The authoritative base-versus-repair numbers for this section are the depth-20 table in §5b for
position A and the depth-12 table in §5 for position B. **I am not repeating them here**, because an
earlier revision of this file carried the same cells at depth 12, 16 and 20 with different values in
three places, and a reader had no way to tell which one an argument was resting on. If a number in this
report is quoted, quote it from §5 (position B) or §5b (position A).

Two cells change between the builds, and they are the two this section is about:

- **B/99.** Base returns `cp 0` where the repair returns `mate -1`. The child position is a genuine mate
  in one, so base is wrong here regardless of any model — this cell needs no value judgement.
- **A/97.** Base returns `cp 0` at 2,672 nodes; the repair returns `-649` at 5,243,161. **I do not
  assert which value is correct.** The claim is that base's decisive-to-draw flip across H=96/H=97 is
  unaccompanied by any mechanism, and the repair removes it.

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
- **The cells both routes call draws stay draws**: A/H=98, A/H=99, B/H=100 are all `cp 0` before and
  after. The repair does not over-correct there.
- **12-position sweep (depth 12)**: 10/12 byte-identical, and the 2 that differ are exactly the two cells
  above.
- A promotion chain (`8/1P1P1P1P/8/8/8/8/8/k1K5 w - - 0 1`) is unchanged: `mate2`, 671 nodes.

**Honest limits on the repair:**

- I verified it on **two** cells (B/99, where base is demonstrably wrong, and A/97, where base is
  internally inconsistent) plus their neighbours and controls. I did not re-run the full 14-cell sweep
  from `docs/forge-findings.md`, so I cannot claim it fixes every cell of the documented band.
- The A/H=97 cell costs **1,962x the nodes** at depth 20 (2,672 → 5,243,161). Correct, but not free.
- For A/97 I have **not** established which build is numerically right. The repair makes the pair
  consistent; consistency is not correctness.
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
9. **`python-chess`'s `push()` accepts a move that leaves the mover's king in check.** `b.push(Move.
   from_uci("f8e7"))` succeeded on `5k2/R4ppp/8/8/8/8/8/6NK b - - 99 41` even though the a7 rook attacks
   e7, and the resulting board fails `is_valid()`. Several of my probes pushed UCI moves without
   `b.is_legal()` first, so they explored **illegal positions**. I found it when a "free pawn capture"
   appeared on a square the rook was attacking. Every probe in `scripts/` now takes moves only from
   `legal_moves`. Re-running the claim question with legal moves only gave the **same verdict**, so this
   one did not change a conclusion — but it easily could have.
10. **A model that agrees with another model built the same way is not a second opinion.** My C++ claim
    model and a python-chess version agreed exactly on -620 at depth 4, and I read that as independent
    confirmation. Varying depth shows both oscillate -520/-620 by parity, identically, because they share
    the same material leaf. **The value was an artefact of the leaf, and the agreement was an artefact of
    the shared design.** The evidence that survived is the window count in §5b, which uses no evaluation
    at all.

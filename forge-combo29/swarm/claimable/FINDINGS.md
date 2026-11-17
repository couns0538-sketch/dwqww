# Seat claimable — the claimable-draw rule INSIDE the root-drawn path

Audit base `6b98f217`. Branch `swarm/claimable`. Threads 1 everywhere (no `Threads` option is
sent by any harness in this seat).

**Verdict: SHIP.** The number that decides it is the pin that did not move: **bench 11 = 312,866,
bench 13 = 862,329, bench 16 = 3,024,920, perft 5 = 4,865,609 — identical to the lock, on release
and on ASan+UBSan.** The pin cost was not "paid down", it was never in the code path this change
touches. Detail in §3.

---

## 0. The one-sentence answer

**The "claim only when no legal move resets the clock" rule can be implemented free of pin cost,
because the pin cost was never in the root path — it was in the LEAF rule, and the root path is
unreachable from every bench position.** The measured attribution: deleting nothing but the
repetition arm of `Worker::is_draw` moves bench 11 from 312,866 to **353,312** — the exact
documented number — while disabling the root adjudication entirely leaves all eleven pins
**bit-identical**.

| what was changed | bench 11 | bench 13 | bench 16 | perft 5 | source |
|---|---|---|---|---|---|
| **lock** (6b98f217) | 312,866 | 862,329 | 3,024,920 | 4,865,609 | `evidence/pins/lock_rel/` |
| composed (seat 12 + 27) | 312,866 | 862,329 | 3,024,920 | 4,865,609 | `evidence/pins/composed_rel/` |
| + general rule **layered** (rejected) | **353,312** | **979,723** | **2,893,009** | 4,865,609 | `evidence/pins/gen_rel/` |
| **root adjudication disabled** (diagnostic) | 312,866 | 862,329 | 3,024,920 | 4,865,609 | `evidence/pins/rootsrch_rel/` |
| **leaf repetition arm deleted only** (diagnostic) | **353,312** | **979,723** | **2,893,009** | 4,865,609 | `evidence/pins/repdiag/` |
| **this seat: rule inside the root path** | **312,866** | **862,329** | **3,024,920** | **4,865,609** | `evidence/pins/candA_rel/` |
| this seat, ASan+UBSan | **312,866** | **862,329** | **3,024,920** | **4,865,609** | `evidence/pins/candA_san/` |

Rows 4 and 5 are the ones that answer the question. Row 4 shows the root path cannot move a pin.
Row 5 shows the leaf repetition arm alone reproduces the exact documented triple. **The pin cost is
in the repetition half of the leaf rule, and this seat did not touch the leaf rule.**

---

## 1. What was built

`patches/claimable_in_root.patch.txt` — one hunk, 18 added lines, inside the existing
post-mate-scan root block of `Worker::search`. Applied on the composed tree it produces
`src/search.cpp` sha256 `2eaf0b5a50e009b8f5ee525624924d21078284fe085ba743de95fae34adb7ec1`.

```cpp
if (root_draw_adjudicated && (board.is_repetition() || board.halfmove_clock() >= 100)) {
    for (const Move move : legal) {
        if (move.is_capture() || piece_type(board.piece_at(move.from)) == Pawn) {
            root_draw_adjudicated = false;   // the clock can be reset: play on
            break;
        }
    }
}
```

Three properties the brief demanded, each verified rather than asserted:

- **(a) the mate-first scan is kept.** The new block sits *after* seat 12's mate scan and only runs
  when the scan did not already cancel the adjudication. Proof it still works: `X3_mate1_at_clock100`
  and `H_threefold_mate` both return `mate 1`, and `A2_two_mates_h100` still returns `mate 1`
  (§4). If the new block ran first, the mate-first arm could never be reached; the ordering is
  what makes both arms live.
- **(b) the reset test is applied only where a claim is available.** It is gated on
  `board.is_repetition() || board.halfmove_clock() >= 100`, so it never runs on a root that is
  not claimable, and it is *explicitly excluded* from the insufficient-material arm — insufficient
  material is an automatic draw, not a claim, and it can offer captures that reset the clock
  without changing the fact that nobody can mate. The instrumented counter confirms the exclusion
  (§5): K v K enters the root block with `adjudicated=1` and **never** enters the claim test.
- **(c) the leaf rule at `search.cpp:1302-1304` is untouched.** Verified by diffing the whole
  function: `Worker::is_draw` is **byte-identical** to the lock, still at line 1300. The only
  changed file in the tree is `src/search.cpp`, and the only changed hunk is the one above.

### Order of application (the `-p` trap, obeyed)

Seat 12 `02_…patch.txt` is `-p1` from the repo root; seat 27 `03_…patch.txt` is `-p1` from inside
`forge-combo29/`. Applying the composed tree this way reproduces exactly the documented
`24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`, and the mistake is loud
(`1 out of 1 hunk ignored`, exit 1) — reproduced in this seat, not taken on trust.

---

## 2. The general-rule patch does not compile — and that is a finding

`patches/01_rejected_general_rule.patch.txt` (seat 12's `claimable_draw.patch.txt`) contains

```cpp
if (!move.is_capture() && board.piece_at(move.from).type != Pawn) return false;
```

`Piece` is a plain `enum Piece : int` with no member `type`, so **the committed general-rule patch
fails to compile against the tree it targets**:

```
error: request for member 'type' in
'(& board)->forge::Board::piece_at(...)', which is of non-class type 'forge::Piece'
```

It compiles after `sed`-ing to `piece_type(board.piece_at(move.from)) != Pawn`, which is how every
layered number in this seat was produced. **Consequence: the documented "353,312 / 979,723 /
2,893,009 + three wrong answers" was measured on a hand-corrected variant, not on the committed
file.** The numbers reproduce exactly once corrected (`evidence/pins/gen_rel/`), so no conclusion in
the findings document is wrong — but the artifact was not runnable as committed, and anyone
re-running it unfixed sees a compiler error rather than a result.

---

## 3. Why the pins do not move — the mechanism, measured twice

A claim of "no pin cost" is only worth the mechanism behind it. There are two independent
measurements, and they agree.

**Measurement 1 — the root gate is unreachable from every bench position.** Instrumented build
(`evidence/instruments/bench_scan_counts.txt`) over the exact pin workload, 8 FENs × 10 bench runs =
80 root visits:

```
ROOT lines:              80     (the code was reached 80 times)
adjudicated roots:        0     (root_draw_adjudicated was true ZERO times)
claim-test entries:       0     (the new block never executed)
declines:                 0
bench pins: 312866 / 862329 / 3024920 / 12389307 / 34048354
            375354 / 907205 / 2448617 / 13573040 / 24506465
```

All eight bench FENs carry **halfmove clock 0**, and a FEN carries no repetition history, so no
bench *root* can be drawn. The 80 ROOT lines prove the counter is live and the zero is a real zero
rather than an unreached branch — the same discipline as the rising-series control in §6.

**Measurement 2 — the leaf counter-control.** The same instrumentation on drawn roots
(`evidence/instruments/drawn_root_scan_counts.txt`) fires on demand:

```
ROOT adjudicated=1 legal=20 hm=16 rep=1   CLAIMTEST enter legal=20   CLAIMTEST decline move=a2a3
ROOT adjudicated=1 legal=3  hm=100 rep=0  CLAIMTEST enter legal=3    (no decline: no reset move)
ROOT adjudicated=1 legal=5  hm=0   rep=0                             (K v K: insufficient, correctly
                                                                      excluded from the claim test)
```

So the zero in bench is "not drawn", not "not implemented", and the third line is the
insufficient-material exclusion (b) showing up as a measured fact.

**Measurement 3 — the attribution control, independent of instrumentation.** Deleting *only* the
repetition arm from the leaf `is_draw` reproduces the documented triple exactly
(`evidence/pins/repdiag/`): **353,312 / 979,723 / 2,893,009**. Neither the fifty-move arm of the
leaf rule nor the root path moves a pin on its own. This is the brief's own sentence — *"the pin
cost is in the REPETITION half, not the fifty-move half"* — converted into a build.

---

## 4. Correctness: the 7 families, the 3 broken cases, and the controls

One harness, `scripts/probe.py`, one fixture file `evidence/fixtures.json` that is **generated and
asserted by python-chess** (`scripts/build_fixtures.py`), one fresh process per search after
`ucinewgame`, every search run twice and required to agree, and a `go perft 1` identity gate on
every row so a silently refused FEN cannot produce a number.

**Result: candidate 20 / 20. Lock 12 / 20.** The lock's eight failures are the attribution
control the brief asked for — the same probes, same harness, same fixtures.

| fixture | what it is | lock | **candidate** |
|---|---|---|---|
| `A2_two_mates_h100` | 2 mates at clock 100 (63 family) | cp 0 / 0n ✗ | **mate 1 / 288n** ✓ |
| `B_single_mate_h100` | exactly 1 mate (63 family) | cp 0 / 0n ✗ | **mate 1 / 217n** ✓ |
| `C_stalemate_not_mate_h100` | stalemates only, no mate (63) | cp 0 / 0n ✓ | cp 0 / 0n ✓ |
| `D_check_not_mate_h100` | checks, no mate (63) | cp 0 / 0n ✓ | cp 0 / 0n ✓ |
| `E_mate_in_2_h100` | mate in 2, no mate in 1 (63) | cp 0 / 0n ✓ | cp 0 / 0n ✓ |
| `F_insuff_KBvK` | insufficient material (63) | cp 0 / 0n ✓ | cp 0 / 0n ✓ |
| `F2_insuff_bishops` | same-colour bishops (63) | cp 0 / 0n ✓ | cp 0 / 0n ✓ |
| `F3_KNNvK_mate` | KNN v K, corner mate (63 control) | mate 1 / 192n ✓ | mate 1 / 192n ✓ |
| `G_threefold_root` | threefold, **resets exist** | cp 0 / 0n ✗ | **cp 22 / 34,047n** ✓ |
| `H_threefold_mate` | threefold **with** a mate (63-F12) | cp 0 / 0n ✗ | **mate 1 / 266n** ✓ |
| `X1_losing_side_threefold` | losing side at threefold, **no reset** — the general rule broke this | cp 0 / 0n ✓ | **cp 0 / 0n** ✓ |
| `X2_clock100_no_reset` | clock 100, no reset anywhere — the general rule broke this | cp 0 / 0n ✓ | **cp 0 / 0n** ✓ |
| `X3_mate1_at_clock100` | correct `mate 1` the general rule turned into cp 488 | cp 0 / 0n ✗ | **mate 1 / 216n** ✓ |
| `Y1_losing_side_threefold_reset` | losing side, **reset available** | cp 0 / 0n ✗ | **cp 0 / 281n** ✓ |
| `Y2_clock100_reset_equal` | clock 100, equal, resets exist | cp 0 / 0n ✗ | **cp 17 / 50,855n** ✓ |
| `Y3_clock100_losing_reset` | clock 100, losing side, resets exist | cp 0 / 0n ✗ | **cp 0 / 205n** ✓ |
| `C1_KvK` | automatic draw control | cp 0 / 0n ✓ | cp 0 / 0n ✓ |
| `C2_winning_board` | non-drawn, must be untouched | cp 1260 / 39,665n ✓ | cp 1260 / 39,665n **identical** ✓ |
| `C3_fifty99_reset_available` | clock 99, must be untouched | cp 0 / 557n ✓ | cp 0 / 557n **identical** ✓ |
| `C4_startpos` | must be untouched | cp 30 / 56,720n ✓ | cp 30 / 56,720n **identical** ✓ |

Three rows deserve the emphasis:

- **`X1`/`X2` are the cases that must stay zero, and they are the ones the general rule broke.** The
  candidate keeps both at `cp 0` with **0 nodes** — same answer and same node count as the lock, so
  these are not "different but defensible", they are unchanged.
- **`X3` is the case where a correct `mate 1` became `cp 488`.** The candidate returns `mate 1`.
- **`C2`/`C3`/`C4` are node-for-node identical** to the lock, which is the positive control that the
  change is not loose in the tree.

### The three documented regressions, reproduced on an r15-like build

The general rule's three failures need the root guard *disarmed* to appear (that is what r15 does).
Built as root-guard-off + general rule (`evidence/probe/three_cases_five_builds.txt`):

| case | lock | composed | + general rule | **r15-like** (guard off) | **candidate** |
|---|---|---|---|---|---|
| `X1` losing side at threefold (want cp 0) | cp 0 | cp 0 | cp 0 | **cp −1,235** ✗ | **cp 0** ✓ |
| `X2` clock 100, no reset (want cp 0) | cp 0 | cp 0 | cp 0 | **cp −501** ✗ | **cp 0** ✓ |
| `X3` mate 1 at clock 100 (want mate 1) | cp 0 | mate 1 | cp 529 ✗ | **cp 529** ✗ | **mate 1** ✓ |

**All three documented failures reproduce, and the candidate is right on all three.** Two are exact
(`cp −501`, and `X3`'s `mate 1` → `cp 529`); `X1` measures **−1,235** here against the documented
**−1,237**. That 2 cp gap is stated rather than smoothed: this r15-like build is *composed + general
rule with the root guard disarmed*, not the original r15 build (base + `pc_r15.patch` +
`-DFORGE_MATE_ALPHA_GUARD=1`), which is not reconstructible from the record — the same provenance gap
the findings document records for every "PC r15" column. The sign, the magnitude and the mechanism are
identical; the last two centipawns belong to the build difference, and claiming an exact match would
be claiming a reproduction I did not perform. **What matters for the verdict is the direction: the
leaf change is what produced `−1,235`, `−501` and `cp 529`, and the candidate produces none of them.**

### A bug I made and caught — worth recording

My first probe script **hand-wrote** copies of the fixtures instead of reading the asserted file, and
silently used `h1g3 h8g6 g3h1 g6h8 h1g3 h8g6 g3h1 g6h8` for the repetition-mate board — which is
**not** a threefold in the engine's history. It reported the composed build as failing 63-F12. The
fixtures file said otherwise. This is exactly seat 63's `63-F8` ("three of my own fixtures were wrong
and were caught by assertions, not by luck") recurring in a new file: **the fix is that the harness
now reads only the asserted JSON and nothing is typed twice.** Any future seat that wants to add a
fixture must add it to `build_fixtures.py` with a `claim`, or it will not be measured.

---

## 5. Honesty pins

The brief asks for the 11 documented pins on the lock, then on the build, then diffed. All runs are
`scripts/pins.sh`: `bench` at depths 11/13/16/20/22 with `UseNNUE true` then `false`, plus
`go perft 5` from startpos, `Threads` never set.

| pin | LOCK.md | lock | **candidate (release)** | **candidate (ASan+UBSan)** |
|---|---|---|---|---|
| bench 11 net on | 312,866 | 312,866 | **312,866** | **312,866** |
| bench 13 net on | 862,329 | 862,329 | **862,329** | **862,329** |
| bench 16 net on | 3,024,920 | 3,024,920 | **3,024,920** | **3,024,920** |
| bench 20 net on | 12,389,307 | 12,389,307 | **12,389,307** | **12,389,307** |
| bench 22 net on | 34,048,354 | 34,048,354 | **34,048,354** | **34,048,354** |
| bench 11 net off | 375,354 | 375,354 | **375,354** | **375,354** |
| bench 13 net off | 907,205 | 907,205 | **907,205** | **907,205** |
| bench 16 net off | 2,448,617 | 2,448,617 | **2,448,617** | **2,448,617** |
| bench 20 net off | 13,573,040 | 13,573,040 | **13,573,040** | **13,573,040** |
| bench 22 net off | 24,506,465 | 24,506,465 | **24,506,465** | **24,506,465** |
| perft 5 startpos | 4,865,609 | 4,865,609 | **4,865,609** | **4,865,609** |

**11 of 11 bit-identical to the lock, on release and on ASan+UBSan.** Both pin runs were repeated on
a fresh process and were bit-identical to their first run (`evidence/pins/lock_rel_2/`,
`evidence/pins/candA_rel_2/`), so this is not a lucky run.

**Reproduced from the committed artifact, not from my working tree.** Applying
`patches/claimable_in_root.patch.txt` to a clean composed checkout, building it, and running the
pins gives the same eleven numbers (`evidence/pins/repro_rel/`), and that binary passes **20/20**
probes. So the thing in `patches/` is the thing that was measured.

The four "honesty pins" in the brief's sense are 312,866 / 862,329 / 3,024,920 / perft 5 = 4,865,609
— all four bit-identical on both builds, so the requirement is met with the other seven reported
alongside rather than instead.

### Sanitizer non-vacuity

A clean ASan+UBSan run proves nothing unless the binary can catch a fault. Two things are shown,
both in `evidence/sanitizer/plant_fault.txt`:

1. **The symbols are present** in the shipped sanitizer binary:
   `nm -C build-san/forge | grep -c __asan_` → **35**; `nm -D | grep -c __ubsan_` → **15**.
2. **A planted fault is caught, one per sanitizer**, at the exact statement this patch adds, in a
   scratch copy of the same tree:

```
FORGE_PLANT=asan   -> ERROR: AddressSanitizer: heap-buffer-overflow on address 0x5020000011dc
FORGE_PLANT=ubsan  -> runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
FORGE_PLANT unset  -> clean
```

Two modes rather than one because **ASan aborts on the first error**, so a single execution cannot
demonstrate both. The "unset" run is the negative control: the same instrumented binary with no plant
is clean, so the two reports cannot be an artefact of the harness itself. The first version of this
control used an offset of +2,000,000, which leaves the heap mapping and made ASan report a bare
**SEGV** rather than a classified overflow — a weaker signal that I initially mis-graded as a
failure; the offset is now +4, inside the redzone, and the check asserts the classifier name.

**20 / 20 correctness probes also pass under ASan+UBSan**, with **zero bytes on stderr**
(`evidence/sanitizer/probe_san.json`).

---

## 6. Blast radius — what else could this change?

Three sweeps, because the first two could not see the fix fire and a null from a blind sweep is not
evidence.

| sweep | positions | claimable roots | differing | verdict |
|---|---|---|---|---|
| self-play, 6 openings × 40 plies, depth 8 | 240 | **0** | **0** | inert, but **blind** |
| endgame self-play, 8 seeds × 24 plies | 145 | **0** | **0** | inert, but **blind** |
| same seeds, clock forced to 99 and 100 | 40 (20 @99, 20 @100) | **20** | **15** | the fix fires, and only here |

The first two sweeps are reported **with their blindness stated**: not one claimable root was
reached, because a self-play game ends before the fifty-move counter fills. They establish only that
the change is inert on ordinary boards; they do not establish that it is correct. That is the
"a check that declines to evaluate has not cleared anything" rule from §6 of the findings document.

The third sweep is the one that can see the fix, and it passes three machine gates
(`evidence/corpus/corpus_claimable.json`):

- **0 of 20 roots at clock 99 differ.** Below the boundary the change is invisible — the strongest
  available control that it is the *claim* being tested and not something else.
- **Both arms observed:** 14 `clock_reset` differences and 1 `mate_first` difference. A sweep that
  saw only one arm could not distinguish "the other arm is inert" from "the other arm was never
  reached".
- **0 unexplained differences.** Every difference is at clock 100, on a root with a reset move or a
  mate, and every root with **no** reset move is unchanged at `cp 0 / 0n`.

An earlier version of this sweep classified a claimable root **with a mate** as an anomaly, because
one predicate (`claimable and no mate`) was carrying two arms. That is the "one phrase doing the
work of three results" shape; the fix is the per-row `arm` field, and the two arms are now counted
separately.

---

## 7. What it is worth, and the honest limit

**What the lock does at a claimable root: returns 0 nodes, `cp 0`, and the head of the generated move
list.** The candidate searches. Measured on the 14 clock-reset roots, using the *same board one
counter-tick earlier* (clock 99, where neither build can adjudicate) as an independent reference
(`evidence/corpus/strength_cost.json`):

- lock returned an **unsearched** move in **14 of 14**;
- candidate's move equals the real clock-99 search **14 of 14**;
- lock's move equals it **3 of 14**.

**Cost, measured with a depth-14 engine oracle applied identically to both moves**
(`evidence/corpus/oracle_eval.json`), delta = candidate − lock from the root side's point of view:

| | value |
|---|---|
| cases | 14 |
| candidate better | **8** |
| equal | 3 |
| candidate **worse** | **3** |
| median delta | **+36 cp** |
| mean delta | +265 cp |
| min / max | **−290** / **+1,211** |

**So: better in 8, equal in 3, worse in 3, median +36 cp.** That is a real but modest median with a
long right tail, and the three negatives are not noise — they have one signature. All three are rows
where the candidate's chosen move **does not reset the clock and scores exactly `cp 0`**, i.e. the
search walks into a node where the **leaf** rule fires. Confirmed by attributing it directly
(`evidence/instruments/leaf_rule_attribution.txt`): relaxing **only** the leaf repetition/fifty rule,
with the candidate otherwise unchanged, turns one of those `cp 0` into **`mate 3`** and moves the
others to −129 / −336 / −359.

**This is why the brief's instruction (c) is right, and it is stated as the bound on this seat's
claim: the candidate fixes the ROOT; the one-ply-down leaf miss is still present and still costs
centipawns on some claimable roots.** Mixing the two would have made both unattributable — and the
attribution above is only possible because they were kept apart. The candidate does not claim to
make a claimable root's *score* right; it claims to stop returning an unsearched move, and that
claim holds 14 of 14.

Limits, stated rather than implied:
- the oracle is a fixed-depth engine evaluation, not a tablebase — it ranks two moves, it does not
  prove either optimal;
- the blast-radius sweep is 40 constructed roots, not a match;
- the repetition arm is covered by named fixtures (`G`, `H`, `X1`, `Y1`), not by a bulk sweep, and a
  FEN cannot carry repetition history — stated because it means the bulk sweep exercises the
  fifty-move arm only.

---

## 8. Do not ship these

| file | why |
|---|---|
| `patches/01_rejected_general_rule.patch.txt` | moves all three pins and produces `−1,235` / `−501` / `cp 529`; **also does not compile** (§2) |
| the leaf diagnostic in §0 row 5 | it is a *diagnostic* that reproduces the pin cost; kept only to prove where the cost lives |
| the leaf diagnostic in §7 | relaxing the leaf rule fixes more positions but is the separate one-ply-down defect, deliberately out of scope |

---

## 9. Files

- `patches/claimable_in_root.patch.txt` — **the change to ship**, sha256 `1ec27d96…`, `-p1` from the
  repo root on top of the composed tree; produces `search.cpp` sha256 `2eaf0b5a…`.
- `patches/02_seat12_two_doors_mate.patch.txt`, `patches/03_seat27_drawn_root_reporting.patch.txt`
  — the settled pair, carried so the tree is reproducible (they compose to `24912a43…`).
- `patches/01_rejected_general_rule.patch.txt` — the rejected layered rule, kept for provenance.
- `scripts/pins.sh` — the 11 pins.
- `scripts/build_fixtures.py` — constructs and asserts every fixture with python-chess.
- `scripts/probe.py` — the 20-probe correctness harness.
- `scripts/plant_fault.py` — sanitizer non-vacuity, two modes plus a negative control.
- `scripts/corpus_diff.py`, `corpus_endgame.py`, `corpus_claimable.py` — the blast-radius sweeps.
- `scripts/oracle_eval.py`, `strength_and_cost.py` — what the fix buys and costs.
- `evidence/` — pins, probes, corpus sweeps, sanitizer, instrumentation.

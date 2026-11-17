# The fifty-move clock inside TT entries — `score_usable` audited

**Seat:** `swarm/rule50tt` · **Base:** `6b98f217` · **Build:** g++ 13.3.0, Release,
`-DFORGE_MARCH=x86-64-v4`, `FORGE_SPD_TT_NOTLS=1` (the lock's defines).
**Pins, all four, before any number below:** bench 11 = **312,866**, bench 13 = **862,329**,
bench 16 = **3,024,920**, `go perft 5` = **4,865,609**. `scripts/pins.sh`,
`evidence/pins.txt`.

---

## The answer first

1. **All four branches are real and each was reached in a live search.** Branch counters over
   76 real searches (`go depth 12`, 11 clocks, 7 boards): exact-clock **262,431,312**,
   mate-distance refusals **680,749**, inside-horizon **142,928**, outside-horizon
   **37,050,750**. Nothing here is dead code. `evidence/branch_sweep.json`.

2. **No stale-clock entry changed a score in this seat's tests — and the guard is not why.**
   Warming the table at clock 10 and probing at clock 90 changed the score on **6 of 7**
   boards. But the **same-clock** warm control (`warmBB`: search at 90, then search at 90)
   changed it on **the same boards**, so the drift is the ordinary warm-table effect the
   report already documents (cp 274/285/293), **not clock provenance**. `score_usable`
   does its job; what moves the score is the table being warm at all.
   `evidence/stale_fresh.json`, `scripts/report_stale.py`.

3. **The mate-distance test is correct and load-bearing.** `stored 90, distance 15, current 95`
   is refused; `current 85` is accepted because 85+15 = 100 is not > 100. 43 cells checked
   against an **independently generated** expectation set: **0 mismatches**. Two of my own
   hand-written expectations were wrong and are recorded below rather than deleted.

4. **The 90 is nearly inert: 89 and 91 differ from it on 3–4 of 40 cells, all at clock 85.**
   Above 90 there are twin guards (`near50` on the cutoff, `halfmove_clock() < 90` in the
   main-search cutoff test) plus the two `+ depth < 100` conjuncts, and they dominate.
   The constant is not sitting on a sharp edge, so "why 90" has no measured answer beyond
   "any value in this neighbourhood behaves the same in the cells that matter".

5. **The drawn-root bail stores nothing — confirmed with both proofs.** Five bail cases:
   **0 stores each**. Search controls on the same boards: **12, 6,952 and 40,629 stores**,
   so the counter is proven to move. A hypothetical 0 planted at clock 100 is accepted
   **only at clock 100** (never at 99, 50 or 0), so it would poison that one board at that
   one clock — a narrower hazard than "every subsequent search".

---

## 1. The function, and its four branches

```106:118:forge-combo29/include/forge/search.hpp
    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? static_cast<int>(current_clock) : 100;
        if (rule50_clock == capped) return true;
        if (is_mate_score(score)) {
            const int distance = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
            if (static_cast<int>(current_clock) + distance > 100) return false;
        }
        const int stored_clock = rule50_clock;
        const int stored_depth = depth;
        const bool inside_horizon = stored_clock + stored_depth < 100 &&
                                    static_cast<int>(current_clock) + stored_depth < 100 &&
                                    stored_clock < 90 && capped < 90;
        return inside_horizon || stored_clock == capped;
    }
```

The key fact underneath all of it: **the position key does not contain the half-move clock**
(`Board::compute_key`, `board.cpp:1407-1415`), so two boards differing only in the clock share
one slot. This function is the only thing standing between them.

| branch | in my words | reached? |
|---|---|---|
| **A** exact-clock short circuit | If the entry was stored at the clock I am at now (both capped at 100), take it, and do not ask any further question — not even whether its mate can still land. | object level: yes · search: **262 M** verdicts |
| **B** mate too far to land | A mate score whose ply distance, added to the current clock, passes 100 cannot be delivered before the rule fires, so refuse it. | object level: yes · search: **680,749** refusals |
| **C** inside horizon | Clocks differ, both under 90, and neither the stored nor the current clock plus the stored depth reaches 100. The search that produced the score could not have been cut short by the rule, so it is sound to reuse. | object level: yes · search: **142,928** |
| **D** outside horizon | Clocks differ and the search horizon touches 100 from either end, or either clock is already ≥ 90. Refuse. | object level: yes · search: **37 M** |

**A is not merely first in the source; it pre-empts B.** An entry stored at the clock it is
read at returns `true` before the mate test runs. That ordering is `d9a8587df`
("Accept identical capped rule-50 clocks before cross-clock TT checks"), which moved the
exact-clock test above the mate test. I built the pre-`d9a8587df` ordering and diffed it
against the shipped build: **0 differences in 48 real searches** (`evidence/mate_first.json`),
and the trace shows why — **`exact_mate_far` = 0 in 76 searches**: the short circuit never
fires on a mate that cannot land. So the reordering is invisible in practice even though it
is visible at object level (2 of 43 cells). Reported, not blamed.

### The object-level harness and its controls

`scripts/tt_probe_harness.cpp` stores through the **real** `TranspositionTable::store` with a
**real** `TTProbe` handle, then probes and reads the entry back. Every one of the 43 rows
reports `landed`; **43 of 43 landed**, so no "refused" row is a silently-rejected store.
Expectations come from `scripts/make_plan.py`, an independent Python model of the documented
rule — not from the C++ and not from my arithmetic.

Two controls, both must fire: store at 95 / probe at 10 must be refused (**it is**), and
store at 10 / probe at 10 must be usable (**it is**). A comparator that never fires would
make "0 mismatches" meaningless.

## 2. Stale-clock reuse: warm at 10, probe at 90

This is the assignment's decisive experiment, and it is where I had to **withdraw** a result.

**Withdrawn.** My first threshold sweep ran every cell through one long-lived process and
reported differences at clocks 0 and 60 under variants that only change a `< 90` constant.
A threshold cannot affect clock 0 in a fresh table. `scripts/aa_control.py` showed the
shared-process design changes the score of **the same board at the same clock**
(krk_far clock 0: cp **441** warm vs cp **475** cold) and that **10 of 12** cells differ
between a warm and a cold table. Every number from that sweep is discarded.

**Design used instead:** one process per measurement, three repeats, all runs required
identical. Design: `coldA`, `coldB` (fresh process, one search), `warmAB` (one process,
search at A then at B), `warmBB` (one process, search at B twice) — the last is the control
that separates "clock provenance" from "table is warm".

| board | A→B | coldA | warm@B | **coldB** | warmBB (same-clock control) | verdict |
|---|---|---|---|---|---|---|
| kqk_b | 10→90 | cp 1064 | mate 5 `c3d2` | mate 5 `c3d2` | mate 5 `c3d2` | no change |
| krk_far | 10→90 | cp 475 | cp 371 | cp 346 | cp 337 | warm table moved it; **same-clock control moved it too** |
| krk_box | 10→90 | cp 482 | cp 313 | cp 347 | cp 345 | same |
| kp_white | 10→90 | cp 129 | cp 175 | cp 121 | cp 142 | same |
| mixed | 10→90 | cp −332 | cp −331 | cp −323 | cp −323 | warm table only |
| kqk_b_rev | 90→10 | mate 5 | cp 1023 | cp 1064 | cp 1060 | same |
| krk_rev | 90→10 | cp 346 | cp 430 | cp 475 | cp 468 | same |

**6 of 7 boards changed score between a warm and a cold search; 0 of them changed in a way
the same-clock warm control did not also change.** So the honest reading is:

> A warm table changes fixed-depth scores by up to ~110 cp here, and `score_usable` does not
> and cannot prevent that, because the change does not come from the entry's clock. It comes
> from the table being warm — exactly the effect already recorded (cp 274/285/293 on one KBN
> board). **No stale-clock reuse was demonstrated in this seat.**

That is a negative, and I want to be plain that it is a negative about *this* design: 7
boards, depth 12, one pair of clocks. It is not a proof that reuse cannot happen; it is a
measurement that at these clocks the entry is refused often enough that the score is
recomputed.

## 3. Mate distance crossing the boundary

`90 + 15 > 100` must not be usable. It is not:

| stored | probe | distance | verdict | why |
|---|---|---|---|---|
| 90 | 95 | 15 | **refused** | 95+15 = 110 > 100 |
| 90 | 91 | 15 | **refused** | 91+15 = 106 > 100 |
| 90 | 86 | 15 | **refused** | 86+15 = 101 > 100 |
| 90 | 85 | 15 | **refused** | 85+15 = **100**, not > 100, so branch B lets it through — but the horizon test refuses it because stored 90 is not < 90 |
| 80 | 90 | 15 | **refused** | 90+15 = 105 |
| 99 | 100 | 3 | **refused** | 100+3 = 103 |
| 98 | 99 | 1 | **refused** | 99+1 = 100; refused by the horizon test, not the mate test |
| 90 | 90 | 15 | **accepted** | branch A short-circuits: 90+15 = 105 > 100 and it is still taken |

The last row is the one worth reading twice: **an exactly-matching clock accepts a mate that
cannot land.** That is intended by `d9a8587df` and it is invisible in real search
(`exact_mate_far` = 0 over 76 searches, 429 million exact accepts), because the search does
not store a mate at clock *c* that needs more than 100 − *c* plies.

**Two of my own expectations were wrong and are kept in the harness with the correction
written beside them** (`scripts/tt_probe_harness.cpp`, rows `B 90->85 mate15` and
`B 99->98 mate1`). I had assumed the mate test was the deciding guard in both; in both the
horizon test refuses first. `scripts/branch_power.py` then quantified it: over 999,698 cells
the exact-clock branch decides **0.23%**, the mate test **7.23%**, the horizon test **20.29%**
— the three are heavily redundant, which is why single-cell reasoning misled me twice.

## 4. Why 90 and not 89 or 91?

I built two variants differing from the shipped one only in that constant (`< 89`, `< 91`),
fresh process per cell, two repeats, 4 boards × 10 clocks:

| variant | cells differing from shipped | where |
|---|---|---|
| `thr89` | 3 of 40 | clock 85 only |
| `thr91` | 4 of 40 | clock 85 only |
| `no_horizon` (the whole horizon clause deleted) | **18 of 40** | clocks 85–95 |

**So ±1 on the constant is nearly inert; deleting the clause is not.** Above 90 nothing
changes at all, and that is explainable rather than mysterious: at `clock >= 90` the TT
cutoff is already refused twice over — `near50` in both `qsearch` and `search`
(`search.cpp:1444`, `:1594`) and `board.halfmove_clock() < 90` in the main-search cutoff test
(`search.cpp:1640`) — and the two `stored + depth < 100` / `current + depth < 100` conjuncts
bite before the constant does. At clock 80–88 the guard does move scores, by up to
**524 cp** (kqk_a clock 80: cp 1013 shipped vs cp 489 with the guard removed).

**Verdict on the constant: 90 is inside a plateau, not on a boundary.** I could not derive
"90" from the arithmetic — a sweep of every threshold from 80 to 100 found **no** threshold
with an unsound accept, because the horizon conjuncts already keep both ends under 100.

## 5. The drawn-root bail does not store

Two proofs, per the brief's rule 2.

| case | bail? | score | nodes | `info depth` lines | **stores** |
|---|---|---|---|---|---|
| halfmove 100, KRK | **BAIL** | — | — | 0 | **0** |
| halfmove 100, KQK | **BAIL** | — | — | 0 | **0** |
| halfmove 100, KP | **BAIL** | — | — | 0 | **0** |
| insufficient material | **BAIL** | — | — | 0 | **0** |
| threefold (move list) | **BAIL** | — | — | 0 | **0** |
| control: same KRK at clock 99 | search | cp 0 | 204 | 12 | **12** |
| control: same KRK at clock 50 | search | cp 468 | 14,615 | 12 | **6,952** |
| control: start position | search | cp 30 | 56,720 | 12 | **40,629** |

The counter is proven to move on searches, so the zeros are a measurement and not a
missing hook. **Why it matters here:** a stored `BoundExact 0` with `rule50_clock = 100`
satisfies `rule50_clock == capped` at a clock-100 probe, i.e. branch A, with no mate or
horizon test in the way. `scripts/poison_probe.cpp` plants exactly that and asks:

| planted | usable @100 | @99 | @50 | @0 |
|---|---|---|---|---|
| `0 @ clock 100` (what the bail would write) | **yes** | no | no | no |
| `0 @ clock 90` | no | no | no | no |
| `120 @ clock 100` | **yes** | no | no | no |
| `mate15 @ clock 100` | **yes** | no | no | no |

and confirms `key(clock 100) == key(clock 99)`. So the poisoning would be **real but confined
to clock 100 on that board** — and it would reach only the eval channel, never a cutoff,
because every cutoff site is gated on the clock being under 90. Since the bail does not
store, the hazard is latent, not live.

---

## What I had to withdraw

- **The first threshold sweep, entirely.** Its process was shared across cells, so it was
  measuring table warmth. `aa_control.py` is the file that caught it (10 of 12 cells differ
  between a warm and a cold table for the *same* build, *same* clock).
- **Two hand-written expectations** in the object harness (90→85 mate15, 99→98 mate1). The
  code was right; my arithmetic was wrong. The rows are kept, with the correction in place.
- **A bail classifier that reported "NO BAIL REACHED".** I required `info_lines >= 1` and a
  `nodes == 0` field that is actually `None`. Five real bails were on screen while my check
  said none were. The fix is in the file with the mistake described.
- **A fixture generator that produced illegal boards** (missing king, a rook giving check to
  the idle king, wrong rank counts). Replaced with programmatic placement + `is_valid()`.

## Not established / not tested

- **Whether a stale-clock entry can change a score through the eval channel at clock ≥ 90.**
  My boards and clocks did not produce one; that is a bound on 7 boards, not on the engine.
  The place to look is the one the coordinator named: **in-check evasions near clock 99**,
  which is the only quiet path to clock 100. See the next section — the shape *is* reachable
  and I measured it; it still did not produce a stale reuse.
- **Threads > 1.** Everything here is Threads 1.
- **`go nodes` / `go movetime`.** Fixed depth only.
- **A game-play corpus.** No self-play games were generated; the boards are constructed.

---

## 6. The evasion path, and the clock-97 false draw — attributed

The coordinator flagged two things this seat had left open. Both are now measured.

### The shape is reachable (so the previous null is not a corpus limitation)

Five roots with the side to move in check, where the only evasions are quiet king moves.
Three of them put a node at **clock 100** on the principal variation, which is the condition
the band needs (`scripts/exp_evasion.py`):

| case | root clock | bestmove | resets the clock? | child clock |
|---|---|---|---|---|
| kq_check_99 | 99 | `h1g1` | no | **100** |
| kr_check_99 | 99 | `h8g7` | no | **100** |
| rook_check_99 | 99 | `g8f8` | no | **100** |
| kq_check_98 | 98 | `h1g1` | no | 99 |
| rook_check_97 | 97 | `g8f8` | no | 98 |

So the earlier negative in §2 is **not** explained by "we never reached the condition".

### Warm-then-probe on exactly those boards: still no clock-specific change

Same design as §2 (fresh process per measurement, 3 repeats, same-clock warm control),
run at clocks 98↔99 and 97↔99 on the three boards above: **every cold cell returned
`cp 0` with the same move, every warm pair returned the same, and every cell was stable
across 3 repeats.** A cp-0 position has nowhere for a stale score to show, so this is a
**weak null** and I am labelling it as one: the boards reached the shape but their scores
were degenerate. `evidence/evasion_diff.json`.

### The clock-97 false draw is the LEAF RULE, not the TT — and that settles an open question

The report lists `6k1/5ppp/8/8/8/8/8/R5NK b - - 97 40` returning `cp 0` where the truth is
−620, and says "whether that comes from the TT or from the leaf rule is not established".
Measured across clocks 94–99, depth 14, 3 repeats, **every cell stable**:

| clock | score | nodes | pv length |
|---|---|---|---|
| 94 | cp −580 | 524,162 | — |
| 95 | cp −524 | 185,994 | — |
| 96 | cp **−552** | 207,911 | 17 |
| 97 | cp **0** | 901 | 3 |
| 98 | cp 0 | 383 | 2 |
| 99 | cp 0 | 313 | 2 |

A **552 cp discontinuity between clock 96 and clock 97**, and the pv collapses from 17 plies
to 3. The discriminating control: the **`always_true` build** — `score_usable` returning
`true` unconditionally, i.e. the TT guard entirely removed — gives **cp 0 at clock 97 too**
(901 → 1,097 nodes, same move, same score). If the zero came from a reused TT entry, removing
the guard would have changed it. It does not.

**So the clock-97 zero is not a transposition-table defect at all.** It is the leaf rule:
`rule50_damped_static` scales a static eval by `(100 − clock)/100`, which is **0.03** at
clock 97, turning a large negative eval into a small one; and `is_draw` at clock ≥ 100 with a
legal move returns a draw. The boundary is at `100 − p` exactly, which is the band already
documented in §2 of the findings. Checked in python-chess: after Black's quiet `Kg8-f8`,
White has **no** move that resets the clock (`resets: NONE`), so the draw is real and the
engine is not wrong to see one — it is wrong about the *evaluation*, not about the rule.

This is a **narrowing** of the report's open question rather than a new defect: the
clock-97 anomaly is rule-50 leaf arithmetic, and anyone looking for it in the TT will not
find it there. The TT's own clock field is not implicated anywhere in this seat.

---

## Reproducing

**Read this first.** `main` does not contain `forge-combo29/` at all, and this branch is
`main` plus `swarm/rule50tt/` only (deliberately — it keeps the PR diff to 38 files instead
of 13,000). So **the scripts here cannot be run against the branch alone**: they need the
engine sources at **base commit `6b98f217`**.

```bash
git clone https://github.com/couns0538-sketch/dwqww
cd dwqww
git checkout 6b98f217                                    # the audit base, NOT main
git checkout cd4a44b65 -- forge-combo29/swarm/rule50tt    # this seat's folder
cd forge-combo29
```

Then:

```bash
swarm/rule50tt/scripts/pins.sh                      # gate: four pins, refuses to continue
python3 swarm/rule50tt/scripts/make_plan.py /tmp/plan.csv
g++ -std=c++20 -O2 -I include -DNDEBUG -DFORGE_NNUE_HIDDEN=256 \
    -DFORGE_NNUE_WEIGHTS="\"$PWD/src/nnue_weights.inc\"" -DFORGE_EXPOSE_TUNABLES=1 \
    -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 \
    -DFORGE_SPD_PREFETCH_EARLY=1 -march=x86-64-v4 \
    swarm/rule50tt/scripts/tt_probe_harness.cpp \
    src/board.cpp src/search.cpp src/eval.cpp src/nnue.cpp src/bitboard.cpp \
    src/eval_params.cpp src/book.cpp -o /tmp/ttprobe -lpthread
/tmp/ttprobe /tmp/plan.csv /tmp/out.json            # 43 cells, 2 controls
python3 swarm/rule50tt/scripts/make_variants.py     # trace + 4 fault variants
python3 swarm/rule50tt/scripts/fresh_diff.py stale  /tmp/stale.json
python3 swarm/rule50tt/scripts/report_stale.py      /tmp/stale.json
python3 swarm/rule50tt/scripts/sweep_branches_final.py
python3 swarm/rule50tt/scripts/exp_bail.py
python3 swarm/rule50tt/scripts/exp_evasion.py
python3 swarm/rule50tt/scripts/exp_evasion_diff.py
```

Variants build under `/tmp/forge-variants/`; **none are committed as binaries**. The
`FORGE_NNUE_WEIGHTS` value must reach the compiler with the quotes intact — an unquoted path
fails with `#include expects "FILENAME"`.

**Verified, not asserted:** `/tmp/ttprobe` was built from a clean clone of this branch and
reproduced `43 cells, landed 43, mismatches 0` with both controls firing, after the branch
had been collapsed to `main` + this folder.

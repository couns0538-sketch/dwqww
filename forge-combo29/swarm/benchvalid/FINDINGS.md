# Is `bench` a sound gate? — no. It is a narrow, thread-blind, book-blind, clock-blind regression counter

Base commit `6b98f217` · branch `swarm/benchvalid` · build `e06310ec…` (g++ 13.3.0,
`-DFORGE_MARCH=x86-64-v4`) · four pins **PASS 4/4** before any measurement below.

**Machine**: 4 cores, Intel Xeon (KVM), 1 hardware thread per core, 15 GB. Load was
shared with sibling audit workers for part of this run; every timing figure says so and
no conclusion here rests on a timing difference under 1.5 %.

---

## 0. The answer, in the order it matters

**The four honesty pins are a valid instrument and an invalid certificate.** They are
exactly reproducible (they moved to the digit on 5 mutants that should move them and on 0
that should not), and **not one of the report's six shipping decisions falls inside what
they measure.**

| the report's decision | can a pin see it? | how that is established |
|---|---|---|
| 1. NNUE prefetch patch — do not ship | **no** | it is a *speed* change; the report records node counts **identical**, so the pins pass it by construction |
| 2. Drawn-root bail — ship both patches | **no** | **B9**: a mutant that returns the wrong move on every drawn root leaves all four pins bit-identical |
| 3. `Threads` > 1 — keep 1 | **no** | **B5**: a mutant that builds the searcher with 2 workers leaves all four pins bit-identical |
| 4. `MultiPV` / Hash ceiling | **no** | bench reads neither (§4): the pin is 862,329 at Hash 1 through 1024 |
| 5. Malformed `go` tokens are unbounded | **no** | bench never enters the `go` branch; `parse_limits` is one of the 22 unreachable functions (§3.1) |
| 6. Re-sending `Hash` clears the table | **no** | bench drives its own `Searcher`, never the UCI one (§4) |

**Two of these are proved by a mutant that a green gate passed; the other four by
coverage or by structure.** **One caveat that goes against my own table**: decision 1 is the
one entry where blindness is *by design* rather than a defect — a node-count pin cannot see a
speed change, and that is a fair thing for a node-count pin to be. The other five are
behavioural changes the pins were supposed to be guarding and are not.

| question | answer | evidence |
|---|---|---|
| **What does bench measure?** | 8 fixed FENs, one fixed depth, **one `Searcher(16)` reused across all 8 with a full `clear()` between each**. The clear makes the positions genuinely independent — proven three ways (below), not inferred from the source line. | `bench_positions_d13.txt`, `order_independence.txt` |
| **Is a pin sensitive?** | **Yes.** 5 of 5 behavioural mutants moved it, by **2.2 % to 30.3 %** on `bench 13` (2.0 % to 30.3 % across all three bench pins); 5 of 5 source-noise mutants did not move it at all. **The gate can move.** | `sensitivity.json` |
| **How much does it cover?** | **63.0 % of lines, 59.6 % of functions** for `bench 13` (64.1 % / 61.1 % for all four pins). **22 functions are reachable by a routine client workload and unreachable by the pins.** | `coverage_*.json`, `blind_functions.json` |
| **The Hash trap** | **Confirmed, and the option is live.** Pin is `862329` at Hash 1, 16, 64, 256 and 1024 — while a real `go depth 14` moves from **109,247 to 101,640 nodes** across the same range. So `setoption` reaches the engine and `bench` does not hear it. | `hash_trap.txt` |
| **Can it see the audit's own findings?** | **No.** **6 of 9** behavioural mutants were passed by a green 4/4 gate: **`OwnBook` off, `Book Variety` 30→0, `Threads` default 1→2, `Move Overhead` 10→200 ms, the fifty-move leaf rule moved one ply, and the drawn-root last-move.** The three the pins did catch are `DrawJitter`, `EvalRule50Damp` and `QsFutilityMargin`. | `blindspots.json` |
| **A better gate** | `forge gate`: **7 checks, 2.4 s wall**, every one proven to fire on its own planted fault and on nothing else. | `gate_selfcheck.txt`, `gate_cost.txt` |

**The one-line version:** *a green pin means "the eval and search constants still
produce the same tree on 8 middlegame positions at depth 13". It does not mean the engine
still plays chess. Six of the nine behavioural changes tested here are invisible to it,
including two of the report's own shipping decisions.*

---

## 1. What bench actually measures

### 1.1 The workload

The FEN list, verbatim from `src/uci.cpp:597-605`, with each position's properties
independently checked with python-chess (`scripts/check_fens.py`):

| # | FEN | move | legal | hm clock | what it is |
|---|---|---|---|---|---|
| 0 | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1` | W | 20 | 0 | start position |
| 1 | `r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1` | W | 48 | 0 | **Kiwipete** |
| 2 | `r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10` | W | 44 | 0 | middlegame, opposite-side castling |
| 3 | `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1` | W | 14 | 0 | **rook endgame** (position 3 of the standard perft suite) |
| 4 | `r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8` | W | 37 | 0 | QGD-type middlegame |
| 5 | `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1` | W | 59 | 0 | sharp middlegame, 59 legal moves |
| 6 | `6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1` | **B** | 8 | 0 | **pure rook endgame**, Black to move |
| 7 | `r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9` | W | 38 | 0 | middlegame |

**All eight validate.** None is refused (`benchprobe.cpp` prints `REFUSED` and exits
non-zero if any is; it never did). **Seven of eight are White to move.** **All eight carry
halfmove clock 0 and a FEN carries no repetition history**, so — independently of the
findings' existing count — **no bench root can be drawn**, which is why the drawn-root
repair costs zero pins (`g2_can_move.json` re-confirms this from the other direction:
the repair leaves all four pins bit-identical).

Default depth is **13**, clamped to 1..64 (`uci.cpp:594`), and `bench N` sets it. Depth is
fixed per position — there is no clock, no node budget, and no iterative deepening to a
limit.

### 1.2 Does `clear()` make the positions independent? Yes — proven three ways

`bench_searcher.clear()` is `shared_.tt.clear()` plus `worker->clear()` for each worker
(`src/search.cpp:2679-2682`), and `Worker::clear()` zeroes every history table, both
correction families, the material/non-pawn corrections, the evaluator cache and all
`SearchStack`s (`search.cpp:1019-1031`). Reading that is not proof, so it was measured
with `orderprobe.cpp` — the same loop with the order or the clear varied:

| mode | what it does | total |
|---|---|---|
| `forward` | bench's own order, `clear()` before each | **862,329** |
| `reverse` | the same 8 FENs in reverse order, `clear()` before each | **862,329** |
| `fresh` | **a brand-new `Searcher` per position** — the strongest independence available | **862,329** |
| `noclear` | bench's order with `clear()` **removed** — the positive control | **956,783** |

**Three arms agree to the digit and the control does not.** Position-by-position, forward
and reverse produce *identical* node counts per FEN (72,062 / 209,792 / 125,478 / 51,234 /
80,137 / 64,111 / 174,097 / 85,418), which is what independence looks like. The `noclear`
arm is 10.9 % higher and changes 6 of 8 bestmoves, including one that returns **`g3g6`
scored `31997`** — a mate score leaking in from the previous position's table.

So: **the eight positions are independent, and `clear()` is the reason.** That is the
single most defensible thing about bench, and it is worth knowing because a replacement
gate built on `go depth N` **does not get this for free** (§4).

### 1.3 What a pin is, and what it is not

`bench` prints **one line** (`info string bench depth D nodes N time T nps P`) and no
per-position detail, no bestmove, no score and no pv. `benchprobe.cpp` re-runs the exact
loop and prints the per-position detail bench withholds; that file is the evidence for
everything in §1.1 and is also the tool that shows the *pin is a single number covering
eight positions* — one position changing by one node moves it exactly as much as a global
eval change does.

---

## 2. Is a pin sensitive at all? Yes, in both directions

The audit's own rule applied to its own instrument: **a gate that cannot move is not a
gate.** Ten mutants, each a source edit on a fresh copy of the base, each built with the
same recipe, each re-read against all four pins.

### 2.1 Changes that MUST move a pin — all five do

| mutant | change | bench 11 | bench 13 | bench 16 | perft 5 | moved |
|---|---|---|---|---|---|---|
| base | — | 312,866 | 862,329 | 3,024,920 | 4,865,609 | — |
| `M1_eval_pawn_psqt` | the **middlegame** half of all 64 `PawnPsqt` weights **+40** (endgame half untouched) | 306,660 | 1,003,472 | 3,386,079 | 4,865,609 | **yes** |
| `M2_lmr_quiet_base` | `LmrQuietBase` 85 → 125 | 263,851 | 881,235 | 2,758,866 | 4,865,609 | **yes** |
| `M3_rfp_margin` | `RfpMargin` 72 → 40 | 226,823 | 601,295 | 2,275,803 | 4,865,609 | **yes** |
| `M4_null_move_off` | `NullMoveMinDepth` 3 → 99 | 330,705 | 815,534 | 3,183,377 | 4,865,609 | **yes** |
| `M5_see_pawn_value` | `SeePieceValue[Pawn]` 100 → 260 | 276,397 | 901,998 | 2,947,795 | 4,865,609 | **yes** |

M1 is a **pure evaluation** change and moves `bench 13` by **+16.4 %**. M3 is the
sharpest: a 45 % cut in a futility margin moves `bench 13` by **−30.3 %**.

**The shift per mutant, so the range is auditable rather than asserted** — this is the
figure §0 quotes, and it is derived from the columns above:

| mutant | `bench 11` | `bench 13` | `bench 16` |
|---|---|---|---|
| `M1_eval_pawn_psqt` | −2.0 % | **+16.4 %** | +11.9 % |
| `M2_lmr_quiet_base` | −15.7 % | +2.2 % | −8.8 % |
| `M3_rfp_margin` | −27.5 % | **−30.3 %** | −24.8 % |
| `M4_null_move_off` | +5.7 % | −5.4 % | +5.2 % |
| `M5_see_pawn_value` | −11.7 % | +4.6 % | −2.5 % |

**Range on `bench 13`: 2.2 % to 30.3 %. Across all three bench pins: 2.0 % to 30.3 %**
(the smallest is M1 on `bench 11`, −2.0 %). **Every one of the five is a change a reviewer
would call "behavioural".**

**The smallest shift in the table is the one to be careful about.** M2's +2.2 % sits close
to this audit's ~1.5 % bias floor for timing ratios — but a *node count* has no noise floor:
T1 repeats are bit-identical here, so a 2.2 % node shift is a real difference and not a
measurement of one. That is why a node pin is a strong instrument on the axis it covers,
even though it covers few axes.

**An earlier draft of §0 said "one by 4.5 % to 64 %". That was wrong and I could not
reconstruct it** — no pair of base-to-mutant values in `sensitivity.json` gives 4.5 % or
64 % on any pin, and neither do pairwise differences between mutants on `bench 13`. The
figures are withdrawn; the range above is derived, and `verify_figures.py` now computes it
from the JSON and fails if the prose disagrees.

**perft 5 did not move for any of the five, and that is correct** — perft counts legal
move trees and none of these touches move generation. That is a useful property to have
measured rather than assumed: the pin set contains one check that is sensitive to search
and eval, and one that is sensitive only to move generation, and they do not contaminate
each other.

### 2.2 Changes that must NOT move a pin — none of the five do

| mutant | change | four pins |
|---|---|---|
| `N1_add_comment` | a 3-line comment block appended to `search.cpp` | **all bit-identical** |
| `N2_reorder_struct_members` | two independent POD members of `SearchStack` swapped | **all bit-identical** |
| `N3_rename_local` | bench's own `total_nodes` accumulator renamed | **all bit-identical** |
| `N4_dead_function` | a `[[maybe_unused]]` function appended to `eval.cpp` | **all bit-identical** |
| `N5_whitespace` | blank lines and re-spacing inside the bench branch | **all bit-identical** |

Each mutant is checked to have actually changed the source tree (a sha256 over
`src/*` + `include/forge/*` that must differ from the base; the script aborts otherwise),
so these are not vacuous controls.

**So the pin is a real measurement of the eval-and-search code and not a hash of the build.**
That is more than the audit credited it with, and it is worth stating plainly because the
rest of this document is about what it misses.

---

## 3. How much does the pin cover?

Measured with `--coverage` on an otherwise identical build (`coverage.py`, which parses
gcov's per-line output and reproduces gcov's own per-file percentages to 0.1 points —
`search.cpp` 67.8 % against gcov's 67.88 %).

| workload | lines | functions | wall |
|---|---|---|---|
| `uci` + `isready` only (floor) | 290 / 4,112 = **7.1 %** | 30 / 198 = 15.2 % | ~0 s |
| `bench 13` | 2,589 / 4,112 = **63.0 %** | 118 / 198 = 59.6 % | 0.44 s |
| all four pins | 2,636 / 4,112 = **64.1 %** | 121 / 198 = 61.1 % | ~1.9 s |
| pins + behavioural paths (§6 gate) | 2,882 / 4,112 = **70.1 %** | 140 / 198 = 70.7 % | 2.4 s |

**Coverage is not the useful number here.** 63 % of lines sounds respectable and it is
badly misleading, because the uncovered 37 % is not a random sample — it is *sorted*: every
line that only a real client reaches. `bench` reaches 63 % because the *search* is most of
the code and bench does search. It reaches none of the code that decides whether the
answer is usable.

### 3.1 The 22 functions a bench pin cannot see

`blind_functions.json`, computed against the §6 workload:

| file | count | functions |
|---|---|---|
| `book.cpp` | 4 | `polyglot_key`, `decode_move`, `Book::candidates`, `Book::probe` |
| `uci.cpp` | 8 | `apply_position`, `parse_limits` (+ its 2 lambdas), 5 option/command lambdas |
| `search.cpp` | 7 | `format_score`, `TranspositionTable::lock_stripe`, `hashfull`, `Worker::elapsed_ms`, `clock_plan_for`, `Searcher::clear_hash`, the search-dispatch lambda |
| `board.cpp` | 3 | `parse_uci`, `move_to_uci`, `perft` |

Read that list as a list of **whole subsystems**: the book is the only path that can answer
without a search; `parse_limits` is the only path that turns a clock into a search budget;
`apply_position` is the only path that turns a FEN into a board; `move_to_uci` is the only
path that turns a move into the string a GUI receives. **A bench pin cannot detect a change
in any of them.**

### 3.2 The behavioural proof, which is stronger than the coverage proof

Coverage says "these lines never ran". That is not the same as "the pins passed a change
here". Nine mutants, each a real behaviour change, each with a probe proving the change is
live:

| mutant | change | pins | behavioural probe | verdict |
|---|---|---|---|---|
| `B1_book_off` | `OwnBook` default → false | **match 4/4** | book lines 20 → 0 | **gate passed a real change** |
| `B4_book_variety0` | `Book Variety` 30 → 0 | **match 4/4** | book reply stable over 20 runs: no → yes | **gate passed a real change** |
| `B5_threads_default2` | searcher built with 2 workers | **match 4/4** | kiwipete d11: 50,541 → 111,175 nodes | **gate passed a real change** |
| `B6_move_overhead` | `Move Overhead` 10 → 200 ms | **match 4/4** | 100 ms clock: depth 6 / 2,789 nodes → depth 1 / 60 | **gate passed a real change** |
| `B8_fifty_move_leaf` | fifty-move leaf rule one ply early | **match 4/4** | clock-98 leaf: 6,064 nodes → 66 | **gate passed a real change** |
| `B9_drawn_root_move` | drawn root returns the **last** candidate move | **match 4/4** | drawn root bestmove changes | **gate passed a real change** |
| `B2_draw_jitter` | `DrawJitter` 0 → 8 | **moved** | kiwipete d11 | pin caught it |
| `B3_rule50_damp` | `EvalRule50Damp` off → on | **moved** | kiwipete d11, leaf98 | pin caught it |
| `B7_qs_futility` | `QsFutilityMargin` 160 → 4000 | **moved** | kiwipete d11 | pin caught it |

**Six of nine real behaviour changes pass a green gate.** B5 and B9 are the two that
should be uncomfortable: **B5 is `Threads`, whose wrong value the findings rank as decision
#3 in the whole report**, and **B9 is the drawn-root bail, which is decision #2.** The pin
that the audit used to certify both is silent on both.

And the reason is structural, not accidental:
- `bench` constructs `Searcher bench_searcher(16)` — a *literal* 16 MB, one worker. It never
  reads `Hash`, never reads `Threads`, never reads `MultiPV`.
- `bench` never enters the UCI `go` branch, so `parse_limits`, the book probe and the
  `game_search` gate are unreachable.
- All eight bench FENs carry halfmove clock 0 with no repetition history, so the drawn-root
  path is unreachable — the findings already established this from a counter; `B9` shows
  the consequence from the other side.

### 3.3 Three of my controls had to be repaired, and that is part of the result

Reported because it is the same failure class the brief warns about:

1. **`B4` first read as "mutant changed nothing".** The book reply is clock-seeded with
   `Book Variety` 30; **at n = 5 the five draws coincide often enough that a base run read
   stable=True**, making a real mutant look inert. Fixed at n = 20 (base: 2 distinct moves;
   mutant: 1).
2. **The `clocked_1s` probe was measuring startpos — which is booked.** Three fresh base
   runs gave `c2c4`, `e2e4`, `c2c4`: pure RNG. Every "clocked search changed" row in an
   earlier draft was noise. Fixed by probing an unbooked position.
3. **`B6` read as "mutant changed nothing" at a 1000 ms clock.** A mutant that adds 390 ms
   of overhead still reaches the same depth inside a full second. At **100 ms** the arms
   separate deterministically: depth 6 / 2,789 nodes against depth 1 / 60. **A probe whose
   margin is larger than the fault it is looking for reports cleanliness.**

---

## 4. The Hash trap: confirmed, with a live control

`bench` uses `Hash 16` regardless of the option, because the 16 is the `Searcher`
constructor's first argument at `uci.cpp:611` and the UCI option path resizes a *different*
object (`searcher`, constructed at `uci.cpp:151`).

| `setoption name Hash value` | bench 13 | `go depth 14` from startpos | `go depth 15` from Kiwipete |
|---|---|---|---|
| 1 | **862,329** | 109,247 | 407,876 |
| 16 | **862,329** | 101,640 | 402,719 |
| 64 | **862,329** | 101,640 | 402,708 |
| 256 | **862,329** | 101,640 | 402,707 |
| 1024 | **862,329** | 101,640 | 402,707 |

**This is the arm that makes the null a result rather than a broken control.** "The pin
did not move when I changed Hash" and "my `setoption` never reached the engine" produce the
same pin value, and the brief's rule 3 says an inert control is worse than no control. The
right-hand columns are the two-sided test: the same `setoption` sequence **does** move a
real search's node count, at Hash 1 versus 16, and by 1–2 % across 64/256/1024. So the
option path is live and `bench` is simply not listening.

The 1,024 row is worth a line on its own: **`Hash 1024` is accepted and the pin is
unchanged**, i.e. a harness can ask for a 1 GB table, get a 16 MB one for the pin, and
never learn it. The findings' Hash-ceiling work (decision #4) is in the same blind spot:
`MultiPV` is also unread by bench.

---

## 5. What a pin CANNOT detect — the list a reviewer should keep

Stated as a list of *kinds*, because each kind is a whole subsystem:

1. **Anything about the book.** `OwnBook`, `Book File`, `Book Depth`, `Book Variety`, the
   polyglot encoder and decoder, and the entire `info string book move` reply. (B1, B4)
2. **Anything about threading.** `Threads`, helper dispatch, and the node inflation the
   findings measured at 3.68×. (B5; findings §3)
3. **Anything about the clock.** `Move Overhead`, the soft/hard limit plan, and
   `TmFinishIteration` / `TmNodeShare` — none of the time-management parameters is read on
   a depth-limited search. (B6)
4. **The drawn-root path.** Unreachable: all eight FENs are clock 0 with no history. (B9;
   findings §2)
5. **The UCI surface.** `parse_limits` (including the malformed-token traps the findings
   call the only undetectable failure shape), `apply_position`, move formatting, and the
   `option`/`readyok` exchange.
6. **`MultiPV`**, the alternate table, and the Hash ceiling that decision #4 turns on —
   bench is MultiPV 1 by construction.
7. **Any table-size question.** Hash is a literal 16 (§4).
8. **Anything above depth 13 on these eight positions**, including the depth-16/18
   instability the findings measured, unless a deeper pin is recorded (and depth 18 costs
   3.3 s, depth 20 costs 6.0 s — `bench_cost_by_depth.txt`).

**What it CAN detect, precisely**: a change to the evaluation, to a search constant, or to
move generation, that alters the node tree on 8 middlegame/endgame positions searched
fixed-depth at 8/13/16. That is a real and useful thing. It is not "the engine still works".

---

## 6. The positive proposal: `forge gate`

Seven checks, **one process**, **2.4 s wall** (5 runs: 2.34 / 2.35 / 2.41 / 2.43 / 2.60).
`scripts/gate.py`. Exit 0 only if all seven pass.

| id | check | what it catches that a pin cannot | cost |
|---|---|---|---|
| **G1** | four pins, sent **on stdin** | eval/search/movegen regressions | 1.9 s |
| **G2** | a drawn root returns a **searched** move (nodes > 0, ≥1 `info depth`) | the drawn-root bail — findings decision #2 | 5 ms |
| **G3** | a booked position emits `info string book move` **and no `info depth`** | book regressions, book-off, `Book Variety` | ~2 ms |
| **G4** | a **100 ms** clocked search returns **and searched** (≥3 info lines, >1,500 nodes, <95 ms wall) | clock collapse, `Move Overhead` misuse | ~40 ms |
| **G5** | `Threads 2` differs from `Threads 1` in nodes | a dead or ignored `Threads` — decision #3 | ~150 ms |
| **G6** | a fixed-depth `go` is **asserted order-dependent** in one session | a gate built on an unstable number | ~120 ms |
| **G7** | a clock-97 root with mate in 2 still reports a **mate** | the fifty-move band — findings §2 | ~5 ms |

**Every check is proven to fire on its own planted fault and on nothing else**
(`gate_selfcheck.py`, `gate_selfcheck.txt`): 7 of 7 `fired-cleanly`, with *collateral
measured against the base's pass set* — an earlier version of that comparison counted G2,
which is red on the base by design, as collateral on every plant, which would have hidden a
real coupling.

**G2 is also proven able to pass** (`g2_can_move.py`): a minimal drawn-root repair flips
G2 red→green and leaves **all four pins bit-identical**. A check that can only fail is as
useless as one that can only pass.

### 6.1 G6 exists because of a trap this seat walked into

A replacement gate is tempting to build out of `go depth N` node counts. **Those are not
stable in a session.** Same FEN, same depth, same process:

| context | Kiwipete `go depth 11` nodes |
|---|---|
| first search of a fresh process | **50,541** |
| the *same* search issued twice in one process | 50,541 → **11,696** |
| after three unrelated searches | **72,365** |
| fresh process + `ucinewgame` + `Clear Hash` | **50,541** |
| target first, then others, then target again | 50,541 → **13,235** |

`go_repeatability.json`, all five rows. **Four distinct node counts for one fixed-depth
search on one position, and the ratio depends entirely on which pair you divide** — so the
figure is stated three ways rather than as one headline:

| comparison | ratio | what it is |
|---|---|---|
| **72,365 / 11,696 = 6.19×** | the full spread | max/min across all seven measurements — the top of the range, not a typical swing |
| **50,541 / 11,696 = 4.32×** | row B | the *same* search repeated with nothing else in between |
| **50,541 / 13,235 = 3.82×** | row E | target, three other searches, target again |
| **72,365 / 50,541 = 1.43×** | rows C vs A | order effect alone, both fresh processes with no prior search of the target |

**An earlier draft of this file said "up to 6.4×", which was wrong**: no pair in the
evidence gives 6.4. The correct maximum is **6.19×** (`72365/11696`), and quoting it as the
swing overstates the *repeated-search* case, which is the one a harness actually meets —
that is **4.32×**. `verify_figures.py` now derives all four ratios from the JSON.

`bench` is pinnable *only* because it clears between positions (§1.2). A `go` harness that
skips the clear inherits **at least 3.82× and at most 6.19×** from search order alone. G6
asserts the dependence deliberately: if a future change removes it, the gate says so, and
until then nobody pins a `go` node count believing it is stable.

### 6.2 What it still does not cover, honestly

- **No SPRT, no Elo, no game play.** 2.4 s cannot buy strength measurement and this gate
  does not pretend to.
- **No `MultiPV`, no ponder, no `go infinite`+`stop`.** Adding them is cheap (the coverage
  workload in `bench_coverage.py` reaches 70.1 % in ~3 s) but none is proven to
  discriminate yet, and an unproven check is the thing this document is complaining about.
- **G4 and G6 are the two timing-shaped checks and the two I would watch.** G4's margin is
  a 100 ms clock against a 60-node floor, which separated 2,789 from 60 deterministically
  here; on a heavily loaded box it should be re-measured before it is trusted. G6 asserts a
  `!=`, which is robust to noise in the safe direction but could in principle pass for the
  wrong reason. Both are labelled as such rather than presented as equals of G1.
- **The gate is Python driving a process, so it is a harness, not an engine feature.** A
  `forge gate` subcommand would be better; this seat did not add one because changing
  `uci.cpp` would invalidate the very pins the gate reads.

---

## 7. Cost

| item | wall |
|---|---|
| bench 11 | 0.17 s |
| bench 13 | 0.44 s |
| bench 16 | 1.47 s |
| bench 18 | 3.27 s |
| bench 20 | 5.97 s |
| perft 5 | ~0.05 s |
| **all four pins (today's gate)** | **~1.9 s** |
| **`forge gate`, 7 checks** | **2.4 s** |
| gate on the repaired build (all 7 pass) | 2.6 s |

**The proposal costs 0.5 s more than the current gate** — 26 % more wall for five checks
covering subsystems the current gate cannot see at all. Depth 16 is 77 % of the current
gate's entire cost and is the one pin that could be dropped to buy back time if it were
ever needed. It should not be: it is the pin that caught M2.

---

## 8. What I had to withdraw, and what is left untested

**Withdrawn / repaired during this seat. Items 1–3 are instrument faults recorded in §3.3;
items 4–7 are figure faults, found by the coordinator checking `evidence/` against this
document rather than by me:**

1. "Book Variety does not affect anything the gate sees" — my n = 5 probe said the mutant
   was inert; at n = 20 it is a live gate-passing change. **The instrument, not the engine.**
2. "A clocked search differs across these mutants" — my probe was on `startpos`, which the
   book answers with a clock-seeded move. Three fresh base runs gave three different moves.
   **Every row that relied on it was noise and is gone.**
3. "Move Overhead is invisible to the gate and the probe agrees" — the probe's margin
   (1,000 ms) was larger than the fault (390 ms). **At 100 ms it separates 2,789 nodes from
   60.** The blind-spot finding survived; the probe that was supposed to demonstrate it did
   not, and had to be rebuilt.
4. **"5 of 9 behavioural mutants were passed by a green gate"** — wrong count and an
   incomplete list. The evidence says **6 of 9**, and the omitted one is **B8, the
   fifty-move leaf rule moved one ply** — the strongest single case, because it is the same
   band defect the leaf seat found independently. The list in §0 now names all six.
5. **"one by 4.5 % to 64 %"** as the sensitivity range — **both figures are unconstructible.**
   No base-to-mutant shift on any pin gives 4.5 % or 64 %, and neither does any pairwise
   difference between mutants on `bench 13`. The range is **2.2 % to 30.3 %**, now derived
   in §2.1 from a per-mutant shift table.
6. **"up to 6.4×"** for the order-dependence swing — no pair in `go_repeatability.json`
   gives 6.4. The maximum is **6.19×** (`72365/11696`); the repeated-search case a harness
   actually meets is **4.32×**. All four ratios are now derived in §6.1.
7. **"all 64 `PawnPsqt` weights +40"** — the mutation touches the **middlegame half only**
   (`S(mg, eg)` packs mg in the low 16 bits, and the rewrite matches only the first field).
   §2.1 now says so.

**And one summary field disagreed with the rows it summarised.** An intermediate copy of
`go_repeatability.json` carried `distinct_values: [11696, 13235, 50541]` while its rows
contained 72,365 — a row whose search returned `None` dropped out of the set
comprehension, so the field was silently computed over six of seven measurements. The
committed file is correct and three re-runs reproduce it, but the class is the one this
audit wrote a trap about: **a summary that disagrees with the data it summarises.**
`go_repeatability.py` now refuses to emit a summary when any row is null or when
`distinct_values` disagrees with the rows, and `verify_figures.py` checks every committed
JSON for the same internal consistency.

**All seven faults above are now machine-checked.** `scripts/plant_check.sh` plants each
one and requires the check to fail with a message naming it — 7 of 7 fire, and the clean
tree passes first so the plants mean something. Two of the guards written for this run
were themselves too weak on the first try and had to be fixed: the count guard accepted
**any** correct sentence rather than every one, and the coverage guard tested for the
presence of a percentage rather than its value. Both are recorded because a guard that
passes for the wrong reason is the defect this document is about.

**Not tested, and why:**
- **No `go movetime` arm in the gate.** Depth and clocks are covered; `movetime` shares
  `parse_limits` with the clock path, so it adds little, but that is an argument and not a
  measurement.
- **No book-file (external `.bin`) arm.** Only the embedded book was exercised.
- **No drawn-root coverage in the *pins* themselves, and none is proposed.** All eight
  bench FENs are clock 0 with no history, so the root gate is structurally unreachable from
  the pin workload. G2 covers it instead. Adding a drawn FEN to the bench list would change
  all four pins and is not something a gate should do casually.
- **The drawn-root repair used in `g2_can_move.py` is mine, not the shipped patch.** The
  shipped patch files are not in this checkout (`swarm/12/job1/two_doors_mate.patch.txt`,
  `swarm/27/job1/drawn_root_reporting.patch.txt`). It exists only to prove G2 can pass; its
  correctness is not claimed beyond that one fixture.
- **Timing on a contended box.** Sibling audit workers shared this 4-core machine for part
  of the run. Nothing here depends on a ratio under 1.5 %, and the two timing-shaped checks
  are flagged in §6.2.

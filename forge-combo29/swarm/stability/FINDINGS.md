# Stability of a fixed-depth score — can it be a training label?

**Answer: yes at `Threads 1`, and only if you reset between positions. No at `Threads 4`.
And the `Threads 1` "yes" is conditional on a harness rule that is easy to get wrong:
if you batch positions in one process without `ucinewgame`, 194 of 200 positions
answer differently depending on what preceded them.**

Measured on base `6b98f217`, g++ 13.3.0, `-DFORGE_MARCH=x86-64-v4`,
`go depth 12`, `Hash 32` (and `Hash 1` as a second arm), `MultiPV 1`,
`OwnBook false`, one fresh process per run unless a row says otherwise.
All four honesty pins matched before anything was recorded
(`312,866 / 862,329 / 3,024,920 / perft 5 4,865,609` — `evidence/pins.txt`).

## The four headline numbers

| question | result |
|---|---|
| Same position, 30 fresh processes, `Threads 1`, depth 12 | **1 distinct score, 1 bestmove, 1 depth, identical node counts** — 4 positions, 120 launches, 0 cp range |
| Same at `Threads 4` | **19–27 distinct scores out of 30**, spread 22–84 cp, 1–6 distinct bestmoves, node ratio up to 2.78× |
| 200 corpus positions, twice, fresh process each, `Threads 1` | **0 of 200 disagree on score, depth, bestmove — or even node count** |
| Same 200 positions, two batch orders, one process each | **194 of 200 disagree**, 66 of them also on bestmove |

So the label question has a clean answer and a trap attached. A fixed-depth score at
`Threads 1` in a fresh process is a label. A fixed-depth score at `Threads 1` **from a
reused process is not**, and the failure is silent.

## What this adds to the audit

The audit knew (a) Threads-1 searches are bit-identical at fixed depth, 40 of 40, and
(b) warm state shifts scores by up to 55 cp. This seat adds five things it had never
measured:

1. **Bit-identity survives process launch.** 120 launches over 5 rows (4 positions at
   depth 12, one at depth 16) produced one score each. Not a spot check: the node counts
   are identical too, to the unit, which is the strongest available form of the claim
   (a hash collision in the *answer* is possible; an identical total node count across
   separate processes is not a coincidence of scoring).
2. **A corpus-level answer, not a spot check.** 0 of 200 positions disagree on any field
   in a fresh-process pair. The corpus deliberately spans phases (35 opening, 140
   middlegame, 25 endgame, 6–32 pieces), so this is not "stable on middlegames".
3. **The warm-state drift is an ORDER dependence, and it is deterministic.** A vs A2
   (same order, fresh process) is 0 of 200; A vs B (same positions, shuffled order) is
   194 of 200. Two arms could not have told those apart — only the ABA design does.
4. **The drift is far larger than the 55 cp the audit recorded, on a real corpus.**
   Corpus-order vs shuffled reaches **433 cp** on one position, mean 25.2 cp over the
   194 that moved. The 55 cp figure was one position; 433 cp is the corpus tail.
5. **`ucinewgame` per position removes it completely.** Batch-with-reset equals the
   fresh-process reference on **200 of 200** positions, and order stops mattering
   (**0 of 200**). This converts the audit's "`ucinewgame` IS a cold reset" from a
   per-search property into a labeling-harness recipe.

## Field-by-field: which field moves

Every disagreement is broken out by field, because they have different consequences.

### `Threads 4` — corpus, 200 positions twice (`evidence/m3b_corpus_T4.json`)

| field moved | positions |
|---|---|
| score | 133 |
| score **and** bestmove | 56 |
| bestmove only | 2 |
| nothing | 9 |
| **any** | **191 of 200** |

Score differs **189 of 200**, bestmove **58 of 200**, depth **0 of 200**, node count
**200 of 200**. Mean cp gap over the 189 score disagreements is 19.8; the largest is
**170**. By phase: opening 33 of 35, middlegame 135 of 140, endgame 23 of 25 — spread
everywhere, not concentrated in one phase.

**Depth never moved.** That is worth stating explicitly: fixed-depth search at four
threads always completes depth 12. The instability is in *which tree* the threads
explored, not in how far they got.

### Order dependence — batch, one process per arm (`evidence/m4_order.json`, `m4b_order_reset.json`)

| comparison | any | score | bestmove | depth |
|---|---|---|---|---|
| A vs A2 — same order, fresh process | 0 / 200 | 0 | 0 | 0 |
| A vs B — corpus order vs shuffled | **194 / 200** | 194 | 66 | 0 |
| A vs fresh — batch vs one-process-per-position | 197 / 200 | 195 | 61 | 0 |
| B vs fresh — shuffled batch vs fresh | 194 / 200 | 193 | 56 | 0 |

A == A2 is the control that makes the rest admissible: the batch is *reproducible*, so
A ≠ B is a property of the order, not noise. **This is a state leak, and it is
deterministic** — which is the audit's trap-3 sentence ("a reusable harness does not get
noise, it gets a stable-looking wrong number") generalized from one position to a corpus.

### Resets — batch vs the fresh reference (`evidence/m5_resets.json`)

| arm (reset before each of the 200 positions) | any | score | bestmove |
|---|---|---|---|
| nothing | 197 / 200 | 195 | 61 |
| `ucinewgame` | **0 / 200** | 0 | 0 |
| `ucinewgame` + `Clear Hash` | 0 / 200 | 0 | 0 |
| `ucinewgame` + `Hash` resend | 0 / 200 | 0 | 0 |

And order dependence under `ucinewgame`: **0 of 200**, against 194 of 200 with no
reset in the same script (`m4b_order_reset.json`). The no-reset arm is the positive
control — this script *can* see a leak, and does, when the reset is removed.

`ucinewgame` alone suffices. Adding `Clear Hash` or a same-value `Hash` resend changes
nothing, which is consistent with trap 3: `ucinewgame` calls `Searcher::clear()`
(`src/search.cpp:2679`) and subsumes both, while a bare `Clear Hash` does not
(`clear_hash()` then `evaluator_.clear()` only, `search.hpp:452`).

## Does the book contaminate this? No — and the harness proves it

The audit found the book varies 3 of 5 at Threads 1 with default variety, because it is
seeded from a **clock** (`uci.cpp:161-162`, `steady_clock`). So a stability test must not
be measuring its own RNG.

**What the harness pins.** `setoption name OwnBook value false` on **every** search that
contributes a number: `BASE_OPTS` in `meas_repeat.py` and `corpus_twice.py`, `OPTS` in
`order_batch.py` and `order_reset.py`, `RESETS`-independent options in `batch_resets.py`,
and the `options=` argument of every `run_one` call in `book_rng.py` and `fault_proof.py`.

**Why that pin is sufficient here, proved rather than assumed** (`evidence/book_rng.json`,
40 fresh processes per arm):

| arm | distinct book moves | histogram | replies with no `info depth` |
|---|---|---|---|
| `OwnBook true`, default variety, T1 | **2** | e2e4 22, c2c4 18 | 40 / 40 |
| `OwnBook true`, `Book Variety 0`, T1 | **1** | e2e4 40 | 40 / 40 |
| `OwnBook false`, T1 | **1** | e2e4 40 | **0 / 40** |
| `OwnBook true`, default variety, T4 | 2 | e2e4 25, c2c4 15 | 40 / 40 |

So the variation is the RNG (killing it with `Book Variety 0` removes it), and it is
thread-invariant (T4 gives the same 2 moves) — the audit's correction, reproduced.

**`go depth` cannot reach the book at all, so the pin is belt-and-braces.** With
`OwnBook true` and `go depth 6`: **0 of 20** replies were book moves. The positive
control on the same instrument, `OwnBook true` with `go movetime 400`: **20 of 20** were
book moves. Source agrees: the gate at `uci.cpp:525` requires `time_ms >= 0 ||
movetime_ms >= 0`, and `go depth` sets neither. **Stated because a corrected condition
that is not needed is a condition a later reproducer will copy and later wonder about.**

I did **not** rely on `Book Variety 0`; I pinned `OwnBook false`. Both arms are reported
so the choice is auditable rather than asserted.

## The drawn root is stable, and stably wrong

A threefold root is bit-identical across 30 fresh processes at **both** thread counts:
`cp 0`, `a2a3`, `depth 12`, `nodes 0` — 30 of 30 each, one distinct value. A mate-in-one
position is likewise identical 30 of 30 at both thread counts (`mate 1`, `a1a8`, depth 12).

**Stability is not correctness.** The drawn-root row is the audit's §1b hazard in its
most dangerous form for a labeling harness: it is *perfectly reproducible*, so every
stability check in this document passes on it, while the move was never searched and the
score is not an assessment. **A stability audit cannot detect this class at all** — it
needs the `nodes == 0` + empty-`pv` check, which is a separate gate. My corpus contains
0 bail positions of 200 (engine self-play never produced a drawn root at the sampled
plies), so **this document says nothing about bail frequency in a real corpus** — only
that when one occurs, repetition will not reveal it.

## My own instrument had this exact bug, and it is the reason F8/F9 exist

The first version of `ucih.parse_search` tested `pv is None` to detect the bail. The
engine prints a **bare `pv` token with nothing after it**, so the parsed value is `""`,
not `None` — and the detector returned `False` on every real bail. Caught by inspecting
the raw wire on a threefold, not by any clean-run check. Fixed, and then pinned with two
fault proofs (F8 must fire on a real threefold; F9, the negative control, must stay
silent on a searching position — a detector hard-wired to `True` passes F8 alone).

Every other checker in this seat is fault-proved the same way: **9 of 9 planted faults
fired** (`evidence/fault_proof.txt`), including F3 (the distinct-score instrument must
see Threads-4 variation, or the Threads-1 zero means nothing) and F5 (the book RNG must
be observable).

## The harness rules a labeling pipeline must follow

1. **One process per position, or `ucinewgame` before every position.** Not `Clear Hash`.
   A batch without reset is wrong on 197 of 200 positions versus fresh.
2. **`Threads 1`.** At `Threads 4` the score is not a label: 189 of 200 positions give a
   different cp on a repeat, mean gap 19.8, max 170.
3. **Pin `OwnBook false`** on every search, even though `go depth` cannot reach the book.
   It costs nothing and removes a clock-seeded RNG from the experiment.
4. **Never pipe `quit` into a live search.** F1 reproduces the fabrication through a real
   shell pipe: a `bestmove` with zero `info depth` lines.
5. **Validate the FEN *and* check the position was not refused.** F2 shows the engine
   answering `d2d4` on a fullmove-0 FEN it rejected, with `info string invalid FEN` on
   the `position` command only.
6. **Filter drawn roots on `nodes == 0` + empty `pv`.** Reproducibility will not catch them.

## What is not established

- **No second machine.** The cross-process claim is launch-to-launch on one CPU (4 cores,
  Xeon). A different CPU, ISA level or `-march` is untested here; the audit's seat 69
  covered build- and environment-proxies and found nothing, but that is not a second box.
- **Endgame coverage is thin.** The 25 endgame positions are 6–32 pieces; no tablebase-range
  positions (≤ 7 pieces) were measured. Nothing here says a 5-piece position is stable.
- **`go nodes N` was not tested.** All stability numbers are `go depth`. The audit records
  `go nodes` and `go softnodes` as different searches, so a node-budget label needs its
  own measurement — none of this transfers automatically.
- **Deeper than 16 unmeasured.** One position at depth 16 was identical 30 of 30. Depth 20+
  is untested, and the drawn-root trap means a deeper search on a drawn root would report
  a *higher* depth on the same 0 nodes.
- **The corpus is engine self-play, not human games.** Positions come from random 8-ply
  openings extended by depth-8 self-play. A human-game corpus has different phase and
  repetition statistics; the *stability* property should transfer, the *bail frequency*
  is unknown (0 of 200 here).
- **`Threads 4` instability was not traced to a mechanism.** Node counts differ 200 of
  200, so it is tree divergence, but which race or ordering produces it is not measured.
- **No order-dependence test at `Threads 4`.** Only `Threads 1`, where the leak was found.

## Files

- `scripts/ucih.py` — UCI driver; send-then-read-to-terminator, never pipes `quit`.
- `scripts/pins_probe.py` — the four honesty pins (`bench` on stdin).
- `scripts/make_corpus.py` — 200-position corpus, python-chess validated.
- `scripts/meas_repeat.py` — M1/M2: N fresh processes on one position.
- `scripts/corpus_twice.py` — M3: 200 positions twice in fresh processes.
- `scripts/order_batch.py` — M4: ABA order test.
- `scripts/order_reset.py` — M4b: order test with and without `ucinewgame`.
- `scripts/batch_resets.py` — M5: reset arms against the fresh reference.
- `scripts/book_rng.py` — M6: book RNG and `go depth` reachability.
- `scripts/fault_proof.py` — 9 planted faults, 9 fired.
- `scripts/rederive.py` — recomputes every headline count from the per-run rows
  independently of the summary counters; all match (`evidence/rederive.txt`).
- `scripts/tables.py` — regenerates every table above from `evidence/`.

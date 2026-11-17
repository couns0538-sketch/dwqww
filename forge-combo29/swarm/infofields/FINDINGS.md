---
cursor:
  subagentId: "bc-9d3317d0-b2da-5a04-9fbd-fe2a6a73fdc6"
---

# Every field on the `info` line, checked against UCI

**Result first: four of the nine fields carry a claim UCI does not support, and two more are
correct only because a `max()` hides the defect. `depth`, `hashfull`, `nodes` and `time` are
wrong on paths a client actually reaches; `seldepth` and `multipv` are structurally unable to
report what they are defined to report. `score`, `nps` and `pv` hold on every searching path
tested. The single worst field is `hashfull`, which is not near-miss wrong — on a table holding
30,940 nodes of warm entries it reports `hashfull 10` per-mille of a table it is not counting.**

Build and settings for every row below: base commit `6b98f217`, `g++` `/usr/bin/g++`,
`-DFORGE_MARCH=x86-64-v4`, Release with `NDEBUG`, 4 cores, `Threads 1` unless the row says
otherwise, `Hash 32` unless stated, `OwnBook false` unless stated. Gate pins all verified before
any recording:

| pin | expected | measured |
|---|---|---|
| `bench 11` | 312,866 | **312,866** |
| `bench 13` | 862,329 | **862,329** |
| `bench 16` | 3,024,920 | **3,024,920** |
| `go perft 5` | 4,865,609 | **4,865,609** |

`bench N` was sent on stdin as a UCI command in every case. No search in this audit was ended by
piping `quit`; every abort used a real `stop` after reading to `bestmove`, and every measurement
came from a fresh process unless the row says the table was deliberately shared.

---

## The conformance table

| field | UCI definition | measured | verdict | line that shows it |
|---|---|---|---|---|
| `depth` | "the depth searched" — the iteration the score and pv belong to | `max_depth` is clamped to `[1,64]` and the emit loop walks it unconditionally; on a drawn root it emits one line per depth with **0 nodes**; on the abort path it emits an **unfinished** iteration's pv under that iteration's depth with the **previous** iteration's score | **NON-CONFORMANT** — independently reproduced on the owner's own build | `info depth 64 seldepth 64 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` and `info depth 22 seldepth 40 score cp 112 … time 950 pv d4c5 …` |
| `seldepth` | "the depth searched including selective deepening" | printed as `max(seldepth_, depth)` — so it **cannot** be < `depth`, by construction not by measurement; on the bail it is `max(0, depth)`, i.e. entirely fabricated | **NON-CONFORMANT on the bail; UNFALSIFIABLE elsewhere** | `info depth 64 seldepth 64 … nodes 0 … pv` |
| `multipv` | 1-based index of this line among the reported lines | 1..n contiguous and present on **every** line at MultiPV 2/3/4; absent entirely at MultiPV 1 (allowed: MultiPV 1 needs no index); **absent on the book path** and **degrades to only `multipv 1`** on a drawn root | **CONFORMANT on searching paths; two known exceptions** | `info depth 1 multipv 3 score cp -10 seldepth 1 nodes 74 …`; book: only `info string book move c2c4` |
| `score` | evaluation in cp, **from the side to move**; `mate N` in moves | same board both sides: `cp 490` (White) vs `cp -477` (Black); mirror: `cp 20` / `cp 5`; `mate 2` and `mate -2` both correct; `mate 0` only on a true checkmate | **CONFORMANT** | `… 4K2R w … → cp 490` / `… 4K2R b … → cp -477` |
| `nodes` | nodes searched so far in this search | exact at Threads 1 (**reproduces the 312,866 pin** from 8 independent searches); **falls between depths on 26% of transitions at MultiPV ≥ 2**; two different totals on the wire under `softnodes` | **PARTLY NON-CONFORMANT** | `info depth 3 multipv 3 … nodes 74` then `info depth 4 multipv 1 … nodes 54` |
| `nps` | nodes per second | exactly `nodes*1000/time` with integer truncation — **28/28 lines exact, 0 mismatches**; but at `time 0` it is a `0` sentinel, not a rate | **CONFORMANT arithmetic; `0` is a sentinel at time 0** | `info depth 1 seldepth 1 score cp 1 nodes 26 nps 0 … time 0` (26 nodes, 0 nps) |
| `hashfull` | per-mille occupancy of the hash table, 0–1000 | in range always (0–1000), but counts **only entries of the current generation**, so a demonstrably warm table reads near 0; under MultiPV > 1 the last line reports a **different, smaller table** | **NON-CONFORMANT** | warm-table run: `info depth 18 … nodes 30940 … hashfull 10` after a run that left 703,960 nodes of entries |
| `time` | "the time spent searching so far, in milliseconds" | from `go`/worker entry, **not** from `ponderhit`, while the budget clock restarts at `ponderhit`; during a ponder it reports 375/933/1655 ms while its own budget clock is hard-pinned at 0 | **NON-CONFORMANT on the ponder path; conformant otherwise** | during ponder: `info depth 22 … time 1699` with `elapsed_ms()==0`; budget clock disagrees by the whole wait |
| `pv` | the principal variation; `pv[0]` is the best move | final line's `pv[0] == bestmove` in **17/17** cases incl. aborts; every pv a **legal** line under python-chess, **0 illegal moves**; intermediate depths legitimately differ (9–13 per case) and are not violations | **CONFORMANT on searching paths** (empty-pv bail is a separate known defect) | `info depth 14 … pv e2a6 b4c3 …` → `bestmove e2a6` |

`info string` is not a field with a definition — UCI reserves it for free text. Two of its uses
here collide with real fields and are reported below.

---

## Where each verdict comes from

### `depth` — two distinct lies, one already known and one not

**The known one, re-measured (bail).** A drawn root skips the search entirely and emits one line
per depth up to the clamp:

```
info depth 10 seldepth 10 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv     (go depth 10)
info depth 64 seldepth 64 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv     (go nodes 1000)
info depth 64 seldepth 64 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv     (go nodes 100000)
```

The line count is `min(requested depth, 64)` and **nothing was searched** — 0 nodes on all of
them. This matches §1b. `bestmove e1d1` follows, a move that never appears in any pv because
there is no pv.

**The new one, proven on the wire (abort).** The abort branch republishes the pv of an
*unfinished* iteration under that iteration's depth, while `result.score` still holds the last
*completed* iteration's score:

```2440:2451:forge-combo29/src/search.cpp
            if (!stopped_by_nodes_ && ss->pv_length > 0 &&
                !(result.pv.size() > 0 && result.pv[0] == ss->pv[0])) {
                result.best_move = ss->pv[0];
                result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
                // Publish the revised line so GUIs see a PV consistent with the move.
                emit(depth, result.score, result.pv);
            }
```

`depth` here is the loop variable of the iteration that just aborted. The proof that the label is
false is internal to the wire: the same position, searched to depth 22 to completion, scores
`cp 104`, and depth 21 scores `cp 112`. An aborted run at 0.98–1.08 s publishes:

```
info depth 22 seldepth 40 score cp 112 nodes 1817600 nps 1913263 hashfull 413 time 950 pv d4c5 d5d4 f3e5 …
```

`depth 22` carrying the depth-21 score, and a pv that is *not* the depth-22 pv. Reproduced at
5 of 8 sampled stop times between 0.96 s and 1.10 s on that position (`sharp-attack`), 0 of 8 on
`kiwipete`. So this fires on a minority of aborts but fires repeatably.

The A/A control that makes this meaningful: two full runs to depth 12 agree on **every**
`(depth, score, pv)` triple. Only `nodes`/`time`/`nps` move with the clock. A separate A/A pair
on the abort path at the same stop time reproduced depth and bestmove exactly.

**Why the first attempt was inconclusive and what had to be withdrawn:** an initial test reset
`Hash` to its own value between abort runs to get a cold table, then compared the aborted ladder
against a cold reference. That comparison is invalid — the `Hash` reset clears the *table* but
leaves *histories* warm (a known trap), so every reference node count was polluted. The A/A pair
failed, which is what caught it. The claim above uses no cross-run comparison at all: it compares
one run's own score at depth 21 against the same run's depth-22 line, plus a single clean
reference run.

**What a client does wrong:** a GUI shows "depth 22" and a score that belongs to depth 21, and
any tool that plots score-versus-depth, or that stops when depth reaches a threshold, treats an
unfinished iteration as finished evidence. On the bail it is worse — a GUI displays the full
configured depth on a search that touched no nodes.

**Independent reproduction (owner, own build).** The owner reproduced the same shape on a
different build — so it is not a property of this harness. Their case: `go infinite`, then `stop`
at 1.05 s, final line `info depth 20 seldepth 33 … pv …` whose pv is **18 plies**. A pv shorter
than the depth it claims, on the last line a client sees.

That is a *weaker* proof than the one cited above and is recorded as confirmation, not as the
basis of the finding:

| observation | what it shows |
|---|---|
| owner: pv length 18 < claimed depth 20 | the line is internally inconsistent — a completed depth-20 iteration cannot carry an 18-ply pv |
| this audit: `depth 22` carries the depth-21 score and the depth-21-shaped pv | *which* iteration the line actually belongs to — depth 21 — and therefore that the label is off by one |

Both agree the abort path mislabels `depth`. Only the score-carried-forward comparison identifies
the mislabelled value, which is why the report cites this audit's instance and the owner's as
corroboration. The owner's run also did not force a pv-head change, which is the condition that
makes the revision fire — consistent with the 5-of-8 rate measured here rather than a contradiction.

**A related check that looks tempting and does not work.** On a searching path one might expect
`len(pv) >= depth`, since the pv runs about one ply per depth. **I tested that and it is false:**
on a clean `go depth 20` from startpos, the completed depth-16 iteration reports a **15-ply pv**
(1 of 20 lines). TT cutoffs and transpositions shorten a pv legitimately, so a short pv is *not* a
violation and cannot be used as a symptom of the revision line. The owner's pv-length observation
is evidence *because it is on the final line of an aborted search* and paired with their knowledge
that no completion was reached — not because shortness alone proves anything. This is exactly why
the score-carried-forward comparison, which needs no heuristic, is the proof of record.

### `seldepth` — cannot be wrong by this measurement, which is the problem

```2232:2245:forge-combo29/src/search.cpp
        const int shown_seldepth = seldepth_override >= 0 ? seldepth_override : seldepth_;
        ...
            std::cout << " multipv " << pv_index << " score " << format_score(score)
                      << " seldepth " << std::max(shown_seldepth, depth);
        } else {
            std::cout << " seldepth " << std::max(shown_seldepth, depth) << " score " << format_score(score);
```

`max(…, depth)` means the "seldepth ≥ depth" invariant holds by construction. A checker for that
invariant is therefore worthless — and I built one and planted a fault in it (`controls.py`), which
correctly fires, but only on synthetic records. **The honest verdict is that the ordering claim is
untestable from the wire.** What *is* testable is whether the number tracks real search depth:
at `go depth 3` on kiwipete every one of the three lines reports `seldepth 11`, and the depth-1 pv
is six plies long, so the number reflects genuine qsearch depth rather than the iteration index.
On the bail it reports `1..64` alongside `nodes 0`, which is fabricated.

**What a client does wrong:** reads `seldepth 64` on a zero-node search and concludes a deep
selective search happened.

### `multipv` — conformant where it applies, absent where it matters

At MultiPV 2, 3 and 4 every depth produced exactly that many lines, numbered 1..n contiguously, on
every depth from 1 to 8 (`multipv.json`). At MultiPV 1 the token is absent on every line, which is
correct — UCI only requires the index when there is more than one line.

The two exceptions, both already in the findings and both re-measured:

- **Book path: zero `info` lines.** `info string book move c2c4` then `bestmove c2c4`. A client
  waiting for `multipv 1` deadlocks.
- **Drawn root: degrades to `multipv 1` only**, one line per depth, even at MultiPV 3:

```
info depth 1 multipv 1 score cp 0 seldepth 1 nodes 0 nps 0 hashfull 0 time 0 pv
```

A GUI expecting three alternatives waits forever for lines 2 and 3.

**What a client does wrong:** renders one PV pane where three were requested, with no signal that
two are missing.

### `score` — the clean field

Side-to-move relative, verified three ways. Same board, both sides to move:

```
4k3/8/8/8/8/8/8/4K2R w  ->  info depth 12 seldepth 16 score cp 490  … pv h1f1 …
4k3/8/8/8/8/8/8/4K2R b  ->  info depth 12 seldepth 17 score cp -477 … pv e8f7 …
```

The magnitudes differ (490 vs 477) because the two searches are of different depths of the same
tree with different mobility; the **sign** is what UCI constrains, and it is correct. Colour-mirrored
position: `cp 20` for White to move, `cp 5` for the same position mirrored with Black to move —
again sign-correct, and a client that negates for Black's POV gets the right answer.

Mate formatting is right in both directions: `score mate 2` for a mate the side to move delivers
(`pv g3g6 c6e5 g6h7`), `score mate -2` for a side about to be mated, and `score mate 0` **only** at a
true checkmate root (validated `is_checkmate()` in python-chess). `mate 1` at mate-in-one.

One caveat worth stating: at `go depth 8` the mate-in-2 position reports `cp 687`, not `mate 2`;
the mate is only found at depth 14. That is a search-depth fact, not a score-format defect, and it
is why §1b's rule "read `mate 0` to distinguish checkmate from stalemate" must be paired with a
depth requirement.

**Verdict: conformant.** No client harm found.

### `nodes` — exact at one thread, incoherent at MultiPV

**Exact where §1b implies it should be.** The eight bench positions searched individually, each in
a fresh process with `Hash 16` and `OwnBook false`, sum to **312,866** — the bench pin, digit for
digit. This is a real cross-check because `bench` builds its own searcher and never reads `Threads`.

The control that makes it a result: the *same* eight searches in **one** process reusing one table
sum to **343,222**, not the pin. A first attempt without the fresh-process control produced 343,222
and would have looked like a `nodes` defect. It is not — it is warm history. **That earlier reading
was withdrawn.**

**Non-conformant at MultiPV ≥ 2.** The node count *falls* across a depth boundary on 26% of
transitions (9 drops in 35 transitions at MultiPV 3, 6 in 23 at MultiPV 2, 0 in 11 at MultiPV 1):

```
info depth 3 multipv 3 score cp 8   seldepth 3  nodes 74    nps 4933  hashfull 0 time 15 pv c2c4
info depth 4 multipv 1 score cp 30  seldepth 6  nodes 54    nps 3176  hashfull 0 time 17 pv e2e4
```

`nodes 74` then `nodes 54` — the search cannot have un-searched 20 nodes. Cause: on the MultiPV
path `emit` is given `node_override = shown_nodes`, the *cumulative* total across the lines of one
depth, which resets to the primary worker's count on the next depth. Off the MultiPV path it is
`total_nodes()`.

**Two different totals on the wire.** Under `go softnodes`, the final depth line and the trailing
`info string softnodes` disagree once MultiPV > 1, because they print different quantities:

```
MultiPV 1:  last depth line nodes 212340   |  info string softnodes nodes 212340      (delta 0)
MultiPV 3:  last depth line nodes 141326   |  info string softnodes nodes 259405      (delta 118,079)
```

**What a client does wrong:** a GUI's node counter counts *down* every few plies (visible to the
user), and any throughput tool that reads node totals gets a number that is neither the primary
worker's work nor the search's work.

Monotonicity *within* a depth is clean at Threads 1, 2 and 4 (0 drops in 4 runs × 3 thread counts),
so the defect is specific to the MultiPV override, not to the cross-worker sum.

### `nps` — arithmetic exact, and one sentinel

28 of 28 lines matched `nodes * 1000 / time` exactly with integer truncation, including the ones
where `time` was small. **Arithmetic verdict: conformant.**

The exception is `time 0`, where `nps` is set to `0` rather than being undefined:

```
info depth 4 seldepth 6 score cp 30 nodes 404 nps 0 hashfull 0 time 0 pv e2e4 e7e5 c2c3 c7c6
```

404 nodes in under a millisecond is a real measurement; `0 nps` is not the rate. The largest such
line carried 1,001 nodes. A client that averages `nps` including these reads a depressed rate;
a client that displays "0 nps" shows a search doing nothing while it searches 404 nodes.

### `hashfull` — the field that is wrong about a fact, not just imprecise

Range is fine: 0–1000 across every run, monotone within a search, `hashfull 1000` reached legitimately
at `Hash 1`. The defect is *what it counts*.

```562:572:forge-combo29/src/search.cpp
int TranspositionTable::hashfull() const {
    int count = 0;
    ...
            if (entry.occupied() && entry.generation() == generation_) ++count;
    ...
    return sample == 0 ? 0 : count * 1000 / (4 * static_cast<int>(sample));
}
```

`Searcher::search` calls `tt.new_search()` once per search, bumping `generation_`. Entries from
earlier searches are still resident and still probed, but are **excluded from the count**.

Both required proofs, from one run (`hashfull_generation.json`):

| run | first-line `hashfull` | last-line `hashfull` | final nodes |
|---|---|---|---|
| 1, cold table | 0 | 185 | 703,960 |
| 2, warm from 1 | **0** | 89 | **311,421** |
| 3, warm from 2 | **0** | 10 | **30,940** |
| 4, after forced clear | 0 | 172 | 702,673 |

**Proof the path ran:** run 3 finished depth 18 in 30,940 nodes — 23× less work than the 702,673
of the cleared run. The table was unambiguously warm and being used.
**Proof it still reports near-zero:** run 3's final line reads `hashfull 10`.

```
info depth 18 seldepth 25 score cp 17 nodes 30940 nps 1933750 hashfull 10 time 16 pv g1f3 g8f6 d2d4 …
```

**And under MultiPV the reported table is not even the engine's.** The last line of a MultiPV search
carries the *alternate* worker's table, which is cleared before every alternate line:

| setting | hashfull per line at depth 18 | last line vs MultiPV 1 reference (185) |
|---|---|---|
| MultiPV 1 | `[185]` | same |
| MultiPV 2 | `[185, 104]` | **different table** |
| MultiPV 3 | `[185, 89, 104]` | **different table** |
| MultiPV 4 | `[185, 89, 81, 104]` | **different table** |

**What a client does wrong:** a GUI advises raising `Hash` when `hashfull` nears 1000. This engine
will read near 0 while the table is full of usable entries, so the advice never comes; and a
long-lived analysis session reads `hashfull 10` on its third search while that search ran 23×
faster than a cold one. A tool that monitors memory pressure from this field measures the wrong
thing entirely.

### `time` — right for ordinary searches, wrong by the whole ponder wait

Ordinary cases are conformant. `go movetime 1000` reports a final `time` of 946 ms against a
990 ms budget (10 ms Move Overhead) and a 0.99 s wall — it tracks the budget. `go depth 18` ends at
377 ms against 0.378 s wall. Monotone in every ordinary run.

The ponder case is not. Two clocks exist and they have different origins:

```1244:1254:forge-combo29/src/search.cpp
std::int64_t Worker::elapsed_ms() const {
    auto origin = start_;
    if (pondering_) {
        const std::int64_t hit_ns = shared_.ponder_hit_ns.load(std::memory_order_relaxed);
        if (hit_ns == 0) return 0;
        origin = ...(hit_ns)...;
    }
    return duration_cast<milliseconds>(now() - origin).count();
}
```

`elapsed_ms()` — the clock that enforces the budget — restarts at `ponderhit` and is **hard-pinned
to 0** before it. But `emit` does not call it:

```2229:2234:forge-combo29/src/search.cpp
        const std::int64_t elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count();
```

That counts from worker entry, i.e. from `go`.

**The race-free observation.** Snapshot the lines the engine publishes *while it is still
pondering*, when its own budget clock is defined to be 0:

| wall since `go` | reported `time` | reported `nps` | budget clock (`elapsed_ms()`) |
|---|---|---|---|
| 0.52 s | **375 ms** | 1,877,226 | 0 |
| 1.02 s | **933 ms** | 1,907,571 | 0 |
| 2.00 s | **1,655 ms** | 1,895,359 | 0 |
| 4.52 s | **3,958 ms** | 1,891,205 | 0 |

The engine publishes `time 375` while its own budget clock says 0. That is the disagreement, proven
without any stop race and without depending on iteration latency. Under `go ponder movetime 1000`
with `ponderhit` at 3.0 s, the search then ran a further 0.99 s and reported final `time 3364` /
`3978` ms against a 990 ms budget — a 2.4–3.0 s surplus.

Control: the same snapshot on `go infinite` (no ponder, one origin for both clocks) shows `time`
tracking the wall clock — 50, 135, 361 ms at 0.07, 0.16, 0.38 s.

**What had to be withdrawn here.** My first attempt varied the ponder wait with the budget fixed and
checked whether the surplus equalled the wait. It does not, reliably: the final `time` is stamped
when the last *completed iteration* ended, which can be seconds before the `stop` fires, so the
surplus is `wait + (time in the unfinished iteration)`. Two rows of five deviated by ~1 s in the
opposite direction. That design cannot attribute the surplus, so I discarded it and used the
during-ponder snapshot instead, which needs no arithmetic on racy quantities. `time_ponder_vary.json`
is kept because the negative result is itself the reason the design was changed.
**What a client does wrong:** a GUI that pairs `time` with the time control it sent sees the engine
"spend" the whole ponder wait out of its own clock — a 6 s think on a 1 s budget after a 5 s ponder —
and its time-management display, `nps` display and any "time trouble" warning fire wrongly. This
is the same defect the ponder audit found; it is *also* a defect in the `time` field itself, which
is the framing that was missing.

### `pv` — conformant on the paths where a pv exists

The contract a client can rely on is the final line's `pv[0] == bestmove`, not every line's — deeper
iterations legitimately change the best move. Tested that way:

| case | final `pv[0]` == bestmove | illegal pv moves | empty final pv |
|---|---|---|---|
| startpos, kiwipete, rook ending, italian, mate-in-2, black to move, black down a rook, french | **8/8 yes** | 0 | no |
| MultiPV 3, startpos and kiwipete | **2/2 yes** | 0 | no |
| aborted searches, 7 runs (4 startpos, 3 italian) | **7/7 yes** | 0 | no |

Every pv on every line — 17 cases, several hundred moves — was replayed through python-chess from
the position given: **zero illegal moves**. Intermediate-depth disagreements (1 to 14 per case) are
normal iterative-deepening behaviour and are counted separately rather than scored as failures.

The bail is the known exception: `pv` absent-to-empty on every line, which §1b already covers and
this audit does not re-report.

**What a client does wrong:** nothing, on searching paths. The empty-pv hazard is the §1b one.

### `info string` — two variants that collide with real fields

Free text, so no definition to violate. But two are readable as data:

- **`info string softnodes nodes 259405`** contains the token pair `nodes 259405`. A client that
  regexes `nodes (\d+)` from any line beginning `info` — a common shortcut — picks up a total that
  differs from the last depth line by 118,079 nodes at MultiPV 3. This is the mechanism behind the
  "two totals" finding above.
- **`info string searchmoves restriction has no legal root moves`** is emitted with **0 nodes and no
  depth line**, alongside `bestmove 0000`. Correct per §1b, but a client waiting for depth output
  deadlocks here exactly as it does on the book path.

The other variants (`invalid FEN`, `illegal move`, `book move`, `bench`, `TmNodeShare`,
`TmFinishIteration`, `eval`, loader messages) are diagnostics that do not shadow a field. Note
`TmNodeShare` and `TmFinishIteration` are **off by default** (`tune::TmNodeShare = false`,
`tune::TmFinishIteration = false`), so they are unreachable in the shipped configuration — I did not
test them on the wire and say so rather than implying coverage.

---

## Method, controls, and what a null here would have meant

Every checker was planted with a deliberate fault before its clean run was trusted
(`scripts/controls.py`): the `seldepth ≥ depth` check, the `nps` arithmetic check, the `hashfull`
range check, the score-sign check, the node-monotonicity check, the multipv-contiguity check and
the time-vs-budget check each **fired on its synthetic fault and passed its clean control**. Output:

```
seldepth >= depth            clean=False fault=True  FIRES
nps == nodes*1000/time       clean=False fault=True  FIRES
0 <= hashfull <= 1000        clean=False fault=True  FIRES
White-up score is positive   clean=False fault=True  FIRES
nodes non-decreasing         clean=False fault=True  FIRES
multipv 1..n                 clean=False fault=True  FIRES
time <= budget               clean=False fault=True  FIRES
```

The abort-revision test was only trusted after an A/A control on the same position and stop time
reproduced depth, score and pv exactly, and after the same test returned **0 hits** on a position
where the pv head does not change mid-iteration (kiwipete). A test that finds its signature
everywhere would have been a test of the harness.

Every fixture was validated in python-chess **and** checked for an `info string invalid FEN`
refusal on the wire. One fixture I first wrote was illegal (`6k1/6Q1/6K1/… w`) and the engine
refused it — the run reported a plausible search of the *previous* position, which is exactly the
"refused FEN manufactures a pass" trap. That reading was discarded and the fixture replaced.

**A null that is a result:** `score`, `nps` arithmetic and `pv` are clean. These are fields where a
plausible defect existed and does not. `seldepth`'s ordering invariant is *unfalsifiable*, which is
stated as such rather than reported as a pass.

---

## What is left untested, and why

- **`seldepth` truth beyond ordering.** There is no wire-observable quantity that distinguishes a
  genuine qsearch depth from a fabricated one, other than the bail case. Comparing against an
  independently instrumented build would be a source change, which this audit does not make.
- **`TmNodeShare` / `TmFinishIteration` `info string` lines.** Both tuning flags default to false.
  I read the code paths but did not force the flags on, because enabling them changes search
  behaviour and would make the rest of this audit's pins non-comparable in the same binary.
- **`hashfull` at Hash 2048 with multi-threaded fill.** The sampling window is the first 1,000
  clusters, so a table large enough to make that sample unrepresentative is untested. The claim
  here is about the generation filter, which is table-size independent.
- **`nodes` under Threads > 1 against an independent count.** No independent per-thread count exists
  on the wire, so the Threads 1 exactness is the only absolute anchor; Threads 2/4 are tested for
  monotonicity only.
- **`score` at the mate-score boundary.** The `MateInMaxPly` transition and the leaf draw rule's
  mate band (`H > 100 - p`) are a search-correctness topic, already reported, not a formatting
  topic. I checked formatting and sign, not the boundary's correctness.
- **The book path's `multipv`** cannot be tested for contiguity because there are no lines at all;
  that is reported as an absence, not as a measured value.
- **`len(pv) >= depth` as a violation.** Tested and **rejected**: a clean `go depth 20` produces a
  completed depth-16 line with a 15-ply pv, so short pvs are legitimate and this cannot serve as a
  symptom check. The owner's pv-length observation is evidence only because it is on the final line
  of an aborted search that never completed, not because shortness proves anything on its own.
- **The deliverable's own git hygiene.** This repo blocks branch deletion, so if a temporary branch
  were created for the tree swap it could not be removed. **No temporary branch was created** — the
  swap was done entirely with `mktemp` index files outside `.git`, a `commit-tree`, and a plain
  fast-forward push, so there is nothing left behind to clean up. The one unreachable object that
  remains is the *superseded* tree from commit `18990db73` (the ~13,327-file one); it is still
  reachable through this branch's ancestry and cannot be deleted without a force-push, which the
  repo blocks. That is stated rather than claimed clean.

---

## Evidence index

All under `evidence/`, each carrying `settings` with build, base commit, threads, hash and pins.

| file | what it holds |
|---|---|
| `depth_bail.json` | bail lines at `go depth 10` and on a stalemate root; python-chess stalemate cross-check |
| `depth_abort_corpus.json` | 10 positions × 10 stop times; the proven `depth 22 / cp 112` violation |
| `depth_abort_repeat.json` | fine sweep on `sharp-attack`; 8 instances of the revision line |
| `depth_abort_decisive.json` | A/A control, reference ladder to depth 22, per-stop attribution |
| `seldepth.json` | seldepth vs depth and pv length across 5 positions incl. the bail |
| `multipv.json` | MultiPV 1–4 contiguity; bail and book exceptions |
| `score_relativity.json` | same board both sides, mirror, mate ±2, mate 0 at checkmate |
| `nodes_bench.json` | 312,866 reproduced; 343,222 control proving the setup matters |
| `nodes_multipv.json` | per-depth node lists at MultiPV 1–4; softnodes vs depth-line totals |
| `nodes_threads.json` | Threads 1/2/4 monotonicity; MultiPV drop rates |
| `nps_zero.json` | `nps 0` at `time 0` with up to 1,001 nodes on the line |
| `hashfull_generation.json` | the four-run warm/cold table with both proofs |
| `hashfull_multipv.json` | per-line hashfull at MultiPV 1–4 vs the MultiPV 1 reference |
| `hashfull_bounds.json` | 0–1000 range at Hash 1, 32, 64 |
| `time_during_ponder.json` | `time` > 0 while the budget clock is pinned at 0 |
| `time_origin.json` | go-infinite control and the discarded vary-the-wait design |
| `time_ponder_vary.json` | the negative result that caused that design to be withdrawn |
| `time_small.json` | movetime 1/5/20/50 and `go depth 5` |
| `pv_contract.json` | final-line `pv[0] == bestmove` and python-chess legality, 17 cases |
| `noinfo.json` | book, `go nodes 0`, empty clock reserve, and their `info` shapes |
| `monotonicity.json` | 4 runs × Threads 1/2/4, node and time drops |

Scripts: `uci.py` (driver + parser), `fixtures.py` (validation helpers), `probe.py`,
`probe_depth_completed.py`, `probe_depth_abort_decisive.py`, `probe_depth_corpus.py`,
`probe_extra.py`, `probe_nodes_pv.py`, `probe_nodes_bench.py`, `probe_nodes_multipv.py`,
`probe_targeted.py`, `probe_time_vary.py`, `probe_time_origin.py`,
`probe_time_during_ponder.py`, `probe_hashfull_generation.py`, `probe_monotonicity.py`,
`probe_pv_contract.py`, `controls.py`.

---

## Appendix: why the PR first read as ~13,327 files, and how it was fixed

Not an audit finding, recorded because it made the deliverable hard to review.

`main` **is** an ancestor of the audit base `6b98f217` — the audit base is 328 commits *ahead* of
it. Branching at the audit base therefore gave the branch a tree containing the whole
`forge-combo29` engine, and a PR against `main` rendered all of it as added:

| | files in PR |
|---|---|
| PR as first pushed (`18990db73`) | **13,327** |
| after the tree swap (`97c9025ab`) | **47** |

The fix is a normal commit whose **tree** is `main`'s tree plus only this seat's 47 paths. It was
built with a throwaway index kept outside `.git`, so the real checkout was never disturbed:

```
IDX=$(mktemp -u /tmp/swapidx.XXXXXX)
GIT_INDEX_FILE=$IDX git read-tree origin/main
# for each path under forge-combo29/swarm/infofields/:
GIT_INDEX_FILE=$IDX git update-index --add --cacheinfo <mode>,<blob>,<path>
TREE=$(GIT_INDEX_FILE=$IDX git write-tree)
git commit-tree $TREE -p <current tip> -m ...
git push origin <new sha>:refs/heads/swarm/infofields      # plain fast-forward, never --force
```

`GIT_INDEX_FILE` was set **per-command and never exported**: it persists in a shell session, and the
next `git status` in the real checkout would then read the swap index and report thousands of staged
deletions — at which point a `git checkout .` or `reset --hard` would destroy the branch. The
variable was verified unset (`GIT_INDEX_FILE=[<unset>]`) and the real checkout verified clean
before the push.

Safety checks run before pushing:

- `git ls-tree -r` over the 47 paths is **byte-identical** between `18990db73` and the new tree —
  same modes, same blob hashes, so no content changed in the swap;
- the tree diff against `origin/main` is **exactly 47 files**, **none** outside
  `forge-combo29/swarm/infofields/`, and **zero deletions**;
- `git merge-base origin/main <new tip>` is `origin/main`'s own sha;
- the push reported `18990db73..97c9025ab` — a fast-forward, so no history was rewritten and every
  earlier commit remains an ancestor.

One file was deliberately dropped: the root `.gitignore` added in `18990db73` sat outside the
deliverable folder. `forge-combo29/swarm/infofields/.gitignore` covers the same patterns
(`build/`, `__pycache__/`, `*.pyc`) for this seat.

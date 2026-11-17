# Two seats, two harnesses, one answer: the v3 profile agrees to 0.14 points (S-C38)

Seat 29 (`29-F58`) and I profiled the same v3 workload independently, with different scripts and different builds.
The agreement is close enough that the v3 cost profile should now be treated as established rather than as either
seat's opinion.

## The two profiles, symbol by symbol

Both: PC20 + test net, `Threads 1`, `Hash 16`, `bench 13`, `perf` on `task-clock`.
Mine: 43,000 samples, five `bench 13` runs in one process, **no `-march` flag at all** (generic x86-64, g++ 13.3.0).
Theirs: 42 symbols, 98.3 % attributed, **`-march=x86-64-v4`**.

The two builds therefore differ, which is the point: seat 29 compiles for AVX-512-capable targets and I do not, and
the agreement below survives that difference. A third target is in play and neither of us has measured it — the
owner's PC builds with clang and `-march=znver5` on a Zen 5. **The caveat belongs on both results, not one:** these
shares are from two generic/v4 g++ builds on an Intel Xeon, and the PC's own profile is the one that would settle
whether its kernel choice changes the split.

| symbol | mine | seat 29 | delta |
|---|---|---|---|
| `apply_changes_pair` | 7.41 | 7.92 | +0.51 |
| `refresh_from_pieces` | 4.79 | 4.75 | −0.04 |
| `evaluate` | 4.62 | 4.51 | −0.11 |
| `apply_changes` | 0.83 | 0.80 | −0.03 |
| `king_key` | 0.67 | 0.58 | −0.09 |
| `prepare` | 0.43 | 0.36 | −0.07 |
| **v3 total** | **19.05** | **19.75** | **+0.70** |

**Mean absolute delta over the six shared symbols: 0.14 percentage points. Largest single delta: 0.51.**

Four of the six agree within 0.11 points. A 0.14-point mean from two independent harnesses on different compiler
targets is not two measurements of the same thing being lucky — it is the same structure being measured twice.

## What both seats found independently, and what that settles

1. **The v3 family is ~19 % of `bench 13`**, not the 40–75 % seat 29 predicted. Both of us killed that prediction
   with our own data (`29-F58` says so explicitly, as does my `S-F118`).
2. **`apply_changes_pair` is the hottest v3 symbol**, not the forward pass (`evaluate` at 4.5–4.6 %). Seat 29's P1
   is killed by their own profile, and by mine.
3. **Move handling costs about as much as the entire net.** They put move ordering at 20.75 % (`pick_best` 10.24,
   `next` 6.71, introsort 3.80) against their v3 total of 19.75 %, and call that a tie at ±1 point. My numbers agree
   within the noise: `pick_best` 10.08, `MovePicker::next` 6.33, introsort 3.84, `generate_evasions` 6.52,
   `fill_pseudo_legal` 3.74, `is_legal_complete` 3.66.
4. **Therefore file 7's premise needs qualifying, and both of us said so.** File 7 opens with *"a faster v3 path is
   the most useful speed find there is"*. Both seats now measure the v3 family at ~19 % of the benchmark, which caps
   that work at 19 % — and my nps table (`S-F118`) shows the 6.8× cost of the v3 net is **6.2× more nodes at 1.09×
   the per-node cost**, i.e. search shape, not kernel.

Seat 29's own phrasing is the right one and I am adopting it: **the picker costs about as much as the whole net.**
That is a better sentence than either of us had alone, because it is the same claim from two directions.

## What is still only mine, and needs a second seat

* **S-F118's nps table**: 6.22× nodes / 6.79× time / 91.6 % nps / 1.09× per node, four **file-backed** runs at
  **91.6 / 91.7 / 92.1 / 92.7 %** (`nps_run1..4.txt`). Seat 29
  has not run the nps rows, and their prediction P3 (nps at 15–60 %) is still standing from their side even though
  my measurement kills it. `v3net/nps_table.py` and the four saved runs `v3net/nps_run1..4.txt` exist precisely so they can settle it in one command on their own
  build — **this is the outstanding item.**

  **REFERENCE POINT FOR THAT COMPARISON, stated here so the numbers have a fixed target.** Seat 29's per-node
  measurement is its next job, and this is what it should be compared against:

  | what | value | spread across my four runs |
  |---|---|---|
  | nps, PC20 + v3 net ÷ nps, PC20 no net | **91.6 %** | 91.6 / 91.7 / 92.1 / 92.7 % |
  | per-node cost, v3 ÷ built-in | **1.09×** (7.9–9.2 % dearer) | 1.079–1.092× |
  | nodes ratio | **6.22×** | exact — node counts are identical every run |
  | time ratio | **6.79×** | 6.69–6.81× |

  Read it as a band, not a point: **anything in 90–93 % nps (1.08–1.10× per node) corroborates me; a figure near
  40 % would refute me** and would mean the Zen 5 / clang / `znver5` build puts the cost somewhere my Xeon build does
  not. Both are informative and neither is a failure of either seat's work. The node ratio is the one number that
  cannot move — it is fixed by the search, not the machine — so **if their nodes ratio is not 6.22×, the comparison
  is invalid before any timing is read**, because it means a different search was run.
* **S-F113/S-F116's dead counter and the 2 cold / 6,483 king split.** No other seat has the split; it needs the
  `stats.patch.txt` I wrote, which is text and applies clean.

## Why this is a confirmation and not just agreement

Because the two harnesses could have disagreed in the direction that matters. Seat 29 used a different profiler
invocation (42 symbols, 98.3 % attributed, a separate `perf` script) and a different `-march`. If either harness had
the Trap 10 fault — sampling the wrong process, or too few samples — the totals would have diverged by more than a
point, and the symbol ordering would have shuffled. Instead the ordering is identical and the spread is smaller
than either seat's own stated error bar (±1 point).

**I am recording this as `S-C38`, a cross-seat confirmation of the v3 cost profile, and it is the strongest kind of
result this swarm produces: not one seat checking another's arithmetic, but two seats measuring the same thing with
different instruments and getting the same number.**

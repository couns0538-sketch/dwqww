# PREDICTION — soak seat (committed before the first measuring command)

Seat area: single-process soak / memory stability. Build: `6b98f217`, g++ 13.3.0,
`-DFORGE_MARCH=x86-64-v4`. Engine sha256 recorded in `evidence/meta/`.

Each prediction carries the observation that would KILL it. Written and committed before
any soak run. Not edited afterwards.

## P1 — RSS over 5,000 `go depth 12` searches, one process, Hash 32, Threads 1

- Shape: the RSS curve rises during the **first ~200 searches** (lazy initialisation and the
  evaluator caches filling) by **0 to 10 MB**, then is flat.
- Plateau (mean of searches 4000–5000): **≤ 70 MB** RSS, i.e. **≤ 27 MB above the
  post-handshake baseline** of a Hash-32 process.
- Slope over searches 1000→5000: **< 2 MB per 1,000 searches**.
- **KILLED IF**: a sustained positive slope **≥ 20 MB per 1,000 searches** over the last
  4,000 searches (that would be ≥ 80 MB of unbounded growth), or any plateau above
  120 MB at Hash 32.

## P2 — RSS tracks the `Hash` option

- RSS(after 50 depth-12 searches) minus RSS(Hash 1, same protocol) ≈ Hash MB, within
  **±15 % and ±8 MB** for Hash 16 / 64 / 256 / 1024.
- **KILLED IF**: any of the four is off by more than 25 %, or the relationship is not
  monotone in Hash.

## P2b — the "second allocation" at Hash 256 + MultiPV

- The report's figure is **105.9 ms**, a time-to-first-`info` number, and the assignment
  carries it as "~105 MB". My reading of `search.cpp:2384-2390`: the alternate table is
  `std::make_unique<SharedSearchState>(hash_mb)` with `hash_mb` recomputed **from the main
  table's cluster count**, i.e. the SAME size as the main table — ~256 MB at Hash 256, not
  105 MB.
- Prediction: peak RSS during a MultiPV-2 search at Hash 256 exceeds the MultiPV-1 peak by
  **≈ 256 MB (200–300 MB acceptable)**; the allocation is a `unique_ptr` owned by the search
  frame and is **freed at the end of the search**, so post-search RSS returns to the
  MultiPV-1 level within **8 MB**.
- **KILLED IF**: the delta is ~105 MB (the assignment's figure is the real size), or if RSS
  does not return after the search (that would be a leak, not a cache).

## P3 — 5,000 × (`ucinewgame` / `Clear Hash`)

- Both are memset-of-the-table plus cache clears; neither allocates. RSS after 5,000 clears
  is **within 4 MB** of the RSS before the loop, whichever of the two is used.
- **KILLED IF**: a net rise **> 10 MB** across 5,000 clears of either kind, or any
  difference in slope between `ucinewgame` and `Clear Hash` larger than 5 MB.

## P4 — 1,000 MultiPV-4 searches at Hash 64

- The per-search alternate table (≈64 MB at Hash 64) is allocated and freed 3 times per
  depth iteration, so RSS oscillates but does not ratchet. Slope over the run
  **< 5 MB per 1,000 searches**; plateau ≤ 40 MB above the MultiPV-1 equivalent.
- **KILLED IF**: RSS grows by **> 30 MB** over the 1,000 searches (that is one alternate
  table's worth not being freed), or if it grows monotonically with no plateau.

## P5 — `ulimit -v` just above the working set

- Below the cliff the process **dies** (allocation failure → `std::bad_alloc` → abort or a
  nonzero exit); above it every answer is **byte-identical** to the unconstrained run.
- Prediction: **no middle band in which answers change but the process survives**. If a
  middle band exists, that refutes the prior work and is the headline.
- **KILLED IF**: any cap that survives produces a different `bestmove` or score than the
  unconstrained run.

## P6 — ASan + UBSan, `detect_leaks=1`

- Proven live by `nm -C | grep -c __asan_` > 0 and by a planted heap over-read on a scratch
  copy that the same runner reports. Prediction: **no leaks** at exit (all allocations are
  `unique_ptr`-owned); any report will be a still-reachable static, not a leak.
- **KILLED IF**: the planted fault is not reported (then the run proves nothing and I say
  so rather than reporting "0 leaks").

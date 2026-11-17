# forge-combo29 soak — memory stability of one long-lived process

Audit base commit `6b98f217` ("Checkpoint standalone NNUE v3 work and evidence"),
folder `forge-combo29`. Build: g++ 13.3.0, `-DFORGE_MARCH=x86-64-v4`, `-O3 -ffp-contract=off
-fno-fast-math`. Engine `id name Chess Engine Forge 6.4.24 candidate`, sha256
`e06310ec…b316a83`. 4 CPUs, no swap, 16 GB.

## The answer in three lines

1. **The engine does not leak.** 5,000 depth-12 searches in one process move RSS by
   **+1.5 MB total and 0.000 MB per 1,000 searches** over searches 1,000–5,000; the value is
   constant to the last sample. The plateau at Hash 32 is **42.1 MB**.
2. **Memory is the table, exactly.** RSS tracks the `Hash` option to within **0.1 %** at
   16 / 64 / 256 / 1024 MB. Every non-table byte is a constant **10.1 MB**, the same at all
   five Hash values.
3. **The MultiPV alternate table is real, is the SAME SIZE as the main table, and is freed.**
   At Hash 256 + MultiPV 2 the process peaks at **259.6 MB above** its MultiPV-1 peak and
   returns within **+3.6 MB** after `bestmove`.

Verdict: **soak-clean.** No unbounded growth in any of the six measurements. The one thing
that changes an answer under pressure is nothing: no cap produced a different move, score or
node count — the process dies instead.

## How sure

High for the RSS verdicts: the curves are the raw output of a committed script, the runs
are 5,000 and 1,000 searches long, and the flat result is flat across every sample rather
than on average. High for the Hash relation: four arms land within 0.1 % of the advertised
size and the residual is constant to 0.1 MB. High for the sanitizer negative: the detector
was shown to fire on a planted fault through the same runner (0 / 0 / 4 lines).
**Not established**: no run exceeds ~5 minutes of engine time or 5,000 searches, so this is
not evidence about multi-day uptime beyond the fact that nothing is accumulating; and no
arm used more than one thread, so per-thread worker memory at `Threads 8` is unmeasured.

## Honesty pins, on the binary these measurements used

Fresh process per line, raw output in `evidence/meta/`:

| pin | expected | measured |
|---|---|---|
| bench 11 | 312,866 | **312,866** |
| bench 13 | 862,329 | **862,329** |
| bench 16 | 3,024,920 | **3,024,920** |
| perft 5 | 4,865,609 | **4,865,609** |

The ASan+UBSan build reproduces all four as well (sha256 `a30da82c…b5defdc`), which is what
makes its leak result admissible.

---

## 1. RSS over 5,000 searches in one process

5,000 × `go depth 12`, Hash 32, Threads 1, `OwnBook false`, positions drawn from a fixed
shuffle over 3,095 varied positions (curated endgames, middlegames and openings plus 120
random legal games sampled every 7 plies), RSS sampled every 50 searches.

```
sample  search   rss_kB   rss_MB
     0       0    41572     40.6     <- after handshake, before any search
     1       1    43112     42.1     <- after the FIRST search
     3       3    43116     42.1
    10      10    43116     42.1
   500     500    43116     42.1
  1000    1000    43116     42.1
  1500    1500    43116     42.1
  2000    2000    43116     42.1
  2500    2500    43116     42.1
  3000    3000    43116     42.1
  3500    3500    43116     42.1
  4000    4000    43116     42.1
  4500    4500    43116     42.1
  5000    5000    43116     42.1
```

- **Plateau: 42.1 MB (43,116 kB).** It is reached on the **first** search, not after a ramp.
- **Slope over searches 1,000–5,000: +0.000 MB per 1,000 searches** (least squares on the
  sampled points, in MB).
- Total change over the whole run: **+1,544 kB**, all of it in the first search (the engine's
  working set — evaluator cache, histories, stack — is touched the first time it searches).
- **3 distinct values in 111 samples**: 41,572 / 43,112 / 43,116. A 4 kB granularity wobble
  on search 1, then nothing.
- 5000 searches logged, **0 with a missing `info depth` line**, 10 zero-node searches (all
  genuine drawn-root bails — bare kings and mutual-zugzwang endgames in the set, which emit
  a full `info` ladder and `cp 0`), 4,991 of 5,000 with a non-null `bestmove`, 482,665,840
  nodes total, 284.9 s.

**This is a plateau, not a slow climb.** The thing a 100-search test cannot see — because it
would finish inside the first-search ramp and report the plateau as if it were the start —
is that there is no ramp to miss.

### Bounded or unbounded?

Neither: it is **flat**. The distinction the assignment asks for (a cache filling vs a leak)
would show as a positive slope that either stops or does not. Here the slope is zero from
search 50 onward, so there is no filling phase to attribute.

## 2. RSS tracks the `Hash` option

40 depth-10 searches per arm, each arm a fresh process, RSS read after the run:

```
Hash   RSS_kB   RSS_MB   over_hash1_MB   (RSS - Hash) MB
   1    11372     11.1            0.0            10.1
  16    26720     26.1           15.0            10.1
  64    75876     74.1           63.0            10.1
 256   272476    266.1          255.0            10.1
1024  1058924   1034.1         1023.0            10.1

marginal cost vs Hash 1:
  Hash   16: 15.0 MB vs  15 MB expected  (-0.1 %)
  Hash   64: 63.0 MB vs  63 MB expected  (-0.0 %)
  Hash  256: 255.0 MB vs 255 MB expected (-0.0 %)
  Hash 1024: 1023.0 MB vs 1023 MB expected (+0.0 %)
```

The advertised size is exact, and the **non-table memory is a constant 10.1 MB** at every
Hash value — the engine has no growing resident component beside the table.

### The "~105 MB alternate table" is 105.9 MILLISECONDS

The report's figure at `findings §3` is **time-to-first-`info`: 1.4 ms at MPV 1 versus
105.9 ms at MPV 2** at Hash 256. It is a latency measurement. The alternate table is not
105 MB, and the source says why:

- `search.cpp:2385-2386` — `hash_mb = max(1, shared_.tt.cluster_count() * sizeof(TTCluster) / (1024*1024))`
- `search.cpp:362-370` — `resize` sets `new_count = bytes / sizeof(TTCluster)` with
  `bytes = mb * 1 MiB`
- `search.hpp:126` — `static_assert(sizeof(TTCluster) == 64)`

so `cluster_count * 64 / 1 MiB` recovers the main table's own MB. **The alternate table is
the same size as the main one.**

**Measured at Hash 256, MultiPV 2 vs MultiPV 1** (RSS sampled at 2 ms from a thread, so a
table that lives only for the length of one search is visible):

```
Hash MPV  settled_kB  peak_med_kB  after_med_kB   peak-settled MB  after-settled MB
 256   1      270920       272624        272480              1.7              1.5
 256   2      270924       538436        276168            261.2              5.1
 256   4      270960       538432        272644            261.2              1.6
  64   1       74324        76008         75864              1.6              1.5
  64   4       74356       145248         79580             69.2              5.1
```

- Peak delta MPV2 − MPV1 at Hash 256: **259.6 MB**, i.e. one more 256 MB table. Not 105 MB.
- **It is freed**: `after` returns to the MultiPV-1 level, +3.6 MB.
- At Hash 64 the alternate table costs **67.6 MB** (69.2 − 1.6), the same rule.
- MultiPV 4 peaks at the *same* level as MultiPV 2 (538 MB), because `search.cpp:2502` calls
  `alt_shared->tt.clear()` per secondary line and reuses **one** alternate table rather than
  allocating one per line. That is why the per-line cost is clearing work, not memory.

The +5.1 MB `after` figure on some rows is not a leak: those rows are the first searches
after the table is touched, and the value settles (`P4` below shows the same 5.1 MB step and
then a fixed value for 1,000 searches).

### A trap this measurement would have hit blind: `resize` allocates before it frees

`search.cpp:365-366` builds `new_clusters` with `make_unique` and only then assigns over
`clusters_`, so any resize holds **old + new** at once. Measured (peak sampled at 2 ms):

```
from  to   rss_before_kB  peak_during_kB  rss_after_kB   peak - max(from,to) MB
  16  256          25188          286416        270948                   23.7
 256  256         270928          531460        270928                  263.0
 256   16         270968          286928         25208                   24.2
1024   64        1057312         1122616         74272                   72.3
```

**At Hash 256 → 256 the transient peak is 263 MB above the table size** — a `setoption name
Hash` with an unchanged value doubles resident memory for an instant. No soak arm resizes
mid-run (every RSS arm sets Hash once at handshake), so **no search peak reported here is a
resize peak**, and that is checked rather than assumed: `soak5` starts a fresh process per
cap, `soak2` arm A sets Hash only at handshake, and arm R is the only arm that resizes and it
is reported separately for exactly this reason.

Owner-facing: a match runner that re-sends `setoption name Hash` between games at Hash 1024
needs 1024 + 1024 = 2 GB of RSS for the duration of the call, on top of anything else.

## 3. 5,000 × `ucinewgame` and 5,000 × `Clear Hash`

Warm process, Hash 32, then 5,000 clears of each kind, RSS sampled every 100:

```
mode        clears  rss_before  rss_after  delta  p50_ms  p99_ms  total_s  best_after  nodes_after
ucinewgame    5000       43128      43128      0   1.296   1.623     6.49       h5e5        15779
clearhash     5000       43096      43096      0   1.225   1.645     6.19       h5e5        36770
```

- **Both leave RSS exactly where it started** (delta 0 kB; the sampled curve is a single
  value across all 50 samples in both arms — span 0 kB).
- The engine is still usable after 5,000 clears in both cases, and returns the same move.

### On time — my prediction covered RSS only, and it should stay that way

Both arms cost about the same: **p50 1.30 ms vs 1.23 ms**, total 6.49 s vs 6.19 s. The
reason is in the source and it is *not* a difference in allocation:

- `Searcher::clear_hash()` → `shared_.tt.clear()` + `clear_caches()`
- `Searcher::clear()` (`search.cpp:2678-2682`) → `shared_.tt.clear()` + `Worker::clear()`
- **both** call `TranspositionTable::clear()`, which is a full `memset`
  (`search.cpp:372-375`)

so at Hash 32 each call writes 32 MiB, and 5,000 calls is **156 GiB of memory traffic for
either arm**. `Worker::clear()` additionally resets the histories and the evaluator cache
(`search.cpp:1019-1031`) — that is the whole of the difference.

`ucinewgame` is **not** cheaper. Measured at four table sizes, 200 calls per arm:

```
Hash  ucinewgame_p50  clearhash_p50  difference  RSS delta (both arms)
  32          1.384          1.167       0.217  0 kB / 0 kB
  64          2.318          2.215       0.103  0 kB / 0 kB
 256         12.413         12.276       0.137  0 kB / 0 kB
1024         86.308         85.891       0.417  0 kB / 0 kB
```

The two are **equal to within 0.4 ms at every size**, and the difference does not grow with
Hash — so the whole cost is the memset and the history reset is in the noise. Cost is linear
in Hash at an effective 11.6–28.2 GB/s, and **RSS is unchanged by 200 clears at any size**,
which is P3 confirmed a second time at 1024 MB instead of 32 MB.

A match runner that sends `ucinewgame` between games at Hash 1024 pays **~86 ms per game**,
and `Clear Hash` costs the same — there is no cheap reset.

Note that `ucinewgame` also **resets the board to startpos** (`uci.cpp:257-259`), so the
`best_after` search below it searched whatever position was set *after* the last
`ucinewgame`. Both arms end with a `position` + `go`, which is why they show different node
counts (15,779 vs 36,770); that is a difference in what was searched, not in health.

## 4. 1,000 MultiPV-4 searches at Hash 64

```
search   peak_kB   after_kB   cum_nodes
     0     74304      74304            0
     3    145216      79548        93778
   200    145276      79548      5173215
   400    145212      79548      9503672
   600    145184      79548     13781864
   800    145232      79548     17944459
  1000    145212      79548      22068189
```

- **Peak: 145,088–145,276 kB across all 1,000 searches — a spread of 188 kB (0.2 MB).**
  The alternate table is allocated and freed 1,000 times and always lands on the same size.
- **After: a fixed 79,548 kB for the last 750 searches.** The distinct values over the whole
  run are `{75992, 76028, 79548}` — three transient values from the first searches while the
  evaluator cache fills, then one value for the rest. No ratchet.
- Growth in `after` over 1,000 searches: **+3.5 MB, all of it in the first ~250 searches**;
  0 kB over the last 750.
- 22,068,189 nodes, 108.3 s, 0 errors.

`tt.clear()` runs **three times per depth iteration** here (`search.cpp:2502`), so 1,000
MultiPV-4 searches at Hash 64 is roughly 1,000 × (8–10 depths) × 3 × 64 MiB ≈ **1.5–1.8 TB
of memset traffic** (depths vary per position; the bound is computed, not measured) — which is why this arm costs 108 s for 22 M nodes (204 knps) against 5,000
depth-12 searches in 285 s for 483 M nodes (1.7 Mnps). **The expense is bandwidth, and it
does not leak.**

## 5. Failure under a hard `ulimit -v`

Prior work (`findings` §7 trap 3c) says: no middle band, every cap that ran gave 0 of 12
different answers, below the cliff 12 of 12 died. **Confirmed on this build, and the shape is
sharper than "it dies":**

| Hash | lowest cap that completes all 12 | highest cap that dies | cliff − Hash |
|---|---|---|---|
| 8 | 52 MB | 50 MB | **44 MB** |
| 16 | 60 MB | 58 MB | **44 MB** |
| 64 | 108 MB | 106 MB | **44 MB** |
| 256 | 300 MB | 298 MB | **44 MB** |

Bisected in 2 MB steps. **The cliff is `Hash + 44 MB` at every value tested**, and the
Hash 16 / Hash 256 figures reproduce the prior work's 60 MB / 300 MB exactly.

At Hash 32 the sweep from uncapped down to 56 MB gives **18 surviving caps, 5 deaths** (plus the uncapped reference), and:

- **0 of 18 surviving caps produced any difference** in `bestmove`, score or node count.
- Every death is `SIGABRT` (rc −6) with `terminate called after throwing an instance of
  'std::bad_alloc'` on stderr, before any `bestmove`.
- **A kill is the expected shape and that is what happens** — confirmed, not refuted.

### Two instrument corrections, both of which changed the reading

**(a) My first pressure sweep reported "not identical" on 13 of 15 caps, including 512 MB.**
It was wrong. The answer key included the `nps` field, and the engine prints `nps 19` on one
run and `nps 17` on the next for the same nodes and the same score. Re-keyed on
`(bestmove, score token, nodes)` the count is **0 of 19**, and the `nps_only` column above
records how many rows differed in that field alone so the correction is visible rather than
silently applied. **A capped run and an uncapped run are not equally fast; a comparison over
a raw `info` line will always find a difference and it will never be about the search.**

**(b) `ulimit -v` does not cap the number it appears to cap.** A Hash-32 process reports
VmSize 119,004 kB uncapped. Under a cap of 180 MB it still reports 119,004 kB, but at 170 MB
and below it reports **53,464 kB** — 64 MB smaller — while RSS stays at 43 MB and every
answer is unchanged. The engine's virtual size is not its working set: above the threshold a
64 MiB glibc arena reservation succeeds, below it fails and malloc falls back to the main
arena. **So the cliff tracks the touching of memory, not the reservation,** and VmPeak is a
constant `Hash + 147.5 MB` at every Hash value (table above), which is why a cap can sit far
below VmPeak and still work.

That also means a memory budget should be set against **`Hash + 44 MB` per process**, not
against VmPeak. A runner giving this engine 200 MB of address space at Hash 32 is fine; the
same runner at Hash 256 dies at 298 MB and lives at 300 MB.

## 6. ASan + UBSan, `detect_leaks=1`

**The sanitizer is live, proven twice.** `nm -C build-asan/forge`: **35 `__asan_` symbols,
15 `__ubsan_` symbols**. The build reproduces all four honesty pins. LSan works in this
container (a 1,234-byte unfreed malloc is reported — `evidence/meta/lsan_control.txt`).

**The runner is proven able to report**, on three cases so the claim is about the runner and
not one code path — a planted heap over-read behind a command no client sends, built in a
scratch copy and driven by the same reader:

```
clean                rc   0  sanitizer_lines 0  info_depth 12  bestmoves ['f1e2', 'g1f3']
planted_untriggered  rc   0  sanitizer_lines 0  info_depth 12  bestmoves ['f1e2', 'g1f3']
planted_triggered    rc  23  sanitizer_lines 4  info_depth  6  bestmoves ['f1e2']
```

0 clean, **0 with the plant compiled in but not triggered**, 4 when triggered (UBSan signed
overflow at `planted/src/uci.cpp:202`, then ASan `heap-buffer-overflow`). The untriggered
row is the one that makes "0" mean something: it shows the detector does not fire on the
merely-present fault.

**The soak**: 120 searches mixing plain depth-6, MultiPV-3, `ucinewgame` and `Clear Hash`
(171 engine operations), `ASAN_OPTIONS=detect_leaks=1`, engine exits via `quit` so LSan runs:

```
searches 120  kinds {'plain': 120, 'multipv3': 24, 'ucinewgame': 17, 'clearhash': 10}
rc 0  sanitizer_lines 0  zero-node rows 0
```

**No leaks, no UB, no still-reachable report.** 0 bytes on stderr.

### Two harness defects I hit and fixed here — both are §7 traps

1. The first version of the proof fed the engine through `printf | exe`. EOF reaching a
   running search **fabricates `bestmove a2a3` with zero `info depth` lines** (trap 3a), so
   my "clean" and "untriggered" rows recorded `a2a3` and neither was the engine's answer.
   They now go through the same non-blocking reader as the soak and assert `info depth`.
2. The first proof waited for an in-band `planted` line on stdout. **An ASan abort closes
   stdout**, so that wait could only time out — a test that cannot fire. The sanitizer writes
   to stderr by construction; the runner now scans stderr after the process is gone.

Left in the record rather than quietly repaired, because both produced plausible-looking
output: the pipe form reported "0 sanitizer lines" and a legal-looking bestmove.

---

## Prediction reconciliation

`PREDICTION.md` was committed and pushed **before the first measuring command**
(`swarm/soak` commit 1). Every prediction **held**; none was killed. The one I would have got
wrong without the coordinator's source reading is P2b — my prior was "≈256 MB, from the
`cluster_count` expression", which held, but I had written the assignment's 105 MB in the
first draft as the alternative and would have reported a 149 MB discrepancy as a finding.

| id | prediction | measured | result |
|---|---|---|---|
| P1 | slope < 2 MB/1,000; plateau ≤ 70 MB | 0.000 MB/1,000; 42.1 MB | **HELD** |
| P1 | rise ≤ 10 MB in first ~200 searches | +1,544 kB, all in search 1 | **HELD** |
| P2 | Hash 16/64/256/1024 within ±15 % and ±8 MB | −0.1 % / −0.0 % / −0.0 % / +0.0 % | **HELD** |
| P2b | MPV2 − MPV1 peak at Hash 256 = 200–300 MB | 259.6 MB | **HELD** |
| P2b | freed within 8 MB after `bestmove` | +3.6 MB | **HELD** |
| P3 | 5,000 clears within 4 MB, either kind | 0 kB / 0 kB | **HELD** |
| P4 | growth < 30 MB over 1,000 MPV-4 searches | +3.5 MB (0 kB after search 250) | **HELD** |
| P5 | no middle band; survivors byte-identical | 0 of 19 survivors differ | **HELD** |
| P6 | detector provable, no leaks | 0/0/4 lines; 0 leaks | **HELD** |

## Suspicions, not proven

- **`ucinewgame` cost is a full table memset, and nothing batches it.** Measured 86 ms per
  call at Hash 1024 (not an estimate). A runner that sends it between every game pays that
  per game. Not a defect; a cost §3 of the report does not mention.
- **The `resize` transient (old+new) has no guard.** `setoption name Hash` with the *same*
  value still doubles the table. A runner that re-sends its full option block between games
  pays a 2× transient every time. Whether that is worth a `if (new_count == cluster_count_)
  return;` in `resize` is an owner decision, not a leak.
- **Threads > 1 is unmeasured here.** Every arm used Threads 1. Each `Worker` owns histories
  and an evaluator cache, so per-thread resident memory is a constant that would show at
  `Threads 8` but is not measured.
- **Days of uptime is not measured, only 285 s of engine time.** The evidence for "stable for
  days" is the zero slope and the zero sanitizer result, not a multi-day run.

## What I did NOT do

- No run longer than 5,000 searches or ~5 minutes of engine time.
- No multi-threaded arm; no `Threads` sweep.
- No `Hash` resize *during* a long soak (deliberate — it would confound a search peak with a
  resize peak). The resize transient is measured on its own instead.
- No NUMA or cgroup memory-limit test; `ulimit -v` only.
- No TSan run (the assignment asked for ASan+UBSan).
- Did not modify any engine source. The planted fault exists only in a scratch copy under
  `/tmp/soak/planted` and is never committed.

## What I am NOT sure about

- Whether the +3.6 MB `after` residual on MultiPV arms is the alternate table's last page
  not yet returned to the OS, or evaluator-cache growth. It is **bounded** (fixed value over
  750–1,000 searches), so it does not change the verdict, but I did not attribute it.
- The exact allocator boundary (170 MB) is a property of this glibc, not of the engine, and
  would move on a different libc or with `MALLOC_ARENA_MAX` set.

## Times

`evidence/stamps.txt` is the `date -u` log from the working session; the run timings above
come from the harnesses' own monotonic clocks and are pasted from their output files.

## Reproducing

```
scripts/pins.sh <exe> <outdir>                  # the four honesty pins, fresh process each
scripts/gen_positions.py positions_R.fens       # the 3,095-position set (seed 6901)
scripts/soak1.py   --exe <exe> --out <prefix>   # 5,000 searches, RSS every 50
scripts/soak2_hash.py --exe <exe> --out <prefix># Hash arms + resize transient + MultiPV peak
scripts/soak3_clears.py --exe <exe> --out <prefix>
scripts/soak4_mpv.py  --exe <exe> --out <prefix>
scripts/soak5_ulimit.py --exe <exe> --out <prefix>
scripts/soak5b_cliff.py                          # cliff bisect, 4 Hash values
scripts/soak6_asan.py --exe <asan-exe> --out <prefix>
scripts/sanitizer_proof.py                       # 0 / 0 / 4 lines
scripts/analyze.py                               # every number in this report
```

`scripts/analyze.py` reads only `evidence/` and asserts its own row counts; it produces the
same output from its own directory and from `/tmp` (checked; see `evidence/meta/`).

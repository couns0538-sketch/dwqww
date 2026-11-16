# Inside `probe_body` at depth 16: the four-way SCAN takes ~39 %, the cluster index ~33 %, the rest ~28 %

seat 19 · area 9 · build **PC r15** + rdtsc buckets · **Threads 1** · cold (`bench` self-clears, 19-F23).

## 1. The three lines

**What was asked.** Every probe pays the cluster address, the load and the four-way scan. Measure which of those
three dominates, cold, at depth 16. If the load dominates, prefetch/layout is the lever; if the scan dominates,
key comparison order is.

**The answer.** **The scan dominates, and the load is part of it.** At depth 16: **scan 39.4 %**, cluster index
**32.7 %**, everything after the scan **27.9 %** (total ≈102.7 cycles per call, inflated by the timing).
The per-call split is stable between depth 13 and 16 (scan 37.5 / 39.4, index 37.5 / 32.7, after 24.3 / 27.9),
so the ratio is not a depth artifact. **The named target is the four-way key-and-occupancy walk over the
64-byte cluster line — that is where a load stall and four comparisons both live, and it is where the owner
should look first.**

**How sure.** Good on the ratio, poor on the absolute cycles. **`rdtsc` around hot code perturbs exactly what it
measures** — each probe now pays three extra timestamp reads plus counter bookkeeping, so the 102.7 cycles/call
is inflated and must not be quoted as the real cost. The ratio is what survives, and the depth-13/depth-16
agreement is the evidence that it is a property of the code rather than of the instrumentation.

## 2. The numbers

| depth | calls | index | scan | after | per call |
|---|---|---|---|---|---|
| 13 | 861,904 | 37.5 % | **38.2 %** | 24.3 % | 36.9 / 37.5 / 23.9 cyc |
| 16 | 3,021,035 | 32.7 % | **39.4 %** | 27.9 % | 33.6 / 40.5 / 28.6 cyc |

Raw: `pcspeed/parts/result.txt`.

**What each bucket is** (from the instrumentation, `pcspeed/probe_parts.py`):

- **index** — from entry to the cluster address being ready: `cluster_for(key)` (the 128-bit multiply into the
  cluster array) plus the `&cluster - clusters_.get()` address arithmetic.
- **scan** — the four-way loop over `cluster.entries`, testing `entry.key32 == key32 && entry.occupied()`. This
  is where the 64-byte line is **loaded** and four 16-byte records are compared.
- **after** — the generation refresh on a hit, or the miss/replacement walk plus the `snapshot` copy.

## 3. What this means for the owner — the named target

**The scan is the largest single bucket and it contains both the load and the comparisons**, so the split does
not separate them; it does separate the scan from the *address computation*, which was the other candidate.

Combined with what is already measured:

- **Replacement scans are 0.204 % of probes at depth 16** (19-F36), so the miss path inside "after" is
  negligible — the "after" 27.9 % is dominated by the hit-path generation refresh and the snapshot copy.
- **The probe count is exactly 1.003 per node at every depth** (19-F36), so there is no frequency effect to
  exploit; the only lever is per-probe cost.
- **A 16× larger hash changes nothing** (19-F38).

So the levers that remain, in the order this data supports:

1. **Reduce the scan's comparisons.** The loop tests `key32` first and `occupied()` second; `occupied()` is a
   read of `gen_bound` in the *same* 16-byte record, so both come from the one line the scan must load anyway.
   A single 64-byte load plus vector compares of all four `key32` fields at once would turn four serial
   comparisons into one — that is the natural next experiment and it is *exactly* the kind of change the four
   honesty pins will either accept or reject, so it is testable in a few minutes.
2. **Do not chase layout or prefetch for the cluster**: the cluster is one 64-byte line, and it is already
   fetched as a unit by the scan's first access. My earlier prefetch result (19-F10, −8.10 %) is the
   cautionary tale for touching this kernel with cache hints.
3. **Do not chase the index**: 32.7 % is large but it is one multiply and an address computation — there is no
   obvious way to remove it without changing the table's indexing, which changes every node count.

### Suspicions, not proven

- That the scan's 39.4 % is dominated by a **memory stall** on the cluster line rather than by the four
  comparisons. I cannot tell from these buckets: the bucket that contains the load also contains the compares.
  Splitting them would need a load-only bucket around a single `_mm_load_si128`, which the compiler may
  reorder anyway. **This is the honest limit of the measurement.**
- That a vectorised four-way key compare would pay off. That is a hypothesis with a cheap test attached
  (item 1 above), not a result.

## 4. What I did NOT do

- I did not implement the vectorised compare. Job 2/3 taught me that a plausible kernel change needs the paired
  timing protocol (`METHOD_timing_tt.md`) and the four pins, and I would rather hand over a named target with a
  measured ratio than a half-tested patch.
- I did not split load from comparisons inside the scan (see above).
- I did not re-run the rdtsc instrumentation under `perf` to cross-check the cycles/call against the 8.47 % self
  share. Two different instruments disagreeing would be informative; I ran out of the cheap version first.

## 5. Files

`pcspeed/probe_parts.py`, `pcspeed/parts/result.txt`.

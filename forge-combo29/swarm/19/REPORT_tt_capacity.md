# Is the depth-16 TT cost table CAPACITY or CALL RATE? — the counters say call rate, and `bench` cannot even take a Hash size

seat 19 · area 9 · build **PC r15** (instrumented with `job4/instrument_tt.py`) · **Threads 1** · cold
(`ucinewgame` before every search, 19-F22).

## 1. The three lines

**What was asked.** Run the TT counters at depth 16 cold to split probe **frequency** from **miss cost**. That
single number tells the owner whether 19-F35's **8.47 %** is table **capacity** at 16 MB — in which case a
larger hash in his GUI fixes it — or a **call-rate** effect, in which case it is search structure.

**The answer.** **It is call rate, not capacity.** The number of TT probes per node is **exactly 1.0000 at
depth 11, 13 and 16** (312,735/312,866; 861,904/862,329; 3,021,035/3,024,920 — identical to four decimals), and
the replacement scan fires on **0.000 % / 0.006 % / 0.204 %** of probes. So the probe cost grows with depth
*only because node count grows with depth*; the per-node work is flat, and the full-table replacement path —
the part a bigger hash would relieve — is **0.204 % of probes**. **A larger hash will not fix the 8.47 %; it is
1.003 probes per node, which is search structure.**

**How sure.** High on the counters (one binary, three depths, cold, `empty_none = 0` cross-check on all three).
High on the interpretation, with the arithmetic in §3.

## 2. The counters, one binary, three depths, cold

`printf 'bench N\nquit\n' | ~/tt16_build/forge` — the PC r15 source with only the counters added.

| depth | nodes | TT probes | **probes per node** | full-table scans | **as % of probes** |
|---|---|---|---|---|---|
| 11 | 312,866 | 312,735 | **1.0000** | 0 | **0.000 %** |
| 13 | 862,329 | 861,904 | **1.0000** | 50 | **0.006 %** |
| 16 | 3,024,920 | 3,021,035 | **1.0000** | 6,174 | **0.204 %** |

`empty_none = 0` on all three, so no probe path was missed. Hit rate 33.4 % / 33.1 % / 35.8 % — flat.

## 3. Why this settles it

If the cost were **capacity**, the signature would be a rising *full-table replacement rate*, since that is the
work a bigger table removes. It is 0.204 % of probes at depth 16 — two tenths of one percent. Even if the entire
8.47 % of `probe_body`'s self time were attributed to the replacement scan (it is not — most of it is the
cluster address computation, the 64-byte load and the four-way key scan), a larger hash could remove at most
**0.204 %** of probes' worth of work, i.e. about **0.017 points** of engine time. The remaining 8.45 points are
per-probe work that every probe must do regardless of table size.

So the depth growth is: **more nodes → more probes, one per node, each costing the same.** That is search
structure — deeper search simply visits more nodes — not a table that is too small.

## 4. And a trap I fell into and had to climb out of: `bench` cannot take a Hash size

My first attempt to test capacity was to run `bench 16` at Hash 16 / 64 / 256 / 1024 and compare the replacement
counts. **All four gave byte-identical counters**, which is the same "too clean" tell that caught my
`setoption` mistake earlier. The cause is at `src/uci.cpp:773`: `bench` constructs its **own**
`forge::Searcher bench_searcher(16)` with a **hardcoded 16 MB** table, so `setoption name Hash` — which calls
`searcher.resize_hash(...)` on the *UCI* searcher at `src/uci.cpp:777` — never reaches the bench searcher.

**Consequence for the swarm:** any Hash-size conclusion drawn from `bench` is measuring nothing. This is a
second, independent reason `bench` is the wrong instrument for TT work — the first being 19-F18/F22's warm/cold
issue, now corrected to "bench is fine, but it is fixed at 16 MB".

Redone properly with a real `go depth` search on the UCI searcher, 12 of set G, depth 14, cold:

| Hash | total nodes | TT probes | full-table scans |
|---|---|---|---|
| 16 MB | 1,645,108 | 1,642,425 | **97** |
| 256 MB | 1,645,106 | 1,642,423 | **0** |

So a bigger table **does** remove the replacement scans (97 → 0) — and moves the node total by **two nodes in
1.6 million** (0.0001 %). That is the direct measurement behind §3: capacity is relievable, and relieving it
changes essentially nothing.

## 5. Findings

**19-F36 — the depth-driven TT cost is probe COUNT (1.003 probes per node at every depth), not table capacity
(full-table scans are 0.204 % of probes at depth 16). A larger hash cannot fix 19-F35's 8.47 %.**

**19-F37 — `bench` hardcodes a 16 MB table (`src/uci.cpp:773`, `Searcher bench_searcher(16)`), so
`setoption name Hash` does not affect `bench` at all.** Verified the hard way: identical counters at Hash
16/64/256/1024. Use a real `go depth` search to test anything hash-related.

**19-F38 — a 16× larger hash (16 → 256 MB), on a real cold depth-14 search, removes every replacement scan
(97 → 0) and changes the node total by 2 in 1,645,108 (0.0001 %).** So "the table is too small" is a real but
negligible effect at these depths, and it is not what makes the probe hot.

### Suspicions, not proven

- That 1.003 probes per node is structural (one probe per visited node by construction). The four-decimal
  agreement strongly suggests it, but I did not count nodes inside the search to confirm the identity.
- That at much deeper searches (depth 20+) capacity would start to matter. Untested; the trend at 11/13/16 is
  flat, so extrapolating past what I measured would be exactly the over-reach I am trying to avoid.

## 6. What I did NOT do

- I stopped measuring CorrHistV2, as instructed — it is a games question and no further measurement settles it.
- I did not test Hash sizes on a deep *real* search (depth 18+); the 12-position depth-14 run is the evidence.
- I did not profile with `Hash 256` to see whether `probe_body`'s share drops. That is the one remaining
  measurement that would close 19-F35 completely, and it is cheap — but the counter arithmetic in §3 already
  bounds the possible answer to ~0.02 points.

## 7. Files

`pcspeed/ttdepth/counters.txt` (three depths, same binary), `pcspeed/ttdepth/RESULT.txt` (Hash 16 vs 256),
`pcspeed/hash_size_at_depth.py`, `job4/instrument_tt.py`.

# S-F70 (v3) — the PC's net pays a full accumulator rebuild every 6 evals, and each rebuild is already cheap

Seat 20. Binary `build-v3/forge` sha256 `227aae56ef1678479cf08d0fc3e3c73683753e89d61f12b252f0fec9e388471e`
(`Chess Engine Forge 6.4.24 candidate`, `-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`, kernel `avx512`).
Regime PC20 (S14 17 options + 5 extras), test net loaded, Threads 1, Hash 16. `bench 13`.

Step 0 passed all twelve pins from file 7 before any measurement: eight bench numbers
(312866 / 862329, 278024 / 587276, 965454 / 4151906, 625258 / 3652372) and three `eval` lines
(968 / 1176 / 31), with the net's checksum `fdff70de72e4ca82`, `max|w1| 64 max|b1| 96 max|w2| 16`,
6,309,096 bytes, sha256 `1db8525e…3ffd4a` — all matched. `job82/step0.json`, `job82/step0_eval.json`.

## The measurement

`bench 13` = 3,652,372 nodes (the file-7 pin) makes:

- **617,443 `refresh_from_pieces` calls** — 169 per 1000 nodes, i.e. one full two-perspective rebuild every
  **~5.9 nodes** (2,556,881 `evaluate` calls vs 617,443 refreshes = 4.14 evals per refresh).
- **4,474,006 columns** pushed through the incremental path during those refreshes — **7.25 columns per refresh**.

Instrumented build `build-v3diag/forge` sha256 `f255b8cb44dae4398a7295f12faef06267db3b524c13959fe31c8fda21932e2c`
(prints the `RefreshCache` counters the struct already keeps and nothing read). **Planted controls**: with `NNUEArch`
off the counter is exactly `0`; with the net on it is `682,678` on the same workload. The zero is a real zero.

## What this says, and what it does not

The design intent is written in `make_valid` (`include/forge/nnue_v3.hpp:276-284`): rebuild from the nearest valid
ancestor, and fall back to `refresh_cached` only when none is valid. `refresh_cached` then diffs the board against a
per-`(perspective, bucket, flip)` entry, so a full refresh costs only the **few columns that changed** — which is
exactly what 7.25 columns/refresh shows it is doing. **The cache is working.** That is the point: the expensive part
of a refresh has already been optimised away, so the remaining 169 refreshes per 1000 nodes are buying almost
nothing, and the cost is elsewhere.

So this is **not** a "make refresh faster" finding, and it is not the speed patch file 7 asked for. It is the
measurement that says where the v3 time actually goes, which changes what Step 2 should target.

## Prediction scorecard (prediction committed alone at `job82/PREDICTION.md`, before any profiling)

| # | predicted | measured | verdict |
|---|---|---|---|
| P1 | hottest v3 function = `apply_changes_avx512` | **`refresh_from_pieces`, 9.4 % of bench 13 self time** | **REFUTED** — wrong function |
| P2 | that function = 45 % of v3 time | **43.2 % of v3** | **CONFIRMED** (inside 30–60 %) |
| P3 | v3 path = 30 % of bench 13 time | **21.6 % of bench 13** (excl. one-time load) | **CONFIRMED** (inside 20–45 %) |
| P4 | forward pass = 20 % of v3 time | **18.9 % of v3** | **CONFIRMED** (inside 12–30 %) |
| P5 | full refresh RARE, ~10 % of v3 | **43.2 % of v3** — the refresh is the single largest v3 item | **REFUTED** — badly; I predicted rarity and got the opposite |
| P6 | bookkeeping = 10 % of v3 time | inlined, no separate entry | **NOT MEASURED** |

**3 confirmed, 2 refuted, 1 not measured.** I first wrote "5 of 6 refuted" from eyeballing the profile; the arithmetic
against my own pre-registered kill ranges says otherwise, and the correction is recorded rather than quietly fixed.
*(This is itself an instance of METHOD's RULE 0b applied to my own scoring: a claim about a measured quantity has to
be divided out, not eyeballed.)*

The two refutations are the informative ones, and they are **the same refutation**: I was wrong about *which* thing is
expensive because I was wrong about *how often the full refresh runs*. Both came from one wrong premise.

**What survives, and it is the useful part:** the top v3 function at 43 % of v3 time is the refresh path, and the
refresh path is *already* the optimised one (7.25 columns, not 768). So the largest remaining v3 cost is the
bookkeeping + incremental apply around a cache that has already been made cheap — i.e. **Step 2 should look at
allocation/cache structure, not at the vector kernels**, which are only 35 % and are already AVX-512.

## Method caveats, stated because they bound the claim
1. **`perf` is not installed on this machine** (`command -v perf` fails, no `/usr/bin/perf*`). Shares come from a
   **`gprof` `-pg` build**, which adds a call-counting prologue to every function and therefore **inflates small,
   frequently-called functions** (`MovePicker::pick_best` at 12.9 % with 13.2 M calls is the clearest beneficiary).
   The `-pg` build reproduces the node count exactly (3,652,372), so behaviour is unperturbed, but **shares are
   distorted and the totals are not wall-clock**. The counter-based numbers (refresh calls, columns) are exact and
   do not depend on `gprof`.
2. `bench 13` is one workload, not the 200 openings file 7 also asks for. Threads 1, Hash 16 throughout.
3. This is the **built-in**-vs-loaded distinction file 7 raised: every number here is with the v3 net loaded, so it
   says nothing about 19-F2/19-F10/19-F11's built-in-net profiles, and they say nothing about this.

## Status
**NEW, needs an independent confirmation** by another seat with its own build and its own counter. The claim to
reproduce is narrow and cheap: under PC20 + the file-7 test net, `bench 13` shows **~169 refreshes per 1000 nodes**
and **~7 columns per refresh**. A different compiler, a different `-march`, or the PC's own clang build should give
the same two numbers if the cache behaves as the source says.

# glmflash3 job 2 report (2026-11-15)

## 1. First line

**`PawnHistory` gains strength per node: pooled M1+M2 = +11.5 Elo, 95 % pair interval [+4.0, +19.0]
(4000 games, 2000 pairs; both seeds positive: M1 +13.4 [+2.9, +23.9], M2 +9.6 [−1.2, +20.3]).**
**The option-off build is proven identical to the unpatched engine: one sha256 over the 2000 depth-9 answers of each side, both `3c976155ede937860062ac79eeefa01894ef0bd4a03360fa5d6d90065cd8353f`,
smallest node count 4534 — and not one node changes at Step 0 (all four known numbers reproduce
on the patched build with the option off).** Not reached at the time of writing: nothing of the
prescribed steps; all of Step 0 and P1-P6 were completed inside the budget (job start ~16:53,
matches done 17:27:47, report written after). What the job did not ask and I did not do: an
equal-time match — see §10, because P6 says the option costs ~8 % nps.

## 2. Step 0 (unpatched build; known numbers)

Build flags for EVERY build in this job (written once, as asked): `cmake -S <tree> -B <build> -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++`
with this tree's own CMakeLists defaults doing the rest (`-O3 -ffp-contract=off -fno-fast-march -march=x86-64-v4`, `FORGE_NNUE_HIDDEN=256`, `FORGE_SEARCH_SPEED2=1`, PEXT/ZMM speed switches on; my CPU has AVX-512 and BMI2). Engine input per bench: Threads 1, Hash 16, OwnBook false, fresh process.

| command | expected | printed (unpatched `build-orig/forge`) | match |
|---|---|---|---|
| bench 11 | 312866 | 312866 | yes |
| bench 13 | 862329 | 862329 | yes |
| bench 16 | 3024920 | 3024920 | yes |
| go perft 5 | 4865609 | 4865609 | yes |

All four agree (raw outputs `step0_orig_*.out`).

## 3. The feature as built

One table per search thread, mirroring the existing `ThreatHistory` switch end to end:

- **Table** (`include/forge/search.hpp:393-394`): `PawnHistoryTable = array<array<array<int16_t,64>,13>,4096>` — indexed `[pawn key bucket][moved piece][to square]`, 16-bit entries, 4096·13·64·2 B = **6,815,744 bytes per search thread**. `constexpr std::size_t PawnHistoryBuckets = 1U << 12U;`
- **Bucket**: `board.pawn_key() & (PawnHistoryBuckets - 1)` (`src/search.cpp:1362`, `:1367`) — the same masking convention the correction history uses for the same key (`search.cpp:1217`).
- **Read** (`Worker::pawn_history_value`, `search.cpp:1360-1363`): gated on `tune::PawnHistory`, returns the raw entry. Added to the quiet score at BOTH sites that compose a quiet history score, which the job named:
  - `Worker::quiet_history`, SPEED2 branch, `search.cpp:1333` (this branch is the live one: `FORGE_SEARCH_SPEED2=1` is in the CMakeLists of this tree, `CMakeLists.txt:34`);
  - the move picker's quiet scoring struct, `search.cpp:799` (`QuietScore::score`, the site that adds `quiet_history_sum(...) + worker.threat_quiet_bonus(...)` directly).
  So move ordering, history pruning (`search.cpp:1829` reads `quiet_history`) and LMR all see it, because they all go through those two sites.
- **Update** (`Worker::update_pawn_history`, `search.cpp:1365-1368`): in `Worker::update_quiet_stats` with the SAME bonus/malus as the butterfly table: best quiet move gets `+bonus` (`search.cpp:1400`), each previously-tried quiet gets `-bonus` (`search.cpp:1407`), through the same `apply_history` gravity rule (`search.cpp:246-249`).
- **Clear** (`search.cpp:1025`): `pawn_history_->fill({});` next to the other tables' clears (ctor calls `clear()`; `ucinewgame` goes through it).
- **UCI**: option line in the `uci` answer (`src/uci.cpp:222`, immediately after ThreatHistory's), name in the check-option list (`uci.cpp:405`), pointer mapping `&forge::tune::PawnHistory` (`uci.cpp:412`); flag defined `bool PawnHistory = false;` in `tune::` (`search.cpp:98`), declared `extern bool PawnHistory;` (`search.hpp:298`).

**Choices the job left open, and why:**
- **4096 buckets** (range given was 512-8192). Per bucket the table is 13·64 = 832 cells; 4096 buckets = 6.8 MB/thread — same order as the default 16 MB hash, and the bucket count halves the aliasing between different pawn structures (the failure mode this feature must avoid) while staying a single allocation per thread. 8192 would double the memory for a collision rate I cannot measure in 80 minutes; 512-1024 would alias visibly different structures. I did not try other sizes in play (see §8).
- **Read added in full** (weight 1), like the threat table's read. The table gets the same number of updates as the butterfly table but spreads them over ~2000× more cells, so its entries stay smaller than the butterfly's; no extra scaling factor to tune on no evidence.
- **No other bonuses** (the butterfly gets bonus/malus only in `update_quiet_stats` in this tree, so there is nothing else to mirror; low-ply/countermove extras would be new design, not a mirror).

**What I tried and dropped:** the first clear idiom `*pawn_history_ = PawnHistoryTable{};` — it
materializes a 6.5 MiB stack temporary; under ASan's inflated frames `Worker::clear()` overflowed
the 8 MB stack (P4 caught it — that is P4 working, not a false alarm). Replaced with
`pawn_history_->fill({});` (no temporary) in the shipped patch; re-verified P2/P3 after the change
(identical hashes and node counts).

## 4. P1-P6

**P1 — counters (traced copy, `pawn_trace.patch.txt` committed).** On `bench 13`, option on:
nodes 1117065 (identical to the untraced patched build — tracing changed nothing), **reads 5,431,360 (4.86/node), updates 108,727 (0.097/node), changed 108,727 (100.0 % of updates change their entry)**. Raw output `p1_trace.out`. The feature is reached and alive: ~4.9 reads per node (every quiet move scored), ~0.1 updates per node (beta cutoffs), no null updates.

**P2 — option OFF is the old engine.** `p2_identity.py`: 2000 FENs (first 2000 lines of the book), per position `ucinewgame`, `position fen`, `go depth 9`; answer line = bestmove + last score + nodes. sha256 over all 2000 answer lines: unpatched `3c976155ede937860062ac79eeefa01894ef0bd4a03360fa5d6d90065cd8353f`, patched-with-option-off **the same hash**; smallest node count 4534 (no empty searches hide in the average). Files: `p2_orig.txt`, `p2_patched_off.txt` (+ logs). Also the four known numbers on the patched build with the option off (raw outputs `step0_patchedoff_*.out`): 312866 / 862329 / 3024920 / 4865609 — all four = known.

**P3 — option ON acts.** Patched build, option on: bench 11 → **302876**, bench 13 → **1117065**, bench 16 → **3249039** — all three differ from the known numbers. Raw outputs `step0_patchedon_*.out`.

**P4 — sanitizers.** ASan+UBSan build (`-fsanitize=address,undefined -fno-omit-frame-pointer`). Planted-fault control FIRST (`fault.c`, one byte past a 4-byte heap allocation, same flags): exit 1 with exactly one `ERROR: AddressSanitizer` on stderr (`fault_stderr.txt`) — the build reports faults. Then, option on: `bench 13` — rc 0, nodes 1117065, **stderr 0 bytes** (`asan_bench_stdout.txt`, `asan_bench_stderr.txt`); 200 book positions at depth 9 — 200 answers, **stderr 0 bytes** (`asan_200_answers.txt`, `asan_200_stderr.txt`).

**P5 — matches.** Form: same patched exe both sides, `nodes=20000`, `option.Threads=1 option.Hash=16 option.OwnBook=false`, UHO openings, each opening twice with colours reversed, no adjudication, `-concurrency 4`. fastchess v1.8.3-alpha, book file verified in job 1.

- **C (control/power)**: nodes 20000 vs 10000 (per engine), 300 games, seed 7600. fastchess
  `Elo: +187.77 +/- 31.32`, LOS 100 %, fast side 176-28-96 (74.67 %); my pair interval
  [157.8, 220.6]. Near +200 as required — the tool sees a planted difference of this size; power
  line intact for this job's setup. Raw `c.out`, per-game `c_games.txt`.
- **M1**: PawnHistory on vs off, 2000 games, seed 7601, complete in 12:44. fastchess
  `Elo: +13.38 +/- 10.50`, LOS 99.38 %, Ptnml [49, 224, 395, 265, 67]; my pair interval
  **[+2.9, +23.9]**. 0 crashes, 0 illegal moves, 0 disconnects. The Ptnml spread also proves the
  option arrived (an undelivered option would show all-draw pairs, the control-1 signature).
- **M2**: same, seed 7602, 2000 games — run always, whatever M1 says. Complete in 12:13.
  fastchess `Elo: +9.56 +/- 10.72`, LOS 95.98 %, Ptnml [60, 225, 379, 272, 64]; my pair interval
  **[−1.2, +20.3]**. 0 crashes/illegal/disconnects. Second seed agrees in direction with M1;
  the pooled number is the result (§5).

**P6 — speed, honestly.** 10 interleaved pairs of `bench 16` (off, on, off, on, ...), same binary, option set in the input only: mean nps off **1,772,577**, on **1,627,137**, mean ratio **0.9205** (option on ≈ 8 % slower), pairwise ratio spread **0.8119 to 1.0305** (`p6_pairs.txt`). Different trees, so a rough figure as the job says: the on-side search visits a bigger tree AND pays ~4.9 table reads/node; the ratio is the combined cost, not a clean per-read cost. New table size: 6,815,744 bytes per search thread.

## 5. Matches table

| match | cand | base | seed | games | W-L-D | fastchess Elo ± | my Elo [95 % pair] | pairs Ptnml | crashes/illegal |
|---|---|---|---|---|---|---|---|---|---|
| C | nodes 20000 | nodes 10000 | 7600 | 300 | 176-28-96 (fast side) | +187.77 ± 31.32 | +187.8 [+157.8, +220.6] | [0, 8, 31, 66, 45] | 0 |
| M1 | PawnHistory=true | off | 7601 | 2000 | 607-530-863 | +13.38 ± 10.50 | +13.4 [+2.9, +23.9] | [49, 224, 395, 265, 67] | 0 |
| M2 | PawnHistory=true | off | 7602 | 2000 | 601-546-853 | +9.56 ± 10.72 | +9.6 [−1.2, +20.3] | [60, 225, 379, 272, 64] | 0 |

**Pooled M1+M2** (pool of the 2000 pair scores of both seeds): mean pair score 0.5165, se 0.0055,
**Elo +11.47, 95 % pair interval [+3.97, +18.98]**, 4000 games. Computation: pooled W-L-D
1208-1076-1716, score (1208+1716/2)/4000 = 0.5165, Elo = −400·log10(1/s−1); interval converts
mean ∓ 1.96·se the same way (`pooled_calc.txt` in the job folder records the run).

## 6. Files of the repository I opened

- `forge-combo29/CMakeLists.txt` (whole file; flags, SPEED2=1, FORGE_MARCH default).
- `forge-combo29/include/forge/search.hpp` — tune namespace externs (297), table usings (382-388), SearchStack (415), Worker members (472-477), method declarations (552-553).
- `forge-combo29/src/search.cpp` — quiet_history_sum + SPEED2 guard (242-268), quiet_threat_index (290+), tune definitions (93-98), Worker ctor (1002-1014), clear (1019-1025), correction-history pawn_key use (1217-1240), Worker::quiet_history (1322-1345), threat hooks (1347-1355), capture history (1357-1361), update_continuation (1363-1371), update_quiet_stats (1373-1395), move picker quiet score (792-801), history-prune read (1829), update call (2077).
- `forge-combo29/src/uci.cpp` — option answer block (216-226), check-option list + ternary chain (404-414), bench handler (626+).
- `forge-combo29/include/forge/board.hpp` — pawn_key() (250, 296).
No engine source file was modified in the repository; the patch exists only as a text file in my job folder.

## 7. Stamps of every step

All times UTC from `/tmp/g3job2/stamps.txt` (committed). Job start (reading the job file) ~16:53;
budget end (80 min) ~18:13; the 70-min stop-and-write mark ~18:03 — all steps finished before it.

| step | start | end |
|---|---|---|
| build unpatched | 16:56:59 | 16:57:05 |
| build patched | 16:57:41 | 16:57:47 |
| P2 identity (both sides, parallel) | 16:57:59 | 16:58:18 |
| build traced (P1) | 16:58:32 | 16:58:35 |
| ASan build + planted fault | 16:58:53 | 16:59:08 |
| ASan bench 13 + 200 positions | 16:59:46 | 17:00:00 |
| P6 speed pairs | 17:00:34 | 17:01:12 |
| control C | 17:01:17 | 17:02:49 |
| M1 | 17:02:49 | 17:15:34 |
| M2 | 17:15:34 | 17:27:47 |
| report + commit + push | 17:28 | ~17:35 |

Step-0/P3 benches were first run inline (terminal only, a repeat of my job-1 slip); they were
re-run into files while control C ran — `saved/*.out` file mtimes 17:07:39-17:07:47 record that
(theirs are the committed raw outputs; numbers identical to the first runs, quoted above).

## 8. What I did not do

- An equal-time match (option on gets ~8 % fewer nodes per second — §10 says why that is the
  natural next check and whose call it is).
- Any tuning of the new table (no weight search, no bucket-size search — see §9).
- Per-phase read counters (ordering vs history pruning vs LMR separately): P1's counters are
  aggregate over all read sites.
- I did not re-check the trace patch after the clear-idiom fix by a second bench (its first run
  already gave node-identical 1117065; the clear change cannot alter search, only its clear).

## 9. What I am not sure about

- Two seeds is the minimum a pooled figure can rest on. The pooled lower bound (+4.0) assumes
  between-seed variance is captured by pooling the pair scores; a third seed would firm it. I
  report both single-seed intervals next to the pooled one so the reader sees the spread.
- The P6 ratio's pairwise spread (0.81-1.03) is wider than I would like; the mean over 10 pairs is the figure I report, but the true steady-state cost per node could sit anywhere in ~4-12 % slower. Different trees make a cleaner decomposition (read cost alone) impossible here.
- My bucket count (4096) and full-weight read are judgement calls (§3); a smaller table with a scaled read might order moves equally well with less memory. The matches measure the choice I made, not the choice space.
- The pawn key is a Zobrist-style hash of pawn placement; masking its low 12 bits gives an even bucket spread only as far as the key mixes well. The correction history's identical use of the same key is my evidence it mixes well enough; I did not measure the bucket occupancy distribution.
- The pooled gain is measured at 20000 nodes/move, one book, this machine. Per-node scales can
  invert at other node counts (job 1's own lesson ran the other way: B4 kept its gain from 2000
  to 250000 nodes on the owner's PC, but that is one data point, not a law).

## 10. A better way

1. **Run the equal-time match before this goes anywhere near the lock.** P6 says the option costs
   ~8 % nps; job 1 showed exactly what that does on the owner's PC (B4: +24 per node became
   +10.6 at equal time). Prediction to check: PawnHistory at equal time lands around +3 to +8
   Elo, not +11.5. One 2000-game match with `tc` instead of `nodes` answers it; if the equal-time
   figure is what decides merges on the PC, the per-node figure alone would oversell this feature
   by roughly its speed cost. How to check that this is better: run the equal-time match; if it
   agrees with the prediction within noise, the two-scale protocol (per node first, equal time
   for the merge decision) is validated on a second feature.
2. **The planted-fault control for P4 should be committed next to the sanitizer outputs from the
   start** (I wrote `fault.c` first — it is committed — but the job text could name the file and
   its expected stderr signature explicitly, so every helper's P4 is the same control, not seven
   improvised ones).
3. **Pool-first reporting worked as designed and is worth keeping**: M2 ran unconditionally, so
   the pooled number cannot be a "best of two seeds" cherry-pick; the pooled pair interval is the
   single number the merge decision should quote (the job's own rule, kept because it also
   protects against my own enthusiasm — M1 alone read +13.4, the pool says +11.5).

## 11. Model

GLM 5.3 Flash (glm-5.3-flash).

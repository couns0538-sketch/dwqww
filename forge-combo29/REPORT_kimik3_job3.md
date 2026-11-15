# kimik3 job 3 report — v3 NNUE eval speed, bit-exact (2026-11-15)

1. **Plain answer.** With my seeded net, evaluation is **46% of the estimated cost of a node**
   (CEst; the incremental-update function alone is 27%). My one patch lowers the **whole node** cost by
   **3.54% of instructions and 2.54% of estimated cycles per node** (and 6.4% of branches), and lowers the
   update path itself by 8.1% Ir / 6.0% CEst; every value stayed identical on every oracle I could run
   (O1–O5 below, including a 2,000-position searched comparison and the engine's own per-eval verifier).
   The one wall-clock line is inconclusive (±10% machine noise); the instruction line is 5 orders of
   magnitude above the run-to-run floor.

2. **Step 0 and the net.**
   - Step 0 (built-in net, all builds): `bench 11` = 312866, `bench 13` = 862329, `go perft 5` = 4865609 — all match.
   - With my net: `bench 11` = **6,909,196**, `bench 13` = **15,806,704**, `bench 16` = **120,474,832**
     (scalar, AVX2 and AVX-512 builds agree; these are the numbers every patched build reproduced).
   - Net: `tests_kimik3_job3/make_net.py.txt`, seed 20261115, FORGENN3, exactly 6,309,096 bytes, hidden 512,
     8 king buckets mirrored, 8 output buckets, standalone, qa 255 qb 64, FNV-1a64 checksum 4acb1ad41c42ec0e,
     kernel line prints `eval_scale 1`. First attempt (w1 ±540 like the header suggests) saturated SCReLU on
     88% of inputs and every eval collapsed to a constant, so I regenerated with w1 ±54; that net's evals on
     the first 20 UHO positions are -16,-14,-14,-11,-21,-18,-21,-14,-15,-5,-16,-19,-14,-5,-16,-7,-22,-19,-13,-14
     (mean ≈ -14, spread ≈ ±5; a scale-9 variant gives ±75 cp but 60M-node bench 13, so I kept scale 1).
   - The net file itself is binary and is **not** committed (text-only rule); the generator reproduces it byte-for-byte.

3. **Part A — where the cost sits** (AVX2 build: `-DFORGE_NNUE_V3=1 -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -g`, g++;
   scalar build kept as reference; callgrind --cache-sim=yes --branch-sim=yes).
   - **Repeated-run line (honest): NOT byte-equal.** Two identical runs differ by 14 Ir, 1 Dr, 1 Dw, 1 Bc, 2 Bcm
     out of 37,388,451,744 Ir (floor 4e-8). In job 2 (built-in net) repeats were byte-equal; cause not found
     inside the budget. Deltas I report are ≥ 3%, i.e. 5+ orders of magnitude above this floor.
   - Workload for Part A: `bench 11` with my net = 6,909,196 nodes (NOT bench 13 = 15.8M nodes: one callgrind
     run of bench 11 is ~11.5 min, bench 13 did not fit the 60-minute budget together with Part B; stated plainly).
   - Totals: Ir 37,388,451,744 (**5,411.4/node**), CEst 48,910,578,244 (**7,079.1/node**).
   - Per node (self cost): `apply_changes` (incremental update) 1,501.8 Ir / 2,209.8 CEst = **31.2% of all CEst**,
     called 1.68/node; `evaluate` (output layer) 389.6 Ir/n, 0.795 evaluations/node; `refresh_from_pieces`
     248.7 Ir/n, 0.13 refreshes/node; `static_evaluate_v3` 3.4% CEst; `prepare` 0.53%; `king_key` 0.44%.
     Eval total ≈ **46% of node CEst**. Refresh cache: `refresh_cached` called 8 times in the whole run
     (refreshes are rare; the cache is nearly irrelevant on this workload).
   - Updates computed for positions never evaluated: **≈ 0 by design** — updates are lazy, applied only when
     an evaluation needs the accumulator. (So Fable's first candidate idea is empty on this path.)
   - Inside `apply_changes` (AVX2): the h-loop reloads the change struct every iteration — 259.7 Dr/node of
     per-iteration `c.columns[i]`/`c.adds[i]`/`c.count` reloads (~4.8 reads/iteration; aliasing stops the
     compiler from keeping them in registers; ≈892 Ir/call ≈ 28/iteration vs ~9 a hoisted loop needs).
     Confirmed hottest lines: nnue_v3.cpp 201–205 (the AVX2 update h-loop) = 933 Ir/node, 17% of all Ir.
     The remaining hot-line ids in the .out use compressed file ids my post-hoc parser could not resolve to
     names; raw files `callgrind_partA_run1.out.txt` / `_run2.out.txt` are in evidence for `callgrind_annotate`.
   - search.cpp side: the cost of calling into eval sits inside `static_evaluate_v3` (3.4%) and the
     make/unmake path; nothing there rivals the update loop.

4. **Part B — the patch.** One patch, two techniques, applied identically to all three kernels
   (scalar / AVX2 / AVX-512 in `src/nnue_v3.cpp`, plus the caller in `include/forge/nnue_v3.hpp`):
   - `v3speed_1_nnue_v3_cpp.patch.txt` — (a) hoist `count`/`columns[0..3]`/`adds[0..3]` into locals before the
     h-loop and unroll the change loop as `if (count > i)` blocks (kills the per-iteration struct reloads);
     (b) fuse the two perspective updates into `apply_changes_pair`: one pass over h updates both
     accumulators, called from `replay_ply` when both perspectives keep their king key (the common case);
     per-perspective fallback otherwise. Bit-exact because per-accumulator int16 add/sub order is unchanged
     and the loader's bound (max|b1| + 32·max|w1| ≤ 32767) keeps every partial sum in range.
   - `v3speed_2_nnue_v3_hpp.patch.txt` — the replay_ply call-site change (part of the same patch logically;
     split only because it lives in the header).
   - Numbers (callgrind, AVX2; workload 4 UHO positions × `go depth 12` = 3,866,594 nodes, trees verified
     identical node-for-node; bench 13/16 did not fit the budget — stated plainly):
     **before 5,106.3 Ir/node, 6,851.7 CEst/node → after 4,925.6 Ir/node (-3.54%), 6,677.8 CEst/node (-2.54%)**;
     branches 771.5 → 722.2/node (-6.4%). Update functions: `apply_changes` 1,272.0 → 72.5 Ir/n (fallback
     only) + `apply_changes_pair` 1,097.2 Ir/n, i.e. the update path 1,272.0 → 1,169.6 Ir/n (-8.1%),
     1,884.2 → 1,770.4 CEst/n (-6.0%). The remaining ~78 Ir/n of the win is spread over search/movegen
     callers (make_move -6.5, search -12.6, evaluate's caller side -9.3 Ir/n, …): fewer call sites and
     straight-line `if (count > i)` blocks instead of loop-back branches.
   - Wall line (secondary; AVX-512 native build, bench 11, 12 interleaved pairs, one core): base
     6120±557 ms, patched 6464±667 ms (mean -5.6% i.e. slower, best-of +9.1%). **Inconclusive**: stdev ≈10%,
     and the AVX-512 build is itself slower than the AVX2 build on this box for identical work (6.1 s vs 4.5 s),
     so I distrust this machine's wall clock for ±5% questions. Instruction counts are the measurement I stand behind.
   - Per-technique split (hoisting alone vs fusion alone) was NOT measured separately — no budget; the two are
     committed as one patch and reported as one.

5. **The oracle (all of it on the fully patched tree).**
   - **O1 PASS.** Node counts identical patched vs base, built-in net: 312866 / 862329 / 3024920 (bench 11/13/16);
     my net: 6,909,196 / 15,806,704 / 120,474,832 (`o1_base.txt`, `o1_p1.txt`).
   - **O2 PASS.** `eval` on 5,000 UHO positions: one sha256 over all answers, base == patched:
     AVX2 `4bbfe94669af…`, AVX-512 native `c4046f0e6d9a…` (the two shas differ from each other only because
     position 1's captured "answer" is the net-load banner, which names the kernel — a harness artifact present
     identically on both sides; the 4,999 real eval lines are identical across kernels too).
     Search `go depth 8` on 2,000 positions, once with `ucinewgame` each (A) and once in one process (B):
     every bestmove/score/nodes/pv/hashfull identical (nps/time fields stripped, they never repeat).
   - **O3 PASS.** Patched build with `-DFORGE_NNUE_V3_VERIFY=1` (the optional per-evaluation check against
     `evaluate_reference`): 5,000 evals, exit 0, same sha.
   - **O4 PASS, with one limit stated.** Planted fault: `collect_changes` uses `count-1` (one changed column
     silently skipped). Root `eval` does NOT detect it (sha unchanged — root evals refresh from scratch and
     never run the incremental path; an oracle of root evals alone would have passed a broken engine).
     Any actual search detects it at once: the verify build exits(3) printing
     `NNUE v3 verification mismatch ply 1 incremental -16 reference -18` on the first searched position
     (`o4_fault_manual.log.txt`).
   - **O5 PASS.** ASan+UBSan build of the fully patched tree: `bench 13` with my net = 15,806,704 nodes
     (exact), exit 0, stderr empty; 200 of the O2 positions, exit 0, stderr empty
     (`o5_bench13.txt.txt`, `o5_eval.log.txt`). Arming: the O4 fault probe above was run before trusting
     these clean results; a *separate* sanitizer-specific fault-injection was not run (stated plainly).

6. **Not bit-exact / no time.** No idea failed bit-exactness (only one idea was implemented). Not done for
   time: hoisting-only and fusion-only as separate measurements; refresh-cache key work (profiling says
   refreshes are 0.13/node and the cache nearly never fires — low value here); output-layer single-loop
   fusion (evaluate self cost is 7% of Ir, the prize is small); bench 13/16 callgrind per patch.

7. **Files opened.** `src/nnue_v3.cpp`, `include/forge/nnue_v3.hpp`, `src/search.cpp`, `src/bitboard.cpp`
   (profile only), `CMakeLists.txt`, the handoff file. All builds and the net live in /tmp, not the repo.

8. **Stamps (UTC).** Job read 18:42. Builds + net 18:44–19:00. Part A profiles done earlier (bench 11 pair,
   ~11.5 min each). Part B patch written 19:05; oracle 19:07–19:27; before/after callgrind pair 19:15–19:25;
   wall line 19:21–19:25; report 19:32–19:45. Budget 60 min; measurement work stopped at 19:32 as instructed.

9. **What I did not do.** Per-patch bench 13/bench 16 callgrind (too slow in budget — bench 13 with my net is
   15.8M nodes, bench 16 120M; my Part B numbers are from a 3.87M-node fixed workload with trees proven
   identical); scalar-kernel profile; a quiet-machine wall-clock confirmation; resolution of the compressed
   callgrind file ids to filenames for the full 15-line table (function-level attribution is complete instead);
   separate asan-arming fault.

10. **What I am not sure about.** The 14-Ir difference between the two Part A runs (in job 2 repeats were
    byte-equal; if this hides a real nondeterminism in the harness it is ≤ 4e-8 and cannot move any number I
    report). Whether the AVX-512 wall-clock regression is real on a quiet machine — instruction counts say the
    code does strictly less work, and the same patch's AVX2 wall line in O1 runs leaned the other way. Whether
    the scattered ~78 Ir/n caller-side win is call-site savings or code-layout luck (a null-patch control pair
    would settle it). The pair/fallback mix depends on king-move frequency in real games; my workload is
    UHO book positions, the PC's real net does not change the costs, but real-game trees may shift the mix a little.

11. **A better way.** Feed callgrind searches through a slow producer (`slowfeed.sh.txt` in evidence): the
    engine aborts `go depth N` the moment any further stdin is pending, so a plain `< commands.txt` silently
    truncates every search at depth 1 — my first two workload runs were garbage for exactly this reason, and
    the trap is invisible unless you count bestmoves. Also: run a null-patch control pair before claiming any
    sub-1% delta, and treat "root evals match" as no evidence at all for incremental-path correctness (O4).

12. **Model.** Kimi K3.

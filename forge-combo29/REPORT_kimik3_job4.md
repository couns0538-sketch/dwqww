# kimik3 job 4 report — v3 eval speed: the split, a null control, loop minimum, prefetch (2026-11-15)

**Plain answer first.** On the job-3 Part-B workload (4 UHO positions × depth 12 = 3,866,594 nodes,
tree identical in every run, AVX2 build, callgrind cache+branch sim):

| variant | Ir/node | vs base | CEst/node | vs base |
|---|---|---|---|---|
| base | 5106.3 | — | 6851.7 | — |
| null (function reorder only) | 5426.4 | **-6.27%** | 7284.4 | **-6.32%** |
| (i) hoisting alone | 5142.0 | -0.70% | 6985.7 | -1.96% |
| (ii) fused pair alone | 5404.6 | -5.84% | 7342.4 | -7.16% |
| (iii) both = job 3 patch | 4925.6 | **+3.54%** | 6677.8 | **+2.54%** |
| B1 = (iii) + loop minimum | 5284.7 | -3.49% | 7260.1 | -5.96% |
| B2 = B1 + column prefetch | 5926.7 | -16.07% | 7934.7 | -15.81% |

Read against the null control: **a pure reorder of one function inside nnue_v3.cpp swings the measured
total by ±6.3%, so every total in the table except B2's regression is inside the layout-luck envelope —
including job 3's +3.54%.** Inside the update function itself the numbers are sharper: hoisting removes
199 Ir/node of its 1272 (-15.6%, 2.3× the null's per-function swing of ±85) and the fusion halves the call
count (0.671 pair-calls/node replace 1.68 single-calls/node); those mechanistic wins are real, but on this
compiler they do not survive to the node total beyond what layout alone produces. B1 (my "loop minimum")
gained nothing dynamically — the disassembly showed gcc had already count-specialized the hot paths — and
B2 (prefetch) is a clear regression: +466 Ir/node of prefetch instructions for **zero** miss reduction.
Oracle on the final tree (job 3 patch + B1 + B2 applied): **O1–O5 all identical** (table below); B2 is
bit-exact, just slower, so the tree is safe and the recommendation is to drop B1 and B2. Cut or not
reached: the full oracle was run only on the final tree (the intermediate B1-only tree got O1's bench 11
node count only); the prefetch-4-lines variant was written but not measured; no wall-clock line this job
(the machine's ±10% noise makes it useless and the budget went to the clean callgrind pairs).

## A1 — the split (same workload, all runs 3,866,594 nodes, depth-12 sums equal)
Numbers in the table above. Hoisting alone: update function 1272.0 → 1072.8 Ir/node (-15.6% of the
function; its per-iteration struct reloads are gone, branches/node 771 → 715), yet the node total moved
only -0.7% — layout elsewhere ate it. Pair alone (non-hoisted pair, 1206.5 Ir/n at 0.671 calls/n =
1798 Ir/call vs base's two single calls ≈ 757×2 = 1514): the unhoisted pair is *worse* per update than two
single hoisted calls, total -5.8% (inside null). Both together (job 3): update path 1169.6 Ir/n
(-8.1% of the path) and the best total. Note the hoist-only tree carries the unused pair functions as dead
code (0.7% layout effect is part of its reading).

## A2 — null-patch control
Patch `a2_null_reorder.patch.txt`: `collect_changes` (418 bytes) moved from before the kernel definitions
to just before the dispatch. No semantic change. Measured like everything else: **-320.1 Ir/node,
-432.7 CEst/node (-6.27% / -6.32%) vs base.** That is the size of "code layout luck" on this
compiler/workload. Every per-node total I report must be read against it; per-function deltas above
~±7% of that function and structural deltas (call counts, disassembly) survive it.

## B1 — the pair loop at its minimum (patch `v3speed_3_loopmin.patch.txt`)
- Count first: the pair needs, per 16 values and perspective with k changed columns: 1 load + k×(column
  load + one add/sub) + 1 store = 2k+2 vector ops. The disassembly of the job-3 build
  (`b1_loop_before.txt`) showed the generic loop carrying 42–67 stack references per body (sign flags and
  column pointers reloaded per iteration) — but gcc had also emitted count-specialized straight-line
  clones, and the *dynamic* hot path already used them.
- Patch: hoisted pointers/flags into locals, `if (count > i)` chains, unroll h by 2, all three kernels
  (`b1_loop_after.txt`: hot specialized bodies now show 0 stack references).
- Measured: pair function 1097.2 → 1112.6 Ir/node (calls identical 2,593,373: 1636 → 1659 Ir/call,
  i.e. **-0.7 Ir/iteration — a hair worse**); node total p1 → B1: -359.1 Ir/node (inside the null swing).
  Honest verdict: **no gain; the compiler had already done the worthwhile part.** Do not take B1.

## B2 — fetching the columns early (patch `v3speed_4_prefetch.patch.txt`)
- Miss counts first (from the cache simulation, per node): update path D1mr 45.3 (job-3 tree) of
  whole-run 83.9; **DLmr ≈ 0.002 everywhere** — the simulated 16 MB last-level cache holds the whole
  6.3 MB table, and the PC's 96 MB LLC holds it too. D1 misses refill from a resident LLC; there is no
  long-latency miss to hide.
- Patch: in `collect_changes` (shared code, covers all kernels), prefetch each changed column's 16 cache
  lines (1 KB) with `__builtin_prefetch(..., 0, 3)`. Bit-exact by construction.
- Measured: update-path D1mr 49.84 → 49.88/node, whole-run 92.14 → 92.20/node — **no change**; the
  prefetches cost +466 Ir/node in `collect_changes` (2,593,373 calls × ~144 instructions) and the node
  total went -642 Ir/node (-12.2%), a regression far beyond the null. Why no reduction: the update is
  lazy — between make-move and the eval that consumes the column, hundreds of other columns pass through
  the 32 KB D1 and evict the prefetched lines; the fetch is always too early.
- What a cache SIMULATION cannot say (stated plainly): it has no hardware prefetcher model, no OOO
  overlap, and its LLC is 16 MB vs the PC's 96 MB; on real hardware the D1-miss cost may already be
  hidden by the OOO engine, or the prefetch traffic itself may hurt more. The conclusion stands on
  instructions alone: +466 Ir/node buys nothing measurable. **Do not take B2.** The 4-lines-only variant
  (`/tmp` tree kept, not committed) was written but not measured — expected same mechanism, smaller cost.

## The oracle (job 3's O1–O5, on the tree with all patches through B2)
| check | result |
|---|---|
| O1 node counts (built-in: 312866/862329/3024920; my net: 6909196/15806704/120474832, bench 11/13/16) | **identical** (`o1_b2.txt`) |
| O2 eval sha256 over 5,000 positions | **identical** `4bbfe946…` (`o2_eval_b2.sha.txt`) |
| O2 search 2,000 × depth 8, mode A (ucinewgame) and B (one process), bestmove/score/nodes/pv | **identical** both modes (nps/time stripped) |
| O3 verify build (`FORGE_NNUE_V3_VERIFY=1`) on 5,000 evals | **exit 0, sha identical** |
| O4 planted fault (`collect_changes` drops last column, `planted_fault_b2.patch.txt`) | **found by a search**: exit(3), "NNUE v3 verification mismatch ply 1 incremental -16 reference -18" (`o4_fault_b2.log.txt`) |
| O5 ASan+UBSan: bench 13 with my net + 200 evals | **15,806,704 nodes exact, exit 0, stderr empty** |

Intermediate trees: the B1-only tree passed O1's bench 11 (6,909,196) and its changes are a strict prefix
of the final tree, which passed everything; a full oracle per intermediate tree did not fit the budget
(each mode-B search run is ~15 minutes). Stated plainly.

## Part C — non-bit-exact next steps (text only; you decide)
1. **8-bit first layer with per-bucket scale.** w1 int16→int8 plus one int16 scale per king bucket; the
   update traffic (45 D1 misses/node, the 1 KB columns) halves. Every value shifts slightly; needs a
   re-tune of qa/scale and an Elo test. Gain: update bytes ÷2, maybe -2-3% node cost on real hardware.
2. **Evaluate fewer nodes in qsearch.** At qsearch depth ≤ 2 with a TT entry, reuse the stored static
   value instead of re-running the output layer when the accumulator is unchanged (it often is after
   quiet recaptures). Changes node counts; needs SPRT. Gain: skips the 0.2 evals/node that are recomputed
   on identical accumulators.
3. **Smaller net (hidden 256).** Halves every cost measured in job 3's Part A (update, refresh, output
   layer all linear in hidden). Strength loss unknown; needs retraining. This dominates everything above
   in magnitude if the Elo holds — the only real lever on the 46%.

## Files of the repository opened
`src/nnue_v3.cpp`, `include/forge/nnue_v3.hpp`, `src/search.cpp`, `CMakeLists.txt`, the handoff file.
Builds and nets live in /tmp; the repository got only `forge-combo29/tests_kimik3_job4/` and this report.

## Stamps (UTC)
Job file read 19:32:51. A trees built 19:33–19:38; B1/B2 patches written 19:34–19:39; B2 prefetch patch
19:39. First callgrind wave (hoist, paironly) 19:33–19:44 — paironly truncated (150 s too short under
contention), rerun. A contaminated null/B1 wave (4 concurrent valgrinds, trees truncated to 2.68 M nodes)
was discarded at 19:49 and rerun clean: null+B1 19:49–20:05, paironly+B2 20:05–20:21, every accepted run
3,866,594 nodes. Oracle on the final tree 19:45–19:59. Report 20:21–20:35. Measurement work stopped
20:23 as instructed; only the discarded contaminated wave ran past plan.

## What I did not do
Full oracle per intermediate tree (final tree only); the prefetch-4-lines variant measured; any
wall-clock line; per-kernel callgrind (AVX-512 cannot run under valgrind; scalar not profiled this job);
the 15-hot-lines table (the job-3 caveat about compressed file ids stands; function-level data is complete).

## What I am not sure about
Whether the null's ±6.3% is a gcc code-alignment lottery that would shrink with `-falign-functions=32` —
if so, job 3's +3.54% may be a real small win after all; the within-function -15.6% for hoisting and the
call-count structure are the parts I would defend either way. Whether callgrind's D1mr→10-cycle model
understates the real latency win B2 could have had on a machine where the table did *not* fit the LLC
(on the PC's 96 MB it fits; on a smaller-LLC machine my "no misses to save" line would not hold).
Whether pair-call frequency (0.671/node) shifts on real-game trees.

## A better way
Pin layout before measuring anything: one fixed function-order file per campaign, or
`-falign-functions=64` on all builds, so the null control reads ~0 and per-node totals become comparable
across variants. And my job-3 claim rule was too weak: from now on no per-node total is a "win" unless it
exceeds 2× that campaign's own null control — the within-function numbers were the honest currency all along.

## Model
Kimi K3.

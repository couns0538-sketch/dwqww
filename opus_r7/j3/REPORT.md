# R7 J3 Forge NPS (Threads=1): hotspots and three node-exact speed options — DONE

Branch `opus-r7-nps` = `opus-r5d-matefix` 5882c383 (engine 9933e43c + R5D docs) + `4c3577d7` (CI profile workflow) +
`2d9889cf` (the engine change, CI-tested) + evidence commits. Machine exclusive: no (gate conc 8, live trainer,
self-play). PC build: `build_r7.sh` = the R5D build script with `RECIPE=znver5` (the PC lock recipe, g++ 15.2 ucrt64,
`-O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static`).

## Hotspots (quiet GitHub runner, `opus-r7-prof` run 40888664822, `logs/ci_prof1_base/`)
perf (cpu-clock samples, bench 16, self time): **1. HCE `evaluate_position<false>` 14.4%** (the eval is residual:
HCE + network), **2. `MovePicker::next` 10.9%**, **3. `TranspositionTable::probe` 10.7%**, then `nnue::update` 8.3%,
`Worker::search` 7.5%, `generate_pseudo_legal` 5.8%, `nnue::evaluate` 4.9%, `is_legal` 4.7%, `see_ge` 3.6%.
callgrind (instructions, bench 13) agrees on the order (HCE 15.0%, `nnue::update` 8.0%, picker 8.9%); its memset
6.9% and magic init 7.7% are start-up / per-position clears of bench, not search.
On the PC build (MinGW) every TT probe and store goes through `lock_stripe()` -> `has_exclusive_access()`, which
reads a `thread_local` with a call to `__emutls_get_address` (emulated TLS) and walks the lease chain, and then
returns a deferred (unlocked) lock, because bench and UCI `go` with one worker hold an `ExclusiveLease`.

## The options (all `type check default false`; node-exact: same nodes, scores and moves)
| option | what it does | hotspot |
|---|---|---|
| `R7TtExclusive` | a one-worker search that holds the lease probes/stores through `probe_exclusive` / `store_exclusive` (tt.inc logic without `lock_stripe()`, in `.text.forge_r7`); every other accessor keeps locking | 3 TT probe |
| `R7QuietGen` | the picker's quiet stage uses `Board::generate_quiets_r7` (pushes, double pushes, piece moves to empty squares, castling) instead of generating every move and dropping captures/promotions | 2 picker / movegen |
| `R7EvalPrefetch` | after `make_move` in search and qsearch, prefetch the child's HCE pawn-cache entry (32,768 entries, ~1 MB per worker) | 1 HCE eval |
| `R7PrefetchEarly` (commit after `2d9889cf`) | the main search prefetches the child's TT cluster from `Board::key_after_r7(move)` as soon as a move survives pruning (before the extension checks, `record_move`, `make_move`); the old prefetch after `make_move` stays | 3 TT probe |

## Verification
| check | result | evidence |
|---|---|---|
| build, warnings, FMA | 0 warnings, FMA 0 (`forge_r7_j3a.exe`) | `logs/build_j3a.log` |
| OFF identity (lock tool `uci_check.py --full`) | ALL OK: bench 312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609, kiwipete 193690690 | `logs/identity_j3a_off.log` |
| each option ON, and all three ON | ALL OK (same numbers) | `logs/identity_j3a_{ttexcl,quietgen,evalpf,all}.log` |
| quiet generator == filtered full generator | 816,100 positions, 26.3M quiet moves (324,714 castles, 1.67M double pushes) identical in content and order; planted mutant (knight captures leak in) FAILS at index 14 | `tests/r7_quiet_gen_tests.cpp` (CTest `forge_r7_quiet_gen_tests`), `logs/quiet_gen_test.log` |
| nodes in every NPS run | equal to OFF in all 125 + 48 measurements | `logs/nps_*.json` |
| `forge_r7_j3b.exe` (adds R7PrefetchEarly) identity | OFF, R7PrefetchEarly ON, all four ON: ALL OK | `logs/identity_j3b_{off,pe,all4}.log` |
| key after move == make_move's key | 29,389,885 moves exact; the only differences are 240,918 double pushes that create a legal en passant (allowed by design) | `logs/quiet_gen_and_key_after_test.log` |
| instructions (callgrind bench 13, Linux runner, run 40895783133) | same nodes 862,329 for every set; R7TtExclusive -1.26%, R7QuietGen -0.35%, R7EvalPrefetch +0.08%, all three -1.53% (totals include bench start-up and per-position clears) | `logs/ci_prof2_options/option_sets.log` |
| CI (release, ASan+UBSan, TSan + profile) | `2d9889cf`: opus-ci 40895783124 success, profile 40895783133 success; `c34a9739`: opus-ci 40900192786 success, profile 40900192820 success | GitHub |
| instructions incl. R7PrefetchEarly (run 40900192820, same nodes) | tt -1.26%, qg -0.35%, pf +0.08%, **pe +0.84%** (the key computation), all four -0.69% | `logs/ci_prof3_c34a9739/` |

## NPS (PC, same exe, option toggled by `setoption`, fresh process per run, rotated order, `tools/nps_opts_ab.py`)
Paired per-round ratios, geometric mean with 95% t-interval (`tools/nps_ci.py`, `logs/nps_ci_pooled.txt`):

| set | runs | d16 wall | d16 CPU | d20 wall | d20 CPU |
|---|---|---|---|---|---|
| A/A (OFF vs OFF) | 10 | -0.02% [-2.24, +2.25] | -0.01% [-2.19, +2.22] | -0.98% [-2.51, +0.57] | -0.84% [-2.48, +0.84] |
| **R7TtExclusive** | 15 (5 + 10) | **+3.59% [+1.38, +5.84]** | +3.07% [+0.33, +5.88] | **+3.97% [+1.23, +6.77]** | +3.80% [+1.22, +6.46] |
| R7QuietGen | 5 | -0.08% [-0.83, +0.68] | -0.80% [-2.36, +0.79] | -1.51% [-7.78, +5.20] | -1.07% [-6.56, +4.75] |
| R7EvalPrefetch | 5 | -0.60% [-2.36, +1.18] | -2.20% [-4.78, +0.44] | -1.33% [-7.29, +5.00] | -1.40% [-6.75, +4.26] |
| all three | 5 | +4.72% [+3.78, +5.67] | +3.74% [-0.17, +7.80] | +2.11% [-4.53, +9.22] | +2.53% [-3.90, +9.38] |
| R7PrefetchEarly (j3b exe, pinned to CPUs 0-11) | 6 | -2.11% [-4.51, +0.35] | -0.58% [-6.19, +5.36] | +1.46% [-1.03, +4.01] | +2.17% [+0.38, +3.99] |
| R7TtExclusive (j3b exe) | 6 | +1.54% [-2.23, +5.45] | +1.93% [-2.97, +7.07] | +5.45% [+3.31, +7.63] | +5.56% [+4.19, +6.94] |
| R7TtExclusive + R7PrefetchEarly (j3b exe) | 6 | +3.34% [+2.08, +4.61] | +3.31% [-1.20, +8.03] | +4.68% [+2.82, +6.57] | +6.36% [+2.93, +9.91] |

- **R7TtExclusive: about +3.6-4.0% NPS on the PC**, the interval excludes 0 at d16 and d20, but the lower bounds
  (+1.2-1.4% wall) miss the PC's speed-eligibility rule (>= +2%). Median per-round gains: +3.3-5.1%.
  The mechanism is MinGW-specific (Linux builds have native TLS), so a Linux runner will show less.
- R7QuietGen, R7EvalPrefetch and R7PrefetchEarly: **no measurable gain** (intervals include 0, mixed signs). They
  stay in the tree OFF; I do not suggest gating them. With R7TtExclusive on, R7PrefetchEarly adds nothing visible.
- The PC was 73% busy (gate 8.0 CPUs, self-play ~2.1, trainer 1.3) while measuring: NPS figures are advisory.

## Exes
- `forge_r7_base.exe` = the unmodified base 5882c383, `forge_r7_j3a.exe` = `2d9889cf` (three options),
  `forge_r7_j3b.exe` = the R7PrefetchEarly commit (four options); sha256 in `EXES_SHA256.txt`.

## What to gate
`forge_r7_j3a.exe` (sha256 `61f641d8a2b5708d7de575cccf2e525e53627fc4625912f964e13bc236481454`, source = `2d9889cf`) with
`option.R7TtExclusive=true` against the same exe with defaults, e.g. a non-regression SPRT `elo0=-10 elo1=0` at the
usual 10+0.1 conc 8 (the change is node-exact, so only the speed differs). OFF reference on the same tree:
`forge_r7_base.exe` = the unmodified base (`13126f9dcbaf7c30bdc073490aebdf924fc69cea81ea027bc586e58e9abe392f`,
identity ALL OK). Exes in `F:\opus_scratch\r7\j3\exe\`. No Elo claim.

## Left
- HCE `evaluate_position` (hotspot 1) is untouched: the residual eval must stay bit-exact and nothing safe and
  measurable was found in the time.
- The `nnue::update` paths are already fused (sub+add, sub-sub-add) and exact in any order; no option added.
- Possible next steps: the same no-TLS idea for `hashfull()` (UCI info only), and an earlier TT prefetch (before
  `make_move`, from a key-after-move) to give the existing prefetch more lead time.

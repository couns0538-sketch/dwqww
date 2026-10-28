# O6 [test plan G-C2] Threat inputs (UCI NNUEThreats, default 0) — DONE

Branch `opus-O6` (from `origin/opus-C4`). Final code 78f5b871, head 42c3d9d5. `patch.diff` is against 294dbed;
`patch_vs_C4.diff` is O6 alone. UNPROVEN; no Elo claim.

## What was built
- **Feature set** (`include/forge/nnue_v2.hpp`, `ThreatFeatures`):
  - One input per pair (attacker A, victim V, victim square): A attacks an occupied square through pawn captures,
    knight or king steps, or a slider ray up to the first piece.
  - Perspective-relative colours and squares, with the king-bucket mirror flip.
  - 12 × 12 × 64 = 9,216 inputs. The input is the pair count, so a victim attacked by two pieces of the same kind
    counts twice.
  - One block, shared by all king buckets.
  - Dropped as redundant: king attacking king, and any piece attacking its own king.
- **File format:** header `feature_set` bit 0, with the block `wt[9216][H]` after w1. Engines that do not know a bit
  reject the file. The loader checks the file size before reading. C4's "one byte larger than the largest valid v2
  file" test now uses the larger maximum size, because files can carry the new block.
- **Option** `NNUEThreats` (spin 0-1): the header bit and the option must agree both ways (fail-loud otherwise). With
  `NNUEKingBuckets 0` it selects a one-bucket net.
- **Update path** (`src/search/evaluation_threats.inc` in this branch; section `.text.forge_v2`):
  - It replays C4's lazy plies, rebuilding each child's piece placement from the recorded changes.
  - It generates the child's pair list from the engine's attack tables and takes the multiset difference to the
    parent's list.
  - It applies all column changes in one pass, with each 64-float chunk held in 8 AVX2 registers (no FMA).
  - Each computed ply's list is cached next to its accumulator.
  - A king-key change refreshes through the cache, then adds the threat columns.
  - Weights are int16/4096, so the arithmetic is exact and incremental results equal a full refresh bit for bit.
- **Trainer** `--threats` (alone or with king buckets): the same pair definition in torch, exported with bit 0. Without
  `--threats` all outputs are byte-identical to C4's trainer.
- **Tools:** `forge_nnue_v2.py from-inc --threats-zero` builds lock replicas with a zero threat block. `v2_parity.py`
  checks the threat block and the accumulators.
- **Tests:** `tests/nnue_threat_tests.cpp` (63 checks). CI: `opus-o6-nnue.yml` / `ci_o6.sh` (about 20 minutes).

## Acceptance
| line | result | evidence |
|---|---|---|
| OFF → bench exact | **PASS** | `uci_check.py forge_o6_v4.exe --full` → all 5 pins, perft and kiwipete, ALL OK, FMA 0; CI also ALL OK. Codegen identical to C4 (vs the lock only C4's 3 known changes). Quiet-runner OFF NPS: d16 +1.26% (CI −0.64 .. +3.16), d20 +1.39% (+0.01 .. +2.77) |
| parity 10000/10000 | **PASS** | CI 40484330699, 1-bucket threat net: export integers OK; keys, accumulators and output 10000/10000; forward truncation 10000/10000. A 4-bucket mirrored threat net gives the same. Local runs (one thread) also PASS for both nets. Planted trainer bug (pawn attack directions swapped): accumulators 2252/10000 → FAIL (CI; locally by hand on the same net). The first local version of this check used the wrong module and missed the bug; it was fixed before CI |
| ON incremental == full refresh, bit-exact, 100k random plies | **PASS** | `forge_nnue_threat_tests`: 102,000 plies across 3 nets of 34,000 each (1 bucket; 8 mirrored buckets with 7,399 king-key changes; 4 unmirrored buckets), about 64,700 computed accumulators compared bit for bit, 0 mismatches. The pair lists match a brute-force reference on 3,000 positions (43,151 pairs). Zero-threat lock replicas give bit-identical evaluations and the lock's depth-8 node counts; through UCI, all 20 CI benches equal the pins |
| ON NPS loss at d16/d20 | **reported** | Zero-threat replica r1 (identical tree to the lock): CI quiet runner d16 −41.0% wall / −40.6% CPU, d20 −39.3% / −39.2%. Local (machine exclusive: no) d16 −42.5%, d20 −41.5%. CPU-trained threat net (another tree): CI d16 −47.1%, d20 −38.5%. Before the speed work the loss was −61.6% / −59.5% (CI) and −66.7% / −65.3% (local) |
| gate primarily at 40+0.4 | stated in the gate spec below | |
| §3 tests, sanitizers, planted bugs | **PASS** | CI opus-ci 40484330844: only the known 4 lines; threat tests pass in release (1.7 s), ASan (10.4 s) and TSan (30.8 s). Local 63/63; C4 suites 101/101 and 17/17. Planted engine bugs: 8/8 caught on the final code. Trainer default paths identical to C4's (4/4, local and CI) |

CI runs (all success): final opus-ci 40484330844, opus-o6-nnue 40484330699 (first version: 40480102586 / 40480103001).

**Profile behind the speed fix** (bench 16 on the zero-threat replica, `logs/profile_*`): lock about 1575 ms; threat
path without any threat work 2100 ms; plus pair lists 2410 ms; plus multiset difference 2640 ms; full path 4700 ms;
full path with every column pointer set to column 0 (no cache misses) 4400 ms, so cache misses were only about 7% and
the column loop itself was the main cost. The register-resident loop and the per-ply list cache brought the full path
from 4700 to about 2917 ms.

## ON bench pins
- The zero-threat replicas equal the lock pins at all 5 depths (CI).
- CPU-trained threat net 853d68515fdbb7a8: d11 343217, d13 1069707, d16 3461769, d20 10485984.

## Proposed gate G-C2 (one option: NNUEThreats; the net file is its payload)
- Candidate: `NNUEFile=<threat net>` with `NNUEThreats=1`. The log must show `… unmirrored residual threat inputs fnv1a <x>`.
- **Primary gate: SPRT [0,10] at 40+0.4** vs AL1 s198 (srand from the G-C2 row). A 10+0.1 run is informational only.
- Record NPS at d16/d20; the threat path costs about 40% NPS.
- Net recipe: copy this branch's `tools/nnue/train_resid_v3b.py` to `F:\forge_nnue_train\tools\train_resid_v3b_o6.py`,
  with `tools/nnue/forge_nnue_v2.py` next to it; run the lock `cmd.txt` with `--threats` added, keeping
  `--residual --init-check`. The queue form works, but needs the explicit `--train` file list to keep the lock's data.
  Smoke-test the threat ops on DirectML first (never run there): CPU cost was 0.35 s/step at batch 1024, about 14
  times the plain model.

## Open issues
- The NPS cost stays high. Remaining ideas: int16 storage of the threat block, deltas computed only for affected
  pieces instead of full lists, and the int16 accumulator pipeline (G-A2).
- Merge conflicts with O4 (`search_options.hpp`, `options.inc`, `uci.cpp`, the rule functions in `evaluation_v2.inc`)
  and C5 (`nnue_v2.hpp`, the loader).
- The RAM guard (6 GB free) stopped several local torch runs while the PC's own training ran; the complete training,
  parity and planted-bug evidence is therefore from CI. Supervisor: no adoption at any check; nothing under
  `F:\forge_nnue_train` was written.

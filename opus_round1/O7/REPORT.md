# O7 [test plan G-C3] Pawn-pair inputs (UCI NNUEPawnPairs, default 0) — DONE

Branch `opus-O7` (from `opus-O6`; O6's speed work merged in). Final code 1a577bf9, head 8399b3db. Diffs: `patch.diff`
(vs 294dbed), `patch_vs_C4.diff`, `patch_vs_O6.diff`. UNPROVEN; no Elo claim.

## What was built
- **Feature definition** (`nnue_v2.hpp`, `PawnPairFeatures`):
  - Every unordered pair of pawns, of any colours, on the same or adjacent files and at most two ranks apart.
  - Described in each perspective's frame by (colour pair, offset of the second pawn from the anchor pawn, anchor
    square), with the mirror flip.
  - 4 × 7 × 64 = 1,792 inputs, covering phalanxes, chains, levers, rams, doubled pawns and pawns two apart.
  - One block, shared by all king buckets.
- **File format and option:** header bit 1, with the block `wp[1792][H]` after the threat block. Option
  `NNUEPawnPairs` (spin 0-1) with the same fail-loud rules as O6. A net with both blocks needs both options. O6's
  "unknown feature bit" test moved from bit 1 to bit 2, because bit 1 is now the pawn-pair block.
- **Update path:** O6's path became `src/search/evaluation_extra.inc` (`static_evaluate_extra`), handling threat and
  pawn-pair blocks in any combination. Each perspective's pawn-pair list is cached per ply and is regenerated only on
  plies that move, capture or promote a pawn.
- **Trainer** `--pawn-pairs`: works alone or with `--threats` / `--king-buckets`. Default paths stay byte-identical
  to C4's trainer.
- **Tools:** `forge_nnue_v2.py --pawn-pairs-zero`; parity support in `v2_parity.py`.
- **Tests:** `tests/nnue_pawn_pair_tests.cpp` (55 checks). CI: `opus-o7-nnue.yml` / `ci_o7.sh` (about 20 minutes).

## Acceptance
| line | result | evidence |
|---|---|---|
| OFF → bench exact | **PASS** | `uci_check.py forge_o7_v4.exe --full` ALL OK, FMA 0; CI also ALL OK. Codegen identical to C4. Quiet-runner OFF NPS: d16 +0.47% (95% CI −2.86 .. +3.80), d20 −0.07% (95% CI −4.33 .. +4.18) |
| parity 10000/10000 | **PASS** | CI 40486074423: pawn-pair net (1 bucket), and a threats + pawn pairs + 4 mirrored buckets net: export integers OK; keys, accumulators and output 10000/10000. Planted trainer bug (two offsets swapped): accumulators 4156/10000 → FAIL. Locally the RAM guard stopped the parity run (5.94 GB free), so the parity evidence is from CI |
| ON incremental == full refresh, 100k plies | **PASS** | 102,000 plies across 3 nets with 0 mismatches: pawn pairs with 1 bucket; pawn pairs with 8 mirrored buckets (6,756 king-key changes); threats + pawn pairs with 4 unmirrored buckets. Pair features match a brute-force reference on 3,000 positions × 2 perspectives × 2 flips. Zero-pawn-pair replicas give identical evaluations and node counts; through UCI all 30 CI benches equal the pins (C4, zero-threat and zero-pawn-pair replicas) |
| ON NPS at d16/d20 | **reported** | Zero-pawn-pair replica r1 (identical tree): CI d16 −17.6% wall / −17.3% CPU, d20 −17.2% / −17.1%. Local d16 −20.6%, d20 −19.4%. CPU-trained pawn-pair net (another tree): CI d16 −21.2%, d20 −20.3%. Before the per-ply list cache the loss was −35.0% / −33.5% (CI) |
| §3 tests, sanitizers, planted bugs | **PASS** | CI opus-ci 40486074459: only the known 4 lines; pawn-pair and threat tests pass in release, ASan and TSan. Locally 55/55, 63/63, 101/101, 17/17. Planted engine bugs: 7/7 caught. Trainer identity 4/4 (local and CI). Local pawn-pair training (one thread) completed 2 epochs; the combined training was stopped by the RAM guard |

CI runs (all success): final opus-ci 40486074459, opus-o7-nnue 40486074423 (earlier: 40482177483 / 40482177570; merge
run 40484632312 ok, 40484632382 superseded).

## ON bench pins
- The zero-block replicas equal the lock pins (CI).
- CPU-trained pawn-pair net 23e0a7eaca429cc0: d11 325381, d13 803697, d16 3053216, d20 13860219.

## Proposed gate G-C3 (one option: NNUEPawnPairs; the net file is its payload)
- Candidate: `NNUEFile=<pawn-pair net>` with `NNUEPawnPairs=1`. The log must show `… residual pawn-pair inputs fnv1a <x>`.
- SPRT [0,10] at 10+0.1 vs AL1 s198 (srand from the G-C3 row). EVAL rule: if H1, confirm at 40+0.4.
- Record NPS at d16/d20.
- Net recipe: the lock `cmd.txt` with `--pawn-pairs` added (keeping `--residual --init-check`), using a copy
  `train_resid_v3b_o7.py` plus `forge_nnue_v2.py`. CPU cost was about 3 times the plain model per step.
- Testing threats and pawn pairs together would need its own option combination and its own gate.

## Open issues
- `src/search/evaluation_threats.inc` remains as a non-included 3-line note (its deletion was refused by the
  permission rules: no deletes); the eventual merge can drop it.
- About 17% NPS cost even without threats. Most of it is the extra path's own overhead (placement replay and list
  copies); a pawn-only fast path would reduce it.
- Merge conflicts with O4 and C5 as described in O4/O6.
- Supervisor: no adoption at any check; nothing under `F:\forge_nnue_train` was written.

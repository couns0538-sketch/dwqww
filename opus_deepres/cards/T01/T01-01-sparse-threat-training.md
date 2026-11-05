# T01-01: sparse threat + pawn-pair inputs on the training side (bullet examples/advanced)
Status: COMPLETE

## Source
- bullet da426a49 (= the bullet commit our ForgeV2 trainer is built on): examples/advanced/inputs.rs and main.rs,
  crates/bullet_lib/src/game/inputs.rs (SparseInputType). https://github.com/jw1912/bullet/tree/da426a49b2/examples/advanced
- Elo / nps: Viridithas PR 425 (merge c14c332a) https://github.com/cosmobobak/viridithas/pull/425 + PR 434 text (tests
  viri.dev 604 / 605 / 607, not opened); Integral PRs 243 / 266 https://github.com/aronpetko/integral/pull/243
- Ours: opus_r13/p4/RESULTS.md (ForgeV2 stage b = 768 + O6 threats 9,216 count-valued, c = + O7 pawn pairs 1,792).

## Licence
bullet: MIT at da426a49 (tools/licence_at.py) = copy with notice. Viridithas AGPL-3.0 at 7489e701bb, Integral no
licence at 29456bb34c = ideas only (PR / release text read, never source). Only bullet files were read of the config.

## Mechanism
- Threats are plain sparse binary features, never stored in the data: the loader's map threads compute them per
  position from the 32-byte board (attack bitboards with real occupancy) and emit up to 128 indices per perspective,
  padded with -1. The GPU runs bullet's sparse affine (gather-add of the active weight columns), so the cost grows
  with ACTIVE features x L1, not with the 59,808 total. That is the whole trick. Our reading of the 51x (not
  measured here): a dense pass touches all ~11,000 bundle inputs per position, a sparse one only the ~100-250 active.
- Encoding in the example: one feature per (attacker side relative to the perspective, attacker type, from-square,
  attacked square, victim type and colour); kings are neither attacker nor victim, each attacker type has its own
  victim set, mutual attacks between equal piece types count once. Only geometrically possible (from, to) pairs get a
  weight (section offset + victim slot x pair count + rank of the target among the from-square's empty-board
  attacks): 29,904 per side, 59,808 in total. Mirror by the own king's file; the other view flips ranks, swaps colours.
- Pawn pairs: one binary feature per (pawn, pawn) pair within a three-file band, 4,560 inputs, at most 120 active.
- Net: threats + pawn pairs share one affine; king-bucketed piece-square (16 mirrored buckets x 768 + a 768
  factoriser) is a second sparse matmul; both are summed before the activation; threat weights get their own
  (tighter) clip range in the optimiser. Count-valued features (our O6) do not fit (indices only, value 1): re-encode.

## Forge fit
`bash tools/forge_has.sh 'threat'`: 18 hits, all hand-crafted eval (src/eval.cpp:276 evaluate_threats,
include/forge/eval_params.hpp:39); the lock NNUE (768 -> 256) has no threat, bucket or pair inputs. The v2 port
(FORGENN2, feature set 0) has king / output buckets; O6 threats + O7 pairs live in forge-bundle-int b7c17722.
HIP: sparse affine + output-bucket select already train on our ROCm build of this bullet commit (ForgeV2, 2.8-4.4M
pos/s at H256), so this is not a dead end; two sparse matmuls summed before the activation: not verified on HIP here.
Change: a binary threat encoding in ForgeV2 (Rust map_features) + exporter + engine feature code + parity.

## Expected gain
Viridithas PR 425: threat inputs (SFNNv12-style set, every threat with a king excluded, 60,144 mirrored inputs); the
same PR cut L1 2560 -> 1024 and widened L2 16 -> 32, so the number is threats NET of a capacity / speed trade. 25k
nodes +27.43 +- 7.91 (3,046 g); STC 8+0.08 +2.98 +- 2.09 (30,040 g, LLR 3.06, [0,3]); LTC 40+0.4 +5.38 +- 2.97
(12,730 g, LLR 2.98, [0,3]); ~87 % of the old speed (AVX-512); book not stated. Integral PR 243 (new threat net; its
README today: 59,808 threats + 4,560 pawn pairs = the bullet example's counts, L1 768): LTC 40+0.4 +24.43 +- 7.77
(1,866 g, LLR 2.89 [0,4]); PR 266 merged threat + piece-square accumulators (+6 % speed). bullet example: no Elo.
Forge estimate: 0 to +5 Elo at LTC vs a v2 control net without threats **UNPROVEN**; vs the lock exe it also carries
the v2 path's own cost (identical-eval control -32.2 +- 18.5, D:/o30/FINAL_REPORT.md) and the threat update cost.

## Effort
Crew ~6-10 h (Rust input type, exporter, engine features, parity 10k + walk). GPU: recipe T01-03 R2 (speed unmeasured: smoke
first). CPU: STC + LTC SPRT at the gate rate.

## Test plan
New input type vs a brute-force feature list (3,000 positions x 2 views), export parity 10000/10000, incremental ==
refresh walk (the O6/O7 harnesses); paired holdout loss vs the lock net (S31 + jobA) before any game. Gate: UHO SPRT
[0,5] at STC, then LTC, against the identical-evaluation v2 control; the update cost by nps ABBA.

## OFF-by-default design
New FORGENN2 feature-set id read from the file under the existing `EvalFileV2` string option (empty = off). Off keeps
the lock's compiled net and code path, so the bench pins are unchanged; a file without the new id is refused.

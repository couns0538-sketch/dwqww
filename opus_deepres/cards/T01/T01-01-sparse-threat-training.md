# T01-01: sparse threat + pawn-pair inputs on the training side (bullet examples/advanced)
Status: PARTIAL (Expected gain PENDING)

## Source
- bullet da426a49 (= the bullet commit our ForgeV2 trainer is built on): examples/advanced/inputs.rs and main.rs,
  crates/bullet_lib/src/game/inputs.rs (the SparseInputType trait).
  https://github.com/jw1912/bullet/tree/da426a49b2/examples/advanced
- Our side: opus_r13/p4/RESULTS.md (ForgeV2 input type: stage b = 768 + O6 threats 9,216 count-valued, stage c = + O7
  pawn pairs 1,792); the owner's note that our dense threat + pawn-pair bundle trained about 51x slower.

## Licence
bullet: MIT at da426a49 (tools/licence_at.py) = copy with notice allowed. The config names a third engine's net
("pawnocchio_new_relabeller") and reads Viridithas-format data (viri.vf); only the bullet files were read.

## Mechanism
- Threats are plain sparse binary features, never stored in the data: the loader's map threads compute them per
  position from the 32-byte board (attack bitboards with real occupancy) and emit up to 128 indices per perspective,
  padded with -1. The GPU then runs bullet's sparse affine (gather-add of the active weight columns), so the cost
  grows with ACTIVE features x L1, not with the 59,808 total. That is the whole trick. The owner measured our dense
  bundle at ~51x slower; our reading of why (not measured here): a dense pass touches all ~11,000 bundle inputs per
  position, a sparse pass only the ~100-250 active ones.
- Encoding in the example: one feature per (attacker side relative to the perspective, attacker type, from-square,
  attacked square, victim type and colour); kings are neither attacker nor victim, each attacker type has its own
  allowed victim set, mutual attacks between equal piece types are counted once. Index = section offset + victim slot
  x (number of empty-board (from, to) pairs of that piece) + rank of the target among the from-square's empty-board
  attack squares, so only geometrically possible pairs get a weight: 29,904 per side, 59,808 in total.
  Perspective: horizontal mirror by the own king's file; the opponent view flips ranks and swaps colours.
- Pawn pairs: binary feature per (pawn, pawn) pair within a three-file band, 4,560 inputs, at most 120 active.
- Net: threats + pawn pairs share one affine; king-bucketed piece-square (16 mirrored buckets x 768, plus a 768
  factoriser) is a second sparse matmul; both are summed before the activation; the threat weights get their own
  (tighter) clip range in the optimiser.
- Count-valued features (our O6) do not fit this API (indices only, value 1): re-encode counts as binary features.

## Forge fit
`bash tools/forge_has.sh 'threat'`: 18 hits, all in the hand-crafted eval (src/eval.cpp:276 evaluate_threats,
include/forge/eval_params.hpp:39); the lock NNUE (768 -> 256) has no threat, bucket or pair inputs. The v2 port
(FORGENN2, feature set 0 only) has king / output buckets; O6 threats and O7 pairs live in forge-bundle-int b7c17722.
Change: a binary threat encoding in ForgeV2 (Rust map_features) + exporter + engine feature code + parity.

## Expected gain
Source number: none in the bullet files (no Elo, no test log). PENDING (threat-input Elo from the deep-read engines).
Forge estimate: PENDING **UNPROVEN**.

## Effort
Crew: ~6-10 h (Rust input type, exporter, engine features, parity 10k + incremental walk). CPU: STC + LTC SPRT.
GPU: one run per recipe (see notes/T01/recipes.md); threat runs are slower per position than H256 runs. PENDING.

## Test plan
Trainer side first: the new input type vs a brute-force feature list on 3,000 positions x 2 perspectives, then
export parity 10000/10000 and incremental == refresh walk (the O6/O7 harnesses). Offline: paired holdout loss vs the
lock net (S31 + jobA) before any game. Gate: UHO SPRT [0,5] at STC, then LTC, against an identical-evaluation control.

## OFF-by-default design
New FORGENN2 feature-set id read from the file under the existing `EvalFileV2` string option (empty = off). Off
keeps the lock's compiled net and code path, so the bench pins are unchanged; a file without the new id is refused.

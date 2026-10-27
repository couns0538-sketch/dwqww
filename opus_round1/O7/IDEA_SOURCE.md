# O7 idea sources (UCI NNUEPawnPairs: pawn-pair inputs for the NNUE input layer)

Ideas only. All code in this job is our own; no code was copied from any engine or trainer.

## Primary source
- **OPUS_TOP_ENGINES_2025_2026.pdf** (Opus's own research report, attached to the round-2 prompt):
  - TL;DR and Key Findings: pawn-pair inputs are among the net features behind the 2025-26 gains; Stockfish 19
    (SFNNv16) added pawn-pair features; Viridithas 20 (+60.84 +- 5.92 at 60+0.6, a bundle with new activations and
    threat inputs);
  - section 7, table row "Pawn-pair inputs": extra features for relationships between pairs of pawns; pawnocchio
    (inventor), Stormphrax, Viridithas, SF 19; expected gain unknown, cheaper than threats; status NEW (test plan row
    G-C3, after O6);
  - "Deferred" paragraph: threat and pawn-pair inputs are what the top engines do now; confirm at long time controls.

## Sources cited by the report (concept level)
- Stockfish 19 release notes (SFNNv16: pawn-pair features added, redundant threat features removed).
- Viridithas 20 release notes (activation functions, threat inputs and pawn-pair inputs).
- pawnocchio (named by the report as the inventor) and Stormphrax (adopters), concept only.

## What we took and what we did ourselves
- Concept: sparse inputs that describe pairs of pawns that stand close to each other.
- Our own definition (forge/nnue_v2.hpp, PawnPairFeatures): every unordered pair of pawns, any colours, on the same
  or adjacent files at most two ranks apart, described in each perspective's frame by (colour pair, offset of the
  second pawn from the anchor, anchor square) = 4 x 7 x 64 = 1792 inputs; this covers phalanxes, chains (supported
  pawns), levers, rams, doubled pawns and pawns two squares apart; one block shared by every king bucket, mirrored
  like the piece-square inputs.
- Our own incremental scheme: the pawn-pair list of each perspective is kept along C4's lazy ply replay and
  regenerated only on plies that move, capture or promote a pawn (other plies cannot change it); its difference is
  applied in the same chunked pass as the piece-square and threat changes; exact float arithmetic keeps incremental
  and from-scratch accumulators bit-identical.
- Our own trainer implementation (tools/nnue/train_resid_v3b.py --pawn-pairs), usable alone or with --threats.

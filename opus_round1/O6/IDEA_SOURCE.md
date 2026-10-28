# O6 idea sources (UCI NNUEThreats: threat inputs for the NNUE input layer)

Ideas only. All code in this job is our own; no code was copied from any engine or trainer. Astra's N20 was a
design note only; this job implements its own design.

## Primary source
- **OPUS_TOP_ENGINES_2025_2026.pdf** (Opus's own research report, attached to the round-2 prompt):
  - TL;DR and Key Findings: the 2025-26 gains of Stockfish, Reckless, PlentyChess and Viridithas came mostly from
    their nets, among them "threat inputs"; Stockfish 18's SFNNv10 "Threat Inputs" net; Stockfish 19 (SFNNv16)
    "removed redundant threat features"; time-control trap: threat inputs in PZChessBot +3.93 at 8+0.08 but
    +14.91 at 40+0.4;
  - section 7, table row "Threat inputs": extra sparse inputs for "piece X attacks piece Y on square Z", updated
    incrementally; cost/risk "large: tens of thousands of features, ~30% NPS loss, complex updates"; status NEW,
    LTC-only (test plan row G-C2, gated primarily at 40+0.4);
  - "Deferred" paragraph: threat inputs cost about 30% NPS and gain mainly at long time controls.

## Sources cited by the report (concept level)
- Stockfish 18 release notes / blog (31 January 2026): SFNNv10 "Threat Inputs" network.
- Stockfish commit 8e5392d (threat inputs; SPRT passed at STC and LTC, as summarised in the report).
- Stockfish 19 release notes (SFNNv16: redundant threat features removed, pawn-pair features added).
- PZChessBot PR #371 (threat inputs: about 30% slowdown; +3.93 +- 2.78 at 8+0.08, +14.91 +- 6.08 at 40+0.4).
- PlentyChess (first engine with threat inputs, per the report), Reckless 0.9, Viridithas 20 release notes.

## What we took and what we did ourselves
- Concept: add sparse inputs that describe which pieces attack which pieces, updated incrementally, and drop
  redundant ones.
- Our own design (forge/nnue_v2.hpp, ThreatFeatures): one input per (attacker kind, victim kind, victim square),
  perspective-relative colours and squares (with the king-bucket mirror flip), counted per attacking pair
  (12 x 12 x 64 = 9216 inputs, one block shared by every king bucket); the redundant pairs we leave out are
  king-attacks-king (impossible) and attacks on the attacker's own king (a king is never captured).
- Our own incremental scheme: C4's lazy ply replay, with the child placement rebuilt from the recorded piece
  changes, its threat list generated from the engine's attack tables, and the multiset difference to the parent
  list applied with the piece-square changes in one chunked pass; exact float arithmetic (int16 / 4096 weights)
  makes incremental, cached and from-scratch accumulators bit-identical.
- Our own trainer implementation (tools/nnue/train_resid_v3b.py --threats): the same pair definition in torch
  (ray tables with first-piece stops, leaper tables), v2 export with feature_set bit 0.

# Independent source-only design review

A second agent reviewed the frozen source16 SEE and the proposed promotion-aware
rare path without writing source, compiling, or running an engine.

Its recommendations agree with DESIGN.md:

- Dispatch before the existing threshold returns.
- Guard on the last-rank target and the corresponding color's live original
  potential promoting pawn, excluding the initial origin and captured/EP square.
  The pawn can belong to either exchange side and need not currently be legal.
- Preserve initial king/castle handling and terminal recapture-king safety.
- Add promotion gain to each promoting capture and carry the promoted victim
  value to the next capture. Fold the full LVA gain stack backward.
- Queen is sufficient inside the target-only optional-stop material model;
  off-target underpromotion tactics remain outside that model.
- Retain source16's LVA/tie choices and ordinary path. Omit threshold pruning
  initially inside the rare helper.

This corroborates the design reasoning. It is not candidate implementation,
runtime validation, a full minimax proof, or strength evidence.

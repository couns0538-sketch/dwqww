# Idea sources - opus_syzygy_gaps

No source, constants, tables or weights from GPL / AGPL engines are copied. Ideas below are described in own words. `cleanroom_lint.py` (R15 tool) reports the patch and the candidate's commit messages clean.

| what | source | licence | use here |
|---|---|---|---|
| Syzygy format and probing rules | R. de Man's format notes, CPW "Syzygy Bases" (via the P6 reader's own IDEA_SOURCE, `opus_round1/C1/IDEA_SOURCE.md`) | public description | existing own reader, unchanged |
| Treating tablebase scores like mate scores in pruning guards and at a null-move cut (`SyzygyTbBounds`) | common engine practice, described in general terms | idea only | own code in the P6 glue |
| Withholding a stored score that cannot be completed at the current clock (`SyzygyRule50` bit 1, read side) | common engine practice for mate scores, described in general terms; the TB-band form and k = 0 rule are this job's | idea only | own code |
| A TB loss distance that covers lines ending in a mate (`SyzygyRule50` bit 1, store side) | this job's reviewer (R2 finding 2, outline), built and tested here | own | own code |
| Resolving dtz + counter = 100 by a walk over the rounded lines (`SyzygyRootExact` bit 2) | this job's; the usual convention leaves that sum at one rank, noted as a deviation in `README.md` | own | own code |
| Fathom (jdart1/Fathom c9c6fef0) | MIT | permitted with notice; **test oracle only**, not linked into the engine | notice kept in `tools/THIRD_PARTY_NOTICES.md` |
| python-chess 1.11.2 `chess.syzygy` | GPL-3.0 | **test oracle only** as a separate program, as in R13 P6; no code copied | expected values for fixtures |

Update this file before any new source is used.

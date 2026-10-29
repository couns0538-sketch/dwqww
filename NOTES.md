# B5 continuation checkpoint — 2026-10-29

Base: b7c177222038e9332965a95ec53ea3b94e90dbc9. Implementation: fde944ae38e6bbfef0b38f2c4a207e08285fcc1d.

Default-zero SingularV2 and explicit N1 have compiled in full Release. All five OFF pins pass: 312866 / 862329 / 3024920 / 12389307 / 34048354. SingularV2 ON: 404121 / 1005954 / 4120585 / 11497954 / 34264955. N1: 277579 / 814055 / 2651984 / 18648191 / 40304213. Startpos perft5 is 4865609. NNUE SIMD/FMA check passes with no fused arithmetic.

Full CTest is running; do not infer success from the existence of partial logs. Next: finish it, report raw failures, seal evidence and qualify the branch. PORT_NOTES.md records every changed engine/build line, actual Forge Fable J3 provenance, CorrHistPlus interactions and CorrExt mutual exclusion. No Elo or speed claim.

IDEA_SOURCE: same-repository Forge J3 experiment and user's isolated validation workflow.

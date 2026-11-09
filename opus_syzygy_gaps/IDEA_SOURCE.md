# Idea sources - opus_syzygy_gaps

No source, constants, tables or weights from GPL / AGPL engines are copied. Ideas below are described in own words.

| what | source | licence | use here |
|---|---|---|---|
| Syzygy format and probing rules | R. de Man's format notes, CPW "Syzygy Bases" (via the P6 reader's own IDEA_SOURCE, `opus_round1/C1/IDEA_SOURCE.md`) | public description | existing own reader, unchanged |
| Treating tablebase scores like mate scores in pruning guards | common engine practice, described in general terms | idea only | own code in the P6 glue |
| Treating a PV-node TB win / loss as a bound and searching on | common engine practice, described in general terms | idea only | own code in the P6 glue |
| Fathom (jdart1/Fathom c9c6fef0) | MIT | permitted with notice; **test oracle only**, not linked into the engine | notice kept in `tools/THIRD_PARTY_NOTICES.md` |
| python-chess 1.11.2 `chess.syzygy` | GPL-3.0 | **test oracle only** as a separate program, as in R13 P6; no code copied | expected values for fixtures |

Update this file before any new source is used.

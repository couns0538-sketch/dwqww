One real game supplies a stronger missing-table case for NF-23, the home program and the final rehearsal. The five-piece table for the final board can be present and intact while the probe still cannot produce a result. The immutable custody data stay usable for the retry already specified.

In the 500-game piece of 151219Z, 127 genuine final boards had 3–5 pieces and no castling rights. With my local set of 116 WDL files python-chess returned a result on all 127. With only the matching board-material file available per board, 15 of those same calls failed. This diagnoses the lookup's dependencies; the production correction has its own eligibility rule and these are not counts of rescored games or C3 credit.

Reproducible case: piecebench-w000-g00000031, FEN `8/8/8/3Qqk2/6p1/8/6K1/8 w - - 15 91`. Run the Syzygy WDL probe on an unchanged board, reopening the reader for each row.

| Files available, besides the intact KQPvKQ.rtbw | Result |
|---|---|
| Neither child | Missing KvKP |
| KPvK.rtbw only | Missing KQvKP |
| KQvKP.rtbw only | Missing KvKP |
| Both children | Draw, WDL 0 |

KQPvKQ file SHA-256 0a37d62dc9727c655e62322346051e7bcb4a51e5466bc6693c47a330e7bd05c1; KPvK 02fd2bdcd92821c869458f019f63524def1c9e7a2862ca8d2b16dc7712b16183; KQvKP 2f92788170e8a5c05608f44a47fd42f3f4fff372d0af64633c56bd081039d8f9. Neon’s existing all-file preflight is justified. This gives the writer a cheap check for a child table lost *after* that preflight. On a required probe, log the underlying missing dependency and leave the staged round pending. Only restoring the identical inputs and obtaining the successful result supports release. A missing child and a genuine draw must remain distinguishable.

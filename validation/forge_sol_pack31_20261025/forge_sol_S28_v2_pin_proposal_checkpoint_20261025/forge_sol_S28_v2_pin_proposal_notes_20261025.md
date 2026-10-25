# S28 v2 isolated pin-proposal rebase — 2026-10-25

Status: source/patch checks PASS; candidate proposal only, not merged, adopted or natively tested in this subtask. No engine/search/eval/TT/move/network/CMake change.

Provided proposal SHA256 `692b164b2601cf84411a7ea8c4b7892b255a219b2a07e5bdf7167b2cad77a35e`, MD5 `3aecb403afebae7a5046e9e4bd3f8f97`. Rebased proposal SHA256 `7feadcd7212c1106f44559bac641f80eaa39c8289bce9d86e5c1aa65c9d29136`. All hashes are calculated from actual files.

Original supplied proposal Git/GNUzero-fuzz checks pass on B and fail on L' at README context. An initial L'-generated terminal README hunk then failed B; that failure is retained. The final README adds a candidate-only section at a common interior anchor, preserving the historical h256_e12 661 checklist and buffix notes. Candidate exact629/no-floor guidance and old6.4.24 mate/rook expectations are explicit.

Only supported targets are current merged L'/B. Actual Git-check and GNUzero-fuzz dry/application pass on both. Plain L lacks Job C/S01 tests/helper and is explicitly rejected by contract. All files already exist on the supported targets: Git headers use full indices and a/b paths; there is no new-file-mode header to invent.

`tests/tests.cpp` and `tools/rerecord_pins.py` are byte-identical to the result of applying the original supplied proposal to B, including its cosmetic reason labels and comments. Helper AST CASES changes only WAC score661→629; promotion entries remain identical. WAC move f6h5/depth12/PV guard stays exact; previous661 and original g3g6/>=31997 expectations stay on record. Promotions retain c6d7/c3d2, depth1 and score>100; observed686 is not made a new guard.

| Base | File | Before SHA256 | After SHA256 |
|---|---|---|---|
| Lp | `tests/tests.cpp` | `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c` | `a23eff7093679f1c4e4214096f9b47049a2c4e5f023cd65fb0f9a43d0cea7701` |
| Lp | `tools/rerecord_pins.py` | `af138972b44e9e95f85bd9c3eaed82e04533b91db9b1304350d8c2781f8be8a5` | `87848b4c299e5a5e73b9b42bc907021c9b2a93efcb0397db4b4872ae37a12096` |
| B | `tests/tests.cpp` | `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c` | `a23eff7093679f1c4e4214096f9b47049a2c4e5f023cd65fb0f9a43d0cea7701` |
| B | `tools/rerecord_pins.py` | `af138972b44e9e95f85bd9c3eaed82e04533b91db9b1304350d8c2781f8be8a5` | `87848b4c299e5a5e73b9b42bc907021c9b2a93efcb0397db4b4872ae37a12096` |

Both order stacks with the separate timepack4 v2 patch pass Git/GNU checks on L'/B and produce identical final target inventories. GNU offset handling initially created an optional IDEA_SOURCE.md.orig backup in one order; that artifact-only comparison failure is retained, and final checks use --no-backup-if-mismatch in NEW directories. No target byte or patch changed to obtain the result.

IDEA uses a distinct shared interior anchor and removes back to each original document exactly. Diffstat: 4 files, +18 −5.

The main S28 tool must bind this explicit reviewed proposal to supplied f006 net/source hashes and actual S01 observations before applying it in an isolated candidate. This does not authorize lock adoption or unreviewed future pin changes. Native post-rerecord KNOWN4 validation belongs to the main owner; no native or build result is claimed here.

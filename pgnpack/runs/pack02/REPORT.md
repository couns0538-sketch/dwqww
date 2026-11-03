# R13 scoped PGN-mode evidence pack

Authentic production game separation: **UNVERIFIED**. No training or strength claim.

The requested base already records its historical final PGN-mode evidence pack as
PASS. Its packer reads protected handoff_v7 and inventories historical output roots.
This new R13 pack uses explicit safe evidence only; it does not rerun or certify
those excluded historical checks. It does not generate a new training dataset.

| Source | IDs / boundaries present | Authentic train/holdout proof |
|---|---|---|
| R14-B jobA, selfplay001/002 | Inferred ordinal groups from changes in ply, result, pieces or rights | UNVERIFIED; generated group-disjointness is a separate internal consistency check |
| R13 old440k FPOS/FEN labels | No original game IDs; reconstructed position state | UNVERIFIED |
| Corrected P5 1k proof | Original full FEN, no recovered game identity | UNVERIFIED; small proof does not repair old labels |
| MIX_SPEC selected selfplay001/002 and complete holdouts013/014 | Physical source rows and whole-shard provenance, no authentic game bindings recovered | UNVERIFIED; historical position clearance is not game clearance |
| Archived million-row PGN capture export | Game ordinal:ply references in normalized selected rows | UNVERIFIED; complete original movetext is under prohibited F:/forge_push and was not opened |
| Historical match/book/personal PGNs found by search | PGN game boundaries exist | No authenticated linkage to the target population; not substitutes for target train/holdout data |

The bounded PC and GitHub search is recorded in SEARCH.json. Inferred boundary
lists, fixture binding maps and unrelated shard003 downloads were rejected as
production identity evidence. Absence within this search is not global absence.
No further recovery scan is planned, following the user's fallback instruction.

The reproducible game-hash helper is D:/a13/tools/game_hash.py. It uses the inherited
strict standard-PGN parser and SHA256 of the initial full position plus normalized
mainline UCI movetext. Headers, comments, annotations and variations cannot create
a new identity for the same complete mainline. Results are not part of the key.
It detects exact normalized game duplication; truncated/extended versions and
original row-to-game assignments still require independent authentic bindings.

Fixture tests cover duplicate games with changed formatting, same-game leakage
despite different selected positions, missing bindings, malformed movetext and
missing setup FEN. Fixture PASS never establishes production separation.
Production authentic-game overlap remains **null**, never a manufactured zero.

The final scoped pack is reproduced with D:/a13/pgnpack/reproduce.ps1, supplying
a fresh run name, a successful full-suite directory, the QC output directory
and its launcher-receipt directory. It checks per-test collection/call equality,
producer source hashes, QC completion hashes and output-path binding. Historical
MIX_SPEC and COMPLETE copies are context only; their old commands are not R13
execution instructions. All actual commands use the contained CPU launcher.

Final checksum verification and full-suite/review receipts are reported in
../FINAL_REPORT.md. SHA256SUMS and MD5SUMS cover payload bytes only; a valid seal
does not upgrade any UNVERIFIED source or establish training readiness.

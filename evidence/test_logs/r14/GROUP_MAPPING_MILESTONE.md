# Prepared group mapping milestone

2026-11-03 13:49 Vienna. Scope: prepared TSV parser, exact source-row join and
comparison of inferred groups with supplied observed chain ranges. Production
CLI and binary evidence binding are not yet implemented. No game provenance or
export authorization is claimed.

Candidate: D:/a14/tools/r14_group_map.py, MD5
366293ba084fd3a7c1cebabc3afd150f. Tests:
D:/a14/tests/test_r14_group_map.py, MD5 f26a62a10680d1e8c42175fcc0027b0f.

Initial parser/range/source-join checks passed13 tests. Independent read-only
review found a definite boundary could disappear from the counts if its whole
segment was omitted from prepared rows. Two regression cases reproduced both
orderings of an UNKNOWN and UNREACHABLE intermediate boundary. The fix inspects
every intervening range, including across source seams. Reachable physical seams
remain continuations. Review rechecked the exact corrected candidate and found
no new concrete defect.

Red: D:/a14/evidence/test_logs/r14/group-review-red01/output.log, two failed and
thirteen passed. Green:
D:/a14/evidence/test_logs/r14/group-review-green01/output.log, fifteen passed,
MD5 a3c9209bb29d2948665822462584998e.

Outstanding integration requirement: complete byte consumption does not imply
complete parse coverage. The final CLI must gate prepared, exact-source join,
source-tail parse and range mapping fill rates independently, bind every artifact
to its hashes and scanner qualification, and keep authentic identities UNVERIFIED.
Next action: integrate qualified source ranges and audit all prepared groups.

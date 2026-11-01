# Review log — UNPROVEN

## Milestone 1: converter compatibility and result semantics

Reviewer: read-only review_converter subagent. Candidate hashes:
evidence/milestones12_candidate.json; fixed candidate evidence/milestone2_candidate.json.
Findings accepted: unknown producer bypassed mate threshold; noninteger scores
accepted; malformed PGN results silently unknown; converter lacked Lichess route;
PGN identity global across files; baseline checkout newline risk.
Fixes: strict normalization, bad-result rejection, normalized/Lichess routes,
per-source game/ply provenance, byte-preserving .gitattributes.
Validation: evidence/review1_red.log (four regressions), review1_green.log (10 pass).
Focused reviewer recheck approved substantive fixes by inspection. Large identity
test remains pending. Reviewer supplied literal 8-cell outcome oracle for 1000 cases.

## Milestone 2: filter before million-row execution

Candidate: evidence/milestone2_candidate.json. Read-only same reviewer.
Rules/order/overlap/metadata alignment and bounded ordered workers approved by
inspection. Confirmed defects: disk guard after allocation and variable subtree;
orientation audit could overwrite evidence. Both fixed; tightened derived field
types and source-row constraints as well. Regression evidence/review2_red.log.
Fixed candidate evidence/review2_fixed_candidate.json; CPU suite 15 pass in
evidence/adapter_green_attempt2.log. Focused recheck requested; million run held.

Existing freeze: started with >80 GB D free and <1 GB new outputs; completed
before guard review. Original source hashes remained stable. It is preserved.

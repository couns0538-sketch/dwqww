# Forge 6.4 bug checkpoint — 2026-10-19 23:57 CEST

Status: NO NEW VERIFIED FINDING.

Accepted development SHA: 9108d012526be80c6d163f7cab684e6acd9abf8d (unchanged).

Existing candidates: OwnBook=false external-book bypass, source candidate 3c197fa1701a7806096dd1eb281ab4b9caa3f6a3; TT halfmove-context reuse (unproven in actual engine); perft UCI responsiveness (source-level); SMP TT consistency (requires tests).

Reproduction priority: run real UCI regression for OwnBook=false with external start-position Polyglot entry and go movetime 100; compare accepted vs candidate, retaining output. Then run rule-50 warm/cold TT and sanitizer cases.

Test status: BLOCKED. Local git clone could not resolve github.com; source inspection via GitHub connector succeeded. No Forge binaries, engine tests, PGNs or Elo results produced.

Next: :15 research, :30 independent executable testing, :45 acceptance review. Main branch not modified.

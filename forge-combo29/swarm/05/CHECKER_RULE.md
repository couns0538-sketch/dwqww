# CHECKER_RULE — house standard for any checker

1. A verdict requires the value found. No value, no verdict.
2. A missing value exits **3**, prints no verdict — never 0, never a pass, never a refutation.
3. "Agree" requires both sides measured; two absences never agree.
4. "Disagree" requires both sides measured; one absence is not a disagreement.
5. Every checker carries a stub engine that prints nothing: on it, exit 3 and print no verdict.
6. Exit codes: 0 = measured and agreed, 1 = measured and disagreed, 3 = nothing measured.
7. The parser must raise on absence, not return a sentinel.

Reference implementation and the seven checkers that failed this rule: `audit_failclosed/`.
**Recommendation for the next swarm — not a finding about the engine.**

# REVIEW_LOG: opus_spsa_resume

Policy: `review/AGENTS_3e900941.md`, section "Development review and verification". It was recovered verbatim from `3e900941:AGENTS.md`, MD5 94169aefef79ccb69c21f8f2c86298f0, because AGENTS.md is absent at main 5176ddf7 and at `opus-r9-spsa`. The first half of that file is scoped to Astra R8 datafilter and does not apply here.

How the policy is applied:
- One reviewer subagent per milestone: M1 inventory and families, M2 harness and engine patch, M3 builds and qualification, M4 confirmation pack, then a final recheck.
- The reviewer inspects the frozen candidate without editing and returns concrete defects, supporting evidence and missing checks.
- I assess every finding: confirmed ones are fixed within scope, rejected ones get a written reason, unresolved ones are recorded. Substantive fixes are rechecked by the same reviewer through SendMessage.
- **Independence:** the reviewer is a same-model subagent with fresh context. It is not an independent human or Code Review pass, and each entry below says so.

| Milestone | Candidate (commit / hashes) | Findings | Fixes / dispositions | Validation | Next |
|---|---|---|---|---|---|
| (none yet) | | | | | |

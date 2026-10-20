# Shared-TT skill update validation

Updated only the reusable TT skill and its supporting scenarios; no engine code,
Git state, existing frozen proof, sanitizer configuration or match was changed by
this documentation task.

Before editing, froze both original skill files and five scenario expectations in
`PROTOCOL.json`. A fresh agent (`tt_skill_red`, no inherited history) read only the
original `SKILL.md` and applied it to the five cases. Its R3 answer explicitly said
“Categorically prohibited by the current wording” because a blanket ban on locks
across recursion omitted the reviewed exact-one-worker ownership distinction.
That is the observed documentation RED. It correctly rejected unprotected bypass,
premature resize and an arbitrary cross-thread deadlock guarantee. Its R2 rejected
acceptance but did not specifically identify the observed detector capacity.

Revised the skill to distinguish ordinary per-entry locks from the narrow explicit
one-worker coarse-gate lease; the linked reference specifies sequential drain,
release/acquire ordering, foreign wait/retry, exception cleanup, all-accessor
lifecycle quiescence and supported nesting limits. The main skill remains under
500 words. Recorded evidence uses frozen candidate
`8865666cc0ab4961cd507bae40ff6ce44e9319df`; it does not relabel operation counts
as speed or Elo.

A second fresh agent (`tt_skill_green`, no inherited history) received the exact
same application prompt and read only updated `SKILL.md`. It correctly treated R3
as eligible for bounded review, retained required proofs and no-helper constraints,
and rejected all four unsafe acceptance/claim alternatives. It specifically
classified the acquisition65 CHECK as detector-capacity failure. Exact returned
agent text is retained in `red-agent.txt` and `green-agent.txt`.

| Scenario | Original skill application | Updated skill application |
|---|---|---|
| R1 unprotected one-worker bypass | Reject: correct | Reject: correct |
| R2 all1024locks/default TSan CHECK | Reject acceptance; capacity not specifically named | Detector-capacity failure; preserve incomplete run; no disabled-check acceptance |
| R3 reviewed gate/drain ownership | Categorically prohibited: observed missing distinction | Conditionally eligible; actual proof obligations retained |
| R4 foreign accessor resumes before resize | Quiesce every accessor: correct | Quiesce every accessor: correct |
| R5 cross-thread ABBA guarantee | Reject guarantee: correct | Reject guarantee: correct |

This is one application sample per document version, not a statistical behavior
study or a general efficiency claim. Generic engineering judgments that passed
before the update are not attributed to the skill change. `verify.py` checks
structure, local references, unchanged baseline hashes and consistency with the
already retained frozen evidence. It performs no engine execution, new sanitizer
run, performance benchmark or strength match. Its result is documentation
validation only. Existing source tests belong to their original checkpoints.

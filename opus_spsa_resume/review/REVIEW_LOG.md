# REVIEW_LOG: opus_spsa_resume

Policy: `review/AGENTS_3e900941.md`, section "Development review and verification". It was recovered verbatim from `3e900941:AGENTS.md`, MD5 94169aefef79ccb69c21f8f2c86298f0, because AGENTS.md is absent at main 5176ddf7 and at `opus-r9-spsa`. The first half of that file is scoped to Astra R8 datafilter and does not apply here.

How the policy is applied:
- One reviewer subagent per milestone: M1 inventory and families, M2 harness and engine patch, M3 builds and qualification, M4 confirmation pack, then a final recheck.
- The reviewer inspects the frozen candidate without editing and returns concrete defects, supporting evidence and missing checks.
- I assess every finding: confirmed ones are fixed within scope, rejected ones get a written reason, unresolved ones are recorded. Substantive fixes are rechecked by the same reviewer through SendMessage.
- **Independence:** the reviewer is a same-model subagent with fresh context. It is not an independent human or Code Review pass, and each entry below says so.

| Milestone | Candidate (commit / hashes) | Findings | Fixes / dispositions | Validation | Next |
|---|---|---|---|---|---|
| M1: inventory, freeze, families (2026-11-10 ≈01:16–01:40) | c6df6af6 | 1 BLOCKER, 2 MAJOR, 6 MINOR, 1 NIT group (details below) | All assessed; fixed or addressed in the M1-fix commit; nothing rejected | Doc and evidence corrections; new evidence files; DR source line scan; 2×2 probe plus control; harness tests 55/55 ×2 | Recheck by the same reviewer |

### M1 findings and dispositions
Reviewer: one same-model subagent, read-only. **Not an independent review.**
1. **BLOCKER: F2 evidence false.** AUDIT said no `Qs*` gate and no in-flight qsearch work. Both were wrong (gate 58, P27R, 24 `CR_PASS_dr_*`, including DR06 on the QsSeeMargin line and DR12/DR04 nearby).
   **Confirmed and fixed.**
   - AUDIT §3–5 rewritten. The full DR list was taken from `queue_entries_DR.json`.
   - A line scan of all 34 deepres `search.cpp` trees shows no razor-line or futility-line edits; only DR06 touches QsSeeMargin.
   - The 6.x experiment record was added.
   - The family choice was re-argued. Razoring and the qsearch margins are verified never tuned. In-flight work is now a disclosed risk, enforced by the identity pin (PLAN §5).
   - F2's tuned scalar is QsFutilityMargin; QsSeeMargin is frozen.
2. **MAJOR: one F2 scalar while other single-scalar families were rejected.** Confirmed. Scalar count is no longer a criterion (AUDIT §5); the selector is code-level coupling. The "single scalar" labels are withdrawn.
3. **MAJOR: discrete levels break under the schedule.** Confirmed by the arithmetic: c0 ≈ 2.3 levels, a one-sided band at 40, and C2 excluding level 2. RazorDepth and QsSeeMargin were removed from the recommended SPSA vector. Level support stays a tested harness capability only.
4. **MINOR: C1–C3 are heuristic and inactive near the lock.** Confirmed. They are now labelled priors with the reviewer's numbers. C3 was reformulated as C3′ (M(1) ≤ 1000) and C2 dropped (PLAN §3).
5. **MINOR: interaction derivation imprecise; claim not measured.** Confirmed.
   - eval vs static_eval, the necessary-only bound, and checks/promotions are now in PLAN §1.
   - The 2×2 bench probe was run with a control. The control (QsFutilityMargin × LmrHistoryDivisor) is as non-additive as the family pair, so bench nodes cannot evidence the interaction. The claim is now code-level only and listed as UNPROVEN.
   - The "cross terms" wording was fixed (PLAN §4.1).
6. **MINOR: missing evidence and STATUS overclaims.** Confirmed and fixed: `evidence/combo29_source_commit_search.json`, "10 pinned + 8 recorded", the unproven-claims list, upstream wording, times.
7. **MINOR: INC-01 deletion inconsistent.** Confirmed. A reconciliation was added: the deleted set matches neither opus3 selection rule, the scope exceeded the approval by 3 earlier packs, and the actor is undetermined.
8. **MINOR: provenance labels.** Fixed (AUDIT §1): the qa_refcache files are trial_w6-derived and valid only via QA's bit-exact proof; the exe↔snapshot link rests on RUN_RECEIPT and build.log:77.
9. **MINOR: extend, don't rewrite.**
   - The confirmation runner's own LLR is justified as independence by design; QA's `forge_queue.ps1` is authoritative and was added to the inventory.
   - The run-size estimate is **PENDING** (S3 synthetic power check).
10. **NITs.**
    - R3/RazorDepth wording, the F2 guard and "evidenced" wording: fixed.
    - setoption-then-`uci` semantics: documented (PLAN §6, same as R9Tune).
    - `uci_driver` timeout: fixed with a reader thread. On failure the engine is asked to quit and is never killed.

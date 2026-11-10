# REVIEW_LOG: opus_spsa_resume

Policy: `review/AGENTS_3e900941.md`, section "Development review and verification". It was recovered verbatim from `3e900941:AGENTS.md`, MD5 94169aefef79ccb69c21f8f2c86298f0, because AGENTS.md is absent at main 5176ddf7 and at `opus-r9-spsa`. The first half of that file is scoped to Astra R8 datafilter and does not apply here.

How the policy is applied:
- One reviewer subagent per milestone: M1 inventory and families; M2 harness, engine patch and confirmation pack (the planned M4 was merged into M2, because the pack was complete by then); M3 builds and qualification; then a final recheck.
- The reviewer inspects the frozen candidate without editing and returns concrete defects, supporting evidence and missing checks.
- I assess every finding: confirmed ones are fixed within scope, rejected ones get a written reason, unresolved ones are recorded. Substantive fixes are rechecked by the same reviewer through SendMessage.
- **Independence:** the reviewer is a same-model subagent with fresh context. It is not an independent human or Code Review pass, and each entry below says so.

| Milestone | Candidate (commit / hashes) | Findings | Fixes / dispositions | Validation | Next |
|---|---|---|---|---|---|
| M1: inventory, freeze, families (2026-11-10 ≈01:16–01:40) | c6df6af6 | 1 BLOCKER, 2 MAJOR, 6 MINOR, 1 NIT group (details below) | All assessed; fixed or addressed in the M1-fix commit; nothing rejected | Doc and evidence corrections; new evidence files; DR source line scan; 2×2 probe plus control; harness tests 55/55 ×2 | Recheck by the same reviewer |
| M2: harness, engine patch and confirmation pack (the planned M4 merged into M2) (2026-11-10 02:33–03:00) | 5cb03dc2 | 1 BLOCKER, 3 MAJOR, 7 MINOR, 1 NIT group (details below) | All assessed as valid and fixed, except NIT (g), which is documented. One extra defect found while fixing (levels) | Harness 63/63, confirmation 35/35, R9 equivalence strict; both synthetic qualifications re-run under the fixed code; end-to-end demonstration redone | Recheck together with M3 |
| M2 recheck + M3: builds and qualification (03:15–03:27) | fd47a42d | M2: all resolved; 2 MINOR + 4 NIT-level new issues from the fixes. M3: 4 MINOR, 4 NIT | All assessed as valid; fixed or documented (details below; M3-3 was already fixed) | Confirmation 39/39, harness 63/63; new evidence: profdata summaries, preprocessed hashes, RazorTune-off equality | Final recheck |
| Final recheck (03:38–03:44) | b960b80b | Every disposition resolved, nothing blocks; 2 MINOR + 8 NIT new | All assessed as valid; fixed or documented (details below) | Harness 64/64, confirmation 39/39, R9 equivalence; selftest ALL PASS | Hand-off |

### M2 findings and dispositions
Reviewer: the same same-model subagent, read-only. It ran only `test_r9_equivalence.py` and small in-memory checks. **Not an independent review.**
1. **BLOCKER: the single-use registry fails both ways.** Confirmed.
   - **Too weak:** a deleted and restarted run directory was accepted, for the same or another candidate.
     - `check_holdout` now refuses:
       - a group registered from another directory, whatever the candidate;
       - a re-run in the registered directory once its CONFIRM.json is gone.
     - A resume with CONFIRM.json present goes on to the CONFIRM.json comparison (exit 11 if protocol or candidate changed).
   - **Too eager:** a refused start could burn the holdout.
     - `check_mode` now validates every mode prerequisite before anything is written: the synthetic block, the replay manifest (incl. hashes and parse), a known mode, and live (refused, exit 40).
     - Registration happens just before the first pair is recorded, with a new crash point `after_register`.
     - Synthetic runs use a separate registry file.
   - Tests: re-run after deletion and another candidate in the same directory (41 ×2); four refused starts leave no registry line and no directory.
   - The real registry `out\confirm_registry.jsonl` was never created.
2. **MAJOR: the audit-pgn leakage check passes vacuously on PGN-book games** (no FEN tag). Confirmed.
   - `start_position` rebuilds the start position from the FEN tag, then from the moves fastchess annotates `{book}` (python-chess). It fails closed (exit 31) on a FEN or book move it cannot replay, and checks that both games of a pair start alike.
   - The audit now requires `training_keys_files` and reports start sources, the 3-field and the 4-field leakage, and candidate issues.
   - Replay reports leakage too.
   - Test in the real fastchess format: 2 of 20 pairs leaked via `{book}` moves are found; an illegal book move gives exit 31.
3. **MAJOR: live-mode resume could lock up** (`.out` without `.pgn`). Confirmed. `next_attempt_base` takes the first attempt number whose `.out` and `.pgn` both do not exist, as R9 does. Unit test added.
4. **MAJOR: the candidate is not bound to a live run or to the real config.** Confirmed.
   - `select_candidate` refuses non-live runs unless `--allow-nonlive` (tests and demonstrations), and records `training_mode`.
   - Protocols pin `training_config_sha256`.
   - `candidate_issues` is reported by dry-run and audit, and replay refuses a non-confirmable candidate (exit 10) unless the protocol sets the test-only `allow_nonlive_candidate`.
   - The G1 example protocol carries a `QA_FILLS_BEFORE_ANY_GAME` slot.
5. **MINOR: `r9_clamp` was not R9 when the rounded plus equals the minus** (E-006 gate). Confirmed. The gate now applies only outside `r9_clamp`, so that mode is R9 in general. Unit test added.
   - `test_r9_equivalence` (finding 10a) is now strict: in inner mode a mismatch is allowed only in a batch that shrank, projected, capped or had an E-006 coordinate.
   - Result: stc1 has 0 mismatches. sanity3 has 1 (batch 0, a by-design batch).
6. **MINOR: the partition key (4 fields) and the leakage key (3 fields) differ;** 2 G1 openings collide on 3 fields. Confirmed by my own recount: G1 0 on 4 fields, 2 on 3 fields; G2 and G3 0 and 0.
   - Documented in HOLDOUT_MANIFEST, CONFIRM_PROTOCOL §3 and the `leakage()` docstring. The audit keeps the conservative 3-field rule and also reports the exact 4-field count.
   - The partition stays frozen; at most 0.08% of G1 is affected.
7. **MINOR: synth_qualify has three problems.** All fixed:
   - `plans_capped` used a truthy list; the corrected count is 0 in every run.
   - The resume check now always starts empty and requires both crashes to fire.
   - The docstring now says four keys.
8. **MINOR: a run ending on a prior can never yield a candidate.** Confirmed. `Space.feasible_engine_values` repairs the rounding (nearest feasible floor/ceil combination, c_end-scaled) for the `complete` record. Unit test with the reviewer's C1 example: plain rounding is (100, 200, 301); the repair gives (100, 201, 301).
9. **MINOR: the tuner's holdout refusal was case-sensitive.** Confirmed and fixed (lowercased on both sides). Test with an uppercase pin.
10. **MINOR: tests that passed for the wrong reason.** All fixed:
    - (a) R9 inner mode now strict, as in 5.
    - (b) The stale-ledger record is now re-chained, so only its run_id betrays it (exit 31, "stale").
    - (c) The fake optimizer now confirms the selected candidate. It stays an A/A run by construction, and the test name says so.
    - (d) `t_levels` indexes by name. **This exposed a real defect:** the QsSeeMargin level coordinate started at the edge index, where plus and minus always round alike, so E-006 froze it forever. The old test only ever measured RazorDepth. Fix: inner mode keeps a level coordinate at least e inside its index range. Integer coordinates and `r9_clamp` are unaffected. The recommended config uses no levels. Both level coordinates now update in more than 0 batches. The exact counts depend on the scratch path, because identity paths enter the run_id: 57/63 in my run, 39/49 in the reviewer's.
    - (e) Direct E-006 test added.
11. **MINOR: PowerShell scripts.** All fixed:
    - `selftest.ps1` runs the suites under `Continue` and keeps stderr as text, so a failing suite still writes TESTS.md; it now also reads back Idle.
    - `rollback.ps1` reads back mask and Idle.
    - `confirm.ps1` has the 30 GiB reserve guard for non-dry-run commands, plus `-AllowNonLive`.
12. **NITs.**
    - (a) A rollback now reopens a COMPLETE run. Test: the rolled-back run completes again (two `complete` records) and verifies.
    - (b) `status` now reports `pair_records` beside k.
    - (c) Rollback refuses a checkpoint whose content the ledger does not reproduce (exit 30, test).
    - (d) An unknown `--mode` is refused before anything is written (test).
    - (e) `identity_check: start` is refused outside synthetic mode (test).
    - (f) The confirmation ledger's torn-tail repair is now fsynced, and `verify` re-checks CONFIRM.json's protocol and candidate hashes.
    - (g) The `.ps1` defaults for `-Python` and `-TempDir` name this PC's paths: documented in README, not changed.
- **Run size:** the reviewer confirmed that ~0.2 c_end drift at N = 4000 is the schedule, not a defect. N was set to 16000 from the synthetic sweep before any game (`PLAN.md` §4.7); this is part of M3.

### M2 recheck and M3 review (same reviewer, of fd47a42d; 03:15–03:27)
The reviewer ran the three Python suites in its own scratch folder: R9 equivalence (strict), confirmation 35/35, harness 63/63. **Not an independent review.**

**M2 recheck.** All 12 findings and the extra levels defect are resolved. The reviewer checked the {book} reconstruction on the real R9 fastchess fixture: 16 book plies, the EPD equal to an independent python-chess replay. The fixes brought new issues, all assessed as valid and fixed:
- **(a) The registry can be bypassed** by a protocol whose `registry` points elsewhere. Every line now also goes to `<holdout file>.registry.jsonl`, and both files are checked. Test: a moved-registry protocol is refused (41). Documented as an accident guard, not a security boundary (deleting both files, or copying the holdout, defeats it).
- **(b) MINOR: a rollback after completion loosened the fixed rule.** `select_candidate` now refuses a run rolled back after completing and completed again. Rollbacks before completion and the pair-record count go into the spec. Test added.
- **(c) MINOR: an interim replay consumed the holdout.** Replay now computes its sequential outcome in memory before writing. PGNs that reach no decision and hold fewer pairs than the cap are refused (exit 10, nothing written). The replay tests now use a 40-pair interim set (refused) and a full 300-pair set (decision recorded). Documented: "replay once, with all PGNs".
- **(d) NIT: no FEN and no `{book}` returned the initial position.** It now fails closed (exit 31, test). Test fixtures use `{book}` moves.
- **(e) NIT: `complete` values were not re-checked.** `_apply("complete")` now requires `values == feasible_engine_values(theta)`. `status` and `export` use the same values; the export notes that the confirmable candidate comes from `select_candidate`.
- **(f) NIT: a test-only replay wrote the real registry.** A replay with `allow_nonlive_candidate` and a non-confirmable candidate now uses the `.synthetic` registries. Test: no real registry file exists afterwards.

**M3 findings and dispositions.**
1. **MINOR: no receipt for "PGO profile total equals QA's".** Confirmed. `evidence/builds/profdata_totals.txt` now holds the `llvm-profdata show` output for QA's merged profile and the three rebuilt ones:
   - QA, ctl and off: 320 functions, 2,481 blocks, total 6,054,052,240.
   - gat: 327 functions, 2,507 blocks, total 6,054,052,518.
   - The files differ byte-wise; BENCH says so.
2. **MINOR: "smallest noise floor" was not established** (3–4 replicates; 0.15 vs 0.32). Confirmed: the ranking against N = 40000 is withdrawn in BENCH §6 and PLAN §4.7. The choice is stated as a cost-benefit judgment on thin synthetic evidence. The gap to the larger-gain cells (0.83–0.90) stays. I did not run more replicates.
3. **MINOR: STATUS was stale at fd47a42d.** Already fixed in 59abe86f. No action.
4. **MINOR: a bare run of `clang_build_o3.ps1` writes into QA's tree.** Confirmed. Added the wrapper `engine/build_o3.ps1`:
   - mandatory paths;
   - refuses other jobs' trees and any `-OutRoot` outside this job's `out\`;
   - checks the recipe's sha256.
   Its refusal paths were tested (nothing created); no build was run through it. The receipted recipe is unchanged.
5. **NIT: the level-update counts depend on the scratch path.** Reworded to "more than 0 in both", with both runs' counts.
6. **NIT: the macro-0 identity evidence existed only in `out\`.** Committed `evidence/patch_macro0_preprocessed.sha256`: parent = off, cf0a9c2a…, 4,436,256 bytes.
7. **NIT: the RazorTune-off check tested only inequality.** Measured directly, the gate sequence set 2 (877190 / 3071864) equals the lock at QsFutilityMargin 176 alone (`evidence/qual/razortune_off_equality.json`). `qualify.py` now checks equality. battery_03 is kept as run with the earlier check.
8. **NIT: `freeze_inputs.ps1` did not read back Idle.** Fixed, so README's claim now holds for every script.

**Verified correct by the reviewer:**
- **Builds:** the recipe interdiff, receipts, training outputs and equal path lengths.
- **Images:** the PE normalization is sound; "normalized-identical, raw UNRESOLVED" holds.
- **Battery:** 16/16 checks.
- **fens12k:** byte-identical to QA's refcache.
- **warm1000:** the copy differs only in the mask lines, and the reading of the two allowed option lines is sound.
- **Synthetic tables:** every table recomputes from the evidence files.
- **Resume checks:** both fired both crashes.
- **Config change:** `pairs_planned` and the comment only.
- **PLAN §3:** its numbers check out.

### Final recheck (same reviewer, of b960b80b)
Every disposition of the M2 recheck and of M3 is resolved, and nothing blocks. The reviewer re-ran the suites, re-hashed the profiles and preprocessed files, and verified two N = 16000 runs under the stricter `complete` check. **Not an independent review.** New items, all assessed as valid:
1. **MINOR: a rollback silently disqualified a COMPLETE run.** `rollback` now refuses a complete run unless `--reopen-complete` / `-ReopenComplete` is given, and says the run can then yield no candidate. HANDOFF, ROLLBACK.md, README and PLAN warn about it. Test: refused without the flag, nothing appended.
2. **MINOR: the audit protocol for the UHO route was not specified.** Added `confirm/configs/audit_protocol_uho_example.json`: audit-only; cap 40,000; the train/screen keys pinned; `qa_gate` names from PROPOSED_QA_ENTRY; `training_config_sha256` to be filled in. HANDOFF step 5, CONFIRM_PROTOCOL and PROPOSED_QA_ENTRY point to it. Exercised on a generated UHO-style PGN: 6 pairs, starts from FEN tags, 0 leaked, candidate issues reported.
3. **NIT: HANDOFF still said confirmation 35/35.** Fixed before this recheck arrived (39/39).
4. **NIT: PLAN showed `rollback.ps1 -Baseline` without `-Config`.** Fixed.
5. **NIT: LIVE_ACK wording.** Fixed. It holds the harness's canonical-JSON config sha256, not `Get-FileHash`, and the refusal prints the expected value (HANDOFF, README, opus3_spsa.py docstring).
6. **NIT: the interim-replay bound failed for an odd cap.** It now compares `n_pairs < cap_games // 2`, as the dry-run plays.
7. **NIT: `{book}` present but on no leading ply.** It now fails closed (exit 31).
8. **NIT: "QA reruns with a fresh srand" fits the UHO route only.** CONFIRM_PROTOCOL now says that on G1 an INVALID replay consumes the group, and a rerun needs G2/G3 by a written protocol change.
9. **NIT: a test-only replay had no label.** Its output now carries a TEST-ONLY label.
10. **NIT: freeze provenance.** FREEZE.json was produced by `bin/freeze_inputs.ps1` as committed in c6df6af6 (blob 1f7da090). The current blob 52b9da3d differs only by the added Idle read-back. Recorded in STATUS.
- **Validation of these fixes:** the first self-test run failed one harness test, the tampered-checkpoint rollback. It runs on a re-completed run, so the new complete-run guard (exit 10) fired before the checkpoint check (exit 30) it exercises. The test now passes `--reopen-complete`. The second run: ALL PASS (R9 equivalence, harness 64/64, confirmation 39/39).

### M1 recheck (same reviewer, of 2d174ca8)
- **Resolved:** findings 2, 3, 4, 5, 7, 8 and 10.
- **Partial:** 1, 6 and 9. Five new non-blocking errors.

All were assessed as valid and fixed in the next commit:
- **(1a) Qsearch in-flight list incomplete.** DR01 and DR15 rewrite the corrected-static-eval line that feeds both the razor `eval` and `futility_base`. DR14 rewrites the qsearch draw line. DR12 also firms the post-loop fail-high.
  - I verified this myself with the line-presence scan of T06-05, T06-04 and T04F-03.
  - AUDIT §3/§5 and the PLAN §5 staleness list now name DR01, DR04, DR06, DR12, DR14 and DR15.
- **(1b) History pruning was rejected with an in-flight argument.** It is now rejected by the coupling selector, like IIR and check extension. The in-flight change is listed only as a disclosed risk.
- **New error 1, runner path.** Both forge_queue copies are named. Which one is installed is not determinable read-only, so the protocol says "QA to confirm".
- **New error 2, d11 without a receipt.** The claim was withdrawn in STATUS. The S3 battery records d11.
- **New error 3, necessary vs sufficient inverted.** Fixed in PLAN §1.
- **New error 4, "reproduced independently".** Reworded. Added `evidence/combo29_lineage_hashes.json` and `evidence/combo29_lineage_header_diffs.txt`; the second shows the four headers differ only in the six speed-switch defaults.
- **New error 5, "no fetch".** Now "no blob fetch; a ref/commit/tree fetch of origin preceded the search".
- **NITs.**
  - STATUS time corrected.
  - Control wording made exact: one control pair is as non-additive as the family pairs, the other is nearly additive.
  - INC-01 now says "most likely".
  - PLAN §2/§8: the synthetic estimate is marked not yet done.

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

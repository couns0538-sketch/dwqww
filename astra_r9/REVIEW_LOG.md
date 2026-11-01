# Review log

## M1 — output SIMD implementation, pre-production-build review

Baseline c8fd0e6. Reviewed nnue.cpp SHA256
8F1CA99DC2FC4374F764A786C9933E0523C94F044C803FCE7AB42C7B635FDAC1.
Reviewer subagent review_wide01 inspected without edits. No production defect found.
Verified lane mapping, operand/order preservation, 32-byte-safe unaligned loads,
default OFF, non-AVX512 fallback, and stop/join before option writes.

Confirmed proof gaps: integer-only comparison did not prove intermediate bits;
HCE digest was not combined static eval; one-ply checks did not cover long sequences.
Fix: diagnostic-only lane/output snapshots, combined residual/HCE digest, and 64
deterministic legal playouts up to 128 plies followed by full unmake. No rejected findings.
Initial diagnostic: 12k FENs, 668216 evaluations, 316108 moves, 12000 nulls, digest
f2c3e077fc92a00 identical to separate unchanged-lock harness. Corpus child coverage:
725 castles, 636 promotions, 9 en-passant moves (reviewer count).
ASan and UBSan deliberate positive controls both produced expected reports and exit 1.
Next: re-run expanded diagnostics and request focused recheck. Candidate NOT accepted.

M1 focused recheck PASS: all three gaps closed, git diff --check clean. Reviewed
nnue.cpp D11B4EED401A3F6C05EA7A5C8917E1E7F933A9E1BDF3E3992D44C62424F3F635.
Expanded unchanged-lock/candidate digests both 3bd3b27ac5a60483, 684200 evaluations,
324100 moves, 12000 nulls. Proceed with production build; not accepted pending full proof.

## M2 — validation harness and pre-timing review

Production c1/b1 and b2 SHA256 775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284;
engine source remains fb58080. Read-only reviewer review_wide01 found three harness
issues: streaming output could defeat an absolute deadline; affinity failure before
cleanup scope could orphan an owned child; timing lacked during-run interference
checks. Confirmed and fixed all; no rejected findings. Added deadline, affinity-failure,
and Windows CPU accounting regressions (3 PASS). Focused recheck PASS, including
production parity comparison and ABBA pair/statistics logic.

Validation: both kit builds full OFF/ON identity PASS and reproducible; diagnostic
684200 comparisons PASS; native sanitizer selfplay zero reports/illegal moves;
T1/T4 smoke PASS; production 12k lock/OFF/ON parity PASS. Next: advisory timing.
No candidate accepted until the speed gate passes and final evidence review closes.

## M3 — first timing rejection and second protocol review

Engine identity unchanged (775EDEA1...A6EF4284). Experiment 1 inconclusive: A/A
paired +1.679%, candidate +1.632%, 21/56 runs contaminated. No speed accepted.
Reviewed protocol v2 and time_abba_blocks.py read-only: PASS to run, not acceptance.
Whole-block telemetry-only eligibility, retained rejected rows, selected/all-attempt
statistics, fixed control/gain thresholds, attempt/deadline bounds verified. No
confirmed outstanding findings. Both experiments and rejection counts must be reported.

Reusable skills/eval-exact-simd/SKILL.md saved in branch, not globally installed.
Baseline gap motivating it was M1's incomplete float/combined-eval/long-sequence proof.
Schema validator PASS; read-only forward-test rejected a hypothetical integer-only,
epsilon-checked horizontal-reduction handover for the correct concrete reasons.
All three relative references resolve and exist. Next: run protocol v2 with other
owned work paused; final evidence review after measurement.

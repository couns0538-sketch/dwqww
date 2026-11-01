# Fitted time allocation implementation plan

UNPROVEN. Implements Couns's Astra R8 Job 1 specification.

Architecture: log completed main-worker root iterations under FORGE_TM_LOG;
fit an original NumPy logistic regression to final-move changes with whole-game
80/20 split; deploy integer coefficients and a bounded sigmoid approximation
behind TmFitModel=0/1. Multiply only the legacy soft-stop threshold. Preserve
hard-time checks and allocation caps. Snapshot model settings once per search.

- [x] Isolate lock fallback source; inspect prior time allocation; preserve crew work.
- [x] Compile logger and capture real >=50,000 root iterations, fixed seeds/openings.
- [x] Validate labeling, grouped split, AUC ties, quantization and extreme inputs.
- [x] Fit data and calibrate a/b/lo/hi with separate paired timing evidence.
- [x] Verify all seven numbered success tests, preserving original failures; actual-lock runtime checks use Linux CI.
- [x] Review scope, license provenance and model timing behavior independently.
- [x] Produce lock-applicable patch, sample/hashes, reusable skill and crew handoff.

Final engineering handoff: actual294 plus exact CR patch, candidate55114017.
Independent final review approved after the provenance receipt correction;
evidence/qualification_actual_lock_final_v2 passes the installed checker.
Strength remains UNPROVEN. Crew LTO+PGO/SPRT and longer-TC confirmation are
pending. Native Windows work never passed CR's CPU startup admission limit.

No copied GPL code/constants, no search changes, no Elo claims. One engine
thread per process and at most two concurrent engine/build workers, BelowNormal.
Do not touch crew processes, locks, gates, data, logs or production branches.
Update RESULTS at every checkpoint and push only astra-r8-tmfit, never force.

Review focus: no future-feature leakage; actual bestmove vs completed iteration;
same feature scaling in Python/C++; malformed/clamped tunables and overflow;
clock-only activation; observer overhead and OS scheduling in timed evidence.

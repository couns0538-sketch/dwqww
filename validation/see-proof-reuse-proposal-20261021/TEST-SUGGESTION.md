# Unapplied existing-group test suggestion

Reuse `test_pinned_static_exchange()` in `tests/tests.cpp`; retain all28 fixtures and both-color mirrors. This already covers legal/pinned defenders, defended king endings, captured-pinner ghosts, EP and Q/R/B/N initial/later promotion semantics. Keep the14 CTest names unchanged. Add no permanent diagnostic executable or observer counters.

After parsing the legal Move and before the final existing FEN/key preservation assertion, additionally snapshot `pawn_key`, `checkers` and `key_history`. Reuse the actual `at_zero` result and sweep a small ordered threshold set, e.g. `{-19200,-2400,-1200,-600,-300,-150,-1,0,1,150,300,600,1200,2400}`. For every case:

- Verify each predicate still agrees with the existing known-gain expectation.
- Verify it never transitions false→true as threshold increases.
- If `at_zero && threshold<=0`, require true at that actual threshold.
- Include the gain0 EP case as a positive-threshold control: ge(0) true and ge(1) false; proof must never override a positive threshold.
- Require FEN/key/pawn-key/checkers/full key-history unchanged after the sequence.

These actual-Board contract assertions support the mathematical implication; they do not independently test the private MovePicker lifetime or validate speed. The closed observer already exercised successful-stage proof against per-next reset/full Move/key controls, including negative return stages and exhausted pickers. The uninstrumented production candidate must still pass full native tests/sanitizers, exact cold/warm search responses and legal replay against frozen23; then calibrated hosted timing can assess useful savings. The proposed patch is source-only and unapplied, with zero mutable proof fields and the accessor evaluated only where the original SEE call would have occurred. Root owns application/versioning/freezing.

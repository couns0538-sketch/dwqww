# SPEC_REVIEW: adversarial review of SPEC_SEARCH2 and SPEC_SEARCH3 against the lock source

Started 04:39 PC clock (`date`), planned stop 05:04. Status: PARTIAL (sections filled as each spec is checked).
Reviewer: fable SPECREV (board slot S3). Read-only lock source FD3A5190 = AL1 s198:
`C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean` (`src/search.cpp`,
`include/forge/{board,search,eval}.hpp`, `src/uci.cpp`). Nothing here edits the engine, a card or a spec; every
Forge-side number is UNPROVEN. No web read.

Questions per spec: (a) anchors exist and say what the spec claims; (b) OFF path node-identical (no reordering, no
changed history writes, no changed TT stores); (c) ON path vs mate scores, stalemate, 50-move, repetition, TT bound
semantics, history ranges; (d) start values own values with a range; (e) interactions and gate order.
Verdicts: OK | FIX (exact fix in words) | BLOCKER.

## Reading record (lock, read-only)
PENDING

## SPEC_SEARCH2

### T04E-03 QuietMalusDecay
PENDING

### T04E-02 NmpTtCaptureMin / NmpTtCaptureSee
PENDING

### T04B-01 NoisySeeHistDiv / NoisySeeHistCap
PENDING

### T04D-01 CutNoTtLmr
PENDING

### T04D-02 TtCutNodeDepth / TtCutNodeForm
PENDING

## SPEC_SEARCH3

### T04C-02 SingularTtPvMargin
PENDING

### T04F-01 QsEvasionLimit
PENDING

### T04N-01 NegExtTtAlpha
PENDING

### T04N-02 NmpCutOnly
PENDING

### T04P-01 TtCutExtraMargin
PENDING

## Table
PENDING

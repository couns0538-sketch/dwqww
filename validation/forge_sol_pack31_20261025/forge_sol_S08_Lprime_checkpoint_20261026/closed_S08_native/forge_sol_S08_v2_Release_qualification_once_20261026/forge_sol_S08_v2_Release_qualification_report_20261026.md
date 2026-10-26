# S08 v2 Lprime Release ON native qualification

The isolated TLS-v2 Release ON candidate passed the authorized fixed-work
qualification. This is correctness evidence; NPS/time fields are unused for
speed or strength claims. The full sanitizer suite, fresh OFF binary proof and
other-base native qualification are separate work.

- Source freeze: `2923e86c186e357aac177e453f5745993d0839af02422d2622ff9f80dffae5ad`.
- Engine: `9208252eba0bc2aee5aa383806f854dff506c1ecd11c151d647c2567c64a3de2`.
- Controller: `33c92609f0b4da116625c98cb80d1b9bdd6763cfb5b3d9e3d82f06df87c4a453`.
- First bare11 was separately executed by root before this controller or any UCI.
- All12 build artifacts/source/20TU recipe and first-runtime receipt passed the
  read-only preflight. The qualification used CPU3/nice19 and fresh processes.

## Exact gates

| Profiled bench depth | Nodes |
|---:|---:|
|11|308972|
|13|745494|
|16|2460422|
|20|11901452|
|22|31111774|

All55 counters, denominator values, main+qs node sum, TT hit+miss sum and15 picker
stage sum passed for each depth. No counter overflow occurred. Profile packets
preceded the final bench summary; strict final pipe drain confirmed rc0, empty
stderr and no late output. Atdepth11, all55 counter rows also match the retained
v1 Release packet exactly. No v1 native result substitutes for these fresh gates.

Startpos perft5=4865609 and Kiwipete perft5=193690690 passed. The unchanged S25
`inspect_bench` parser passed ordinary default-false bench11 output through EOF.
The typed UCI allowlist was the frozen S25 baseline plus exactly the explicitly
approved Profile/check/defaultfalse option; this is not an untouched full S25
CLI pass with its original OFF-only option allowlist.

The seven lifecycle cases passed: defaultfalse, enabledT1, disabledT1, active
option toggle (old enabled snapshot after stop/join), next disabled search,
enabledT2 and disabledT2. All bestmoves were legal in startpos. The enabledT1
case counted10000 nodes; the active-toggle case772. The T2 case counted26882
actual total nodes for `go nodes 10000`; no deterministic SMP limit/count pin
was asserted, and accounting validated the actual finished total. Every case
has an explicit ready fence and the final process passed complete drain/EOF.

Full registered CTest passed15/15 with four known findings and zero unexpected
FAIL/PIN_MISMATCH. WAC remains the exact documented f6h5/661/d12/PV case. The
promotion cases reported c6d7/c3d2 atscore642/d1; acceptance followed the frozen
C++ source's score>100/d1/documented-king/PV guard, not a newly invented exact
score pin. The initial draft607 guess from an unrelated S26 candidate was
rejected and corrected before any S08 qualification execution; its failed
preflight and all draft/test logs are retained.

The frozen S05 checker passed the NNUE object and all demangled NNUE bodies in
the ELF. A separate complete-ELF disassembly scan found0 fused instructions.
All tool groups were reaped with no remaining members. All engine processes
returned0 with empty stderr and valid final drains. Source80 and engine hashes
remained unchanged. The closed capsule contains64 files and2,129,301 bytes
before this human-readable report; min observed free space29,310,976 bytes.

## Preserved review failures

The missing ready fence after the after-toggle disabled case was reproduced
with a delayed-info transport test (actual unfixed test failure), then repaired
before execution. Five pure controller tests pass, including exact first-runtime
binding, full CTest registration/known cases, startpos legal moves, variable
source-valid promotion scores and delayed-output rejection. Old controller
versions, RED/GREEN logs, the v1 TLS sanitizer failure and the sandbox LSan
EPERM diagnostics remain intact. No engine source changed during qualification.

The authorized2000 substitute corpus is independently verified as300WAC,
7bench and1693 legally replayed supplied-opening positions, with provenance.
It has not been collected by this controller. The root-owned full ASan+UBSan
build/runtime and capacity authorization remain separate prerequisites for the
remaining delivery claim.

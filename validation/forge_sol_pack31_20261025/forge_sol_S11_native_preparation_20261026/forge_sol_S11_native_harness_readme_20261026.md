# S11 native harness preparation — 2026-10-26

Source preparation only. No S11 compiler, engine, sanitizer, million-position
oracle or performance run has been executed. Native results remain UNVERIFIED.
Do not start these commands until root verifies S10 publication and grants the
specific finite execution window. A date or elapsed time is not that grant.

The engine patch is the existing immutable always-on material-history key patch
`1ac47bd324bf971005fcf3f8f57ad5f9ed6e4758e3186274230f07be4ea8bcee`.
The actual-API C++ oracle remains
`7d3be5616fe9e52382b2deb5b36d76c507a07a66bda07a6311f2e6a5dd557bd1`.
Its table is5,200 bytes. No NNUE update, TT prefetch, option or engine flag is
added by this harness. Original S11 preparation files are unchanged.

## Existing protocols reused

- S09 Release/ASAN compiler recipe auditors and the owned85 process/subreaper
  helper, including their actual compiler and source-hash checks.
- S09 native transport, typed S25 output checks, exact known-failure rules,
  full CTest/JUnit inspection, FMA checker and explicit engine-group cleanup.
- The original sealed-input utility and completed S09 one-million-legal-FEN
  corpus. No corpus is regenerated or positions selected for this candidate.
- The existing fixed-record chunk retention approach: one actual C++ process
  emits a complete million-record stream, archived at fixed record boundaries.
  A chunk is not a separately restarted ten-thousand-position experiment.

Source roles are the original Lprime or B and the corresponding isolated S11
source view. They contain no S09 eight-head engine changes. Full configured
CTest inventories are Lprime14 and B15, with exactly four known diagnostic
lines and zero additional FAIL lines.

## Ready interfaces

`forge_sol_S11_build_native_20261026.py` selects a frozen source using
`--base Lprime|B --role baseline|candidate --profile Release|ASAN`. It builds
the complete original standard targets in a new `/tmp/forge_sol_S11_native_20261026`
directory. The Release profile also compiles the actual-source material oracle.
ASAN builds the full engine/test suite without repeating an expensive oracle
compile. Each build is bounded to900seconds, one compiler job and4GiB sampled
owned RSS. The compiler process may have a4GiB address-space cap; this is not
an ASAN runtime address-space limit.

`forge_sol_S11_qualify_native_20261026.py --mode FIRST` must run exactly once
on each new main executable before UCI or oracle execution. It requires bare
`bench 11`, then `quit`, nodes308972, full EOF and unchanged source/artifacts.
`--mode FULL --first-runtime-receipt ...` consumes the original raw FIRST proof.
Release checks all five fixed bench counts, both perft5 results, unchanged UCI,
legal T1/T2 search, the complete CTest/JUnit inventory and FMA0. ASAN checks the
complete suite plus bench11, both perft4 positions, UCI and FMA0. Leak detection
stays enabled; ASAN runtime requires unlimited virtual address space and uses a
sampled4GiB owned-RSS guard. The existing LSan sandbox restriction requires the
same escaped runtime already used successfully for S09; do not disable leaks.

`forge_sol_S11_scalar_parity_run_20261026.py` consumes closed same-base Release
and FIRST receipts. A test-only scalar NNUE object is linked before the unchanged
core archive. The driver itself is compiled normally, so its FP-control header
remains comparable. Actual macro and disassembly checks reject a packed SSE
fallback, FMA, double/x87 inference and unsupported vector widths. Link maps must
show the intended object and no duplicate archive NNUE/search implementation.

The three arms are baseline AVX2, candidate AVX2 and candidate scalar. Each reads
the same sealed one-million-FEN input, checks the actual material key and emits
the actual NNUE CP and every accumulator float bit. The first4,096 roots also
exercise legal children and null-move restoration. Coverage counts are observed,
not assumed to be nonzero for every special-move class.

Each stream is36+1,000,000*2068=2,068,000,036 bytes. Fixed10,000-record gzip1
chunks keep each new data file below the GitHub100MB limit. The sole36-byte header
is in the first chunk; contiguous offsets/counts, complete EOF, original summary,
per-chunk and global hashes supplement exact comparison of every decoded byte.
The baseline expects zero table-basis checks; each candidate expects650 actual
checks. No rounded-decimal substitute or hash-only comparison is sufficient.

The JSON preregister contains complete command templates and explicit budgets.
`VERIFIED_S10_40HEX` and `ROOT_NEW_S11_GRANT` are required operator placeholders,
not existing publication or execution claims. Reuse a previous baseline only
when its exact source/flags/binary evidence closes; never rewrite a historical
build receipt or substitute an S09-feature engine.

## Advisory timing, last

Only after correctness and an exclusive native window, run the supplied unchanged
`forge_abba_time.py` at d16 and d20, AA6 and ABBA10, core2, nice19, the original
load6.0/busy0.08 gates and pair-wait0. Preserve every trial or ABORTED result.
The previous preparation's fourteen-pair suggestion is retained in its original
document; the current root request permits at least ten and this bounded plan
registers ten before execution. Do not alter noise gates to force a speed result.
Linux results are advisory. PC eligibility still requires the Windows CI lower
bound to reach+2% at both depths. No playing-strength or Elo claim follows.

## Pure tests

Python fixture tests exercise dependency/source/artifact identity, wrong compiler
and ISA modes, table marker roles, full FIRST/CTest rules, chunk gaps/reordering/
truncation and cleanup. Python fake children used for transport tests are marked
as fixtures; they are not C++ or engine evidence. All native gate results remain
UNVERIFIED until the actual commands finish and original outputs are inspected.

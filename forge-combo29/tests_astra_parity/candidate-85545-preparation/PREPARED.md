# Candidate 085545 diagnostic publication

Preparation only: no engine, Git or root-state operation. The original v5 blocked audit and complete pending record are retained here and pinned. Candidate depth9 returned e3a3,cp-949,25093nodes. Its total quit allowance was3ms, graceful phase1ms, observed exit0/signal0 at1.193467ms with driverSIGTERM set; reference search was batch-budget interrupted. This does not measure a natural-exit overrun of3ms or250ms.

After root's diagnostic controller has finalized PROCESS.txt and AUDIT.txt, use its actual directory:

```text
node /workspace/work/parity-candidate-85545-preparation/finalize.mjs ACTUAL_DIAGNOSTIC_DIRECTORY --check
node /workspace/work/parity-run/command.mjs candidate-85545-finalize node /workspace/work/parity-candidate-85545-preparation/finalize.mjs ACTUAL_DIAGNOSTIC_DIRECTORY
```

For the currently declared diagnostic, root supplied `/workspace/work/parity-run/shutdown-diagnostics/S2-0005-global-85545`. The helper does not assume the result: it re-audits that directory with the frozen original diagnostic auditor, checks its exact declaration/FEN/trigger/source-binary/input hashes and every finalized transcript, and requires its audit to reproduce. Missing PROCESS/AUDIT is refused rather than synthesized.

Counts retain actual attempted/finalized cycles,1000-per-side targets, timeout/error/signal data, tuple frequencies, forced/budget status groups, measured/unavailable/max/above100ms timing and exact pair comparisons. `completePrescribed2000` is coverage, not a claim of zero faults. The first-ten frequencies use only actual finalized cycles per side; a short run reports its true denominator and isFullTen=false.

Publication adds `tests_astra_parity/faults/shutdown-candidate-085545.txt`, full immutable diagnostic raw package `tests_astra_parity/shutdown-diagnostic-085545`, and original/proof package `tests_astra_parity/shutdown-diagnostic-085545-proof`. Every finalized transcript, cycles.jsonl, stderr, command, process result, declaration and native audit is retained through the raw package's SHA256 reconstruction manifest. No original diagnostic file is edited. The new state field is `candidateShutdown85545`; all other current stop/continuation flags remain untouched. No corpus credit or continuation waiver is issued.

The finalizer checks root state's initial hash after packaging and replaces it atomically. Wait for it to finish before checkpoint writes. Immutable outputs allow a safe retry if that state guard fires. Three synthetic derivation cases passed: full2000, partial13withtrue7/6first-ten denominators, and observed timeouts/tuple difference. No actual diagnostic result was assumed during preparation; first live finalization belongs to root.

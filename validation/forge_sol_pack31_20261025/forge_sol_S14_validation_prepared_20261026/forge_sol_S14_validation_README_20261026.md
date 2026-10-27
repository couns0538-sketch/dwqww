# S14 validation-only source preparation — 2026-10-26

No engine patch or new UCI option. Existing fixed MovePicker storage and mailbox lookup are being audited, not presented as a new optimization. C++ compilation and runtime are still UNVERIFIED.

This packet preserves our exact historical actual-MovePicker oracle in `history/` and its full hash in the adaptation provenance. The new driver still includes the exact bound search.cpp, uses the original seeded history/TT-move/killers/countermove/six-mode context, and checks parent restoration. It changes only diagnostic workload/output/counters. The20-case TSV and compiled expected-workload header are identical, bound inputs; output retains at most64 returned pseudo-legal picks per record while all calls drain through the terminator.

The counter observes the eight global C++ new/new[]/aligned/nothrow allocation entry forms on the current thread. It does NOT intercept direct C malloc/calloc/realloc/aligned APIs. Positive controls call escaping ordinary allocation functions through volatile function pointers, so C++ new-expression allocation elision cannot turn a broken hook into a successful control. A counter-disabled mode and an injected-allocation mode must both fail when actually run. These native controls have NOT run.

Windows conditional aligned allocation helpers are source only; no Windows qualification is claimed. The supplied build plans bind GCC14 Linux canonical references. Source/core/compiler/qualification changes require a newly reviewed binding rather than silently substituting bytes.

After the ordered S11–S13 native work and root grant, a plan can be created with:

```bash
python -B forge_sol_S14_build_plan_20261026.py --base Lprime --new-out /tmp/forge_sol_S14_native_20261026/Lprime_diagnostic_once
python -B forge_sol_S14_build_plan_20261026.py --base B --new-out /tmp/forge_sol_S14_native_20261026/B_diagnostic_once
```

Those commands save JSON only; they never execute a compiler or engine. Execute the exact `argv` and `runtime_templates` arrays through the existing owned-process supervisor with the preregistered CPU/RSS/deadline/capture limits. Verify inputs before/after and the mandatory link map. Capture original normal and both negative-mode results. The reference engine binaries already have original FIRST/Std evidence and remain unchanged; a diagnostic is a workload-CLI executable, not a new UCI engine.

Then compare actual closed Lprime/B streams:

```bash
python -B forge_sol_S14_compare_picker_20261026.py --left /path/to/Lprime.stdout --right /path/to/B.stdout --new-out /tmp/forge_sol_S14_native_20261026/comparison_once
```

The parser checks strict stream structure, declared bindings, controls and equality. It explicitly does NOT authenticate a native producer: keep owned-execution receipts, source/binary/map hashes, original raw output, exits and completeness proof. A same-baseline stream cannot stand in for the required Lprime/B comparison. No new engine candidate exists, so same-source comparisons cannot demonstrate an improvement.

Run the complete Python fixture suite with `python -B -m unittest discover -s . -p 'test_forge_sol_S14_*.py' -v`. All47 methods pass; they use synthetic non-executable fixtures and establish no native allocation result. Initial missing-tool RED captures and an intentionally weakened qualification-binding mutant are retained. Historical/draft files are evidence, not alternative entry points to run.

The current source-bound plans have been checked without compiler/runtime execution. L's optional plan borrows the Lprime core only after identical complete src/include inventories, and makes no L-full-Std claim. Required native comparison is Lprime/B. Current canonical main/tests/support/flags/original-qualification hashes are rechecked before allowing qualification reuse. Source plans still require execution-time integrity checks.

No ELF, full engine source, ZIP, LICENSE, AGENTS or .agents files are included. Source-only S13 provenance notes remain in the separate recon packet. All native dump, C++ counter, sanitizer, Windows, NPS and Elo conclusions remain UNVERIFIED.

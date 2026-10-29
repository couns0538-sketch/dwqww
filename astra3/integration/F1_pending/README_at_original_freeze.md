# F1 preparation: preset layout proof — 2026-10-29

**Synthetic compile-only evidence. No live engine file was edited.** This folder is preparation for the parent’s
named-construction repair; it is not that repair and is not a bench, perft, or playing-strength result.

Source revision label supplied by parent: `0fe9b37` (post-B5 integration). The exact copied live header SHA256 is
`3962c28cf4f2f814779fea7c6f874e7dcc42370678c92b695d1167dcfaeb86d0`.
The probe confirms:
- N1 has CorrHistPlus=4, SingularV2=true, SmpV2=false and TmSoftHardClamp=false, with no unrelated preset features.
- OFF and B1–B4 leave SingularV2, SmpV2 and TmSoftHardClamp false.

The original header copy compiles successfully. The intentionally broken copy exchanges only the `smp_v2` and
`singular_v2` declarations, leaving the positional preset initializer unchanged. It fails the two intended static
assertions: N1 no longer enables SingularV2 and wrongly enables SmpV2. The broken header remains under
`before_designators_0fe9b37/permuted_NEGATIVE_FIXTURE/include/forge/fb2.hpp`; it is NEVER an engine source candidate.
The live header was hashed and compared byte-for-byte before and after this experiment and is unchanged.

Only the newer Boolean fields are permuted. The first three fields stay in their original order because C++20
designated initializers must follow declaration order; this isolates the positional-field binding defect without
creating an unrelated designator-order compilation error. A named construction that names only needed fields
should keep the intended settings when the unused new flag moves before SingularV2.

Exact preparation command, from the integration checkout:
```
nice -n 19 python3 astra3/integration/F1_pending/probe_preset_layout.py --header include/forge/fb2.hpp --out-dir astra3/integration/F1_pending/before_designators_0fe9b37 --expect-permuted fail --source-ref 0fe9b37
```
The driver records exact compiler argument arrays, GCC version, raw stdout/stderr, both complete header copies,
probe source, hashes and expected/actual verdicts. It uses `nice -n 19`, C++20 and `-fsyntax-only`; no engine build
or engine executable is run. Existing output folders are rejected rather than overwritten.

After the parent implements F1, rerun the SAME driver/probe into a NEW folder:
```
python3 astra3/integration/F1_pending/probe_preset_layout.py --header include/forge/fb2.hpp --out-dir astra3/integration/F1_pending/after_designators_F1 --expect-permuted pass --source-ref ACTUAL_F1_SOURCE_SHA
```
Both original and permuted copies must then compile successfully. That result remains UNVERIFIED in this
preparation checkpoint. The parent separately owns all engine changes, regression suite updates, benchmarks,
M4 evidence, commits and pushes. Do not mistake the supplied source-ref label for a Git verification by this driver;
the exact source bytes are independently identified by SHA256.

IDEA_SOURCE: the recurring positional-option integration defect and the user's requirement for explicit named
construction and preset ownership. Original probe and mutation driver; no other-engine code.

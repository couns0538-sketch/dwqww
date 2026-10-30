# Independent exporter implementation review, 2026-10-30

Files read: tools/bullet/export_forge.py, tools/bullet/make_checkpoint_fixture.py, tests/bullet/test_export_forge.py in /tmp/forge-astra-bullet-export. Checked against exact R10 loader and MIT Bullet writer documented in /tmp/astra-export-review-contract.md. Read-only review; no product edits.

## Findings

1. MED: corruption fixture may itself invoke native undefined behavior. `corrupt_active_weight` replaces an output weight with127/-128 and evaluates it in wide Python arithmetic without calling `validate_bounds` on changed tensors. A valid original net near int32 limits can become unsafe. Reproduced with FTbias128, FTweights0,L1/L2bias512, otherweights0, finalbias2147483647. Original `validate_bounds`passes. Mutation chooses stack0,column96,0→127 and reports raw1258291199→1258291794; validating changed net fails `l3 affine sum could overflow Forge int32 arithmetic`. Native final `b3+dot` is int32 before widening. Fix: accept only mutations whose conservative bounds pass; select smaller/negative alternative or fail explicitly. Add regression proving original safe and generated negative fixture remains safe.

2. MED: nearest-away rounding is incorrect for permitted float scales just below half. Reproduced `quantize(np.array([1],f32),math.nextafter(.5,0),'nearest_ties_away','i1') == [1]`; true Rust round of0.49999999999999994 is0. `floor(abs(z)+.5)` double-rounds addition. Bullet's actual scales are integers with type-specific multiplier widths; exporter currently accepts arbitrary finitepositivefloat. Fix: restrict to explicit Bullet-supported integer scale types/ranges, and implement half-away through truncation and fractional comparison if floats remain accepted. Tests should pin both exactties and nextbelow/nextabove.

3. MED (integrity): checkpoint hash is checked before reopening/parsing and not computed over the actual parsed bytes. A concurrent writer can change the checkpoint between hashing and reading; resulting output need not correspond to manifest SHA. The export status hashes path again but doesn't compare to manifest. Fix: compute hash during parsing (same reads) and compare it before returning, optionally stat before/after as extra diagnosis. This also moves max-size check before expensive SHA I/O on an arbitrary oversizedfile.

4. LOW: malformed JSON top-level or tensor entries can throw uncaught AttributeError (`m.get` onlist or `s.get` onscalar), producing traceback instead of planned clean `ERROR` line. Validate dict types. Output remains absent on thisfailure, so no incorrectnet acceptance observed.

## Checks with no concrete issue

- Dense source Column-major→logicalmatrix→stackreshape is correct; FTtranspose matches file feature-major layout.
- File offset/hash/header/stackpadding expressions match R10.
- Featureorientation,material-state selector,sharedkingplane,stackselector match loader.
- Integerreference uses int64 sums/squares and final truncationtowardzero correctly.
- Original FT/dense bound tests prevent overflow before normal export.
- Synthetic imported checkpoint is clearly labelled notBullet-trained.
- Exclusivecreation preserves old files. FENstateignored by NNUEidentity is appropriate for evaluation (reference requires syntacticallyfullFEN).
- Mutation compares exactoriginalbyte at chosenweightoffset and changes exactlyonebyte.

No native execution or GPU smoke independently run in this review. Nativebuild/parity owned byroot.

## Independent recheck addendum

Before this review completed, implementation changed concurrently. Reproducer `/tmp/astra-export-review-repro.py` now prints correct half-neighbor result0 and rejects the unsafe mutant with ValueError. `/tmp/astra-export-review-repro-postfix.log` preserves that post-fix output; the identical earlier-named `*-original.log` is NOT a red log. Initial red outputs are in tool transcript above and the findings section; do not reconstruct them as test files. Independent17-test run passed in `/tmp/astra-export-review-unit-postfix.log`. Hash-as-parsed and malformed-manifest findings remain open in this snapshot.

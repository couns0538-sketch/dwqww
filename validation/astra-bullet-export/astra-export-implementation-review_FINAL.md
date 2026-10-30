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

## Final addendum: four findings closed; AL1 exporter inspected

Reviewed `export_forge.py` SHA2561e3bf0ee02fed64c9ecae990c186ee1c4d4e6eb3f243e08bf08d6dc4cdf803fe:
- Mutated net now passes `validate_bounds` before accepted corruption output; unsafe mutation rejects.
- Nearest-away now compares fractional part to .5 without lossy +.5 operation.
- `read_checkpoint(expected_sha)` hashes exactly the ID/header/payload bytes actually parsed and rejects mismatched digest; export calls it with manifest digest.
- Manifest root, tensor mapping and tensor-entry types are checked before `.get`; malformed structures fail cleanly.

New AL1 files inspected against `294dbed3:src/nnue.cpp`:
- `lock_export.py` SHA256ef5b7b99adf2e67f1fda70c2329ce3902c51296f3549bb2ce95181c09a98fad5.
- `train_lock_cpu_smoke.py` SHA25655eb662aa94d14bb25d534de10c31eaeb27c25b7daf84d55b059bf1c6741d9c2.
- `lock_oracle.cpp` SHA25604d4256cbdcfe95911817dd845f8a447fe24cee454e2fc5b024d9b173659724c.

No additional concrete product bug found. Lock matrix flattening matches shared768×256 FT and512 outputweights; /4096 quantization values are exactlyrepresentable in float32. Reference adds pieces in ascendingboard-square order and reproduces16independentlanes thenorderedbiassum, followed by float32multiply400/divide2.25 and clamp/truncation. Sourceincludeparser rejects oversized files,wrongcounts,outrangeintegers,duplicateddeclarations and unexpectedarraysyntax. It parses trusted Forgeinclude data; it does not executeC++.

Nativeoracle preflights canonical/hardlink aliases and everydestination before exclusive `fopen("wbx")`; checksstreamflushes/inputEOF/nonemptycorpus. Nooverwrite path reviewfoundnoadditionalgap.

CPU smoke is explicitly PyTorch, notBullet, preservesfullFEN/HCE slice,performsoneboundedepoch,usesfixedseed,recordsoriginalindices/losses/sourcehashes. It is a smalltrainingplumbingcheck, not300Mtraining orplayingstrength evidence. Export uses verified checkpointdigestagain andnewoutputs only.

Independent final suite `/tmp/astra-export-review-unit-final.log`:40tests,33passed,7nativeoracle tests explicitlyskipped because FORGE_LOCK_ORACLE wasnotset in thisindependentreview. Parentowns actualnativeparity/oracleIOlogs. No newnativeperformance orGPUclaimsfromthisreview.

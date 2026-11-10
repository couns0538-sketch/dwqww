# Latest combined TSan lifecycle screen with continuation weight 50

**Result:** 72 searches across eight lifecycle rounds completed with exit 0,
no ThreadSanitizer warnings, and no sanitizer initialization/runtime failure.
This is finite race coverage only. Positive-weight continuation4 search is
**UNPROVEN**; this result is neither a strength nor a speed claim.

## Tested build

- Last engine-source commit: `289c939fb870c2366d0518a416f09c1f192e1ce2`.
- Binary: `/workspace/shared/forge-build/smp-tsan-combined50/enabled`.
- SHA-256: `da6a7247cc28a4137b6911b6219c28b0d46a9f77cd4a5a5190e083f4839a4aa7`.
- GCC 14.2, C++20, O1, debug symbols, ThreadSanitizer, frame pointers, pthread,
  non-PIE, strict FP, x86-64-v3, assertions enabled and NNUE hidden size 256.
- Portable base ISA paths: PEXT=0 and NNUE_ZMM=0. TT_NOTLS=1,
  NO_ZERO_MOVELISTS=2, SEARCH_SPEED2=1 and PREFETCH_EARLY=1.
- All ten reviewed switches enabled: SMP_NODE_RESET, SMP_FINAL_NODES,
  SMP_STOP_LATCH, UCI_OPTION_CASE, BOOK_LEGAL_REUSE, NNUE_CASTLE_FUSE,
  ATTACKS_INIT_ONCE, SMP_EXCEPTIONS, MATERIAL_CORRECTION_CACHE and
  TT_DEPTH_OVERFLOW. Full `FORGE_*` spellings are in the build script.
- `FORGE_EXPERIMENT_CONTINUATION4=1` compiled, and
  `setoption name Continuation4Weight value 50` sent explicitly before search.
- With tunables exposed, UCI reports the current value as its advertised
  default. The harness requires the value 50 both immediately after setting
  it and after all lifecycle rounds; both acknowledgments were observed.

## Exercised behavior

Each Threads 2/4 × NNUE on/off combination occurs twice. Hash cycles through
1, 4 and 16 MB, OwnBook is false and Ponder is true. Each round exercises
successive node budgets 0/1/256/4096, infinite search followed by stop,
ponder-movetime followed by ponderhit, ponder followed by stop, movetime20,
movetime0, Clear Hash and newgame. Options and positions change only after
bestmove. Active searches receive only isready and their stop/ponderhit command.
The weight remains 50 throughout; no experiment tuning occurs during search.

## Reproduction and evidence

From `forge-combo29`:

```sh
tests/smp_tsan_combined50_build.sh /tmp/forge-smp-tsan-combined50
python3 tests/smp_tsan_combined50.py /tmp/forge-smp-tsan-combined50/enabled \
  --output /tmp/smp_tsan_combined50_results.json
```

`TSAN_OPTIONS=halt_on_error=1:exitcode=66:history_size=4`.
The recorded commands/output are in `smp_tsan_combined50_results.log`;
the outcome, exact executable hash and weight acknowledgments are in the
adjacent JSON file. No production code was edited for this screen.

A finite TSan pass does not prove every interleaving or branch was exercised,
does not detect all semantic errors in atomic state, and does not substitute
for native Windows testing, longer searches or strength testing. Existing
single-thread equivalence evidence at weight zero cannot establish equivalence
for this deliberately nonzero search experiment.

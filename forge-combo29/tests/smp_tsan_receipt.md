# Full-engine ThreadSanitizer UCI/SMP screen, 2026-11-10

**Result:** default-off and all-eight-fixes-enabled binaries each completed
72 searches in eight rounds, exit 0, with no ThreadSanitizer warnings. This
is a successful instrumented execution, not a sanitizer startup failure.
Raw command/output logs and machine-readable outcomes are preserved beside
this receipt. No production files were changed for this screen.

## Scope and reproducibility

Engine source's last modifying commit:
`dd1d7832cf7f8db8c1e789cf5b116a7251e595c6`.
Compiler: `g++-14 (Debian 14.2.0-19) 14.2.0`.

Full build flags are in `smp_tsan_build.sh`: C++20, O1, debug symbols,
ThreadSanitizer, frame pointers, non-PIE, pthread, strict FP, x86-64-v3,
NNUE hidden 256. PEXT and NNUE ZMM are disabled; TT_NOTLS, SEARCH_SPEED2,
PREFETCH_EARLY and NO_ZERO_MOVELISTS=2 retain the relevant search paths.
Assertions remain enabled. The enabled build turns on all eight review
switches; the default build leaves all eight at their default zero.

The binaries dynamically link `/lib/x86_64-linux-gnu/libtsan.so.2`.
`TSAN_OPTIONS=halt_on_error=1:exitcode=66:history_size=4`.

- Default: `/workspace/shared/forge-build/smp-tsan/default`
- SHA-256: `c25d83a1cfdd6ffe6dc383aba0f44d2a534936f8a29732732f9fff593c1eaf7a`
- Enabled: `/workspace/shared/forge-build/smp-tsan/enabled`
- SHA-256: `be8bf5ad4608901a5aa82ddad04cdf719e572c1103ebb67163bf2b9eef243cfb`

From `forge-combo29`:

```sh
tests/smp_tsan_build.sh /tmp/forge-smp-tsan
python3 tests/smp_tsan_stress.py /tmp/forge-smp-tsan/default \
  --output /tmp/smp_tsan_default.json
python3 tests/smp_tsan_stress.py /tmp/forge-smp-tsan/enabled \
  --output /tmp/smp_tsan_enabled.json
```

## Exercised lifecycle

Each of the four combinations of Threads 2/4 and NNUE on/off occurs twice.
Hash cycles through 1, 4 and 16 MB; OwnBook is false and Ponder is enabled.
Each round executes:

1. Set Threads, Hash, UseNNUE; `ucinewgame`; wait for `isready`.
2. Successive fresh-startpos `go nodes` budgets 0, 1, 256 and 4096.
3. `go infinite`; wait for depth-one info; `isready`; `stop`.
4. `go ponder movetime 40`; depth-one info; `isready`; `ponderhit`.
5. `go ponder`; depth-one info; `isready`; `stop`.
6. `go movetime 20`, then `go movetime 0`.
7. Clear Hash and wait for `isready`.

Every search waits for bestmove before the next position/options command.
Only the permitted isready/stop/ponderhit commands are sent during search.
This exercises UCI controller/search concurrency as well as multiple search
workers and shared TT access, unlike the earlier isolated attack-table test.

## Interpretation and limits

No new data race was established. A passing finite TSan run is not proof that
all interleavings are safe. In particular, stale node totals and overwritten
atomic stop requests are semantic races, so the default-off binary passing
TSan does not invalidate their deterministic reproductions.

This does not exercise unsupported concurrent Searcher API mutations, every
thread-creation exception, external NNUE reloads, all positions, or native
Windows execution. No speed or strength conclusion is drawn from instrumented
timings. The runner distinguishes actual sanitizer warnings from recognized
shadow-memory initialization failures and other sanitizer runtime failures;
none occurred in these recorded runs.

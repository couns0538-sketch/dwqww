# Prepared focused t12 recurrence check — not run

A native helper is built and ready for exactly ten repetitions of the existing failure FEN:

`8/4K3/8/1R6/8/8/7k/8 w - - 0 1`

**No search has been executed during this preparation.** Only the private helper was compiled; build exit was 0. Do not treat the prepared run command as execution evidence.

Original unchanged test invocation was `t12-krk_mate_test 40 10 2 16 14 1`. It completed with one no-mate-score miss out of 400 searches (zero non-mating-move misses), at zero-based pos=2/run=5: cp580/b5g5, original oracle root DTM13 and move DTM13. Its T1 recorded comparator was mate10/b5g5. Original stdout/metadata are copied and hash-pinned, and no expectations were changed.

Precise setup from tests_t12/krk_mate_test.cpp:245–251,355–380:

- Sixth argument is `clear_all=1`, not an NNUE setting. NNUE is default true.
- MateAlphaGuard, HindsightDepth, and SoundMatePruning stay at default false, despite the binary's compiled guard support.
- One `Searcher(16, 2)` is reused; each attempt starts with a new Board set to the FEN and full `Searcher::clear()`, clearing TT, evaluator caches, histories and search-stack state. This is not just clear_hash and not one newly constructed Searcher per repetition.
- SearchLimits has only depth changed to14; node/clock/mate limits remain defaults. The exact three-argument call is `search(board, limits, false)`, retaining default `TTAccess::Shared` and no iteration-output timing changes.
- The exact original KrkTablebase class and formatting helper are included from a byte-identical private copy of the existing test. Its original main is renamed, never called by the focused helper. The original main-loop miss predicate is preserved: positive mate score required; chosen move's oracle DTM must fit claimed plies for a mate score, or depth for a non-mate score.

The existing krk_guard_validation acceptance driver is not an exact substitute: its soundness mode enables the guard and changes invocation controls. The prepared focused helper keeps the failing test defaults.

When the parent authorizes actual execution, the command is:

```text
node /workspace/work/r4-krk-repeat/run-repeats.mjs --execute-authorized
```

That wrapper verifies preparation pins and fresh output paths, invokes the helper under `timeout -k 2 400`, preserves full stdout/stderr and actual exit/signal/hash metadata, counts exactly ten completed ROW records if present, and retains incomplete runs distinctly. A completed helper can exit1 for reproduced misses; the wrapper reports recurrence rather than suppressing it. Per-attempt output includes raw score, formatted score, bestmove, depth/seldepth, nodes, PV, original-oracle root/move DTM, and both unchanged failure predicates. Run files do not exist yet.

The focused check omits the original candidate-selection searches, 100 T1 preflight searches, and preceding positions. It preserves the intended fresh-search state contract of the failing loop, but cannot reproduce the exact original SMP scheduling or process-history prefix. Zero recurrences would not invalidate the retained failure. No deterministic seed controls OS scheduling.

`preparation-provenance.txt` pins source, existing engine objects, original failure output, existing native test binary, private source and prepared binary. `build.command.txt`, `build.stdout.txt`, and `build.stderr.txt` record actual compilation only. Prepared scripts have inert .mjs.txt publication twins; native scratch binary stays VM-local. No engine/test source, state, Git refs, or expected values were modified.

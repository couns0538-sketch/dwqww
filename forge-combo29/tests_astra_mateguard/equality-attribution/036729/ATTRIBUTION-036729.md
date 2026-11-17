# Causal attribution: equality record 036729

**Attributed to the mate-distance rejection in the r4-09 transposition-table clock-horizon fix.** On this exact FEN, removing only that rejection restores the reference score, nodes, PV, and every completed-iteration search signature. The r3-21 mate normalization and r3-24 duplicate-entry fixes remain intact. The new MateAlphaGuard is excluded as the cause: the existing audited binary with the guard not compiled has the same result as the guard-enabled binary with its default false option.

FEN: `8/8/2n2r2/3qN1k1/8/8/8/K7 w - - 90 141`

The unchanged original fault remains `tests_astra_mateguard/faults/equality-036729.txt`. `original-evidence-pins.txt` pins that full 11-pair transcript record and the E-0003 audit. This report adds attribution; it does not waive or erase the observed difference.

## Exact causal code

In the current frozen source, `forge-combo29/include/forge/search.hpp:104–106`, `TTEntry::score_usable` contains:

```cpp
if (is_mate_score(score)) {
    const int distance = MateValue - (score < 0 ? -static_cast<int>(score) : static_cast<int>(score));
    if (static_cast<int>(current_clock) + distance > 100) return false;
}
```

This returns false for a stored mate score whose encoded distance plus the current halfmove clock exceeds 100. Both `Worker::qsearch` (`src/search.cpp:1281`) and `Worker::search` (`src/search.cpp:1431`) use this admission predicate before decoding the TT score; rejected entries supply `ValueNone` to that score path. The decision is part of the default search, independent of MateAlphaGuard.

The change was authored as `bf4154454ddc7b226bc1734bfc84d75569cdfc07` (“Reject hash scores that cross the 50-move horizon”), then reapplied to the audited base by `bafb2d5bf3a542da5c51608bc9babf87f79cfa69`. The commit patch and actual read-only Git commands/output are retained in `history-*`. The other part of r4-09, the stored-depth/clock admission condition at header lines 108–114, is independently tested below.

## Controlled counterfactual results

Every search used a fresh process and `ucinewgame`, Threads=1, Hash=16, OwnBook=false, UseNNUE=true, MultiPV=1, default remaining options, and `go depth 9`. Every bestmove was `a1b2`. All eight diagnostic searches exited 0 with empty stderr. These are search-result counts, not speed measurements.

| Binary / one change | Fresh runs | Score | Nodes | PV family |
| --- | ---: | ---: | ---: | --- |
| Untouched reference e04556dd/f27 (`e2788a10…`) | 1 | mate -5 | 2,566,746 | Reference |
| Untouched audited base, guard not compiled (`06a2b1d5…`) | 1 | mate -6 | 2,565,143 | Candidate |
| Untouched guard-enabled, default false (`710cfcf7…`) | 1 | mate -6 | 2,565,143 | Candidate |
| Audited base with exact complete legacy r4-09 admission rule (`991ecdc5…`) | 2 | mate -5 | 2,566,746 | Reference |
| Audited base with **only mate-distance rejection removed**, new depth/clock condition intact (`831bde29…`) | 2 | mate -5 | 2,566,746 | Reference |
| Audited base with only depth/clock condition reverted, **mate-distance rejection intact** (`0245007a…`) | 1 | mate -6 | 2,565,143 | Candidate |

Reference PV:
`a1b2 c6e5 b2a1 d5d1 a1a2 d1c2 a2a3 f6a6 a3b4 c2c4`

Candidate PV:
`a1b2 c6e5 b2a3 f6a6 a3b2 d5d2 b2b3 a6b6 b3a3 d2b4 a3a2 b6a6`

The first differing completed iteration is depth 8. Both full-legacy runs and both mate-rejection-only removal runs match the reference at **every completed iteration** in depth, seldepth, score kind/value/bound, nodes, and PV. Elapsed time/NPS are deliberately excluded.

## Build and evidence integrity

The private control rebuild uses `12c791d5451b158fd6ed1b506b4869b15c8a5b4e` source/header bytes and the existing audited base object files, replacing only the privately rebuilt search object. Its executable is byte-for-byte identical to the untouched audited base (`06a2b1d582c05bb4a762ef76f64ec171a8a2ca031230b27fe3a5d2bc8ed8bace`). This verifies the private build path before interpreting the counterfactuals.

To avoid changing a shared class definition in only one linked translation unit, each variant adds a private search-local predicate and substitutes it at the two existing `score_usable` call sites. The helper is either the exact pre-r4-09 predicate, the current predicate minus its mate-distance rejection, or the current mate-distance rejection plus the exact legacy clock rule. No TT layout, move handling, normalization, duplicate-entry handling, evaluator, or other search change is made. Each variant's complete source and exact unified patch are retained.

One compiler was used at a time. Compiler argv, strict-FP/x86-64-v4 flags, stdout/stderr, exits, compiler version, source/object/binary hashes, and reused object hashes before/after are retained in each variant directory. `audited-source-manifest.txt` pins the full private header snapshot and search source. `one-case.py.txt`, `build-variant.py.txt`, and `verify-results.py.txt` are inert copies of the exact diagnostic helpers. Native scratch binaries and objects should remain VM-local.

`verification.command.txt` records the verifier exit 0. `verification.stdout.txt` records all eight run signatures and hashes; `verification.stderr.txt` is empty. Per-run `*.metadata.txt` records actual executable argv, every UCI command, final result, process exit, and full stdout/stderr hashes; full streams are sibling files.

## Limits

This establishes the cause of the equality difference for record 036729. It does **not** prove which mate distance is correct, validate a six-man result, or establish that the r4-09 predicate is correct for every position. No tablebase/oracle, broader benchmark, native test suite, or other FEN was run. The first internal TT rejection was not instrumented; predicate-level causality is established by the independent removals and exact counterfactual restoration above. Production source, frozen objects/binaries, expected values, state, Git refs, and original fault evidence were not modified.

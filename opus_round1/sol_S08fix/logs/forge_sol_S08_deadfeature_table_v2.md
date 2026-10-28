# Forge S08 low-frequency counter table v2 (AL1 lock, per-worker counter banks)

Observed event frequencies, not proof that a feature is dead code. No timing, speed or Elo inference.
Search-only instrumentation excludes board/FEN setup. Undefined rates (zero opportunities) are never rare.

Corpus limit: the specified 2,000 WAC/STS set is not available (no STS file exists on the PC); this run uses Sol's sealed substitute corpus: 300 WAC + 7 bench + 1,693 synthetic opening positions, 2,000 distinct. It is not a WAC/STS corpus.

Engine: FORGE_PROF build of opus-sol-S08fix (bench d11 312866, d20 12389307); collector f3715b9254e0; report sha256 595520dd5dc979466d224874011afd402410dd9b100642e33784f47620d4bf5d; positions completed 2000; search limit `go nodes 10000`; overflow False.

## Benchmark depth 20 (12,389,307 nodes)

Only defined rates below 0.1% appear. Denominators differ by event.

| Event | Count | Denominator | Opportunities | Rate |
|---|---:|---|---:|---:|
| nnue_refresh | 8 | nnue_forward | 6931060 | 0.00011542246% |

Not dead-feature rows (switched off by the lock defaults, so a zero count is expected):
- capture_futility_prunes: 0 of 1911546 capture_futility_checks -- tune::CaptureFutilityBase = 0 in the lock defaults (src/search.cpp); the prune requires CaptureFutilityBase > 0, the opportunity counter runs before that guard

## Substitute 2,000-position corpus (19,878,446 nodes)

Only defined rates below 0.1% appear. Denominators differ by event.

| Event | Count | Denominator | Opportunities | Rate |
|---|---:|---|---:|---:|
| nnue_refresh | 2000 | nnue_forward | 12076007 | 0.016561766% |
| history_prunes | 1108 | history_checks | 7794309 | 0.0142155% |

Not dead-feature rows (switched off by the lock defaults, so a zero count is expected):
- capture_futility_prunes: 0 of 3723977 capture_futility_checks -- tune::CaptureFutilityBase = 0 in the lock defaults (src/search.cpp); the prune requires CaptureFutilityBase > 0, the opportunity counter runs before that guard

## Interpretation

A rare cutoff may still protect critical tactical cases; rates with different denominators are not comparable; call frequency is not CPU-time share. No feature is removed on this evidence, and this substitute corpus is not the specified WAC/STS set.

# Forge S08 low-frequency counter table — 2026-10-26

These are observed event frequencies, not proof that a feature is dead code. No timing, speed or Elo inference is made. Search-only instrumentation excludes board/FEN setup. Undefined rates retain zero opportunities; no undefined rate is classified as rare.

Corpus: 300 canonical WAC positions, 7 additional benchmark positions and 1,693 supplied opening positions, selected under the handoff substitution rule. All 2,000 positions are distinct and legally verified. This is not 2,000 WAC/STS positions. Each search requested 10,000 nodes; actual work was 19,881,407 nodes.

Source report SHA256: `a45e190d31eff86eb80f69254ec1150919cfac4b077a2a04b54f7932741b549e`. Raw 2,001 packets and streams are preserved in checkpoint605adc9218a484ffcd222f57cf78a8a4469e124a.

## Benchmark depth20 (11,901,452 nodes)

Only defined rates below 0.1% appear below. Denominators differ by event and remain explicit.

| Event | Count | Denominator | Opportunities | Rate |
|---|---:|---|---:|---:|
| nnue_refresh | 8 | nnue_forward | 8129843 | 9.8402884e-05% |
| capture_futility_prunes | 0 | capture_futility_checks | 2330182 | 0% |

Full NNUE refreshes: 8 / 8129843 forward evaluations = 9.8402884e-05%. This is a call-frequency ratio, not CPU-time share.

## Authorized 2,000-position corpus

Only defined rates below 0.1% appear below. Denominators differ by event and remain explicit.

| Event | Count | Denominator | Opportunities | Rate |
|---|---:|---|---:|---:|
| nnue_refresh | 2000 | nnue_forward | 12097858 | 0.016531852% |
| capture_futility_prunes | 0 | capture_futility_checks | 3710321 | 0% |
| history_prunes | 993 | history_checks | 7754531 | 0.012805417% |

Full NNUE refreshes: 2000 / 12097858 forward evaluations = 0.016531852%. This is a call-frequency ratio, not CPU-time share.

## Interpretation

The table describes this fixed workload and current search eligibility checks. A rare cutoff may still protect critical tactical cases. Selective pruning and extension rates must be judged with their listed opportunity counts; rates with different denominators are not directly comparable. No feature is removed by this instrumentation patch.

Accepted source/network remain h256_e12. Buffer-fixed B qualification is separate and remains pending at table creation.

The zero capture-futility count is expected in the locked defaults: `tune::CaptureFutilityBase = 0` (src/search.cpp:64), and the prune requires `CaptureFutilityBase > 0` (line1224). Its opportunity counter runs before that default-disable guard. This observation does not identify a pruning defect or justify changing its default.

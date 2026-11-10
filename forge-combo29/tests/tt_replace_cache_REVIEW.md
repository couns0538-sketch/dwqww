# TT replacement-score cache: bounded correctness evidence

Source candidate 2da9593 (exact revision in receipt). Default-off
FORGE_SPD_TT_REPLACE_CACHE changes only the replacement scans in both NOTLS
implementations. The complete occupied-key hit scan stays before replacement;
BoundNone holes remain supported. First empty selection and strict-less tie
order are unchanged. Only an occupied first slot initializes the cached score.
The stripe lock or exclusive lease keeps entry payloads stable through the scan.

Validation command:
`python3 forge-combo29/tests/tt_replace_cache_validate.py /workspace/shared/forge-build/tt-replace-cache`

Source-only isolated snapshot contains only src/include, not bundled binaries.
Compiler commands and binary/test hashes are in tt_replace_cache_receipt.json.
GCC14 O3, NNUE256, strict FP, x86-64-v4 engine flags match the immutable lock.
Only the candidate switch differs between engine0 and engine1. No other new
review switches were enabled in this isolated experiment.

- Off binary is byte-identical to immutable lock: SHA256
  1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6.
- On binary SHA256
  7dadb780b66205a78122cc28c14201fcaf59ee883f31321a1931db43ec98d01c.
- All four NOTLS0/1 x cache0/1 variants pass existing public TT contracts under
  TSan, including 4 threads x 5000 concurrent operations per variant, with no
  reported race. Lifecycle operations remain quiescent.
- Each also passes 4096 seeded public-API selected-slot oracle cases, including
  depth extremes, equal-depth/equal-age ties, generation wrap, arbitrary
  BoundNone holes and later-slot hits. The oracle uses the original strict-min
  rule. Existing contracts additionally cover early empty selection.
- Engine candidate passes all ten immutable depth11/13/16/20/22 pins, NNUE on
  and off, and startpos perft5=4865609; full signatures retained in pins log.
- All 256 cold-TT depth7 comparisons on 128 deterministic FENs match baseline
  depth/nodes/score/bestmove/PV in both NNUE modes, Threads1 Hash16 OwnBookfalse.
  Complete raw compared fields are retained in the equivalence JSON.

The test harness includes existing contracts with their main renamed but never
called; GCC warns about that unused renamed function's implicit return. Actual
contract functions are called directly; this is not a sanitizer failure.

## Generated code and limits

Owned probe disassembly for both binaries is retained. Candidate holds selected
scores in r11d/r12d across the later comparisons, removing selected-winner
payload reloads and age-score recomputation. It also saves more registers after
occupied slot0 (rbp/r13/r12/rbx), so fewer arithmetic operations alone do not
establish a gain. Empty slot0 returns before these saves. The earlier measured
headroom remains narrow, below 0.09 redundant winner recomputations per probe.

This is finite correctness/race coverage, not exhaustive interleaving proof,
combined-switch qualification, native 12k validation, speed or Elo evidence.
Timing remains UNPROVEN pending coordinated isolated diagnostic ABBA. No early
hit-scan exit is implemented: that premise was disproved by BoundNone holes.

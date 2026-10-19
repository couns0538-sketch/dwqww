# Current baseline

Snapshot: 2026-10-19. Correctness validation and playing strength have separate acceptance gates.

| Role | Exact reference |
| --- | --- |
| Accepted development baseline | `forge/6.4-hourly-20261019` — `9108d012526be80c6d163f7cab684e6acd9abf8d` |
| Last fully tested correctness candidate | Forge 6.4.5 source/tests `82cd2c24062d07cbacbe5b722b6ec0b718981abd` |
| Published 6.4.4 checkpoint | `cb1cafa6048976382da6bcd8616da53771176af0` |
| Latest isolated candidate | Forge 6.4.5 legal witness — `82cd2c24062d07cbacbe5b722b6ec0b718981abd`, branch `forge/legal-witness-20261019` |

The [6.4.4 Windows Zen5 ZIP](../releases/forge-6.4.4-candidate-windows-zen5.zip) has SHA256 `d4fc94a529b1b0be89a37adb229433aade6923c8453a565fcf0b06e280171439`. It preserves the AVX2, clock, terminal, promotion and coherent-TT work, and adds the bounded halfmove-context score policy. NNUE weights and float operation order remain unchanged.

6.4.4 passed Release and ASan/UBSan 7/7 CTest suites, eight TSan TT groups, targeted rule-50 checks and 11 legal full-engine TSan searches. Current assertions fail seven times on the frozen 6.4.3 parent. Ordinary cold/warm search parity passed; benchmark node signatures are 419798 on Linux and 351063 on Windows. Five Windows checks passed under Wine. These are finite correctness results; native Windows/Ryzen validation remains pending.

No equal-clock Elo gain, reliable whole-engine speed gain or full-strength Stockfish superiority is established. The accepted reference therefore stays `9108d012`. The exact original 6.4.0 ZIP remains a separate comparison reference.

6.4.5 passed Release8/8, ASan/UBSan8/8,18,947 dual-oracle checks, exact cold/warm
parent parity and seven Wine checks; Linux/Windows signatures remain419798/351063.
Its [Windows ZIP](../releases/forge-6.4.5-candidate-windows-zen5.zip) is separately
packaged. Kernel60/60 blocks completed, but AA noise failed despite pinning, so
speed is inconclusive and the whole-engine screen was not run. Independent
artifact review is pending. No new games/Elo. Follow [status](../validation/legal-witness-20261019/STATUS.md),
[experiment summary](EXPERIMENT_LEDGER.md) and [62-record machine ledger](../validation/EXPERIMENTS.json).

Active unfinished experiment: 6.4.6 qsearch query deferral on `forge/qsearch-query-20261019`, based on tested6.4.5, with production patch reused from upstream3dddd864. Validation is pending.

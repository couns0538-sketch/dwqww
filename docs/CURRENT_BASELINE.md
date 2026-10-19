# Current baseline

Snapshot2026-10-19. Accepted integration `forge/6.4-hourly-20261019` remains
`9108d012526be80c6d163f7cab684e6acd9abf8d`; no strength candidate was merged.

Latest fully tested isolated correctness candidate: **Forge6.4.7**, source/tests
`2c0c7efa49023d8e3f49de3f5596f333a3f01202`, branch `forge/lazy-movepicker-20261019`.
It cumulatively preserves earlier AVX2, clock/terminal, promotion, coherent-TT and
bounded rule50 repairs. The accepted residual NNUE weights are unchanged.

Three sequential speed candidates:6.4.5 legal pawn witness;6.4.6 qsearch pure-query
deferral;6.4.7 lazy MovePicker masks. Each passed Release8/8,ASan/UBSan8/8,
18,947 legal-query comparisons, exact parent cold/warm parity and7Wine checks.
6.4.7 additionally passed60,138 actual ordered-picker comparisons; all3Windows
packages passed independent static audit. Signatures419798Linux/351063Windows.

[6.4.7 Windows Zen5 ZIP](../releases/forge-6.4.7-candidate-windows-zen5.zip) SHA256
`493511ad75bf340e1e0d1c4e0c842277f1987d2db0c80a26d3dfd29376e0aabb`. Wine tests do not establish native Ryzen performance.

NPS and equal-clock Elo remain unproven: whole-engine and pinned-kernel identical-
code calibration failed on this host. All failures are retained. A bounded hosted
Linux pilot is prepared, pending launch/actual results. It compares6.4.4 source
816423b against6.4.7 to isolate the3speed changes; the original6.4ZIP and accepted
9108 reference remain distinct. No full-strength Stockfish superiority exists.

See [69-record ledger](../validation/EXPERIMENTS.json), [concise ledger](EXPERIMENT_LEDGER.md),
[active status](../validation/lazy-movepicker-20261019/STATUS.md) and [next work](NEXT_EXPERIMENTS.md).

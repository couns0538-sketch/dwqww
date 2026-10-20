# Current baseline

Snapshot2026-10-19. Accepted integration `forge/6.4-hourly-20261019` remains
`9108d012526be80c6d163f7cab684e6acd9abf8d`; no strength candidate was merged.

Latest fully tested isolated correctness candidate: **Forge6.4.8**, source/tests
`7125b3379a850de34041d42529cf95993607f93c`, branch `forge/root-effort-20261019`.
It cumulatively preserves earlier AVX2, clock/terminal, promotion, coherent-TT and
bounded rule50 repairs. The accepted residual NNUE weights are unchanged.

Three sequential speed candidates:6.4.5 legal pawn witness;6.4.6 qsearch pure-query
deferral;6.4.7 lazy MovePicker masks. Each passed Release8/8,ASan/UBSan8/8,
18,947 legal-query comparisons, exact parent cold/warm parity and7Wine checks.
6.4.7 additionally passed60,138 actual ordered-picker comparisons; all3Windows
packages passed independent static audit. Signatures419798Linux/351063Windows.

[6.4.8 Windows Zen5 ZIP](../releases/forge-6.4.8-candidate-windows-zen5.zip) SHA256
`4b4de385808f5a383aa60de6bfc09cf48c02e5d23c191624540026cdac95b55e`. Wine tests do not establish native Ryzen performance.

NPS and accepted equal-clock Elo remain unproven. The hosted647versus644run
completed with a positive native144game snapshot(+43.66±28.69Elo), but its
16min deadline left an orphan among147normal records; no SPRTboundary was
reached. Independent73pairGLR0.815 remains inside±2.944. These are promising
descriptive results, with originals preserved; nothing transfers to648orStockfish.
The [new648offlineWindowsbundle](../releases/forge-6.4.8-windows-validation-bundle.zip)
is manifest/read-only-runtime verified; nativeAA/pilot/SPRT remain pending.

See [76-record ledger](../validation/EXPERIMENTS.json), [concise ledger](EXPERIMENT_LEDGER.md),
[active status](../validation/lazy-movepicker-20261019/STATUS.md) and [next work](NEXT_EXPERIMENTS.md).

6.4.8 separately repairs demonstrated root-effort attribution: c3d5 now601nodes rather than1355mixedordinalnodes. Release8/8,ASan8/8,all28actualtraceoracleiterations,parentuntimedparity and7Winechecks+52/52artifactauditpassed. Timed/Eloeffect unmeasured; hosted6.4.7results do not transfer. See [root status](../validation/root-effort-20261019/STATUS.md).

# Current baseline

Accepted integration `forge/6.4-hourly-20261019` remains
`9108d012526be80c6d163f7cab684e6acd9abf8d`. Do not reset newer candidates.

Latest fully correctness-tested isolated source is **Forge6.4.10**,
`36f5b2f6e1ff519e82a4b52edc85caceaf15aed0`, branch
`forge/nnue-update-fusion-20261019`. It preserves6.4.9 and every earlier candidate
repair, the accepted residual NNUE and training infrastructure. Its new count-two
remove/add update fuses three passes into one with identical float operation order.

Release9/9 and ASan/UBSan9/9 pass. The1644case update stream and original
21.2MBNNUEstream match parent and Windows byte-for-byte; the new ASan and
x86-64-v2/SSE update streams match too. Eight Winechecks and independent
Windowsartifactaudit pass. Exact cold/warm1T parent search parity and benchmark
signatures419798Linux/351063Windows remain unchanged.

WindowsZIP: `releases/forge-6.4.10-candidate-windows-zen5.zip`,
SHA256 `771ea7ab84bd86a006c6197af56e81911625224144f33d3fd59ebcb51d5ecd2a`.
These are Wine results, not nativeRyzen performance.

NPS/Elo remain unproven. Fresh hosted performance39334266771 stopped after
12same-binaryAAprocesses failed its strict3%noisegate. No A/B/kernel ran; all
actualsource/binaries and finalhashes survive on results/nnue-performance-39334266771-1.
Do not repeat the same attempt or widen its gate. Retain the optimization.

Fresh equal-clock647versus644run39332822379 is active and separate. Its sources
do not include6.4.8–6.4.10. Earlier147gameattempt is inconclusive; the144game
+43.66±28.69snapshot is descriptive and never pooled with the fresh test.

Next bounded source experiment: extend exactoperation-order one-pass updates to
three-change captures, as a new isolated6.4.11candidate. A larger independently
frozen official8movesbook is available for subsequent strength testing.
Read [ledger](EXPERIMENT_LEDGER.md), [next work](NEXT_EXPERIMENTS.md) and
[active evidence](../validation/nnue-update-fusion-20261019/STATUS.md).

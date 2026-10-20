# Current baseline

Accepted integration `forge/6.4-hourly-20261019` is
`356e863dbd86d2ce24b8ee9486d7406f1d525480`. Engine repair
`294cf1ba7d2e3e77a70a08578958a5faea3b54dd` charges timed UCI admission delay,
preserving the earlier TT repair and untimed/ponder behavior. The former
`2fc649e` metadata / `9108d012` source checkpoint is historical. This is timing
correctness, not an accepted Elo gain. [Integration evidence](https://github.com/couns0538-sketch/dwqww/blob/294cf1ba7d2e3e77a70a08578958a5faea3b54dd/validation/hourly/2026-10-20-go-origin-native/INTEGRATION_REPORT.md).

Latest correctness-tested isolated candidate is **Forge 6.4.12**,
`8865666cc0ab4961cd507bae40ff6ce44e9319df`, preserving 6.4.11 and earlier work.
Its opt-in single-worker TT gate drains stripes sequentially; shared/default
and SMP remain synchronized. Release, ASan/UBSan and TSan each passed 9/9
CTests; seven actual-API groups per profile, eight active-UCI TSan edges and
eight Wine checks plus independent artifact audit passed. Six parent cold/warm
cases remain exact; bench signatures remain 419798 Linux / 351063 Windows.
Mutex acquisitions 706157→8204 establish fewer operations only. The rejected
all-held-stripes prototype `a5d2fcb5` and its default TSan held-lock-limit failure
remain retained; no detector was disabled.

Windows ZIP `releases/forge-6.4.12-candidate-windows-zen5.zip`, SHA-256
`09a445d6bc14ffd866bc90b5a3530cb45bb858a158bfc9028fdc408790e298b3`.
This is Wine correctness, not native Ryzen performance. Frozen886 already
accounts for timed admission but differs from the newer accepted untimed/ponder
reporting contract. A separate regression/follow-up is underway; do not mutate
the frozen strength source.

Both original strength runs completed validly and **inconclusively**:

- 6.4.7 versus 6.4.4: 320 games, W114 D101 L105, independent LLR0.457429,
  natural160-pair cap; all2794 final-audit checks passed. Original push failed
  on its152.78MB log. Recovery1 failed an inventory-order check; corrected
  tests17/17 passed; recovery2 succeeded at results `61aabe2`.
- 6.4.11 versus 6.4.9, run39348571407: 2048 games, W427 D1194 L427,
  independent LLR−0.756524236, natural1024-pair cap. Final archive/source,
  41-input, opening, full legal-replay and complete raw-log audit passed;
  results `eb1c1b7`.

The fresh 6.4.12 versus 6.4.11 protocol is **launched once**, run39403471059 at frozen launchb48af4c:0/+5 SPRT,1024 fresh pairs, equal2+0.02, serial
Threads1/Hash32/OwnBookfalse. All30proof hashes/23package entries pass.
[Finished job](https://github.com/couns0538-sketch/dwqww/actions/runs/39403471059) failed on a baseline time forfeit by45ms. Original84records/42pairs (W13/D59/L12) are invalid for strength acceptance. Final frozen-input rehash passed; raw resultsffc598ad. No retry; exact UCI failure audit is underway.

New isolated6.4.13 source `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d` merges accepted356e and preserves886. It scopes automatic origin to finite timed searches and retains both timestamp names with accepted start_time priority. Release9/9 passed; remaining sanitizer/API/Windows proof is underway. This clock-reporting correction is not a demonstrated remedy for the baseline time forfeit.

No NPS/Elo gain is accepted; no result transfers across candidates or games are
pooled. Failed strict3% timing A/A receives no retry or widened threshold.
Native Windows/Ryzen and full-strength Stockfish superiority remain unproven.
Read the [ledger](EXPERIMENT_LEDGER.md), [next work](NEXT_EXPERIMENTS.md),
[6.4.12 evidence](../validation/single-thread-tt-20261020/STATUS.md),
[confirmation audit](../validation/hosted-confirmation-20261019/final-audit/REPORT.md)
and [NNUE audit](../validation/nnue-strength-20261019/final-audit/AUDIT.md).

# Next experiments

1. Launch the reviewed 6.4.11 versus 6.4.9 paired strength test once. Use the
   frozen `.github/hosted-nnue-strength/` protocol: 0/+5 SPRT, 1,024 fresh pairs,
   equal 2+0.02, serial Threads1/Hash32/OwnBookfalse. Preserve complete original
   PGNs, logs, actual binaries and source exports. Any fault, deadline, orphan
   or changed input invalidates acceptance. A natural cap is inconclusive.
2. Audit the separate 6.4.7 versus 6.4.4 confirmation run39332822379 when its
   actual results branch appears. Do not infer completion from elapsed time or
   pool earlier pilot games. Replay original PGNs and rehash actual binaries.
3. Finish the bounded actual-search counter investigation of repeated NNUE
   output inference. Implement a cache only if duplicate calls are demonstrated;
   invalidate on every real/null move, new search and clear. Retain TT priority
   and recompute HCE/corrections. Keep the long test's frozen source unchanged.

Keep all existing candidate branches and the accepted integration's newer
2fc649e metadata. The accepted engine source remains9108. The older TT-tag
timeout/truncated replay remains unresolved; its blocked archive must retain
its publication hold. It uses different sources/settings/runner and proves
neither failure nor clock reliability for the new serial tests.

The strict hosted performance profile39334266771 failed same-binary AA and
ran noAB/kernel. Do not retry it or widen its threshold. Local shared-VM
small-speed measurements also failed calibration. No NPS or Elo gain is
accepted; no native Windows/Ryzen or full-strength Stockfish superiority exists.

The new bounded job may continue independently of chat. There is no persistent
24-hour agent or six-hour chat scheduler; record actual run and monitoring state.

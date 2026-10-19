# Lazy MovePicker check masks: implementation pending validation

6.4.7 is isolated on forge/lazy-movepicker-20261019, preserving6.4.6 source4e15dea
(published2ce76ad), all earlier candidates and the residual NNUE unchanged.
Accepted integration remains9108d012.

Move the identical direct-check-mask calculations from every constructor into
quiet/evasion generation, the only consumers. These stages are mutually exclusive
and each runs at most once. No new boolean/member, move ordering, scores, sorting,
pruning or evaluation changes. Ordinary qsearch and earlier cutoffs avoid work.
Every caller restores the parent Board before requesting another move.

The actual patch's control-flow and board-restoration proof is preserved in
preparation.zip. Root omitted only a redundant helper comment versus the proposal.
Next: frozen Release build, all8 suites, exact parent cold/warm parity, appropriate
ASan/UBSan, Windows functional/signature checks and meaningful actual-MovePicker
ordered-stream differential checks across corpus and special positions.

Timing remains blocked on this shared host by failed old full-engine and fresh
pinned-kernel AA gates. Do not claim NPS/Elo, infer benefit from fewer calculations,
or repeat failed protocols. A separately calibrated hosted pilot may be attempted;
no game, hosted acceptance or native Ryzen result exists for this source yet.

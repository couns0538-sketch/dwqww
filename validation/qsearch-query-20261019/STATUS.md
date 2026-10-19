# Qsearch query deferral: implementation pending validation

Parent correctness candidate6.4.5 production/tests82cd2c2, published63ee572.
Accepted integration remains9108d012. The residual NNUE and all earlier isolated
improvements are preserved. No accepted new Elo or NPS gain exists.

Reuses the actual upstream3dddd864d45288787b6e949dca5528e88be9f535
one-line declaration relocation, independently reviewed against current source.
Only compute Board::gives_check when its sole qsearch use guard is true.
Checking evasions and the mating-loss branch omit this pure Boolean query;
move legality, count, ordering, board updates, pruning predicates and scores
are unchanged. Main search's separate query remains in place.

6.4.6 is isolated on forge/qsearch-query-20261019. Next: freeze source, compile
Release, run all8 suites and exact parent cold/warm parity, then ASan/UBSan and
Windows checks. Existing actual-Worker rule50 checked-evasion tests exercise
the deferral path. No new mirror-of-implementation unit test is needed.

Performance/strength gates remain open: prior same-binary full-engine and pinned
kernel noise gates failed on this host; do not restart timed VM/Wine matches or
claim gains from omitted work. Preserve proposals, source, builds and raw logs.

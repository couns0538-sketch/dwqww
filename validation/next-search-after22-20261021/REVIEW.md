One next hypothesis, source-only — ff2e269c6058be84456e3b98344826d17b0056eb

Current search/header/NNUE-weight hashes match EXPECTED-FROZEN22-SOURCE-77.json.
Read current NEXT/EXPERIMENT_LEDGER, prior next-search/proposed quiet-evasion leads,
initial search-history audit and actual22 singular repair. No Git command, engine,
compiler, timing, patch or production edit. Only this new report directory written.

Rank1: ablate TT refresh-on-hit as an explicit recency policy.

search.cpp:262-263 immediately returns a coherent hit without refreshing generation.
Replacement at:267-271 penalizes an entry by4*age; new_search advances generation
(search.hpp:119). Thus an entry just reused from the previous search still ages as
though unused, until some later store overwrites it. Direct TT cutoffs (:910-914,
qsearch:782-786) return without a store, so useful reused bounds can remain old.
This policy is unimplemented in current source; targeted ledger/proposal searches
found no completed refresh-on-hit experiment. It is NOT a correctness defect.

A bounded candidate would refresh only the generation bits on a verified occupied
hit, while holding the EXISTING stripe lock or valid exclusive lease, before making
the value snapshot. Keep score/eval/depth/move/rule50/PV/bound bits, opaque selected
slot/key/epoch validation, and stop/join-only lifecycle contracts. No unsynchronized
access, lock removal or new network. Controller-owned1T leasing is already applied
(:218-220,uci.cpp:357/403); do not rediscover that speed change.

Important coupling: generation also affects same-position overwrite eligibility
(:287) and hashfull (:303). Refreshing it may protect an old deep score from a
later shallow nonexact store that previously overwrote solely due to age. This is
an explicit coupled TT-policy ablation, NOT a behavior-preserving cache optimization.
Do not accidentally claim replacement-only causality or preserve exact warm trees.

Quick falsifier: actual-table four-colliding-key fixture. Store A depth12 at gen0;
advance search, store B/C/D depth8 at gen1; probe A without storing; then probe a
fifth colliding key. Baseline chooses A (12-4 ties8, first-slot tie); candidate
should choose B after refreshing A. Also freeze/test the shallow same-key store
and hashfull consequences, generation wrap, rejected stale handles, snapshot
independence and concurrent correlated tuples under existing locking. Cold/new-
table1T behavior should remain exact; warm-search behavior deliberately may change.

Before implementation: one bounded actual-search observer should count old-generation
usable hits returning without store and later eviction pressure on those slots.
If absent/negligible, deprioritize. If frequent, freeze ONLY this policy variant and
run full correctness/TSan, then fresh preregistered equal-clock paired strength.
Retaining hot old bounds can save work; keeping stale/selectively misleading bounds
can regress. No gain or probability of gain is established by this source review.

Same-frame triage, not extra ranked bugs: current_move/moved_piece/continuation are
reassigned before the selected child (:1105-1107). Existing25RED observations kept
in_check/raw/static unchanged. History/killers intentionally learn during search;
blanket frame rollback lacks evidence. High-depth null verification (:978-981)
also reuses ss without PV-flag restoration, but its caller is nonPV; the proven
outer-PV→nonPV mechanism does not directly transfer. Require an actual before/after
witness before another repair. No new same-frame bug is claimed here. Previously
reported quiet-evasion-history and sparse-null-material leads remain pending,
not new findings or accepted improvements.

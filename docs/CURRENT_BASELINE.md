# Current baseline

Accepted integration `forge/6.4-hourly-20261019` remains
`356e863dbd86d2ce24b8ee9486d7406f1d525480`, with timed-only admission repair
`294cf1b`. Preserve it; no accepted Elo gain is established.

Latest isolated correctness-tested engine is **Forge6.4.13**, source
`cecf0b9e3af5602053bcaf5c5d16ffc09f58850d`, branch
`forge/clock-contract-reconcile-20261020`. It merges the newer accepted work
and preserves6.4.12's TT gate, both NNUE fusions, weights and earlier repairs.
Accepted start_time takes precedence over legacy request_start. Automatic
clock origins apply only to finite timed searches; untimed/ponder reporting
stays worker-local. Ponder budgets still start at hit.

Release, ASan/UBSan and TSan each passed9CTest+7main-origin+7actualTTAPI groups.
Eight active UCI TSan transitions and six exact parent cold/warm cases passed.
Bench signatures419798Linux/351063Windows are unchanged. Original invalid
GNU-wrap observation is retained; corrected interposition observes three helpers
and demonstrates actual old5RED/new7GREEN. Windows8Winechecks and872independent
artifact checks passed. [Proof](../validation/upstream-clock-reconcile-20261020/STATUS.md).

[Windows Zen5 ZIP](../releases/forge-6.4.13-candidate-windows-zen5.zip), SHA256
`ca2512f2b7a91a3b9e391992fa8e5ebc622e79daa5a9fcc088f3b2819a74cbb7`.
Wine is not native Ryzen performance. No calibrated NPS or positive Elo gain.

The6.4.12-versus6.4.11 TT run39403471059 is invalid: Baseline forfeited in
started game85. All84completedrecords (W13/D59/L12) remain retained; no strength
or TT regression inference. Response observation108.696ms versus63ms remaining
does not isolate the delay. [Original evidence audit](../validation/tt-strength-20261020/final-audit/REPORT.md),
results `ffc598ad12760e5cdc8cb1ee15383f13787acad8`. No retry or threshold change.
The6.4.13 reporting repair is not a demonstrated remedy for this forfeit.

Earlier valid capped matches are inconclusive:6.4.7vs6.4.4 W114/D101/L105
(320games, results61aabe2 recovered original evidence), and6.4.11vs6.4.9
W427/D1194/L427 (2048games, resultseb1c1b7). No accepted gain or game pooling.

Next bounded candidate repairs extension-path bookkeeping. Actual bench trace
found5038child-count mismatches; an isolated17-line proposal clears all seven
mismatch classes with the same419798nodes. Eligibility mismatches were already
zero in this shallow workload, so neither changed decisions nor Elo is proven.
[Investigation](../validation/double-extension-path-20261020/REPORT.md).

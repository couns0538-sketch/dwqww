# Current baseline

Accepted integration `forge/6.4-hourly-20261019` is now
`5101c2529d386b7c3a04ba9156a69ee34df6bb43` (remote fast-forward verified
2026-10-20 20:44:42UTC). It adds the existing one-line OwnBook repair af19413 and
its unchanged native regression to356e863, preserving the TT and timed-only clock
repairs. Acceptance is for the finite book contract; no accepted equal-time Elo gain.
[Integration receipt](../validation/accepted-ownbook-integration-20261020/INTEGRATION.json).

Latest isolated finite-tested candidate is **Forge6.4.18**, source
`fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`, branch
`forge/correction-history-residual-20261020`. It changes one correction-history
update from EMA toward an already-corrected residual to residual increments under
unchanged guards, weights and clamps. It preserves all17work and accepted5101.
**First-attempt Release10/10, ASan/UBSan10/10, default TSan10/10 and8active UCI
transitions PASS. Nine Wine checks and1064independent artifact checks PASS.**
[Native proofs](../validation/correction-history-native-20261020/ROOT-NATIVE-PROOFS.json).
[Windows proofs](../validation/correction-history-windows-20261020/ROOT-WINDOWS-PROOFS.json).

[Windows Zen5 candidate ZIP](../releases/forge-6.4.18-candidate-windows-zen5.zip),
SHA256 `286a913f8bb6366d28020ef83bce5235809d1d991d41023609f0ea6446284ebc`.
Actual native/Windows bench11signatures321912/352313 are reproducibility checks;
no calibrated NPS difference, Elo gain or native Windows/Ryzen result follows.
The actual-method fixed6cp target learns6cp versus old3/4cp, while the larger64cp
reachable envelope and retention of noisy/aliased feedback are explicit risks.
This is an **unaccepted search ablation**, not a demonstrated bug repair.
[Experiment](../validation/correction-history-residual-20261020/RESULTS.md).

Fresh18vs17 strength preparation is BLOCKED/unlaunched: actual canonical captures
now pass; independent review requires final rehash coverage for proof files and
mandatory source/build provenance before READY. Draft0/+10,.05errors,equal10+0.1,
256paired openings; no games or Elo result. Historical17binary/source47proofs remain
genuinely labeled47; all72build inputs equal baselineb590byte-for-byte. A future
hosted attempt must build actualb590 and pass all9baseline CTests before games.

Previous isolated finite-correctness-tested engine is **Forge6.4.17**, source
`47f0560221d986e41a309853e1295c557fcf5bf6`, on
`forge/promotion-see-20261020`. It preserves prior accepted work, residual NNUE
and its weights, and repairs promotion-recapture SEE before threshold shortcuts.
First-attempt Release9/9, ASan/UBSan9/9, TSan9/9 and8active UCI TSan checks PASS.
The actual qsearch witness changes SKIP_SEE to a searched legal Qxb8 capture;
324legal oracle cases and30actual search-margin answers pass. These are correctness
results, not Elo or a general startup/clock-reliability claim.
[Native proofs](../validation/promotion-see-20261020/native/ROOT-NATIVE-PROOFS.json).

[Windows Zen5 candidate ZIP](../releases/forge-6.4.17-candidate-windows-zen5.zip)
SHA256 `9c532d5394b58f8654e316de99b4a5771149e75327c31586ae179814212e85f9`.
Eight Wine checks passed;1211artifact checks passed after one README case-comparison
checker repair, with the original failed checker/logs retained and binary unchanged.
Linux/Windows bench11signatures385781/382424 are reproducibility checks.
No calibrated NPS difference or native Windows/Ryzen result is established.
Complete source/build/raw/qsearch/Windows evidence is verified and split-archived in
[archive-complete](../validation/promotion-see-20261020/archive-complete/).

**The one hosted17vs14 attempt failed in the harness before any games.**
Run[39492317400](https://github.com/couns0538-sketch/dwqww/actions/runs/39492317400),
results commit `0e292d6193918fa71a06b99798808ecb60e5807a`.
Both frozen engine builds and their CTests passed; baseline gross A/A passed.
The candidate emitted the correct `info string bench depth 11 nodes 385781 ...`,
but the readiness parser expected prefixless `bench ...`. Its mock GOOD fixture
shared that error. The original failed attempt and frozen package remain unchanged.
All75original payloads and40frozen inputs have been independently verified.
Candidate returncode/group-empty facts were not separately saved before the parser
raised, so full candidate readiness is not independently proved. **Games0; W/L/D0/0/0;
no Elo estimate, confidence interval, NPS comparison or H0/H1 decision.**
[Independent audit](../validation/hosted-promotion-see-strength-20261020/final-audit/REPORT.md).
No match is currently running; no retry, resume or second trigger has occurred.

The accepted-lineage OwnBook bypass was reproduced on356e863. Exactexisting
repair af1941375111717f415a46d9ce0224c329034466 and child5101c252 passed both
Release4/4 suites and candidateASan/UBSan4/4; unchanged original book tests
reproduced the parent leak and suppressed it in both candidate profiles.
The independent807check audit and root76payload/binary-byte review passed.
Evidence was published at67aa4fed2a4f0d9d46d395e7815420001028e3fb before the
non-forced fast-forward. Current17lineage merges5101at3105720 with every production
byte unchanged; source47f0560 and its failed frozen attempt remain immutable.
Historical CI success metadata was verified, but authenticated original artifacts
could not be retrieved; the fresh local originals are separate evidence.

Both user handoffs are manifest/byte verified (145shutdown +28clock-replay payloads).
The original108.696ms response,84.647ms last-info discrepancy and0.049ms final gap
were independently recomputed; they do not locate the historical time-forfeit cause.
No new clock patch follows. Forge is the priority; GrokChess port is deferred.
[Handoff reviews](../validation/handoffs-20261020-1916-2120/HANDOFF.md).

Preserve prior failures:16original TSan batch8/9 initial UCI deadline,14original
60s barebench timeout, and12vs11 baseline time forfeit in startedgame85. Later
successful bounded diagnostics did not reproduce or explain those anomalies.
Earlier valid capped647vs644 (320games,W114/D101/L105) and6411vs649
(2048games,W427/D1194/L427) remain separate/inconclusive. Never pool them.
Details and next work are in[ledger](EXPERIMENT_LEDGER.md) and
[next experiments](NEXT_EXPERIMENTS.md); historical records remain in Git.

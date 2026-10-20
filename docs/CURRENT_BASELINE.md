# Current baseline

Accepted integration `forge/6.4-hourly-20261019` is now
`5101c2529d386b7c3a04ba9156a69ee34df6bb43` (remote fast-forward verified
2026-10-20 20:44:42UTC). It adds the existing one-line OwnBook repair af19413 and
its unchanged native regression to356e863, preserving the TT and timed-only clock
repairs. Acceptance is for the finite book contract; no accepted equal-time Elo gain.
[Integration receipt](../validation/accepted-ownbook-integration-20261020/INTEGRATION.json).

Active next candidate **Forge6.4.20**, source
`fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`, branch
`forge/pawn-span-fill-20261020`, replaces a per-enemy-pawn outpost-span traversal
with an unsigned8/16/32 directional fill of the existing attack mask. Prototype
version19 passed12Release CTests,37320mask checks and95public cached/uncached/full
trace positions (61465integers identical). Original first fixture and one relocated
link-dependency-path failure are preserved; final label-only fixture passes.
Frozen20 differs from final prototype only in CMake/UCI version strings.
**Full frozen20native qualification is running; no20speed/Elo/Windows result yet.**
[Source freeze](../validation/pawn-span-fill-native-20261020/ROOT-FROZEN-SOURCE-GATES.json).
[Public trace evidence](../validation/pawn-span-fill-20261020/independent-review/PUBLIC-DIFFERENTIAL.md).
Latest fully qualified workload-speed source remains19 below; accepted5101unchanged.

New isolated performance candidate **Forge6.4.19** is frozen at
`61f598056572dfade6994af8ad2e38817cd28aa3`, branch
`forge/lazy-runtime-psqt-20261020`, remotely verified. It reuses classical PSQT
and unclamped phase alongside existing lazy NNUE dirty-state replay, privately per
Worker. Board, NNUE/weights and public evaluator/tuner contracts are preserved.
**First-attempt Release11/11, ASan/UBSan11/11, default unsuppressed TSan11/11,
347runtime assertions in each profile, and8active TSan UCI checks PASS.**
56cold/warm searches match18 exactly (including NNUE-off), excluding only time/NPS;
bench321912. Independent native audit2298/2298 PASS after one saved checker-key
correction; all engine gates passed first attempt. Root rehashed251evidence files,
524live source/build originals and6single originals. The NNUE compiled object is
byte-identical to18, preserving the existing strict floating-kernel validation.
Windows19 first build, all10Wine checks,1184independent artifact checks PASS;
347runtime assertions,18947legal comparisons, exact352313. Root byte-verified all
205raw payloads,71sources,219unchanged parent files and8actual built PEs.
[Native proof](../validation/lazy-runtime-psqt-20261020/root-verification/NATIVE.json).
[Windows proof](../validation/lazy-runtime-psqt-20261020/root-verification/WINDOWS.json).
[Windows19 Zen5 ZIP](../releases/forge-6.4.19-candidate-windows-zen5.zip), SHA256
`f0ec03308098bf8e675647f091b3b1afeb74d2632d9c972883e5907cfcb23d85`.
**Verified hosted whole-process throughput gain versus18:** CPU+1.6084%
(95%block-bootstrap interval+1.2336..+1.9498%); wall+1.5990%
(+1.2217..+1.9459%). One frozen run39510219605 passed15same-binary A/A blocks,
31A/B blocks, all188processes/940canonical rows and every final integrity gate.
Independent calculation agrees within1e-12. Root compared all160consumed byte
records and200actual Git blobs, including both complete73/74source exports;
both hosted compiled NNUE objects are bit-identical. Keep this optimization as a
qualified Linux workload improvement. **No Elo gain, nativeWindows/Ryzen result or
Stockfish superiority is established; accepted integration remains5101.**
[Independent performance audit](../validation/hosted-runtime-psqt-performance-20261020/final-audit/REPORT.md).
[Root Git/input audit](../validation/hosted-runtime-psqt-performance-20261020/ROOT-INPUT-AUDIT.json).
Original result commit0124dbd075b252552a27264996b72cf2ef800598; frozen launch
payload5e50d99a93a381a881b4f1813dce462a3e4106bf. No retries or pooled outcomes.
Complete19checkpoint is independently verified:1762originals/1774payloads,
112207796bytes, combinedSHA256
`d90110e326c6d24c3045c8601ed4dd37ba7b9fbfc35c1bffcabddab6cf733f31`.
Both published parts were downloaded and hash verified. File/directory modes are
recorded; generic0600ZIP modes require explicit restoration in a NEW empty scratch
destination. Actual extraction/chmod recovery was not run.
[Archive proof](../validation/lazy-runtime-psqt-20261020/archive-complete/ROOT-VERIFY.json).
[Published part verification](../validation/lazy-runtime-psqt-20261020/archive-complete/REMOTE-PARTS-VERIFY.json).
[Prototype history](../validation/lazy-runtime-psqt-20261020/REPORT.md).

Latest isolated finite-tested candidate is **Forge6.4.18**, source
`fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`, branch
`forge/correction-history-residual-20261020`. It changes one correction-history
update from EMA toward an already-corrected residual to residual increments under
unchanged guards, weights and clamps. It preserves all17work and accepted5101.
**First-attempt Release10/10, ASan/UBSan10/10, default TSan10/10 and8active UCI
transitions PASS. Nine Wine checks and1064independent artifact checks PASS.**
[Native proofs](../validation/correction-history-native-20261020/ROOT-NATIVE-PROOFS.json).
[Windows proofs](../validation/correction-history-windows-20261020/ROOT-WINDOWS-PROOFS.json).
Complete checkpoint:1,434live originals and1,446archive payloads independently
byte verified, including full native/prototype/Windows source and build trees.
Two parts, combinedSHA256
`fc000c6fc58b38c023d636880e82bf191b297fc8b7ea529d9c14153c8fbe5868`.
[Archive receipt](../validation/correction-history-native-20261020/archive-complete/ROOT-VERIFY.json).
All earlier failed attempts and directly published raw files remain retained.


[Windows Zen5 candidate ZIP](../releases/forge-6.4.18-candidate-windows-zen5.zip),
SHA256 `286a913f8bb6366d28020ef83bce5235809d1d991d41023609f0ea6446284ebc`.
Actual native/Windows bench11signatures321912/352313 are reproducibility checks;
no calibrated NPS difference, Elo gain or native Windows/Ryzen result follows.
The actual-method fixed6cp target learns6cp versus old3/4cp, while the larger64cp
reachable envelope and retention of noisy/aliased feedback are explicit risks.
This is an **unaccepted search ablation**, not a demonstrated bug repair.
[Experiment](../validation/correction-history-residual-20261020/RESULTS.md).

Fresh18vs17 strength preparation has closed the independently identified proof
rehash and mandatory-provenance gaps. The original disabled phase2 is preserved
at `be2033884a2cd82c5c9bd8d4b56dc2ca6ed72acd`;96 offline tests passed there.
Root binds335 exact finite proof files and verifies24 package/workflow entries.
After enabling the restricted first-attempt-only push workflow,94 applicable
offline tests and9 actual missing-gate controls pass. Two historical draft-state
assertions remain unchanged and are replaced by explicit READY/negative checks.
Final enabled-metadata review PASS; payload `1203e13cfd80451d7194c7fba2f775de71dc9604`
was published and one trigger push remotely verified at21:39:20UTC. Run
[39502109381](https://github.com/couns0538-sketch/dwqww/actions/runs/39502109381)
has passed the hosted source-build/test step; combined readiness/SPRT step is
running at22:44:08UTC. Public metadata does not expose games or prove a particular
readiness subgate. Frozen0/+10,.05errors,equal10+0.1,256paired openings; no observed
game statistics or Elo result. Do not trigger/retry/resume this experiment.
Historical17binary/source47proofs remain genuinely labeled47; all72build inputs
equal baselineb590byte-for-byte. The hosted attempt must build actualb590 and
pass all9baseline CTests before games; candidate must pass all10.

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
That17attempt has not been retried or resumed. The independent18vs17run above
uses a different hypothesis and fresh opening cohort, with no pooling.

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

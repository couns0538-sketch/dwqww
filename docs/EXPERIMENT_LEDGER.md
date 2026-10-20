# Experiment ledger

The authoritative [machine ledger](../validation/EXPERIMENTS.json) preserves all 83 earlier IDs and six new records (89 total), exact inputs, hashes, settings, failures and evidence links. This is the concise reading index as of 2026-10-20.

| Experiment | Observed result | Acceptance scope |
| --- | --- | --- |
| Historical accepted `9108d012` | TT index/signature independence repair | Preserved reference, superseded by current accepted clock repair |
| Current accepted `356e863` | Timed-only admission-clock repair `294cf1b`, preserving TT repair and untimed/ponder behavior | Native correctness/admission-delay checks; no accepted Elo gain |
| AVX2, clock/stalemate, underpromotions | Arithmetic and regression checks passed on their recorded sources | Correctness/kernel evidence; timed VM attempts invalid |
| 6.4.1 versus original ZIP | 178 normal games, W/D/L 66/44/68; paired GLR −3.02565, H0 accepted for [0,+20] | Fixed 10,000 nodes/move only; no accepted gain or equal-clock inference |
| 6.4.3 coherent TT | Actual parent race reproduced; corrected Release/ASan suites and 38 full-engine TSan searches passed | Finite correctness; first faulty stress fixture retained |
| 6.4.4 score context | Forward/reverse regressions repaired; seven current parent assertions fail, candidate assertions pass | Release/ASan/TSan, ordinary behavior parity and Wine correctness passed |
| Same-binary speed A/A | 72 sessions/216 searches; one-thread wall ratios 0.6566–1.4704; identical work reported 339–1730 ms | Whole-engine overhead inconclusive; full A/B stopped |
| Windows artifacts/readiness | 6.4.4 five Wine checks passed; original 6.4.2 bundle remains immutable; a separate 6.4.8 bundle is now audited | No native Windows, physical Ryzen or Elo result |
| 6.4.5 legal witness | Parent and actual `82cd2c2` each passed18,947 oracle/state checks; Release8/8, ASan8/8 and exact parent parity passed | Seven Wine checks passed; kernel AA failed, speed/Elo inconclusive |

Original failures remain available, including timed forfeits, opening-representation rejection, the null-move stress fixture, incomplete manifest inventory, copied audit/launch metadata and incorrect package wording. No invalid games, separate candidates or microbenchmark ratios are pooled into cumulative Elo.

Immutable archives: [TT correctness](../validation/tt-coherence-20261019/complete-linux-correctness-checkpoint.zip), [speed A/A and independent audit](../validation/tt-coherence-20261019/speed-aa-calibration.zip), [rule-50 investigation](../validation/rule50-context-20261019/investigation-before-integration.zip), and [6.4.4 Linux validation](../validation/rule50-context-20261019/linux-validation-checkpoint.zip). See [current references](CURRENT_BASELINE.md) and [next experiments](NEXT_EXPERIMENTS.md).

6.4.5 original [kernel records](../validation/legal-witness-20261019/kernel-attempt1.zip) retain all60 blocks, failed calibration and descriptive ratios; they are not an accepted speed result.

6.4.6 qsearch pure-query deferral (`4e15dea`): Release8/8, ASan8/8, exact cold/warm parent parity and7Wine checks passed.419798/351063 signatures unchanged; no measured NPS/Elo. [Evidence](../validation/qsearch-query-20261019/STATUS.md).

6.4.7 lazy masks (`2c0c7ef`): Release8/8, ASan8/8, exact parent parity,60,138 byte-identical actual picker rows,7Wine checks and independent artifact audit passed. NPS remains unmeasured; hosted Elo attempt is inconclusive (see final result below). [Raw evidence](../validation/lazy-movepicker-20261019/STATUS.md).

Historical checkpoint before completion: run 39325939081 had started and build/tests had succeeded. Its then-running status is superseded by the audited final result below. No second workflow attempt was launched.

6.4.8 root effort (`7125b337`): actual mixed-bucket parent reproduction; stable full-Move repair passed28actual-iteration oracles, Release8/8,ASan8/8,untimedparentparity and7Winechecks+52/52audit.601ratherthan1355forc3d5; no actualtimed-stop/Elo evidence. [Original data](../validation/root-effort-20261019/STATUS.md).

Hosted647final:147normalrecords(W/D/L62/43/42),73completepairs+oneorphan;16mincap,noH0/H1. Native144game snapshot+43.66±28.69 is promising/descriptive; wholeattemptinconclusive. FullPGNunchanged+59Gitblobs+auditedlikelihood/openings+21066legalreplayedplies saved. Native648offlinebundle is verified43/43, gamespending. [Result audit](../validation/hosted-strength-20261019/independent-result-audit.md).

6.4.9 external-book control (`4edda780`): actual parent RED and five-transition candidate GREEN; Release9/9,ASan/UBSan9/9,exact parent parity. Eight Wine checks and independent artifact audit pass. No NPS/Elo claim. [Evidence](../validation/ownbook-control-20261019/STATUS.md).

Fresh 647-versus-644 confirmation was preregistered and pushed once at `f1b44cc`: [0,+10] SPRT, 160 natural pairs, disjoint openings, retained actual binaries/UCI exchanges/final rehash. Completed320normalgames/160pairs:W114D101L105, pentanomial[1,30,96,25,8], independentLLR0.4574291989231206, no boundary: capped inconclusive. All2794offlinechecks passed, including42454legalplies and full raw exchanges. Descriptive+9.77Elo has approximate paired95%interval[−10.47,+30.09]; no accepted gain. The prior147-game attempt is never pooled. [Final audit](../validation/hosted-confirmation-20261019/final-audit/REPORT.md).

6.4.10 NNUE fusion (`36f5b2f`): Release9/9, exact4.1MB update/21.2MB NNUE streams, six cold/warm parent search cases passed. ASan9/9+ASanstream,8Winechecks+bothWindowsstreams and independent audit pass; SSEstream matches too. Independent-host primaryAAfailed; noAB/kernel. NoNPS/Elogain.

Hosted NNUE performance39334266771: allsource/build checks passed, but twelve same-binary primaryAAprocesses failed the strict3%gate (maximum wallratio1.04843). No A/B or kernel comparison ran. Final frozenhashes pass; originalsource/executables/results preserved on the immutable results branch. No retry or speed claim.

6.4.11 capturefusion (`c5cbf97a`): Release9/9,ASan9/9+instrumentedexactupdate, bothactualcoreNNUEstreamsparent/crossplatformexact, sixcold/warmparity,8Winechecks+independentartifact/codegenaudit pass. Signatures419798/351063. FirstincompleteASanexportconfigurefailedandretained; completeattempt2passed. NoNPS/Elogain. [Evidence](../validation/nnue-capture-fusion-20261019/HYPOTHESIS.md).

Historical integration2fc649e contained three tools/evidence commits, engine source9108, preserved by merge3cabc1b. Current accepted356e863 adds timed-only clock repair294cf1b; source is no longer unchanged9108. OlderTTtagtimeout andtruncateddiagnosticrawlogremainunresolved, noEloacceptance; exactblockedarchivepublicationholdretained. ItsweakerhistoricalmatchhelperisnotusedbynewstrictSPRT.

Actual NNUE output reuse counter: 1,417 exact-input repeats in 275,743 calls (0.5139%); all21processes/searchparity/counterrepeat pass. No outputcacheimplemented; rejectedasnextpriority, notameasuredspeedresult. [Evidence](../validation/nnue-output-cache-20261019/REPORT.md).

Combined6.4.11-versus6.4.9 run39348571407 completed validly:2048normalgames/1024pairs,W427D1194L427,pentanomial[25,190,591,196,22],nativeLLR−0.76/independent−0.7565242360831034. Natural cap, no boundary: inconclusive; no accepted gain or equivalence. Final independent audit passed99payloads/41inputs, source/build provenance, fresh openings,284195legalplies and complete1.1GBrawlog. Results `eb1c1b7ff3b5769609cf3dd5290e29cde0912763`, ref `results/nnue-strength-39348571407-1`. [Final audit](../validation/nnue-strength-20261019/final-audit/AUDIT.md).

Original confirmation push failed on its152.78MB log against GitHub100MB (original log584/587). Recovery1 `39349372297` retrieved/uploaded original bytes but failed nested inventory ordering (Path versus relative POSIX strings), not a payload mismatch. Corrected suite17/17 passed; frozen archive helper unchanged. Recovery2 `39350375158` succeeded:99recoverypayloads/85originalZIPfiles verified, results `61aabe2cd23e8171c625f1cc1d7e798d0faacc28`, ref `results/confirmation-recovery-39332822379-39350375158-1`. Failed attempts retained; no match rerun.

Rejected6.4.12 all-stripes prototype `a5d2fcb5b3270c50b96bcc1b2ebd3bc42db5f2fc`:Release9/9 and exact parity passed, but default TSan hit64-held-lock capacity on acquisition65. Source/failure retained; no disabled detector or transferred acceptance.

Revised6.4.12 gated source `8865666cc0ab4961cd507bae40ff6ce44e9319df`:Release9/9,ASan/UBSan9/9,TSan9/9;7actualAPIgroups/profile,8activeUCITSanedges,8Winechecks+independentartifactaudit pass. Six parent cold/warm cases exact;419798Linux/351063Windows signatures unchanged. Mutex operations706157→8204 are not NPS/Elo. Shared/default/SMP stay synchronized; foreign calls block; lifecycle requires all accessors quiescent. Full1427-file evidence archive is verified in two parts. [Evidence](../validation/single-thread-tt-20261020/STATUS.md).

Fresh6.4.12-versus6.4.11 package reviewed/ready, **not launched at this checkpoint**:0/+5SPRT,1024freshpairs,equal2+0.02,serialThreads1/Hash32/OwnBookfalse. All30proofhashes/23packageentries and root-ready check pass; root will record actual launch ID. A separate regression/follow-up must reconcile accepted timed-only clock contract294cf1b with frozen886 untimed/ponder reporting; timed admission is already accounted for. Keep frozenstrengthsource unchanged. No NPS/Elo or Windows/Ryzen/Stockfish inference.

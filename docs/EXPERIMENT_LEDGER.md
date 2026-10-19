# Experiment ledger

The authoritative [machine ledger](../validation/EXPERIMENTS.json) preserves 78 experiments, exact inputs, hashes, settings, failures and evidence links. This is the concise reading index as of 2026-10-19.

| Experiment | Observed result | Acceptance scope |
| --- | --- | --- |
| Accepted `9108d012` baseline | TT index/signature independence repair | Development/correctness reference; no accepted Elo gain |
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

Fresh 647-versus-644 confirmation was preregistered and pushed once at `f1b44cc`: [0,+10] SPRT, 160 natural pairs, disjoint openings, retained actual binaries/UCI exchanges/final rehash. Outcome pending; prior attempt is never pooled.

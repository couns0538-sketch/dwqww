# Native correction-history validation, Forge6.4.18

STABLE. Execution and independent evidence audit complete (841 checks passed, zero failures). Frozen source `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b` only. This is an unaccepted strength ablation, not a known correctness-bug repair.

The original Release, ASan/UBSan and default-TSan attempts each passed all ten CTests, including the actual-method permanent correction-history test (54 checks, zero failures per profile). Eight additional active-UCI transitions passed under the same TSan engine, each waiting for positive-node structured output before mutation. No sanitizer suppressions or checks were disabled. All executed gates were single attempts, without retries or waivers.

The same Release test object linked against frozen17 core produced the expected new-behavior-contract RED (17 failures/54 checks, exit1). No parent rebuild or candidate test rerun occurred. Headers are identical. The one raw Release bench11 signature was 321912 nodes. Source, test, object, parent core, engine, candidate core and executable identities are retained before/after.

A 1200-second hard timeout applies separately to each configure/build/CTest command; CTest has a300-second per-test timeout. Parent RED and bench have30-second limits; active-UCI has90-second session/120-second outer limits. Every command records return/timeout/cleanup/raw-stream identities before gate assertions. No owned live processes remained. Full source/build originals are retained outside the checkout, with complete final file hashes in `ORIGINALS-FINAL-SHA256.json` (73source files and137files per build).

Actual commands and raw output are in `frozen-*-attempt1`, `release-extras-attempt1`, and `active-uci-*-attempt1`. Source export/TAR and full profile configuration are retained. The driver rejects existing output/build directories to preserve original attempts.

No further engines or builds are planned. No Git, production source, root documents or ledger changes were made by this task. These finite checks establish no speed, NPS, Elo, physical Ryzen or native Windows result.

The independent audit checks the exact ten test registrations and explicitly scans original sanitizer logs, covering two narrower assertions in the reused runtime driver. The1200-second limit remains a per-command limit. All original Release/ASan/TSan/extras/active files were preserved unchanged during final metadata freeze. `FINAL-RECEIPT.json` records the final result; `EVIDENCE-SHA256SUMS` covers every other file in this tree.

# Independent prelaunch review: promotion SEE, 2026-10-20

**Disposition: no new material runner/acceptance defect found in this targeted read-only review; launch remains blocked by the existing pending gates.** This is qualified protocol review, not launch authorization, a new test execution, or playing-strength acceptance.

Reviewed `.github/hosted-promotion-see-strength/{protocol.json,README.md,run_hosted.py,match/run_match.py,match/pgn_stats.py,provenance/root-readiness-decision.json}`, its workflow, the final-likelihood functions in `tools/match/windows_validate.py`, retained preparation results, and current candidate17 `ROOT-NATIVE-PROOFS.json`. No engines, builds, mocks, Git commands, archives or production/config edits were performed. Only this report was written; the previous candidate16 startup review remains unchanged.

## Required closure before the single push

At inspection, `protocol.json` is `PENDING_REVIEW`, `source_gates_status` is `PENDING`, and `correctness_evidence_sha256` is empty. `require_launch_protocol` rejects this state before compiler/engine execution. Root must finish the current17 independent Windows artifact review, bind the actual current17 evidence and final review hashes, resolve metadata, refresh the package inventory and perform the existing ready check before any trigger. The native proof records first-attempt 9/9 Release, 9/9 ASan/UBSan, 9/9 TSan and eight active UCI TSan passes for source `47f0560221d986e41a309853e1295c557fcf5bf6`; I did not rerun or independently re-audit all underlying native suites. The Windows packaging record read as `packaged_and_verified`; the independent wording-checker repair remains root's separate closure item.

One factual metadata correction is needed during that closure: `provenance/root-readiness-decision.json` still says “no17benchmark signature known yet,” while the protocol and verified runner freeze 385781. Update that record and its pinned hash/inventory before the final freeze, retaining its earlier provenance as appropriate. This does not require changing the experiment or any outcome-dependent setting.

The workflow rejects rerun attempts through `github.run_attempt == 1`, but a second push can create another attempt-1 workflow. “Exactly one push/run” therefore also requires root's publishing discipline; the workflow predicate is not a repository-wide once-ever lock. Do not push subsequent changes onto the trigger branch or launch another matching branch after an outcome.

## Checks that support the qualified disposition

- **Exact scope:** candidate17 versus baseline14 `21538ec5416c909fc98a08688242a0b3b9710b25` measures the combined pin-aware SEE, equivalent mask refinement and promotion-recapture repair. It does not isolate promotion-recapture Elo or compare against Stockfish.
- **Candidate readiness:** `run_hosted.py:231–266` requires one anchored depth-11 record with exactly 385781 nodes, normal exit, empty stderr and no warning/error/fatal record. The process is started in its own session; communication uses the remaining ten-second response budget, and failures clean up the owned group. A surviving owned descendant prevents success. The guard is a readiness/fault bound; recorded engine time/NPS is not compared against baseline and supplies no speed estimate.
- **Prerequisites:** unchanged baseline gross A/A runs before candidate readiness, followed by four deterministic, complete baseline/baseline color-swapped 10,000-node pairs before A/B. These are operational gates, not proof of general clock reliability. Current17 correctness is independently required; original16's failed TSan batch remains failed and its isolated passing diagnostic does not waive anything.
- **Frozen match:** serial pinned Fastchess `60d7a7a26c6b0582a15c112fb29a1829bef2adb3`; H0=0/H1=+10 logistic SPRT; alpha=beta=.05; equal `10+0.1`; Threads1/Hash32/OwnBookfalse/MoveOverhead10/restarton; fresh reserved openings; 128 pairs/256 games maximum. A native boundary may stop earlier. The 12,000-second emergency limit invalidates acceptance instead of turning unfinished play into a valid cap result.
- **Acceptance:** the outer audit requires complete normal unique color-swapped pairs, exact frozen opening prefix/order, native/independent pentanomial agreement, exactly one native acceptance for a decided result, finite final LLR, and independent crossing of the matching bound. The inner helper's weaker preliminary decision parse cannot bypass this outer audit. A stop before 128 pairs without an audited boundary fails; a natural cap with neither boundary remains inconclusive. Final input changes invalidate even a previously successful result.
- **Preservation:** workflow/source/build metadata and actual runtime engine/core/Fastchess bytes are retained before timing. Fault scanning and owned-group cleanup preserve failures. The workflow attempts raw upload and separate archive/results-branch publication even on failure; abrupt platform loss remains an acknowledged preservation limitation. The reviewed 63 runner and eight archive test results are retained evidence from root's execution, not tests performed by this reviewer.

## Interpretation and power limits

The 128-pair ceiling is a bounded pilot and may well finish inconclusive, especially for a modest effect. The observed draw rate and paired-outcome variance are not yet known, so this review assigns no numerical power. Configuring alpha=beta=.05 does not promise 95% probability of a decision by this finite cap. A positive interim estimate or completing all games is not accepted gain.

An audited H1 supports gain for this exact combined candidate, baseline, hosted Linux resources, openings and clock. It does not establish a gain of at least +10 Elo, an absolute Forge rating, native Ryzen/Windows strength, or superiority over Stockfish configured at 3200. H0 favors the null over this alternative within the design; it does not prove equality. Capped inconclusive remains inconclusive. Any fault invalidates the attempt. Do not change caps, hypotheses, openings or tolerances after observing results, and do not retry, pool, trim, or selectively discard faults.

Prior baseline14 bench timeout, prior hosted TT time forfeit and original16 startup timeout remain unresolved. The recorded authorization permits one fresh-host readiness attempt despite those anomalies; passing its checks would not identify their causes or prove that the longer clock remedied them.

## Reviewed code identity

| File | SHA256 |
|---|---|
| `run_hosted.py` | `6fe3164904cbb5a823cc13fd9fce0e8bd2c7ed3f27f7994eecb39ec58cf6b75e` |
| `match/run_match.py` | `6cddd135550320a460bc4695e33311077511e53941fdb802ca5fdc908e0033df` |
| `match/pgn_stats.py` | `a5a6b46e1d5381fc063475fb90f012051653cefbca485c46a01179fafbeec2bf` |
| workflow | `ea0c387048283e608233b90ca8405f8f681aaa1fc48eb4e9c7baa36f6b85d257` |
| `tools/match/windows_validate.py` | `0fa959b97cedd340db57957cbae5cd9701d4468bdc4689f0131edc4984072719` |
| protocol at review, still pending | `682c878ca96bccb35d5c7077f29346550f2ea03c97fe2f0ee8dd5fa098f0da5f` |

Metadata-only final gate closure will necessarily change the protocol/readiness-record inventory hashes. This report does not preapprove a change to the reviewed executable runner logic, source pins, openings or stopping rule.

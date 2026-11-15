# Final corpus acceptance and report preparation

Preparation only: no engine/Git execution or root-state write. The actual full corpus is not marked complete here.

After the final v5 batch has been audited **and published with the regular v5 recorder**, regenerate source attribution using a fresh output label:

```text
timeout -k 2 120 node /workspace/work/parity-sameclock-attribution-preparation/review-corpus-v5.mjs ACTUAL_FINAL_AUDIT FINAL_FRESH_LABEL
sha256sum /workspace/work/parity-sameclock-attribution-preparation/FINAL_FRESH_LABEL/ATTRIBUTION.txt
node /workspace/work/parity-final-acceptance-preparation/record.mjs ACTUAL_FINAL_RECEIPT ACTUAL_ATTRIBUTION_FILE ACTUAL_ATTRIBUTION_SHA256 --check
node /workspace/work/parity-final-acceptance-preparation/record.mjs ACTUAL_FINAL_RECEIPT ACTUAL_ATTRIBUTION_FILE ACTUAL_ATTRIBUTION_SHA256 --record-authorized
```

Use real finalized paths/hashes. `--check` is the default. It preserves root state but writes one fresh read-only attribution snapshot under the attribution preparation directory. The recorder never starts an engine; its only subprocesses are the frozen raw-evidence verifier in check mode and the pinned attribution helper, whose Git commands are read-only.

Required checks:latest final-v5 receipt and root publication row match; exact100000selection including99958low/42high and all4original digests/cursors; zero validation/partial differences; exactly one difference at36729,FEN/clock90 as already observed; all11complete pairs have a1b2,mate−5/2566746 versus a1b2,mate−6/2565143. Source attribution is recomputed from raw artifacts and compared to the supplied proof, not accepted from prose. Current operational policy must allow continuation with all cutoff findings retained; a second candidate timeout or other unresolved fault remains blocking. Root global stop must be false. Default pins,16optioncounts and9unitrows must still pass.

The helper deliberately refuses any new low-clock difference, extra high-clock difference, different tuple, missing repeat or incomplete corpus. It does not generalize the explanation to unreviewed findings.

The explicit decision writes only new fields:

- `step2Acceptance`, with audit/receipt/attribution hashes and a precise limited explanation.
- `step2EffectiveGatePassed=true`.
- `validation.step2.acceptance`.

It does **not** rewrite `step2gatePassed`, `step2AttributionPending`, raw equality rows/totals, strict audit decisions or original faults. These historical strict fields may remain false/pending; consumers must use the separate effective gate after reading its attribution. It does not mark Job A or sanitizer work complete and does not authorize Job B by itself. Root must close Job A honestly and include this acceptance evidence in the later match declaration.

Publication evidence goes to `parity-run/inputs/step2-effective-acceptance-S2-NNNN.txt` plus a per-attempt verification log. Existing accepted state is a verified no-op. If interrupted after evidence publication but before state replacement, a retry verifies and reuses the immutable acceptance evidence, records its fresh verification separately, and completes the atomic state update. A changed root state during verification blocks the update rather than overwriting it.

The source attribution says only that the sole Boolean source delta requires equal capped clocks with the prior mate-distance rejection, under identical compiler/flags and the recorded deterministic protocol. It does not claim a measured runtime TT-entry clock or a chess-theoretic proof of the printed mate distance.

Eleven pure synthetic gate tests passed. They simulate completion only in memory and explicitly reject incomplete/wrong counts, new low/extra/partial differences, missing repeats, wrong tuple/FEN, wrong baseline and fabricated runtime-entry claims. Recorder syntax passed. An independent peer found no blocking normal-path defect; its two suggestions (source-commit cross-check and publication-before-state retry recovery) were incorporated before freeze. No real full-corpus acceptance invocation has run yet.

Report suggestion: `report-parity.patch.txt` and `report-parity.candidate.mjs.txt`. They were generated from the root report source hash recorded in `REPORT-PATCH-PROVENANCE.txt`; the shared file is untouched. The candidate passed syntax and rendered the current state to `current-state-report-preview.md`.

The suggested report distinguishes the original failed contract batch's observations from strict-v2 accepted sanitizer coverage, adds ordinary/soft game counts, aggregate X/cap counts and per-group rows, and displays the separate effective corpus gate without rewriting the strict audit. Apply only after checking the base hash, or reconcile against any later root report edits. No preparation test is counted as an engine search.

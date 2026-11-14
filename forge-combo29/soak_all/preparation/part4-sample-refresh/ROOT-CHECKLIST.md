# Refreshed 4sample launch checklist — root only

Scratch proposal; nothing installed or executed natively. Current baseline:
`c471c0287c542defcbaac4ba05a0173fc1f9550ad8224f88a55d35d5bf6c82dc`.
Refreshed `/workspace/work/part4-sample-refresh/control-proposed.mjs`:
`5ff103498365ee5b15d362f9486d4a238cb5ea2e7519443155588920fabf4934`.

1. Finish the planned origintrace/match work and use an idle controller boundary. Recheck the current controller SHA against the baseline above; if it changed, reapply only `control-proposal.diff.txt` after review rather than replacing newer controller changes. The reviewed proposal changes only `collectSpecCounts`; all bytes outside that function, including the current transport implementation, are identical. Its accounting function is byte-identical to the earlier reviewed proposal.
2. Adopt the reviewed controller proposal at that boundary and run `node --check` on the installed helper. This task did **not** install it. Keep origintrace evidence and the original Part4 observation/counter summary separate from new phase **4sample**.
3. Generate a fresh spec using the existing pinned generator. First batch uses id1, offset0; later batches use a fresh id and the independently audited prior `next_offset`:

```
node /workspace/work/part4-sample-integration/make-spec.mjs \
  --id 1 --offset 0 --spec /workspace/work/all-run/specs/4sample-0001.json
```

4. **Immediately before launch**, independently recompute all nine `spec.expectedHashes` and refuse launch on a mismatch. The generator/auditor are still pinned to `81f1774fd5195b9af630593e53a6ec010be848207188984ff474231e04f5792e` / `bebd5bf65f146bad463b552ac14be23bd23bbc06b18d3bc1354d71f92dbb9d78`. This refresh checked all nine declared native/source hashes, but those preparation checks do not replace an immediate prelaunch check. The controller does not enforce expectedHashes itself.
5. Confirm sufficient time remains for the fixed bounded batch and evidence audit, then root may invoke the existing controller:

```
node /workspace/work/all-run/control.mjs run-spec /workspace/work/all-run/specs/4sample-0001.json
```

The spec fixes taskset CPU4; roots10000; seed1296127045; limit10000; seconds300; timeout-ms5000. Native Threads1/Hash16/OwnBookfalse/depth13, lock+merged × NNUE false+true, all new options default. The external controller timeout remains450s plus5s kill grace. Each root is one atomic unit: four baselines plus ten additional fresh observations for each faulty baseline. Each batch gets a fresh output directory/log. A target of10000 is not a claim that all10000 finished.
6. Once the batch is finished and its manifest exists, audit preserved evidence using a fresh report path:

```
node /workspace/work/part4-sample-integration/audit-sample.mjs \
  --metadata /workspace/work/all-run/logs/4sample-0001.txt.run-spec.json \
  --manifest /workspace/work/dwqww-all/forge-combo29/soak_all/batches/4sample-0001.evidence/manifest.txt \
  --evidence-root /workspace/work/dwqww-all/forge-combo29/soak_all \
  --report /workspace/work/all-run/4sample-0001-audit.json
```

Do not use `--preparation` for official sample coverage. Exit0=valid evidence/no retained findings;1=invalid evidence/accounting;2=valid accounting with findings. Always inspect `safety_findings`/`fault_candidates`; `accounting_valid` is not a correctness claim. The auditor never edits state or creates numbered fault files.
7. Adopt only completed-unit counts. Resume at the audited next_offset; rerun any partial root in full under a fresh batch id. `auditSequence(reports)` checks contiguous same-corpus cursors and marks earlier partial roots resolved only with later completed-unit evidence. Do not infer ten-repeat frequency for raw-only/interrupted diagnostics: their pending reproductions stay explicit. Root owns any concrete fault materialization and final state/checkpoints. Preserve sampled KRK scope and the upperbound-criterion caveat; do not merge these counts into the earlier Part4 summary or claim universal correctness.

Evidence in this folder: `refresh-command.txt`, `fixture-command.txt` (25pass; native_runs0/state_writes0), `verification-command.txt`, `diff-command.txt`, `hash-verification.json.txt`, frozen baseline/proposal and exact diff. The old helper package and fixture evidence remain untouched. Independent peer hash check: `/workspace/work/part4-sample-contract-peer/refresh-hash-check-output.json`.

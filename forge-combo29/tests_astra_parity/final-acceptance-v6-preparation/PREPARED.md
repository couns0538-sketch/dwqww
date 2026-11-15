# Final v6 corpus acceptance preparation

Preparation only. No engines, Git commands, root-state mutations or changes to old evidence occurred. The raw v6 recorder is now pinned at SHA256 `8dde48bab7b0c1e825be7daa8f7df0fec0948d828bfe4f5d92c9c3b5cea9925b`; `FINAL-PINS.txt` records the frozen helper and acceptance hashes. The previous pending source and metadata remain as preparation history.

The new attribution helper is `/workspace/work/parity-sameclock-attribution-v6-preparation/review-corpus-v6.mjs`. Its SHA256 is `0d8b10a1d30d07be3e4ceafd4d8d5ad8734cae290f13db0360261cef2bb9753e`. Compared with the frozen v5 helper, only its output directory and final-stage metadata paths changed. Its source comparison, compiler/build comparison, Step 1 lookup and original-plus-ten-pairs extraction are unchanged.

The pure `acceptance.mjs` and eleven synthetic tests are byte-identical to the prior preparation. The recorder retains the existing source-commit cross-check and interrupted-publication recovery. It requires the latest finalized v6 receipt to match root state, all 100,000 original selected positions (99,958 lower clocks and 42 higher), the single expected high-clock difference at global index 36729, eleven exact recorded result pairs, the live operational policy, the default pins, sixteen option counts and nine unit rows. It reruns the raw recorder in read-only mode and independently regenerates the attribution proof before acceptance.

The resumed instruction is pinned from `/workspace/work/parity-run/inputs/FABLE_ANSWER_0016.md.txt`, SHA256 `1ca13976a15e8e8b7dbd994aeca5176d8158a18ff71db87422095adf83d6c1b2`. Its Job A deadline is recorded as 2026-11-15 04:20 UTC. This acceptance tool runs no search and does not start the next job. The source-level attribution does not claim an observed runtime TT entry or a chess-theoretic mate proof.

Once the verifier is pinned and the corpus is complete, root uses the actual final audit/receipt and a fresh output label:

```text
node /workspace/work/parity-sameclock-attribution-v6-preparation/review-corpus-v6.mjs AUDIT_FILE FRESH_LABEL
sha256sum /workspace/work/parity-sameclock-attribution-v6-preparation/FRESH_LABEL/ATTRIBUTION.txt
node /workspace/work/parity-final-acceptance-v6-preparation/record.mjs RECEIPT_FILE /workspace/work/parity-sameclock-attribution-v6-preparation/FRESH_LABEL/ATTRIBUTION.txt PROOF_SHA256 --check
node /workspace/work/parity-final-acceptance-v6-preparation/record.mjs RECEIPT_FILE /workspace/work/parity-sameclock-attribution-v6-preparation/FRESH_LABEL/ATTRIBUTION.txt PROOF_SHA256 --record-authorized
```

`--check` is the default and does not write root state; it does create a fresh attribution verification directory. The authorized record adds `step2Acceptance`, `step2EffectiveGatePassed`, and `validation.step2.acceptance`, plus immutable text evidence under `parity-run/inputs`. Raw strict gates, attribution-pending fields, equality rows, source and push metadata stay unchanged. A state hash check rejects concurrent mutation.

Preparation checks actually completed: both generated tools passed syntax checks; all eleven synthetic pure acceptance cases passed; source-path validation confirmed the pure function/tests were unchanged and the attribution helper differed only by the intended v6/output paths. The initial generator created the source files but failed while writing preparation metadata because its generator variable was undefined; that failure is retained in `PREPARATION-FAILURE.txt`, and the metadata was subsequently written without recreating or changing those source files. No complete corpus or acceptance result is claimed here.

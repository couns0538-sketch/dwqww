# Full-data controller v2 bounded independent review

**PASS: no blocking finding or config-key mismatch.** This is read-only source/config-schema review, not execution or proof of completed full-data training.

Reviewed controller SHA256 `c8286ff370ddbcab9fa521763fa30da333b25dd257a1effcc0bf77b8a6fbcd3f`. The diff changes the new attempt namespace, corrected closure-v2 receipt and additional manifest/summary/config/input-hash gates. It preserves the original zero20 then separate warm20 schedule and every training hyperparameter. All ten source-freeze entries match the original controller protocol's captured bytes.

The trainer really emits all **11** keys in the controller's expected-config map: epochs, batch_size, threads, lr, min_lr, result_start, result_end, seed, hidden, residual and sigmoid_k. It additionally emits data_dir, run_dir and initial_net. Existing genuine completed pilot summaries confirm the schema and all common values; their threads=2 is correctly distinct from this predeclared full-run threads=4. Warm initial_net contains actual path/SHA fields; zero initialization records null. No unseen KeyError is apparent.

The completed closure-v2 receipt was inspected and its small manifest/integrity/prior-failure SHA bindings rechecked. It records 1,000,000 training rows, 4,149 validation rows, 200 declared training-partition games and **196 games with retained rows**. The corrected checker requires that observed subset to equal the established fresh-only recipe's actual IDs and diagnoses the exact four zero-retained partition IDs (:33, :48, :56, :151). Three have only >1,000-cp records; :33 emitted zero quiet records. No data, filter, partition or game identity changes are made.

The shared loader still checks original source and NPZ hashes/schema; v2 also compares every validation array dtype/shape/value byte and the validation recipe identity against the established holdout before launching. After each run it requires completed20 epochs, exact manifest/counts/config, unchanged inputs and unchanged source freezes. Candidate selection remains conditional on the same held-out set, not an independent test or Elo result.

The original failed closure/controller artifacts remain unchanged. The old controller's failure reports no training attempted and contains no START/command/training result records. The new controller has no automatic training retry.

No controller, trainer, data validator, engine, build, benchmark or match was executed by this review. No NPZ arrays or full legacy corpus were loaded. Reviewed file hashes, exact diff, existing schema evidence and observed closure metadata are in REVIEW.json. Root owns the actual launch and its closure.

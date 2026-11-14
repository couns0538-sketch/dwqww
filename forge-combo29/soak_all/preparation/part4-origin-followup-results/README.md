This text-only snapshot preserves completed later TT-origin evidence. Read [FOLLOWUP_RESULTS.md](FOLLOWUP_RESULTS.md) for the factual result and its limits. The earlier first-pass bundle is deliberately not duplicated here, and the separate r3-23 experiment is outside this snapshot.

- `pass2/` through `pass9/` preserve exact source/helpers, instrumentation records, commands, native logs, full run streams, comparisons, and extracted ledgers from the eight later trace passes.
- `oracle/` preserves source, input rows, and both completed query command/output records. Its no-history DTM comparisons are not a full-history correctness certificate.
- `static-eval-counterfactual/` preserves the private four-setting experiment, its nine run records, all comparisons/PVs, and a read-only packaging review. These guards are not production fixes.
- `analysis/readonly-inputs-after-all-native.json.txt` preserves the14-input post-run verification. `tooling/prepare-origin-variant.mjs.txt` is the shared preparation source, copied as inert text.
- `independent-review/` contains only four reports confirmed final/stable for this snapshot. Their earlier-stage limitations and references are preserved; unfinished pass9/guard review reports are excluded.
- Copy inventories preserve exact original paths, publication paths, byte sizes, SHA256 values, and excluded binary/object hashes. No executable, object, symlink, or binary archive is included. Helpers are `.mjs.txt` and dependencies `.d.txt`; embedded commands are evidence, not actions performed during packaging.

The final root `SHA256SUMS.txt` will cover every other publication file. After the draft result has been reviewed, the snapshot will be sealed with read-only files/directories and its manifest hash supplied to the publisher. Any retained preparation-stage text remains historical evidence; the actual completed-run status comes from command logs and summaries. This bundle is not itself a publication or push.

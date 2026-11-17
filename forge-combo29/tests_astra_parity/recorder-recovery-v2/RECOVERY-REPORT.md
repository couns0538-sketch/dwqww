# Equality recorder layout recovery

The root successfully migrated to new versioned metadata and recorded S1-0001 with the corrected controller. The retained result is **16,719 committed comparisons, zero differences, one partial operational finding, audit exit 3**. The speed-stage continuation gate remains blocked.

The fault is candidate shutdown timeout at worker 1, local index 4407 (global 17629), FEN `rn4rN/p1k5/8/P1p3P1/2b1p3/b2P2pR/4Q1q1/1R2KBN1 w - - 1 33`. The candidate's completed search is not marked budget-interrupted; its shutdown timeout survives the later interrupted reference attempt. This partial position contributes no committed corpus count. The unchanged aggregate retains the finding, without waiver or changed expectations. Subsequent reproduction/classification is separate root work.

The original recorder failure was a preparation error: the layout transformation asserted on a missing string before writing `control.mjs`. A following syntax-check command returned 0 and the preparer failed to inspect transformation stderr. Syntax, planner and retained-aggregate checks therefore passed without testing controller ID/path integration. The original controller still expected E-NNNN and stage-local configs/batches. The earlier readiness report incorrectly said that the S1/S2 adaptation had been installed. No unexplained file reversion occurred. Original script, stderr, controller, metadata and failed live audit are preserved and pinned.

The new controller is entirely under this v2 directory. It consistently uses S1/step1 and S2/step2 in ID generation, receipt discovery, config/output resolution, seed generation and executed-plan checks. It uses the root's pinned wrapper and unchanged native comparator. A static review rejects remaining literal E-prefix, E-receipt and old stage-local config/batch assumptions. The actual `check-batch speed S1-0001` path validates root config, stored native plan, cursor plan, binary/tool pins and aggregate; legacy E-0001 is rejected. Transformation and validation subprocess statuses are individually checked.

Migration creates `/workspace/work/parity-run/equality-speed-v2/stage.txt`, without overwriting the original initialized stage. It pins corrected tools, original stage/tools, original transformation failure output, all retained live naming-failure reproduction files, native summary/manifest/config, candidate/reference/driver and build flags. Audit/fault/receipt artifacts are stored under the new metadata directory; raw S1 batch artifacts remain unchanged. The corrected same-clock stage uses a separate `equality-final-v2` directory and still requires complete clean speed-stage equality. No gate was relaxed.

Root executed:

```text
node /workspace/work/parity-equality-preparation-v2/control.mjs migrate speed /workspace/work/parity-run/equality-speed/stage.txt
node /workspace/work/parity-equality-preparation-v2/control.mjs audit speed S1-0001
```

The resulting stage SHA256 is `ca6e536aa06dd1df90e4f4d54c9682b8dc42e731c315fa7de08b202828cd1bee`. `ROOT-RECOVERY-VERIFIED.txt` records an independent read-only check of the root's real stage/receipt/audit hashes, corrected and original tool pins, and the blocked finding. Copies of those three small records are retained here. No further migration or engine execution is needed for this repair.

The coincidental 16,719-position total in both old E-0001 and new S1-0001 was investigated. All four native JSONL hashes, config hash and summary hash differ. Seeds are 1449420001 versus 1449530001; native intervals are 21:29:12.337–21:34:41.596 UTC versus 23:33:23.398–23:38:52.759 UTC. New config and rows identify the new binaries/seed. All 32 new native artifact hash/byte-size entries verified. Preparation wrote no runtime S1 output: its first plan invocation was explicitly `--dry-run`; its historical aggregate read E-0001 and wrote only under preparation. These observations support distinct native records; the equal total by itself establishes neither reuse nor any performance result.

Evidence: `ANOMALY-CHECK.txt`, `S1-0001-independent-audit.*`, `VALIDATION.txt`, exact preview/check/rejection commands and stdout/stderr, `control-v1-to-v2.diff.txt`, original observed evidence snapshots, and identical inert `.mjs.txt` twins. The adapted aggregate matched the independent unmodified audit for the actual batch. Preparation/recovery validation performed zero engine runs and no state/Git/source writes; root alone executed migration and recording. Runtime bounds and all difference/partial-operational gates remain unchanged.

# Pyright findings — assessed, not a clean scan

Pyright 1.1.414 analyzed all 23 then-existing core Python files, reporting 30
errors in 5.434 seconds. The reused reviewer inspected the exact pinned source,
surrounding code and installed API behavior. Main read and accepted these
dispositions. No reachable runtime defect was established from these diagnostics.

| Count | Group | Assessment |
|---:|---|---|
| 6 | Optional PGN node moves | The installed type describes both root and child nodes; mainline iteration skips the root, and parsed children have moves. Empty games yield no child nodes. |
| 2 | Converter current_metadata | Every result-aware caller assigns metadata before keep(); the legacy path does not index it. These diagnostics do not concern the eval regex. |
| 11 | Heterogeneous dictionaries | Converter statistics, audit result lists and profile/report dictionaries contain intentionally different value types. The accessed list/dictionary keys are initialized consistently and not replaced with scalars. |
| 4 | npt metadata treated as Tensor | The adapter supplies eight tensors plus a metadata dictionary, then passes only eight tensors to the installed superclass. Actual device transfer retains non-tensor metadata. |
| 2 | Optional lifecycle fields | pending/runtime begin as None, then receive a tensor/dictionary. Guards, runtime checks and finally cleanup govern use. |
| 4 | Optional module paths | getattr(module, '__file__', None) is checked before Path construction; builtin/namespace modules without filenames are skipped. |
| 1 | CheckedPGNInput versus TextIO | The installed parser calls readline(), which the wrapper implements. The nominal annotation is broader than the consumed interface. |

Existing real adapter feature/model/loss/cleanup tests and generated PGN cases
support these assessments. No behavior or annotation was changed solely to
suppress diagnostics. The earlier zero-file configuration attempt is preserved
and is not successful static-analysis evidence. Future code changes require a
new scoped assessment; this report does not cover the later admission auditor.

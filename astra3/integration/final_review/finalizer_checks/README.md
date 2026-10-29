# Final TSan identity sealer: synthetic failure checks

IDEA_SOURCE: independent review of the same-repository sealer; explicit acceptance gates, exact build provenance and original failure-byte preservation.

The original helper is copied verbatim before editing. Five synthetic Python tests substitute every subprocess.run call. The executable is a non-executable text file; mocked objdump and kiwipete results are fixtures, not native evidence. Synthetic PASS receipts and FMA/perft values inside fixture directories must never be presented as chess, sanitizer or benchmark results.

RED with python -O: five methods ran; invalid pins, wrong build digest and wrong source falsely passed (three failures), and failed objdump raw bytes were absent (one missing-file error). The valid control passed. Original test logs and all fixtures are retained.

Fix: every production assert is now an explicit require that remains active under Python optimization. The supplied engine digest and fixed M5 source are verified against a BUILT TSan build receipt, whose hash is recorded. objdump exit/stderr are always preserved and original stdout is retained on failure before the failure is raised. Existing timeout/kiwipete/perft/pin/raw evidence behavior is unchanged.

GREEN: all five methods pass under both python -O and ordinary Python. An AST check confirms no assert remains in the production helper. commands_and_results.json records exact commands, interpreter test exits and helper/test hashes. These interpreter exits are not engine exit evidence.

The unchanged native workload remains root-owned. No engine source, REPORT, Git operation or native process was touched by this task. Reruns require a new --evidence-dir; no existing fixtures are overwritten or removed.

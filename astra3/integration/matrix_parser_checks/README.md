# Matrix-parser review repair

IDEA_SOURCE: the same-repository qualifier and the independent review finding that malformed extra bench lines and explicit errors could be ignored.

The original runner snapshot is preserved verbatim (SHA-256 in commands_and_results.json). RED tests execute its actual three parser assignments, selected from its AST, with unchanged-binary placeholders; they do not emulate an engine or run subprocesses. The baseline failed seven subcases across malformed duplicates, explicit error lines and missing/duplicate handshakes. Existing valid, duplicate-valid rejection, numeric format, option rejection, fixed-reference and exit-code checks passed.

The reusable parse_bench_result now requires exactly one bench-prefixed record with complete numeric grammar; expected depth/nodes; exactly one uciok and readyok; zero exit status; and no ERROR/invalid/refused/unknown diagnostic on either original stream. Main execution retains fresh-process settings, supplied pins and raw transcript capture. A main guard makes the parser importable without executing the matrix. The existing binary hash checks remain in the caller.

GREEN: eight synthetic test methods pass. Tests include LF/CRLF valid records, malformed and valid duplicates, explicit errors on stdout/stderr, missing/duplicate handshakes, incorrect pins/depth, nonzero exit, and unknown/invalid/refused options. Exact commands, exit codes and original stdout/stderr are adjacent.

No engine run, compile, benchmark, performance conclusion or Elo claim is part of this repair. Final native matrix qualification remains root-owned. No engine source, CMake or Git operation was changed by this task.

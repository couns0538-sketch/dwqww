# Identity timeout evidence checks

IDEA_SOURCE: the existing identity runner and the requirement that interrupted benchmarks retain original partial streams without fabricated child exit status.

These are synthetic Python tests only. Every subprocess.run call inside the helper is replaced by a mock raising TimeoutExpired. The supplied executable path is a non-executable text fixture. No chess engine or native build runs, and these results are not benchmark, sanitizer or playing-strength evidence.

The parent materialized the exact pre-change identity_bench.py from commit 3928739 into /tmp/astra3_identity_bench_3928739.py. Its bytes are copied unchanged here, with SHA-256 f3c4f6391f4a83cf63423d25d5560bd2ef825c2039063e3d93a886700061e8e7. The current helper was read, not modified, and its before/after-test hash was identical: 4f006ec2f9684d3b669f97dd47d3de917162cd382a8803553b41d141da793d3c.

RED: five methods ran, with six failing subcases and two missing-file errors. The old helper ignored timeout overrides and invalid values and did not preserve timeout streams. The unchanged default of 300 seconds passed.

GREEN: all five methods passed. Coverage: default 300; positive override 17 consumed by the mocked call and exception; invalid text, zero, negative, fractional and empty override rejected before subprocess invocation; original non-UTF8/NUL/CRLF stdout and stderr preserved byte for byte; exact stdin preserved; absent partial streams become empty files; timeout.json records INCOMPLETE_TIMEOUT with actual_returncode null; no completed results.json is fabricated.

commands_and_results.json records exact test commands and test-process exit statuses (RED 1, GREEN 0). These statuses belong to the Python test runner, not an engine. Raw test stdout/stderr, synthetic fixture trees, source snapshots and the reviewed helper delta remain preserved. No defect was found in the bounded timeout change. Perft timeout handling and the broader identity-record parser are outside this check.

To rerun, use a NEW --evidence-dir; existing fixture directories are never overwritten or removed.

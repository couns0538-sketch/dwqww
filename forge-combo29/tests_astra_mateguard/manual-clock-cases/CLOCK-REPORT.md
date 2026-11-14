# Manual clock command result

All **14 listed cases completed**, seven per frozen Release/ASAN engine. All four huge-clock cases produced no bestmove before the explicit stop sent after the 150 ms checkpoint, then returned normally. Both engines and helpers exited 0; engine/helper stderr is empty, no sanitizer diagnostic was observed, and both shutdowns were reaped normally without timeout or driver signals.

The exact original go and position sequence was verified from submitted raw stdin. Each mode used one fresh engine with Threads 1, Hash 16, OwnBook false and Move Overhead 10. The helper waited for each bestmove before the next go, preserving the original sequence and shared state between listed cases.

| Case | Go command | Release bestmove ms | ASAN bestmove ms | Release stop ms | ASAN stop ms |
|---:|---|---:|---:|---:|---:|
| 1 | `go wtime 3000000000 btime 3000000000` | 151.194 | 158.497 | 151.035 | 150.922 |
| 2 | `go movetime +80` | 70.519 | 72.410 | — | — |
| 3 | `go movetime -5` | 1.265 | 1.614 | — | — |
| 4 | `go movetime abc` | 1.297 | 1.144 | — | — |
| 5 | `go movetime +-80` | 1.117 | 2.889 | — | — |
| 6 | `go movetime 999999999999999999999abc` | 1.160 | 1.284 | — | — |
| 7 | `go wtime 1 btime 3000000000` | 150.937 | 156.295 | 150.691 | 150.591 |

Times above are monotonic observations from successful command write to first received bestmove, rounded to 0.001 ms; exact chunk timestamps remain in events.jsonl.txt and the verification table. Stop columns use the actual submitted stop timestamp. Read/pipe/scheduler latency is included. The file's approximate 70 ms and 1 ms comments supply no strict wall-time tolerance on this shared VM, so no such tolerance was invented. For example, ASAN's malformed double-sign case measured 2.889 ms and remains a recorded measurement. The huge-clock observation supports the listed non-immediate-search behavior; it does not identify an exact internal engine stopping timestamp.

Root executed both modes at 2026-11-14T22:52:03.348Z through 2026-11-14T22:52:04.613Z. Complete raw engine stdin/stdout/stderr, helper stdout/stderr, monotonic events, transport transcripts and exact argv/env/exit/hash records are retained in enabled/ and asan/. The private transport extension only adds raw-byte observation and a nonthrowing timed read; no engine or existing test changed. The preparation's missing original-report limitation remains: the annotated command file and current parser test were the authoritative context.

This closes the concrete manual-command inventory omission. It is separate from the original 118 suite entries, does not replace any failed/incomplete test, and supplies no strength, timing-comparison or throughput claim. Independent review reassembled event payloads byte-for-byte, checked all source/binary/stream pins and recomputed all 14 command timings without executing further tests.

# swarm-67 — protocol-boundary fuzz (ASan + UBSan)

Status file. Written before findings, as asked.

## Build

Sanitizer build succeeds and runs.

```
cmake -S forge-combo29 -B /tmp/asan -DCMAKE_CXX_COMPILER=g++ \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
```

- Compiler: GCC 13.3.0. **Clang 18 cannot be used on this VM**: `libclang_rt.asan*`
  and `-lstdc++` are missing, so every sanitized link fails. This matches what
  `REPORT_r3_01.md` already records about `/usr/bin/c++` on this machine.
- `FORGE_PORTABLE` is OFF and `-march=x86-64-v4` is on, which the host supports
  (avx512f + bmi2 present). The sanitizer build keeps the same ISA switches as the
  lock, so a crash here is not an artifact of a portability build.
- Sanitizers are live: a deliberately planted heap overflow in a scratch copy of
  the engine is caught (see Self-test).

## Harness

`fuzz.py` + `cases.py` + `selftest.py` in this directory.

Discipline implemented:

- `os.read()` on non-blocking fds for stdout and stderr; no `select()`, no
  `readline()`.
- Every wait has a hard deadline; a case that overruns is killed, never left
  holding an engine.
- Waits are on `bestmove`, `readyok`, or `nodes N` — never on `info depth`.
  (`go perft` answers `nodes N` and never emits `bestmove`; waiting for
  `bestmove` there is a harness bug, found and fixed during development.)
- Every reply line is timestamped and attributed to the most recent preceding
  command write, so "where did the refusal appear" is measured from the protocol
  stream rather than guessed from text order.

## Self-test (both detectors proven able to fail)

`python3 selftest.py /tmp/brokenb/forge` → `SELFTEST PASS`

- Sanitizer detector: 4 of 6 over-64-char `position fen` cases flagged on an
  engine with a planted heap overflow; 0 false positives across 12 ordinary FEN
  cases.
- Hang detector: a wrapper that reads and never answers is flagged
  `unresponsive`; a healthy wrapper is not.
- All FEN fixtures validated legal with python-chess 1.11.2.

## Corpus

123 cases across the six assigned classes, each malformed `position` class run in
both harness patterns (`position→isready→go` and `position→go`).

Running now. Results, counts and `FUZZ.md` to follow in this directory.

## Not yet claimed

No crash, no hang, and no sanitizer line is claimed at this time.

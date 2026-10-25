# S02 gate-option precheck — 2026-10-25

Python **3.10 or later**, standard library only. The normal engine and PC gate build keep `FORGE_WARN_UNKNOWN_OPTIONS=OFF`. Build a separate warning-enabled executable for this precheck; it must use `-DFORGE_WARN_UNKNOWN_OPTIONS=ON` through CMake. This tool never enables that setting, launches games, runs bench/perft, changes host limits or signals its caller.

```bash
python3 -B forge_sol_S02_gate_option_precheck_20261025.py \
  --manifest forge_sol_S02_gate_precheck_clean_20261025.json \
  --engine /absolute/path/to/separate-warn-ON/forge \
  --out /absolute/path/to/NEW-precheck-output
```

`--out` must not exist and its parent must already exist. Existing output is rejected with one line and exit 1. `--timeout` defaults to 10 seconds per readiness barrier and can be increased on a busy machine. The tool writes only its new output; inputs are hashed before/after. A timed-out child is asked to quit gracefully, never killed; an unclosed PID/incomplete stream is reported as failure rather than complete evidence.

The manifest is a nonempty JSON list. Every gate has a unique string `id`, positive integer `Threads`/`Hash`, boolean `OwnBook`, and an `options` object. Other metadata is ignored. Options must not repeat those three core settings; duplicate JSON keys and embedded CR/LF/NUL are errors. Option values may be finite numbers, booleans or strings. Booleans render as lowercase `true`/`false`, numbers use their standard JSON representation, and strings retain their exact single-token value text. Current Forge reads only one value token, so empty or whitespace-containing values are rejected rather than silently truncated. Commands are emitted in core order Threads/Hash/OwnBook, then the manifest's options order. Multiword option names use canonical single spaces, with no leading/trailing whitespace or literal `value` token. Core-setting aliases such as `Hash ` are rejected.

One fresh process is used per gate. It exchanges `uci`, then a reserved deliberately unknown capability probe, then each exact `setoption name ... value ...` line followed by `isready`. The capability probe prevents a silent warning-OFF executable from producing a false clean result; it is not a new UCI option. Every option is checked in a readiness-bounded context so an unknown reply names both the manifest gate and exact option. A final full captured-stream sweep also rejects diagnostics emitted during quit/EOF drain. Hidden recognized tunables are allowed; the advertised option list is not used as an exhaustive allowlist.

Exit 0 means every gate completed cleanly. Exit 1 names the gate/option on an unknown reply, and also covers malformed input, invalid-value diagnostics, wrong warning capability, child/stderr failures, changed inputs or incomplete capture. The two supplied fixtures demonstrate a clean gate and a typo `RefutLmrMinr`; the live PC manifest and live gates are **UNVERIFIED** and were not accessed or edited. This is not the later full gate-schema validator or a strength/activation test.

The result JSON retains original stdin/stdout/stderr as base64 plus full SHA256 and byte counts, child exit, EOF completion and exact sent lines. CRLF is normalized only for parsing; raw bytes remain unchanged. An output checksum file is generated and verified with that output as the working directory. Raw engine banners remain encoded.

Run the Python-only tests from this folder:

```bash
python3 -B forge_sol_S02_gate_precheck_tests_20261025.py -v
```

Their children are explicitly Python protocol fixtures, not chess engines. The engine warning regression is separately wired into CTest only when the warning build switch is ON. All patches/tools remain UNPROVEN for playing strength and speed; no PC script, PGO or live gate is run.

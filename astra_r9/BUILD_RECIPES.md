# Build and proof reproduction

Production source is commit fb58080, frozen under D:\a9\c1. Only include/ and src/
enter kit builds. The original lock remains at the user-supplied C: path, read only.
All execution output/temp/cache paths belong under D:\a9. Never reuse existing output
tags or overwrite retained executables/logs. Check resource limits before running.

Production: unchanged build_ltopgo.ps1 v2.3, MD5 729FE7275C3C01D22C751CB751D5C9D2,
PowerShell 7.6.8, -SrcDir D:\a9\c1 -Work D:\a9\w -Tag <fresh-short-tag> -Affinity 12
-Expose -CheckOpt NNUEWideOutput=true, with all specified bench and perft pins.
tools/build_pair.py records complete argv, verifies source manifests, and constrains
only its own descendants to Idle and CPUs 2/3. Its existing tags are immutable;
choose new tags before reproducing. The kit retains -flto=1, frozen PGO workload,
-ffp-contract=off, -fno-fast-math and -march=znver5. Plain kit builds are identity
controls only, never speed comparison arms.

Auxiliary diagnostic and sanitizer commands, compiler versions/hashes, environment,
source/harness identities, and executable hashes are retained in
evidence/auxiliary-build-provenance.json. This command record was reconstructed from
the executed tool history after review; empty original compiler stdout logs are
retained and are not presented as command logs. Commands are argv arrays, not shell
strings. Set the indicated compiler bin directory first in process-local PATH.
Use new output filenames when rerunning them.

Diagnostic binaries are correctness tools, not production candidates. Run each
against evidence/fens_12k.txt and compare the full PASS record. The wide build also
asserts each OFF/ON lane/output float bit and incremental/fresh accumulator bit;
FORGE_NNUE_DIAGNOSTICS is absent from production. Sanitizer builds use llvm-mingw
with address+undefined instrumentation, recovery disabled, O1/debug/frame pointers.
LeakSanitizer is not claimed: detect_leaks=0 is explicit on Windows.

Run tools/validate_uci.py pins/smoke/selfplay with fresh evidence directories.
Selfplay sanitizer OFF and ON runs use eight deterministic starting FENs, up to
80 plies/game, 1000 search nodes/move, and the independent python-chess legality
oracle; termination at game-over explains fewer than 640 plies. Positive controls
deliberately fail and are kept separate from the zero-report engine checks.

tools/parity_release.py compares lock/OFF/ON production depth-2 results on all
12000 FENs. tools/verify_packet.py checks source commit blobs, manifest and binary
identity, mode attribution, pins, parity, smoke legality and complete sanitizer
transcripts. Give the audit a fresh output filename. Timing protocols are separately
preregistered; a correctness audit never grants speed acceptance.

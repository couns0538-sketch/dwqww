#!/usr/bin/env bash
# Replica check of the status handling in opus_round1/sol_SIT/ci_sit.sh (code review finding 4): the script's own
# lines from the uci_check.py step to the final status echo run with python3 replaced by a shell function that
# prints "ALL OK" (so only the exit status differs) and exits with <rc>. nm/sha256sum act on missing files and only
# write to the hot-function log. Writes only into <out_dir>.
# usage: ci_exit_check.sh <ci_sit.sh> <rc> <out_dir>
set -uo pipefail
CI_SH=$1; STUB_RC=$2; OUT=$3
mkdir -p "$OUT"
CI=/nonexistent/ci; JOB=/nonexistent/job
status=0
python3() { echo "ALL OK"; echo "stub python3 ${*:1:2} ... -> exit $STUB_RC"; return "$STUB_RC"; }
block=$(sed -n '/uci_check\.py" "\$OUT\/build_sit\/forge"/,/^echo "ci_sit status/p' "$CI_SH")
[ -n "$block" ] || { echo "block not found"; exit 2; }
eval "$block"
echo "replica: python3 exit $STUB_RC -> status=$status"

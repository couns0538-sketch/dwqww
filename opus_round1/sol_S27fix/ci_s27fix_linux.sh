#!/usr/bin/env bash
# S27fix on Linux (GitHub runner): the v2 tests, and Sol's own S27 suites run against v2 through the same shim as on
# the PC (v2 tools under Sol's v1 file names next to his unchanged test files from 17aa0cae). Closes the REPORT's
# "v2 on Linux not run (Sol's suite in CI): UNVERIFIED". Read-only on the repo; writes only under <out_dir>.
# usage: opus_round1/sol_S27fix/ci_s27fix_linux.sh <out_dir>
set -uo pipefail
OUT=${1:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
J="$ROOT/opus_round1/sol_S27fix"
SOL=17aa0cae
SOLDIR=releases/forge_sol_pack31_20261025/S27
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
status=0
{ python3 --version; git --version; patch --version | head -1; } 2>&1 | tee "$OUT/toolchain.log"
# Sol's v1 (for the v2 tests' v1-contrast cases) and his unchanged suites
mkdir -p "$OUT/sol_v1" "$OUT/shim"
for f in forge_sol_S27_hygiene_20261026.py forge_sol_S27_buildcompare_20261026.py forge_sol_S27_known_hashes_20261026.json \
         test_forge_sol_S27_buildcompare_20261026.py test_forge_sol_S27_hygiene_20261026.py; do
  git -C "$ROOT" show "$SOL:$SOLDIR/$f" > "$OUT/sol_v1/$f" || { echo "missing $f on $SOL"; exit 1; }
done
sha256sum "$OUT"/sol_v1/* | tee "$OUT/sol_v1_sha256.log"
# shim: v2 tools under v1 names + Sol's test files and data
cp "$J/forge_sol_S27_hygiene_v2_20261027.py" "$OUT/shim/forge_sol_S27_hygiene_20261026.py"
cp "$J/forge_sol_S27_buildcompare_v2_20261027.py" "$OUT/shim/forge_sol_S27_buildcompare_20261026.py"
cp "$J/forge_sol_S27_buildcompare_v2_20261027.py" "$J/forge_sol_S27_known_hashes_20261026.json" \
   "$J/forge_sol_S27_reviewed_bugfixes_v2_20261027.json" "$OUT/shim/"
cp "$OUT/sol_v1/test_forge_sol_S27_buildcompare_20261026.py" "$OUT/sol_v1/test_forge_sol_S27_hygiene_20261026.py" "$OUT/shim/"
mkdir -p "$OUT/scratch"
S27_SCRATCH="$OUT/scratch" S27_V1="$OUT/sol_v1/forge_sol_S27_hygiene_20261026.py" \
  python3 -I -B "$J/test_forge_sol_S27_v2_20261027.py" -v > "$OUT/tests_v2_linux.log" 2>&1 || status=1
tail -4 "$OUT/tests_v2_linux.log"
# Expected on v2 (by design, see REPORT): Sol's buildcompare fixture prints his dev-base d11 308972 while v2's default
# pins are AL1 (S27-2), so the first d11 gate fails before the UCI capture that replaces the file; that one test fails.
declare -A EXPECTED=([buildcompare]="test_probe_rejects_file_replacement_during_protocol_capture" [hygiene]="")
for t in buildcompare hygiene; do
  (cd "$OUT/shim" && python3 -B "test_forge_sol_S27_${t}_20261026.py" -v) > "$OUT/sol_suite_${t}_on_v2_linux.log" 2>&1
  echo "Sol's ${t} suite on v2 (Linux): exit $? :: $(tail -1 "$OUT/sol_suite_${t}_on_v2_linux.log")"
  got=$(grep -E '^(FAIL|ERROR):' "$OUT/sol_suite_${t}_on_v2_linux.log" | sed -E 's/^(FAIL|ERROR): ([a-zA-Z0-9_]+).*/\2/' | sort | tr '\n' ' ' | sed 's/ $//')
  echo "  failing: [${got}] expected: [${EXPECTED[$t]}]"
  [ "$got" = "${EXPECTED[$t]}" ] || { echo "  UNEXPECTED Sol-suite result for $t"; status=1; }
done
echo "ci_s27fix_linux status=$status"
exit $status

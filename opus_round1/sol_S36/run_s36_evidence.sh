#!/usr/bin/env bash
# S36 evidence on the real merge record (read-only copies): Job C + S01 merges into the lock-derived tree L' and the
# in-place base B, the CR LOW 1-4 follow-up, planted one-line changes, determinism.
# usage: run_s36_evidence.sh <inputs dir> <scratch dir>   (inputs: merge_record/ and approved/ as copied for S36)
set -uo pipefail
IN=$1; SCR=$2
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python}
V="$HERE/forge_sol_S36_samediff_verify_20261027.py"
M="$IN/merge_record"; A="$IN/approved"
L="$M/merge_jobC_S01_lockderived_h256e12_20261025.diff"
B="$M/merge_jobC_S01_base_h256e12_buffix_20261025.diff"
FL="$M/followup_CR_LOW1-4_lockderived_h256e12_20261025.diff"
FB="$M/followup_CR_LOW1-4_base_h256e12_buffix_20261025.diff"
JC="$A/forge_sol_knownfail_h256e12_20261025.patch"
S1="$A/forge_sol_S01_pinmsg_20261025.patch"
mkdir -p "$SCR"
run() { local name=$1 expect=$2; shift 2
  echo "=== $name (expected exit $expect)"
  "$PY" -I -B "$V" "$@" --json "$SCR/$name.json"; local rc=$?
  echo "exit $rc"; [ "$rc" -eq "$expect" ] && echo "AS EXPECTED" || { echo "UNEXPECTED"; status=1; }
}
status=0
echo "# inputs"; (cd "$M" && sha256sum -c --ignore-missing SHA256SUMS_merge_jobC_S01_20261025.txt); sha256sum "$JC" "$S1"
run r1_jobC_S01_only 1 --a L="$L" --b B="$B" --approved "$JC" "$S1"
run r2_jobC_S01_followupL 0 --a L="$L" --b B="$B" --approved "$JC" "$S1" "$FL"
run r3_jobC_S01_followupB 0 --a L="$L" --b B="$B" --approved "$JC" "$S1" "$FB"
run r4_followup_L_vs_B 0 --a L="$FL" --b B="$FB"
{ cat "$B"; printf -- '--- a/tests/tests.cpp\n+++ b/tests/tests.cpp\n@@ -5,0 +6,1 @@\n+// planted extra line (S36 check)\n'; } > "$SCR/B_planted_tests.diff"
run r5_planted_tests_line 1 --a L="$L" --b B="$SCR/B_planted_tests.diff" --approved "$JC" "$S1" "$FL"
{ cat "$B"; printf -- '--- a/src/search.cpp\n+++ b/src/search.cpp\n@@ -10,0 +11,1 @@\n+// planted source line (S36 check)\n'; } > "$SCR/B_planted_src.diff"
run r6_planted_src_line 1 --a L="$L" --b B="$SCR/B_planted_src.diff" --approved "$JC" "$S1" "$FL"
run r2_again 0 --a L="$L" --b B="$B" --approved "$JC" "$S1" "$FL"
if cmp -s "$SCR/r2_jobC_S01_followupL.json" "$SCR/r2_again.json"; then echo "determinism: r2 JSON byte-identical on re-run"
else echo "determinism: DIFFERENT"; status=1; fi
run r8_AL1_optional_patch_vs_L 0 --a L="$L" --b AL1patch="$IN/merge_record/forge_lockderived_jobC_S01_tests_tools_vs_AL1.patch" \
  --approved "$JC" "$S1" "$FL"
echo "evidence status=$status"
exit $status

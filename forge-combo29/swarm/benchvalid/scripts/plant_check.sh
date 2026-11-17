#!/usr/bin/env bash
# Prove verify_figures.py fires on each fault it is supposed to catch.
#
# The brief's rule 3: a control that silently does nothing is worse than no control. Every
# guard in verify_figures.py is planted with the specific defect that motivated it, and
# this script requires a non-zero exit AND a message naming the fault. It also requires the
# clean tree to pass, so a guard that fails everything does not score.
#
# Faults:
#   A  the withdrawn sensitivity range  (originally "4.5 % to 64 %")
#   B  a stale blind-spot count         (originally "5 of 9" in the section 0 table)
#   B2 the spelled-out form             ("Five of nine" vs "Six of nine")
#   C  a short distinct_values field    (originally missing 72,365)
#   D  the withdrawn 6.4x order swing   (originally "up to 6.4x")
#   E  a coverage figure
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE/.."
pass=0; fail=0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cp "$ROOT/FINDINGS.md" "$tmp/FINDINGS.md"
cp "$ROOT/evidence/go_repeatability.json" "$tmp/gr.json"

restore() { cp "$tmp/FINDINGS.md" "$ROOT/FINDINGS.md"; cp "$tmp/gr.json" "$ROOT/evidence/go_repeatability.json"; }

run_case() {
  local name="$1" expect_substr="$2"
  local out rc
  out="$(python3 "$HERE/verify_figures.py" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "FAIL [$name] guard did not fire (exit 0)"; fail=$((fail+1))
  elif ! grep -qF "$expect_substr" <<<"$out"; then
    echo "FAIL [$name] fired but not for the stated reason; got:"
    sed 's/^/       /' <<<"$out" | head -4
    fail=$((fail+1))
  else
    echo "PASS [$name] $(head -1 <<<"$out")"; pass=$((pass+1))
  fi
  restore
}

if python3 "$HERE/verify_figures.py" >/dev/null 2>&1; then
  echo "PASS [clean] verify_figures.py is green before planting"; pass=$((pass+1))
else
  echo "FAIL [clean] the clean tree does not pass, so plant results are void"; fail=$((fail+1))
fi

python3 - "$ROOT/FINDINGS.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
t = t.replace("**2.2 % to 30.3 %** on `bench 13`", "**4.5 % to 64 %** on `bench 13`", 1)
p.write_text(t)
PY
run_case "A sensitivity range" "4.5 % to 64 %"

python3 - "$ROOT/FINDINGS.md" <<'PY'
import sys, pathlib, re
p = pathlib.Path(sys.argv[1]); t = p.read_text()
t = re.sub(r"\*\*6 of 9\*\* behavioural mutants", "**5 of 9** behavioural mutants", t, count=1)
p.write_text(t)
PY
run_case "B blind-spot count" "5 of 9"

python3 - "$ROOT/FINDINGS.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
t = t.replace("**Six of nine real behaviour changes", "**Five of nine real behaviour changes", 1)
p.write_text(t)
PY
run_case "B2 spelled count" "Five of nine"

python3 - "$ROOT/evidence/go_repeatability.json" <<'PY'
import sys, json
p = sys.argv[1]; d = json.load(open(p))
d["distinct_values"] = [11696, 13235, 50541]
json.dump(d, open(p, "w"), indent=2)
PY
run_case "C short distinct_values" "distinct_values"

python3 - "$ROOT/FINDINGS.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
t = t.replace("**72,365 / 11,696 = 6.19\u00d7**", "**up to 6.4\u00d7**", 1)
p.write_text(t)
PY
run_case "D withdrawn 6.4x swing" "6.4"

python3 - "$ROOT/FINDINGS.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
t = t.replace("**63.0 % of lines, 59.6 % of functions**", "**68.0 % of lines, 59.6 % of functions**", 1)
p.write_text(t)
PY
run_case "E coverage figure" "63.0"

echo
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ] || exit 1

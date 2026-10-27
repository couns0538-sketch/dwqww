#!/usr/bin/env bash
# S49 box run (GitHub-hosted ubuntu-24.04 runner = a quiet "box" without gates; labelled box-only):
#   1. builds the lock tree (release, box flags) and a TEST-ONLY copy with test_only_synthetic_slowdown.patch
#      (-DFORGE_S49_SYNTHETIC_SLOWDOWN_PCT=5: bench burns 5% of its search time; nodes unchanged);
#   2. runs pc_speed_ci_20261027.ps1 -SelfTest and the Python tests (pwsh on Linux);
#   3. A/A run: lock vs lock, >= 40 pairs + control pairs -> the CI must contain 1.00;
#   4. A/B run: lock vs the synthetic 5% slowdown -> the CI must exclude 1.00.
# usage: opus_round1/sol_S49/ci_s49_box.sh <out_dir>
set -uo pipefail
OUT=${1:-ci_out}
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
J="$ROOT/opus_round1/sol_S49"
CXX=${CXX:-$(command -v g++-14 || command -v g++)}
FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
status=0
{
  echo "== runner: $(nproc) CPUs; $(lscpu | grep 'Model name' | sed 's/  */ /g')"
  echo "== pwsh: $(pwsh -NoProfile -Command '$PSVersionTable.PSVersion.ToString()')"
  echo "== thermal zones: $(ls /sys/class/thermal 2>/dev/null | tr '\n' ' ')"
} | tee "$OUT/runner.log"
cmake -S "$ROOT" -B "$OUT/build_lock" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" "-DCMAKE_CXX_FLAGS=$FLAGS" > "$OUT/configure_lock.log" 2>&1 || exit 1
cmake --build "$OUT/build_lock" --target forge -j"$(nproc)" > "$OUT/build_lock.log" 2>&1 || { tail -40 "$OUT/build_lock.log"; exit 1; }
SLOW_SRC="$OUT/src_slow"
mkdir -p "$SLOW_SRC"
(cd "$ROOT" && tar -cf - src include tests bench tools CMakeLists.txt) | (cd "$SLOW_SRC" && tar -xf -)
(cd "$SLOW_SRC" && git apply --check -p1 "$J/test_only_synthetic_slowdown.patch" && git apply -p1 "$J/test_only_synthetic_slowdown.patch") > "$OUT/patch_slow.log" 2>&1 || { cat "$OUT/patch_slow.log"; exit 1; }
cmake -S "$SLOW_SRC" -B "$OUT/build_slow" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" "-DCMAKE_CXX_FLAGS=$FLAGS -DFORGE_S49_SYNTHETIC_SLOWDOWN_PCT=5" > "$OUT/configure_slow.log" 2>&1 || exit 1
cmake --build "$OUT/build_slow" --target forge -j"$(nproc)" > "$OUT/build_slow.log" 2>&1 || { tail -40 "$OUT/build_slow.log"; exit 1; }
sha256sum "$OUT/build_lock/forge" "$OUT/build_slow/forge" | tee "$OUT/exe_sha256.log"
python3 "$ROOT/opus_round1/ci/uci_check.py" "$OUT/build_lock/forge" 2>&1 | tee "$OUT/identity_lock.log" || status=1
python3 "$ROOT/opus_round1/ci/uci_check.py" "$OUT/build_slow/forge" 2>&1 | tee "$OUT/identity_slow.log" || status=1
pwsh -NoProfile -File "$J/pc_speed_ci_20261027.ps1" -SelfTest 2>&1 | tee "$OUT/selftest.log"; [ "${PIPESTATUS[0]}" -eq 0 ] || status=1
PWSH=pwsh python3 -I -B "$J/tests/test_pc_speed_ci.py" > "$OUT/tests.log" 2>&1 || status=1
tail -4 "$OUT/tests.log"
pwsh -NoProfile -File "$J/pc_speed_ci_20261027.ps1" -ExeA "$OUT/build_lock/forge" -ExeB "$OUT/build_lock/forge" -Depths 13,16 -Pairs 40 \
  -ControlEvery 4 -BoxOnly -ReservedCores 0 -AllowNoTemperature -OutDir "$OUT/run_aa" -Label "box-only A/A (GitHub runner)" 2>&1 | tee "$OUT/run_aa.log"
[ "${PIPESTATUS[0]}" -eq 0 ] || status=1
pwsh -NoProfile -File "$J/pc_speed_ci_20261027.ps1" -ExeA "$OUT/build_lock/forge" -ExeB "$OUT/build_slow/forge" -Depths 13,16 -Pairs 40 \
  -ControlEvery 4 -BoxOnly -ReservedCores 0 -AllowNoTemperature -OutDir "$OUT/run_slow5" -Label "box-only synthetic 5% slowdown (GitHub runner)" 2>&1 | tee "$OUT/run_slow5.log"
[ "${PIPESTATUS[0]}" -eq 0 ] || status=1
python3 - "$OUT" <<'PY' | tee "$OUT/verdict.log"
import json, sys
out = sys.argv[1]
aa = json.load(open(f"{out}/run_aa/summary.json", encoding="utf-8-sig"))
sl = json.load(open(f"{out}/run_slow5/summary.json", encoding="utf-8-sig"))
ok = True
for d, r in aa["per_depth"].items():
    c = r["ci95"]; inside = c[0] <= 1.0 <= c[1]; ok &= inside
    print(f"A/A {d}: median {r['median_ratio']:.4f} CI {c[0]:.4f}-{c[1]:.4f} contains 1: {inside}; control CI {r.get('control_ci95')} contains 1: {r.get('control_ci_contains_1')}")
for d, r in sl["per_depth"].items():
    c = r["ci95"]; excl = c[1] < 1.0; ok &= excl
    print(f"5% slowdown {d}: median {r['median_ratio']:.4f} CI {c[0]:.4f}-{c[1]:.4f} excludes 1 (below): {excl}; nodes A=B: {r['node_exact']}")
print("S49 BOX VERDICT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
[ "${PIPESTATUS[0]}" -eq 0 ] || status=1
echo "ci_s49_box status=$status"
exit $status

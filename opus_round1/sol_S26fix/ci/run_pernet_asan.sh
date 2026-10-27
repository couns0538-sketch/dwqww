#!/usr/bin/env bash
# S26-v4-3: per-net ASan+UBSan on base B + one net (Linux CI), mirroring opus-ci's asan mode
# (g++-14, RelWithDebInfo, x86-64-v3, no FMA contraction, -DFORGE_ENABLE_SANITIZERS=ON, recover off).
# PASS = no sanitizer report anywhere, every configured test ran, the only failing test is forge_tests, its
# FAIL/KNOWN_FAILURE/PIN_MISMATCH lines equal Sol's Release lines for this net, and the sanitizer build's
# bench d11 equals the net's frozen reference. Test expectations are never edited.
# usage: run_pernet_asan.sh <B_lock|f019|f020|f021|f022|f023> <out_dir>
set -uo pipefail
NET_ID=$1
OUT=$(realpath -m "$2")
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
WORK=$(realpath -m "${RUNNER_TEMP:-/tmp}/s26fix_asan_$NET_ID")
case "$NET_ID" in
  B_lock) F=resid_h256_e12_e_ep12 ;;
  f019) F=resid_h256_e20_f019_b06_ep20 ;;
  f020) F=resid_h256_e16_f020_b06_sol_ep16 ;;
  f021) F=resid_h256_e20_f021_b06_ep20 ;;
  f022) F=resid_h256_e20_f022_b06_ep20 ;;
  f023) F=resid_h256_e16_f023_b06_ep16 ;;
  *) echo "unknown net id $NET_ID" >&2; exit 2 ;;
esac
CXX=${CXX:-$(command -v g++-14)}
mkdir -p "$OUT" "$WORK"
LOGDIR="$OUT/sanitizer_logs"
mkdir -p "$LOGDIR"
bash "$HERE/make_base_B.sh" "$ROOT" "$WORK/B_src" | tee "$OUT/make_base_B.json" || exit 1
cp -r "$WORK/B_src" "$WORK/B_net"
gzip -dc "$HERE/inputs/nets/$F.inc.gz" > "$WORK/B_net/src/nnue_weights.inc"
sha256sum "$WORK/B_net/src/nnue_weights.inc" | tee "$OUT/net_sha256.txt"
BASE_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
BD="$WORK/build_asan"
echo "compiler: $($CXX --version | head -1)" > "$OUT/toolchain.txt"
cmake -S "$WORK/B_net" -B "$BD" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_COMPILER="$CXX" \
  -DFORGE_ENABLE_SANITIZERS=ON "-DCMAKE_CXX_FLAGS=$BASE_FLAGS -fno-sanitize-recover=all" > "$OUT/configure.log" 2>&1 || exit 1
cmake --build "$BD" -j"$(nproc)" > "$OUT/build.log" 2>&1 || { tail -50 "$OUT/build.log"; exit 1; }
export ASAN_OPTIONS="log_path=$LOGDIR/asan:detect_leaks=1:abort_on_error=1"
export UBSAN_OPTIONS="log_path=$LOGDIR/ubsan:print_stacktrace=1:halt_on_error=1"
(cd "$BD" && ctest --output-on-failure --timeout 3000 --output-junit "$OUT/ctest_asan.xml") > "$OUT/ctest_asan.log" 2>&1
echo "ctest exit $?" | tee "$OUT/ctest_exit.txt"
printf 'bench 11\nquit\n' | "$BD/forge" > "$OUT/bench11_asan.txt" 2> "$OUT/bench11_asan.stderr"
echo "bench exit $?" >> "$OUT/ctest_exit.txt"
python3 -B "$HERE/check_pernet_asan.py" --net "$NET_ID" --out "$OUT" \
  --expected "$HERE/inputs/expected_v3_diagnostics.json" | tee "$OUT/asan_check.json"
exit "${PIPESTATUS[0]}"

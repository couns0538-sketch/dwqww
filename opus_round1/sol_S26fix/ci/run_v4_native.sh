#!/usr/bin/env bash
# S26-v4-1: re-run ONE of Sol's six frozen-v3 native first attempts under Sol's delivered v4
# (successor_ctest_v4/forge_sol_S26_netbatch_v4_20261026.py, sha256 4dbf73e6...), bytes unchanged, on a
# Linux CI runner (v4 needs fcntl, /proc/meminfo and sched_setaffinity, so it cannot run on the Windows PC).
# Inputs: Sol's packet (read-only sparse checkout of 17aa0cae), base B rebuilt by make_base_B.sh (must equal
# Sol's 78-file snapshot), one net from inputs/nets. Every v4 output except private source copies and build
# trees is copied to <out_dir> for the artifact; summarize_v4.py compares the outcome with Sol's v3 attempt.
# usage: run_v4_native.sh <B_lock|f019|f020|f021|f022|f023> <packet_root> <out_dir>
set -uo pipefail
NET_ID=$1
PKT=$(realpath "$2")
OUT=$(realpath -m "$3")
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
WORK=$(realpath -m "${RUNNER_TEMP:-/tmp}/s26fix_v4_$NET_ID")
case "$NET_ID" in
  B_lock) F=resid_h256_e12_e_ep12 ;;
  f019) F=resid_h256_e20_f019_b06_ep20 ;;
  f020) F=resid_h256_e16_f020_b06_sol_ep16 ;;
  f021) F=resid_h256_e20_f021_b06_ep20 ;;
  f022) F=resid_h256_e20_f022_b06_ep20 ;;
  f023) F=resid_h256_e16_f023_b06_ep16 ;;
  *) echo "unknown net id $NET_ID" >&2; exit 2 ;;
esac
mkdir -p "$OUT" "$WORK"
V4="$PKT/S26/successor_ctest_v4/forge_sol_S26_netbatch_v4_20261026.py"
echo "4dbf73e63032d7512c6beff12fdca03b7d29e1489b6d0ae3cab26b09753ac36f  $V4" | sha256sum -c - | tee "$OUT/v4_sha256_check.txt" || exit 1
bash "$HERE/make_base_B.sh" "$ROOT" "$WORK/B_src" | tee "$OUT/make_base_B.json" || exit 1
gzip -dc "$HERE/inputs/nets/$F.inc.gz" > "$WORK/$F.inc"
sha256sum "$WORK/$F.inc" | tee "$OUT/net_sha256.txt"
python3 -B "$PKT/S26/forge_sol_S26_setup_local_dependencies_20261026.py" --packet-root "$PKT" \
  --out "$PKT/S26/owner_dependencies_ci_$NET_ID.json" --lock-file "$PKT/S26/owner_resource_ci_$NET_ID.lock" \
  | tee "$OUT/setup.json" || exit 1
{ echo "compiler: $(g++-14 --version | head -1)"; echo "cmake: $(cmake --version | head -1)"; echo "python: $(python3 --version)";
  python3 -c 'import chess; print("python-chess", chess.__version__)'; nproc; lscpu | grep -E 'Model name' ; } > "$OUT/toolchain.txt" 2>&1
# TOOL=v5 runs the Opus v5 successor (v4 + the CTest JUnit status="fail" fix) with identical arguments.
TOOL=${TOOL:-v4}
if [ "$TOOL" = v5 ]; then
  V5="$HERE/../forge_sol_S26_netbatch_v5_20261027.py"
  sha256sum "$V5" | tee "$OUT/v5_sha256.txt"
  RUNNER=(python3 -B "$V5")
else
  RUNNER=(sh "$PKT/S26/forge_sol_S26_run_v4_20261026.sh")
fi
START=$(date -u +%FT%TZ)
"${RUNNER[@]}" \
  --dependencies "$PKT/S26/owner_dependencies_ci_$NET_ID.json" \
  --base "$WORK/B_src" \
  --net "$WORK/$F.inc" \
  --out "$WORK/v4_out" \
  --bench-ref "$PKT/S26/forge_sol_S26_bench_refs_20261026.json" \
  --allowlist "$PKT/S26/forge_sol_S26_allowlist_20261026.json" \
  --suite "$PKT/provided_inputs/WAC300_original.epd" \
  --lock-file "$PKT/S26/owner_resource_ci_$NET_ID.lock" \
  --cmake "$(command -v cmake)" --ctest "$(command -v ctest)" --objdump "$(command -v objdump)" \
  --cxx "$(command -v g++-14)" --record-pins > "$OUT/v4_stdout.json" 2> "$OUT/v4_stderr.txt"
RC=$?
echo "$TOOL exit $RC start $START end $(date -u +%FT%TZ)" | tee "$OUT/v4_exit.txt"
# Copy v4 outputs (no private source copy, no build tree, no binaries) for the artifact.
if [ -d "$WORK/v4_out" ]; then
  (cd "$WORK/v4_out" && find . -type f ! -path '*/source/*' ! -path '*/build/*' -size -8M -print0 \
     | tar --null -cf - -T -) | (mkdir -p "$OUT/v4_out" && tar -x -C "$OUT/v4_out")
  for b in "$WORK"/v4_out/*/build; do
    [ -d "$b" ] || continue
    d="$OUT/v4_out/$(basename "$(dirname "$b")")/build_meta"; mkdir -p "$d"
    cp "$b/CMakeCache.txt" "$b/compile_commands.json" "$d/" 2>/dev/null || true
    find "$b" -name 'CTestTestfile.cmake' -print0 | tar --null -cf - -T - 2>/dev/null | tar -x -C "$d" 2>/dev/null || true
  done
fi
python3 -B "$HERE/summarize_v4.py" "$NET_ID" "$OUT" "$HERE/inputs/expected_v3_diagnostics.json" | tee "$OUT/summary.json"
# A FAIL verdict from v4 (e.g. WAC reference or PIN_MISMATCH) is a recorded result, not an infrastructure error.
[ -f "$OUT/v4_out/result.json" ] || { echo "v4 produced no result.json" >&2; exit 1; }
exit 0

#!/bin/bash
# build_ltopgo.sh - plain + LTO+PGO build of ANY Forge source tree with the FROZEN profiling workload,
# gcda sha256 manifest + archive, missing-profile/FMA checks, and plain-vs-LTO+PGO node identity. Engine Coder, M8 kit.
# Box rules: nice 19, -j1 (+ -flto=1 serial LTRANS), flock build.lock, taskset core 5 only, wait while load > 5. Never deletes.
#
# usage: bash build_ltopgo.sh --src DIR --tag TAG [--out DIR] [--expose] [--check-opt Name=Value]... [--opt-set "N=V;N2=V2"]...
#                             [--pins d11=..,d13=..] [--perft-pins startpos=..,kiwipete=..] [--depths "11 13 16 20 22"] [--fen-depth 13]
#   --src        candidate source tree (CMakeLists.txt at its root); read only
#   --tag        run name; output goes to OUT/TAG (default OUT = <kit>/runs); refuses if OUT/TAG already exists
#   --expose     add -DFORGE_EXPOSE_TUNABLES=ON to BOTH builds (only needed to see tunables in the uci list; release accepts them silently)
#   --check-opt  one extra node-identity run with that single option set (repeatable; each is its own run)
#   --opt-set    one extra run with several options at once, ";" separated (repeatable); option names may contain spaces
#   --pins       expected OFF bench totals (e.g. the lock's); --perft-pins expected perft5 counts. Without them plain-vs-LP only.
# The PROFILE run itself never sets any option (workload/frozen_train_cmds.txt, sha256 checked).
set -euo pipefail
export TZ=Europe/Vienna
KIT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WL=$KIT/workload/frozen_train_cmds.txt; WL_SHA=1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
FENS=$KIT/workload/bench_fens.txt;    FENS_SHA=16f158933265dc5dc05ffd00a181809d345b25d72d3de8e169804efed7b1a835
LOCK=${LOCK:-/workspace/forge-coder/build.lock}; CXX=g++-14; CORE=${CORE:-5}; LOADMAX=${LOADMAX:-5}   # env-overridable (CR L5); Coder box rules = defaults
BASEFLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"   # = AL1 box CMake cache (Release adds -O3 -DNDEBUG)
LTO="-flto=1 -fuse-linker-plugin"
SRC=; TAG=; OUTROOT=$KIT/runs; EXPOSE=OFF; PINS=; PPINS=; DEPTHS="11 13 16 20 22"; FDEPTH=13; RUNS=()
while [ $# -gt 0 ]; do case "$1" in
  --src) SRC=$2; shift 2;; --tag) TAG=$2; shift 2;; --out) OUTROOT=$2; shift 2;; --expose) EXPOSE=ON; shift;;
  --check-opt) RUNS+=("$2"); shift 2;; --opt-set) RUNS+=("$2"); shift 2;;
  --pins) PINS=$2; shift 2;; --perft-pins) PPINS=$2; shift 2;; --depths) DEPTHS=$2; shift 2;; --fen-depth) FDEPTH=$2; shift 2;;
  *) echo "unknown arg $1"; exit 2;; esac; done
[ -n "$SRC" ] && [ -n "$TAG" ] || { sed -n 2,16p "$0"; exit 2; }
SRC=$(cd "$SRC" && pwd); [ -f "$SRC/CMakeLists.txt" ] || { echo "no CMakeLists.txt in $SRC"; exit 2; }
[[ "$TAG" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "bad tag"; exit 2; }
O=$OUTROOT/$TAG; [ -e "$O" ] && { echo "$O exists; use a new --tag (never overwrite)"; exit 1; }
echo "$WL_SHA  $WL" | sha256sum -c --quiet && echo "$FENS_SHA  $FENS" | sha256sum -c --quiet || { echo "frozen workload hash mismatch"; exit 1; }
grep -qi '^setoption' "$WL" && { echo "frozen workload must not set options"; exit 1; }
LEFT=$(find "$SRC" \( -name "*.gcda" -o -name "*.o" -o -name CMakeCache.txt \) -print -quit); [ -z "$LEFT" ] || { echo "source tree has build leftovers ($LEFT); pass a clean copy"; exit 1; }
mkdir -p "$O"/{logs,profile,ident}; P=$O/profile; L=$O/logs
trap 'rc=$?; [ $rc = 0 ] || echo "FAILED $(date "+%F %T %Z") exit $rc -- do not use any exe from this folder" > "$O/FAILED"' EXIT   # CR L3
w(){ while awk -v m=$LOADMAX '{exit !($1>m)}' /proc/loadavg; do echo "$(date '+%F %T %Z') load $(cut -d' ' -f1 /proc/loadavg) >$LOADMAX, waiting"; sleep 60; done; }
log(){ echo "$(date '+%F %T %Z') $*" | tee -a "$L/run.log"; }
cmk(){ # builddir flags logfile
  w; flock "$LOCK" bash -c "nice -n 19 taskset -c $CORE cmake -S '$SRC' -B '$1' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=$CXX -DCMAKE_AR=/usr/bin/gcc-ar-14 -DCMAKE_RANLIB=/usr/bin/gcc-ranlib-14 -DFORGE_EXPOSE_TUNABLES=$EXPOSE '-DCMAKE_CXX_FLAGS=$2' && nice -n 19 taskset -c $CORE cmake --build '$1' --target forge -j1 --clean-first -- VERBOSE=1" > "$3" 2>&1; }
log "src $SRC tag $TAG expose $EXPOSE workload sha256 $WL_SHA"
# source fingerprint (what was built)
(cd "$SRC" && find . -type f ! -path './.git/*' ! -path '*/__pycache__/*' -print0 | sort -z | xargs -0 sha256sum) > "$O/SOURCES.sha256"
python3 - "$SRC/src/uci.cpp" "$FENS" <<'PY' | tee -a "$L/run.log"
import sys
u=open(sys.argv[1]).read(); f=[l.strip() for l in open(sys.argv[2]) if l.strip()]
miss=[x for x in f[1:] if x not in u]
print("bench FEN list check: " + ("same 7 non-start FENs as workload/bench_fens.txt" if not miss else f"WARNING {len(miss)} workload FENs not in this uci.cpp bench list"))
PY
# 1. plain (= lock recipe)
log "plain build"; cmk "$O/build_plain" "$BASEFLAGS" "$L/build_plain.log"; cp "$O/build_plain/forge" "$O/forge_plain_$TAG"
# 2. LTO+PGO instrumented
log "instrumented LTO build"; cmk "$O/build_lp" "$BASEFLAGS $LTO -fprofile-generate=$P -fprofile-update=single" "$L/build_gen.log"
cp "$O/build_lp/forge" "$O/forge_instr_$TAG"
# 3. frozen workload (no setoption: all UCI defaults)
[ -z "$(ls -A "$P")" ] || { log "profile dir not empty; refusing"; exit 1; }
w; log "profile run (frozen workload)"
nice -n 19 taskset -c $CORE timeout 3600 "$O/forge_instr_$TAG" < "$WL" > "$L/profile_run.txt" 2>&1
NB=$(grep -c 'bench depth' "$L/profile_run.txt" || true); grep 'bench depth' "$L/profile_run.txt" | tee -a "$L/run.log"
[ "$NB" = 3 ] || { log "profile run gave $NB bench lines (want 3)"; exit 1; }
NG=$(find "$P" -name '*.gcda' | wc -l); NO=$(find "$O/build_lp" -name '*.o' | wc -l); log "gcda files $NG, objects $NO"
[ "$NG" = "$NO" ] || { log "gcda count != object count"; exit 1; }
(cd "$P" && find . -name '*.gcda' -printf '%P\n' | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$O/gcda_manifest.txt"
MB=$(printf %s "$O/build_lp" | tr / "#"); sed -i "s|$MB|<BUILD>|g" "$O/gcda_manifest.txt"   # names carry the mangled build path; show it as <BUILD>
tar -C "$O" -cf "$O/profile_archive_$TAG.tar" profile
log "gcda_manifest sha256 $(sha256sum "$O/gcda_manifest.txt" | cut -d' ' -f1) (record only)"
(cd "$P" && find . -name '*.gcda' -printf '%P\n' | LC_ALL=C sort | while read -r f; do printf '%s  %s\n' "$(tail -c +13 "$f" | sha256sum | cut -d' ' -f1)" "$f"; done | sed "s|$MB|<BUILD>|g") > "$O/gcda_manifest_nohdr.txt"   # v2.1: first 12 bytes (magic/version/stamp) stripped
log "gcda_manifest_nohdr sha256 $(sha256sum "$O/gcda_manifest_nohdr.txt" | cut -d' ' -f1) (record only; value-profile counters may still differ)"
python3 "$KIT/tools/gcda_arcs_digest.py" "$P" | sed "s|$MB|<BUILD>|g" > "$O/gcda_arcs_manifest.txt"   # edge counters only: reproducible run to run
log "gcda_arcs_manifest sha256 $(sha256sum "$O/gcda_arcs_manifest.txt" | cut -d' ' -f1) (record only since v2.1; binding = exe sha256 of two clean rebuilds)"
# 4. LTO+PGO final (same build dir so the .gcda object paths match)
log "LTO+PGO use build"; cmk "$O/build_lp" "$BASEFLAGS $LTO -fprofile-use=$P -fprofile-correction -Wmissing-profile" "$L/build_use.log"
cp "$O/build_lp/forge" "$O/forge_ltopgo_$TAG"
MP=$(grep 'warning:' "$L/build_use.log" | grep -c 'Wmissing-profile\|profile count data\|coverage mismatch\|Wcoverage-mismatch' || true)
WP=$(grep -c 'warning:' "$L/build_plain.log" || true); WU=$(grep -c 'warning:' "$L/build_use.log" || true)
LL=$(grep -c -- '-flto=1.*-o forge ' "$L/build_use.log" || true)
{ for e in forge_plain_$TAG forge_ltopgo_$TAG; do echo "$e sha256 $(sha256sum "$O/$e"|cut -d' ' -f1) md5 $(md5sum "$O/$e"|cut -d' ' -f1) vfmadd $(objdump -d "$O/$e" | grep -c vfmadd || true)"; done
  echo "compiler warning lines: plain $WP, ltopgo $WU; real missing-profile/coverage warnings: $MP; -flto on link line: $LL"; } | tee "$O/hashes.txt" | tee -a "$L/run.log"
[ "$MP" = 0 ] || { log "FAIL: profile not applied everywhere"; exit 1; }
[ "$LL" -ge 1 ] || { log "FAIL: -flto not on link line"; exit 1; }
FMA=$(awk '{s+=$NF} END{print s+0}' <(grep -o "vfmadd [0-9]*$" "$O/hashes.txt"))
[ "$FMA" = 0 ] || { log "FAIL: vfmadd found ($FMA); the lock has 0"; exit 1; }   # CR L2
# 5. node identity plain vs LTO+PGO: OFF (no setoption at all), then each requested option run
rc=0; i=0
ident(){ # name optargs...
  local n=$1; shift
  for e in plain ltopgo; do w; timeout 7200 python3 "$KIT/tools/lp_check.py" run "$O/forge_${e}_$TAG" "$O/ident/$n.$e.json" "$@" --depths "$DEPTHS" --fen-depth $FDEPTH --fens "$FENS" --core $CORE > "$O/ident/$n.$e.txt"; done
}
log "identity OFF"; ident off
python3 "$KIT/tools/lp_check.py" compare "$O/ident/off.plain.json" "$O/ident/off.ltopgo.json" ${PINS:+--pins $PINS} ${PPINS:+--perft-pins $PPINS} | tee "$O/ident/off.compare.txt" | tee -a "$L/run.log" || rc=1
for r in "${RUNS[@]}"; do i=$((i+1)); a=(); IFS=";" read -ra kvs <<< "$r"; for kv in "${kvs[@]}"; do a+=(--opt "$kv"); done
  log "identity opt$i: $r"; ident opt$i "${a[@]}"
  python3 "$KIT/tools/lp_check.py" compare "$O/ident/opt$i.plain.json" "$O/ident/opt$i.ltopgo.json" --off "$O/ident/off.plain.json" | tee "$O/ident/opt$i.compare.txt" | tee -a "$L/run.log" || rc=1
done
log "RESULT $([ $rc = 0 ] && echo PASS || echo FAIL) (out $O)"; exit $rc

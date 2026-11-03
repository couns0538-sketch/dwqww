#!/usr/bin/env bash
# engine_fresh_check.sh REF OUT [--quick] [extra g++ flags...] - Opus R14-B: does the engine source of REF (a branch,
# tag or commit of this repo; the lock is d4f4312) still search the lock's tree? Read-only on the repo:
#  1. git archive REF src include -> OUT/src (LF files, no worktree; REF must have a top-level src/)
#  2. build with the lock's direct g++ line (box recipe: MSYS2 ucrt64 g++, -std=c++20 -O3 -DNDEBUG
#     -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread, all src/*.cpp or
#     FORGE_UNITS="src/a.cpp ..."; extra flags such as -DFORGE_EXPOSE_TUNABLES=1 go last) on CPUs 2-3 at BelowNormal
#  3. print the exe sha256 and the FMA instruction count (the lock recipe gives 0)
#  4. the lock package's uci_check.py (UCI_CHECK overrides its path) on the same CPUs: bench d11/13/16/20/22 =
#     312866 / 862329 / 3024920 / 12389307 / 34048354, perft 5 startpos 4865609, kiwipete 193690690
#     (--quick: d11/13/16 + perft). Threads 1, Hash 16, OwnBook false - options OFF, as the lock pins need.
# OUT must not exist. Exit 0 ALL OK, 1 a number differs, 2 usage / REF has no src, 3 build failed. A build takes
# ~15 s, the full check ~30 s on a free core (2026-11-02; crew load on CPUs 2-3 makes both longer).
set -u
here=$(cd "$(dirname "$0")" && pwd)
repo=$(git -C "$here" rev-parse --show-toplevel 2>/dev/null || echo /d/grok-pc-data/dwqww)
ref=${1:-}; out=${2:-}
[ -n "$ref" ] && [ -n "$out" ] || { sed -n 2,13p "$0"; exit 2; }
shift 2
full=--full; [ "${1:-}" = "--quick" ] && { full=""; shift; }
[ -e "$out" ] && { echo "engine_fresh_check: $out exists (write fresh, named folders)"; exit 2; }
sha=$(git -C "$repo" rev-parse --verify -q "$ref^{commit}") || { echo "engine_fresh_check: unknown ref $ref"; exit 2; }
git -C "$repo" cat-file -e "$sha:src" 2>/dev/null || { echo "engine_fresh_check: $ref has no top-level src/"; exit 2; }
GPP=${GPP:-/c/msys64/ucrt64/bin/g++.exe}
OBJDUMP=$(dirname "$GPP")/objdump.exe
UCI_CHECK=${UCI_CHECK:-/d/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039/2_build/uci_check.py}
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
for f in "$GPP" "$UCI_CHECK" "$PY"; do [ -f "$f" ] || { echo "engine_fresh_check: missing $f"; exit 2; }; done
mkdir -p "$out/src" || exit 2
git -C "$repo" -c core.autocrlf=false archive "$sha" src include | tar -x -C "$out/src" || exit 2
echo "ref $ref = $sha ($(git -C "$repo" log -1 --format='%cd %s' --date=format:'%F %H:%M' "$sha" | cut -c1-70))"
echo "source: $(find "$out/src" -type f | wc -l) files, tree $(git -C "$repo" rev-parse "$sha:src" | cut -c1-12) (src)"
units=${FORGE_UNITS:-$(cd "$out/src" && ls src/*.cpp | sort | tr '\n' ' ')}
args="-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread $* -Iinclude $units -o ../forge_check.exe"
echo "build: g++ $args" > "$out/build.log"
start=$(date +%s)
( cd "$out/src" && PATH="$(dirname "$GPP"):$PATH" powershell -NoProfile -ExecutionPolicy Bypass \
    -File "$(cygpath -w "$here/lowrun.ps1")" -Mask 0xC -Priority BelowNormal -Exe "$(cygpath -w "$GPP")" \
    -ArgLine "$args" -Out "$(cygpath -w "$out/build.out")" -Err "$(cygpath -w "$out/build.err")" ) \
  || { cat "$out/build.err" | tail -20; echo "engine_fresh_check: build failed (exit 3)"; exit 3; }
[ -f "$out/forge_check.exe" ] || { tail -20 "$out/build.err"; echo "engine_fresh_check: no exe (exit 3)"; exit 3; }
echo "built in $(( $(date +%s) - start )) s; warnings: $(grep -c 'warning:' "$out/build.err" || true)"
echo "exe sha256 $(sha256sum "$out/forge_check.exe" | cut -d' ' -f1)"
echo "FMA (vfmadd/vfmsub/vfnmadd) count: $("$OBJDUMP" -d "$out/forge_check.exe" | grep -cE 'vfn?m(add|sub)' || true)"
start=$(date +%s)
powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$here/lowrun.ps1")" -Mask 0xC -Priority BelowNormal \
  -Exe "$(cygpath -w "$PY")" -ArgLine "-I -B $(cygpath -w "$UCI_CHECK") $(cygpath -w "$out/forge_check.exe") $full" \
  -Out "$(cygpath -w "$out/uci_check.txt")" -Err "$(cygpath -w "$out/uci_check.err")"
rc=$?
cat "$out/uci_check.txt"
echo "check in $(( $(date +%s) - start )) s; exit $rc"
[ $rc = 0 ] && exit 0 || exit 1

#!/usr/bin/env bash
# fresh_checkout_checks.sh [OUT_DIR] - Opus R14-B "works in Forge": run the deliverables from fresh clones of the branches made
# with this PC's default git settings (core.autocrlf=true), not from Opus's worktrees or scratch copies.
#   1 relabel branch: the full test suite (exit codes + reasons, --jobs 2, game across files, disk floor, status, kill)
#   2 relabel branch: build_probe_opt.sh with its defaults (lock source from git, committed training file):
#     LTO exe must be 565ddbf8..., PGO exe 08299f9f... (the tested ones)
#   3 fast-loader branch: rebuild forge_fastloader.dll -> sha256 must equal the tested b5 DLL 9eb29b7d...
#   4 fast-loader branch: the acceptance check with the REBUILT DLL and the clone's forge_fastloader.py
set -u
base=${1:-/c/o14b/fresh}   # OUT_DIR (must not exist); default /c/o14b/fresh
[ -e "$base" ] && { echo "refusing existing $base" >&2; exit 2; }
mkdir -p "$base"
repo=/d/grok-pc-data/dwqww
for b in relabel fast-loader; do
  git clone -q --shared --no-checkout "$repo" "$base/$b" && git -C "$base/$b" checkout -q "origin/opus-r14b-$b" || exit 2
  echo "clone $b at $(git -C "$base/$b" rev-parse --short HEAD) (core.autocrlf=$(git -C "$base/$b" config --get core.autocrlf))"
done
r2=$base/relabel/opus_r14b/item2
l1=$base/fast-loader/opus_r14b/item1
fails=0
ok() { if [ "$2" = "$3" ]; then echo "PASS $1 ($2)"; else echo "FAIL $1: $2 != $3"; fails=$((fails + 1)); fi; }
echo "=== 1 relabel tests from the clone $(date '+%T')"
bash "$r2/test_relabel2.sh" "$base/r2_test" > "$base/r2_test.log" 2>&1
rc=$?
echo "exit=$rc PASS $(grep -c '^PASS' "$base/r2_test.log") FAIL $(grep -c '^FAIL' "$base/r2_test.log")"
grep '^FAIL' "$base/r2_test.log" | head -5
[ $rc = 0 ] || fails=$((fails + 1))
echo "=== 2 probe builds from the clone $(date '+%T')"
bash "$r2/build_probe_opt.sh" "$base/probe" > "$base/probe_build.log" 2>&1 || { echo "FAIL probe build"; fails=$((fails + 1)); }
grep "plain vs\|^lto \|^pgo \|training answers" "$base/probe_build.log"
ok "LTO probe" "$(sha256sum < "$base/probe/lto/forge_data_probe.exe" | cut -c1-16)" 565ddbf8230b7c57
ok "PGO probe" "$(sha256sum < "$base/probe/pgo/forge_data_probe.exe" | cut -c1-16)" 08299f9f6f4bb802
PYV=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
"$PYV" -I -B "$r2/probe_bench.py" run --exe "$(cygpath -w "$base/probe/pgo/forge_data_probe.exe")" \
  --req "$(cygpath -w "$r2/probe_ref_500.tsv")" --out "$(cygpath -w "$base/probe_ref_check.jsonl")" --mask 0x4
"$PYV" -I -B "$r2/probe_bench.py" compare "$r2/probe_ref_500_r13.jsonl" "$base/probe_ref_check.jsonl" \
  || { echo "FAIL the clone-built PGO probe differs from the R13 reference answers"; fails=$((fails + 1)); }
echo "=== 3 DLL rebuild from the clone $(date '+%T')"
bash "$l1/fastloader/build_fastloader.sh" "$base/l1_build" > "$base/l1_build.log" 2>&1 || { echo "FAIL DLL build"; fails=$((fails + 1)); }
ok "fast loader DLL" "$(sha256sum < "$base/l1_build/forge_fastloader.dll" | cut -c1-16)" 9eb29b7d134a73eb
ok "forge_fastloader.py" "$(sha256sum < "$l1/fastloader/forge_fastloader.py" | cut -c1-16)" 39af47b0f347963c
cp "$l1/fastloader/forge_fastloader.py" "$base/l1_build/"
echo "=== 3b the loader self-test built on Windows (MinGW g++ -O2; CI runs it on Linux with sanitizers) $(date '+%T')"
mkdir -p "$base/selftest/scratch"
PATH=/c/msys64/ucrt64/bin:$PATH powershell -NoProfile -File "$(cygpath -w "$l1/tools/lowrun.ps1")" -Mask 0x4 -Priority BelowNormal \
  -Exe 'C:\msys64\ucrt64\bin\g++.exe' -ArgLine "-std=gnu++20 -O2 -pthread -o $(cygpath -w "$base/selftest/ffl_selftest.exe") $(cygpath -w "$l1/fastloader/ffl_selftest.cpp") $(cygpath -w "$l1/fastloader/forge_fastloader.cpp")" \
  -Out "$(cygpath -w "$base/selftest/build.log")" -Err "$(cygpath -w "$base/selftest/build.err")" || true
if [ -s "$base/selftest/ffl_selftest.exe" ]; then
  PATH=/c/msys64/ucrt64/bin:$PATH powershell -NoProfile -File "$(cygpath -w "$l1/tools/lowrun.ps1")" -Mask 0x4 -Priority BelowNormal \
    -Exe "$(cygpath -w "$base/selftest/ffl_selftest.exe")" -ArgLine "$(cygpath -w "$base/selftest/scratch")" \
    -Out "$(cygpath -w "$base/selftest/run.log")" -Err "$(cygpath -w "$base/selftest/run.err")"
  rc=$?; echo "self-test exit=$rc; $(tail -2 "$base/selftest/run.log" | tr '\n' ' ')"; [ $rc = 0 ] || fails=$((fails + 1))
else
  echo "FAIL self-test build: $(tail -3 "$base/selftest/build.err" | tr '\n' ' ')"; fails=$((fails + 1))
fi
echo "=== 4 acceptance with the rebuilt DLL $(date '+%T')"
bash "$l1/tools/fl_acceptance.sh" /d/o14b/npt "$base/l1_accept" 'D:\o14b\ref\libtraining_data_loader.dll' \
  "$(cygpath -w "$base/l1_build")" > "$base/l1_accept.log" 2>&1
rc=$?
cat "$base/l1_accept.log"
grep -h "fast loader:" "$base/l1_accept/ds_fast.log" | head -1
[ $rc = 0 ] || fails=$((fails + 1))
echo "=== 5 adoption rehearsal (HANDOFF steps 1-3b) on a fresh copy of the live trainer tree $(date '+%T')"
npt=$base/npt_copy
mkdir -p "$npt"
npt_w=$(cygpath -w "$npt")  # Git Bash rewrites /E into E:/ (robocopy exit 16): no path conversion for this call
MSYS_NO_PATHCONV=1 robocopy 'F:\opus_scratch\r6\nnue-pytorch-amd' "$npt_w" /E /NFL /NDL /NJH /NJS /NP > "$base/robocopy.log" 2>&1
rc=$?   # robocopy: 0-7 = success
[ $rc -lt 8 ] || { echo "FAIL robocopy exit $rc"; fails=$((fails + 1)); }
(cd "$npt" && sha256sum -c "$l1/trainer_manifest_b2614500.sha256" 2>/dev/null | grep -vc ': OK$' > "$base/manifest_bad.txt")
echo "copy vs the installer's base manifest (from the clone): $(grep -c . "$l1/trainer_manifest_b2614500.sha256") files, not OK: $(cat "$base/manifest_bad.txt")"
/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B "$l1/tools/install_fast_loader.py" "$(cygpath -w "$npt")" \
  --loader-dll "$(cygpath -w "$base/l1_build/forge_fastloader.dll")" || { echo "FAIL installer"; fails=$((fails + 1)); }
bash "$l1/tools/fl_acceptance.sh" "$npt" "$base/adopt_accept" \
  > "$base/adopt_accept.log" 2>&1 || { echo "FAIL acceptance on the fresh copy"; fails=$((fails + 1)); }   # defaults: the copy's own files
cat "$base/adopt_accept.log"
grep -h "fast loader:" "$base/adopt_accept/ds_fast.log" | head -1
echo "=== failures: $fails $(date '+%T')"
exit $((fails > 0))

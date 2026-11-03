#!/usr/bin/env bash
# p6crfix_run.sh - R14-B follow-up (Couns 2026-11-02 ~20:57): after CR's LOW crfix p6_checks_crfix.patch (md5 4b537823)
# was applied with patch -p1 in the opus-r13-p6-syzygy worktree: rebuild and re-run the P6 checks of run_p6.sh /
# run_p6b.sh into fresh folders under C:/o14b/p6crfix (C:/o13/p6 is only read). One step after the other, CPUs 2-3.
set -uo pipefail
export PATH=/c/msys64/ucrt64/bin:$PATH
B=/c/o14b/p6crfix
[ -e "$B" ] && { echo "refusing existing $B"; exit 2; }
W=/d/grok-pc-data/dwqww/.claude/worktrees
P6=$W/o13-p6/opus_r13/p6
T1=$W/o13-p1/opus_r13/tools
LOW=$(cygpath -w "$W/o14b-status/opus_r14b/tools/lowrun.ps1")
GPP='C:\msys64\ucrt64\bin\g++.exe'
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
O=$B/checks
mkdir -p "$O" "$B/port"
echo "=== 0 $(date '+%F %T') branch $(git -C "$W/o13-p6" log -1 --format=%h) + uncommitted crfix: $(git -C "$W/o13-p6" diff --stat | tail -1)"
echo "=== 1 port tree from git (lock d4f4312 + the branch's syzygy_port.patch)"
git -C "$W/o13-p6" -c core.autocrlf=false archive d4f43124dde1d1e37de90e18930e374f32ea7ffa src include | tar -x -C "$B/port"
(cd "$B/port" && patch -p1 --no-backup-if-mismatch < "$P6/syzygy_port.patch" > "$B/port_patch.log" 2>&1); echo "port patch exit $?"
if diff -r "$B/port/src" /c/o13/p6/syz/src > /dev/null && diff -r "$B/port/include" /c/o13/p6/syz/include > /dev/null; then
  echo "PASS port tree = C:/o13/p6/syz (the source of the R13 builds and the kit exe 150374ff)"
else echo "FAIL port tree differs from C:/o13/p6/syz"; fi
echo "=== 2 plain engine build (R13 plain_build.sh flags, CPUs 2-3 BelowNormal)"
units=$(cd "$B/port" && ls src/*.cpp | sort | tr '\n' ' ')
(cd "$B/port" && powershell -NoProfile -File "$LOW" -Mask 0xC -Priority BelowNormal -Exe "$GPP" \
  -ArgLine "-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -DFORGE_EXPOSE_TUNABLES=1 -Iinclude $units -o $(cygpath -w "$B/forge_plain.exe")" \
  -Out "$(cygpath -w "$B/build_plain.out")" -Err "$(cygpath -w "$B/build_plain.err")"); echo "plain build exit $?"
echo "plain exe $(sha256sum < "$B/forge_plain.exe" | cut -c1-16); FMA $(objdump -d "$B/forge_plain.exe" | grep -cE 'vfn?m(add|sub)' || true); bytes differing from R13's C:/o13/p6/syz_plain/forge_plain.exe: $(cmp -l "$B/forge_plain.exe" /c/o13/p6/syz_plain/forge_plain.exe | wc -l) (PE timestamp + checksum only = 4 to 6)"
E=$B/forge_plain.exe
echo "=== 3 OFF / ON benches (lp_check via R13 lpc.sh, CPU 2)"
bash "$T1/lpc.sh" "$E" "$O/off.json" 0x4 > "$O/off.out" 2>&1; echo "OFF: $(grep -E '^bench d' "$O/off.out" | awk '{printf "%s/", $3}') perft $(grep -E '^perft5' "$O/off.out" | awk '{printf "%s ", $3}')"
bash "$T1/lpc.sh" "$E" "$O/tb.json" 0x4 --opt "SyzygyPath=D:\syzygy345" --fen-depth 1 > "$O/tb.out" 2>&1; echo "ON SyzygyPath: $(grep -E '^bench d' "$O/tb.out" | awk '{printf "%s/", $3}')"
bash "$T1/lpc.sh" "$E" "$O/tb_pd4.json" 0x4 --opt "SyzygyPath=D:\syzygy345" --opt SyzygyProbeDepth=4 --fen-depth 1 > "$O/tb_pd4.out" 2>&1; echo "ON SyzygyPath + ProbeDepth 4: $(grep -E '^bench d' "$O/tb_pd4.out" | awk '{printf "%s/", $3}')"
echo "=== 4 tb_probe rebuilt from the patched tb_probe.cpp"
(cd "$B/port" && powershell -NoProfile -File "$LOW" -Mask 0xC -Priority BelowNormal -Exe "$GPP" \
  -ArgLine "-std=c++20 -O2 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -march=x86-64-v3 -static -Iinclude $(cygpath -w "$P6/tb_probe.cpp") src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp -o $(cygpath -w "$B/tb_probe.exe")" \
  -Out "$(cygpath -w "$B/build_tb_probe.out")" -Err "$(cygpath -w "$B/build_tb_probe.err")"); echo "tb_probe build exit $?; $(sha256sum < "$B/tb_probe.exe" | cut -c1-16)"
echo "=== 5 WDL / DTZ vs python-chess (check_tb.py gen, seed 13601: must equal the committed tb200 sample)"
"$PY" -I -B "$P6/check_tb.py" gen D:/syzygy345 "$O/tb200" > "$O/gen.out" 2>&1; echo "gen exit $?: $(tail -1 "$O/gen.out")"
cmp -s "$O/tb200.fens" "$P6/logs/tb200.fens" && echo "PASS fens = logs/tb200.fens" || echo "FAIL fens differ from logs/tb200.fens"
cmp -s "$O/tb200.oracle" "$P6/logs/tb200.oracle" && echo "PASS oracle = logs/tb200.oracle" || echo "FAIL oracle differs from logs/tb200.oracle"
powershell -NoProfile -File "$LOW" -Mask 0xC -Priority BelowNormal -Exe "$(cygpath -w "$B/tb_probe.exe")" \
  -ArgLine "D:\syzygy345 $(cygpath -w "$O/tb200.fens")" -Out "$(cygpath -w "$O/tb200.engine")" -Err "$(cygpath -w "$O/tb200.engine.err")"; echo "tb_probe exit $?"; cat "$O/tb200.engine.err"
"$PY" -I -B "$P6/check_tb.py" compare "$O/tb200" "$O/tb200.engine"; echo "compare exit $?"
cmp -s "$O/tb200.engine" "$P6/logs/tb200.engine" && echo "PASS engine answers = logs/tb200.engine (R13 tb_probe)" || echo "FAIL engine answers differ from logs/tb200.engine"
echo "=== 6 50-move rule cases (check50.py, as run_p6b.sh)"
"$PY" -I -B "$P6/check50.py" "$E" 'D:\syzygy345' "$O/tb200" --depth 6 > "$O/check50.out" 2>&1; echo "check50 exit $?: $(tail -n 1 "$O/check50.out")"
echo "=== end $(date '+%F %T')"

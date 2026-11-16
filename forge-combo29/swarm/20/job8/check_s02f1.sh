#!/usr/bin/env bash
# check_s02f1.sh — seat 20 job 8: does the engine read argv at all?
# Every case: the exact command, the stdout byte count, the exit code, and the first line of output.
set -u
EXE="${1:?exe}"
OUT="${2:?outdir}"
mkdir -p "$OUT"
date -u +"start %Y-%m-%dT%H:%M:%SZ" >> "$OUT/stamps.txt"
echo "exe=$EXE sha256=$(sha256sum "$EXE" | cut -d' ' -f1)"
echo "id name: $(printf 'uci\nquit\n' | "$EXE" 2>/dev/null | grep -m1 '^id name')"
echo
printf '%-32s %-10s %-6s %s\n' "command" "bytes" "exit" "first line of output / verdict"
run() { # label, then the command words
  local label="$1"; shift
  local f="$OUT/case_$label.txt"
  if [ "$label" = "argv_with_stdin" ]; then
    printf 'uci\nquit\n' | timeout 20 "$@" > "$f" 2>&1
  else
    timeout 20 "$@" < /dev/null > "$f" 2>&1
  fi
  local rc=$?
  local n; n=$(wc -c < "$f")
  local first; first=$(head -1 "$f")
  [ -z "$first" ] && first="(no output)"
  local verdict="reads argv"
  [ "$n" -eq 0 ] && verdict="IGNORES argv (0 bytes)"
  printf '%-32s %-10s %-6s %s\n' "$label" "$n" "$rc" "$first  [$verdict]"
}
run no_args              "$EXE"
run argv_bench           "$EXE" bench
run argv_bench13         "$EXE" bench 13
run argv_help            "$EXE" --help
run argv_uci             "$EXE" uci
run argv_garbage         "$EXE" zzzz
run argv_with_stdin      "$EXE" bench 13
echo
echo "-- the stdin form, for comparison (this one is supposed to work):"
printf 'bench 13\nquit\n' | timeout 60 "$EXE" > "$OUT/stdin_bench13.txt" 2>&1
echo "bytes=$(wc -c < "$OUT/stdin_bench13.txt")  line: $(grep 'bench depth' "$OUT/stdin_bench13.txt")"
echo
echo "-- main() source lines:"
grep -n -A4 'int main' /agent/repos/base/forge-combo29/src/uci.cpp | head -10
date -u +"done %Y-%m-%dT%H:%M:%SZ" >> "$OUT/stamps.txt"

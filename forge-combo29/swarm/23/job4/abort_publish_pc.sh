#!/usr/bin/env bash
# abort_publish_pc.sh : does the PC r15 build's FORGE_FIX_ABORT_PUBLISH change the abort behaviour
# that seat 19 measured (19-F12)? File 5 lists FORGE_FIX_ABORT_PUBLISH among the fixes, so this is worth
# an exact measurement rather than an assumption either way.
# Three ways to end a search, base vs PC build, each its own fresh process:
#   A `quit` while a search runs (19-F12's shape)
#   B `stop` while a search runs (what FORGE_FIX_ABORT_PUBLISH is about)
#   C stdin EOF while a search runs
set -u
BASE="${1:-$HOME/build/forge}"
PC="${2:-$HOME/pcbuild/forge}"

meta() {
  local exe="$1"
  echo "   exe=$exe"
  echo -n "   sha256="; sha256sum "$exe" | awk '{print $1}'
  echo -n "   id="; "$exe" <<< "uci
quit" | grep "^id name"
}

probe() { # label exe  shell-snippet-that-writes-input
  local label="$1" exe="$2"; shift 2
  local out
  out=$( "$@" | timeout 30 "$exe" 2>&1 )
  local infos best
  infos=$(printf '%s\n' "$out" | grep -c "info depth")
  best=$(printf '%s\n' "$out" | grep "bestmove" | tail -1)
  printf '   %-22s info_depth_lines=%-3s %s\n' "$label" "$infos" "${best:-<no bestmove>}"
}

for pair in "BASE:$BASE" "PC:$PC"; do
  name="${pair%%:*}"; exe="${pair#*:}"
  echo
  echo "== $name"
  meta "$exe"

  probe "A quit mid-search" "$exe" bash -c 'printf "uci\nisready\nposition startpos\ngo depth 12\nquit\n"'
  probe "B stop mid-search" "$exe" bash -c 'printf "uci\nisready\nposition startpos\ngo depth 12\n"; sleep 0.3; printf "stop\n"; sleep 0.5; printf "quit\n"'
  probe "C EOF mid-search"  "$exe" bash -c 'printf "uci\nisready\nposition startpos\ngo depth 12\n"'
  probe "D go depth 14 + stop" "$exe" bash -c 'printf "uci\nisready\nposition startpos\ngo depth 14\n"; sleep 0.3; printf "stop\n"; sleep 0.5; printf "quit\n"'
  probe "E control: full search" "$exe" bash -c 'printf "uci\nisready\nposition startpos\ngo depth 10\n"; sleep 1.5; printf "quit\n"'
done

#!/usr/bin/env bash
# port_controls.sh - the two build copies of a default-OFF search port tree (own code, 2026-11-06; = SingularNonCut's
# snc_controls.sh with the folder, tree and macro as arguments).
# usage: bash port_controls.sh <src folder> <tree> <MACRO>
#   e.g. bash port_controls.sh /f/ospd/cut_nott_lmr/src cnl FORGE_CUT_NO_TT_LMR
# Input <src folder>/<tree> = trial_w6 source + the port's after_w6 patch, every switch at its source default 0.
# Output (refused if a target exists):
#   <tree>_id   : the six trial_w6 defaults flipped exactly as hunt_identity.sh / speed_pack flip them (TT_NOTLS=1,
#                 NO_ZERO_MOVELISTS=2, SEARCH_SPEED2=1, PREFETCH_EARLY=1, SLIDER_PEXT=1, NNUE_ZMM=1); <MACRO> stays 0 ->
#                 build_variants lp_v1 must give the live lock trial_w6 4181A589 byte for byte;
#   <tree>_gate : the same six + <MACRO> 1 (the port's options, default 0) -> the gate exe. Flipped in the source (not
#                 -D) so QA's kit can rebuild the gate exe from this tree as it is.
# Every flip must hit exactly one '#define NAME 0' line and read back; no CR bytes in either copy.
set -u
[ $# -eq 3 ] || { echo "usage: port_controls.sh <src folder> <tree> <MACRO>"; exit 2; }
S="$1"; T="$2"; M="$3"
[ -d "$S/$T" ] || { echo "port_controls: no $S/$T"; exit 2; }
SIX="FORGE_SPD_TT_NOTLS=1 FORGE_SPD_NO_ZERO_MOVELISTS=2 FORGE_SEARCH_SPEED2=1 FORGE_SPD_PREFETCH_EARLY=1 FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1"

flip() {   # <tree> <NAME=value>
  local t="$1" n="${2%%=*}" v="${2#*=}" lines files f
  lines=$(grep -rhE "^#define $n 0$" "$t/include" "$t/src" | wc -l)
  files=$(grep -rlE "^#define $n 0$" "$t/include" "$t/src" | wc -l)
  [ "$lines" = 1 ] && [ "$files" = 1 ] || { echo "port_controls: '#define $n 0' found $lines times in $t"; return 1; }
  f=$(grep -rlE "^#define $n 0$" "$t/include" "$t/src")
  sed -i "s/^#define $n 0\$/#define $n $v/" "$f"
  [ "$(grep -cE "^#define $n $v$" "$f")" = 1 ] || { echo "port_controls: flip of $n failed in $f"; return 1; }
  echo "  $(basename "$t"): $n 0 -> $v (${f#"$t"/})"
}

for t in "${T}_id" "${T}_gate"; do
  [ -e "$S/$t" ] && { echo "port_controls: $S/$t exists (never overwritten)"; exit 2; }
  cp -r "$S/$T" "$S/$t" && chmod -R u+w "$S/$t" || exit 1
  for kv in $SIX; do flip "$S/$t" "$kv" || exit 1; done
done
flip "$S/${T}_gate" "$M=1" || exit 1
[ "$(grep -rhE "^#define $M 0$" "$S/${T}_id/include" "$S/${T}_id/src" | wc -l)" = 1 ] || { echo "port_controls: ${T}_id must keep $M 0"; exit 1; }
if grep -rlI $'\r' "$S/${T}_id" "$S/${T}_gate" | grep -q .; then echo "port_controls: CR bytes in a control copy"; exit 1; fi
echo "$T -> ${T}_id:";        diff -r "$S/$T" "$S/${T}_id" | grep -E '^[<>]'
echo "${T}_id -> ${T}_gate:"; diff -r "$S/${T}_id" "$S/${T}_gate" | grep -E '^[<>]'
echo "port_controls: OK"

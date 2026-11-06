#!/usr/bin/env bash
# snc_controls.sh - the two build copies of the SingularNonCut tree (own code, 2026-11-06).
# usage: bash opus_singular_noncut/tools/snc_controls.sh
# Input D:/opus_singular_noncut/src/snc = trial_w6 source + singular_noncut_after_w6.patch, every switch at its source
# default 0. Output (refused if a target exists):
#   snc_id   : the six trial_w6 defaults flipped exactly as hunt_identity.sh / speed_pack flip them (TT_NOTLS=1,
#              NO_ZERO_MOVELISTS=2, SEARCH_SPEED2=1, PREFETCH_EARLY=1, SLIDER_PEXT=1, NNUE_ZMM=1); FORGE_SINGULAR_NONCUT
#              stays 0 -> build_variants lp_v1 must give the live lock trial_w6 4181A589 byte for byte;
#   snc_gate : the same six + FORGE_SINGULAR_NONCUT 1 (option SingularNonCut, default 0) -> the gate exe. Flipped in the
#              source (not -D) so QA's kit can rebuild the gate exe from this tree as it is.
# Every flip must hit exactly one '#define NAME 0' line and read back; no CR bytes in either copy.
set -u
S=/d/opus_singular_noncut/src
[ -d "$S/snc" ] || { echo "snc_controls: no $S/snc"; exit 2; }
SIX="FORGE_SPD_TT_NOTLS=1 FORGE_SPD_NO_ZERO_MOVELISTS=2 FORGE_SEARCH_SPEED2=1 FORGE_SPD_PREFETCH_EARLY=1 FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1"

flip() {   # <tree> <NAME=value>
  local t="$1" n="${2%%=*}" v="${2#*=}" lines files f
  lines=$(grep -rhE "^#define $n 0$" "$t/include" "$t/src" | wc -l)
  files=$(grep -rlE "^#define $n 0$" "$t/include" "$t/src" | wc -l)
  [ "$lines" = 1 ] && [ "$files" = 1 ] || { echo "snc_controls: '#define $n 0' found $lines times in $t"; return 1; }
  f=$(grep -rlE "^#define $n 0$" "$t/include" "$t/src")
  sed -i "s/^#define $n 0\$/#define $n $v/" "$f"
  [ "$(grep -cE "^#define $n $v$" "$f")" = 1 ] || { echo "snc_controls: flip of $n failed in $f"; return 1; }
  echo "  $(basename "$t"): $n 0 -> $v (${f#"$t"/})"
}

for t in snc_id snc_gate; do
  [ -e "$S/$t" ] && { echo "snc_controls: $S/$t exists (never overwritten)"; exit 2; }
  cp -r "$S/snc" "$S/$t" && chmod -R u+w "$S/$t" || exit 1
  for kv in $SIX; do flip "$S/$t" "$kv" || exit 1; done
done
flip "$S/snc_gate" FORGE_SINGULAR_NONCUT=1 || exit 1
[ "$(grep -cE '^#define FORGE_SINGULAR_NONCUT 0$' "$S/snc_id/include/forge/search.hpp")" = 1 ] || { echo "snc_controls: snc_id must keep FORGE_SINGULAR_NONCUT 0"; exit 1; }
if grep -rlI $'\r' "$S/snc_id" "$S/snc_gate" | grep -q .; then echo "snc_controls: CR bytes in a control copy"; exit 1; fi
echo "snc -> snc_id:";      diff -r "$S/snc" "$S/snc_id" | grep -E '^[<>]'
echo "snc_id -> snc_gate:"; diff -r "$S/snc_id" "$S/snc_gate" | grep -E '^[<>]'
echo "snc_controls: OK"

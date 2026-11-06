#!/usr/bin/env bash
# hunt_identity.sh - the two identity builds of a hunt tree (speed hunt vs trial_w6, 2026-11-05, own code).
# usage: bash opus_speed/tools/hunt_identity.sh <tree name under F:/ospd/src> [both|sw0|six]
#  (a) sw0: the tree as it is (every switch at its source default 0) -> lp_v1 must be the old lock FD3A5190 byte for byte;
#  (b) six: a copy C:/ospd_hunt/ctl/<tree>_six with ONLY the six trial_w6 defaults flipped, line for line as speed_pack
#      flips them (TT_NOTLS=1, NO_ZERO_MOVELISTS=2, SEARCH_SPEED2=1, PREFETCH_EARLY=1, SLIDER_PEXT=1, NNUE_ZMM=1) ->
#      lp_v1 must be the live lock trial_w6 4181A589 byte for byte (the new switch at 0 adds nothing on top of trial_w6).
# Builds: build_variants.ps1 -Variant lp_v1 -Work C:\ospd_hunt\builds (it pins itself to CPUs 0-1 Idle and checks the
# quick pins). Exit 0 = every requested identity holds, 1 = an identity differs or a build failed, 2 = usage.
set -u
T="${1:-}"; WHAT="${2:-both}"
[ -n "$T" ] || { echo "usage: hunt_identity.sh <tree> [both|sw0|six]"; exit 2; }
SRC="/f/ospd/src/$T"
[ -d "$SRC" ] || { echo "hunt_identity: no tree $SRC"; exit 2; }
OLD_LOCK="/c/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe"
LIVE_LOCK="/c/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_trial_w6.exe"
WANT_SW0=$(sha256sum "$OLD_LOCK" | cut -c1-64)
WANT_SIX=$(sha256sum "$LIVE_LOCK" | cut -c1-64)
[ "${WANT_SW0:0:8}" = fd3a5190 ] || { echo "hunt_identity: old lock exe is not FD3A5190 ($WANT_SW0)"; exit 1; }
[ "${WANT_SIX:0:8}" = 4181a589 ] || { echo "hunt_identity: live lock exe is not 4181A589 ($WANT_SIX)"; exit 1; }
BV='F:\ospd\wt\opus_speed\tools\build_variants.ps1'
rc=0

build() {   # <src dir (Windows form)> <tag> <wanted sha256> <label>
  local src="$1" tag="$2" want="$3" label="$4"
  local work="/c/ospd_hunt/builds/${tag}_lp_v1"
  [ -e "$work" ] && { echo "hunt_identity: $work exists (use a new tree name)"; return 1; }
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$BV" -SrcDir "$src" -Tag "$tag" -Variant lp_v1 \
    -Work 'C:\ospd_hunt\builds' > "/c/ospd_hunt/logs/identity_${tag}.out" 2>&1
  local brc=$?
  local exe="$work/src_copy/forge_lp_v1.exe"
  if [ $brc -ne 0 ] || [ ! -f "$exe" ]; then
    echo "IDENTITY $label: BUILD FAILED (rc $brc, log /c/ospd_hunt/logs/identity_${tag}.out)"; return 1
  fi
  local got; got=$(sha256sum "$exe" | cut -c1-64)
  if [ "$got" = "$want" ]; then echo "IDENTITY $label: OK sha256 $got ($exe)"; return 0; fi
  echo "IDENTITY $label: DIFFERS sha256 $got, want $want ($exe)"; return 1
}

if [ "$WHAT" = both ] || [ "$WHAT" = sw0 ]; then
  build "F:\\ospd\\src\\$T" "${T}_sw0" "$WANT_SW0" "all switches 0 = FD3A5190" || rc=1
fi
if [ "$WHAT" = both ] || [ "$WHAT" = six ]; then
  CTL="/c/ospd_hunt/ctl/${T}_six"
  [ -e "$CTL" ] && { echo "hunt_identity: $CTL exists"; exit 2; }
  cp -r "$SRC" "$CTL" && chmod -R u+w "$CTL" || exit 1
  for kv in FORGE_SPD_TT_NOTLS=1 FORGE_SPD_NO_ZERO_MOVELISTS=2 FORGE_SEARCH_SPEED2=1 FORGE_SPD_PREFETCH_EARLY=1 \
            FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1; do
    n="${kv%%=*}"; v="${kv#*=}"
    hits=$(grep -rlE "^#define $n 0$" "$CTL/include" "$CTL/src" | wc -l)
    lines=$(grep -rhE "^#define $n 0$" "$CTL/include" "$CTL/src" | wc -l)
    [ "$hits" = 1 ] && [ "$lines" = 1 ] || { echo "hunt_identity: '#define $n 0' found $lines times"; exit 1; }
    f=$(grep -rlE "^#define $n 0$" "$CTL/include" "$CTL/src")
    sed -i "s/^#define $n 0\$/#define $n $v/" "$f"
    grep -qE "^#define $n $v$" "$f" || { echo "hunt_identity: flip of $n failed"; exit 1; }
  done
  grep -rlE $'\r' "$CTL/include" "$CTL/src" | grep -q . && { echo "hunt_identity: CR bytes in the control copy"; exit 1; }
  build "C:\\ospd_hunt\\ctl\\${T}_six" "${T}_six" "$WANT_SIX" "six ON + new OFF = 4181A589" || rc=1
fi
exit $rc

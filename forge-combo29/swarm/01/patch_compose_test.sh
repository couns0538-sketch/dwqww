#!/usr/bin/env bash
# swarm seat 01: does my one-line patch compose with seat 12's and seat 27's patches?
#
# Both other patches touch src/search.cpp:
#   mine : --- a/forge-combo29/src/search.cpp   (needs -p2 from a cwd that HAS src/, i.e. from forge-combo29/)
#   seat12: --- a/forge-combo29/src/search.cpp  (same shape)
#   seat27: --- a/src/search.cpp                (needs -p1 from forge-combo29/)
# So every run below does its applies from inside the forge-combo29 directory, which is where the
# patches' path prefixes resolve. Each level is also tried the other way so the table says what is true
# rather than what I assumed.
set -u
BASE=/agent/repos/base/forge-combo29
MINE=/agent/repos/dwqww/forge-combo29/swarm/01/job2/fifty_move_mate.patch.txt
S12=/tmp/s12.patch.txt
S27=/tmp/s27.patch.txt
OUT=/agent/repos/dwqww/forge-combo29/swarm/01/patch_compose.txt

apply_one() {  # $1 = patch file, $2 = level ; cwd must already be forge-combo29/
  local pf="$1" level="$2"
  if patch -p"$level" --fuzz=0 --no-backup-if-mismatch < "$pf" > /tmp/patchout.txt 2>&1; then
    echo "CLEAN"
  else
    echo "FAILED"
  fi
}

run_combo() {
  local label="$1"; shift
  local dir=/tmp/compose_$label
  rm -rf "$dir"; mkdir -p "$dir"
  cp -r "$BASE" "$dir/forge-combo29"
  cd "$dir/forge-combo29" || return
  echo "=== $label   (cwd: forge-combo29/)"
  local ok=0
  for step in "$@"; do
    local level="${step%%:*}"
    local pf="${step#*:}"
    local name; name=$(basename "$pf")
    local res; res=$(apply_one "$pf" "$level")
    echo "  $name -p$level : $res"
    if [ "$res" = "FAILED" ]; then
      ok=1
      sed 's/^/      /' /tmp/patchout.txt | head -8
      break
    fi
  done
  if [ $ok -eq 0 ]; then echo "  result: ALL STEPS CLEAN"; else echo "  result: A STEP FAILED"; fi
  echo
}

{
echo "patch-composition test — every run is a fresh copy of 6b98f217 in /tmp, applies done from forge-combo29/"
echo "date -u: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "mine  : $(sha256sum "$MINE" | cut -c1-16)  $(basename "$MINE")"
echo "seat12: $(sha256sum "$S12"  | cut -c1-16)  $(basename "$S12")"
echo "seat27: $(sha256sum "$S27"  | cut -c1-16)  $(basename "$S27")"
echo "levels: mine and seat12 use a/forge-combo29/src/search.cpp -> -p2 ; seat27 uses a/src/search.cpp -> -p1"
echo
run_combo "mine_only"     "2:$MINE"
run_combo "s12_only"      "2:$S12"
run_combo "s27_only"      "1:$S27"
run_combo "mine_then_s27" "2:$MINE" "1:$S27"
run_combo "s12_then_s27"  "2:$S12"  "1:$S27"
run_combo "s27_then_mine" "1:$S27"  "2:$MINE"
run_combo "s27_then_s12"  "1:$S27"  "2:$S12"
run_combo "mine_then_s12" "2:$MINE" "2:$S12"
run_combo "s12_then_mine" "2:$S12"  "2:$MINE"
} 2>&1 | tee "$OUT"

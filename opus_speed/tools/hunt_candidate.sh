#!/usr/bin/env bash
# hunt_candidate.sh - CPU-side steps of one hunt idea (speed hunt vs trial_w6, 2026-11-05, own code).
# usage: bash opus_speed/tools/hunt_candidate.sh <tree under F:/ospd/src> <NEW_SWITCH>=<value> ["<note>"]
# 1. hunt_identity.sh <tree> both: all switches 0 = FD3A5190 and six ON + new OFF = 4181A589 (byte for byte);
# 2. only if both hold: speed_pack.ps1 -Quick -SkipAbba with the six trial_w6 values + the new switch (pc1 = pc2, bitexact
#    L1-L4 vs the live lock trial_w6: bench net on + net off, perft, 2,000 FENs, sanitizers). No timing here: the ABBA
#    runs afterwards, alone, into C:\ospd_hunt\abba (abba.ps1 -Out).
# Exit: 0 BIT-EXACT pack, 3 not bit-exact / not reproducible (search-changing), 1 identity or other failure, 2 usage.
set -u
T="${1:-}"; NEW="${2:-}"; NOTE="${3:-hunt idea $T on top of trial_w6}"
[ -n "$T" ] && [ -n "$NEW" ] || { echo "usage: hunt_candidate.sh <tree> <SWITCH>=<value> [note]"; exit 2; }
SIX='FORGE_SPD_TT_NOTLS=1,FORGE_SPD_NO_ZERO_MOVELISTS=2,FORGE_SEARCH_SPEED2=1,FORGE_SPD_PREFETCH_EARLY=1,FORGE_SPD_SLIDER_PEXT=1,FORGE_SPD_NNUE_ZMM=1'
echo "hunt_candidate $T $NEW start $(date '+%F %T')"
bash /f/ospd/wt/opus_speed/tools/hunt_identity.sh "$T" both; irc=$?
echo "hunt_candidate identity rc $irc $(date '+%T')"
[ $irc -eq 0 ] || { echo "hunt_candidate: identity failed - no pack"; exit 1; }
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'F:\ospd\wt\opus_speed\tools\speed_pack.ps1' \
  -SrcDir "F:\\ospd\\src\\$T" -Name "$T" -Define "$SIX,$NEW" -Quick -SkipAbba -Note "$NOTE"; prc=$?
echo "hunt_candidate speed_pack rc $prc $(date '+%T')"
exit $prc

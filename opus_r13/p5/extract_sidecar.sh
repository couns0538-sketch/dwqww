#!/usr/bin/env bash
# R14 A1: extract Astra's original FEN sidecar (that member only) from the A1 release archive parts; verify; .part -> rename.
set -u
DL=/d/grok-pc-data/r11_nnue/astra_dl
P0=$DL/forge_astra_a1_data_results_20261030.tar.gz.part000000
P1=$DL/forge_astra_a1_data_results_20261030.tar.gz.part000001
OUT=/d/o14a/p5
F=$OUT/forge_filtered.fen
mkdir -p $OUT
if [ -e "$F" ] || [ -e "$F.part" ]; then echo "exists: $F(.part) - refusing"; exit 2; fi
date '+start %F %T'
whole=$(cat "$P0" "$P1" | sha256sum | cut -c1-64)
echo "whole archive sha256 $whole (expected 148803c5a45a5e29...)"
[ "$whole" = 148803c5a45a5e291c18f667b918100ec1fa1a8e08d5a74dfe430651b3f1418f ] || { echo "ARCHIVE SHA256 MISMATCH"; exit 1; }
cat "$P0" "$P1" | tar -xzOf - --occurrence=1 completed/full10m/forge_filtered.fen > "$F.part"
got=$(sha256sum "$F.part" | cut -c1-64); size=$(stat -c %s "$F.part")
echo "member sha256 $got size $size (expected beb3c31d377d4f5f..., 483989105)"
[ "$got" = beb3c31d377d4f5f610c2fa2b877fe434177230197e074ee54a35b59f7d41c97 ] || { echo "MEMBER SHA256 MISMATCH (left as .part)"; exit 1; }
mv "$F.part" "$F" && echo "OK $F lines $(wc -l < "$F")"
date '+end %F %T'

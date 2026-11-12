#!/usr/bin/env bash
# Fetch the Syzygy 3- and 4-piece WDL+DTZ tables (70 files, about 4 MB) for CI from a public
# mirror, politely: one file at a time, a short pause between files, every file md5-checked
# against the mirror's checksum.md5. Files already present with the right md5 are kept, so a
# restored CI cache downloads nothing. Never commit table files.
# Safety (2026-11-12): every line of checksum.md5 must be "<32 hex digits>  <table file name>" with a plain
# table name (letters KQRBNP, one "v", extension .rtbw or .rtbz). Any other line stops the script before a
# single file is fetched, so a damaged or tampered list cannot make it write outside <dest_dir>.
# The default mirror has no valid HTTPS certificate, so the list and the tables travel unauthenticated;
# they are chess data and are never executed. Set SYZYGY_MIRROR to an https mirror of the same layout if
# one is available.
# usage: ci_fetch_tables.sh <dest_dir>
set -euo pipefail
DEST=$1
MIRROR=${SYZYGY_MIRROR:-http://tablebase.sesse.net/syzygy/3-4-5}
mkdir -p "$DEST"
if [ ! -s "$DEST/checksum.md5" ]; then
  curl -sSf -m 60 --retry 3 "$MIRROR/checksum.md5" -o "$DEST/checksum.md5"
fi
bad=$(awk '!(NF == 2 && length($1) == 32 && $1 !~ /[^0-9a-f]/ && $2 ~ /^[KQRBNP]+v[KQRBNP]+\.rtb[wz]$/)' "$DEST/checksum.md5" | wc -l)
if [ "$bad" -ne 0 ]; then
  echo "FAIL: $DEST/checksum.md5 has $bad line(s) that are not '<md5>  <table file name>'; nothing was downloaded"
  exit 1
fi
# 3-4 piece tables: the name without extension has at most 5 characters (e.g. "KRPvK").
awk 'length($2) <= 10 {print $1, $2}' "$DEST/checksum.md5" > "$DEST/wanted.md5"
fetched=0
while read -r sum name; do
  if [ -f "$DEST/$name" ] && [ "$(md5sum "$DEST/$name" | cut -d' ' -f1)" = "$sum" ]; then continue; fi
  curl -sSf -m 120 --retry 3 "$MIRROR/$name" -o "$DEST/$name.part"
  if [ "$(md5sum "$DEST/$name.part" | cut -d' ' -f1)" != "$sum" ]; then echo "md5 mismatch: $name"; exit 1; fi
  mv "$DEST/$name.part" "$DEST/$name"
  fetched=$((fetched + 1))
  sleep 0.3
done < "$DEST/wanted.md5"
echo "tables: $(ls "$DEST" | grep -c 'rtb[wz]$') present, $fetched downloaded"

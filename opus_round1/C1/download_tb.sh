#!/usr/bin/env bash
# Polite sequential download of the Syzygy 3-4-5 piece WDL+DTZ set from a public mirror.
# One request at a time, short pause between files, md5 check against the mirror's checksum.md5,
# resumable (verified files are skipped). Destination is outside every git repository.
# Safety (2026-11-12): every line of <checksum.md5> must be "<32 hex digits>  <table file name>" with a plain
# table name (letters KQRBNP, one "v", extension .rtbw or .rtbz). Any other line stops the script before a
# single file is fetched, so a damaged or tampered list cannot make it write outside <dest_dir>.
# The default mirror has no valid HTTPS certificate, so the tables travel unauthenticated; they are chess
# data and are never executed. Set MIRROR to an https mirror of the same layout if one is available.
# usage: download_tb.sh <dest_dir> <checksum.md5>   (checksum.md5: curl http://tablebase.sesse.net/syzygy/3-4-5/checksum.md5)
set -u
DEST=$1
SUMS=$2
MIRROR=${MIRROR:-http://tablebase.sesse.net/syzygy/3-4-5}
if [ ! -r "$SUMS" ]; then echo "FAIL: cannot read $SUMS"; exit 1; fi
bad=$(awk '!(NF == 2 && length($1) == 32 && $1 !~ /[^0-9a-f]/ && $2 ~ /^[KQRBNP]+v[KQRBNP]+\.rtb[wz]$/)' "$SUMS" | wc -l)
if [ "$bad" -ne 0 ]; then
  echo "FAIL: $SUMS has $bad line(s) that are not '<md5>  <table file name>'; nothing was downloaded"
  exit 1
fi
mkdir -p "$DEST"
# order: 3-man, 4-man, 5-man (by name length = piece count + 2), WDL before DTZ within a size
awk '{print $2}' "$SUMS" | awk '{ n=length($1)-6; t=($1 ~ /rtbw$/)?0:1; print n, t, $1 }' | sort -k1,1n -k2,2n -k3,3 | awk '{print $3}' > "$DEST/.order"
total=$(wc -l < "$DEST/.order")
i=0; ok=0; fail=0
while read -r f; do
  i=$((i+1))
  want=$(grep "  $f\$" "$SUMS" | awk '{print $1}')
  if [ -f "$DEST/$f" ] && [ "$(md5sum "$DEST/$f" | awk '{print $1}')" = "$want" ]; then ok=$((ok+1)); continue; fi
  for attempt in 1 2 3; do
    curl -sS -f -m 900 --retry 2 -o "$DEST/$f.part" "$MIRROR/$f" && \
      [ "$(md5sum "$DEST/$f.part" | awk '{print $1}')" = "$want" ] && mv "$DEST/$f.part" "$DEST/$f" && break
    echo "retry $attempt for $f"; sleep 5
  done
  if [ -f "$DEST/$f" ]; then ok=$((ok+1)); echo "[$i/$total] $f ok"; else fail=$((fail+1)); echo "[$i/$total] $f FAILED"; fi
  sleep 0.5
done < "$DEST/.order"
echo "done: ok=$ok fail=$fail total=$total"

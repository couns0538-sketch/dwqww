#!/usr/bin/env bash
# Polite sequential download of the Syzygy 3-4-5 piece WDL+DTZ set from a public mirror.
# One request at a time, short pause between files, md5 check against the mirror's checksum.md5,
# resumable (verified files are skipped). Destination is outside every git repository.
# usage: download_tb.sh <dest_dir> <checksum.md5>   (checksum.md5: curl http://tablebase.sesse.net/syzygy/3-4-5/checksum.md5)
set -u
DEST=$1
SUMS=$2
MIRROR=${MIRROR:-http://tablebase.sesse.net/syzygy/3-4-5}
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

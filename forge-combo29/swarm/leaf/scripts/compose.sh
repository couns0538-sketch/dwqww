#!/bin/sh
# compose.sh REPO_ROOT OUTFILE — apply the two SHIPPED patches and this seat's
# patch, in both orders, and prove the result is byte-identical.
#
# The -p trap is real: seat 12's hunks name a/forge-combo29/src (so -p2 from
# inside forge-combo29/), seat 27's and this seat's name a/src (so -p1).
set -eu
root="$1"; out="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
seat12="$root/forge-combo29/swarm/leaf/patches/upstream/seat12_two_doors_mate.patch.txt"
seat27="$root/forge-combo29/swarm/leaf/patches/upstream/seat27_drawn_root_reporting.patch.txt"
leaf_search="$root/forge-combo29/swarm/leaf/patches/leaf_clock100_mate.patch.txt"
leaf_hpp="$root/forge-combo29/swarm/leaf/patches/leaf_clock100_mate_hpp.patch.txt"
: > "$out"
for order in "12 27" "27 12"; do
  w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
  cp -r "$root/forge-combo29/src" "$root/forge-combo29/include" "$w/"
  ( cd "$w"
    for p in $order; do
      if [ "$p" = 12 ]; then
        patch -p2 --fuzz=0 --no-backup-if-mismatch < "$seat12" >/dev/null
      else
        patch -p1 --fuzz=0 --no-backup-if-mismatch < "$seat27" >/dev/null
      fi
    done
    patch -p1 --fuzz=0 --no-backup-if-mismatch < "$leaf_search" >/dev/null
    patch -p1 --fuzz=0 --no-backup-if-mismatch < "$leaf_hpp" >/dev/null
    echo "$order $(sha256sum src/search.cpp | cut -d' ' -f1) $(sha256sum include/forge/search.hpp | cut -d' ' -f1)" >> "$out"
  )
done
cat "$out"
a=$(head -1 "$out" | awk '{print $3}'); b=$(tail -1 "$out" | awk '{print $3}')
[ "$a" = "$b" ] || { echo "FAIL: the two orders disagree"; exit 1; }
echo "PASS: both orders compose to $a"
echo "SHIPPED-ONLY baseline (seat 12 + seat 27, no leaf patch) must be 24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671"

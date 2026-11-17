#!/usr/bin/env bash
# compose.sh ORDER: builds a fresh copy of forge-combo29 from base commit and applies both patches.
set -u
ORDER="${1:?order mate|report}"
W="$HOME/comp/$ORDER"
rm -rf "$W"; mkdir -p "$W"
git -C /agent/repos/dwqww archive 6b98f217 forge-combo29 | tar -x -C "$W" || { echo "FAIL archive"; exit 2; }
APP="$W/applied"; mkdir -p "$APP"
cp -a "$W/forge-combo29" "$APP/forge-combo29"
cd "$APP" || exit 2
if [ "$ORDER" = "mate" ]; then
  patch -p1 --no-backup-if-mismatch -i "$HOME/p/two_doors_mate.patch.txt"; echo "EXIT_mate=$?"
  ( cd forge-combo29 && patch -p1 --no-backup-if-mismatch -i "$HOME/p/drawn_root_reporting.patch.txt"; echo "EXIT_report=$?" )
else
  ( cd forge-combo29 && patch -p1 --no-backup-if-mismatch -i "$HOME/p/drawn_root_reporting.patch.txt"; echo "EXIT_report=$?" )
  patch -p1 --no-backup-if-mismatch -i "$HOME/p/two_doors_mate.patch.txt"; echo "EXIT_mate=$?"
fi
sha256sum forge-combo29/src/search.cpp

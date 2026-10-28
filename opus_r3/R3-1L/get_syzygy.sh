#!/usr/bin/env bash
# R3-1L: downloads the 3-4-5-piece Syzygy tables the self-play configs load (145 WDL + 145 DTZ, 939 MB; the PC
# engine prints "Syzygy: 145 WDL and 145 DTZ tables") and checks every file against the sha256 list taken from
# the PC's copy (D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345), so the runner uses the same bytes.
# Source: the lichess mirror, fallback tablebase.sesse.net.
# usage: get_syzygy.sh <dest dir> <sha256 list>
set -euo pipefail
DEST=$1
LIST=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
mkdir -p "$DEST"
cd "$DEST"
export WDL=https://tablebase.lichess.ovh/tables/standard/3-4-5-wdl
export DTZ=https://tablebase.lichess.ovh/tables/standard/3-4-5-dtz
export ALT=http://tablebase.sesse.net/syzygy/3-4-5
fetch() {
  local f=$1 u
  case $f in
    *.rtbw) u=$WDL/$f ;;
    *.rtbz) u=$DTZ/$f ;;
    *) echo "unexpected table name $f"; return 1 ;;
  esac
  curl -sfL --retry 4 --retry-delay 3 -o "$f" "$u" || curl -sfL --retry 4 --retry-delay 3 -o "$f" "$ALT/$f"
}
export -f fetch
sed -E 's/^[0-9a-f]{64} [ *]//' "$LIST" | xargs -P 8 -I{} bash -c 'fetch "$1"' _ {}
sha256sum -c --quiet "$LIST"
echo "syzygy: $(ls "$DEST" | wc -l) files, $(du -sh "$DEST" | cut -f1), all sha256 match $(basename "$LIST")"

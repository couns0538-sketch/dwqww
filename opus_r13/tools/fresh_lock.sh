#!/usr/bin/env bash
# fresh_lock.sh <dir> - fresh copy of the lock source (git d4f4312 = src_al1s198_clean, byte-identical, 20 files)
# as LF files, plus a scratch git repo with the lock as its base commit, so `git diff` gives a/ b/ patches.
# Refuses an existing <dir>. Clean build copies for the kit: export_src.sh <dir> <out>.
set -euo pipefail
dir="$1"; repo=/d/grok-pc-data/dwqww; lock=d4f43124dde1d1e37de90e18930e374f32ea7ffa
[ -e "$dir" ] && { echo "refusing: $dir exists" >&2; exit 2; }
mkdir -p "$dir"
git -C "$repo" -c core.autocrlf=false archive "$lock" src include | tar -x -C "$dir"
cd "$dir"
git init -q && git config core.autocrlf false && git config user.name o13 && git config user.email o13@local
git add -A && git commit -q -m "lock d4f4312 (AL1 s198 source)"
n=$(git ls-files | wc -l); echo "fresh lock copy $dir: $n files, base $(git rev-parse --short HEAD)"
[ "$n" = 20 ] || { echo "expected 20 files" >&2; exit 3; }

#!/usr/bin/env bash
# make_stack.sh - build a stacked source tree from per-change patches (speed job, own code).
# usage: bash opus_speed/tools/make_stack.sh <stack name> <patch> [<patch> ...]
# Copies the exact lock source F:/ospd/src/lock to F:/ospd/src/<stack name> (refused if it exists), applies each patch
# with GNU patch -p1 -F0 (dry run first, no fuzz, no offsets tolerated silently: any reject stops), checks that every
# FORGE_SPD_* / FORGE_SEARCH_* switch default line is still '#define <SWITCH> 0' exactly once, and writes the stacked
# patch opus_speed/patches/<stack name>.patch (diff -ruN against the lock, relative 'lock/' paths, -p1). Patches are
# expected in the 'lock/... -> <tree>/...' form (diff -ruN lock <tree> run in F:/ospd/src).
set -u
NAME="$1"; shift
SRC=/f/ospd/src
DST="$SRC/$NAME"
PATCHDIR=/f/ospd/wt/opus_speed/patches
[ -e "$DST" ] && { echo "make_stack: $DST exists"; exit 2; }
[ $# -ge 1 ] || { echo "make_stack: no patches"; exit 2; }
cp -r "$SRC/lock" "$DST" && chmod -R u+w "$DST" || exit 2
cd "$DST" || exit 2
for p in "$@"; do
  [ -f "$p" ] || p="$PATCHDIR/$p"
  [ -f "$p" ] || { echo "make_stack: missing patch $p"; exit 2; }
  if ! patch -p1 -F0 --no-backup-if-mismatch --dry-run < "$p" > /f/ospd/tmp/make_stack_dry.txt 2>&1; then
    echo "make_stack: $(basename "$p") does not apply cleanly on top of the previous ones:"; cat /f/ospd/tmp/make_stack_dry.txt; exit 1
  fi
  patch -p1 -F0 --no-backup-if-mismatch < "$p" > /f/ospd/tmp/make_stack_apply.txt 2>&1 || { cat /f/ospd/tmp/make_stack_apply.txt; echo "make_stack: apply failed for $p"; exit 1; }
  grep -i -E "offset|fuzz" /f/ospd/tmp/make_stack_apply.txt | sed "s/^/  /"
  echo "applied $(basename "$p") (md5 $(md5sum < "$p" | cut -c1-8))"
done
find . -name '*.rej' | grep -q . && { echo "make_stack: .rej files left - check"; exit 1; }
bad=0
for sw in $(grep -rhoE '^#ifndef (FORGE_SPD_[A-Z0-9_]+|FORGE_SEARCH_[A-Z0-9_]+)' include src | awk '{print $2}' | sort -u); do
  # strip CR first: '\r' is not an escape in GNU ERE (review LOW 9)
  n=$(cat $(grep -rl "$sw" include src) | tr -d '\r' | grep -cE "^#define $sw 0$")
  if [ "$n" -ne 1 ]; then echo "make_stack: switch $sw default line count $n (want 1)"; bad=1; else echo "switch $sw default 0"; fi
done
[ $bad -eq 0 ] || exit 1
[ -e "$PATCHDIR/$NAME.patch" ] && { echo "make_stack: $PATCHDIR/$NAME.patch exists (never overwritten)"; exit 2; }
cd "$SRC" && { diff -ruN lock "$NAME" > "$PATCHDIR/$NAME.patch"; rc=$?; [ $rc -le 1 ] || { echo "make_stack: diff failed (exit $rc)"; exit 1; }; }
echo "make_stack: $DST ready; stacked patch $PATCHDIR/$NAME.patch ($(grep -c '^+' "$PATCHDIR/$NAME.patch") added lines, $(grep -c '^-[^-]' "$PATCHDIR/$NAME.patch") removed lines)"

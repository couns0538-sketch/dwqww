#!/usr/bin/env bash
# Same runner for the clean sanitizer search and the deliberate-bug search.
set -u
EXE="$1"
FENS="$2"
DEPTH="$3"
OUT="$4"
LIMIT="$5"
export ASAN_OPTIONS="${ASAN_OPTIONS:-detect_leaks=0:halt_on_error=1:abort_on_error=1}"
export UBSAN_OPTIONS="${UBSAN_OPTIONS:-halt_on_error=1:print_stacktrace=1}"
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/harness_depth.py" --exe "$EXE" --fens "$FENS" --depth "$DEPTH" --out "$OUT" --switch true --limit "$LIMIT"

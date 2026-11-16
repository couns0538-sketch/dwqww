#!/usr/bin/env bash
# pos_echo.sh — does the engine ever print a stdout line starting with "position"?
# Reads a normal sequence from stdin-file arg 1, prints every stdout line that starts with "position".
set -u
EXE="${1:?exe}"
IN="${2:?stdin file}"
echo "exe=$EXE sha256=$(sha256sum "$EXE" | cut -d' ' -f1)"
echo "--- lines of stdout starting with 'position':"
timeout 60 "$EXE" < "$IN" 2>/dev/null | grep -c '^position' | sed 's/^/count=/'
echo "--- every distinct stdout line prefix (first word), to see what the engine does print:"
timeout 60 "$EXE" < "$IN" 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn

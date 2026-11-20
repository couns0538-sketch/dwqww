#!/usr/bin/env bash
# One fresh engine process, no setoption. Usage: honesty_one.sh EXE LABEL COMMAND...
set -u
EXE=$1
LABEL=$2
shift 2
OUTDIR=$(dirname "$0")
SHA=$(sha256sum "$EXE" | awk '{print $1}')
IDNAME=$(printf 'uci\nquit\n' | "$EXE" | awk -F'\n' '/^id name /{print; exit}')
RAW="$OUTDIR/${LABEL}.txt"
META="$OUTDIR/${LABEL}.meta"
printf '%s\nquit\n' "$*" | "$EXE" > "$RAW"
{
  echo "exe=$EXE"
  echo "sha256=$SHA"
  echo "id_name=$IDNAME"
  echo "option_lines_sent="
  echo "command=$*"
} > "$META"
echo "WROTE $RAW"
tail -n 3 "$RAW"

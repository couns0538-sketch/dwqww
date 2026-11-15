#!/bin/bash
# Run one fastchess match under a wall-clock limit.
# usage: run_match.sh <name> <limit_seconds> <fastchess args...>
# TERM at the limit: fastchess stops gracefully; in this version (1.8.3-alpha)
# unfinished games are marked abandoned in output/PGN. KILL 15 s later only as
# a backstop. Records argv and start/end stamps inside the match directory.
name=$1
limit=$2
shift 2
dir=/tmp/matches/$name
mkdir -p "$dir"
cd "$dir" || exit 1
printf '%s\n' "$@" > command.txt
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee stamps.txt
timeout -s TERM -k 15 "$limit" /tmp/fastchess/fastchess "$@" > stdout.log 2>&1
code=$?
echo "end $(date -u +%Y-%m-%dT%H:%M:%SZ) exit=$code" | tee -a stamps.txt
exit $code

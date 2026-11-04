#!/usr/bin/env bash
# idle.sh <hex cpu mask> <program> [args ...] - Opus 30-h job: run a program at Idle on a CPU mask. Pins THIS bash
# process first (pin_pid.py on its Windows pid, fail closed: exit 78), so the program and everything it starts inherit
# Idle and the mask. Also sourced by the job's bash scripts: `. tools/idle.sh` defines o30_pin_self <mask> only.
# O30_MASK (hex, optional) overrides the mask a script asks for - e.g. O30_MASK=0x1 keeps a script off CPU 1 while
# a timing-sensitive match runs there.
o30_pin_self() {
  local mask="${O30_MASK:-$1}" wp here
  here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
  wp=$(cat /proc/$$/winpid 2>/dev/null)
  [ -n "$wp" ] || { echo "o30_pin_self: no Windows pid for bash $$" >&2; return 1; }
  C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B "$(cygpath -w "$here/pin_pid.py")" "$wp" "$mask" >&2
}
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  [ $# -ge 2 ] || { echo "usage: idle.sh <hex cpu mask> <program> [args ...]" >&2; exit 2; }
  mask="$1"; shift
  o30_pin_self "$mask" || { echo "idle.sh: cannot pin (fail closed)" >&2; exit 78; }
  "$@"
fi

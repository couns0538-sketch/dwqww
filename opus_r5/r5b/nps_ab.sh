#!/usr/bin/env bash
# MSYS2 / Git Bash wrapper of nps_ab.py (the driver pins itself to one core and runs at BelowNormal by itself).
# usage: bash opus_r5/r5b/nps_ab.sh --a OFF.exe --b X.exe [Y.exe ...] [--names x,y] --aa [--depths 16,20] [--pairs 12]
#        [--core 14] [--pins 16=3024920,20=12389307] [--json out.json]
# PowerShell: & C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe -I -B opus_r5\r5b\nps_ab.py --a ... --b ...
PY=${PY:-C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
exec "$PY" -I -B "$(dirname "$0")/nps_ab.py" "$@"

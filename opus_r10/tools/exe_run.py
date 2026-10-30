"""R10: run a program with its arguments from Python, so run_pinned.py's CPU mask and priority reach it.
usage: python -I -B run_pinned.py --mask 0x0FF0 -- exe_run.py <program.exe> [args...]"""
import subprocess
import sys

sys.exit(subprocess.call(sys.argv[1:]))

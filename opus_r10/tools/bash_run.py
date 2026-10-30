"""R9: run a bash script with Git Bash from Python, so run_pinned.py's CPU mask and priority reach bash and every
process it starts (cmd's `start /affinity` from Git Bash fails on this PC and leaves processes behind).
usage: python -I -B run_pinned.py --mask 0x000F -- bash_run.py <script.sh> [args...]"""
import subprocess
import sys

BASH = r"C:\Program Files\Git\bin\bash.exe"
sys.exit(subprocess.call([BASH] + sys.argv[1:]))

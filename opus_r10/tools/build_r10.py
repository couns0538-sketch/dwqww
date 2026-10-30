"""R9: box-recipe build of a Forge tree (the PC lock recipe, build_pc.sh) under the caller's CPU mask / priority.
usage: python -I -B run_pinned.py --mask 0x000F -- build_r9.py <src_dir> <out.exe> [extra g++ flags...]
Prints the build script's output (sha256, FMA count) and the number of compiler warnings."""
import subprocess
import sys

BUILD = "D:/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh"
BASH = r"C:\Program Files\Git\bin\bash.exe"
src, out, extra = sys.argv[1], sys.argv[2], sys.argv[3:]
p = subprocess.run([BASH, BUILD, src, out] + extra, capture_output=True, text=True)
text = p.stdout + p.stderr
print(text, end="")
print(f"build exit {p.returncode}, warnings {text.lower().count('warning')}")
sys.exit(p.returncode)

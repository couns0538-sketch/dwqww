"""Summarise nnue_pins_check.sh output into MATCH/MISMATCH lines."""
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
out = ["# NNUE v2 ON pins recorded on the branches (trained smoke nets), re-run on a stack exe (" + sys.argv[2] + ")",
       "# 'ERROR NNUE v2' lines in the raw log are the documented transient half-set-request messages (NNUEFile set",
       "# before the matching option); the search then ran with the requested net. Nodes from 'bench <d>', d11/13/16/20."]
for name, got, exp in re.findall(r"^(?:DIFF|OK)\s+(.*?): got \[.*?(\d+ \d+ \d+ \d+)\] expected \[([\d ]+)\]", text, re.S | re.M):
    out.append(("MATCH    " if got == exp else "MISMATCH ") + f"{name}: {got} (branch: {exp})")
open(sys.argv[3], "w", newline="\n").write("\n".join(out) + "\n")
print("\n".join(out))

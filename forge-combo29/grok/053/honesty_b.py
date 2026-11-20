#!/usr/bin/env python3
"""Fresh process per honesty line. No setoption. Writes raw output, meta, HONESTY_B.txt."""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/base/forge-combo29/build-release/forge").resolve()
OUT = Path(__file__).resolve().parent
EXPECTED = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
COMMANDS = {
    "bench11": "bench 11\nuci\nquit\n",
    "bench13": "bench 13\nuci\nquit\n",
    "bench16": "bench 16\nuci\nquit\n",
    "perft5": "go perft 5\nuci\nquit\n",
}

def nodes_of(name: str, text: str) -> int:
    if name.startswith("bench"):
        found = re.findall(r"bench depth \d+ nodes (\d+)", text)
    else:
        found = re.findall(r"^nodes (\d+)\s*$", text, re.M)
    if len(found) != 1:
        raise SystemExit(f"{name}: expected one nodes line, got {found!r}")
    return int(found[0])

def main() -> int:
    sha = hashlib.sha256(EXE.read_bytes()).hexdigest()
    lines = []
    ok = True
    for name, cmd in COMMANDS.items():
        proc = subprocess.run([str(EXE)], input=cmd, text=True, capture_output=True, timeout=180)
        raw = proc.stdout
        if proc.stderr:
            raw += proc.stderr
        (OUT / f"honesty_b_{name}.txt").write_text(raw)
        id_names = re.findall(r"^id name (.+)$", raw, re.M)
        got = nodes_of(name, raw)
        exp = EXPECTED[name]
        status = "OK" if got == exp else "MISS"
        if got != exp:
            ok = False
        lines.append(f"{name} nodes {got} expected {exp} {status}")
        meta = (
            f"exe={EXE}\n"
            f"sha256={sha}\n"
            f"id_name={id_names[-1] if id_names else 'MISSING'}\n"
            f"options_sent=none\n"
            f"command={cmd.strip().splitlines()[0]}\n"
            f"returncode={proc.returncode}\n"
        )
        (OUT / f"honesty_b_{name}.meta").write_text(meta)
        print(lines[-1], flush=True)
    summary = "\n".join(lines) + ("\nPASS\n" if ok else "\nFAIL\n")
    (OUT / "HONESTY_B.txt").write_text(summary)
    print(summary, end="")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())

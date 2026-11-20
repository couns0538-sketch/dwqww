#!/usr/bin/env python3
import hashlib, re, subprocess, sys
from pathlib import Path
EXE = Path("/agent/repos/work/forge-combo29/build-release/forge").resolve()
OUT = Path(__file__).resolve().parent
EXPECTED = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
COMMANDS = {
    "bench11": "bench 11\nuci\nquit\n",
    "bench13": "bench 13\nuci\nquit\n",
    "bench16": "bench 16\nuci\nquit\n",
    "perft5": "go perft 5\nuci\nquit\n",
}
def nodes_of(name, text):
    if name.startswith("bench"):
        found = re.findall(r"bench depth \d+ nodes (\d+)", text)
    else:
        found = re.findall(r"^nodes (\d+)\s*$", text, re.M)
    if len(found) != 1:
        raise SystemExit(f"{name}: expected one nodes line, got {found!r}")
    return int(found[0])
def main():
    sha = hashlib.sha256(EXE.read_bytes()).hexdigest()
    lines = []
    ok = True
    for name, cmd in COMMANDS.items():
        proc = subprocess.run([str(EXE)], input=cmd, text=True, capture_output=True, timeout=180)
        raw = proc.stdout + (proc.stderr or "")
        (OUT / f"honesty_p_{name}.txt").write_text(raw)
        id_names = re.findall(r"^id name (.+)$", raw, re.M)
        got = nodes_of(name, raw)
        exp = EXPECTED[name]
        status = "OK" if got == exp else "MISS"
        if got != exp:
            ok = False
        lines.append(f"{name} nodes {got} expected {exp} {status}")
        (OUT / f"honesty_p_{name}.meta").write_text(
            f"exe={EXE}\nsha256={sha}\nid_name={id_names[-1] if id_names else 'MISSING'}\noptions_sent=none\ncommand={cmd.strip().splitlines()[0]}\nreturncode={proc.returncode}\n"
        )
        print(lines[-1], flush=True)
    (OUT / "HONESTY_P.txt").write_text("\n".join(lines) + ("\nPASS\n" if ok else "\nFAIL\n"))
    # options listed by uci
    listed = []
    text = (OUT / "honesty_p_bench11.txt").read_text()
    for needle in ("option name IdeaS38 type check default false",
                   "option name IdeaS38_Divisor type spin default 64 min 1 max 4096",
                   "option name IdeaS38_Clamp type spin default 1 min 0 max 8"):
        listed.append(f"{needle} {'YES' if needle in text else 'NO'}")
    (OUT / "uci_options_p.txt").write_text("\n".join(listed) + "\n")
    print("\n".join(listed))
    return 0 if ok else 1
if __name__ == "__main__":
    sys.exit(main())

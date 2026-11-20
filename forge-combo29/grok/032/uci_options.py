#!/usr/bin/env python3
"""Save the uci option list and check IdeaA1 defaults."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXE = Path("/agent/repos/work/build/forge")
OUT = Path(__file__).resolve().parent
WANT = {
    "IdeaA1": "check default false",
    "IdeaA1_Scale": "spin default 1024 min 2 max 8192",
    "IdeaA1_Clamp": "spin default 2 min 0 max 8",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    proc = subprocess.run(
        [str(EXE)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    text = proc.stdout
    if proc.stderr:
        text += proc.stderr
    (OUT / "uci_options.txt").write_text(text)
    name = "MISSING"
    found = {}
    for line in text.splitlines():
        if line.startswith("id name "):
            name = line[len("id name ") :]
        if line.startswith("option name "):
            for key in WANT:
                prefix = f"option name {key} type "
                if line.startswith(prefix):
                    found[key] = line[len(prefix) :]
    digest = sha256(EXE)
    lines = [
        f"exe={EXE}",
        f"sha256={digest}",
        f"id_name={name}",
        "options=",
        "command=uci",
    ]
    ok = True
    for key, expect in WANT.items():
        got = found.get(key, "MISSING")
        status = "OK" if got == expect else "FAIL"
        if status != "OK":
            ok = False
        lines.append(f"{key} {got} expected {expect} {status}")
    (OUT / "uci_options.meta").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

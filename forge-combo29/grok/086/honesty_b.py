#!/usr/bin/env python3
"""Fresh process per honesty line. No setoption. Writes raw files, metas, HONESTY_B.txt."""
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED = [
    ("bench 11", "HONESTY_B_bench11.txt", 312866),
    ("bench 13", "HONESTY_B_bench13.txt", 862329),
    ("bench 16", "HONESTY_B_bench16.txt", 3024920),
    ("go perft 5", "HONESTY_B_perft5.txt", 4865609),
]


def nodes_of(text: str) -> int | None:
    found = None
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            found = int(parts[parts.index("nodes") + 1])
    return found


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()

    def run(commands: list[str]) -> str:
        proc = subprocess.run(
            [str(exe)],
            input="\n".join(commands) + "\n",
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        if proc.returncode not in (0, None):
            # The engine returns 0 on quit. Anything else is kept in the raw file.
            pass
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        return proc.stdout

    uci_text = run(["uci", "quit"])
    (out_dir / "HONESTY_B_uci.txt").write_text(uci_text)
    id_name = ""
    for line in uci_text.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    (out_dir / "HONESTY_B_uci.meta").write_text(
        f"exe={exe}\nsha256={sha}\nid_name={id_name}\noptions:\n(none)\ncommand=uci\n"
    )

    summary = []
    ok = True
    chunks = []
    for command, raw_name, expected in EXPECTED:
        text = run([command, "quit"])
        (out_dir / raw_name).write_text(text)
        got = nodes_of(text)
        meta_name = raw_name[: -len(".txt")] + ".meta"
        (out_dir / meta_name).write_text(
            "\n".join(
                [
                    f"exe={exe}",
                    f"sha256={sha}",
                    f"id_name={id_name}",
                    "options:",
                    "(none)",
                    f"command={command}",
                    "process=fresh",
                    "setoption=not sent",
                    "",
                ]
            )
        )
        good = got == expected
        ok = ok and good
        line = f"{command} nodes {got} expected {expected} {'OK' if good else 'FAIL'}"
        summary.append(line)
        chunks.append(f"===== {command} =====")
        chunks.append(text.rstrip("\n"))

    chunks.append("===== summary =====")
    chunks.extend(summary)
    chunks.append("ALL_OK" if ok else "FAIL")
    (out_dir / "HONESTY_B.txt").write_text("\n".join(chunks) + "\n")
    print("\n".join(summary))
    print("ALL_OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

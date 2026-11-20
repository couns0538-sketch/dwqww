#!/usr/bin/env python3
"""Honesty check for exe B. One fresh process per line. No setoption."""
import hashlib
import pathlib
import subprocess
import sys

EXE = pathlib.Path("/agent/repos/base/forge-combo29/build-rel/forge")
OUT = pathlib.Path(__file__).resolve().parent
EXPECT = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
COMMANDS = {
    "bench11": "bench 11",
    "bench13": "bench 13",
    "bench16": "bench 16",
    "perft5": "go perft 5",
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def run_fresh(command: str) -> str:
    proc = subprocess.run(
        [str(EXE)],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    text = proc.stdout
    if proc.stderr:
        text += proc.stderr
    if proc.returncode != 0:
        raise SystemExit(f"engine exit {proc.returncode} for {command}\n{text}")
    for bad in ("unknown option", "invalid value", "invalid FEN", "illegal move"):
        if bad in text:
            raise SystemExit(f"STOP {bad}\n{text}")
    return text


def nodes_of(text: str) -> int:
    found = None
    for line in text.splitlines():
        if "nodes " in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "nodes" and i + 1 < len(parts):
                    found = int(parts[i + 1])
    if found is None:
        raise SystemExit(f"no nodes line in:\n{text}")
    return found


def id_name() -> str:
    proc = subprocess.run(
        [str(EXE)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    raise SystemExit("no id name")


def main() -> None:
    if not EXE.is_file():
        raise SystemExit(f"missing exe {EXE}")
    digest = sha256(EXE)
    name = id_name()
    summary = []
    ok = True
    for key, command in COMMANDS.items():
        text = run_fresh(command)
        raw = OUT / f"honesty_b_{key}.txt"
        raw.write_text(text)
        got = nodes_of(text)
        want = EXPECT[key]
        status = "PASS" if got == want else "FAIL"
        if got != want:
            ok = False
        summary.append(f"{command} -> nodes {got} expect {want} {status}")
        meta = OUT / f"honesty_b_{key}.meta"
        meta.write_text(
            f"exe={EXE}\nsha256={digest}\nid_name={name}\n"
            f"option_lines_sent=\ncommand={command}\n"
            f"note=fresh process, no setoption; id name from a separate uci process of this exe\n"
        )
        print(summary[-1])
    report = OUT / "HONESTY_B.txt"
    report.write_text("\n".join(summary) + ("\nALL PASS\n" if ok else "\nALL FAIL\n"))
    print(report.read_text(), end="")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

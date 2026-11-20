#!/usr/bin/env python3
"""Record the uci option list and require IdeaS37 plus IdeaS37_Margin."""
import pathlib
import subprocess
import sys

EXE = pathlib.Path("/agent/repos/work/forge-combo29/build-rel/forge")
OUT = pathlib.Path(__file__).resolve().parent
NEED = {
    "option name IdeaS37 type check default false",
    "option name IdeaS37_Margin type spin default 40 min 0 max 500",
}


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
    (OUT / "uci_p.txt").write_text(text)
    missing = [line for line in NEED if line not in text.splitlines()]
    report = ["exe=" + str(EXE)]
    for line in sorted(NEED):
        report.append(("PASS " if line not in missing else "FAIL ") + line)
    (OUT / "uci_p_options.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

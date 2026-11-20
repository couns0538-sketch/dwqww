#!/usr/bin/env python3
"""Run one measured set with S14, Threads 1, Hash 16, then extra options.

Usage:
  run_measured.py <exe> <positions> <depth> <raw-out> <meta-out> [Name Value]...
"""
import hashlib
import subprocess
import sys
from pathlib import Path

S14 = [
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
    ("Threads", "1"),
    ("Hash", "16"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def id_name(exe: Path) -> str:
    proc = subprocess.run(
        [str(exe)],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        timeout=30,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            return line[len("id name ") :]
    return ""


def main() -> int:
    exe = Path(sys.argv[1]).resolve()
    positions = Path(sys.argv[2]).resolve()
    depth = sys.argv[3]
    raw_out = Path(sys.argv[4]).resolve()
    meta_out = Path(sys.argv[5]).resolve()
    extra = sys.argv[6:]
    if len(extra) % 2 != 0:
        raise SystemExit("extra options must be Name Value pairs")
    options = list(S14) + list(zip(extra[0::2], extra[1::2]))
    here = Path(__file__).resolve().parent
    cmd = [sys.executable, str(here / "search_set.py"), str(exe), str(positions), depth, str(raw_out)]
    for name, value in options:
        cmd.extend(["--option", name, value])
    meta_out.write_text(
        "\n".join(
            [
                f"exe {exe}",
                f"sha256 {sha256(exe)}",
                f"id_name {id_name(exe)}",
                "options",
                *[f"setoption name {name} value {value}" for name, value in options],
                f"depth {depth}",
                f"positions {positions}",
                "",
            ]
        )
    )
    print("meta", meta_out, flush=True)
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())

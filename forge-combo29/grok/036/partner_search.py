#!/usr/bin/env python3
"""Partner review searches. Not a copy of another seat's harness.

Discovers the partner's new UCI options by diffing `uci` against exe B.
Runs O depth 12 with the new check option false, then true (spins at the
defaults the partner's uci line advertises).
"""
import hashlib
import subprocess
import sys
from pathlib import Path

S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
    "setoption name Threads value 1",
    "setoption name Hash value 16",
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def uci_options(exe: str) -> tuple[str, list[str]]:
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.stdin and proc.stdout
    proc.stdin.write("uci\nquit\n")
    proc.stdin.flush()
    lines = proc.stdout.read().splitlines()
    proc.wait(timeout=10)
    name = ""
    opts = []
    for line in lines:
        if line.startswith("id name "):
            name = line[len("id name "):]
        if line.startswith("option name "):
            opts.append(line)
    return name, opts


def main() -> None:
    exe = str(Path(sys.argv[1]).resolve())
    base_exe = str(Path(sys.argv[2]).resolve())
    out_dir = Path(sys.argv[3])
    fen_file = Path(sys.argv[4])
    depth = int(sys.argv[5])
    fens = [ln.split(";")[0].strip() for ln in fen_file.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    id_name, theirs = uci_options(exe)
    _, base = uci_options(base_exe)
    base_names = set()
    for line in base:
        parts = line.split()
        # option name NAME type ...
        if "type" in parts:
            base_names.add(" ".join(parts[2:parts.index("type")]))
    new_lines = []
    for line in theirs:
        parts = line.split()
        if "type" not in parts:
            continue
        name = " ".join(parts[2:parts.index("type")])
        if name not in base_names:
            new_lines.append(line)
    (out_dir / "partner_new_options.txt").write_text("\n".join(new_lines) + ("\n" if new_lines else ""))
    checks = []
    spins = []
    for line in new_lines:
        parts = line.split()
        name = " ".join(parts[2:parts.index("type")])
        kind = parts[parts.index("type") + 1]
        default = parts[parts.index("default") + 1] if "default" in parts else ""
        if kind == "check":
            checks.append((name, default))
        elif kind == "spin":
            spins.append((name, default))
    if len(checks) != 1:
        die(f"expected one new check option, found {checks}")
    switch, _ = checks[0]
    print("switch", switch)
    for name, default in spins:
        print("spin", name, default)

    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    def run(tag: str, extra: list[str]) -> None:
        proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert proc.stdin and proc.stdout
        raw: list[str] = []

        def send(line: str) -> None:
            proc.stdin.write(line + "\n")
            proc.stdin.flush()

        def until(marker: str) -> None:
            while True:
                line = proc.stdout.readline()
                if line == "":
                    die(tag + " engine closed waiting for " + marker)
                line = line.rstrip("\n")
                raw.append(line)
                low = line.lower()
                for bad in BAD:
                    if bad.lower() in low:
                        proc.kill()
                        die(tag + " STOP " + line)
                if marker in line:
                    return

        send("uci")
        until("uciok")
        for opt in S14 + extra:
            send(opt)
            send("isready")
            until("readyok")
        rows = []
        for index, fen in enumerate(fens, start=1):
            send("ucinewgame")
            send("isready")
            until("readyok")
            send("position fen " + fen)
            send("isready")
            until("readyok")
            send(f"go depth {depth}")
            nodes = None
            while True:
                line = proc.stdout.readline()
                if line == "":
                    die(tag + " closed during go")
                line = line.rstrip("\n")
                raw.append(line)
                low = line.lower()
                for bad in BAD:
                    if bad.lower() in low:
                        proc.kill()
                        die(tag + " STOP " + line)
                if " nodes " in line and "nodes" in line.split():
                    parts = line.split()
                    nodes = int(parts[parts.index("nodes") + 1])
                if line.startswith("bestmove"):
                    break
            if nodes is None:
                die(tag + " no nodes")
            rows.append(f"{index} {nodes}")
            if index % 50 == 0:
                print(tag, index, file=sys.stderr, flush=True)
        send("quit")
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        (out_dir / f"{tag}.txt").write_text("\n".join(rows) + "\n")
        (out_dir / f"{tag}.raw").write_text("\n".join(raw) + "\n")
        meta = [f"exe {exe}", f"sha256 {sha}", f"id name {id_name}", "options:"]
        meta.extend(S14 + extra)
        meta.append(f"depth {depth}")
        meta.append(f"positions {len(fens)}")
        (out_dir / f"{tag}.meta").write_text("\n".join(meta) + "\n")
        print(tag, "sum", sum(int(r.split()[1]) for r in rows))

    run("partner_off", [f"setoption name {switch} value false"])
    on_extra = [f"setoption name {switch} value true"]
    for name, default in spins:
        on_extra.append(f"setoption name {name} value {default}")
    run("partner_on", on_extra)
    (out_dir / "partner_switch.txt").write_text(switch + "\n")


if __name__ == "__main__":
    main()

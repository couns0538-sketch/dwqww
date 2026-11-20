#!/usr/bin/env python3
"""S14 depth search over a FEN list. One process. ucinewgame before every go."""
import hashlib
import os
import subprocess
import sys

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")
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
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    exe, fen_path, prefix, depth = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    extra = sys.argv[5:]  # extra setoption name value pairs, after S14
    exe = os.path.abspath(exe)
    fens = []
    with open(fen_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                fens.append(line)
    proc = subprocess.Popen(
        [exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
    )
    sent_options = []
    id_name = ""
    raw = open(prefix + ".txt", "w", encoding="utf-8")
    rows = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(ok):
        nonlocal id_name
        while True:
            line = proc.stdout.readline()
            if line == "":
                err = proc.stderr.read()
                raise SystemExit("stdout closed\n" + err)
            line = line.rstrip("\r\n")
            raw.write(line + "\n")
            low = line.lower()
            for bad in BAD:
                if bad in low:
                    raise SystemExit("STOP " + line)
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
            if ok(line):
                return line

    send("uci")
    read_until(lambda s: s == "uciok")
    send("isready")
    read_until(lambda s: s == "readyok")
    base_opts = [("Threads", "1"), ("Hash", "16")] + S14
    # extra is name value name value
    for i in range(0, len(extra), 2):
        base_opts.append((extra[i], extra[i + 1]))

    def options_once():
        for name, value in base_opts:
            cmd = f"setoption name {name} value {value}"
            sent_options.append(cmd)
            send(cmd)
            send("isready")
            read_until(lambda s: s == "readyok")

    nodes_list = []
    for index, fen in enumerate(fens):
        send("ucinewgame")
        send("isready")
        read_until(lambda s: s == "readyok")
        options_once()
        send("position fen " + fen)
        send("isready")
        read_until(lambda s: s == "readyok")
        send(f"go depth {depth}")
        last_nodes = None
        while True:
            line = proc.stdout.readline()
            if line == "":
                raise SystemExit("stdout closed during go")
            line = line.rstrip("\r\n")
            raw.write(line + "\n")
            low = line.lower()
            for bad in BAD:
                if bad in low:
                    raise SystemExit("STOP " + line)
            if line.startswith("info depth ") and " nodes " in line:
                parts = line.split()
                try:
                    last_nodes = int(parts[parts.index("nodes") + 1])
                except (ValueError, IndexError):
                    pass
            if line.startswith("bestmove "):
                break
        if last_nodes is None:
            raise SystemExit(f"no nodes for position {index}")
        nodes_list.append(last_nodes)
        rows.append(f"{index} {last_nodes}")
        raw.write(f"# row {index} {last_nodes}\n")
        raw.flush()
    send("quit")
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
    err = proc.stderr.read()
    raw.close()
    total = sum(nodes_list)
    with open(prefix + ".rows", "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
        f.write(f"SUM {total}\n")
        f.write("FIRST3 " + " ".join(str(n) for n in nodes_list[:3]) + "\n")
    with open(prefix + ".err", "w", encoding="utf-8") as f:
        f.write(err)
    with open(prefix + ".meta", "w", encoding="utf-8") as f:
        f.write(f"exe={exe}\n")
        f.write(f"sha256={sha256(exe)}\n")
        f.write(f"id_name={id_name}\n")
        f.write(f"fen_file={os.path.abspath(fen_path)}\n")
        f.write(f"positions={len(fens)}\n")
        f.write(f"depth={depth}\n")
        f.write(f"sum={total}\n")
        f.write("option_lines:\n")
        # the option lines of the first position (the set repeated before every go)
        seen = []
        for cmd in sent_options:
            if cmd in seen:
                break
            seen.append(cmd)
        for cmd in seen:
            f.write(cmd + "\n")
        f.write(f"option_repeats={len(sent_options) // max(1, len(seen))}\n")
    if err.strip():
        print("STDERR", err, file=sys.stderr)
        return 3
    print(f"SUM {total}")
    print("FIRST3", " ".join(str(n) for n in nodes_list[:3]))
    print("N", len(nodes_list))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            sys.exit(1)
        raise

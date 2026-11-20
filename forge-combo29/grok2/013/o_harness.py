#!/usr/bin/env python3
"""Depth-12 O-run harness. One engine process. Stops on a refused option or FEN."""
import hashlib
import select
import subprocess
import sys
import time

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = [
    ("Threads", "1"),
    ("Hash", "16"),
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


class Stop(Exception):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    if len(sys.argv) < 5:
        sys.exit("usage: o_harness.py EXE none|false|true FENS OUT_PREFIX [MAX]")
    exe, mode, fens_path, prefix = sys.argv[1:5]
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    if mode not in ("none", "false", "true"):
        sys.exit("mode must be none, false or true")
    options = list(S14)
    if mode != "none":
        options.append(("IdeaB8", mode))
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    if limit:
        fens = fens[:limit]
    raw_path = prefix + "_raw.txt"
    nodes_path = prefix + "_nodes.txt"
    meta_path = prefix + ".meta"
    open(raw_path, "w", encoding="utf-8").close()
    option_lines = [f"setoption name {name} value {value}" for name, value in options]
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe: {exe}\n")
        meta.write(f"sha256: {sha256_file(exe)}\n")
        meta.write("id name: (pending)\n")
        meta.write("options:\n")
        for line in option_lines:
            meta.write(line + "\n")
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    id_name = ""

    def send(line):
        proc.stdin.write((line + "\n").encode())
        proc.stdin.flush()

    def read_until(marker, timeout):
        deadline = time.monotonic() + timeout
        collected = []
        with open(raw_path, "a", encoding="utf-8") as raw:
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                ready, _, _ = select.select([proc.stdout], [], [], remaining)
                if not ready:
                    break
                blob = proc.stdout.readline()
                if blob == b"":
                    break
                line = blob.decode("utf-8", errors="replace").rstrip("\r\n")
                raw.write(line + "\n")
                collected.append(line)
                for bad in STOP_MARKERS:
                    if bad in line:
                        raise Stop(line)
                if line == marker or line.startswith(marker + " "):
                    return collected
            raise Stop(f"timeout waiting for {marker}; last={collected[-3:]}")

    try:
        send("uci")
        uci_lines = read_until("uciok", 30)
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        text = open(meta_path, encoding="utf-8").read()
        text = text.replace("id name: (pending)", "id name: " + id_name, 1)
        open(meta_path, "w", encoding="utf-8").write(text)
        for line in option_lines:
            send(line)
            send("isready")
            read_until("readyok", 30)
        with open(nodes_path, "w", encoding="utf-8") as nodes_out:
            for index, fen in enumerate(fens, start=1):
                send("ucinewgame")
                send("isready")
                read_until("readyok", 30)
                send("position fen " + fen)
                send("isready")
                read_until("readyok", 30)
                send("go depth 12")
                played = read_until("bestmove", 120)
                info = [line for line in played if line.startswith("info ")]
                if not info or " nodes " not in info[-1]:
                    raise Stop(f"position {index} last info has no nodes: {info[-1] if info else 'none'}")
                parts = info[-1].split()
                count = int(parts[parts.index("nodes") + 1])
                nodes_out.write(f"{index} {count}\n")
                nodes_out.flush()
                if index % 25 == 0:
                    print(f"{prefix} {index}", flush=True)
        send("quit")
        proc.wait(timeout=10)
        print(f"{prefix} done {len(fens)}", flush=True)
    except Stop as error:
        print(f"STOP {prefix}: {error}", file=sys.stderr, flush=True)
        proc.kill()
        sys.exit(1)


if __name__ == "__main__":
    main()

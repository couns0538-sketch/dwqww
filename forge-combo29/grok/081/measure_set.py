#!/usr/bin/env python3
"""One engine, S14, Threads 1, Hash 16, ucinewgame before every go depth.

Stops on unknown option, invalid value, invalid FEN, or illegal move.
Writes the raw UCI transcript, one node count per line, and a .meta file.
"""
import argparse
import hashlib
import subprocess
import sys

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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Stop(Exception):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path):
    fens = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            fens.append(text)
    return fens


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--s10", choices=("omit", "false", "true"), default="omit")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    fens = load_fens(args.fens)
    if args.limit:
        fens = fens[: args.limit]
    exe_sha = sha256_file(args.exe)
    proc = subprocess.Popen(
        [args.exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = []
    options_sent = []
    id_name = ""

    def send(line):
        raw.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done):
        got = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                raw.append("<< <eof>")
                raise Stop("engine closed stdout")
            text = line.rstrip("\r\n")
            raw.append("<< " + text)
            got.append(text)
            for bad in BAD:
                if bad in text:
                    raise Stop(text)
            if done(text):
                return got

    def ready():
        send("isready")
        read_until(lambda text: text == "readyok")

    nodes = []
    try:
        send("uci")
        uci_lines = read_until(lambda text: text == "uciok")
        id_name = ""
        for text in uci_lines:
            if text.startswith("id name "):
                id_name = text[len("id name ") :]
        ready()
        for name, value in [("Hash", "16"), ("Threads", "1"), *S14]:
            line = "setoption name %s value %s" % (name, value)
            options_sent.append(line)
            send(line)
            ready()
        if args.s10 != "omit":
            line = "setoption name IdeaS10 value %s" % args.s10
            options_sent.append(line)
            send(line)
            ready()
        for index, fen in enumerate(fens):
            send("ucinewgame")
            ready()
            send("position fen " + fen)
            ready()
            send("go depth %d" % args.depth)
            info = read_until(lambda text: text.startswith("bestmove "))
            count = None
            for text in info:
                if text.startswith("info depth "):
                    parts = text.split()
                    if "nodes" in parts:
                        count = int(parts[parts.index("nodes") + 1])
            if count is None:
                raise Stop("no nodes on position %d" % index)
            nodes.append(count)
            if (index + 1) % 25 == 0 or index + 1 == len(fens):
                print("progress %d/%d last %d" % (index + 1, len(fens), count), file=sys.stderr)
        send("quit")
    except Stop as error:
        print("STOP %s" % error, file=sys.stderr)
        try:
            proc.kill()
        except OSError:
            pass
        write_outputs(args.stem, args.exe, exe_sha, id_name, options_sent, raw, nodes)
        return 2
    finally:
        if proc.poll() is None:
            try:
                proc.stdin.close()
            except OSError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    write_outputs(args.stem, args.exe, exe_sha, id_name, options_sent, raw, nodes)
    print("positions %d" % len(nodes))
    return 0


def write_outputs(stem, exe, exe_sha, id_name, options_sent, raw, nodes):
    with open(stem + ".raw.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(raw))
        if raw:
            handle.write("\n")
    with open(stem + ".nodes.txt", "w", encoding="utf-8") as handle:
        for count in nodes:
            handle.write("%d\n" % count)
    with open(stem + ".meta", "w", encoding="utf-8") as handle:
        handle.write("started: %s\n" % exe)
        handle.write("sha256: %s\n" % exe_sha)
        handle.write("id name: %s\n" % id_name)
        handle.write("option lines sent:\n")
        for line in options_sent:
            handle.write(line + "\n")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print("FAIL %s" % error, file=sys.stderr)
        sys.exit(1)

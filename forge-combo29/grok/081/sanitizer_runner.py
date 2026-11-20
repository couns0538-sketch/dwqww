#!/usr/bin/env python3
"""Same runner for the sanitizer build and the deliberate-error build.

S14, Threads 1, Hash 16, IdeaS10 true, ucinewgame before every go.
Stderr is kept apart from the UCI transcript. The .meta file records
nm -C <exe> | grep -c __asan_ .
"""
import argparse
import hashlib
import os
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


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path, limit):
    fens = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            fens.append(text)
            if limit and len(fens) >= limit:
                break
    return fens


def asan_count(exe):
    proc = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, check=False)
    count = 0
    for line in proc.stdout.splitlines():
        if "__asan_" in line:
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--depth", type=int, default=10)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    fens = load_fens(args.fens, args.limit)
    exe_sha = sha256_file(args.exe)
    count = asan_count(args.exe)
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1:abort_on_error=0"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    proc = subprocess.Popen(
        [args.exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )
    raw = []
    options_sent = []
    id_name = ""
    stopped = ""

    def send(line):
        raw.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done):
        while True:
            line = proc.stdout.readline()
            if line == "":
                raw.append("<< <eof>")
                return False
            text = line.rstrip("\r\n")
            raw.append("<< " + text)
            for bad in BAD:
                if bad in text:
                    raise RuntimeError(text)
            if done(text):
                return True

    def ready():
        send("isready")
        if not read_until(lambda text: text == "readyok"):
            raise RuntimeError("no readyok")

    try:
        send("uci")
        while True:
            line = proc.stdout.readline()
            if line == "":
                raw.append("<< <eof>")
                raise RuntimeError("eof during uci")
            text = line.rstrip("\r\n")
            raw.append("<< " + text)
            if text.startswith("id name "):
                id_name = text[len("id name ") :]
            if text == "uciok":
                break
        ready()
        for name, value in [("Hash", "16"), ("Threads", "1"), *S14, ("IdeaS10", "true")]:
            line = "setoption name %s value %s" % (name, value)
            options_sent.append(line)
            send(line)
            ready()
        for index, fen in enumerate(fens):
            send("ucinewgame")
            ready()
            send("position fen " + fen)
            ready()
            send("go depth %d" % args.depth)
            if not read_until(lambda text: text.startswith("bestmove ")):
                stopped = "eof during go %d" % index
                break
            if (index + 1) % 25 == 0 or index + 1 == len(fens):
                print("progress %d/%d" % (index + 1, len(fens)), file=sys.stderr)
        if not stopped:
            send("quit")
    except Exception as error:
        stopped = str(error)
        print("STOP %s" % error, file=sys.stderr)
    stderr = ""
    try:
        proc.stdin.close()
    except OSError:
        pass
    try:
        stderr = proc.stderr.read()
    except OSError:
        stderr = ""
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        stderr += proc.stderr.read() if proc.stderr else ""
    with open(args.stem + ".raw.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(raw) + ("\n" if raw else ""))
    with open(args.stem + ".stderr.txt", "w", encoding="utf-8") as handle:
        handle.write(stderr)
    hits = []
    for line in stderr.splitlines():
        if "AddressSanitizer" in line or "runtime error:" in line or "SUMMARY:" in line:
            hits.append(line)
    with open(args.stem + ".sanitizer.txt", "w", encoding="utf-8") as handle:
        handle.write("asan_symbol_lines %d\n" % count)
        handle.write("sanitizer_lines %d\n" % len(hits))
        if stopped:
            handle.write("stopped: %s\n" % stopped)
        for line in hits:
            handle.write(line + "\n")
    with open(args.stem + ".meta", "w", encoding="utf-8") as handle:
        handle.write("started: %s\n" % args.exe)
        handle.write("sha256: %s\n" % exe_sha)
        handle.write("id name: %s\n" % id_name)
        handle.write("nm -C %s | grep -c __asan_ = %d\n" % (args.exe, count))
        handle.write("option lines sent:\n")
        for line in options_sent:
            handle.write(line + "\n")
    print("asan_symbol_lines %d" % count)
    print("sanitizer_lines %d" % len(hits))
    if stopped:
        print("stopped %s" % stopped)
    return 0


if __name__ == "__main__":
    sys.exit(main())

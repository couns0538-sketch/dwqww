#!/usr/bin/env python3
"""STEP 2 harness (seat 030, arm 10). Honesty lines and the three O runs.

Arm 10 has no patch: exe P is exe B (the same file). A fresh process is used
for every honesty line and for each O run. No setoption is sent before an
honesty command. O runs send Threads, Hash, S14, and (runs 2 and 3) the
switch, each followed by isready. Every position is ucinewgame, isready,
position, isready, go depth 12.
"""
import hashlib
import os
import subprocess
import sys

EXE = "/agent/repos/base/forge-combo29/build/forge"
FENS = os.path.expanduser("~/first200.fens")
SEAT = open(os.path.expanduser("~/grok2_seat.txt"), encoding="utf-8").read().strip()
REPO = open(os.path.expanduser("~/grok2_repo.txt"), encoding="utf-8").read().strip()
OUT = os.path.join(REPO, "forge-combo29", "grok2", SEAT)

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
SWITCH = "HindsightDepth"
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bad_line(line):
    return any(mark in line for mark in STOP_MARKS)


class Engine:
    def __init__(self, path):
        self.path = path
        self.lines = []
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    def send(self, command):
        self.lines.append(">> " + command)
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, done):
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                raise SystemExit("STOP: engine closed stdout")
            line = line.rstrip("\r\n")
            self.lines.append(line)
            if bad_line(line):
                raise SystemExit("STOP: " + line)
            if done(line):
                return line

    def isready(self):
        self.send("isready")
        self.read_until(lambda line: line == "readyok")

    def close(self):
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)


def id_name_of(lines):
    for line in lines:
        if line.startswith("id name "):
            return line[len("id name "):]
    return ""


def write_meta(path, options):
    eng = Engine(EXE)
    eng.send("uci")
    eng.read_until(lambda line: line == "uciok")
    name = id_name_of(eng.lines)
    eng.close()
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"exe {EXE}\n")
        handle.write(f"sha256 {sha256_file(EXE)}\n")
        handle.write(f"id_name {name}\n")
        handle.write("options\n")
        if not options:
            handle.write("(none)\n")
        for opt_name, value in options:
            handle.write(f"setoption name {opt_name} value {value}\n")


def nodes_field(line):
    parts = line.split()
    if "nodes" not in parts:
        return None
    index = parts.index("nodes")
    if index + 1 >= len(parts):
        return None
    return int(parts[index + 1])


def save(path, lines):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def honesty_one(tag, command, done):
    eng = Engine(EXE)
    eng.send("uci")
    eng.read_until(lambda line: line == "uciok")
    eng.send(command)
    eng.read_until(done)
    eng.close()
    raw = os.path.join(OUT, f"honesty_{tag}.txt")
    save(raw, eng.lines)
    write_meta(os.path.join(OUT, f"honesty_{tag}.meta"), [])
    found = None
    for line in eng.lines:
        got = nodes_field(line)
        if got is not None and (line.startswith("info string bench") or line.startswith("nodes ")):
            found = got
    print(f"honesty {tag}: {found}", flush=True)
    return found


def run_honesty():
    expected = {
        "B_bench11": (312866, "bench 11", lambda line: line.startswith("info string bench")),
        "B_bench13": (862329, "bench 13", lambda line: line.startswith("info string bench")),
        "B_bench16": (3024920, "bench 16", lambda line: line.startswith("info string bench")),
        "B_perft5": (4865609, "go perft 5", lambda line: line.startswith("nodes ")),
    }
    # Arm 10: exe P is exe B, so the same four commands are also the P lines.
    tags = list(expected)
    tags += [("P_" + tag[2:], expected[tag]) for tag in expected]
    # rebuild as pairs
    jobs = []
    for tag, spec in expected.items():
        jobs.append((tag, spec))
        jobs.append(("P_" + tag[2:], spec))
    ok = True
    for tag, (want, command, done) in jobs:
        got = honesty_one(tag, command, done)
        if got != want:
            print(f"MISS {tag}: got {got} want {want}", flush=True)
            ok = False
    if not ok:
        raise SystemExit("honesty MISS")
    print("honesty ok", flush=True)


def load_fens():
    with open(FENS, encoding="utf-8") as handle:
        rows = [line.strip() for line in handle if line.strip()]
    if len(rows) != 200:
        raise SystemExit(f"STOP: first200.fens has {len(rows)} lines")
    return rows


def one_search(eng):
    last = None
    while True:
        line = eng.proc.stdout.readline()
        if line == "":
            raise SystemExit("STOP: engine closed stdout during search")
        line = line.rstrip("\r\n")
        eng.lines.append(line)
        if bad_line(line):
            raise SystemExit("STOP: " + line)
        if line.startswith("bestmove"):
            if last is None:
                raise SystemExit("STOP: bestmove with no info nodes")
            return last
        if line.startswith("info ") and " nodes " in line:
            got = nodes_field(line)
            if got is not None:
                last = got


def run_o(tag, extra_options):
    options = list(S14) + list(extra_options)
    fens = load_fens()
    eng = Engine(EXE)
    eng.send("uci")
    eng.read_until(lambda line: line == "uciok")
    for opt_name, value in options:
        eng.send(f"setoption name {opt_name} value {value}")
        eng.isready()
    rows = []
    for index, fen in enumerate(fens, start=1):
        eng.send("ucinewgame")
        eng.isready()
        eng.send("position fen " + fen)
        eng.isready()
        eng.send("go depth 12")
        nodes = one_search(eng)
        rows.append((index, nodes))
        if index % 25 == 0:
            print(f"{tag} {index} {nodes}", flush=True)
    eng.close()
    save(os.path.join(OUT, f"{tag}.txt"), eng.lines)
    write_meta(os.path.join(OUT, f"{tag}.meta"), options)
    with open(os.path.join(OUT, f"{tag}.rows"), "w", encoding="utf-8") as handle:
        for index, nodes in rows:
            handle.write(f"{index}\t{nodes}\n")
    print(f"{tag} done sum {sum(nodes for _, nodes in rows)}", flush=True)


def read_rows(tag):
    rows = []
    with open(os.path.join(OUT, f"{tag}.rows"), encoding="utf-8") as handle:
        for line in handle:
            index, nodes = line.rstrip("\n").split("\t")
            rows.append((int(index), int(nodes)))
    return rows


def run_table():
    labels = {
        "B_bench11": 312866,
        "B_bench13": 862329,
        "B_bench16": 3024920,
        "B_perft5": 4865609,
        "P_bench11": 312866,
        "P_bench13": 862329,
        "P_bench16": 3024920,
        "P_perft5": 4865609,
    }
    print("honesty")
    for tag, want in labels.items():
        got = None
        with open(os.path.join(OUT, f"honesty_{tag}.txt"), encoding="utf-8") as handle:
            for line in handle:
                line = line.rstrip("\n")
                if line.startswith("info string bench") or line.startswith("nodes "):
                    got = nodes_field(line)
        mark = "ok" if got == want else "MISS"
        print(f"{tag} {got} expect {want} {mark}")
    b_rows = read_rows("o1_B")
    off_rows = read_rows("o2_P_off")
    on_rows = read_rows("o3_P_on")
    def show(tag, rows, expect_sum, expect_first, expect_differ):
        total = sum(nodes for _, nodes in rows)
        first = [nodes for _, nodes in rows[:3]]
        differ = None
        if expect_differ is not None:
            differ = sum(1 for (i, n), (_, b) in zip(rows, b_rows) if n != b)
        print(
            f"{tag} n {len(rows)} sum {total} expect_sum {expect_sum} "
            f"first {first[0]} {first[1]} {first[2]} expect_first {expect_first[0]} {expect_first[1]} {expect_first[2]}"
        )
        if expect_differ is None:
            same = sum(1 for (i, n), (_, b) in zip(rows, b_rows) if n == b)
            print(f"{tag} identical {same} of {len(rows)}")
        else:
            print(f"{tag} differ {differ} expect_differ {expect_differ}")
        sum_ok = total == expect_sum
        first_ok = first == list(expect_first)
        if expect_differ is None:
            ident_ok = all(n == b for (_, n), (_, b) in zip(rows, b_rows))
            print(f"{tag} match {sum_ok and first_ok and ident_ok}")
        else:
            print(f"{tag} match {sum_ok and first_ok and differ == expect_differ}")
    show("o1_B", b_rows, 9500069, (41311, 24872, 28574), None)
    show("o2_P_off", off_rows, 9500069, (41311, 24872, 28574), None)
    show("o3_P_on", on_rows, 9845650, (23395, 31504, 35958), 200)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "honesty":
        run_honesty()
    elif mode == "o1":
        run_o("o1_B", [])
    elif mode == "o2":
        run_o("o2_P_off", [(SWITCH, "false")])
    elif mode == "o3":
        run_o("o3_P_on", [(SWITCH, "true")])
    elif mode == "table":
        run_table()
    else:
        raise SystemExit("mode: honesty o1 o2 o3 table")

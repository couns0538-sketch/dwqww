#!/usr/bin/env python3
"""Same measured-set protocol as run_set.py, with stderr kept for sanitizers.

Writes PREFIX.raw.txt (stdout), PREFIX.stderr.txt, PREFIX.tsv, PREFIX.meta.
The meta line asan_symbols is: nm -C EXE | grep -c __asan_
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
]

def load_fens(path):
    fens = []
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 6 and "/" in parts[0]:
            fens.append(" ".join(parts[:6]))
        else:
            fens.append(line)
    return fens

def main():
    if len(sys.argv) != 7:
        print("usage: run_asan.py EXE FENS DEPTH SWITCH OUT_PREFIX LIMIT", file=sys.stderr)
        sys.exit(2)
    exe = str(Path(sys.argv[1]).resolve())
    fens = load_fens(sys.argv[2])
    depth = int(sys.argv[3])
    switch = sys.argv[4]
    prefix = Path(sys.argv[5])
    limit = int(sys.argv[6])
    if limit > 0:
        fens = fens[:limit]
    options = [("Threads", "1"), ("Hash", "16")] + S14
    if switch != "omit":
        options.append(("IdeaS35", switch))
    digest = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    nm = subprocess.run(["nm", "-C", exe], text=True, capture_output=True)
    asan_symbols = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1:abort_on_error=1"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )
    raw = []
    err = []
    died = False

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def bad(line):
        low = line.lower()
        return ("unknown option" in low or "invalid value" in low or "invalid fen" in low or "illegal move" in low)

    def read_until(predicate):
        nonlocal died
        got = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                died = True
                return got
            raw.append(line)
            got.append(line)
            if bad(line):
                return got
            if predicate(line):
                return got

    option_lines = []
    id_name = ""
    rows = []
    stop_reason = ""
    send("uci")
    uci = read_until(lambda line: line.strip() == "uciok")
    for line in uci:
        if line.startswith("id name "):
            id_name = line[len("id name "):].strip()
        if bad(line):
            stop_reason = line.strip()
    if not died and not stop_reason:
        send("isready")
        ready = read_until(lambda line: line.strip() == "readyok")
        if any(bad(line) for line in ready):
            stop_reason = "bad ready"
    if not died and not stop_reason:
        for name, value in options:
            sent = f"setoption name {name} value {value}"
            option_lines.append(sent)
            send(sent)
            send("isready")
            ready = read_until(lambda line: line.strip() == "readyok")
            if died or any(bad(line) for line in ready):
                stop_reason = "".join(ready).strip() or "died during option"
                break
    if not died and not stop_reason:
        for index, fen in enumerate(fens, start=1):
            send("ucinewgame")
            send("isready")
            if not read_until(lambda line: line.strip() == "readyok") and died:
                stop_reason = f"died before position {index}"
                break
            send(f"position fen {fen}")
            send("isready")
            pos = read_until(lambda line: line.strip() == "readyok")
            if died or any(bad(line) for line in pos):
                stop_reason = "".join(pos).strip() or f"died on position {index}"
                break
            send(f"go depth {depth}")
            info = read_until(lambda line: line.startswith("bestmove "))
            if died:
                stop_reason = f"died during go {index}"
                break
            if any(bad(line) for line in info):
                stop_reason = "".join(info).strip()
                break
            nodes = None
            for line in info:
                if line.startswith("info ") and " nodes " in line:
                    parts = line.split()
                    nodes = int(parts[parts.index("nodes") + 1])
            if nodes is None:
                stop_reason = f"no nodes at {index}"
                break
            rows.append((index, nodes, fen))
            if index % 25 == 0:
                print(f"progress {index}/{len(fens)}", flush=True)
    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    err_text = proc.stderr.read() if proc.stderr else ""
    err.append(err_text)
    stderr_text = "".join(err)
    sanitizer_lines = [
        line for line in stderr_text.splitlines()
        if "ERROR:" in line or "runtime error:" in line or "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line
    ]
    prefix.parent.mkdir(parents=True, exist_ok=True)
    Path(str(prefix) + ".raw.txt").write_text("".join(raw))
    Path(str(prefix) + ".stderr.txt").write_text(stderr_text)
    total = sum(n for _, n, _ in rows)
    tsv = ["index\tnodes\tfen"]
    for index, nodes, fen in rows:
        tsv.append(f"{index}\t{nodes}\t{fen}")
    tsv.append(f"SUM\t{total}\t")
    Path(str(prefix) + ".tsv").write_text("\n".join(tsv) + "\n")
    meta = [
        f"exe={exe}",
        f"sha256={digest}",
        f"id_name={id_name}",
        f"depth={depth}",
        f"switch={switch}",
        f"positions_done={len(rows)}",
        f"positions_asked={len(fens)}",
        f"sum={total}",
        f"asan_symbols={asan_symbols}",
        f"sanitizer_lines={len(sanitizer_lines)}",
        f"died={died}",
        f"stop_reason={stop_reason}",
        "ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1",
        "UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1",
        "options:",
        *option_lines,
        "sanitizer:",
        *sanitizer_lines,
        "",
    ]
    Path(str(prefix) + ".meta").write_text("\n".join(meta))
    print(f"done positions={len(rows)} asan_symbols={asan_symbols} sanitizer_lines={len(sanitizer_lines)} died={died}", flush=True)
    if sanitizer_lines:
        print(sanitizer_lines[0], flush=True)

if __name__ == "__main__":
    main()

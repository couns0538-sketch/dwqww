#!/usr/bin/env python3
"""One engine process. S14, Threads 1, Hash 16, ucinewgame+isready before every go.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import argparse
import hashlib
import re
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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe: str):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: list[str] = []

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, marker: str) -> str:
        assert self.proc.stdout is not None
        while True:
            raw = self.proc.stdout.readline()
            if raw == "":
                raise SystemExit("engine closed stdout before " + marker)
            line = raw.rstrip("\r\n")
            self.lines.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit("STOP " + line)
            if marker in line:
                return line

    def close(self) -> None:
        try:
            self.send("quit")
        except Exception:
            pass
        if self.proc.stdout is not None:
            rest = self.proc.stdout.read()
            if rest:
                self.lines.extend(rest.splitlines())
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def load_fens(path: Path) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fens.append(line)
    return fens


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--fens", required=True)
    ap.add_argument("--depth", type=int, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--switch", choices=["omit", "false", "true"], default="omit")
    ap.add_argument("--option", default="IdeaS38")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    exe = Path(args.exe).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fens = load_fens(Path(args.fens))
    sha = hashlib.sha256(exe.read_bytes()).hexdigest()

    options = list(S14)
    if args.switch != "omit":
        options.append((args.option, args.switch))

    eng = Engine(str(exe))
    eng.send("uci")
    uciok = eng.read_until("uciok")
    id_name = ""
    for line in eng.lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):]
    rows = []
    crashed = ""
    try:
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until("readyok")
            for name, value in options:
                eng.send(f"setoption name {name} value {value}")
                eng.send("isready")
                eng.read_until("readyok")
            eng.send("position fen " + fen)
            eng.send("isready")
            eng.read_until("readyok")
            eng.send(f"go depth {args.depth}")
            best = eng.read_until("bestmove")
            nodes = None
            depth_seen = None
            for line in reversed(eng.lines):
                if line == best:
                    continue
                m = re.search(r"\bnodes (\d+)\b", line)
                if m and line.startswith("info "):
                    nodes = int(m.group(1))
                    dm = re.search(r"\bdepth (\d+)\b", line)
                    depth_seen = int(dm.group(1)) if dm else -1
                    break
            if nodes is None:
                raise SystemExit(f"no nodes for position {index}")
            rows.append((index, nodes, depth_seen, best))
            if index <= 3 or index % 50 == 0 or index == len(fens):
                print(f"{args.tag} {index} depth {depth_seen} nodes {nodes}", flush=True)
    except SystemExit as exc:
        crashed = str(exc)
    finally:
        eng.close()
        raw_path = out / f"{args.tag}.raw.txt"
        raw_path.write_text("\n".join(eng.lines) + "\n")
        nm = subprocess.run(["nm", "-C", str(exe)], capture_output=True, text=True)
        asan_lines = 0
        if nm.returncode == 0:
            asan_lines = sum(1 for line in nm.stdout.splitlines() if "__asan_" in line)
        opt_lines = "\n".join(f"setoption name {n} value {v}" for n, v in options)
        (out / f"{args.tag}.meta").write_text(
            f"exe={exe}\nsha256={sha}\nid_name={id_name}\nuciok_line={uciok}\n"
            f"switch={args.switch}\ndepth={args.depth}\nfens={args.fens}\n"
            f"nm_asan_symbol_lines={asan_lines}\n"
            f"crashed={crashed}\n"
            f"options_sent:\n{opt_lines}\n"
        )

    tsv = out / f"{args.tag}.nodes.tsv"
    with tsv.open("w") as fh:
        fh.write("index\tnodes\tdepth\tbestmove\n")
        for index, nodes, depth_seen, best in rows:
            fh.write(f"{index}\t{nodes}\t{depth_seen}\t{best}\n")
    total = sum(r[1] for r in rows)
    summary = out / f"{args.tag}.sum.txt"
    summary.write_text(
        f"tag={args.tag}\npositions={len(rows)}\ndepth={args.depth}\nswitch={args.switch}\n"
        f"sum={total}\nfirst3={rows[0][1] if rows else ''} {rows[1][1] if len(rows)>1 else ''} {rows[2][1] if len(rows)>2 else ''}\n"
    )
    print(summary.read_text(), end="")
    if crashed:
        print(crashed)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

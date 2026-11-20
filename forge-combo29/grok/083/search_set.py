#!/usr/bin/env python3
"""Depth search over a FEN list. Stops on unknown option, invalid value, invalid FEN, illegal move."""
import argparse
import hashlib
import subprocess
import sys
import threading
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

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe: Path, raw):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.raw = raw
        self.err_text = ""
        self.err_thread = threading.Thread(target=self._drain_err, daemon=True)
        self.err_thread.start()

    def _drain_err(self) -> None:
        if self.proc.stderr is None:
            return
        self.err_text = self.proc.stderr.read()

    def send(self, line: str) -> None:
        self.raw.write(f"> {line}\n")
        self.raw.flush()
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, marker: str) -> list[str]:
        assert self.proc.stdout is not None
        lines = []
        while True:
            line = self.proc.stdout.readline()
            if line == "":
                self.proc.wait(timeout=5)
                self.err_thread.join(timeout=5)
                self.raw.write("\n# stderr\n")
                self.raw.write(self.err_text)
                self.raw.flush()
                raise SystemExit(f"engine closed before {marker}\n{self.err_text}")
            self.raw.write(line)
            self.raw.flush()
            text = line.rstrip("\r\n")
            lines.append(text)
            low = text.lower()
            for bad in BAD:
                if bad in low:
                    raise SystemExit(f"STOP {text}")
            if marker in text:
                return lines

    def close(self) -> str:
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.err_thread.join(timeout=5)
        if self.err_text:
            self.raw.write("\n# stderr\n")
            self.raw.write(self.err_text)
        return self.err_text

    def setoption(self, name: str, value: str, sent: list[str]) -> None:
        command = f"setoption name {name} value {value}"
        sent.append(command)
        self.send(command)
        self.send("isready")
        self.read_until("readyok")


def load_fens(path: Path, limit: int) -> list[str]:
    fens = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fen = line.split(";")[0].strip()
        # epd may carry opcodes after the 6 fen fields
        parts = fen.split()
        if len(parts) >= 6:
            fen = " ".join(parts[:6])
        fens.append(fen)
        if limit and len(fens) >= limit:
            break
    return fens


def parse_nodes(lines: list[str]) -> tuple[str, str]:
    nodes = ""
    score = ""
    for line in lines:
        if not line.startswith("info ") or " nodes " not in line or " depth " not in line:
            continue
        parts = line.split()
        if "nodes" in parts:
            nodes = parts[parts.index("nodes") + 1]
        if "score" in parts:
            score_idx = parts.index("score")
            if parts[score_idx + 1] == "cp":
                score = parts[score_idx + 2]
            elif parts[score_idx + 1] == "mate":
                score = "mate " + parts[score_idx + 2]
            else:
                score = parts[score_idx + 1]
    return nodes, score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True)
    parser.add_argument("--fens", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--idea", choices=("omit", "false", "true"), default="omit")
    parser.add_argument("--min-depth", default="")
    args = parser.parse_args()

    exe = Path(args.exe).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    fens = load_fens(Path(args.fens), args.limit)
    raw_path = outdir / f"{args.label}.raw.txt"
    tsv_path = outdir / f"{args.label}.tsv"
    meta_path = outdir / f"{args.label}.meta"

    options = [("Threads", "1"), ("Hash", "16")]
    if args.idea != "omit":
        options.append(("IdeaA2", args.idea))
    if args.min_depth:
        options.append(("IdeaA2_MinDepth", args.min_depth))
    options.extend(S14)

    id_name = ""
    sent = []
    with raw_path.open("w") as raw:
        engine = Engine(exe, raw)
        engine.send("uci")
        uci_lines = engine.read_until("uciok")
        for line in uci_lines:
            if line.startswith("id name "):
                id_name = line[len("id name ") :]
        for name, value in options:
            engine.setoption(name, value, sent)
        rows = []
        for index, fen in enumerate(fens, start=1):
            for name, value in S14:
                engine.setoption(name, value, sent)
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until("readyok")
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until("readyok")
            engine.send(f"go depth {args.depth}")
            go_lines = engine.read_until("bestmove")
            nodes, score = parse_nodes(go_lines)
            if nodes == "":
                raise SystemExit(f"no nodes for position {index}")
            rows.append((index, nodes, score, fen))
            if index % 25 == 0:
                print(f"{args.label} {index}/{len(fens)}", file=sys.stderr, flush=True)
        err = engine.close()
        if err.strip():
            (outdir / f"{args.label}.stderr.txt").write_text(err)

    with tsv_path.open("w") as tsv:
        tsv.write("index\tnodes\tscore\tfen\n")
        for index, nodes, score, fen in rows:
            tsv.write(f"{index}\t{nodes}\t{score}\t{fen}\n")
    total = sum(int(nodes) for _, nodes, _, _ in rows)
    first = " ".join(nodes for _, nodes, _, _ in rows[:3])
    meta_path.write_text(
        f"exe: {exe}\n"
        f"sha256: {sha256(exe)}\n"
        f"id name: {id_name}\n"
        f"depth: {args.depth}\n"
        f"positions: {len(rows)}\n"
        f"sum_nodes: {total}\n"
        f"first3: {first}\n"
        f"options sent:\n" + "\n".join(sent) + "\n"
    )
    print(f"{args.label} positions {len(rows)} sum {total} first3 {first}")


if __name__ == "__main__":
    main()

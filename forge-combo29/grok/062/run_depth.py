#!/usr/bin/env python3
"""Depth-sum harness. One engine process. Stops on a refused option or FEN."""

import hashlib
import pathlib
import queue
import subprocess
import sys
import threading
import time

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


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path: pathlib.Path, limit: int | None) -> list[str]:
    fens = []
    for line in path.read_text(encoding="utf-8").splitlines():
        core = line.split(";", 1)[0].strip()
        if not core:
            continue
        parts = core.split()
        if len(parts) == 4:
            core = core + " 0 1"
        elif len(parts) < 6:
            raise SystemExit(f"short fen: {core}")
        else:
            core = " ".join(parts[:6])
        fens.append(core)
        if limit is not None and len(fens) >= limit:
            break
    return fens


class Engine:
    def __init__(self, exe: str) -> None:
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.stderr: list[str] = []
        threading.Thread(target=self._read_out, daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()

    def _read_out(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _read_err(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self.stderr.append(line)

    def send(self, line: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, marker: str, timeout: float) -> list[str]:
        got: list[str] = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remain = deadline - time.monotonic()
            try:
                line = self.lines.get(timeout=min(0.5, remain))
            except queue.Empty:
                continue
            if line is None:
                raise SystemExit(f"engine exited {self.proc.returncode} waiting for {marker}")
            got.append(line)
            stripped = line.strip()
            for bad in BAD:
                if bad in stripped:
                    raise SystemExit("STOP " + bad + ": " + stripped)
            if stripped == marker or stripped.startswith(marker + " ") or stripped.startswith(marker + "\t"):
                return got
        raise SystemExit(f"timeout waiting for {marker}")

    def close(self) -> None:
        try:
            self.send("quit")
        except (BrokenPipeError, OSError):
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def nodes_of(info_lines: list[str]) -> int:
    found = None
    for line in info_lines:
        if not line.startswith("info "):
            continue
        parts = line.split()
        if "nodes" in parts:
            found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise SystemExit("no nodes field")
    return found


def main() -> None:
    if len(sys.argv) < 6:
        raise SystemExit("usage: run_depth.py EXE FENS DEPTH OUTSTEM MODE [LIMIT]")
    exe, fen_path, depth_s, outstem, mode = sys.argv[1:6]
    limit = int(sys.argv[6]) if len(sys.argv) > 6 else None
    depth = int(depth_s)
    if mode not in {"base", "off", "on"}:
        raise SystemExit("MODE is base, off, or on")
    fens = load_fens(pathlib.Path(fen_path), limit)
    out = pathlib.Path(outstem)
    out.parent.mkdir(parents=True, exist_ok=True)
    engine = Engine(exe)
    raw: list[str] = []
    sent: list[str] = []
    rows: list[str] = []

    def talk(line: str, marker: str | None, timeout: float) -> list[str]:
        sent.append(line)
        raw.append(">> " + line + "\n")
        engine.send(line)
        if marker is None:
            return []
        got = engine.read_until(marker, timeout)
        raw.extend(got)
        return got

    try:
        hello = talk("uci", "uciok", 30)
        id_name = "MISSING"
        for line in hello:
            if line.startswith("id name "):
                id_name = line[len("id name "):].strip()
        talk("isready", "readyok", 30)
        talk("setoption name Threads value 1", None, 0)
        talk("isready", "readyok", 30)
        talk("setoption name Hash value 16", None, 0)
        talk("isready", "readyok", 30)
        for name, value in S14:
            talk(f"setoption name {name} value {value}", None, 0)
            talk("isready", "readyok", 30)
        if mode == "off":
            talk("setoption name DeadMaterial value false", None, 0)
            talk("isready", "readyok", 30)
        elif mode == "on":
            talk("setoption name DeadMaterial value true", None, 0)
            talk("isready", "readyok", 30)
        total = 0
        for index, fen in enumerate(fens, 1):
            talk("ucinewgame", None, 0)
            talk("isready", "readyok", 30)
            talk("position fen " + fen, None, 0)
            talk("isready", "readyok", 30)
            info = talk(f"go depth {depth}", "bestmove", 180)
            count = nodes_of(info)
            move = "none"
            for line in info:
                if line.startswith("bestmove "):
                    move = line.split()[1]
            total += count
            rows.append(f"{index} {count} {move}")
            if index % 50 == 0:
                print(f"{out.name} {index}/{len(fens)} sum {total}", flush=True)
        summary = [
            f"exe {exe}",
            f"sha256 {sha256(pathlib.Path(exe))}",
            f"id name {id_name}",
            f"fens {fen_path}",
            f"fen_sha256 {sha256(pathlib.Path(fen_path))}",
            f"count {len(fens)}",
            f"depth {depth}",
            f"mode {mode}",
            f"sum {total}",
        ]
        if rows:
            summary.append("first " + rows[0])
            if len(rows) > 1:
                summary.append("second " + rows[1])
            if len(rows) > 2:
                summary.append("third " + rows[2])
        (out.parent / (out.name + ".txt")).write_text("".join(raw), encoding="utf-8")
        (out.parent / (out.name + ".rows")).write_text("\n".join(rows) + "\n", encoding="utf-8")
        (out.parent / (out.name + ".meta")).write_text(
            "\n".join(summary) + "\noptions sent:\n" + "\n".join(sent) + "\n",
            encoding="utf-8",
        )
        print("\n".join(summary), flush=True)
    finally:
        engine.close()
        if engine.stderr:
            (out.parent / (out.name + ".stderr")).write_text("".join(engine.stderr), encoding="utf-8")


if __name__ == "__main__":
    main()

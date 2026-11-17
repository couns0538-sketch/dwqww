"""A UCI driver that reads to `bestmove` before sending anything else.

The audit's trap #1: piping `quit` into a live search makes the engine abort
and fabricate a bestmove with zero info lines. This driver never does that:
every `go` is followed by a blocking read to `bestmove`, and `quit` is only
sent from close() after the engine is idle.
"""

from __future__ import annotations

import queue
import subprocess
import threading
from dataclasses import dataclass, field


@dataclass
class InfoLine:
    depth: int = 0
    multipv: int = 1
    score_cp: int | None = None
    score_mate: int | None = None
    nodes: int = 0
    pv: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def is_mate(self) -> bool:
        return self.score_mate is not None


@dataclass
class GoResult:
    bestmove: str
    infos: list[InfoLine]
    strings: list[str]

    @property
    def last(self) -> InfoLine | None:
        return self.infos[-1] if self.infos else None

    @property
    def nodes(self) -> int:
        return self.infos[-1].nodes if self.infos else 0


class Engine:
    def __init__(self, path: str, options: dict[str, str] | None = None,
                 env: dict[str, str] | None = None):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        self._q: queue.Queue[str | None] = queue.Queue()
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()
        self.send("uci")
        self._read_until(lambda ln: ln.strip() == "uciok")
        for k, v in (options or {}).items():
            self.send(f"setoption name {k} value {v}")
        self.isready()

    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self._q.put(line.rstrip("\n"))
        self._q.put(None)

    def send(self, cmd: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def _read_until(self, pred) -> list[str]:
        lines: list[str] = []
        while True:
            try:
                ln = self._q.get(timeout=600)
            except queue.Empty:
                raise TimeoutError(f"engine silent; collected {len(lines)} lines")
            if ln is None:
                raise RuntimeError(f"engine died; collected {len(lines)} lines: {lines[-5:]}")
            lines.append(ln)
            if pred(ln):
                return lines

    def isready(self) -> None:
        self.send("isready")
        self._read_until(lambda ln: ln.strip() == "readyok")

    def newgame(self) -> None:
        """Clear the table AND reset the board to startpos.

        Order matters: `ucinewgame` calls `board.set_fen(StandardStartFen)`, so a
        `position fen ...` sent before it is silently discarded. This harness ran
        four different positions and got four identical node counts before that
        was caught -- always call newgame(), then set the position.
        """
        self.send("ucinewgame")
        self.isready()

    def setoption(self, name: str, value: str) -> None:
        self.send(f"setoption name {name} value {value}")
        self.isready()

    def position_fen(self, fen: str) -> list[str]:
        """Returns any engine complaint lines (e.g. invalid FEN / illegal move)."""
        self.send(f"position fen {fen}")
        return []

    def go(self, spec: str) -> GoResult:
        self.send(f"go {spec}")
        lines = self._read_until(lambda ln: ln.startswith("bestmove"))
        infos: list[InfoLine] = []
        strings: list[str] = []
        best = "0000"
        for ln in lines:
            if ln.startswith("bestmove"):
                parts = ln.split()
                if len(parts) >= 2:
                    best = parts[1]
            elif ln.startswith("info string"):
                strings.append(ln[len("info string"):].strip())
            elif ln.startswith("info "):
                infos.append(_parse_info(ln))
        return GoResult(bestmove=best, infos=infos, strings=strings)

    def close(self) -> None:
        try:
            self.send("quit")
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def _parse_info(line: str) -> InfoLine:
    tok = line.split()
    info = InfoLine(raw=line)
    i = 1
    while i < len(tok):
        t = tok[i]
        if t == "depth" and i + 1 < len(tok):
            info.depth = int(tok[i + 1]); i += 2
        elif t == "multipv" and i + 1 < len(tok):
            info.multipv = int(tok[i + 1]); i += 2
        elif t == "nodes" and i + 1 < len(tok):
            info.nodes = int(tok[i + 1]); i += 2
        elif t == "score" and i + 2 < len(tok):
            kind, val = tok[i + 1], int(tok[i + 2])
            if kind == "cp":
                info.score_cp = val
            elif kind == "mate":
                info.score_mate = val
            i += 3
        elif t == "pv":
            info.pv = tok[i + 1:]
            break
        else:
            i += 1
    return info


class FenRefused(RuntimeError):
    pass


def check_fen(engine: Engine, fen: str) -> None:
    """The trap the brief names: a refused FEN manufactures a pass.

    `position` reports `invalid FEN` on the command channel, not in search
    output, so it must be read back explicitly.
    """
    engine.send(f"position fen {fen}")
    engine.send("isready")
    lines = engine._read_until(lambda ln: ln.strip() == "readyok")
    for ln in lines:
        if "invalid FEN" in ln or "illegal move" in ln:
            raise FenRefused(f"{fen!r} refused: {ln.strip()}")

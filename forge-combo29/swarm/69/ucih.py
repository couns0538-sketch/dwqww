"""Interactive UCI driver for the Forge determinism audit (swarm seat 69).

Why this exists: piping `printf 'go depth 6\n' | forge` and closing stdin makes the
engine see EOF during the search. It then publishes a fabricated legal move
(`bestmove a2a3` from startpos) and prints NO `info depth` line at all. That answer is
perfectly reproducible, so it looks like a measurement. This driver keeps stdin open
and blocks on `bestmove` with a timeout instead.

Every search is guarded by four rules from the brief:
  * FEN is validated with python-chess BEFORE it is sent;
  * the reply to `position` is scanned for `invalid FEN` AND the `go` output is
    scanned for it, because the diagnostic lands in the position reply when an
    `isready` follows `position` and in the `go` output when it does not;
  * we wait for `bestmove` with a timeout, never for `info depth`;
  * `go infinite` always gets an explicit `stop`.
"""

import os
import queue
import subprocess
import sys
import threading
import time

import chess

INVALID_MARKERS = ("invalid FEN", "illegal move", "unknown option", "invalid value", "ERROR")


class EngineError(RuntimeError):
    pass


class Engine:
    def __init__(self, exe, cwd=None, env=None, timeout=180.0, prefix=None):
        self.exe = exe
        self.timeout = timeout
        run_env = dict(os.environ if env is None else env)
        self.proc = subprocess.Popen(
            list(prefix or ()) + [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            env=run_env,
            text=True,
            bufsize=1,
        )
        self._q = queue.Queue()
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()
        self.name = None
        self.options = []

    def _pump(self):
        for line in self.proc.stdout:
            self._q.put(line.rstrip("\n"))
        self._q.put(None)

    def send(self, line):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, token, timeout=None):
        """Collect lines up to and including one that starts with `token`."""
        limit = self.timeout if timeout is None else timeout
        out = []
        deadline = time.monotonic() + limit
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineError("timeout waiting for %r after %d lines" % (token, len(out)))
            try:
                line = self._q.get(timeout=remaining)
            except queue.Empty:
                raise EngineError("timeout waiting for %r after %d lines" % (token, len(out)))
            if line is None:
                raise EngineError("engine closed stdout while waiting for %r" % token)
            out.append(line)
            if line.split(" ", 1)[0] == token or line == token:
                return out

    def uci(self):
        self.send("uci")
        lines = self.read_until("uciok", timeout=30)
        for line in lines:
            if line.startswith("id name "):
                self.name = line[len("id name "):]
            elif line.startswith("option name "):
                self.options.append(line)
        return lines

    def sync(self, context):
        """Send isready and return every line up to readyok, checking for diagnostics."""
        self.send("isready")
        lines = self.read_until("readyok", timeout=60)
        for line in lines:
            for marker in INVALID_MARKERS:
                if marker in line:
                    raise EngineError("%s: engine said %r" % (context, line))
        return lines

    def setoption(self, name, value=None):
        if value is None:
            self.send("setoption name %s" % name)
        else:
            self.send("setoption name %s value %s" % (name, value))
        self.sync("setoption %s" % name)

    def position_fen(self, fen):
        board = chess.Board(fen)  # raises on an illegal FEN, before we send it
        del board
        self.send("position fen %s" % fen)
        reply = self.sync("position")
        for line in reply:
            if "invalid FEN" in line:
                raise EngineError("refused FEN: %s" % fen)
        return reply

    def position_startpos(self, moves=()):
        cmd = "position startpos"
        if moves:
            cmd += " moves " + " ".join(moves)
        self.send(cmd)
        reply = self.sync("position")
        for line in reply:
            if "invalid FEN" in line or "illegal move" in line:
                raise EngineError("refused position: %s" % cmd)
        return reply

    def newgame(self):
        self.send("ucinewgame")
        self.sync("ucinewgame")

    def clear_hash(self):
        self.setoption("Clear Hash")

    def go(self, command, stop_after=None):
        """Run one search. Returns dict(bestmove, nodes, score, depth, lines, elapsed)."""
        if not command.startswith("go "):
            raise EngineError("go() wants a `go ...` command")
        infinite = "infinite" in command.split()
        if infinite and stop_after is None:
            raise EngineError("`go infinite` needs an explicit Stop_after delay")
        start = time.monotonic()
        self.send(command)
        if infinite:
            time.sleep(stop_after)
            self.send("stop")
        lines = self.read_until("bestmove", timeout=self.timeout)
        elapsed = time.monotonic() - start

        for line in lines:
            if "invalid FEN" in line:
                raise EngineError("go output carried `invalid FEN`")

        nodes = None
        score = None
        depth = None
        for line in lines:
            if not line.startswith("info depth "):
                continue
            fields = line.split()
            info = {}
            i = 1
            while i + 1 < len(fields):
                if fields[i] in ("depth", "seldepth", "nodes", "nps", "hashfull", "time", "tbhits"):
                    try:
                        info[fields[i]] = int(fields[i + 1])
                    except ValueError:
                        pass
                    i += 2
                else:
                    i += 1
            if "nodes" in info:
                nodes = info["nodes"]
            if "depth" in info:
                depth = info["depth"]
            if "score" in fields:
                j = fields.index("score")
                if j + 2 < len(fields):
                    kind = fields[j + 1]
                    try:
                        val = int(fields[j + 2])
                    except ValueError:
                        val = None
                    if val is not None:
                        score = "%s %d" % (kind, val)

        best = None
        for line in lines:
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2:
                    best = parts[1]

        return {
            "bestmove": best,
            "nodes": nodes,
            "score": score,
            "depth": depth,
            "elapsed": elapsed,
            "lines": lines,
            "n_info": sum(1 for l in lines if l.startswith("info depth ")),
        }

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def search_once(exe, fen, go_cmd, options=(), fresh=True, timeout=180.0, cwd=None, env=None):
    """One fresh process: uci, options, position, go. Returns the go() dict."""
    engine = Engine(exe, cwd=cwd, env=env, timeout=timeout)
    try:
        engine.uci()
        for name, value in options:
            engine.setoption(name, value)
        if fen is None:
            engine.position_startpos()
        else:
            engine.position_fen(fen)
        return engine.go(go_cmd)
    finally:
        engine.close()


def lone_king(board):
    """True when either side has no pieces but its king (the PC patch's root predicate)."""
    for color in (chess.WHITE, chess.BLACK):
        pieces = board.piece_map()
        own = [p for p, piece in pieces.items() if piece.color == color]
        if len(own) == 1 and pieces[own[0]].piece_type == chess.KING:
            return True
    return False


def validate_fens(path):
    """Read a FEN/EPD list, return (valid, invalid) with python-chess as the judge."""
    valid, invalid = [], []
    with open(path) as handle:
        for raw in handle:
            fen = raw.strip()
            if not fen or fen.startswith("#"):
                continue
            fields = fen.split()
            core = " ".join(fields[:6]) if len(fields) >= 6 else fen
            try:
                board = chess.Board(core)
            except Exception as exc:  # noqa: BLE001 - we want every failure class
                invalid.append((fen, str(exc)))
                continue
            if not board.is_valid():
                invalid.append((fen, "not valid: " + str(board.status())))
                continue
            valid.append(core)
    return valid, invalid


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("usage: ucih.py EXE FEN 'go depth 8'", file=sys.stderr)
        raise SystemExit(2)
    result = search_once(sys.argv[1], None if sys.argv[2] == "-" else sys.argv[2], sys.argv[3])
    print({k: v for k, v in result.items() if k != "lines"})

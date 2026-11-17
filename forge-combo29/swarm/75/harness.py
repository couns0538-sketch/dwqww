"""Synchronized UCI harness for the Forge evaluation audit (seat 75).

Protocol rules enforced here (from the measured correction):
  * `info string invalid FEN` is emitted in the POSITION reply when an
    `isready` follows it, and in the `go` output when it does not.
    Every read therefore scans BOTH streams.
  * A rejected FEN leaves the engine on the PREVIOUS board. Any caller that
    does not notice would silently measure the wrong position, so a rejected
    FEN raises instead of returning a number.
  * No search is ever left open: every `go` is drained to `bestmove` or to a
    hard timeout, and the timeout is an error, not a score.
"""

from __future__ import annotations

import queue
import subprocess
import threading
import time

import chess

ENGINE = "/tmp/build75/forge"
POSITION_TIMEOUT = 20.0
SEARCH_TIMEOUT = 180.0


class EngineError(RuntimeError):
    """Raised when the engine refuses input or does not answer in time."""


class InvalidFen(EngineError):
    """The engine rejected a FEN and kept the previous board."""


def parse_fen(fen: str) -> chess.Board:
    """Validate a FEN string as text, then as a position.

    chess.Board() silently pads a five-field FEN and its .fen() always returns
    six fields, so a board object alone cannot prove the caller's text was
    well formed. The raw string is checked here, before construction.
    """
    if not isinstance(fen, str):
        raise EngineError(f"FEN must be a string, got {type(fen).__name__}")
    if len(fen.split()) != 6:
        raise EngineError(f"FEN must have six fields: {fen!r}")
    try:
        board = chess.Board(fen)
    except ValueError as exc:
        raise EngineError(f"python-chess rejects this FEN: {fen!r} ({exc})") from None
    if not board.is_valid():
        raise EngineError(f"python-chess rejects this position: {fen!r} status={board.status()!r}")
    if board.fen() != fen:
        raise EngineError(f"FEN is not in canonical form: {fen!r} -> {board.fen()!r}")
    return board


class Forge:
    """One engine process, one thread, strictly request/response."""

    def __init__(self, path: str = ENGINE, options: dict[str, str] | None = None):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str] = queue.Queue()
        self.reader = threading.Thread(target=self._pump, daemon=True)
        self.reader.start()
        self.diagnostics: list[str] = []

        self.send("uci")
        self.wait_for("uciok", 20.0)
        # Threads 1 and a fixed hash are mandatory: every comparison in this
        # audit is measured under the same settings.
        base = {"Threads": "1", "Hash": "16", "OwnBook": "false"}
        if options:
            base.update(options)
        for name, value in base.items():
            self.send(f"setoption name {name} value {value}")
        self.sync()

    # -- transport ---------------------------------------------------------
    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\r\n"))
        self.lines.put("<<eof>>")

    def send(self, command: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def read_until(self, token: str, timeout: float) -> list[str]:
        out: list[str] = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineError(f"timeout waiting for {token!r}; got {out!r}")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty:
                raise EngineError(f"timeout waiting for {token!r}; got {out!r}") from None
            if line == "<<eof>>":
                raise EngineError(f"engine exited while waiting for {token!r}; got {out!r}")
            out.append(line)
            if line == token:
                return out

    def wait_for(self, token: str, timeout: float) -> list[str]:
        return self.read_until(token, timeout)

    def sync(self) -> list[str]:
        """Barrier: everything queued before this call is returned.

        The rejection scan lives HERE, in the transport, rather than only in the
        position/eval helpers: a caller that talks to the engine directly then
        still cannot consume an `invalid FEN` silently.
        """
        self.send("isready")
        reply = self.read_until("readyok", POSITION_TIMEOUT)
        self._scan_for_rejection(reply)
        return reply

    def _scan_for_rejection(self, lines: list[str]) -> None:
        """Raise on any engine refusal found in a reply stream."""
        for line in lines:
            if "invalid FEN" in line:
                self.diagnostics.append(line)
                raise InvalidFen(line)
            for marker in ("illegal move", "invalid value for option",
                           "searchmoves restriction has no legal root moves"):
                if marker in line:
                    self.diagnostics.append(line)
                    raise EngineError(line)

    # -- position ----------------------------------------------------------
    def set_position(self, board: chess.Board) -> None:
        """Send a position and prove the engine accepted exactly it."""
        # Local validation first: a FEN that python-chess rejects can never be a
        # legitimate fixture, and python-chess is the audit's independent oracle.
        board = board.copy()
        fen = board.fen()
        parsed = parse_fen(fen)

        self.send(f"position fen {fen}")
        reply = self.sync()
        self._scan_for_rejection(reply)

        # Second, independent proof that the engine holds THIS board: its own
        # `eval` reports the in-check flag, and a mismatch is a fixture bug.
        probe = self.eval_raw()
        if probe["incheck"] != parsed.is_check():
            raise EngineError(
                f"engine board disagrees with python-chess on check for {fen!r}: "
                f"engine incheck={probe['incheck']} python-chess={parsed.is_check()}"
            )

    def new_game(self) -> None:
        self.send("ucinewgame")
        self.sync()

    # -- evaluation --------------------------------------------------------
    def eval_raw(self) -> dict:
        """Static evaluation, side-to-move relative.

        `eval` prints `info string eval hce H nnue N total T [incheck 1]`
        followed by nothing else, so an `isready` barrier terminates it.
        """
        self.send("eval")
        reply = self.sync()
        self._scan_for_rejection(reply)
        for line in reply:
            if "info string eval" not in line:
                continue
            fields = line.split()
            # info string eval hce <h> nnue <n> total <t> [incheck 1]
            out = {"raw": line, "hce": None, "nnue": None, "total": None, "incheck": False}
            i = 3
            while i + 1 < len(fields):
                key, value = fields[i], fields[i + 1]
                if key in ("hce", "nnue", "total"):
                    out[key] = int(value)
                    i += 2
                elif key == "incheck":
                    out["incheck"] = value == "1"
                    i += 2
                else:
                    i += 1
            if out["total"] is None:
                raise EngineError(f"eval line had no total: {line!r}")
            return out
        raise EngineError(f"no eval line in reply: {reply!r}")

    def evaluate(self, board: chess.Board) -> dict:
        self.set_position(board)
        return self.eval_raw()

    # -- search ------------------------------------------------------------
    def search(self, board: chess.Board, depth: int, movetime: float | None = None) -> dict:
        """Fixed-depth search. Returns the final score line and bestmove."""
        self.set_position(board)
        if movetime is None:
            self.send(f"go depth {depth}")
        else:
            self.send(f"go depth {depth} movetime {int(movetime)}")
        out: list[str] = []
        deadline = time.monotonic() + SEARCH_TIMEOUT
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.send("stop")
                raise EngineError(f"search timed out waiting for bestmove: {out[-3:]!r}")
            try:
                line = self.lines.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                continue
            if line == "<<eof>>":
                raise EngineError("engine exited during search")
            out.append(line)
            if line.startswith("bestmove"):
                break
        self._scan_for_rejection(out)

        best: dict = {"bestmove": out[-1].split()[1] if len(out[-1].split()) > 1 else None,
                      "score": None, "depth": None, "nodes": None, "raw": out}
        for line in out:
            if not line.startswith("info ") or " score " not in line:
                continue
            fields = line.split()
            entry = {"depth": None, "score": None}
            for i, tok in enumerate(fields):
                if tok == "depth" and i + 1 < len(fields):
                    entry["depth"] = int(fields[i + 1])
                elif tok == "nodes" and i + 1 < len(fields):
                    entry["nodes"] = int(fields[i + 1])
                elif tok == "score" and i + 2 < len(fields):
                    kind, value = fields[i + 1], fields[i + 2]
                    # Mate scores are kept distinct from centipawn scores so a
                    # magnitude test can never pass off "mate 0" as "0 cp".
                    entry["score"] = {"type": kind, "value": int(value)}
            if entry["score"] is not None:
                best.update(entry)
        if best["score"] is None:
            raise EngineError(f"no score line from search on {board.fen()!r}")
        return best

    # -- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        try:
            self.send("quit")
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()

    def __enter__(self) -> "Forge":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# -- mirroring -------------------------------------------------------------

def mirror_board(board: chess.Board) -> chess.Board:
    """Colour-mirror: swap colours and reflect ranks. Side to move is preserved."""
    fen = board.fen()
    placement, stm, castling, ep, halfmove, fullmove = fen.split()
    mirrored_ranks = []
    for rank in reversed(placement.split("/")):
        row = "".join(ch.swapcase() if ch.isalpha() else ch for ch in rank)
        mirrored_ranks.append(row)
    new_placement = "/".join(mirrored_ranks)
    new_stm = "b" if stm == "w" else "w"
    new_castling = castling.swapcase() if castling != "-" else "-"
    if new_castling != "-":
        # Keep the canonical KQkq order after the case swap.
        new_castling = "".join(c for c in "KQkq" if c in new_castling)
    if ep != "-":
        square = chess.parse_square(ep)
        new_ep = chess.square_name(chess.square_mirror(square))
    else:
        new_ep = "-"
    return chess.Board(f"{new_placement} {new_stm} {new_castling} {new_ep} {halfmove} {fullmove}")


def verify_mirror(board: chess.Board) -> None:
    """The mirror must be a legal position, and mirroring twice must be identity."""
    mirrored = mirror_board(board)
    # python-chess validates on construction; force the check explicitly.
    if not mirrored.is_valid():
        raise EngineError(f"mirror of {board.fen()!r} is not a legal position: {mirrored.fen()!r}")
    back = mirror_board(mirrored)
    if back.fen() != board.fen():
        raise EngineError(f"mirror is not an involution: {board.fen()!r} -> {back.fen()!r}")


def piece_count(board: chess.Board, color: chess.Color, piece_type: chess.PieceType) -> int:
    return len(board.pieces(piece_type, color))

"""A strict, documented-UCI-only consumer for the Forge engine.

The client's rules, restated so the code can be read against them:

  * It sends only `uci`, `isready`, `setoption`, `ucinewgame`, `position`, `go`, `stop`, `quit`.
  * Every decision comes from engine stdout.  The client keeps its own board, but only to
    (a) generate the `position ... moves` line it must send, and (b) verify what arrived.
  * It assumes nothing the UCI specification does not promise.  The one place it must go
    beyond the text is the null-token convention (`0000`), which is flagged as C4/C18.

Each assumption from ASSUMPTIONS.md is a check here, and every check appends to
`self.violations` rather than raising, so one bad reply does not lose the rest of a game's
evidence.  A violation that leaves the client without a usable move ends the game and is
reported as a protocol failure; a violation that leaves a usable move is reported but the
game continues.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import chess

from engine import Engine, EngineDied, EngineTimeout

# Categories a reply can fall into, decided from stdout alone.
BOOK = "BOOK"                 # `info string book move X` + bestmove, no depth, no score
NORMAL = "NORMAL"             # at least one `info depth` line with a score and a non-empty pv
BAIL = "BAIL"                 # a real move, nodes 0, EMPTY pv  -> sec 1b: no move was chosen
NO_MOVE_MATE = "NO_MOVE_MATE"  # 0000 with `score mate 0`     -> checkmate
NO_MOVE_DRAW = "NO_MOVE_DRAW"  # 0000 with `score cp 0`       -> stalemate / empty restriction
UNSEARCHED = "UNSEARCHED"     # bestmove with zero info lines
UNPARSED = "UNPARSED"         # bestmove payload is not a move and not 0000
HANG = "HANG"                 # no bestmove inside the client's deadline


@dataclass
class InfoLine:
    depth: int | None = None
    seldepth: int | None = None
    nodes: int | None = None
    nps: int | None = None
    time_ms: int | None = None
    multipv: int | None = None
    score_kind: str | None = None   # "cp" or "mate"
    score: int | None = None
    pv: list[str] = field(default_factory=list)
    has_pv_token: bool = False
    text: str = ""


@dataclass
class Reply:
    category: str
    bestmove: str | None = None
    ponder: str | None = None
    infos: list[InfoLine] = field(default_factory=list)
    strings: list[str] = field(default_factory=list)
    elapsed: float = 0.0
    deadline: float = 0.0
    raw: list[str] = field(default_factory=list)
    double_bestmove: bool = False

    @property
    def last(self) -> InfoLine | None:
        return self.infos[-1] if self.infos else None

    @property
    def score(self) -> tuple[str, int] | None:
        li = self.last
        if li is None or li.score_kind is None or li.score is None:
            return None
        return (li.score_kind, li.score)

    @property
    def has_score(self) -> bool:
        return self.score is not None

    @property
    def pv(self) -> list[str]:
        return self.last.pv if self.last else []


def parse_info(text: str) -> InfoLine:
    li = InfoLine(text=text)
    tok = text.split()
    i = 0
    while i < len(tok):
        t = tok[i]
        if t == "depth" and i + 1 < len(tok):
            li.depth = _int(tok[i + 1]); i += 2
        elif t == "seldepth" and i + 1 < len(tok):
            li.seldepth = _int(tok[i + 1]); i += 2
        elif t == "nodes" and i + 1 < len(tok):
            li.nodes = _int(tok[i + 1]); i += 2
        elif t == "nps" and i + 1 < len(tok):
            li.nps = _int(tok[i + 1]); i += 2
        elif t == "time" and i + 1 < len(tok):
            li.time_ms = _int(tok[i + 1]); i += 2
        elif t == "multipv" and i + 1 < len(tok):
            li.multipv = _int(tok[i + 1]); i += 2
        elif t == "score" and i + 2 < len(tok):
            li.score_kind = tok[i + 1]
            li.score = _int(tok[i + 2])
            i += 3
        elif t == "pv":
            li.has_pv_token = True
            li.pv = tok[i + 1:]
            break
        else:
            i += 1
    return li


def _int(s: str) -> int | None:
    try:
        return int(s)
    except ValueError:
        return None


class Client:
    """One engine process, spoken to in documented UCI only."""

    def __init__(self, path: str, *, log=None) -> None:
        self.path = path
        self.eng = Engine(path)
        self.violations: list[dict] = []
        self.notes: list[str] = []
        self.assumptions_checked: dict[str, int] = {}
        self._log = log or (lambda *a: None)

    # -- assumption bookkeeping --------------------------------------------
    def note(self, aid: str, ok: bool, detail: str, *, fatal: bool = False) -> None:
        self.assumptions_checked[aid] = self.assumptions_checked.get(aid, 0) + 1
        if not ok:
            self.violations.append({"assumption": aid, "detail": detail, "fatal": fatal})

    # -- handshake ----------------------------------------------------------
    def shake(self, timeout: float = 20.0) -> bool:
        self.eng.send("uci")
        try:
            wires = self.eng.read_until(lambda w: w.text.strip() == "uciok", timeout)
        except (EngineTimeout, EngineDied) as e:
            self.note("C1", False, f"no uciok: {e}", fatal=True)
            return False
        lines = [w.text for w in wires]
        stray = [ln for ln in lines[:-1] if not (ln.startswith("id ") or ln.startswith("option ")
                                                 or ln.startswith("info string"))]
        self.note("C1", not stray, f"unexpected lines before uciok: {stray[:3]}")
        self.options = {ln.split()[2]: ln for ln in lines if ln.startswith("option name ")}
        return True

    def isready(self, timeout: float = 20.0) -> bool:
        self.eng.send("isready")
        try:
            self.eng.read_until(lambda w: w.text.strip() == "readyok", timeout)
            return True
        except (EngineTimeout, EngineDied) as e:
            self.note("C2", False, f"no readyok: {e}", fatal=True)
            return False

    def newgame(self) -> None:
        self.eng.send("ucinewgame")
        self.isready()

    def setoption(self, name: str, value: str) -> None:
        self.eng.send(f"setoption name {name} value {value}")

    def set_position(self, board: chess.Board) -> None:
        # Built from the client's own board: a UCI client must remember the moves.
        hist = board.move_stack
        if not hist:
            self.eng.send("position startpos")
            return
        root = board.root()
        if root.fen() == chess.Board().fen():
            self.eng.send("position startpos moves " + " ".join(m.uci() for m in hist))
        else:
            self.eng.send(f"position fen {root.fen()} moves " + " ".join(m.uci() for m in hist))

    def go(self, **limits: int) -> None:
        parts = ["go"]
        for k, v in limits.items():
            parts.append(f"{k} {v}")
        self.eng.send(" ".join(parts))

    def stop(self) -> None:
        self.eng.send("stop")

    # -- the one read that matters -----------------------------------------
    def read_reply(self, deadline: float) -> Reply:
        """Collect stdout until the first `bestmove`, bounded by `deadline` seconds."""
        start = time.monotonic()
        try:
            wires = self.eng.read_until(lambda w: w.text.startswith("bestmove"), deadline)
        except EngineTimeout:
            raw = [w.text for w in self.eng.drain_now()]
            return Reply(category=HANG, elapsed=time.monotonic() - start,
                         deadline=deadline, raw=raw)
        except EngineDied as e:
            raw = [w.text for w in self.eng.drain_now()]
            r = Reply(category=HANG, elapsed=time.monotonic() - start, deadline=deadline, raw=raw)
            self.note("C3", False, f"stdout died before bestmove: {e}", fatal=True)
            return r
        elapsed = time.monotonic() - start
        raw = [w.text for w in wires]

        infos = [parse_info(t) for t in raw if t.startswith("info depth")]
        strings = [t[len("info string "):] for t in raw if t.startswith("info string ")]
        bm_line = raw[-1]
        tok = bm_line.split()
        bestmove = tok[1] if len(tok) > 1 else None
        ponder = tok[3] if len(tok) > 3 and tok[2] == "ponder" else None

        # C3: exactly one bestmove.  A second one with no command sent is a violation.
        # The probe is cheap: after the bestmove the engine is idle, so a short quiet
        # window is enough; this runs once per move in a long match, so it must not
        # cost a quarter second each time.
        extra = self.eng.drain_idle(quiet_for=0.02, cap=0.1)
        extra_bm = [w.text for w in extra if w.text.startswith("bestmove")]
        if extra_bm:
            self.note("C3", False, f"second bestmove without a command: {extra_bm[:1]}", fatal=False)
        raw.extend(w.text for w in extra)

        return Reply(
            category=self._classify(bestmove, infos, strings),
            bestmove=bestmove,
            ponder=ponder,
            infos=infos,
            strings=strings,
            elapsed=elapsed,
            deadline=deadline,
            raw=raw,
            double_bestmove=bool(extra_bm),
        )

    @staticmethod
    def _classify(bestmove: str | None, infos: list[InfoLine], strings: list[str]) -> str:
        if bestmove is None or not _looks_like_move(bestmove):
            return UNPARSED
        if bestmove == "0000":
            kind = None
            for li in reversed(infos):
                if li.score_kind is not None:
                    kind = (li.score_kind, li.score)
                    break
            if kind == ("mate", 0):
                return NO_MOVE_MATE
            return NO_MOVE_DRAW
        if any(s.startswith("book move") for s in strings):
            return BOOK
        if not infos:
            return UNSEARCHED
        last = infos[-1]
        if last.nodes == 0 and last.has_pv_token and not last.pv:
            return BAIL
        if not last.has_pv_token or not last.pv:
            return BAIL
        return NORMAL

    # -- verification of a reply against the client's own board -------------
    def verify(self, reply: Reply, board: chess.Board, *, allow_bail_play: bool = False) -> dict:
        """Return {'usable': bool, 'play': uci|None, 'why': str}.  Records violations."""
        out = {"usable": False, "play": None, "why": "", "category": reply.category}

        if reply.category == HANG:
            self.note("C12", False,
                      f"no bestmove within {reply.deadline:.2f}s (last info: "
                      f"{reply.last.text if reply.last else 'none'})", fatal=True)
            out["why"] = "hang"
            return out

        if reply.category == UNPARSED:
            self.note("C4", False, f"bestmove payload not a move and not 0000: {reply.bestmove!r}",
                      fatal=True)
            out["why"] = "unparsed"
            return out

        # --- no-move replies -------------------------------------------------
        if reply.category in (NO_MOVE_MATE, NO_MOVE_DRAW):
            legal = list(board.legal_moves)
            if legal:
                # The client's own board disagrees with the engine's "no move".
                self.note("C18", False,
                          f"{reply.bestmove} on a board with {len(legal)} legal moves "
                          f"(score {reply.score})", fatal=True)
                out["why"] = "null-token-on-live-board"
                return out
            out["usable"] = True
            out["play"] = None
            out["why"] = "game_over"
            return out

        # --- a real move ------------------------------------------------------
        try:
            move = chess.Move.from_uci(reply.bestmove)
        except ValueError:
            self.note("C4", False, f"unparseable move {reply.bestmove!r}", fatal=True)
            out["why"] = "unparsed"
            return out
        if move not in board.legal_moves:
            self.note("C5", False, f"illegal move {reply.bestmove} in {board.fen()}", fatal=True)
            out["why"] = "illegal"
            return out

        if reply.category == BAIL:
            # sec 1b: a real move, nodes 0, empty pv is "no move was chosen".
            # The depth ladder still has to be checked here: this is the ONLY path where
            # the engine reports a depth it never searched, so a C7 check that ran only on
            # NORMAL replies could never fire on the one path that needs it.
            self._check_depth(reply)
            self.note("C11", False,
                      f"empty pv with nodes {reply.last.nodes if reply.last else '?'} "
                      f"and move {reply.bestmove}")
            if not allow_bail_play:
                out["why"] = "bail"
                out["play"] = None
                return out
            self.notes.append(f"played a bail move {reply.bestmove} (allow_bail_play)")
            out["play"] = reply.bestmove
            out["usable"] = True
            out["why"] = "bail-played"
            return out

        if reply.category in (BOOK, UNSEARCHED):
            # C6/C22: no depth line / no score.  Recorded, not fatal: the move is legal.
            self.note("C6", False, f"{reply.category}: no info depth line before {reply.bestmove}")
            self.note("C22", False, f"{reply.category}: no score for the returned move")
            out["play"] = reply.bestmove
            out["usable"] = True
            out["why"] = reply.category.lower()
            return out

        # --- NORMAL: check the promises a client leans on ---------------------
        self._check_depth(reply)
        self._check_nodes(reply)
        self._check_nps(reply)
        if reply.pv and reply.pv[0] != reply.bestmove:
            self.note("C10", False,
                      f"pv[0]={reply.pv[0]} but bestmove={reply.bestmove} (score {reply.score})")
        out["play"] = reply.bestmove
        out["usable"] = True
        out["why"] = "normal"
        return out

    def _check_depth(self, reply: Reply) -> None:
        depths = [li.depth for li in reply.infos if li.depth is not None]
        if not depths:
            self.note("C7", False, "info lines with no depth field")
            return
        if any(b < a for a, b in zip(depths, depths[1:])):
            self.note("C20", False, f"depth went backwards: {depths}")
        last = reply.last
        if last and last.nodes == 0 and len(depths) > 1:
            # sec 1b: the line count on a bailed root is not a depth.
            self.note("C7", False,
                      f"reported depth {depths[-1]} over {len(depths)} lines with nodes 0")

    def _check_nodes(self, reply: Reply) -> None:
        last = reply.last
        if last is None:
            return
        if last.nodes == 0 and last.pv:
            self.note("C8", False, f"nodes 0 but a pv was given: {last.pv[:3]}")

    def _check_nps(self, reply: Reply) -> None:
        for li in reply.infos:
            if li.nps not in (None, 0) and li.nodes == 0:
                self.note("C21", False, f"nps {li.nps} with nodes 0")

    def close(self) -> None:
        self.eng.quit()


def _looks_like_move(token: str) -> bool:
    if token == "0000":
        return True
    if len(token) not in (4, 5):
        return False
    return all(c in "abcdefgh12345678" for c in token[:4]) and (len(token) == 4 or token[4] in "qrbn")

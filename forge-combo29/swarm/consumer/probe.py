"""Probe every wire path the client can reach, and record exactly what arrived.

Contract: this script makes NO judgement about whether a reply is good.  It records
lines, arrival times, and which deadline fired.  `analyse.py` reads the JSON and
applies the assumptions.

Usage:  python3 probe.py ENGINE_PATH OUT.json
"""

from __future__ import annotations

import json
import sys
import time

from engine import Engine, EngineDied, EngineTimeout


def enc(text: str) -> str:
    """Escape control characters so a NUL/tab/newline echoed by the engine cannot
    make the evidence file unreadable (trap 3a000)."""
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"<U+{ord(ch):04X}>")
        else:
            out.append(ch)
    return "".join(out)


class Case:
    def __init__(self, name: str, engine_path: str, note: str = "") -> None:
        self.name = name
        self.note = note
        self.engine_path = engine_path
        self.sent: list[tuple[float, str]] = []
        self.lines: list[dict] = []
        self.events: list[dict] = []
        self.eng: Engine | None = None
        self.t0 = time.monotonic()

    # -- recording ----------------------------------------------------------
    def _record(self, wires) -> None:
        for w in wires:
            self.lines.append({"t": round(w.t - self.t0, 6), "text": enc(w.text)})

    def open(self) -> None:
        self.eng = Engine(self.engine_path)
        self.t0 = time.monotonic()
        self.send("uci")
        try:
            self._record(self.eng.read_until(lambda w: w.text.strip() == "uciok", 20.0))
            self.events.append({"what": "uciok", "ok": True})
        except (EngineTimeout, EngineDied) as e:
            self._record(self.eng.drain_now())
            self.events.append({"what": "uciok", "ok": False, "error": str(e)})

    def send(self, line: str) -> None:
        assert self.eng is not None
        self.sent.append((round(time.monotonic() - self.t0, 6), enc(line)))
        self.eng.send(line)

    def isready(self, timeout: float = 10.0) -> bool:
        self.send("isready")
        try:
            self._record(self.eng.read_until(lambda w: w.text.strip() == "readyok", timeout))
            self.events.append({"what": "readyok", "ok": True})
            return True
        except (EngineTimeout, EngineDied) as e:
            self._record(self.eng.drain_now())
            self.events.append({"what": "readyok", "ok": False, "error": str(e)})
            return False

    def expect_bestmove(self, timeout: float) -> dict:
        """Wait for the first bestmove.  Record whether a second ever arrives."""
        start = time.monotonic()
        try:
            wires = self.eng.read_until(lambda w: w.text.startswith("bestmove"), timeout)
            self._record(wires)
            elapsed = time.monotonic() - start
            self.events.append({"what": "bestmove", "ok": True, "elapsed": round(elapsed, 6)})
            # does a second bestmove follow with no further command sent?
            extra = self.eng.drain_idle(quiet_for=0.5, cap=3.0)
            self._record(extra)
            dupes = [w.text for w in extra if w.text.startswith("bestmove")]
            if dupes:
                self.events.append({"what": "extra_bestmove", "count": len(dupes), "lines": [enc(d) for d in dupes]})
            return {"bestmove": True, "elapsed": round(elapsed, 6), "timeout": timeout}
        except EngineTimeout:
            elapsed = time.monotonic() - start
            self._record(self.eng.drain_now())
            self.events.append({"what": "bestmove", "ok": False, "elapsed": round(elapsed, 6), "error": "timeout"})
            return {"bestmove": False, "elapsed": round(elapsed, 6), "timeout": timeout, "error": "timeout"}
        except EngineDied as e:
            self._record(self.eng.drain_now())
            self.events.append({"what": "bestmove", "ok": False, "error": str(e)})
            return {"bestmove": False, "error": str(e)}

    def close(self) -> None:
        if self.eng is not None:
            rc = self.eng.quit()
            self.events.append({"what": "quit", "rc": rc})
        self.eng = None

    def as_dict(self) -> dict:
        return {
            "case": self.name,
            "note": self.note,
            "sent": [{"t": t, "text": s} for t, s in self.sent],
            "lines": self.lines,
            "events": self.events,
        }


# -- case bodies ------------------------------------------------------------

STARTPOS = "position startpos"
MIDGAME = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
BARE_KINGS = "position fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1"
FIFTY = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 100 60"
# threefold reached by move list: knights out and back twice
REPEAT_MOVES = "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"
K_R_VS_K = "position fen 7k/8/8/8/8/8/R7/K7 w - - 0 1"


def case_uci_only(path: str) -> Case:
    c = Case("uci_handshake", path, "C1: uci is answered with uciok")
    c.open()
    c.isready()
    c.send("quit")
    c.events.append({"what": "quit", "rc": c.eng.quit()})
    c.eng = None
    return c


def case_book_both_clocks(path: str) -> Case:
    c = Case("book_both_clocks", path, "book move: startpos, mover's own clock sent")
    c.open()
    c.send("setoption name OwnBook value true")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(STARTPOS)
    c.isready()
    c.send("go wtime 10000 btime 10000 winc 100 binc 100")
    c.expect_bestmove(20.0)
    c.close()
    return c


def case_book_movetime(path: str) -> Case:
    c = Case("book_movetime", path, "book move via movetime")
    c.open()
    c.send("setoption name OwnBook value true")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(STARTPOS)
    c.isready()
    c.send("go movetime 100")
    c.expect_bestmove(20.0)
    c.close()
    return c


def case_book_multipv(path: str) -> Case:
    c = Case("book_multipv3", path, "MultiPV 3 on the book path (trap 19c)")
    c.open()
    c.send("setoption name MultiPV value 3")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(STARTPOS)
    c.isready()
    c.send("go wtime 10000 btime 10000")
    c.expect_bestmove(20.0)
    c.close()
    return c


def case_drawn_bare_kings_depth(path: str) -> Case:
    c = Case("drawn_bare_kings_depth64", path, "drawn root, go depth 64 (sec 1b)")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(BARE_KINGS)
    c.isready()
    c.send("go depth 64")
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_drawn_bare_kings_time(path: str) -> Case:
    c = Case("drawn_bare_kings_time", path, "drawn root under a clock budget")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(BARE_KINGS)
    c.isready()
    c.send("go wtime 5000 btime 5000")
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_drawn_threefold(path: str) -> Case:
    c = Case("drawn_threefold_movelist", path, "drawn root reached BY MOVE LIST (trap 2d)")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(REPEAT_MOVES)
    c.isready()
    c.send("go depth 20")
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_drawn_fifty(path: str) -> Case:
    c = Case("drawn_fifty_move", path, "drawn root at halfmove 100")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(FIFTY)
    c.isready()
    c.send("go depth 20")
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_stalemate(path: str) -> Case:
    c = Case("stalemate_root", path, "stalemate: 0000 vs cp 0 discriminator")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send("position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    c.isready()
    c.send("go depth 10")
    c.expect_bestmove(20.0)
    c.close()
    return c


def case_checkmate(path: str) -> Case:
    c = Case("checkmate_root", path, "checkmate: 0000 with mate 0 must NOT be read as an error")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send("position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
    c.isready()
    c.send("go depth 10")
    c.expect_bestmove(20.0)
    c.close()
    return c


def case_normal_depth(path: str) -> Case:
    c = Case("normal_depth12", path, "normal search, go depth 12")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send("go depth 12")
    c.expect_bestmove(60.0)
    c.close()
    return c


def case_normal_time(path: str) -> Case:
    c = Case("normal_time", path, "normal search under a clock")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send("go wtime 60000 btime 60000 winc 1000 binc 1000")
    c.expect_bestmove(60.0)
    c.close()
    return c


def case_offbook_ownbook_true(path: str) -> Case:
    c = Case("offbook_ownbook_true", path, "off-book position with OwnBook true (must search)")
    c.open()
    c.send("setoption name OwnBook value true")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send("go wtime 10000 btime 10000")
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_illegal_short_fen(path: str) -> Case:
    c = Case("illegal_short_fen", path, "5-field FEN: refused? previous board re-searched?")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    before = c.eng.drain_idle(quiet_for=0.3, cap=2.0)
    c._record(before)
    c.send("position fen 8/8/8/4k3/8/8/8/4K3 w - - 0")
    c.isready()
    c.send("go depth 8")
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_illegal_surplus_fen(path: str) -> Case:
    c = Case("illegal_surplus_fen", path, "9-field FEN: silently loads? (sec 1b table)")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c._record(c.eng.drain_idle(quiet_for=0.3, cap=2.0))
    c.send("position fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1 bogus")
    c.isready()
    c.send("go depth 8")
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_position_nonsense(path: str) -> Case:
    c = Case("position_nonsense", path, "unknown position type: previous board re-searched?")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(K_R_VS_K)
    c.isready()
    c._record(c.eng.drain_idle(quiet_for=0.3, cap=2.0))
    c.send("position nonsense")
    c.isready()
    c.send("go depth 8")
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_illegal_move_token(path: str) -> Case:
    c = Case("illegal_move_token", path, "move-list truncation at a bad token (trap 3ac)")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send("position startpos moves e2e4 zzzz e7e5")
    c.isready()
    c._record(c.eng.drain_idle(quiet_for=0.3, cap=2.0))
    c.send("go depth 8")
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_one_clock_missing(path: str, deadline: float = 25.0) -> Case:
    c = Case(
        "one_clock_missing",
        path,
        "go btime only, White to move: trap 18/19 - bounded at %.0fs" % deadline,
    )
    c.open()
    c.send("setoption name OwnBook value true")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send("go btime 10000")
    res = c.expect_bestmove(deadline)
    c.events.append({"what": "one_clock_deadline", "deadline": deadline, "bounded": not res["bestmove"]})
    # recover: an explicit stop is the only documented way out
    if not res["bestmove"]:
        c.send("stop")
        try:
            c._record(c.eng.read_until(lambda w: w.text.startswith("bestmove"), 10.0))
            c.events.append({"what": "stop_recovered", "ok": True})
        except (EngineTimeout, EngineDied) as e:
            c._record(c.eng.drain_now())
            c.events.append({"what": "stop_recovered", "ok": False, "error": str(e)})
    c.close()
    return c


def case_one_clock_missing_black(path: str, deadline: float = 25.0) -> Case:
    c = Case("one_clock_missing_black", path, "go wtime only, Black to move (mirror, trap 19)")
    c.open()
    c.send("setoption name OwnBook value true")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send("position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4")
    c.isready()
    c.send("go wtime 10000")
    res = c.expect_bestmove(deadline)
    if not res["bestmove"]:
        c.send("stop")
        try:
            c._record(c.eng.read_until(lambda w: w.text.startswith("bestmove"), 10.0))
            c.events.append({"what": "stop_recovered", "ok": True})
        except (EngineTimeout, EngineDied) as e:
            c._record(c.eng.drain_now())
            c.events.append({"what": "stop_recovered", "ok": False, "error": str(e)})
    c.close()
    return c


def case_movetime_only(path: str) -> Case:
    c = Case("movetime_only_white", path, "movetime alone IS a clock (trap 18 exception)")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send("go movetime 300")
    c.expect_bestmove(20.0)
    c.close()
    return c


def case_searchmoves_legal(path: str) -> Case:
    c = Case("searchmoves_legal", path, "searchmoves with legal moves only")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send('go depth 10 searchmoves g1f3 b1c3 d2d4')
    c.expect_bestmove(40.0)
    c.close()
    return c


def case_searchmoves_mixed(path: str) -> Case:
    c = Case("searchmoves_mixed", path, "one legal + one illegal token (trap 3a00: silent drop)")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send('go depth 10 searchmoves g1f3 z9z9')
    c.expect_bestmove(40.0)
    c.close()
    return c


def case_searchmoves_all_illegal(path: str) -> Case:
    c = Case("searchmoves_all_illegal", path, "all-illegal restriction: 0000 + info string")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send('go depth 10 searchmoves z9z9 y8y8')
    c.expect_bestmove(40.0)
    c.close()
    return c


def case_searchmoves_empty(path: str) -> Case:
    c = Case("searchmoves_empty", path, "empty restriction (nothing after the token)")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send('go depth 10 searchmoves')
    c.expect_bestmove(40.0)
    c.close()
    return c


def case_nodes_zero(path: str) -> Case:
    c = Case("go_nodes_0", path, "go nodes 0: zero info lines (trap 21)")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send("go nodes 0")
    c.expect_bestmove(20.0)
    c.close()
    return c


def case_isready_during_search(path: str) -> Case:
    c = Case("isready_during_search", path, "C2: readyok must arrive while a search runs")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send("go movetime 3000")
    # send isready immediately, mid-search
    c.send("isready")
    ok = False
    start = time.monotonic()
    try:
        c._record(c.eng.read_until(lambda w: w.text.strip() == "readyok", 15.0))
        ok = True
    except (EngineTimeout, EngineDied) as e:
        c._record(c.eng.drain_now())
        c.events.append({"what": "readyok_midsearch", "ok": False, "error": str(e)})
    if ok:
        c.events.append({"what": "readyok_midsearch", "ok": True, "elapsed": round(time.monotonic() - start, 4)})
    c.expect_bestmove(30.0)
    c.close()
    return c


def case_ucinewgame_determinism(path: str) -> Case:
    c = Case("ucinewgame_determinism", path, "C17: ucinewgame resets state")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    runs = []
    for i in range(3):
        c.send("ucinewgame")
        c.isready()
        c.send(MIDGAME)
        c.isready()
        mark = len(c.lines)
        c.send("go depth 10")
        c.expect_bestmove(40.0)
        runs.append(mark)
    c.events.append({"what": "run_markers", "marks": runs})
    c.close()
    return c


def case_setoption_bad(path: str) -> Case:
    c = Case("setoption_malformed", path, "malformed setoption is reported (sec 1b table)")
    c.open()
    c.isready()
    c.send("setoption name Hash value abc")
    c.isready()
    c._record(c.eng.drain_idle(quiet_for=0.3, cap=2.0))
    c.send("setoption name NoSuchOption value 1")
    c.isready()
    c._record(c.eng.drain_idle(quiet_for=0.3, cap=2.0))
    c.close()
    return c


def case_go_depth_abc(path: str) -> Case:
    c = Case("go_depth_abc", path, "unparseable go value silently defaults (trap 3aa)")
    c.open()
    c.send("setoption name OwnBook value false")
    c.isready()
    c.send("ucinewgame")
    c.isready()
    c.send(MIDGAME)
    c.isready()
    c.send("go depth abc")
    c.expect_bestmove(40.0)
    c.close()
    return c


BUILDERS = [
    case_uci_only,
    case_book_both_clocks,
    case_book_movetime,
    case_book_multipv,
    case_drawn_bare_kings_depth,
    case_drawn_bare_kings_time,
    case_drawn_threefold,
    case_drawn_fifty,
    case_stalemate,
    case_checkmate,
    case_normal_depth,
    case_normal_time,
    case_offbook_ownbook_true,
    case_illegal_short_fen,
    case_illegal_surplus_fen,
    case_position_nonsense,
    case_illegal_move_token,
    case_one_clock_missing,
    case_one_clock_missing_black,
    case_movetime_only,
    case_searchmoves_legal,
    case_searchmoves_mixed,
    case_searchmoves_all_illegal,
    case_searchmoves_empty,
    case_nodes_zero,
    case_isready_during_search,
    case_ucinewgame_determinism,
    case_setoption_bad,
    case_go_depth_abc,
]


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    path, out = sys.argv[1], sys.argv[2]
    results = []
    for build in BUILDERS:
        try:
            c = build(path)
        except Exception as e:  # noqa: BLE001 - a crash in one case must not lose the rest
            results.append({"case": build.__name__, "error": f"{type(e).__name__}: {e}"})
            continue
        results.append(c.as_dict())
        print(f"{c.name}: {len(c.lines)} lines, {len(c.events)} events", flush=True)
    with open(out, "w") as f:
        json.dump({"engine": path, "cases": results}, f, indent=1)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

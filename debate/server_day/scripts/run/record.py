"""Fable 2026-11-23, W5 (c), (e), (f) with A23 of FINAL_PLAN_2311.md: ONE game's record, and the binding that ties
its rows to the opening really written for its game id. Standard library only. Used by the worker (it writes
records) and by the receiver at home (it reads them again and gives credit).

A record, plain ASCII, every line ends with LF:

    game <id> opening <m1> ... <m8>      the reservation: the opening that belongs to this id
    sent <the position line exactly as it was written to the engine>
    sg ...                               the engine's rows, unchanged
    sgend ...                            the engine's end line, unchanged
    bind <sha256>                        over: id LF, sent line LF, every row LF, end line LF

A game that ended inside its random plies (mate or stalemate) has `sent none`, no rows, and the end line
`openingend plies <n> reason nomoves`.

Why (A23): two legal openings can end in the SAME position and still give different games, and the engine's end
line lists only the moves played after the opening. A row file alone can therefore never show that a game was
played from another history than the one its id reserved. The worker binds, at the time of play, what it really
wrote; the receiver computes the reservation AGAIN from root seed and id and compares.

What the binding does NOT prove: that the engine played these rows from this position (that is the plan's
content parity sample, a replay), and nothing against someone who rewrites a record AND its bind line.
"""
import hashlib
import re

ID = re.compile(r"[A-Za-z0-9_]+-w\d{3}-g\d{8}")
MOVE = re.compile(r"[a-h][1-8][a-h][1-8][qrbn]?")


class RecordError(ValueError):
    """The bytes are not a sequence of whole records."""


def position_tokens(moves) -> list:
    """The position line as tokens, spelt out here a second time on purpose (never built from position_line)."""
    return ["position", "startpos"] + (["moves"] + list(moves) if moves else [])


def position_line(moves) -> str:
    return "position startpos" + (" moves " + " ".join(moves) if moves else "")


def bind(game_id: str, sent: str, rows, end: str) -> str:
    h = hashlib.sha256()
    for part in (game_id, sent, *rows, end):
        h.update(part.encode("ascii") + b"\n")
    return h.hexdigest()


def text(game_id: str, opening, sent: str, rows, end: str) -> str:
    return (f"game {game_id} opening {' '.join(opening)}".rstrip() + "\n" + f"sent {sent}\n"
            + "".join(r + "\n" for r in rows) + end + "\n" + f"bind {bind(game_id, sent, rows, end)}\n")


def parse(data: bytes) -> list:
    """Every record of a piece, in order: dicts with id, opening, sent, rows, end, bind, first (byte), last (byte).
    Raises RecordError with the line number at the first line that does not fit."""
    try:
        txt = data.decode("ascii")
    except UnicodeDecodeError as e:
        raise RecordError(f"byte {e.start} is not ASCII") from None
    if txt and not txt.endswith("\n"):
        raise RecordError("the last line has no line end (a record cut off)")
    out, g, pos = [], None, 0
    for n, ln in enumerate(txt.split("\n")[:-1], 1):
        here, pos = pos, pos + len(ln) + 1
        word = ln.split(" ", 1)[0]
        if word == "game":
            t = ln.split(" ")
            if g is not None or len(t) < 3 or not ID.fullmatch(t[1]) or t[2] != "opening" or \
                    not all(MOVE.fullmatch(m) for m in t[3:]):
                raise RecordError(f"line {n}: a game line out of place or unreadable: {ln[:80]}")
            g = {"id": t[1], "opening": t[3:], "sent": None, "rows": [], "end": None, "bind": None, "first": here}
        elif g is None:
            raise RecordError(f"line {n}: outside a record: {ln[:80]}")
        elif word == "sent":
            if g["sent"] is not None or g["rows"] or g["end"] is not None or len(ln) < 6:
                raise RecordError(f"line {n}: a sent line out of place")
            g["sent"] = ln[5:]
        elif word == "sg":
            if g["sent"] is None or g["end"] is not None:
                raise RecordError(f"line {n}: a row out of place")
            g["rows"].append(ln)
        elif word in ("sgend", "openingend"):
            if g["sent"] is None or g["end"] is not None:
                raise RecordError(f"line {n}: an end line out of place")
            g["end"] = ln
        elif word == "bind":
            if g["end"] is None or not re.fullmatch(r"bind [0-9a-f]{64}", ln):
                raise RecordError(f"line {n}: a bind line out of place or unreadable")
            g["bind"], g["last"] = ln[5:], pos
            out.append(g)
            g = None
        else:
            raise RecordError(f"line {n}: not a line of a record: {ln[:80]}")
    if g is not None:
        raise RecordError(f"the record of {g['id']} is not closed by its bind line")
    return out


def faults(g: dict, reserved=None) -> list:
    """What is wrong with one parsed record; an empty list = it may be credited. `reserved` is the opening the
    READER computed for this id by itself (root seed and id, its own move rules); None = not checked here."""
    bad = []
    if bind(g["id"], g["sent"], g["rows"], g["end"]) != g["bind"]:
        bad.append("the bind digest is not the one of this id, sent line, rows and end line")
    if g["end"].startswith("openingend "):
        if g["sent"] != "none" or g["rows"]:
            bad.append("a game that ended inside its opening has a sent line or rows")
        if not re.fullmatch(rf"openingend plies {len(g['opening'])} reason nomoves", g["end"]):
            bad.append("the opening end line does not fit the opening's length")
    else:
        if g["sent"].split(" ") != position_tokens(g["opening"]):
            bad.append("the sent line is not the position line of the record's own opening")
        m = re.match(r"sgend result (-?\d+) reason \S+ plies (\d+) run \d+ searches (\d+) nodes \d+ ", g["end"])
        if not m:
            bad.append("the end line cannot be read")
    if reserved is not None and list(reserved) != g["opening"]:
        bad.append("the opening is not the one reserved for this game id")
    return bad

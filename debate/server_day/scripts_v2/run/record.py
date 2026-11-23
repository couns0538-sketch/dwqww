"""Fable 2026-11-23, server-day plan, FORMATS.md section 0.1 (version 2 of the record, binding 2): the plain
record of ONE game, byte for byte, and the binding that ties its bytes to its run. Standard library only. Used
by the worker (it writes records) and by every reader (the worker's own restart, the packer, home).

A record, printable ASCII, every line ended by ONE LF, nothing before, between or after records:

    game <id> opening <m1> ... <mk>      the reservation: the opening that belongs to this id (k may be 0)
    sent <the position line exactly as it was written to the engine>        or:  sent none
    sg <ply> <score> <move> <six-field position>                            0 or more rows, as the engine wrote them
    sgend ...                            the engine's end line, unchanged   or:  openingend plies <k> reason nomoves
    bind <64 hex digits>

THE BINDING = sha256 over three parts in this order: the text `forge-serverday-bind-2` and LF; the run's
fingerprint (64 hex digits) and LF; every byte of the record from the `g` of `game` through the LF of the end
line. It covers the id, the OPENING (this morning's binding did not: two legal openings can end in the same
position, and the end line lists only the moves after the opening), the sent line, every row and the end
line, and it ties the record to this run's header: a record of another run, or one made under this morning's
binding, does not verify.

THE ROWS DIGEST of a game = sha256 over every row line with its LF, in order, then the line `result <-1|0|1>`
and LF with the result of the end line. It names the five fields a row gives (ply, score, move, position,
result) and nothing else; a game without rows has NO rows digest (None).

parse() refuses the BYTES (RecordError, with the name of the check in `.check`): `bytes` (anything but
printable ASCII and LF: a CR, a NUL), `final-lf` (the last line has no line end), `blank` (an empty line),
`id`, `run`, `slot`, `counter` (the name grammar of FORMATS section 0, judged before a name is used),
`structure` (a line out of place or of no kind), `row`, `end` (a line that is not in its shape) and `binding`.
faults() then says what is wrong with ONE parsed record's meaning (its sent line against its opening, the
kind of its end, the reader's own reservation); a record with a fault is set aside, the piece stays readable.

What the binding does NOT prove: that the engine played these rows from this position (that is the rules
replay and the engine replays at home), and nothing against someone who rewrites a record AND its bind line
with the run's fingerprint in hand (the seal chain and the custody receipts are what stand against that).
"""
import hashlib
import re

TAG = b"forge-serverday-bind-2\n"
_M = r"[a-h][1-8][a-h][1-8][qrbn]?"
MOVE = re.compile(_M)
_FEN = r"[1-8pnbrqkPNBRQK/]+ [wb] (?:-|[KQkq]{1,4}) (?:-|[a-h][36]) [0-9]+ [0-9]+"
ROW = re.compile(r"sg [0-9]+ -?[0-9]+ " + _M + r" " + _FEN)
END = re.compile(r"sgend result (-1|0|1) reason (mate|stalemate|rule|plylimit|matescore|evallimit|drawadj)"
                 r" plies ([0-9]+) run ([0-9]+) searches ([0-9]+) nodes ([0-9]+) fen (" + _FEN + r") moves((?: " + _M + r")*)")
OPENING_END = re.compile(r"openingend plies ([0-9]+) reason nomoves")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_RUN = re.compile(r"[a-z0-9]{1,32}")
_SLOT = re.compile(r"w[0-9]{3}")
_COUNTER = re.compile(r"g[0-9]{8}")
_PLAIN = bytes(range(0x20, 0x7f)) + b"\n"       # the only bytes a piece may hold
_LINE = re.compile(r"[ -~]*")


class RecordError(ValueError):
    """The bytes are not a sequence of whole records of this run. `.check` names the check that refused."""

    def __init__(self, check: str, text: str):
        super().__init__(f"{check}: {text}")
        self.check = check


def position_tokens(moves) -> list:
    """The position line as tokens, spelt out here a second time on purpose (never built from position_line)."""
    return ["position", "startpos"] + (["moves"] + list(moves) if moves else [])


def position_line(moves) -> str:
    return "position startpos" + (" moves " + " ".join(moves) if moves else "")


def id_parts(game_id) -> tuple:
    """(run, slot, counter) of a game id `<run>-w<NNN>-g<NNNNNNNN>`; RecordError `id`, `run`, `slot` or `counter`
    for a name that does not fit FORMATS section 0 (a counter is 1 to 99,999,999)."""
    if not isinstance(game_id, str):
        raise RecordError("id", "a game id must be a text")
    t = game_id.split("-")
    if len(t) != 3:
        raise RecordError("id", f"not <run>-w<NNN>-g<NNNNNNNN>: {game_id[:60]!r}")
    if not _RUN.fullmatch(t[0]):
        raise RecordError("run", f"a run name is 1 to 32 of a-z and 0-9: {t[0][:60]!r}")
    if not _SLOT.fullmatch(t[1]):
        raise RecordError("slot", f"a slot is `w` and three digits: {t[1][:60]!r}")
    if not _COUNTER.fullmatch(t[2]) or int(t[2][1:]) < 1:
        raise RecordError("counter", f"a counter is `g` and eight digits, from 1: {t[2][:60]!r}")
    return t[0], int(t[1][1:]), int(t[2][1:])


def _fp(run_fp) -> bytes:
    if not isinstance(run_fp, str) or not _HEX64.fullmatch(run_fp):
        raise RecordError("run-fingerprint", "the run's fingerprint must be 64 hex digits (lower case)")
    return run_fp.encode("ascii")


def _checked(game_id, opening, sent, rows, end) -> tuple:
    """The five parts as (opening, rows) lists after every shape was judged; RecordError otherwise. The writer
    and the reader use this ONE judge, so that the worker can never write a record its readers refuse."""
    id_parts(game_id)
    opening, rows = list(opening), list(rows)
    if not all(isinstance(m, str) and MOVE.fullmatch(m) for m in opening):
        raise RecordError("structure", f"an opening move of {game_id} is not a move")
    if not isinstance(sent, str) or not sent or not _LINE.fullmatch(sent):
        raise RecordError("structure", f"the sent line of {game_id} is empty or not printable ASCII")
    for r in rows:
        if not isinstance(r, str) or not ROW.fullmatch(r):
            raise RecordError("row", f"a row of {game_id} is not in its shape: {str(r)[:80]!r}")
    if not isinstance(end, str) or not (END.fullmatch(end) or OPENING_END.fullmatch(end)):
        raise RecordError("end", f"the end line of {game_id} is not in its shape: {str(end)[:80]!r}")
    return opening, rows


def _body(game_id, opening, sent, rows, end) -> bytes:
    return ("game " + game_id + " opening" + "".join(" " + m for m in opening) + "\n" + "sent " + sent + "\n"
            + "".join(r + "\n" for r in rows) + end + "\n").encode("ascii")


def bind(run_fp, game_id, opening, sent, rows, end) -> str:
    """The binding of a record with these parts in this run (64 hex digits)."""
    fp = _fp(run_fp)
    opening, rows = _checked(game_id, opening, sent, rows, end)
    return hashlib.sha256(TAG + fp + b"\n" + _body(game_id, opening, sent, rows, end)).hexdigest()


def text(run_fp, game_id, opening, sent, rows, end) -> str:
    """The record's exact text, with its bind line."""
    fp = _fp(run_fp)
    opening, rows = _checked(game_id, opening, sent, rows, end)
    body = _body(game_id, opening, sent, rows, end)
    return body.decode("ascii") + "bind " + hashlib.sha256(TAG + fp + b"\n" + body).hexdigest() + "\n"


def rows_digest(rows, end):
    """The rows digest of a game (see the head of this file), or None for a game without rows."""
    rows = list(rows)
    if not rows:
        return None
    m = END.fullmatch(end) if isinstance(end, str) else None
    if not m:
        raise RecordError("end", "a game with rows needs the engine's end line for its result")
    h = hashlib.sha256()
    for r in rows:
        if not isinstance(r, str) or not ROW.fullmatch(r):
            raise RecordError("row", f"a row is not in its shape: {str(r)[:80]!r}")
        h.update(r.encode("ascii") + b"\n")
    h.update(b"result " + m[1].encode("ascii") + b"\n")
    return h.hexdigest()


def parse(data: bytes, run_fp) -> list:
    """Every record of a piece, in order: dicts with id, run, slot, counter, opening, sent, rows, end, bind,
    first and last (the record is data[first:last]). The bytes must be whole records of THIS run and nothing
    else; RecordError (with `.check`) at the first byte or line that is not."""
    fp = _fp(run_fp)
    if not isinstance(data, (bytes, bytearray)):
        raise RecordError("bytes", "a piece is bytes")
    data = bytes(data)
    odd = data.translate(None, _PLAIN)
    if odd:
        at = next(i for i, b in enumerate(data) if b not in _PLAIN)
        raise RecordError("bytes", f"byte {at} is 0x{data[at]:02x}: a piece holds printable ASCII and LF only")
    if data and not data.endswith(b"\n"):
        raise RecordError("final-lf", "the last line has no line end (a record cut off)")
    out, g, pos, stage = [], None, 0, "game"
    for n, raw in enumerate(data.split(b"\n")[:-1], 1):
        here, pos = pos, pos + len(raw) + 1
        ln = raw.decode("ascii")
        if not ln:
            raise RecordError("blank", f"line {n} is empty: nothing stands before, between or after records")
        if stage == "game":
            t = ln.split(" ")
            if len(t) < 3 or t[0] != "game" or t[2] != "opening":
                raise RecordError("structure", f"line {n}: a game line is expected here: {ln[:80]!r}")
            run, slot, counter = id_parts(t[1])
            if not all(MOVE.fullmatch(m) for m in t[3:]):
                raise RecordError("structure", f"line {n}: the opening of {t[1]} holds something that is not a move")
            g = {"id": t[1], "run": run, "slot": slot, "counter": counter, "opening": t[3:], "sent": None,
                 "rows": [], "end": None, "bind": None, "first": here, "last": None}
            stage = "sent"
        elif stage == "sent":
            if not ln.startswith("sent ") or len(ln) < 6:
                raise RecordError("structure", f"line {n}: the sent line of {g['id']} is expected here: {ln[:80]!r}")
            g["sent"] = ln[5:]
            stage = "rows"
        elif stage == "rows":
            if ln.startswith("sg "):
                if not ROW.fullmatch(ln):
                    raise RecordError("row", f"line {n}: a row of {g['id']} is not in its shape: {ln[:80]!r}")
                g["rows"].append(ln)
            elif ln.startswith("sgend ") or ln.startswith("openingend "):
                if not (END.fullmatch(ln) or OPENING_END.fullmatch(ln)):
                    raise RecordError("end", f"line {n}: the end line of {g['id']} is not in its shape: {ln[:80]!r}")
                g["end"] = ln
                g["_bound"] = hashlib.sha256(TAG + fp + b"\n" + data[g["first"]:pos]).hexdigest()
                stage = "bind"
            else:
                raise RecordError("structure", f"line {n}: a row or the end line of {g['id']} is expected here: {ln[:80]!r}")
        else:
            if not (ln.startswith("bind ") and _HEX64.fullmatch(ln[5:])):
                raise RecordError("structure", f"line {n}: the bind line of {g['id']} is expected here: {ln[:80]!r}")
            if ln[5:] != g.pop("_bound"):
                raise RecordError("binding", f"line {n}: the bind line is not the binding of {g['id']} in this run "
                                             "(another run, changed bytes, or this morning's binding)")
            g["bind"], g["last"] = ln[5:], pos
            out.append(g)
            g, stage = None, "game"
    if g is not None:
        raise RecordError("structure", f"the record of {g['id']} is not closed by its bind line")
    return out


def faults(g: dict, reserved=None) -> list:
    """What is wrong with the MEANING of one parsed record; an empty list = nothing found here. `reserved` is
    the opening the READER computed for this id by itself (root seed and id, its own move rules); None = not
    checked here. The rules of the game (legality, positions, the end) are the rules replay's work, not this."""
    bad = []
    k = OPENING_END.fullmatch(g["end"])
    if k:
        if g["sent"] != "none" or g["rows"]:
            bad.append("a game that ended inside its opening has a sent line or rows")
        if int(k[1]) != len(g["opening"]):
            bad.append("the opening end line does not name the opening's length")
    else:
        if g["sent"] != position_line(g["opening"]) or g["sent"].split(" ") != position_tokens(g["opening"]):
            bad.append("the sent line is not the position line of the record's own opening")
    if reserved is not None and list(reserved) != g["opening"]:
        bad.append("the opening is not the one reserved for this game id")
    return bad

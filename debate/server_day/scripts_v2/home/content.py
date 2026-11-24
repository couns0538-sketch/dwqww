"""Opus 2026-11-23, A3d part 2 (FORMATS 2.2): stage a2 at HOME, the CONTENT VERDICT of every receipted piece.

    content.py --home DIR --fingerprint HEX64 --converter EXE_OR_PY [--openings FILE] [--convert-seconds S = 600]

Runs under a Python with python-chess 1.11.2 (the reader's OWN move rules), beside custody.py (stage a1, whose
receipts it reads and whose run-header check it uses) and the package's run/ folder (record.py; the packer's
convert and rebuild, which home repeats). For every receipt without a verdict, in slot and index order:
 1 THE KEPT BYTES: every member the receipt names is opened and hashed again, wire and data. Other bytes or a member
   gone: WAITS (a1's confirmation brings them again), no verdict.
 2 TRANSPORT (2.2 (i)): raw = the zlib member decoded; binpack = the converter (`convert piece.binpack piece.plain` in
   a fresh scratch folder content/scratch/w<NNN>.p<N>) and the piece built again from that text and the decoded meta
   text (packer.rebuild). A converter that is missing, fails or does not end in time is a LOCAL outage: WAITS, no
   verdict. So is a binpack whose text does not rebuild, or rebuilds into other bytes than the seal's: its members
   are the server's bytes, whose packer proved that round trip before offering, so home's converter differs. The
   bytes must have the seal's raw_bytes and raw_sha256 (a raw member that does not: REFUSED), then parse as whole
   records of THIS run (record.parse: every binding), then give the seal's games, rows, first and last game and
   counter and ids_digest again, with every id of this run and slot and counters that rise. Any failure from there
   on: the piece is REFUSED whole (piece "refused", why, games []): never replayed, never credited.
 3 THE RULES (2.2, from the engine's own self-game loop, uci.cpp): per game, the opening against home's own
   reservation (rule seed: python-chess's legal moves as sorted UCI text, entry sha256("<seed>|<id>|<ply>") mod their
   number; rule list: --openings, whose sha256 and line count are the header's, entry (counter - 1) mod count), the
   sent line (record.faults), then the walk of the engine's loop with the values of the header's game_line: the
   state before each search (no legal move; a rule draw: material, clock 100, a third occurrence; the ply limit) ends
   the game only where the end line says so and with its reason; a searched ply at or past writeminply has its row
   (ply, the position before the move, |score| below evallimit, the move played, written as home writes it); the draw
   run counted as the engine counts it; the end FEN, run, searches, plies and result. accepted, noselfgame (home's
   own board has no legal move after the opening it computed, at the end line's length) or set_aside with the check.
 4 THE INDEX (2.2): content/equal.sqlite, table entries (slot, counter) -> round, game, piece, state, rows_digest,
   bind: one entry per game RECORD of a judged piece, every state (rows_digest only for an accepted game with rows;
   a lookup index on it), committed BEFORE the verdict. The same entry again (a restart) is kept. Other values under
   one (slot, counter): the index keeps the first, and THE CONFLICT RECORD (2.3) conflicts/<game id>.json (or
   <id>.2.json, ... when that name holds another conflict of the id) names both, each {piece, seal_sha256, bind,
   rows_digest, state}, how "two records under one id"; the pass goes on. Credit (repeats, conflicts) is stage b's.
   An index that is gone (or empty) while verdicts exist stops the pass before anything is written (exit 4): a new
   index would miss every judged game, and judged pieces are never judged again.
 5 THE VERDICT content/w<NNN>/p<NNNNNN>.verdict.json, create-only, no time in it (a restart writes the same bytes):
   schema 2, run_fingerprint, slot, index, seal_sha256, round, piece ("judged" or "refused"), why, games: per game
   {game, rows, rows_digest, state, why}.
The last line: content: judged .. pieces (.. refused); accepted .. games .. rows (C2); noselfgame ..; set_aside ..;
waits ..; conflicts ..   Exit codes: 0 a pass; 2 a wrong call; 3 the header, the game line, the openings file or the
rules library cannot be trusted (nothing written); 4 a file or the index that cannot be read or written.

VERSION 2 (Opus 23 Nov; the seats' NOT YET of 223800Z and 186600fd; known answers
tmp/opus_scratch/content_v2/KNOWN_ANSWERS_content_v2_by_opus.md on the PC, 22:54 and 23:03, written before this
code): every pass first reads every receipt and fork record through custody's record check (another run's: exit 3;
one custody did not write: exit 4), then the index's run row (another run's index: exit 3) and every verdict on the
disk: canonical, the form of 2.2 for its own slot and index, this run (another run's: exit 3), its receipt's seal,
and the judged row (slot, idx, seal_sha256) of its piece in the index, which index() writes in the transaction of
the piece's entries (an index older than the verdicts, or an empty one: exit 4). The opening rule is read as the
worker reads it (seed: exactly kind, plies 0 to 64, a root_seed of letters, digits and _, and --openings with it:
exit 2; list: exactly count, kind, sha256). The draw run is compared with drawcount only after a ply that qualified
(uci.cpp 543-551: drawcount 0 acts as 1). --convert-seconds must be finite. A piece's scratch folder is removed on
every exit of its transport, a WAITS too.
"""
import argparse
import hashlib
import json
import lzma
import math
import re
import shutil
import sqlite3
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "run"))
sys.path.insert(0, str(HERE))
import record  # noqa: E402
from custody import HEX64, Home, is_int  # noqa: E402
from packer import convert, rebuild  # noqa: E402
from worker import Stop, canon, create_only, parse_canon, sha256_bytes  # noqa: E402

try:
    import chess
except ImportError:
    chess = None

KEYS = ("softnodes", "evallimit", "maxply", "writeminply", "drawply", "drawscore", "drawcount")
RECEIPT = re.compile(r"p([0-9]{6})\.receipt\.json")
VERDICT = re.compile(r"p([0-9]{6})\.verdict\.json")
VERDICT_KEYS = sorted(("schema", "run_fingerprint", "slot", "index", "seal_sha256", "round", "piece", "why", "games"))
GAME_KEYS = sorted(("game", "rows", "rows_digest", "state", "why"))


class SetAside(Exception):
    """The rules replay refuses this game; the text names the check."""


class Waits(Exception):
    """Nothing is decided about this piece in this pass."""


def need(ok, why):
    if not ok:
        raise SetAside(why)


def num(text: str) -> int:
    need(text.lstrip("-").isdigit() and str(int(text)) == text, f"the number {text} is not written as the engine writes it")
    return int(text)


def game_values(line) -> dict:
    t = line.split(" ") if isinstance(line, str) else []
    v = {}
    if len(t) == 1 + 2 * len(KEYS) and t[0] == "selfgame":
        for key, val in zip(t[1::2], t[2::2]):
            if key in KEYS and key not in v and val.isdigit() and str(int(val)) == val:
                v[key] = int(val)
    if len(v) != len(KEYS):
        raise Stop(3, f"the header's game_line is not `selfgame` with {', '.join(KEYS)} once each: {str(line)[:200]}")
    if v["drawply"] < v["writeminply"]:
        raise Stop(3, "drawply is below writeminply: the draw run would count plies without rows, which home cannot see")
    return v


def legal(board, tok: str):
    try:
        m = board.parse_uci(tok)
    except ValueError:
        raise SetAside(f"{tok} is not a legal move on the replayed board") from None
    need(m.uci() == tok, f"{tok} is not written in standard form (home writes {m.uci()})")
    return m


def reserve(rule: dict, table, gid: str, counter: int) -> tuple:
    """(moves, whole): the opening home computes for this id by its own move rules; whole is False when no legal
    move is left inside it. A listed move that is not legal: SetAside."""
    board, moves = chess.Board(), []
    fixed = table[(counter - 1) % len(table)] if rule["kind"] == "list" else None
    for ply in range(len(fixed) if fixed is not None else rule["plies"]):
        ls = sorted(m.uci() for m in board.legal_moves)
        if not ls:
            return moves, False
        if fixed is None:
            mv = ls[int.from_bytes(hashlib.sha256(f"{rule['root_seed']}|{gid}|{ply}".encode("ascii")).digest()[:8], "big") % len(ls)]
        else:
            mv = fixed[ply]
            need(mv in ls, f"the listed opening holds an illegal move at ply {ply}")
        moves.append(mv)
        board.push_uci(mv)
    return moves, True


def check_game(g: dict, reserved: tuple, v: dict) -> str:
    """'accepted' or 'noselfgame' for one parsed record (record.parse's dict); SetAside names the failed check."""
    moves, whole = reserved
    need(g["opening"] == moves, "the opening is not the one reserved for this id")
    bad = record.faults(g)
    need(not bad, bad[0] if bad else "")
    k = len(moves)
    oe = record.OPENING_END.fullmatch(g["end"])
    if oe:
        need(not whole and num(oe[1]) == k, "an opening end, but home's board has a legal move after this opening")
        return "noselfgame"
    need(whole, "home's own reservation ends inside the opening, the record does not")
    e = record.END.fullmatch(g["end"])
    result, reason = num(e[1]), e[2]
    plies, run, searches, nodes = (num(x) for x in e.group(3, 4, 5, 6))
    played = e[8].split()
    m_ = len(played)
    extra = reason in ("matescore", "evallimit", "drawadj")
    need(plies == k + m_ and plies <= v["maxply"], "plies is not the opening plus the end line's moves, or past maxply")
    need(searches == m_ + int(extra), f"searches {searches} is not the table's for {reason} with {m_} moves")
    need(searches > 0 or nodes == 0, "nodes without a search")
    board = chess.Board()
    for mv in moves:
        board.push_uci(mv)
    rows, ri, drun = g["rows"], 0, 0
    for j in range(m_ + 1):
        ply, last = k + j, j == m_
        if not any(board.legal_moves):
            need(last and reason == ("mate" if board.is_check() else "stalemate"), "the board ends the game here (no legal move)")
            break
        rule = board.is_insufficient_material() or board.halfmove_clock >= 100 or board.is_repetition(3)
        if rule or ply >= v["maxply"]:
            need(last and reason == ("rule" if rule else "plylimit"), "the board ends the game here (a rule draw or the ply limit)")
            break
        need(not last or extra, f"the end line says {reason}, but the board goes on")
        if last and reason != "drawadj":
            break                                   # matescore, evallimit: that search left no row
        if ply >= v["writeminply"]:
            need(ri < len(rows), "a row is missing")
            r = rows[ri].split(" ", 4)
            ri += 1
            score, tok = num(r[2]), r[3]
            need(num(r[1]) == ply, f"row {ri - 1} has ply {r[1]}, the board is at ply {ply}")
            need(r[4] == board.fen(), f"the position of row {ri - 1} is not the board's")
            need(abs(score) < v["evallimit"], f"row {ri - 1}'s score is at or past evallimit")
            drun = drun + 1 if ply >= v["drawply"] and abs(score) <= v["drawscore"] else 0
            need((drun > 0 and drun >= v["drawcount"]) == last,    # uci.cpp: compared only after ++run
                 "the draw run does not end the game where the engine ends it")
            legal(board, tok)
            need(last or tok == played[j], f"row {ri - 1}'s move is not the move played")
        else:
            drun = 0                                # below writeminply <= drawply the engine resets its run
            need(not last, "a draw adjudication before the first written ply")
        if last:
            break                                   # drawadj: its move is not applied
        board.push(legal(board, played[j]))
    need(ri == len(rows), "rows beyond the game")
    need(e[7] == board.fen(), "the end line's position is not the board's")
    need(run == drun, f"the end line's run {run} is not the draw counter {drun}")
    if reason == "mate":
        need(result == (-1 if board.turn == chess.WHITE else 1), "the mate result has the wrong sign")
    elif reason in ("matescore", "evallimit"):
        need(result in (-1, 1), f"a {reason} ending with a draw result")
    else:
        need(result == 0, f"a {reason} ending with a win")
    return "accepted"


class Content:
    def __init__(self, home: Path, fp: str, conv: str, openings, secs: float):
        if chess is None or getattr(chess, "__version__", "") != "1.11.2":
            raise Stop(3, "the rules library is not python-chess 1.11.2 (the version this reader was qualified with)")
        self.H = Home(home, fp)
        self.home, self.fp, self.conv, self.secs = home, fp, conv, secs
        self.out, self.db = home / "content", home / "content" / "equal.sqlite"
        if self.H.h is None:
            return
        self.v = game_values(self.H.h.get("game_line"))
        rule = self.H.h.get("opening_rule")
        self.rule, self.table = rule, None
        if isinstance(rule, dict) and sorted(rule) == ["kind", "plies", "root_seed"] and rule["kind"] == "seed":
            if type(rule["plies"]) is not int or not 0 <= rule["plies"] <= 64 \
                    or not (isinstance(rule["root_seed"], str) and re.fullmatch(r"[A-Za-z0-9_]{1,64}", rule["root_seed"])):
                raise Stop(3, "the header's seed rule needs plies 0 to 64 and a root_seed of letters, digits and _ "
                              "(as the worker reads it)")
            if openings:
                raise Stop(2, "--openings is given and the run's opening rule is seed (the worker refuses that call)")
            return
        if not (isinstance(rule, dict) and sorted(rule) == ["count", "kind", "sha256"] and rule["kind"] == "list"
                and openings):
            raise Stop(3, "the header's opening_rule is not seed, or list with --openings given")
        data = Path(openings).read_bytes()
        self.table = [ln.split(" ") if ln else [] for ln in data.decode("ascii").split("\n")[:-1]]   # the worker's parse
        if sha256_bytes(data) != rule.get("sha256") or not data.endswith(b"\n") or len(self.table) != rule.get("count") \
                or not self.table:
            raise Stop(3, "--openings is not the list the header names (sha256, count, every line ended by LF)")

    def kept(self, r: dict, name: str) -> dict:
        d, files = self.home / r["kept"], {}
        for m in r["members"]:
            try:
                wb = (d / m["wire_name"]).read_bytes()
                data = zlib.decompress(wb) if m["name"].endswith(".seal.json") else wb
            except (OSError, zlib.error):
                raise Waits(f"the kept member {m['wire_name']} is gone or does not decode (a1 --confirm)") from None
            if (len(wb), sha256_bytes(wb), len(data), sha256_bytes(data)) != \
                    (m["wire_bytes"], m["wire_sha256"], m["bytes"], m["sha256"]):
                raise Waits(f"the kept member {m['wire_name']} is not the bytes of its receipt (a1 --confirm)")
            files[m["name"][len(name):]] = data
        return files

    def transport(self, k: int, name: str, files: dict) -> bytes:
        if ".raw.zz" in files:
            return zlib.decompress(files[".raw.zz"])
        meta = lzma.decompress(files[".meta.xz"]).decode("ascii")
        work = self.out / "scratch" / f"w{k:03d}.{name}"
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        (work / "piece.binpack").write_bytes(files[".binpack"])
        try:
            convert(self.conv, work / "piece.binpack", work / "piece.plain", self.secs)
        except RuntimeError as e:
            raise Waits(f"the converter failed here, a local outage: {e}") from None
        try:
            raw = rebuild(meta, (work / "piece.plain").read_bytes().decode("ascii"))
        except ValueError as e:                 # UnicodeDecodeError too; the server proved this round trip
            raise Waits(f"the binpack does not rebuild here, a local outage (home's converter differs): {e}") from None
        return raw

    def judge(self, k: int, i: int, r: dict) -> tuple:
        name = f"p{i:06d}"
        files = self.kept(r, name)
        s = json.loads(files[".seal.json"])
        head = {"schema": 2, "run_fingerprint": self.fp, "slot": k, "index": i, "seal_sha256": r["seal_sha256"],
                "round": s["round"]}

        def refused(why):
            return dict(head, piece="refused", why=why, games=[]), []
        try:
            raw = self.transport(k, name, files)
        except (zlib.error, lzma.LZMAError, UnicodeDecodeError, ValueError) as e:
            return refused(f"transport: {e}")
        finally:
            shutil.rmtree(self.out / "scratch" / f"w{k:03d}.{name}", ignore_errors=True)   # every exit, a WAITS too
        if (len(raw), sha256_bytes(raw)) != (s["raw_bytes"], s["raw_sha256"]):
            if ".binpack" in files:
                raise Waits("the binpack does not rebuild here, a local outage (home's converter differs): the bytes "
                            "are not the seal's raw_bytes and raw_sha256")
            return refused("transport: the bytes built again are not the seal's raw_bytes and raw_sha256")
        try:
            games = record.parse(raw, self.fp)
        except record.RecordError as e:
            return refused(f"records: {e}")
        ids = hashlib.sha256()
        for g in games:
            ids.update(f"{g['id']}\n{'noselfgame' if g['end'].startswith('openingend ') else 'done'}\n{g['bind']}\n".encode("ascii"))
        again = {"games": len(games), "rows": sum(len(g["rows"]) for g in games), "ids_digest": ids.hexdigest(),
                 "first_game": games[0]["id"] if games else None, "last_game": games[-1]["id"] if games else None,
                 "first_counter": games[0]["counter"] if games else None,
                 "last_counter": games[-1]["counter"] if games else None}
        off = [x for x in again if s.get(x) != again[x]]
        if not games or off:
            return refused(f"the seal's fields do not describe its bytes: {', '.join(off) or 'no game'}")
        if any(g["run"] != self.H.h["run"] or g["slot"] != k for g in games) \
                or any(b["counter"] <= a["counter"] for a, b in zip(games, games[1:])):
            return refused("an id of another run or slot, or counters that do not rise")
        out, entries = [], []
        for g in games:
            try:
                st, why = check_game(g, reserve(self.rule, self.table, g["id"], g["counter"]), self.v), None
            except SetAside as e:
                st, why = "set_aside", str(e)
            dg = record.rows_digest(g["rows"], g["end"]) if st == "accepted" else None
            out.append({"game": g["id"], "rows": 0 if st == "noselfgame" else len(g["rows"]), "rows_digest": dg,
                        "state": st, "why": why})
            entries.append((k, g["counter"], s["round"], g["id"], f"w{k:03d}/{name}", st, dg, g["bind"]))
        return dict(head, piece="judged", why=None, games=out), entries

    def index(self, entries: list, judged: tuple) -> list:
        """Every entry not in the index yet is committed, with the run row and the piece's judged row (slot, idx,
        seal_sha256) in the same transaction; (first, second) for each (slot, counter) that holds other values: the
        index keeps the first."""
        con, clashes = sqlite3.connect(self.db, isolation_level=None), []
        try:
            con.execute("PRAGMA synchronous=FULL")
            con.execute("CREATE TABLE IF NOT EXISTS entries (slot INTEGER, counter INTEGER, round INTEGER, game TEXT, "
                        "piece TEXT, state TEXT, rows_digest TEXT, bind TEXT, PRIMARY KEY (slot, counter))")
            con.execute("CREATE INDEX IF NOT EXISTS by_digest ON entries (rows_digest)")
            con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS judged (slot INTEGER, idx INTEGER, seal_sha256 TEXT NOT NULL, "
                        "PRIMARY KEY (slot, idx))")
            con.execute("BEGIN IMMEDIATE")
            con.execute("INSERT OR IGNORE INTO meta VALUES ('run_fingerprint', ?)", (self.fp,))
            for e in entries:
                old = con.execute("SELECT slot, counter, round, game, piece, state, rows_digest, bind FROM entries "
                                  "WHERE slot = ? AND counter = ?", e[:2]).fetchone()
                if old is None:
                    con.execute("INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?)", e)
                elif tuple(old) != e:
                    clashes.append((tuple(old), e))
            con.execute("INSERT OR REPLACE INTO judged VALUES (?, ?, ?)", judged)
            con.execute("COMMIT")
        finally:
            con.close()                                 # a transaction left open here is rolled back
        return clashes

    def conflict(self, first: tuple, second: tuple) -> None:
        """The record of two records under one id (2.3), create-only; a restart finds the same bytes."""
        def side(e):
            rp = self.H.cust / e[4].split("/")[0] / f"{e[4].split('/')[-1]}.receipt.json"
            return {"piece": e[4], "seal_sha256": json.loads(rp.read_bytes())["seal_sha256"] if rp.is_file() else None,
                    "state": e[5], "rows_digest": e[6], "bind": e[7]}
        data = canon({"schema": 2, "run_fingerprint": self.fp, "game": second[3], "how": "two records under one id",
                      "first": side(first), "second": side(second)})
        d, n = self.home / "conflicts", 1
        d.mkdir(exist_ok=True)
        while True:
            p = d / (f"{second[3]}.json" if n == 1 else f"{second[3]}.{n}.json")
            if not p.exists() or p.read_bytes() == data:
                create_only(p, data)
                print(f"CONFLICT {second[3]}: two records under one id ({first[4]} and {second[4]}): {p.name}")
                return
            n += 1

    def check_index(self) -> None:
        """2.1, 2.2: the index serves this run (its run row), and every verdict on the disk is one this program wrote
        for this run: canonical, the form of 2.2 for its own slot and index, its receipt's seal, and that piece's judged
        row in the index. Another run's index or verdict: STOP 3 (a home folder serves one run); an index older than
        the verdicts (a backup put back), an empty one, or anything else: STOP 4. Nothing is written before."""
        seen, run = {}, None
        if self.db.is_file() and self.db.stat().st_size:
            con = sqlite3.connect(self.db)
            try:
                tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
                if "meta" in tables:
                    run = con.execute("SELECT value FROM meta WHERE key = 'run_fingerprint'").fetchone()
                if "judged" in tables:
                    seen = {(a, b): c for a, b, c in con.execute("SELECT slot, idx, seal_sha256 FROM judged")}
            finally:
                con.close()
        if run is not None and run[0] != self.fp:
            raise Stop(3, "content/equal.sqlite is another run's index: a home folder serves one run (2.1); give this "
                          "run a fresh home folder (nothing was written)")
        for d in sorted(self.out.glob("w[0-9][0-9][0-9]")) if self.out.is_dir() else []:
            for p in sorted(d.iterdir()):
                if not (m := VERDICT.fullmatch(p.name)):
                    continue
                k, i, what = int(d.name[1:]), int(m[1]), f"content/{d.name}/{p.name}"
                try:
                    v = parse_canon(p.read_bytes(), what)
                except ValueError as e:
                    raise Stop(4, f"{what} is not a verdict this program writes: {e}") from None
                if isinstance(v, dict) and sorted(v) == VERDICT_KEYS and v["run_fingerprint"] != self.fp:
                    raise Stop(3, f"{what} is another run's verdict: a home folder serves one run (2.1); give this "
                                  "run a fresh home folder (nothing was written)")
                if not (isinstance(v, dict) and sorted(v) == VERDICT_KEYS and is_int(v["schema"], v["slot"], v["index"])
                        and (v["schema"], v["slot"], v["index"]) == (2, k, i) and v["piece"] in ("judged", "refused")
                        and isinstance(v["games"], list)
                        and all(isinstance(g, dict) and sorted(g) == GAME_KEYS and is_int(g["rows"])
                                and g["state"] in ("accepted", "noselfgame", "set_aside") for g in v["games"])):
                    raise Stop(4, f"{what} is not a verdict of 2.2 for w{k:03d}/p{i:06d}")
                seal = self.H.record(k, i)["seal_sha256"]
                if v["seal_sha256"] != seal:
                    raise Stop(4, f"{what} is not of its receipt's seal_sha256")
                if seen.get((k, i)) != seal:
                    raise Stop(4, f"{what} has no judged row of its receipt's seal in content/equal.sqlite: the index "
                                  "is older than the verdicts (a backup put back) or empty; move content/ aside and "
                                  "judge again from the receipts")

    def one_pass(self) -> int:
        waits = 0
        self.H.check_records()
        if (not self.db.is_file() or self.db.stat().st_size == 0) and any(self.out.glob("w*/p*.verdict.json")):
            raise Stop(4, "content/equal.sqlite is gone while verdicts exist: a new index would miss their games (equal "
                          "games, two records under one id); move content/ aside and judge again from the receipts")
        self.check_index()
        for k in self.H.h["slots"]:
            d = self.H.cust / f"w{k:03d}"
            for i in sorted(int(m[1]) for p in (d.iterdir() if d.is_dir() else []) if (m := RECEIPT.fullmatch(p.name))):
                vp = self.out / f"w{k:03d}" / f"p{i:06d}.verdict.json"
                if vp.exists():
                    continue
                try:
                    verdict, entries = self.judge(k, i, json.loads((d / f"p{i:06d}.receipt.json").read_bytes()))
                except Waits as e:
                    print(f"WAITS w{k:03d}/p{i:06d}: {e}")
                    waits += 1
                    continue
                self.out.mkdir(exist_ok=True)
                for first, second in self.index(entries, (k, i, verdict["seal_sha256"])):
                    self.conflict(first, second)
                vp.parent.mkdir(exist_ok=True)
                create_only(vp, canon(verdict))
                if verdict["piece"] == "refused":
                    print(f"REFUSED w{k:03d}/p{i:06d}: {verdict['why']}")
                for x in verdict["games"]:
                    if x["state"] == "set_aside":
                        print(f"SET ASIDE {x['game']}: {x['why']}")
        return waits

    def counts(self, waits: int) -> str:
        t = dict(pieces=0, refused=0, accepted=0, c2=0, noselfgame=0, set_aside=0)
        for d in sorted(self.out.glob("w[0-9][0-9][0-9]")) if self.out.is_dir() else []:
            for p in sorted(d.iterdir()):
                if VERDICT.fullmatch(p.name):
                    x = json.loads(p.read_bytes())
                    t["pieces"] += 1
                    t["refused"] += x["piece"] == "refused"
                    for g in x["games"]:
                        t[g["state"]] = t.get(g["state"], 0) + 1
                        t["c2"] += g["rows"] if g["state"] == "accepted" else 0
        cf = self.home / "conflicts"
        n = sum(1 for p in cf.iterdir() if p.name.endswith(".json")) if cf.is_dir() else 0
        return (f"content: judged {t['pieces']} pieces ({t['refused']} refused); accepted {t['accepted']} games "
                f"{t['c2']} rows; noselfgame {t['noselfgame']}; set_aside {t['set_aside']}; waits {waits}; "
                f"conflicts {n}")


def main() -> int:
    ap = argparse.ArgumentParser(description="stage a2 at home: transport, rules replay, index, verdict")
    ap.add_argument("--home", required=True)
    ap.add_argument("--fingerprint", required=True)
    ap.add_argument("--converter", required=True)
    ap.add_argument("--openings")
    ap.add_argument("--convert-seconds", type=float, default=600.0)
    try:
        a = ap.parse_args()
    except SystemExit:
        return 2
    home = Path(a.home)
    if not home.is_dir() or not HEX64.fullmatch(a.fingerprint) \
            or not (math.isfinite(a.convert_seconds) and a.convert_seconds > 0):
        print("content: STOP (2): --home must be a folder, --fingerprint 64 hex digits, --convert-seconds a finite "
              "number above 0")
        return 2
    try:
        c = Content(home, a.fingerprint, a.converter, a.openings, a.convert_seconds)
        if c.H.h is None:
            print("content: no wire/RUN.json.zz at home yet: nothing to do")
            return 0
        print(c.counts(c.one_pass()))
        return 0
    except Stop as e:
        print(f"content: STOP ({e.code}): {e}")
        return e.code
    except (OSError, ValueError, sqlite3.Error) as e:
        print(f"content: STOP (4): {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())

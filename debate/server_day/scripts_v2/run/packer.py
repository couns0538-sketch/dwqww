"""Fable 2026-11-23 (version 1, W5 (d) and (e)); Opus 2026-11-23 (version 2, to FORMATS 2.2 sections 0, 0.1, 1.5, 1.6
and 1.8): the SERVER side of the transfer. Every sealed piece of the workers becomes ONE immutable offer, proven
lossless on the server before it is published. Standard library only.

    packer.py --root DIR --converter EXE_OR_PY [--once] [--poll S = 5] [--convert-seconds S = 600]
              [--probe-every S = 600]

--root is the run's folder (RUN.json, w<NNN>/, out/). For every slot of the header, in index order, each sealed piece
w<NNN>/closed/p<NNNNNN>.seal.json without its offer out/w<NNN>/p<NNNNNN>.offer.json:
 1 THE SEAL AND ITS PIECE (1.5). The seal canonical (an empty or unreadable one is a named stop: Neon N7), with the
   keys of 1.5 and no other: schema 2, this run, this run's fingerprint, this slot and index, prev_seal the genesis
   text for index 0 and otherwise the sha256 of the seal before it (which must be there); the piece's size and
   sha256; every record parsed against this run's fingerprint and its binding computed again (0.1); the ids in
   this run's and slot's grammar with rising counters; games (at least 1), rows, first and last game and counter,
   and ids_digest (`done` for an engine end line, `noselfgame` for an opening end) computed again. Anything that
   does not hold: exit 3, the piece named, nothing of it offered.
 2 THE FORM (1.6). A piece without a single row: "raw" at once, without the converter and not a failure of it. In
   fallback mode: "raw" at once. Otherwise ONE bounded attempt (--convert-seconds for both directions together,
   in out/scratch): the rows as the loop's six-line text (fen, move, score, ply, and the result as the side to
   move sees it, from the engine's own end line) -> the converter -> binpack -> the converter -> text, which must
   be the text sent, every field of every row (case 12: the result too); and the piece built again from that text
   and the meta text (`rebuild`, what home does) must have the seal's raw_sha256. Then "binpack". Any failure (no
   converter, no end in time, an exit code, a missing or empty file, a difference, a scratch folder that could
   not be made: B2) gives "raw" and counts; three
   in a row append `fallback` to out/PACKER_MODE.jsonl, which survives a restart. In that mode a probe (every
   --probe-every seconds) runs the round trip on the newest piece with rows this packer offered, in out/scratch
   only; a probe that passes appends `normal`.
 3 THE MEMBERS, create-only into out/w<NNN>/ (FORMATS 0: a temporary name, flushed, os.link, the folder flushed,
   the temporary name removed; the same bytes there = done, other bytes = both kept and exit 4): p.seal.json
   (codec none, fetched as its wire copy p.seal.json.zz), and for "binpack" p.binpack (none) and p.meta.xz (lzma
   6), for "raw" p.raw.zz (zlib 6). Every packed file is decoded again and compared before it is published.
 4 THE OFFER: p.offer.json (schema, run_fingerprint, slot, index, seal_sha256, form, members), then its wire copy
   p.offer.json.zz LAST (2.3, Neon's closure: a fetch lists and fetches only *.offer.json.zz, so a piece is offered
   when that file is there, and a restart redoes a piece without it, every earlier file found equal). A restart
   that finds p.offer.json WITHOUT its wire copy does not decide the form again (B1, Fable 14:43 with Neon's
   conditions 153530Z: a converter that works now, or fails now, would meet the offer with other bytes and stop the
   packer at that piece at every start): the offer must be this piece's (canonical, the keys of 1.6, schema 2, this
   run's fingerprint, slot, index, the seal's sha256, the members of its form as written here; a piece without rows
   raw), every member it names there with its bytes and sha256, wire and decoded (the seal, raw.zz and meta.xz
   decoded to the piece's own), and only then its wire copy is written; anything else: exit 4 naming the piece and
   the file, nothing written. A member of the other form left by a stop before any offer existed is left as it is
   and named in the log: no offer names it, so no fetch takes it.
 5 THE OTHER WIRE COPIES (2.3), create-only beside their files: RUN.json.zz, SCHEDULE.<n>.json.zz,
   RESUME.<n>.json.zz, FENCE.json.zz and ranges/r<NNNN>.w<NNN>.seal.json.zz (TERMINAL.jsonl.zz is the guard's).
Nothing sealed is ever removed (D2), and there is no index file (case 13: a fetch lists the offers). One packer at a
time (out/LOCK). It ends with exit 0 after one more pass when FENCE.json is there and every slot of the header has
its `ended` line (1.8.4), when STOP_PACKER is in the root (the guard's word that the other slots are unreconciled),
or after one pass with --once. The last pass also stops on a seal missing before later ones.
SECOND READ (Opus 2026-11-24, the seats' NOT YET: Astra 214929Z, Neon 223800Z): P1 a piece found already
offered becomes the probe piece when its seal names rows, so a restart in fallback mode probes on schedule;
P2 every last pass reads each slot's journal end BEFORE its seals, and an `ended` slot is complete only when
its seals end at that line's last_index and last_seal is that seal's sha256 (the genesis text for -1), else
exit 3; P3 --poll, --probe-every and --convert-seconds finite; P4 a wire copy only of a canonical file, else
exit 4; P5 a piece is passed over only when its offer's wire copy gives the offer back, the offer is this
piece's and every member's wire file is there at the size named, else exit 4.
Exit codes: 0; 2 a wrong call; 3 a piece that cannot be trusted, or another packer holds out/LOCK; 4 a file that
cannot be read or written, or a publication conflict. Never a traceback.
"""
import argparse
import hashlib
import lzma
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record  # noqa: E402
from worker import SlotLock, Stop, canon, create_only, file_sha256, parse_canon, sha256_bytes  # noqa: E402

SEAL_KEYS = sorted(("schema", "run", "run_fingerprint", "slot", "epoch", "index", "prev_seal", "raw_sha256",
                    "raw_bytes", "games", "rows", "first_game", "last_game", "first_counter", "last_counter",
                    "ids_digest", "round", "schedule"))
SEAL_NAME = re.compile(r"p([0-9]{6})\.seal\.json\Z")         # B3: [0-9], not any Unicode digit; the worker's grammar
WIRED_IN_ROOT = re.compile(r"(RUN|FENCE|SCHEDULE\.[1-9][0-9]{0,2}|RESUME\.[1-9][0-9]{0,2})\.json\Z")
RANGE_SEAL = re.compile(r"r[0-9]{4}\.w[0-9]{3}\.seal\.json\Z")
OFFER_KEYS = sorted(("schema", "run_fingerprint", "slot", "index", "seal_sha256", "form", "members"))
MEMBER_KEYS = sorted(("name", "codec", "bytes", "sha256", "wire_name", "wire_bytes", "wire_sha256"))
FORMS = {"binpack": ((".seal.json", "none"), (".binpack", "none"), (".meta.xz", "lzma")),
         "raw": ((".seal.json", "none"), (".raw.zz", "zlib"))}
PACK = {"none": (lambda b: b, lambda b: b), "lzma": (lambda b: lzma.compress(b, preset=6), lzma.decompress),
        "zlib": (lambda b: zlib.compress(b, 6), zlib.decompress)}


def printable(text, n: int = 300) -> str:
    return "".join(c if " " <= c <= "~" else "?" for c in str(text))[:n]


def convert(converter: str, src: Path, dst: Path, secs: float) -> None:
    """The converter's own command on its input, `convert <src> <dst>`, both in one folder, its output into a file
    (no pipe that a child of it could hold open). No end within `secs`: killed (on POSIX its whole session)."""
    if not secs > 0:
        raise RuntimeError("no time was left for the converter")
    if not Path(converter).is_file():
        raise RuntimeError(f"the converter {converter} is missing")
    cmd = [sys.executable, "-I", "-B", converter] if converter.endswith(".py") else [converter]
    with open(dst.parent / "converter.log", "ab") as log:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT, cwd=str(dst.parent),
                             start_new_session=os.name != "nt")
        try:
            p.communicate(f"convert {src.name} {dst.name}\nquit\n".encode("ascii"), timeout=secs)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except OSError:
                    pass
            p.kill()
            p.wait()
            raise RuntimeError(f"convert {src.name} -> {dst.name}: no end within {secs:.0f} s, killed") from None
    if p.returncode != 0 or not dst.is_file() or dst.stat().st_size == 0:
        raise RuntimeError(f"convert {src.name} -> {dst.name} failed (exit {p.returncode})")


def plain_of(games: list) -> str:
    """The loop's six-line text of every row, with the engine's own result (pipeline/nnloop/datagen_uci.py)."""
    out = []
    for g in games:
        if not g["rows"]:
            continue
        result = int(g["end"].split()[2])
        for row in g["rows"]:
            _, ply, score, move, fen = row.split(" ", 4)
            res = result if fen.split(" ", 2)[1] == "w" else -result
            out.append(f"fen {fen}\nmove {move}\nscore {score}\nply {ply}\nresult {res}\ne\n")
    return "".join(out)


def meta_of(games: list) -> str:
    return "".join(f"game {g['id']} opening {' '.join(g['opening'])}".rstrip() + f"\nsent {g['sent']}\nrows {len(g['rows'])}\n"
                   f"{g['end']}\nbind {g['bind']}\n" for g in games)


def rebuild(meta: str, plain: str) -> bytes:
    """The raw piece again, from the meta text and the unpacked six-line text. Raises ValueError when they do
    not fit together. Used here for the proof and by the receiver at home."""
    m = meta.split("\n")
    if m and m[-1] == "":
        m.pop()
    if len(m) % 5:
        raise ValueError("the meta text is not five lines a game")
    p = plain.replace("\r\n", "\n").split("\n")    # the converter on Windows writes CR LF: text is never hashed
    if p and p[-1] == "":
        p.pop()
    if len(p) % 6:
        raise ValueError("the unpacked text is not six lines a row")
    out, at = [], 0
    for k in range(0, len(m), 5):
        game, sent, rows, end, bind = m[k:k + 5]
        if not rows.startswith("rows ") or not rows[5:].isdigit():
            raise ValueError(f"meta line {k + 3} is not a row count")
        out += [game, sent]
        for _ in range(int(rows[5:])):
            r = p[at:at + 6]
            if len(r) != 6 or not (r[0].startswith("fen ") and r[1].startswith("move ") and r[2].startswith("score ")
                                   and r[3].startswith("ply ") and r[4].startswith("result ") and r[5] == "e"):
                raise ValueError(f"unpacked row at line {at + 1} is missing or not a row")
            out.append(f"sg {r[3][4:]} {r[2][6:]} {r[1][5:]} {r[0][4:]}")
            at += 6
        out += [end, bind]
    if at != len(p):
        raise ValueError(f"the unpacked text has {(len(p) - at) // 6} rows more than the meta names")
    return ("\n".join(out) + "\n").encode("ascii") if out else b""


class Packer:
    def __init__(self, a):
        self.a, self.root = a, Path(a.root).resolve()
        self.conv = str(Path(a.converter).resolve())
        hp = self.root / "RUN.json"
        if not hp.is_file():
            raise Stop(2, f"{hp} is not there: --root must be a run's folder")
        hb = hp.read_bytes()
        try:
            h = parse_canon(hb, "RUN.json")
        except ValueError as e:
            raise Stop(4, str(e)) from None
        slots = h.get("slots") if isinstance(h, dict) else None
        if not isinstance(h, dict) or h.get("schema") != 2 or not re.fullmatch(r"[a-z0-9]{1,32}", str(h.get("run"))) \
                or not isinstance(slots, list) or not slots or len(set(slots)) != len(slots) \
                or any(type(k) is not int or not 0 <= k <= 999 for k in slots):
            raise Stop(4, "RUN.json is not a run header of schema 2 (run, slots)")
        self.fp, self.run_name, self.slots = sha256_bytes(hb), h["run"], slots
        self.out = self.root / "out"
        self.out.mkdir(exist_ok=True)
        self.lock = SlotLock(self.out)
        self.logf = open(self.out / "packer.log", "a", encoding="ascii", errors="replace", buffering=1)
        self.scratch = self.out / "scratch"
        if self.scratch.is_symlink() or (hasattr(self.scratch, "is_junction") and self.scratch.is_junction()):
            raise Stop(4, f"{self.scratch} is a link: nothing is removed through it")
        shutil.rmtree(self.scratch, ignore_errors=True)  # this packer's own scratch, never data
        self.mode_file = self.out / "PACKER_MODE.jsonl"
        self.mode = self.read_mode()
        self.fails, self.probe_piece, self.last_probe = 0, None, time.monotonic()
        self.next, self.wired = {k: 0 for k in self.slots}, set()
        self.counts = {"binpack": 0, "raw": 0}

    def say(self, text: str) -> None:
        self.logf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")

    # ---- the mode (1.6) -----------------------------------------------------------------------------------------
    def read_mode(self) -> str:
        if not self.mode_file.exists():
            return "normal"
        data = self.mode_file.read_bytes()
        cut = data.rfind(b"\n") + 1
        if cut != len(data):                            # an append a crash cut off: only whole lines count (0)
            with open(self.mode_file, "r+b") as f:
                f.truncate(cut)
                f.flush()
                os.fsync(f.fileno())
            self.say(f"PACKER_MODE.jsonl: an unfinished last line of {len(data) - cut} bytes dropped")
        mode = "normal"
        for n, line in enumerate(data[:cut].splitlines(keepends=True), 1):
            try:
                r = parse_canon(line, f"PACKER_MODE.jsonl line {n}")
            except ValueError as e:
                raise Stop(4, str(e)) from None
            if not isinstance(r, dict) or r.get("t") != "mode" or r.get("mode") not in ("normal", "fallback"):
                raise Stop(4, f"PACKER_MODE.jsonl line {n} is not a mode line")
            mode = r["mode"]
        return mode

    def set_mode(self, mode: str, why: str, piece: str) -> None:
        line = canon({"t": "mode", "mode": mode, "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      "why": printable(why), "piece": piece})
        with open(self.mode_file, "ab") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        self.mode = mode
        self.say(f"MODE {mode} at {piece}: {printable(why)}")

    # ---- one piece ----------------------------------------------------------------------------------------------
    def verify(self, k: int, i: int):
        """(seal bytes, seal, piece bytes, records) of a piece whose seal and bytes hold (1.5, 0.1); else Stop 3."""
        key = f"w{k:03d}/p{i:06d}"
        closed = self.root / f"w{k:03d}" / "closed"

        def bad(why):
            return Stop(3, f"{key}: {why}; nothing of it is offered")

        sb = (closed / f"p{i:06d}.seal.json").read_bytes()
        if not sb:
            raise bad(f"p{i:06d}.seal.json is empty")
        try:
            s = parse_canon(sb, f"p{i:06d}.seal.json")
        except ValueError as e:
            raise bad(str(e)) from None
        if not isinstance(s, dict) or sorted(s) != SEAL_KEYS:
            raise bad("the seal's keys are not those of FORMATS 1.5")
        for name, want in (("schema", 2), ("run", self.run_name), ("run_fingerprint", self.fp), ("slot", k), ("index", i)):
            if type(s[name]) is not type(want) or s[name] != want:
                raise bad(f"the seal's {name} is {s[name]!r}, not {want!r}")
        for name, lo, hi in (("epoch", 1, 9999), ("round", 1, 9999), ("schedule", 0, 999), ("games", 1, 10 ** 9),
                             ("rows", 0, 10 ** 12), ("raw_bytes", 1, 10 ** 13)):
            if type(s[name]) is not int or not lo <= s[name] <= hi:
                raise bad(f"the seal's {name} is {s[name]!r}")
        prev = closed / f"p{i - 1:06d}.seal.json"
        if i == 0:
            want_prev = f"genesis:{self.fp}:w{k:03d}"
        elif prev.is_file():
            want_prev = file_sha256(prev)
        else:
            raise bad(f"the seal before it, {prev.name}, is not there")
        if s["prev_seal"] != want_prev:
            raise bad("prev_seal is not the seal before it")
        rp = closed / f"p{i:06d}.raw"
        if not rp.is_file():
            raise bad(f"{rp.name} is not there")
        raw = rp.read_bytes()
        if len(raw) != s["raw_bytes"] or sha256_bytes(raw) != s["raw_sha256"]:
            raise bad("the piece's bytes are not the sealed ones")
        try:
            games = record.parse(raw, self.fp)
        except (record.RecordError, ValueError) as e:
            raise bad(printable(e)) from None
        if not games:
            raise bad("a sealed piece without a game")
        ids, counters = hashlib.sha256(), []
        for g in games:
            if (g["run"], g["slot"]) != (self.run_name, k):        # the id's parts as the record module judged them
                raise bad(f"{g['id']} is not an id of this run's slot")
            c = g["counter"]
            if counters and c <= counters[-1]:
                raise bad(f"the counters do not rise at {g['id']}")
            counters.append(c)
            if record.bind(self.fp, g["id"], g["opening"], g["sent"], g["rows"], g["end"]) != g["bind"]:
                raise bad(f"{g['id']} does not carry its own binding")
            state = "done" if g["end"].startswith("sgend ") else "noselfgame" if g["end"].startswith("openingend ") else ""
            if not state:
                raise bad(f"{g['id']} has no end line of a game")
            ids.update(f"{g['id']}\n{state}\n{g['bind']}\n".encode("ascii"))
        fresh = {"games": len(games), "rows": sum(len(g["rows"]) for g in games), "first_game": games[0]["id"],
                 "last_game": games[-1]["id"], "first_counter": counters[0], "last_counter": counters[-1],
                 "ids_digest": ids.hexdigest()}
        for name, v in fresh.items():
            if s[name] != v:
                raise bad(f"the seal's {name} is {s[name]!r}, the piece's {v!r}")
        return sb, s, raw, games

    def round_trip(self, games: list, meta: str, raw_sha: str, folder: Path) -> str:
        """'' when the converter gives every row back unchanged and the piece built again is the piece; else why not.
        One bounded attempt; the binpack is left in the folder."""
        src, binp, back = folder / "piece.plain", folder / "piece.binpack", folder / "back.plain"
        t_end = time.monotonic() + self.a.convert_seconds
        try:
            folder.mkdir(parents=True)                  # B2: one that could not be removed is a failed attempt
            text = plain_of(games)
            src.write_bytes(text.encode("ascii"))
            convert(self.conv, src, binp, t_end - time.monotonic())
            convert(self.conv, binp, back, t_end - time.monotonic())
            again = back.read_bytes().decode("ascii", "replace").replace("\r\n", "\n")
        except (RuntimeError, OSError, ValueError, IndexError) as e:
            return printable(e)
        if again != text:
            a, b = text.split("\n"), again.split("\n")
            n = next((j for j, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            return (f"the rows came back changed at line {n + 1} of the six-line text: sent "
                    f"`{printable(a[n] if n < len(a) else '', 90)}`, back `{printable(b[n] if n < len(b) else '', 90)}`")
        try:
            if sha256_bytes(rebuild(meta, again)) != raw_sha:
                return "the piece built again from the meta text and the rows is not the piece"
        except ValueError as e:
            return printable(e)
        return ""

    def member(self, d: Path, name: str, content: bytes, codec: str, wire: bool = False) -> dict:
        """One member published create-only, its packed bytes and its wire copy decoded again and compared first."""
        enc, dec = PACK[codec]
        data = enc(content)
        if dec(data) != content:
            raise Stop(4, f"{name}: the packed bytes do not give the content back")
        wire_name, wire_data = (name + ".zz", zlib.compress(data, 6)) if wire else (name, data)
        if wire and zlib.decompress(wire_data) != data:
            raise Stop(4, f"{wire_name}: the wire copy does not give the file back")
        create_only(d / wire_name, wire_data)
        return {"name": name, "codec": codec, "bytes": len(data), "sha256": sha256_bytes(data),
                "wire_name": wire_name, "wire_bytes": len(wire_data), "wire_sha256": sha256_bytes(wire_data)}

    def pack(self, k: int, i: int) -> str:
        sb, s, raw, games = self.verify(k, i)
        key, name = f"w{k:03d}/p{i:06d}", f"p{i:06d}"
        meta = meta_of(games)
        d = self.out / f"w{k:03d}"
        if (d / f"{name}.offer.json").exists():         # B1: a stop between the offer and its wire copy
            return self.finish_offer(k, i, d, key, name, sb, s, raw, meta)
        work = self.scratch / f"w{k:03d}.{name}"       # flat: a removed piece leaves no folder
        shutil.rmtree(work, ignore_errors=True)
        form, why = "raw", ("no rows" if s["rows"] == 0 else "fallback mode" if self.mode == "fallback" else "")
        if not why:
            why = self.round_trip(games, meta, s["raw_sha256"], work)
            if why:
                self.fails += 1
                self.say(f"{key}: the converter's attempt failed ({self.fails} in a row): {why}")
                if self.fails >= 3:
                    self.set_mode("fallback", why, key)
            else:
                form, self.fails = "binpack", 0
        d.mkdir(exist_ok=True)
        members = [self.member(d, f"{name}.seal.json", sb, "none", wire=True)]
        if form == "binpack":
            members += [self.member(d, f"{name}.binpack", (work / "piece.binpack").read_bytes(), "none"),
                        self.member(d, f"{name}.meta.xz", meta.encode("ascii"), "lzma")]
        else:
            members.append(self.member(d, f"{name}.raw.zz", raw, "zlib"))
        offer = canon({"schema": 2, "run_fingerprint": self.fp, "slot": k, "index": i,
                       "seal_sha256": sha256_bytes(sb), "form": form, "members": members})
        create_only(d / f"{name}.offer.json", offer)
        self.member(d, f"{name}.offer.json", offer, "none", wire=True)    # its wire copy LAST: what a fetch lists
        shutil.rmtree(work, ignore_errors=True)
        if s["rows"]:
            self.probe_piece = (k, i)
        self.say(f"{key}: offered as {form}" + (f" ({why})" if why else "") + f", {s['games']} games, {s['rows']} rows")
        self.leftovers(d, key, name, members)
        return form

    def finish_offer(self, k: int, i: int, d: Path, key: str, name: str, sb: bytes, s: dict, raw: bytes,
                     meta: str) -> str:
        """B1: p.offer.json there without its wire copy (a stop between the two). The form is NOT decided again. The
        offer must be this piece's and every member it names there with its bytes; only then its wire copy is
        written. Anything else: Stop 4 naming the piece and the file, nothing written."""
        op = d / f"{name}.offer.json"

        def bad(why):
            return Stop(4, f"{key}: {op.name} is there without its wire copy and {why}; nothing is written")
        try:
            ob = op.read_bytes()
            o = parse_canon(ob, op.name)
        except (OSError, ValueError) as e:
            raise bad(printable(e)) from None
        why = self.offer_fault(o, k, i, sha256_bytes(sb), s["rows"])    # the shape check P5 shares
        if why:
            raise bad(why)
        form, members = o["form"], o["members"]
        own = {f"{name}.seal.json": sb, f"{name}.raw.zz": raw, f"{name}.meta.xz": meta.encode("ascii")}
        for m in members:
            wire = m["name"].endswith(".seal.json")
            try:
                wd = (d / m["wire_name"]).read_bytes()
                data = zlib.decompress(wd) if wire else wd
                if m["name"] in own and PACK[m["codec"]][1](data) != own[m["name"]]:
                    raise ValueError("it does not decode to the piece's own content")
            except (OSError, ValueError, zlib.error, lzma.LZMAError) as e:
                raise bad(f"the member {m['wire_name']}: {printable(e)}") from None
            if [len(wd), sha256_bytes(wd), len(data), sha256_bytes(data)] != \
                    [m["wire_bytes"], m["wire_sha256"], m["bytes"], m["sha256"]]:
                raise bad(f"the member {m['wire_name']} is not the bytes the offer names")
        self.member(d, op.name, ob, "none", wire=True)  # its wire copy LAST, as in pack()
        if s["rows"]:
            self.probe_piece = (k, i)
        self.say(f"{key}: offered as {form}, finished from the files on disk: the offer was there without its wire "
                 f"copy (a stop between the two); nothing decided again")
        self.leftovers(d, key, name, members)
        return form

    def offer_fault(self, o, k: int, i: int, seal_sha: str, rows) -> str:
        """'' when o is this piece's offer as this packer writes it (1.6), else why not (B1 and P5 share it)."""
        name = f"p{i:06d}"
        want = {"schema": 2, "run_fingerprint": self.fp, "slot": k, "index": i, "seal_sha256": seal_sha}
        if not isinstance(o, dict) or sorted(o) != OFFER_KEYS or type(o["form"]) is not str \
                or o["form"] not in FORMS or any(type(o[n]) is not type(v) or o[n] != v for n, v in want.items()):
            return "it is not this piece's offer (keys, schema, run_fingerprint, slot, index, seal_sha256, form)"
        form, members = o["form"], o["members"]
        if rows == 0 and form != "raw":
            return "it offers a piece without rows as binpack"
        if not isinstance(members, list) or [(m.get("name"), m.get("codec")) if isinstance(m, dict) else None
                                             for m in members] != [(name + x, c) for x, c in FORMS[form]]:
            return f"its members are not those of the form {form}"
        for m in members:
            wire = m["name"].endswith(".seal.json")
            if sorted(m) != MEMBER_KEYS or m["wire_name"] != m["name"] + (".zz" if wire else ""):
                return f"the member {m['name']} is not written as this packer writes it"
        return ""

    def check_offered(self, k: int, i: int) -> None:
        """P5 (Neon 223800Z): a piece whose offer's wire copy is there is passed over only when that copy gives the
        offer back, the offer is this piece's (offer_fault) and every member's wire file is there at the size it
        names; else exit 4, nothing written (not a re-hash of every member: B1 does that before a wire copy exists).
        P1 (Astra 214929Z): such a piece with rows becomes the probe piece, so a restart in fallback mode probes on
        schedule even when every piece was offered before it."""
        key, name, d = f"w{k:03d}/p{i:06d}", f"p{i:06d}", self.out / f"w{k:03d}"

        def bad(why):
            return Stop(4, f"{key}: {name}.offer.json.zz is there but {why}; nothing is written")
        try:
            sb = (self.root / f"w{k:03d}" / "closed" / f"{name}.seal.json").read_bytes()
            ob = (d / f"{name}.offer.json").read_bytes()
            if zlib.decompress((d / f"{name}.offer.json.zz").read_bytes()) != ob:
                raise ValueError(f"it does not give {name}.offer.json back")
            o = parse_canon(ob, f"{name}.offer.json")
            s = parse_canon(sb, f"{name}.seal.json")
        except (OSError, ValueError, zlib.error) as e:
            raise bad(printable(e)) from None
        rows = s.get("rows") if isinstance(s, dict) else None
        why = self.offer_fault(o, k, i, sha256_bytes(sb), rows)
        if why:
            raise bad(why)
        for m in o["members"]:
            f = d / m["wire_name"]
            if not f.is_file() or f.stat().st_size != m["wire_bytes"]:
                raise bad(f"the member {m['wire_name']} is not there at {m['wire_bytes']} bytes")
        if type(rows) is int and rows > 0:
            self.probe_piece = (k, i)

    def leftovers(self, d: Path, key: str, name: str, members: list) -> None:
        """B1: a member of the other form, or a temporary name, left by a stop before this piece's offer existed. No
        offer names it, so no fetch takes it: it is left as it is and named once."""
        named = {m["wire_name"] for m in members} | {f"{name}.offer.json", f"{name}.offer.json.zz"}
        for x in (".seal.json.zz", ".binpack", ".meta.xz", ".raw.zz", ".offer.json", ".offer.json.zz"):
            for f in (name + x, name + x + ".tmp"):
                if f not in named and (d / f).exists():
                    self.say(f"{key}: {f} is left as it is: no offer names it")

    # ---- the passes ---------------------------------------------------------------------------------------------
    def probe(self) -> None:
        """Fallback mode: the round trip on the newest piece with rows this packer offered, in out/scratch only."""
        if self.mode != "fallback" or self.probe_piece is None or time.monotonic() - self.last_probe < self.a.probe_every:
            return
        self.last_probe = time.monotonic()
        k, i = self.probe_piece
        key = f"w{k:03d}/p{i:06d}"
        _, s, _, games = self.verify(k, i)
        work = self.scratch / "probe"
        shutil.rmtree(work, ignore_errors=True)
        why = self.round_trip(games, meta_of(games), s["raw_sha256"], work)
        shutil.rmtree(work, ignore_errors=True)
        if why:
            self.say(f"probe on {key}: the converter still fails: {why}")
        else:
            self.fails = 0
            self.set_mode("normal", "a probe passed", key)

    def ended(self, k: int):
        """The slot's `ended` line (1.8.4) when it is the journal's last whole line, else None."""
        try:
            data = (self.root / f"w{k:03d}" / "journal.txt").read_bytes()
        except OSError:
            return None
        lines = data[:data.rfind(b"\n") + 1].splitlines(keepends=True)
        try:
            last = parse_canon(lines[-1], "journal") if lines else None
        except ValueError:
            return None
        return last if isinstance(last, dict) and last.get("t") == "ended" else None

    def check_end(self, k: int, end: dict) -> None:
        """P2 (Neon 223800Z): a slot whose journal ends with `ended` is complete only when its seals here end exactly
        at that line's last_index and its last_seal is that seal's sha256 (the genesis text when none was sealed);
        else exit 3. The line is read before the scan (one_pass), so every seal it names is there for the scan."""
        slot, n = f"w{k:03d}", self.next[k]
        if type(end.get("last_index")) is not int or end["last_index"] != n - 1:
            raise Stop(3, f"{slot}: the journal's ended line names last_index {end.get('last_index')!r}, but the seals "
                          f"here end at index {n - 1} (-1: none); the slot is not complete")
        if n == 0:
            want, what = f"genesis:{self.fp}:{slot}", "the genesis text of this slot"
        else:
            want = file_sha256(self.root / slot / "closed" / f"p{n - 1:06d}.seal.json")
            what = f"the sha256 of p{n - 1:06d}.seal.json"
        if end.get("last_seal") != want:
            raise Stop(3, f"{slot}: the journal's ended line names last_seal {printable(end.get('last_seal'), 80)}, "
                          f"not {what}")

    def one_pass(self, final: bool) -> None:
        for k in self.slots:
            end = self.ended(k) if final else None     # P2: read BEFORE the scan
            closed, i = self.root / f"w{k:03d}" / "closed", self.next[k]
            while (closed / f"p{i:06d}.seal.json").exists():
                if (self.out / f"w{k:03d}" / f"p{i:06d}.offer.json.zz").exists():
                    self.check_offered(k, i)            # P5 and P1
                else:
                    self.counts[self.pack(k, i)] += 1
                i += 1
            self.next[k] = i
            if final and closed.is_dir():
                later = sorted(int(m.group(1)) for f in closed.iterdir() if (m := SEAL_NAME.match(f.name)))
                later = [j for j in later if j > i]
                if later:
                    raise Stop(3, f"w{k:03d}: p{i:06d}.seal.json is missing while {len(later)} later seals are there "
                                  f"(first p{later[0]:06d}); they are not offered")
            if end is not None:
                self.check_end(k, end)
        self.wire_copies()
        self.probe()

    def wire_copies(self) -> None:
        """2.3: the wire copy of every other file a fetch takes, create-only beside it (the bytes as they lie)."""
        files = [f for f in self.root.iterdir() if WIRED_IN_ROOT.match(f.name)]
        ranges = self.root / "ranges"
        if ranges.is_dir():
            files += [f for f in ranges.iterdir() if RANGE_SEAL.match(f.name)]
        for f in sorted(files):
            if f not in self.wired and f.is_file():
                data = f.read_bytes()
                try:
                    parse_canon(data, f.name)          # P4 (Neon 223800Z): only a whole canonical record is wired
                except ValueError as e:
                    raise Stop(4, f"{printable(e)}: its wire copy is not written") from None
                self.member(f.parent, f.name, data, "none", wire=True)
                self.wired.add(f)

    def run(self) -> int:
        self.say(f"packer of run {self.run_name}, slots {self.slots}: mode {self.mode}, converter {self.conv}")
        while True:
            final = (self.a.once or (self.root / "STOP_PACKER").exists()
                     or ((self.root / "FENCE.json").exists() and all(self.ended(k) for k in self.slots)))
            self.one_pass(final)
            if final:
                text = f"offered {self.counts['binpack']} pieces as binpack and {self.counts['raw']} as raw"
                self.say(f"ended: {text}")
                print(f"packer: {text}")
                return 0
            time.sleep(self.a.poll)


def main() -> int:
    ap = argparse.ArgumentParser(description="the packer of the server day (FORMATS 1.6)")
    ap.add_argument("--root", required=True)
    ap.add_argument("--converter", required=True)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--poll", type=float, default=5.0)
    ap.add_argument("--convert-seconds", type=float, default=600.0)
    ap.add_argument("--probe-every", type=float, default=600.0)
    a = ap.parse_args()
    for opt, v, ok, rule in (("--poll", a.poll, a.poll >= 0, "0 or more"),
                             ("--probe-every", a.probe_every, a.probe_every >= 0, "0 or more"),
                             ("--convert-seconds", a.convert_seconds, a.convert_seconds > 0, "more than 0")):
        if not (ok and math.isfinite(v)):              # P3 (Neon 223800Z): infinity is no bound
            print(f"packer: STOP (2): {opt} {v!r}: must be a finite number, {rule}")
            return 2
    packer = None
    try:
        packer = Packer(a)
        return packer.run()
    except Stop as e:
        code, text = e.code, str(e)
    except Exception as e:  # noqa: BLE001   never a traceback: the stop is named
        code, text = 4, f"{type(e).__name__}: {e}"
    if packer is not None:
        packer.say(f"STOP ({code}): {printable(text, 600)}")
    print(f"packer: STOP ({code}): {printable(text, 600)}")
    return code


if __name__ == "__main__":
    sys.exit(main())

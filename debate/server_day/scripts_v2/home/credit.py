"""Opus 2026-11-23, A3d part 3 (FORMATS 2.3, A26): stage b at HOME, part 1: THE CREDIT OF A ROUND. Standard library.

    credit.py --home DIR --fingerprint HEX64

Beside custody.py (stage a1: the run header, the schedules, the receipts, the kept seals) and the outputs of
content.py (stage a2: the verdicts, content/equal.sqlite, conflicts/), which it reads and never writes. ONE PASS
decides the rounds in rising order and stops at the first round that WAITS or HOLDS: a round is decided only when
every earlier round is, because a repeat is judged against the credit of the rounds before it (2.2, "credit goes to
the first ELIGIBLE game in the frozen order (round, slot, counter)").

ROUND r WAITS while anything of it is still on the way, and HOLDS (an alarm line; nothing is decided) when home's
evidence contradicts itself. For every slot k with a row (k, r) in the newest schedule home holds (the header's
pilot ranges are schedule 0; 1.2 [2.4]: every schedule lists ALL ranges of the day as they then stand):
 1 THE RANGE SEAL wire/ranges/r<NNNN>.w<NNN>.seal.json.zz (1.7): not at home, or written under a schedule newer than
   home's newest: WAITS. Its bytes canonical, schema 2,
   this run, round r, slot k, first and last the row's, the six counts summing to the range's length, the
   never-dispatched ids the range's tail, not_done in counter order inside the range: else HOLDS.
 2 THE PIECES first_index .. through_index of slot k (none when first_index is -1): each in C1 (a receipt; its kept
   seal read and hashed again; linked from the genesis; epochs not falling; no fork record) and judged (a verdict):
   else WAITS. first_prev_seal is the seal before first_index (the genesis text for index 0), through_seal the kept
   seal of through_index, every seal of round r, the range seal's games, rows and raw_bytes the sums of the pieces'
   seals: else HOLDS.
THE CREDIT LIST of a decided round, in the frozen order (slot, counter), one entry per id of every range:
 accepted (a2) with rows: "credited", or "repeat" with same_rows_as when an EARLIER credited game (an earlier round,
   or this round before it) has the same rows_digest (the verdicts' digests; a2 keeps them in its index too);
 accepted without rows: "credited" (an explicit record, no digest); noselfgame (a2): "noselfgame";
 set_aside (a2): "set_aside"; an id with a conflict record (conflicts/<id>.json, either kind): the ROUND WAITS
   (2.3: only A26's replay decides the id, and 2.2: who is credited is decided when every earlier round's
   eligibility is final; A26's replay is not built); an id held by two pieces with no conflict record: HOLDS;
 an id of not_done that holds no record: the range seal's state (refused, unfinished, dispatch_unknown); the
   never-dispatched tail: "never_dispatched"; an id that is in no record and not named by the range seal: "missing".
 Status: "complete" when every id is credited, repeat or noselfgame; otherwise "partial" (2.3: it credits nothing).
WRITTEN for a decided round, first in ONE transaction of stage/credited.sqlite: credited(rows_digest PRIMARY KEY,
game, round), the digest of every credited game of a COMPLETE round (a repeat looks its representative up here:
"a credited digest of a round below r"; within the round, in memory), and rounds(round PRIMARY KEY, status, games,
rows); an earlier interrupted insert of the same round is deleted first. Only after the commit, create-only and
without a time in it, so that a second pass writes the same bytes: stage/r<NNNN>/credit.json {schema 2,
run_fingerprint, round, status, range_seals [{slot, sha256}], games_in, raw_rows_in, ids [{game, slot, counter,
state, rows, rows_digest, same_rows_as}], missing_ids, set_aside_ids, conflict_ids, repeat_games}.
A partial round is decided here; its PUBLICATION as partial needs the home guard's DRAIN.json (2.3, part 2).
A decided round is never decided again and never read again (a day is about 22 million games: no pass reads every
credit list back): its rounds row stands for it. A credit.json the table does not know, or a round without one
below the table's highest round, HOLDS; the table gone or empty while a credit.json exists is STOP 4 (a new table
would credit every later repeat again: move stage/ aside and decide every round again). The table names its run
(meta: run_fingerprint, written when the table is new): a table of another run, or one that holds decided rounds and
names no run, is STOP 3 (a home reused by another run must not stand for this run's rounds). C1 and the conflict
records are read once a pass.
The last line: credit: decided .. rounds (.. complete, .. partial) this pass; credited .. games .. rows (C2 rows of
the credited games of every complete round); waits: <round: why, or none>; holds <0 or 1>   A HOLD prints a line
that begins "ALARM credit HOLDS". Exit codes: 0 a pass (also with a round that waits; also with no run header at
home yet); 2 a wrong call; 3 the run header at home cannot be trusted; 4 a file that cannot be read or written,
or stage/credited.sqlite gone or unreadable; 3 also for a table of another run; 5 a round HOLDS (the home
guard's alarm).
VERSION 2 (Neon 20261123T231800Z: six defects, each reproduced on Linux; known answers written before the code,
tmp/opus_scratch/credit_v2/KNOWN_ANSWERS_credit_v2_by_opus.md on the PC):
 C1 the range seal also: six counts >= 0; not_done in rising counter order (1.7) and below never_dispatched_first;
   epoch an int >= 1; short the bool of its row in the newest schedule; complete as FORMATS 1.7 [2.4] and the worker
   write it (no id unfinished, dispatch_unknown or never_dispatched: a refused id does not make a range incomplete,
   so Neon's `done + noselfgame == length` is not taken); first_index >= -1.
 C2 a verdict is checked before it is used: canonical (else HOLDS naming it), content's keys, schema 2, piece judged
   or refused (refused: no games and a why); judged: why null and as many games as its kept seal, each with
   content's keys, state accepted / noselfgame / set_aside and rows an int >= 0; rows_digest a hex text exactly for
   an accepted game with rows, none for noselfgame (and no rows) or set_aside; the games' rows sum to the seal's.
 C3 every receipt and fork record of the header's slots is read through custody's own reader at the start of a
   pass: another run's is STOP 3, one custody would not write is STOP 4. The walk of C1 ends where a piece is still
   on its way (no receipt, or its kept seal not at home yet: the rounds that need it WAIT), and with a reason at a
   fork record, a kept seal that is not the receipt's bytes, not canonical, not of this run, slot and index, a
   prev_seal that is not the seal before, or an epoch below 1 or below the one before: a round that needs that
   index or a later one HOLDS.
 C5 before any round: every wire/SCHEDULE.*.json.zz is a link of custody's chain (the next one present but not
   taken, or a name outside the chain's grammar: HOLDS; a later one while the next is absent: WAITS, a gap), and
   every stage/<folder>/credit.json and every rounds row of the table is a round of the newest schedule: else HOLDS.
 C6 the C1 pieces of slot k whose kept seal names round r are exactly the range seal's [first_index, through_index]
   (none for an empty range): else HOLDS naming the first one outside. With credit lists in stage/, the table is
   first opened READ-ONLY and must hold a decided round: else STOP 4, and nothing is written.
"""
import argparse
import json
import re
import sqlite3
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "run"))
sys.path.insert(0, str(HERE))
from custody import HEX64, Home  # noqa: E402
from record import RecordError, id_parts  # noqa: E402
from content import GAME_KEYS, VERDICT_KEYS  # noqa: E402   C2: the keys of the program that writes the verdicts
from worker import NOT_COMPLETE, STATES, Stop, canon, create_only, parse_canon, sha256_bytes  # noqa: E402

RECEIPT = re.compile(r"p([0-9]{6})\.receipt\.json")
FORK = re.compile(r"p([0-9]{6})\.fork\.json")
SCHED = re.compile(r"SCHEDULE\.([1-9][0-9]{0,2})\.json\.zz")       # the chain's grammar ends at 999 (packer, worker)
STAGE = re.compile(r"r([0-9]{4})")
RANGE_KEYS = sorted(["schema", "run", "run_fingerprint", "round", "slot", "epoch", "schedule", "first", "last", "short",
                     "complete", "first_index", "first_prev_seal", "through_index", "through_seal", "games", "rows",
                     "raw_bytes", "dispositions"])
MISSING = ("missing", "refused", "unfinished", "dispatch_unknown", "never_dispatched")   # no record the round needed


class Waits(Exception):
    """Something of the round is still on the way."""


class Holds(Exception):
    """Home's evidence contradicts itself: an alarm, nothing is decided."""


def is_int(*xs) -> bool:
    return all(type(x) is int for x in xs)


def need(ok, text: str) -> None:
    if not ok:
        raise Holds(text)


class Rounds:
    def __init__(self, home: Path, fp: str):
        self.H = Home(home, fp)                 # Stop(3) when wire/RUN.json.zz is not the pinned run
        self.home, self.fp = home, fp
        self.stage = home / "stage"
        self.db = self.stage / "credited.sqlite"
        self._chains, self._conflicts, self._broken, self._rounds_of, self.short = {}, None, {}, {}, {}

    # ---- what home holds ------------------------------------------------------------------------------------------
    def rows(self) -> dict:
        """(slot, round) -> (first, last) of the newest schedule home holds (0 = the header's pilot ranges).
        C5: every wire/SCHEDULE.*.json.zz is a link of custody's chain: SCHEDULE.<newest + 1> present (custody's walk
        stopped before it), or a name outside the grammar: HOLDS; a later one while the next is absent: WAITS (a gap:
        the next may still be on its way). self.short: (slot, round) -> short of the newest schedule's row."""
        rng = self.H.ranges()
        self.newest = n = max(rng)
        names = sorted(p.name for p in self.H.wire.glob("SCHEDULE.*.json.zz"))
        for x in names:
            need(SCHED.fullmatch(x),
                 f"wire/{x} is not a name of the schedule chain (SCHEDULE.<n>.json.zz, n from 1 to 999)")
        ns = {int(SCHED.fullmatch(x)[1]) for x in names}
        need(n + 1 not in ns,
             f"wire/SCHEDULE.{n + 1}.json.zz is at home and custody's chain stopped before it: it does not verify, or "
             f"it is not schedule {n + 1} of this run linked to schedule {n}")
        if any(m > n + 1 for m in ns):
            raise Waits(f"the schedule chain at home has a gap: SCHEDULE.{n + 1}.json.zz is not at home, "
                        f"SCHEDULE.{max(ns)}.json.zz is")
        src = self.H.h["pilot_ranges"] if n == 0 else parse_canon(
            zlib.decompress((self.H.wire / f"SCHEDULE.{n}.json.zz").read_bytes()), f"SCHEDULE.{n}.json")["ranges"]
        self.short = {(x["slot"], x["round"]): x.get("short") for x in src}
        return rng[n]

    def chain(self, k: int) -> dict:
        """C1 of slot k as a1 walks it: index -> kept seal (a dict, with its sha256) for the pieces inside C1, in
        order; walked once a pass. The walk ends where the next piece is still on its way: no receipt, or its kept
        seal not at home yet (the rounds that need it WAIT). C3: it ends with a reason, self._broken[k] = (index, why),
        at a fork record or a kept seal that does not link (kept()); a round that needs that index or a later one
        HOLDS (release). self._rounds_of[k]: round -> the C1 indices whose kept seal names that round (C6)."""
        if k in self._chains:
            return self._chains[k]
        d = self.H.cust / f"w{k:03d}"
        files = list(d.iterdir()) if d.is_dir() else []
        rs = {int(m[1]) for p in files if (m := RECEIPT.fullmatch(p.name))}
        forks = {int(m[1]) for p in files if (m := FORK.fullmatch(p.name))}
        out, by, prev, ep, i = {}, {}, f"genesis:{self.fp}:w{k:03d}", 0, 0
        while i in rs or i in forks:
            name = f"w{k:03d}/p{i:06d}"
            if i in forks:
                self._broken[k] = (i, f"{name} has a fork record at home (custody/{name}.fork.json): two offers of "
                                      "one index; nothing from it on is in C1")
                break
            rec = self.H.record(k, i)                   # read and bound by check_records at the start of the pass
            got = self.kept(k, i, rec, prev, ep)
            if got is None:
                break                                   # not kept at home yet: the rounds that need it WAIT
            why, s = got
            if why:
                self._broken[k] = (i, f"the kept seal of {name} {why}")
                break
            out[i] = dict(s, sha256=rec["seal_sha256"])
            by.setdefault(s["round"], []).append(i)
            prev, ep, i = rec["seal_sha256"], s["epoch"], i + 1
        self._chains[k], self._rounds_of[k] = out, by
        return out

    def kept(self, k: int, i: int, rec: dict, prev: str, ep: int):
        """The kept seal of piece (k, i) as C1 needs it: None when custody has not kept it at home yet; else
        (why, seal) with why None when it links to the seal before (C3)."""
        p = self.home / rec["kept"] / f"p{i:06d}.seal.json.zz"
        if not p.exists():
            return None
        try:
            sb = zlib.decompress(p.read_bytes())
        except zlib.error as e:
            return f"does not decompress: {e}", None
        if sha256_bytes(sb) != rec["seal_sha256"]:
            return "is not the bytes its receipt names (seal_sha256)", None
        try:
            s = parse_canon(sb, p.name)
        except ValueError as e:
            return f"is not a canonical record: {e}", None
        if not (isinstance(s, dict) and s.get("run_fingerprint") == self.fp and is_int(s.get("slot"), s.get("index"))
                and (s["slot"], s["index"]) == (k, i)):
            return "names another run, slot or index than its receipt", None
        if not (is_int(s.get("epoch"), s.get("round"), s.get("games"), s.get("rows"), s.get("raw_bytes"))
                and type(s.get("prev_seal")) is str):
            return "has not the fields of a piece seal (1.5)", None
        if s["prev_seal"] != prev:
            return f"names prev_seal {s['prev_seal'][:16]}..., not the seal of the piece before", None
        if s["epoch"] < max(ep, 1):
            return f"has epoch {s['epoch']}, below 1 or below {ep}, the epoch of the piece before", None
        return None, s

    def verdict(self, k: int, i: int):
        p = self.home / "content" / f"w{k:03d}" / f"p{i:06d}.verdict.json"
        if not p.exists():
            return None
        try:
            return parse_canon(p.read_bytes(), p.name)
        except ValueError as e:
            raise Holds(f"content/w{k:03d}/{p.name} is not a canonical record: {e}") from None

    @staticmethod
    def check_verdict(k: int, i: int, seal: dict, v) -> None:
        """C2: a verdict as content writes it (2.2), checked before anything of it is used; HOLDS naming it."""
        what = f"content/w{k:03d}/p{i:06d}.verdict.json"
        need(isinstance(v, dict) and sorted(v) == VERDICT_KEYS, f"{what}: its keys are not content's (2.2)")
        need(is_int(v["schema"]) and v["schema"] == 2,
             f"{what}: its schema is {v['schema']!r}, not 2")
        need(v["piece"] in ("judged", "refused"),
             f"{what}: piece is {v['piece']!r}, not judged or refused")
        gs = v["games"]
        if v["piece"] == "refused":
            need(gs == [] and type(v["why"]) is str, f"{what}: a refused piece with games or without a why")
            return
        need(v["why"] is None and isinstance(gs, list) and len(gs) == seal["games"],
             f"{what}: judged with {len(gs) if isinstance(gs, list) else gs!r} games, its kept seal holds "
             f"{seal['games']}")
        for g in gs:
            need(isinstance(g, dict) and sorted(g) == GAME_KEYS,
                 f"{what}: a game record whose keys are not content's (2.2)")
            need(g["state"] in ("accepted", "noselfgame", "set_aside"),
                 f"{what}: the state {g['state']!r} of {g['game']} is not accepted, noselfgame or set_aside")
            need(is_int(g["rows"]) and g["rows"] >= 0,
                 f"{what}: the rows of {g['game']} are {g['rows']!r}, not a number >= 0")
            dg = g["rows_digest"]
            if g["state"] == "accepted":
                need(type(dg) is str and HEX64.fullmatch(dg) is not None if g["rows"] else dg is None,
                     f"{what}: the rows_digest of {g['game']} is not what 2.2 writes for an accepted game of "
                     f"{g['rows']} rows")
            elif g["state"] == "noselfgame":
                need(g["rows"] == 0 and dg is None,
                     f"{what}: {g['game']} is noselfgame with rows or a rows_digest")
            else:
                need(dg is None,
                     f"{what}: {g['game']} is set_aside with a rows_digest")
        need(sum(g["rows"] for g in gs) == seal["rows"],
             f"{what}: the rows of its games do not sum to its kept seal's {seal['rows']}")

    def range_seal(self, k: int, r: int, first: int, last: int) -> tuple:
        """(sha256, record) of the range seal of (k, r), checked as 1.7 says."""
        name = f"r{r:04d}.w{k:03d}.seal.json"
        p = self.H.wire / "ranges" / (name + ".zz")
        if not p.exists():
            raise Waits(f"the range seal {name} is not at home")
        try:
            b = zlib.decompress(p.read_bytes())
            s = parse_canon(b, name)
        except (zlib.error, ValueError) as e:
            raise Holds(f"the range seal {name} is not a canonical record: {e}") from None
        need(isinstance(s, dict) and sorted(s) == RANGE_KEYS, f"{name} has not the keys of 1.7")
        need(s["schema"] == 2 and s["run"] == self.H.h["run"] and s["run_fingerprint"] == self.fp,
             f"{name} is not of this run")
        need(is_int(s["schedule"]) and s["schedule"] >= 0, f"{name}: its schedule is not a number")
        if s["schedule"] > self.newest:
            raise Waits(f"{name} was written under schedule {s['schedule']}; home holds schedule {self.newest}")
        need((s["round"], s["slot"], s["first"], s["last"]) == (r, k, first, last),
             f"{name} is not round {r}, slot {k}, [{first}, {last}] of the schedule")
        d = s["dispositions"]
        need(isinstance(d, dict) and sorted(d) == sorted(list(STATES) + ["never_dispatched_first", "not_done"])
             and is_int(*(d[x] for x in STATES)) and sum(d[x] for x in STATES) == last - first + 1,
             f"{name}: the six counts do not sum to the range's {last - first + 1} ids")
        need(all(d[x] >= 0 for x in STATES), f"{name}: a count below 0")       # implied by the rules around it
        nd = d["never_dispatched_first"]
        need((nd is None and d["never_dispatched"] == 0) or
             (is_int(nd) and first <= nd <= last and d["never_dispatched"] == last - nd + 1),
             f"{name}: the never-dispatched ids are not the range's tail")
        nd_ = d["not_done"]
        four = ("noselfgame", "refused", "unfinished", "dispatch_unknown")
        need(isinstance(nd_, list) and all(isinstance(x, list) and len(x) == 2 and type(x[0]) is str and x[1] in four
                                           for x in nd_)
             and all([x[1] for x in nd_].count(st) == d[st] for st in four),
             f"{name}: not_done does not list the ids of the four counts")
        cs = []
        for x in nd_:
            try:
                run, kk, c = id_parts(x[0])
            except RecordError:
                raise Holds(f"{name}: not_done names {x[0]!r}, not a game id") from None
            need(run == self.H.h["run"] and kk == k and first <= c <= last,
                 f"{name}: not_done names {x[0]}, not an id of its range")
            cs.append(c)
        need(all(a < b for a, b in zip(cs, cs[1:])),
             f"{name}: not_done is not in rising counter order (1.7)")
        need(nd is None or all(c < nd for c in cs),
             f"{name}: not_done names an id at or after never_dispatched_first {nd}")
        need(is_int(s["epoch"]) and s["epoch"] >= 1,
             f"{name}: its epoch {s['epoch']!r} is not a number >= 1")
        need(type(s["short"]) is bool and s["short"] is self.short.get((k, r)),
             f"{name}: short {s['short']!r} is not the short of its row in schedule {self.newest} "
             f"({self.short.get((k, r))!r})")
        need(type(s["complete"]) is bool and s["complete"] == (sum(d[x] for x in NOT_COMPLETE) == 0),
             f"{name}: complete {s['complete']!r} is not what its counts say (FORMATS 1.7 [2.4]: no id unfinished, "
             "dispatch_unknown or never_dispatched)")
        need(is_int(s["first_index"], s["through_index"], s["games"], s["rows"], s["raw_bytes"])
             and (s["first_index"] == -1) == (s["through_index"] == -1) and s["first_index"] <= s["through_index"],
             f"{name}: first_index and through_index are not a range of pieces")
        need(s["first_index"] >= -1,
             f"{name}: first_index {s['first_index']} is below -1")
        return sha256_bytes(b), s

    def release(self, r: int, rows: dict) -> list:
        """Every slot of round r: (k, range seal sha256, range seal, [(index, kept seal, verdict)]); else Waits or
        Holds with the reason."""
        out = []
        for (k, rr), (first, last) in sorted(rows.items()):
            if rr != r:
                continue
            sha, s = self.range_seal(k, r, first, last)
            c1 = self.chain(k)
            outside = [i for i in self._rounds_of[k].get(r, []) if not s["first_index"] <= i <= s["through_index"]]
            if outside:
                raise Holds(f"r{r:04d}.w{k:03d}: C1 holds w{k:03d}/p{outside[0]:06d} of round {r} outside its range "
                            f"seal's pieces [{s['first_index']}, {s['through_index']}]")
            pieces = []
            if s["first_index"] >= 0:
                for i in range(s["first_index"], s["through_index"] + 1):
                    if i not in c1:
                        if k in self._broken:
                            raise Holds(self._broken[k][1])
                        raise Waits(f"w{k:03d}/p{i:06d} of round {r} is not in custody's chain (C1) yet")
                    v = self.verdict(k, i)
                    if v is None:
                        raise Waits(f"w{k:03d}/p{i:06d} of round {r} has no content verdict yet")
                    self.check_verdict(k, i, c1[i], v)
                    pieces.append((i, c1[i], v))
                first_prev = c1[s["first_index"]]["prev_seal"]
                need(first_prev == s["first_prev_seal"], f"r{r:04d}.w{k:03d}: first_prev_seal is not the seal before "
                                                         f"p{s['first_index']:06d} at home ({first_prev})")
                need(c1[s["through_index"]]["sha256"] == s["through_seal"],
                     f"r{r:04d}.w{k:03d}: through_seal {s['through_seal']} is not the kept seal of "
                     f"p{s['through_index']:06d} at home ({c1[s['through_index']]['sha256']})")
                need(all(p[1]["round"] == r for p in pieces), f"r{r:04d}.w{k:03d}: a piece of another round in its range")
                need([s["games"], s["rows"], s["raw_bytes"]] ==
                     [sum(p[1][x] for p in pieces) for x in ("games", "rows", "raw_bytes")],
                     f"r{r:04d}.w{k:03d}: games, rows or raw_bytes are not the sums of its pieces' seals")
            else:
                need(s["first_prev_seal"] is None and s["through_seal"] is None and
                     (s["games"], s["rows"], s["raw_bytes"]) == (0, 0, 0), f"r{r:04d}.w{k:03d}: a range without a "
                     "piece names a seal or holds games")
            out.append((k, sha, s, pieces))
        return out

    def conflicts(self) -> set:
        """Every game id that a conflict record at home names (2.3: both kinds, one folder); read once a pass."""
        if self._conflicts is not None:
            return self._conflicts
        d = self.home / "conflicts"
        out = set()
        for p in sorted(d.glob("*.json")) if d.is_dir() else []:
            try:
                c = json.loads(p.read_bytes())
            except ValueError:
                raise Holds(f"conflicts/{p.name} is not a record") from None
            need(isinstance(c, dict) and type(c.get("game")) is str and c.get("run_fingerprint") == self.fp,
                 f"conflicts/{p.name} is not a conflict record of this run")
            out.add(c["game"])
        self._conflicts = out
        return out

    @staticmethod
    def earlier(con, digest: str, r: int):
        """The credited game of a COMPLETE round below r with these rows, or None."""
        row = con.execute("SELECT game FROM credited WHERE rows_digest = ? AND round < ?", (digest, r)).fetchone()
        return row[0] if row else None

    def decide(self, r: int, rel: list, con) -> tuple:
        """(the credit list of round r, {rows_digest: id} of its credited games when it is complete, else {})."""
        conflicts, ids, mine = self.conflicts(), [], {}
        for k, sha, s, pieces in rel:
            held = {}
            for i, seal, v in pieces:
                need(v.get("run_fingerprint") == self.fp and (v.get("slot"), v.get("index")) == (k, i)
                     and v.get("seal_sha256") == seal["sha256"] and v.get("round") == r,
                     f"the verdict of w{k:03d}/p{i:06d} is not of its kept seal (round {r})")
                for g in v["games"] if v["piece"] == "judged" else []:
                    run, kk, c = id_parts(g["game"])
                    need(run == self.H.h["run"] and kk == k and s["first"] <= c <= s["last"],
                         f"{g['game']} in w{k:03d}/p{i:06d} is not an id of r{r:04d}.w{k:03d}")
                    held.setdefault(c, []).append(g)
            named = {}
            for gid, st in s["dispositions"]["not_done"]:
                run, kk, c = id_parts(gid)
                need(run == self.H.h["run"] and kk == k and s["first"] <= c <= s["last"] and c not in named,
                     f"r{r:04d}.w{k:03d}: not_done names {gid}, not once an id of its range")
                named[c] = st
            nd = s["dispositions"]["never_dispatched_first"]
            for c in range(s["first"], s["last"] + 1):
                gid = f"{self.H.h['run']}-w{k:03d}-g{c:08d}"
                gs, said = held.get(c, []), named.get(c, "never_dispatched" if nd is not None and c >= nd else "done")
                e = {"game": gid, "slot": k, "counter": c, "rows": 0, "rows_digest": None, "same_rows_as": None}
                if gid in conflicts:
                    raise Waits(f"{gid} has a conflict record; A26's replay decides it (FORMATS 2.3)")
                if len(gs) > 1:
                    raise Holds(f"{gid} is held by {len(gs)} pieces of its range and no conflict record at home names it")
                if gs:
                    g = gs[0]
                    need((g["state"] == "noselfgame") == (said == "noselfgame") and said in ("done", "noselfgame"),
                         f"{gid}: the record is {g['state']}, the range seal says {said}")
                    e["rows"], e["rows_digest"] = g["rows"], g["rows_digest"]
                    if g["state"] == "accepted":
                        first = (self.earlier(con, g["rows_digest"], r) or mine.get(g["rows_digest"])
                                 if g["rows_digest"] else None)
                        e["state"], e["same_rows_as"] = ("repeat", first) if first else ("credited", None)
                        if g["rows_digest"] and not first:
                            mine[g["rows_digest"]] = gid
                    else:
                        e["state"] = g["state"]                       # noselfgame or set_aside
                else:
                    e["state"] = "missing" if said == "done" else said
                ids.append(e)
        partial = [e for e in ids if e["state"] not in ("credited", "repeat", "noselfgame")]
        return {"schema": 2, "run_fingerprint": self.fp, "round": r, "status": "partial" if partial else "complete",
                "range_seals": [{"slot": k, "sha256": sha} for k, sha, _s, _p in rel],
                "games_in": sum(s["games"] for _k, _h, s, _p in rel), "raw_rows_in": sum(s["rows"] for _k, _h, s, _p in rel),
                "ids": ids, "missing_ids": [e["game"] for e in ids if e["state"] in MISSING],
                "set_aside_ids": [e["game"] for e in ids if e["state"] == "set_aside"],
                "conflict_ids": [e["game"] for e in ids if e["state"] == "conflict"],
                "repeat_games": sum(e["state"] == "repeat" for e in ids)}, ({} if partial else mine)

    def strays(self, con, rows: dict) -> None:
        """C5: every credit list in stage/ and every rounds row of the table is a round of the newest schedule."""
        sched = {rr for (_k, rr) in rows}
        for p in sorted(self.stage.glob("*/credit.json")):
            m = STAGE.fullmatch(p.parent.name)
            need(m and int(m[1]) in sched,
                 f"stage/{p.parent.name}/credit.json is not a round of schedule {self.newest}")
        stray_rounds = sorted(x for (x,) in con.execute("SELECT round FROM rounds") if x not in sched)
        if stray_rounds:
            raise Holds(f"stage/credited.sqlite holds round {stray_rounds[0]}, not a round of schedule {self.newest}")

    def table(self):
        """stage/credited.sqlite, made on first use; STOP 4 when it is gone or empty while a credit list exists."""
        if any(self.stage.glob("r*/credit.json")) and (not self.db.is_file() or self.db.stat().st_size == 0):
            raise Stop(4, "stage/credited.sqlite is gone while decided rounds exist: a new table would credit every "
                          "later repeat again; move stage/ aside and decide every round again")
        if any(self.stage.glob("r*/credit.json")):     # C6 (Neon 231800Z 6): looked at READ-ONLY before any write
            ro = sqlite3.connect(f"{self.db.resolve().as_uri()}?mode=ro", uri=True)
            try:
                held = ro.execute("SELECT COUNT(*) FROM rounds").fetchone()[0]
            except sqlite3.Error:
                held = 0
            finally:
                ro.close()
            if not held:
                raise Stop(4, "stage/credited.sqlite holds no decided round while stage/ holds credit lists: a table "
                              "made again would credit every later repeat again; move stage/ aside and decide every "
                              "round again (nothing was written)")
        self.stage.mkdir(exist_ok=True)
        con = sqlite3.connect(self.db, isolation_level=None)
        con.execute("CREATE TABLE IF NOT EXISTS credited (rows_digest TEXT PRIMARY KEY, game TEXT NOT NULL, "
                    "round INTEGER NOT NULL)")
        con.execute("CREATE TABLE IF NOT EXISTS rounds (round INTEGER PRIMARY KEY, status TEXT NOT NULL, "
                    "games INTEGER NOT NULL, rows INTEGER NOT NULL)")
        con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        row = con.execute("SELECT value FROM meta WHERE key = 'run_fingerprint'").fetchone()
        if row is None and con.execute("SELECT COUNT(*) FROM rounds").fetchone()[0]:
            con.close()
            raise Stop(3, "stage/credited.sqlite holds decided rounds and names no run")
        if row is None:
            con.execute("INSERT INTO meta VALUES ('run_fingerprint', ?)", (self.fp,))
        elif row[0] != self.fp:
            con.close()
            raise Stop(3, f"stage/credited.sqlite belongs to another run (fingerprint {str(row[0])[:16]}...), not to "
                          "the pinned run")
        return con

    @staticmethod
    def record(con, r: int, status: str, mine: dict, games: int, rows: int) -> None:
        """Round r into the table in ONE transaction; an earlier interrupted insert of r is deleted first."""
        con.execute("BEGIN IMMEDIATE")
        try:
            con.execute("DELETE FROM credited WHERE round = ?", (r,))
            con.executemany("INSERT INTO credited VALUES (?, ?, ?)", [(dg, g, r) for dg, g in sorted(mine.items())])
            con.execute("INSERT OR REPLACE INTO rounds VALUES (?, ?, ?, ?)", (r, status, games, rows))
            con.execute("COMMIT")
        except BaseException:
            con.execute("ROLLBACK")
            raise

    def one_pass(self) -> int:
        self.H.check_records()                          # C3, C4: STOP 3 or 4 before anything is decided or written
        self._chains, self._conflicts, self._broken, self._rounds_of = {}, None, {}, {}
        t, waits, holds = dict(decided=0, complete=0, partial=0, games=0, rows=0), "none", 0
        try:
            rows = self.rows()                          # C5: the schedule files at home
        except Waits as e:
            print(f"WAITS schedule: {e}")
            return self.last(t, f"schedule: {e}", 0)
        except Holds as e:
            print(f"ALARM credit HOLDS: {e}")
            return self.last(t, "none", 1)
        con = self.table()
        try:
            try:
                self.strays(con, rows)                  # C5: no credit list or rounds row outside the schedule
            except Holds as e:
                holds, rows = 1, {}
                print(f"ALARM credit HOLDS: {e}")
            top = con.execute("SELECT MAX(round) FROM rounds").fetchone()[0]
            for r in sorted({rr for (_k, rr) in rows}):
                p = self.stage / f"r{r:04d}" / "credit.json"
                try:
                    known = con.execute("SELECT status, games, rows FROM rounds WHERE round = ?", (r,)).fetchone()
                    if p.exists():
                        need(known is not None, f"stage/r{r:04d}/credit.json exists and stage/credited.sqlite has no "
                                                f"row for round {r}")
                        status, games, nrows = known
                    else:
                        need(top is None or top <= r, f"round {r} has no credit list and stage/credited.sqlite holds "
                                                      f"round {top}: a later round is decided")
                        c, mine = self.decide(r, self.release(r, rows), con)
                        done = [e for e in c["ids"] if e["state"] == "credited"] if c["status"] == "complete" else []
                        status, games, nrows = c["status"], len(done), sum(e["rows"] for e in done)
                        self.record(con, r, status, mine, games, nrows)
                        p.parent.mkdir(parents=True, exist_ok=True)
                        create_only(p, canon(c))
                        t["decided"] += 1
                        t[status] += 1
                        print(f"round {r}: {status}; {len(c['ids'])} ids, repeat {c['repeat_games']}, missing "
                              f"{len(c['missing_ids'])}, set aside {len(c['set_aside_ids'])}, conflict "
                              f"{len(c['conflict_ids'])}")
                except Waits as e:
                    waits = f"round {r}: {e}"
                    print(f"WAITS {waits}")
                    break
                except (Holds, RecordError, KeyError, TypeError, ValueError) as e:
                    holds = 1
                    print(f"ALARM credit HOLDS round {r}: {e}")
                    break
                if status == "complete":
                    t["games"] += games
                    t["rows"] += nrows
        finally:
            con.close()
        return self.last(t, waits, holds)

    @staticmethod
    def last(t: dict, waits: str, holds: int) -> int:
        print(f"credit: decided {t['decided']} rounds ({t['complete']} complete, {t['partial']} partial) this pass; "
              f"credited {t['games']} games {t['rows']} rows; waits: {waits}; holds {holds}")
        return 5 if holds else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--home", required=True)
    ap.add_argument("--fingerprint", required=True)
    try:
        a = ap.parse_args()
    except SystemExit:
        return 2
    if not HEX64.fullmatch(a.fingerprint) or not Path(a.home).is_dir():
        print("credit: STOP (2): --home must be a folder and --fingerprint 64 lowercase hex")
        return 2
    try:
        R = Rounds(Path(a.home), a.fingerprint)
        if R.H.h is None:
            print("credit: no run header at home yet; nothing to do")
            return 0
        return R.one_pass()
    except Stop as e:
        print(f"credit: STOP ({e.code}): {e}")
        return e.code
    except OSError as e:
        print(f"credit: STOP (4): {e}")
        return 4
    except sqlite3.Error as e:
        print(f"credit: STOP (4): stage/credited.sqlite: {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())

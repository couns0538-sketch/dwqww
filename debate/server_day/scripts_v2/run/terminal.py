"""Opus 2026-11-23: the terminal inventory TERMINAL.jsonl (A3c; FORMATS 1.9, after 1.8). Standard library and the
worker's own helpers. The server guard writes it once the packer has made its last pass (1.8 point 4), before
guard/CLOSED.json; this file is also a program for a person or a test:

    terminal.py --root DIR

THE LINES (1.9), each canonical with one LF:
 1. RUN.json's bytes. 2. Every SCHEDULE.<n>.json from 1 to n, its bytes (the chain checked: no gap, `n`, this run,
    `prev` linked), or `{"n":0,"t":"schedule"}` when there is none. 3. FENCE.json's bytes (none: refused).
 4. Per slot in the header's order: the slot line {epochs (its epoch lines as written), last_index, last_seal (the
    end of its seal chain; -1 and the genesis text without a seal), slot, state ("ended" when the journal's last
    complete line is `ended`, else "unreconciled"), t "slot"}; one piece line a seal of the chain {index, offer (the
    plain offer's sha256 when its wire file .zz is there; else null), offered_bytes (the members' wire_bytes; 0),
    packed_bytes (the `bytes` of the members other than the seal; null), raw_bytes, seal, slot, t "piece"}; the bytes
    of each of the slot's range seals, by round; one id line {game, state, t "id", why} for every [id, state] of a
    range seal's not_done (why: refused and unfinished from the id's journal line, an unfinished id without one from
    its failed line; noselfgame "nomoves"; dispatch_unknown a fixed text, and the id has no journal line).
 5. The footer {completed_at_utc, cutoff_reached (the fence's why is "D"), fingerprint (sha256 of every byte before
    it), ids (the six counts summed over the range seals), offered_bytes, pieces, pieces_offered, raw_rows (the
    chain seals' rows), slots {ended, unreconciled}, stop_reason (the fence's why), t "footer"}.
Refused (exit 4, nothing written) where the spool contradicts itself: a seal that does not descend from the one before,
a seal missing before later ones, a `closed` line that names no seal of the chain, an ended slot whose chain does not
end at its ended line, an offer of another seal or whose .zz is not its bytes, an offer outside the chain, a range seal
whose pieces are not the chain's, an id state without its journal line, a line after an `ended` line. The ids of an
unreconciled slot's open range have no range seal: they are counted nowhere, and the slot's state says so.
VERSION 2 (Opus 2026-11-24; the NOT YETs of Astra 65c89bdc and Neon 20261123T222600Z section 3) refuses as well: RUN.json
or FENCE.json not schema 2, a FENCE.json without exactly FENCE_KEYS; a SCHEDULE.*.json name outside the worker's
grammar; a schedule row or pilot row the worker's check_rows refuses (A0); an offer's wire file outside the chain; a
range seal whose round has no row in the schedule it names, or whose first, last and short are not that row's (A1, A2);
an ENDED slot without a range seal of every row of schedule L, the highest schedule its seals name (A3); a range seal's
wire copy that is not its bytes (A5); a range without a piece that names one or counts a game (B); counts below 0, not
summing to the range, not matching their not_done ids, a never_dispatched_first that does not fit, a not_done id outside
the range or not rising (C); a piece in two range seals, and a piece of an ENDED slot in none (E). A range seal whose
plain file is gone is read from its wire copy (A4). An ENDED slot's rows of the FINAL schedule that A3 does not require
and that have no seal (the guard may write a schedule after a slot ended) are named on the output, not refused.
WRITTEN create-only: TERMINAL.jsonl, then TERMINAL.jsonl.zz (zlib 6). A TERMINAL.jsonl found from an earlier run must be
this spool's (its bytes before the footer the same, its footer the same but for completed_at_utc): it is kept and a
missing .zz is written; otherwise refused and nothing changes. A second run changes nothing.
EXIT CODES: 0 there; 2 a wrong call; 4 refused or a file that cannot be written.
"""
import argparse
import re
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record import RecordError, id_parts  # noqa: E402
from worker import FENCE_KEYS, STATES, Stop, canon, check_rows, create_only, parse_canon, sha256_bytes  # noqa: E402

SCHED = re.compile(r"SCHEDULE\.([1-9][0-9]{0,2})\.json")        # the worker's grammar (load_schedules)
SEAL = re.compile(r"p([0-9]{6})\.seal\.json")
OFFER = re.compile(r"p([0-9]{6})\.offer\.json(?:\.zz)?")
ROWF = ("first", "last", "short")
DOUBT = "no line: in doubt after an earlier play epoch (1.8 point 3)"


class Refused(Exception):
    pass


def need(ok, text: str) -> None:
    if not ok:
        raise Refused(text)


def rec(path: Path, what: str, zz: bool = False):
    """(bytes, object) of a canonical record; zz: the file is its wire copy (zlib) and the decoded bytes are read."""
    try:
        data = path.read_bytes()
        if zz:
            data = zlib.decompress(data)
        return data, parse_canon(data, what)
    except (OSError, zlib.error) as e:
        raise Refused(f"{what} cannot be read ({type(e).__name__})") from None
    except ValueError as e:
        raise Refused(str(e)) from None


def same_zz(zz: Path, data: bytes) -> bool:
    try:
        return zlib.decompress(zz.read_bytes()) == data
    except (OSError, zlib.error):
        return False


def journal(path: Path, what: str) -> list:
    """The complete lines: a torn last line (no LF) is not durable and is not read."""
    if not path.exists():
        return []
    out = []
    for n, ln in enumerate(path.read_bytes().split(b"\n")[:-1], 1):
        try:
            obj = parse_canon(ln + b"\n", f"{what} line {n}")
        except ValueError as e:
            raise Refused(str(e)) from None
        need(isinstance(obj, dict) and isinstance(obj.get("t"), str), f"{what} line {n}: not a journal line")
        out.append(obj)
    return out


def slot_lines(root: Path, fp: str, run, scheds: list, k: int, tally: dict) -> list:
    """scheds[s]: the rows of schedule s (0 = the header's pilot_ranges), each list passed by check_rows."""
    name = f"w{k:03d}"
    sdir, odir, genesis = root / name, root / "out" / name, f"genesis:{fp}:{name}"
    jl = journal(sdir / "journal.txt", f"{name}/journal.txt")
    chain, prev = [], genesis                           # (sha256, seal) of index 0, 1, ...
    while (sdir / "closed" / f"p{len(chain):06d}.seal.json").exists():
        i = len(chain)
        b, s = rec(sdir / "closed" / f"p{i:06d}.seal.json", f"{name}/closed/p{i:06d}.seal.json")
        need(isinstance(s, dict) and s.get("run_fingerprint") == fp and s.get("slot") == k and s.get("index") == i
             and s.get("prev_seal") == prev and type(s.get("raw_bytes")) is int and type(s.get("rows")) is int,
             f"{name}/closed/p{i:06d}.seal.json does not descend from the seal before it (or the genesis)")
        prev = sha256_bytes(b)
        chain.append((prev, s))
    beyond = sorted(int(m[1]) for p in (sdir / "closed").glob("p*.seal.json")
                    if (m := SEAL.fullmatch(p.name)) and int(m[1]) > len(chain))
    if beyond:
        raise Refused(f"{name}: p{len(chain):06d}.seal.json is missing before later seals (p{beyond[0]:06d})")
    for ln in jl:
        if ln["t"] == "closed":
            ix = ln.get("index")
            need(type(ix) is int and 0 <= ix < len(chain) and ln.get("seal") == chain[ix][0],
                 f"{name}: the journal's closed line of index {ix} names no seal of the chain")
    ended = bool(jl) and jl[-1]["t"] == "ended"
    need(sum(ln["t"] == "ended" for ln in jl) == int(ended), f"{name}: its journal goes on after an ended line")
    last_index, last_seal = len(chain) - 1, chain[-1][0] if chain else genesis
    if ended:
        need(jl[-1].get("last_index") == last_index and jl[-1].get("last_seal") == last_seal,
             f"{name}: the ended line names index {jl[-1].get('last_index')}, the seals end at {last_index}")
    tally["ended" if ended else "unreconciled"] += 1
    out = [canon({"epochs": [ln for ln in jl if ln["t"] == "epoch"], "last_index": last_index, "last_seal": last_seal,
                  "slot": k, "state": "ended" if ended else "unreconciled", "t": "slot"})]
    stray = [int(m[1]) for p in odir.glob("p*.offer.json*") if (m := OFFER.fullmatch(p.name)) and int(m[1]) >= len(chain)]
    if stray:
        raise Refused(f"out/{name}: an offer of p{min(stray):06d}, which is not a seal of the chain")
    for ix, (x, s) in enumerate(chain):
        osha, ob, pb, what = None, 0, None, f"out/{name}/p{ix:06d}.offer.json"
        if (odir / f"p{ix:06d}.offer.json.zz").exists():   # the wire file the fetch takes: offered
            b, o = rec(odir / f"p{ix:06d}.offer.json", what)
            need(isinstance(o, dict) and o.get("run_fingerprint") == fp and o.get("slot") == k and o.get("index") == ix
                 and o.get("seal_sha256") == x and isinstance(o.get("members"), list),
                 f"{what} is not the offer of this seal (a fork, or another piece)")
            need(same_zz(odir / f"p{ix:06d}.offer.json.zz", b), f"{what}.zz does not decode to the plain offer")
            ms = o["members"]
            need(all(isinstance(m, dict) and isinstance(m.get("name"), str) and type(m.get("bytes")) is int
                     and type(m.get("wire_bytes")) is int for m in ms), f"{what}: a member without its sizes")
            osha, ob = sha256_bytes(b), sum(m["wire_bytes"] for m in ms)
            pb = sum(m["bytes"] for m in ms if m["name"] != f"p{ix:06d}.seal.json")
            tally["offered"] += 1
            tally["bytes"] += ob
        tally["pieces"] += 1
        tally["rows"] += s["rows"]
        out.append(canon({"index": ix, "offer": osha, "offered_bytes": ob, "packed_bytes": pb,
                          "raw_bytes": s["raw_bytes"], "seal": x, "slot": k, "t": "piece"}))
    rpat = re.compile(rf"r([0-9]{{4}})\.{name}\.seal\.json(?:\.zz)?")
    ids, spans, named, sealed = [], [], [], set()
    for r in sorted({int(m[1]) for p in (root / "ranges").glob(f"r*.{name}.seal.json*")
                     if (m := rpat.fullmatch(p.name))}):
        what = f"ranges/r{r:04d}.{name}.seal.json"
        plain, twin = root / what, root / f"{what}.zz"
        b, rs = rec(plain, what) if plain.exists() else rec(twin, f"{what}.zz", zz=True)    # A4: the wire copy
        d = rs.get("dispositions") if isinstance(rs, dict) else None
        need(isinstance(d, dict) and rs.get("run_fingerprint") == fp and rs.get("slot") == k and rs.get("round") == r
             and all(type(d.get(st)) is int for st in STATES) and isinstance(d.get("not_done"), list),
             f"{what}: not this run's, this slot's and this round's range seal")
        fi, ti = rs.get("first_index"), rs.get("through_index")
        if ti != -1:
            need(type(fi) is int and type(ti) is int and 0 <= fi <= ti < len(chain)
                 and rs.get("through_seal") == chain[ti][0]
                 and rs.get("first_prev_seal") == (genesis if fi == 0 else chain[fi - 1][0]),
                 f"{what}: its pieces are not the chain's (through_seal or first_prev_seal)")
            spans.append((fi, ti))
        else:                                           # B (1.7): a range without a piece names none and played none
            need(fi == -1
                 and rs.get("first_prev_seal") is None
                 and rs.get("through_seal") is None, f"{what}: a range without a piece names one (first_index, "
                                                     f"first_prev_seal or through_seal)")
            need(d["done"] + d["noselfgame"] == 0, f"{what}: it counts a game done, but it has no piece: no game")
        need(not plain.exists() or not twin.exists() or same_zz(twin, b),
             f"{what}.zz does not decode to the plain range seal")
        s = rs.get("schedule")                          # A1, A2: the row of the schedule the seal names
        rows = scheds[s] if type(s) is int and 0 <= s < len(scheds) else []
        row = next((x for x in rows if x["slot"] == k and x["round"] == r), {})
        need(row, f"{what}: no range of round {r} in the schedule it names ({str(s)[:12]})")
        need(canon({x: rs.get(x) for x in ROWF}) == canon({x: row.get(x) for x in ROWF}),
             f"{what}: not the schedule's range (first, last, short)")
        named.append(s)
        sealed.add(r)
        nd = d["not_done"]                              # C: the counts and their ids
        need(all(isinstance(p, list) and len(p) == 2 and all(isinstance(v, str) for v in p) for p in nd),
             f"{name}: a not_done entry that is not [id, state]")
        need(all(d[st] >= 0 for st in STATES), f"{what}: a count below 0 (every count must be >= 0)")
        need(sum(d[st] for st in STATES) == rs["last"] - rs["first"] + 1,
             f"{what}: the six counts do not sum to the range's size")
        need(all(d[st] == sum(p[1] == st for p in nd) for st in ("dispatch_unknown", "noselfgame", "refused",
                                                                 "unfinished")),
             f"{what}: a count is not the number of its not_done pairs")
        ndf = d.get("never_dispatched_first")
        need(ndf is None if d["never_dispatched"] == 0 else
             (type(ndf) is int and d["never_dispatched"] == rs["last"] - ndf + 1),
             f"{what}: never_dispatched_first does not fit never_dispatched")
        ctr = []
        for g, _ in nd:
            try:
                part = id_parts(g)
            except RecordError:
                part = None
            need(part is not None and part[:2] == (run, k) and rs["first"] <= part[2] <= rs["last"],
                 f"{what}: {g[:60]} is not an id of the range")
            ctr.append(part[2])
        need(all(x < y for x, y in zip(ctr, ctr[1:])), f"{what}: the not_done ids do not rise")
        out.append(b)
        for st in STATES:
            tally["ids"][st] += d[st]
        ids += d["not_done"]
    spans.sort()
    for (_, t0), (f1, _) in zip(spans, spans[1:]):     # E1: a piece lies in one range at most
        need(f1 > t0, f"{name}: p{f1:06d} is in two range seals")
    if ended:
        L = max(named, default=0)                       # A3: the slot held a schedule at least this high
        for want in (x for x in scheds[L] if x["slot"] == k):
            need(want["round"] in sealed, f"ranges/r{want['round']:04d}.{name}.seal.json is missing (and no wire copy)")
        miss = sorted(set(range(len(chain))) - {i for f0, t0 in spans for i in range(f0, t0 + 1)})
        if miss:                                        # E2: every piece of an ended slot lies in a range
            raise Refused(f"{name}: p{miss[0]:06d} is not in a range seal of the ended slot")
        late = sorted(x["round"] for x in scheds[-1] if x["slot"] == k and x["round"] not in sealed)
        if late:
            print(f"terminal: note: {name} ended without a range seal of round(s) {late}: no seal of the slot names a "
                  f"schedule that has them (the slot ended before them, or their seals are lost); their ids are not in "
                  f"the inventory")
    for pair in ids:
        need(isinstance(pair, list) and len(pair) == 2 and all(isinstance(v, str) for v in pair),
             f"{name}: a not_done entry that is not [id, state]")
        g, st = pair
        mine = [ln for ln in jl if ln.get("game") == g]
        if st == "dispatch_unknown":
            need(not mine, f"{name}: {g} is dispatch_unknown and has a journal line")
            why = DOUBT
        elif st == "noselfgame":
            need(any(ln["t"] == "noselfgame" for ln in mine), f"{name}: {g} is noselfgame without its journal line")
            why = "nomoves"
        else:
            why = None
            for t in {"refused": ("refused",), "unfinished": ("unfinished", "failed")}.get(st, ()):
                whys = [ln.get("why") for ln in mine if ln["t"] == t]
                if whys:
                    why = whys[-1]
                    break
            need(isinstance(why, str), f"{name}: {g} is {st} without a journal line that says why")
        out.append(canon({"game": g, "state": st, "t": "id", "why": why}))
    return out


def body(root: Path):
    """The bytes before the footer, the fence, the counts."""
    hb, h = rec(root / "RUN.json", "RUN.json")
    fp = sha256_bytes(hb)
    need(isinstance(h, dict) and isinstance(h.get("slots"), list)
         and all(type(k) is int and 0 <= k <= 999 for k in h["slots"]), "RUN.json: no list of slots")
    need(type(h.get("schema")) is int and h["schema"] == 2, "RUN.json: not schema 2")
    scheds = [check_rows(h.get("pilot_ranges"), h["slots"], 0, "RUN.json pilot_ranges")]     # A0: the worker's rule
    lines = [hb]
    names = sorted(p.name for p in root.glob("SCHEDULE.*.json"))
    bad = [x for x in names if not SCHED.fullmatch(x)]
    if bad:                                             # the worker stops on such a name (Stop 4); so does this
        raise Refused(f"{bad[0]}: a schedule file name outside the worker's grammar (SCHEDULE.1.json to "
                      f"SCHEDULE.999.json)")
    nums = sorted(int(m[1]) for x in names if (m := SCHED.fullmatch(x)))
    need(nums == list(range(1, len(nums) + 1)), f"the schedules are not exactly 1 to {len(nums)}: {nums[:8]}")
    prev = "first"
    for n in nums:
        b, s = rec(root / f"SCHEDULE.{n}.json", f"SCHEDULE.{n}.json")
        need(isinstance(s, dict) and s.get("n") == n and s.get("run_fingerprint") == fp and s.get("prev") == prev,
             f"SCHEDULE.{n}.json is not schedule {n} of this run, linked to the one before it")
        scheds.append(check_rows(s.get("ranges"), h["slots"], n, f"SCHEDULE.{n}.json"))
        lines.append(b)
        prev = sha256_bytes(b)
    if not nums:
        lines.append(canon({"n": 0, "t": "schedule"}))
    need((root / "FENCE.json").exists(), "no FENCE.json: the inventory is written after the fence (1.8 point 1)")
    fb, f = rec(root / "FENCE.json", "FENCE.json")
    need(isinstance(f, dict) and f.get("run_fingerprint") == fp and isinstance(f.get("why"), str),
         "FENCE.json is not this run's fence")
    need(sorted(f) == FENCE_KEYS, "FENCE.json: not the keys of a fence")
    need(type(f.get("schema")) is int and f["schema"] == 2, "FENCE.json: not schema 2")
    lines.append(fb)
    tally = {"ended": 0, "unreconciled": 0, "pieces": 0, "offered": 0, "bytes": 0, "rows": 0,
             "ids": dict.fromkeys(STATES, 0)}
    for k in h["slots"]:
        lines += slot_lines(root, fp, h.get("run"), scheds, k, tally)
    return b"".join(lines), f, tally


def write(root: Path):
    """TERMINAL.jsonl and its .zz: (sha256, number of lines). Refused: nothing written."""
    data, fence, t = body(root)
    foot = {"completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cutoff_reached": fence["why"] == "D", "fingerprint": sha256_bytes(data), "ids": t["ids"],
            "offered_bytes": t["bytes"], "pieces": t["pieces"], "pieces_offered": t["offered"], "raw_rows": t["rows"],
            "slots": {"ended": t["ended"], "unreconciled": t["unreconciled"]}, "stop_reason": fence["why"],
            "t": "footer"}
    path, zz = root / "TERMINAL.jsonl", root / "TERMINAL.jsonl.zz"
    if path.exists():                                   # an earlier run's: kept only when it is this spool's
        full = path.read_bytes()
        try:
            old = parse_canon(full[len(data):], "TERMINAL.jsonl's footer") if full.startswith(data) else None
        except ValueError:
            old = None
        need(isinstance(old, dict) and dict(old, completed_at_utc=None) == dict(foot, completed_at_utc=None),
             "TERMINAL.jsonl exists and is not this spool's inventory: nothing changed")
    else:
        full = data + canon(foot)
        create_only(path, full)
    if zz.exists():
        need(same_zz(zz, full), "TERMINAL.jsonl.zz exists and does not decode to TERMINAL.jsonl")
    else:
        create_only(zz, zlib.compress(full, 6))
    return sha256_bytes(full), full.count(b"\n")


def main() -> int:
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--root", required=True)
    a = ap.parse_args()
    root = Path(a.root)
    if not root.is_dir():
        print(f"terminal: STOP (2): {a.root} is not a folder")
        return 2
    try:
        sha, n = write(root)
    except Refused as e:
        print(f"terminal: REFUSED (nothing written): {e}")
        return 4
    except (Stop, OSError) as e:
        print(f"terminal: STOP (4): {type(e).__name__}: {e}")
        return 4
    print(f"terminal: TERMINAL.jsonl {sha} ({n} lines) and TERMINAL.jsonl.zz in {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

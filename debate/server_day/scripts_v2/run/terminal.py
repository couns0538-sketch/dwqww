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
from worker import STATES, Stop, canon, create_only, parse_canon, sha256_bytes  # noqa: E402

SCHED = re.compile(r"SCHEDULE\.([1-9][0-9]*)\.json")
SEAL = re.compile(r"p([0-9]{6})\.seal\.json")
OFFER = re.compile(r"p([0-9]{6})\.offer\.json")
DOUBT = "no line: in doubt after an earlier play epoch (1.8 point 3)"


class Refused(Exception):
    pass


def need(ok, text: str) -> None:
    if not ok:
        raise Refused(text)


def rec(path: Path, what: str):
    """(bytes, object) of a canonical record."""
    try:
        data = path.read_bytes()
        return data, parse_canon(data, what)
    except OSError as e:
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


def slot_lines(root: Path, fp: str, k: int, tally: dict) -> list:
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
    stray = [int(m[1]) for p in odir.glob("p*.offer.json") if (m := OFFER.fullmatch(p.name)) and int(m[1]) >= len(chain)]
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
    rpat = re.compile(rf"r([0-9]{{4}})\.{name}\.seal\.json")
    ids = []
    for r in sorted(int(m[1]) for p in (root / "ranges").glob(f"r*.{name}.seal.json") if (m := rpat.fullmatch(p.name))):
        what = f"ranges/r{r:04d}.{name}.seal.json"
        b, rs = rec(root / what, what)
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
        out.append(b)
        for st in STATES:
            tally["ids"][st] += d[st]
        ids += d["not_done"]
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
    lines = [hb]
    nums = sorted(int(m[1]) for p in root.iterdir() if (m := SCHED.fullmatch(p.name)))
    need(nums == list(range(1, len(nums) + 1)), f"the schedules are not exactly 1 to {len(nums)}: {nums[:8]}")
    prev = "first"
    for n in nums:
        b, s = rec(root / f"SCHEDULE.{n}.json", f"SCHEDULE.{n}.json")
        need(isinstance(s, dict) and s.get("n") == n and s.get("run_fingerprint") == fp and s.get("prev") == prev,
             f"SCHEDULE.{n}.json is not schedule {n} of this run, linked to the one before it")
        lines.append(b)
        prev = sha256_bytes(b)
    if not nums:
        lines.append(canon({"n": 0, "t": "schedule"}))
    need((root / "FENCE.json").exists(), "no FENCE.json: the inventory is written after the fence (1.8 point 1)")
    fb, f = rec(root / "FENCE.json", "FENCE.json")
    need(isinstance(f, dict) and f.get("run_fingerprint") == fp and isinstance(f.get("why"), str),
         "FENCE.json is not this run's fence")
    lines.append(fb)
    tally = {"ended": 0, "unreconciled": 0, "pieces": 0, "offered": 0, "bytes": 0, "rows": 0,
             "ids": dict.fromkeys(STATES, 0)}
    for k in h["slots"]:
        lines += slot_lines(root, fp, k, tally)
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

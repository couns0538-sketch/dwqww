"""Opus 2026-11-24 (FORMATS 2.9 section 2.3 [2.1], [2.2]; the seats' spec home_guard.md): THE HOME GUARD'S DRAIN
RECORD, home/DRAIN.json. Standard library and custody's own readers. Known answers written before the code
(tmp/opus_scratch/drain/KNOWN_ANSWERS_drain_by_opus.md on the PC).

    drain.py --home DIR --fingerprint HEX64 --why "lease ended" | "declared stop" | "source gone since <UTC>"

ONE CALL, made by the home guard or a person when the fetch will bring nothing more. In this order:
 1 the call (exit 2): --why is "lease ended", "declared stop" or "source gone since YYYY-MM-DDTHH:MM:SSZ";
 2 the run header at home, custody's own check (exit 3); no header at home: REFUSED (exit 4), nothing of the run
   arrived and a record would name nothing;
 3 home/DRAIN.json already there: this run's, nothing is written (exit 0; the authority is not asked again); another
   run's (exit 3: a home folder serves one run); not the home guard's record (exit 4). It is never replaced;
 4 THE AUTHORITY (refused: exit 4): "lease ended" only when the PC's clock in UTC is at or after the header's
   lease_end_utc; "source gone since T" only when T is not after that clock; "declared stop" is a person's word;
 5 custody's receipts and fork records read and bound (custody's check_records: exit 3 or 4);
 6 WAITS (exit 0, nothing written): a check on data already in custody runs: a receipt without its content verdict,
   or an offer whose every member is at home and intact without a receipt (custody's next pass receipts it). The
   guard calls drain only after a fetch pass that left no member still receiving (FORMATS 2.1 [2.7]; the fetch is
   not this program's);
 7 THE MISSING LIST: every piece that is NAMED and has no receipt, named by the verified inventory
   (TERMINAL.jsonl.zz), a range seal at home (first_index .. through_index), the chain (an index below the slot's
   highest receipt) or an offer at home; each with named_by, seal_sha256 (every source that names one must agree,
   else HOLDS: the offer, the inventory, a range seal's through_seal, the prev_seal of the next piece's kept seal),
   offer_sha256 (the offer at home, the inventory; they must agree), wire (an offer that waits for members: each
   member not at home or not its bytes, with the offer's wire_bytes and wire_sha256; else null) and offered_bytes
   (the inventory's; else null). Then every row of the newest schedule home holds whose range seal is not at home.
   A range seal at home that is not one of this run, slot and round with a range of pieces: HOLDS (exit 5);
 8 home/DRAIN.json, canonical, create-only: {schema 2, run_fingerprint, at_utc, why, missing}, publish.py's keys.
The last line: drain: written (sha256 ..); why ..; missing .. pieces, .. range seals | drain: waits: .. |
drain: DRAIN.json of this run is at home ... A HOLD prints a line that begins "ALARM drain HOLDS".
read_drain() is the one reader of the record for credit.py (publish.py keeps its own; the tests compare them).
"""
import argparse
import json
import re
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "run"))
sys.path.insert(0, str(HERE))
from custody import HEX64, OFFER, RECEIPT, Bad, Home, Waits, canon_of, is_int, unzz, utc  # noqa: E402
from packer import MEMBER_KEYS  # noqa: E402
from worker import Stop, canon, create_only, parse_canon, sha256_bytes  # noqa: E402

KEYS = sorted(("schema", "run_fingerprint", "at_utc", "why", "missing"))
WHY = re.compile(r"lease ended|declared stop|source gone since .+")          # publish.py's patterns
UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
GONE = re.compile(r"source gone since ([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)")


class Holds(Exception):
    """Home's evidence contradicts itself: nothing is written."""


class Wait(Exception):
    """A check on data already in custody runs: nothing is written yet."""


def read_drain(home: Path, fp: str):
    """(sha256, record) of home/DRAIN.json, of whichever run; None when there is none. ValueError when it is not the
    home guard's record (canonical, the five keys, schema 2, run_fingerprint, at_utc, why, missing a list)."""
    p = home / "DRAIN.json"
    if not p.exists():
        return None
    b = p.read_bytes()
    d = parse_canon(b, "DRAIN.json")
    if not isinstance(d, dict) or sorted(d) != KEYS or d["schema"] != 2 or type(d["run_fingerprint"]) is not str \
            or type(d["at_utc"]) is not str or not UTC.fullmatch(d["at_utc"]) or type(d["why"]) is not str \
            or not WHY.fullmatch(d["why"]) or not isinstance(d["missing"], list):
        raise ValueError("DRAIN.json is not the home guard's record of 2.3 (schema 2, run_fingerprint, at_utc, why, "
                         "missing)")
    return sha256_bytes(b), d


def authority(H: Home, why: str, now: str):
    """None when the reason holds; else why not."""
    if why == "lease ended":
        end = H.h.get("lease_end_utc")
        if type(end) is not str or not UTC.fullmatch(end):
            return "the run header at home has no lease_end_utc of the form YYYY-MM-DDTHH:MM:SSZ"
        if now < end:
            return f"the lease ends at {end}; the PC's clock reads {now} (UTC)"
    elif why != "declared stop" and GONE.fullmatch(why)[1] > now:
        return f"'{why}' names a time after the PC's clock ({now}, UTC)"
    return None


def inventory_bytes(H: Home) -> dict:
    """(slot, index) -> offered_bytes of the piece lines of TERMINAL.jsonl.zz; called only after custody's
    inventory() verified the file (footer fingerprint, header bytes, no piece twice)."""
    data = zlib.decompress((H.wire / "TERMINAL.jsonl.zz").read_bytes())
    body = data[:data.rstrip(b"\n").rfind(b"\n") + 1]
    out = {}
    for ln in body.split(b"\n")[:-1]:
        o = json.loads(ln)
        if isinstance(o, dict) and o.get("t") == "piece" and is_int(o.get("slot"), o.get("index")):
            ob = o.get("offered_bytes")
            out[(o["slot"], o["index"])] = ob if is_int(ob) and ob >= 0 else None
    return out


def range_seal(H: Home, k: int, r: int):
    """(first_index, through_index, through_seal) of the range seal of (k, r) at home; None when it is not there."""
    name = f"r{r:04d}.w{k:03d}.seal.json"
    p = H.wire / "ranges" / (name + ".zz")
    if not p.exists():
        return None
    try:
        s = parse_canon(zlib.decompress(p.read_bytes()), name)
    except (zlib.error, ValueError) as e:
        raise Holds(f"the range seal {name} at home is not a canonical record: {e}") from None
    fi, ti = (s.get("first_index"), s.get("through_index")) if isinstance(s, dict) else (None, None)
    if not (isinstance(s, dict) and s.get("run_fingerprint") == H.fp and is_int(s.get("slot"), s.get("round"), fi, ti)
            and (s["slot"], s["round"]) == (k, r) and (fi == -1) == (ti == -1) and -1 <= fi <= ti
            and (s.get("through_seal") is None) == (fi == -1)):
        raise Holds(f"the range seal {name} at home is not one of this run, slot {k} and round {r} with a range of "
                    "pieces (first_index, through_index, through_seal)")
    return fi, ti, s.get("through_seal")


def offer_facts(H: Home, k: int, i: int) -> tuple:
    """(seal_sha256, offer_sha256, wire) of an offer at home without a receipt whose members are not all at home;
    (None, None, None) for an offer custody refuses. An offer that custody would receipt now: Wait."""
    try:
        H.take(k, i)
    except Bad:
        return None, None, None                         # its fields are not trusted: it names nothing (a GUESS)
    except Waits:
        d = H.wire / "out" / f"w{k:03d}"
        ob = unzz((d / f"p{i:06d}.offer.json.zz").read_bytes(), "offer")
        o = canon_of(ob, "offer")                       # take() accepted its keys, run, slot, index and form
        if type(o["seal_sha256"]) is not str or not HEX64.fullmatch(o["seal_sha256"]):
            return None, None, None                     # custody will refuse it (its seal member cannot match)
        wire = []
        for m in o["members"]:
            ok = sorted(m) == MEMBER_KEYS and m["wire_name"] == m["name"] + (".zz" if m["name"].endswith(".seal.json")
                                                                               else "") \
                and is_int(m["bytes"], m["wire_bytes"]) and all(type(m[x]) is str for x in ("sha256", "wire_sha256"))
            if not ok:
                return None, None, None                 # a member written against 1.6: as custody's Bad
            f = d / m["wire_name"]
            if not f.exists() or f.stat().st_size != m["wire_bytes"] or sha256_bytes(f.read_bytes()) != m["wire_sha256"]:
                wire.append({"wire_name": m["wire_name"], "wire_bytes": m["wire_bytes"], "wire_sha256": m["wire_sha256"]})
        return o["seal_sha256"], sha256_bytes(ob), wire
    raise Wait(f"w{k:03d}/p{i:06d}: its offer and every member are at home and intact, and it has no receipt yet "
               "(custody's next pass receipts it)")


def missing_list(H: Home) -> list:
    """The waits (Wait), then the missing list of 7 (Holds on a contradiction)."""
    slots = H.h["slots"]
    rs = {}
    for k in slots:
        d = H.cust / f"w{k:03d}"
        rs[k] = {int(m[1]) for p in (d.iterdir() if d.is_dir() else []) if (m := RECEIPT.fullmatch(p.name))}
        for i in sorted(rs[k]):
            if not (H.home / "content" / f"w{k:03d}" / f"p{i:06d}.verdict.json").exists():
                raise Wait(f"w{k:03d}/p{i:06d} has a receipt and no content verdict yet (content's next pass judges it)")
    named = {}                                          # (k, i) -> {"by": set, "seal": {src: sha}, "offer": {..}, ..}

    def name(k, i, src, seal=None, offer=None, **x):
        if k not in rs or i in rs[k]:
            return
        e = named.setdefault((k, i), {"by": set(), "seal": {}, "offer": {}, "wire": None, "offered_bytes": None})
        e["by"].add(src)
        if seal is not None:
            e["seal"][src] = seal
        if offer is not None:
            e["offer"][src] = offer
        e.update(x)

    for k in slots:                                     # offers at home first: one that custody would take now waits
        d = H.wire / "out" / f"w{k:03d}"
        for i in sorted(int(m[1]) for p in (d.iterdir() if d.is_dir() else []) if (m := OFFER.fullmatch(p.name))):
            if i not in rs[k]:
                seal, offer, wire = offer_facts(H, k, i)
                name(k, i, "offer", seal, offer, wire=wire)
    inv = H.inventory()                                 # None: no inventory at home, or it does not verify
    if inv:
        ib = inventory_bytes(H)
        for (k, i), (seal, offer) in sorted(inv.items()):
            name(k, i, "inventory", seal, offer, offered_bytes=ib.get((k, i)))
    rng = H.ranges()
    rows = rng[max(rng)]
    gone = []
    for (k, r), (first, last) in sorted(rows.items(), key=lambda x: (x[0][1], x[0][0])):
        got = range_seal(H, k, r)
        if got is None:
            gone.append({"kind": "range_seal", "round": r, "slot": k, "first": first, "last": last})
            continue
        fi, ti, through = got
        for i in range(fi, ti + 1) if fi >= 0 else ():   # a range without a piece (-1, -1) names none (credit.py 372)
            name(k, i, "range_seal", through if i == ti else None)
    for k in slots:
        for i in range(max(rs[k], default=-1)):
            if i not in rs[k]:
                nxt = H.kept_seal(H.record(k, i + 1)) if i + 1 in rs[k] else None
                prev = nxt.get("prev_seal") if isinstance(nxt, dict) else None
                name(k, i, "chain", prev if type(prev) is str else None)
    out = []
    for (k, i), e in sorted(named.items()):
        key = f"w{k:03d}/p{i:06d}"
        for what in ("seal", "offer"):
            vals = set(e[what].values())
            if len(vals) > 1 or any(type(v) is not str or not HEX64.fullmatch(v) for v in vals):
                raise Holds(f"{key}: the sources do not name one {what}_sha256: {sorted(e[what].items())}")
        out.append({"kind": "piece", "slot": k, "index": i, "named_by": sorted(e["by"]),
                    "seal_sha256": next(iter(e["seal"].values()), None),
                    "offer_sha256": next(iter(e["offer"].values()), None), "wire": e["wire"],
                    "offered_bytes": e["offered_bytes"]})
    return out + gone


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--home", required=True)
    ap.add_argument("--fingerprint", required=True)
    ap.add_argument("--why", required=True)
    try:
        a = ap.parse_args()
    except SystemExit:
        return 2
    home = Path(a.home)
    if not HEX64.fullmatch(a.fingerprint) or not home.is_dir() \
            or not (a.why in ("lease ended", "declared stop") or GONE.fullmatch(a.why)):
        print('drain: STOP (2): --home must be a folder, --fingerprint 64 lowercase hex, --why "lease ended", '
              '"declared stop" or "source gone since YYYY-MM-DDTHH:MM:SSZ"')
        return 2
    try:
        H = Home(home, a.fingerprint)                   # Stop(3) when wire/RUN.json.zz is not the pinned run
        if H.h is None:
            print("drain: REFUSED (4): no run header at home (wire/RUN.json.zz): nothing of the run arrived; a record "
                  "would name nothing")
            return 4
        try:
            got = read_drain(home, a.fingerprint)
        except ValueError as e:
            print(f"drain: STOP (4): {e}")
            return 4
        if got and got[1]["run_fingerprint"] != a.fingerprint:
            print("drain: STOP (3): DRAIN.json at home is another run's (a home folder serves one run); nothing written")
            return 3
        if got:
            print(f"drain: DRAIN.json of this run is at home (sha256 {got[0][:12]}): nothing written")
            return 0
        now = utc()
        refused = authority(H, a.why, now)
        if refused:
            print(f"drain: REFUSED (4): {refused}; nothing written")
            return 4
        H.check_records()                               # STOP 3 or 4 before anything is read or written
        try:
            missing = missing_list(H)
        except Wait as e:
            print(f"drain: waits: {e}")
            return 0
        rec = canon({"schema": 2, "run_fingerprint": a.fingerprint, "at_utc": now, "why": a.why, "missing": missing})
        create_only(home / "DRAIN.json", rec)
        n = sum(e["kind"] == "piece" for e in missing)
        print(f"drain: written (sha256 {sha256_bytes(rec)[:12]}); why {a.why}; missing {n} pieces, "
              f"{len(missing) - n} range seals")
        return 0
    except Holds as e:
        print(f"ALARM drain HOLDS: {e}")
        print("drain: holds; nothing written")
        return 5
    except Stop as e:
        print(f"drain: STOP ({e.code}): {e}")
        return e.code
    except (OSError, ValueError, zlib.error) as e:
        print(f"drain: STOP (4): {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())

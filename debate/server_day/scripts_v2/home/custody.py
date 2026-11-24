"""Opus 2026-11-23, A3d part 1 (FORMATS 2.1 and 2.4): stage a1 at HOME, CUSTODY. Standard library only.

    custody.py --home DIR --fingerprint HEX64 [--confirm w<NNN>/p<NNNNNN> ...]

THE HOME FOLDER. `wire/` holds what the fetch brought, under the server's own relative paths and names, whole files
only: RUN.json.zz, SCHEDULE.<n>.json.zz, FENCE.json.zz, TERMINAL.jsonl.zz, ranges/*.seal.json.zz, and per slot
out/w<NNN>/p<N>.offer.json.zz with the member files each offer names by `wire_name`. This program never writes in
wire/. It writes, create-only (FORMATS 0), custody/w<NNN>/p<NNNNNN>.receipt.json and custody/w<NNN>/p<NNNNNN>.fork.json.
--fingerprint is home's own pin of the run: wire/RUN.json.zz must decode to canonical bytes with that sha256.

ONE PASS:
 1 A RECEIPT (2.1) for every offer without one, only when every member is at home under its final name and was
   hashed again from the disk, wire bytes and decoded bytes both: the offer's wire file decodes to a canonical
   record with the keys of 1.6, schema 2, this run's fingerprint, the slot and index of its own name, a form of 1.6
   with its members' names, codecs and wire names; every member's length and sha256 are the offer's, wire and data;
   the seal member is the offer's seal_sha256 and a canonical seal of this run, slot and index. A member that is not
   there yet: WAITS (no receipt, no fault). Anything else: NOT RECEIVED with the reason (the fetch brings it again).
   An offer that HAS a receipt is not read again (2.4: seeing a name again confirms nothing).
 2 FORKS (2.1, 2.4): when wire/TERMINAL.jsonl.zz is there and verifies (its footer's fingerprint, its first line this
   run's header), every piece line whose seal, or non-null offer, is not the receipt's gives p<N>.fork.json.
 3 THE COUNTS: RECEIVED = every receipt. C1 per slot walks from index 0 while a piece has a receipt, its kept seal
   (read and hashed again) is the receipt's, no fork record names it, its prev_seal is the genesis text or the seal
   before, and its epoch is not below the epoch before (epochs are judged along the index, never by arrival).
   Pieces and rows (the seal's rows) of both. INTERVALS (2.1): two receipted pieces of a slot whose counter intervals
   overlap, or a piece whose interval is not inside the ONE range of its seal's round in the schedule its seal names
   (0 = the header's pilot_ranges), are CONFLICT lines; when home does not hold that schedule yet the piece WAITS
   (a conflict is immutable downstream: it is never judged on a schedule that has not arrived). The conflict records
   with both bindings (2.3) need the records: they are stage b's; this stage finds and counts.
--confirm KEY ... (2.4: an explicit confirmation): the kept offer and members of each receipt opened and hashed again,
wire and data; CONFIRMED, or CONFIRM FAILED with the member (exit 5: the fetch brings it again). Never a second
receipt.
Exit codes: 0 a pass or every confirmation; 2 a wrong call (or a key without a receipt); 3 the run header at home
cannot be trusted (nothing written); 4 a file that cannot be read or written; 5 a confirmation failed.
The last line of a pass: custody: RECEIVED .. pieces .. rows; C1 .. pieces .. rows; new receipts ..; not received
..; waits ..; conflicts ..; forks ..
"""
import argparse
import json
import re
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "run"))
from packer import FORMS, MEMBER_KEYS, OFFER_KEYS, SEAL_KEYS  # noqa: E402
from worker import Stop, canon, create_only, parse_canon, sha256_bytes  # noqa: E402

HEX64 = re.compile(r"[0-9a-f]{64}")
OFFER = re.compile(r"p([0-9]{6})\.offer\.json\.zz")
RECEIPT = re.compile(r"p([0-9]{6})\.receipt\.json")
FORK = re.compile(r"p([0-9]{6})\.fork\.json")
KEY = re.compile(r"w([0-9]{3})/p([0-9]{6})")


class Bad(Exception):
    """This offer gets no receipt."""


class Waits(Exception):
    """A file this offer needs is not at home yet."""


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def unzz(data: bytes, what: str) -> bytes:
    try:
        return zlib.decompress(data)
    except zlib.error as e:
        raise Bad(f"{what} does not decode ({e})") from None


def canon_of(data: bytes, what: str):
    try:
        return parse_canon(data, what)
    except ValueError as e:
        raise Bad(str(e)) from None


def is_int(*v) -> bool:
    return all(type(x) is int for x in v)


class Home:
    def __init__(self, home: Path, fp: str):
        self.home, self.fp, self.wire, self.cust = home, fp, home / "wire", home / "custody"
        self.h = self.hb = None
        hz = self.wire / "RUN.json.zz"
        if not hz.exists():
            return
        try:
            hb = zlib.decompress(hz.read_bytes())
            h = parse_canon(hb, "RUN.json")
        except (zlib.error, ValueError) as e:
            raise Stop(3, f"wire/RUN.json.zz cannot be trusted: {e}") from None
        if sha256_bytes(hb) != fp:
            raise Stop(3, f"wire/RUN.json.zz is not the run home pinned (its sha256 is {sha256_bytes(hb)})")
        if not isinstance(h, dict) or type(h.get("run")) is not str or not isinstance(h.get("slots"), list) \
                or not all(is_int(k) and 0 <= k <= 999 for k in h["slots"]) or not isinstance(h.get("pilot_ranges"), list):
            raise Stop(3, "RUN.json at home has no run, slots or pilot_ranges as 1.1 says")
        self.h, self.hb = h, hb

    def rpath(self, k: int, i: int, kind: str = "receipt") -> Path:
        return self.cust / f"w{k:03d}" / f"p{i:06d}.{kind}.json"

    # ---- 1: receipts --------------------------------------------------------------------------------------------
    def take(self, k: int, i: int) -> dict:
        d, name = self.wire / "out" / f"w{k:03d}", f"p{i:06d}"
        ow = (d / f"{name}.offer.json.zz").read_bytes()
        ob = unzz(ow, f"{name}.offer.json.zz")
        o = canon_of(ob, f"{name}.offer.json")
        if not isinstance(o, dict) or sorted(o) != OFFER_KEYS or not is_int(o["schema"], o["slot"], o["index"]) \
                or o["schema"] != 2:
            raise Bad("the offer has not the keys and schema of 1.6")
        if o["run_fingerprint"] != self.fp:
            raise Bad("not this run's offer (run_fingerprint)")
        if (o["slot"], o["index"]) != (k, i):
            raise Bad(f"the offer is of slot {o['slot']} index {o['index']}, not of its own name")
        ms = o["members"]
        if type(o["form"]) is not str or o["form"] not in FORMS or not isinstance(ms, list) or \
                [(m.get("name"), m.get("codec")) if isinstance(m, dict) else None for m in ms] != \
                [(name + x, c) for x, c in FORMS[o["form"]]]:
            raise Bad("its members are not those of a form of 1.6")
        seal = b""
        for m in ms:
            wire = m["name"].endswith(".seal.json")
            if sorted(m) != MEMBER_KEYS or m["wire_name"] != m["name"] + (".zz" if wire else "") \
                    or not is_int(m["bytes"], m["wire_bytes"]) or not all(type(m[x]) is str for x in ("sha256", "wire_sha256")):
                raise Bad(f"the member {m['name']} is not written as 1.6 says")
            f = d / m["wire_name"]
            if not f.exists():
                raise Waits(f"{m['wire_name']} is not at home yet")
            wb = f.read_bytes()
            if (len(wb), sha256_bytes(wb)) != (m["wire_bytes"], m["wire_sha256"]):
                raise Bad(f"{m['wire_name']}: the wire bytes are not the offer's (length or sha256)")
            data = unzz(wb, m["wire_name"]) if wire else wb
            if (len(data), sha256_bytes(data)) != (m["bytes"], m["sha256"]):
                raise Bad(f"{m['wire_name']}: the decoded bytes are not the offer's (length or sha256)")
            if wire:
                seal = data
        if sha256_bytes(seal) != o["seal_sha256"]:
            raise Bad("the seal member is not the offer's seal_sha256")
        s = canon_of(seal, f"{name}.seal.json")
        if not isinstance(s, dict) or sorted(s) != SEAL_KEYS or s["schema"] != 2 or s["run"] != self.h["run"] \
                or s["run_fingerprint"] != self.fp or (s["slot"], s["index"]) != (k, i) \
                or not is_int(s["epoch"], s["first_counter"], s["last_counter"], s["rows"], s["round"], s["schedule"]) \
                or not 1 <= s["first_counter"] <= s["last_counter"] or s["epoch"] < 1 or type(s["prev_seal"]) is not str:
            raise Bad("the seal is not a seal of 1.5 for this run, slot and index")
        return {"schema": 2, "run_fingerprint": self.fp, "slot": k, "index": i, "epoch": s["epoch"],
                "first_counter": s["first_counter"], "last_counter": s["last_counter"], "offer_sha256": sha256_bytes(ob),
                "offer_wire_bytes": len(ow), "offer_wire_sha256": sha256_bytes(ow), "seal_sha256": o["seal_sha256"],
                "members": ms, "kept": f"wire/out/w{k:03d}", "at_utc": utc()}

    def receipts(self) -> dict:
        t = {"new": 0, "bad": 0, "waits": 0}
        for k in self.h["slots"]:
            d = self.wire / "out" / f"w{k:03d}"
            for i in sorted(int(m[1]) for p in (d.iterdir() if d.is_dir() else []) if (m := OFFER.fullmatch(p.name))):
                key, rp = f"w{k:03d}/p{i:06d}", self.rpath(k, i)
                if rp.exists():
                    continue
                try:
                    r = self.take(k, i)
                except Waits as e:
                    print(f"WAITS {key}: {e}")
                    t["waits"] += 1
                    continue
                except Bad as e:
                    print(f"NOT RECEIVED {key}: {e}")
                    t["bad"] += 1
                    continue
                rp.parent.mkdir(parents=True, exist_ok=True)
                create_only(rp, canon(r))
                t["new"] += 1
        return t

    # ---- 2: forks from the terminal inventory --------------------------------------------------------------------
    def inventory(self):
        p = self.wire / "TERMINAL.jsonl.zz"
        if not p.exists():
            return None
        try:
            data = zlib.decompress(p.read_bytes())
            body = data[:data.rstrip(b"\n").rfind(b"\n") + 1]
            foot = json.loads(data[len(body):])
            ok = data.endswith(b"\n") and isinstance(foot, dict) and foot.get("t") == "footer" \
                and foot.get("fingerprint") == sha256_bytes(body) and body.startswith(self.hb)
            lines = [json.loads(ln) for ln in body.split(b"\n")[:-1]] if ok else []
        except (zlib.error, ValueError) as e:
            ok, lines = False, []
            print(f"TERMINAL.jsonl.zz at home does not verify: {e}")
        if not ok:
            print("TERMINAL.jsonl.zz at home does not verify (footer fingerprint or header): no fork is judged from it")
            return None
        return {(o["slot"], o["index"]): (o.get("seal"), o.get("offer")) for o in lines
                if isinstance(o, dict) and o.get("t") == "piece" and is_int(o.get("slot"), o.get("index"))}

    # ---- 3: the counts -------------------------------------------------------------------------------------------
    def ranges(self) -> dict:
        def rows(v):
            return {(x["slot"], x["round"]): (x["first"], x["last"]) for x in v if isinstance(x, dict)
                    and is_int(x.get("slot"), x.get("round"), x.get("first"), x.get("last"))}
        out, prev, n = {0: rows(self.h["pilot_ranges"])}, "first", 1
        while (p := self.wire / f"SCHEDULE.{n}.json.zz").exists():
            try:
                b = zlib.decompress(p.read_bytes())
                s = parse_canon(b, p.name)
            except (zlib.error, ValueError) as e:
                print(f"{p.name} at home does not verify: {e}")
                break
            if not isinstance(s, dict) or s.get("n") != n or s.get("run_fingerprint") != self.fp \
                    or s.get("prev") != prev or not isinstance(s.get("ranges"), list):
                print(f"{p.name} at home is not schedule {n} of this run linked to the one before")
                break
            out[n], prev, n = rows(s["ranges"]), sha256_bytes(b), n + 1
        return out

    def kept_seal(self, r: dict):
        try:
            sb = zlib.decompress((self.home / r["kept"] / f"p{r['index']:06d}.seal.json.zz").read_bytes())
        except (OSError, zlib.error):
            return None
        return json.loads(sb) if sha256_bytes(sb) == r["seal_sha256"] else None

    def judge(self) -> dict:
        t = dict(received=0, received_rows=0, c1=0, c1_rows=0, waits=0, conflicts=0, forks=0)
        rng, inv = self.ranges(), self.inventory()
        for k in self.h["slots"]:
            d, name = self.cust / f"w{k:03d}", f"w{k:03d}"
            files = list(d.iterdir()) if d.is_dir() else []
            rs = {int(m[1]): json.loads(p.read_bytes()) for p in files if (m := RECEIPT.fullmatch(p.name))}
            forks = {int(m[1]) for p in files if (m := FORK.fullmatch(p.name))}
            for (kk, i), (seal, offer) in sorted((inv or {}).items()):
                r = rs.get(i) if kk == k else None
                if r and i not in forks and (seal != r["seal_sha256"] or (offer is not None and offer != r["offer_sha256"])):
                    create_only(self.rpath(k, i, "fork"), canon({
                        "schema": 2, "run_fingerprint": self.fp, "slot": k, "index": i,
                        "receipt_seal_sha256": r["seal_sha256"], "receipt_offer_sha256": r["offer_sha256"],
                        "found_seal_sha256": seal, "found_offer_sha256": offer, "at_utc": utc(),
                        "how": "the terminal inventory names another seal or offer for a piece with a receipt"}))
                    print(f"FORK {name}/p{i:06d}: the terminal inventory names another seal or offer")
                    forks.add(i)
            t["forks"] += len(forks)
            seals = {i: self.kept_seal(r) for i, r in rs.items()}
            t["received"] += len(rs)
            t["received_rows"] += sum(s["rows"] for s in seals.values() if s)
            prev, ep, i, why = f"genesis:{self.fp}:{name}", 0, 0, ""
            while i in rs:
                s = seals[i]
                why = ("its kept seal is gone or not the receipt's" if s is None else "a fork" if i in forks else
                       "prev_seal does not link to the seal before" if s["prev_seal"] != prev else
                       f"epoch {s['epoch']} after epoch {ep}" if s["epoch"] < ep else "")
                if why:
                    break
                t["c1"] += 1
                t["c1_rows"] += s["rows"]
                prev, ep, i = rs[i]["seal_sha256"], s["epoch"], i + 1
            if rs and max(rs) >= i:
                print(f"C1 {name} stops before p{i:06d}: " + (why or "it has no receipt"))
            top = None
            for i in sorted(rs, key=lambda j: (rs[j]["first_counter"], j)):
                r = rs[i]
                if top is not None and r["first_counter"] <= rs[top]["last_counter"]:
                    print(f"CONFLICT {name}: p{top:06d} [{rs[top]['first_counter']}, {rs[top]['last_counter']}] and "
                          f"p{i:06d} [{r['first_counter']}, {r['last_counter']}] overlap")
                    t["conflicts"] += 1
                if top is None or r["last_counter"] > rs[top]["last_counter"]:
                    top = i
                s = seals[i]
                if s is None:
                    continue
                have = rng.get(s["schedule"])
                if have is None:
                    print(f"WAITS {name}/p{i:06d}: schedule {s['schedule']} is not at home yet (its ranges)")
                    t["waits"] += 1
                    continue
                a, b = have.get((k, s["round"]), (1, 0))
                if not a <= r["first_counter"] <= r["last_counter"] <= b:
                    print(f"CONFLICT {name}/p{i:06d}: [{r['first_counter']}, {r['last_counter']}] is not inside round "
                          f"{s['round']}'s range of schedule {s['schedule']}")
                    t["conflicts"] += 1
        return t

    def confirm(self, key: str) -> bool:
        m = KEY.fullmatch(key)
        rp = self.rpath(int(m[1]), int(m[2])) if m else None
        if rp is None or not rp.exists():
            raise Stop(2, f"{key} is not a key with a receipt")
        r = json.loads(rp.read_bytes())
        d = self.home / r["kept"]
        want = [(f"p{r['index']:06d}.offer.json.zz", None, r["offer_wire_bytes"], r["offer_wire_sha256"], None, None)]
        want += [(x["wire_name"], x["name"].endswith(".seal.json"), x["wire_bytes"], x["wire_sha256"], x["bytes"],
                  x["sha256"]) for x in r["members"]]
        for wn, wire, wl, ws, dl, ds in want:
            try:
                wb = (d / wn).read_bytes()
                data = zlib.decompress(wb) if wire else wb
            except (OSError, zlib.error) as e:
                print(f"CONFIRM FAILED {key}: {wn} is gone or does not decode ({e.__class__.__name__})")
                return False
            if (len(wb), sha256_bytes(wb)) != (wl, ws) or (dl is not None and (len(data), sha256_bytes(data)) != (dl, ds)):
                print(f"CONFIRM FAILED {key}: {wn} is not the bytes of its receipt")
                return False
        print(f"CONFIRMED {key}")
        return True


def main() -> int:
    ap = argparse.ArgumentParser(description="stage a1 at home: custody receipts, forks, RECEIVED and C1")
    ap.add_argument("--home", required=True)
    ap.add_argument("--fingerprint", required=True)
    ap.add_argument("--confirm", nargs="+")
    try:
        a = ap.parse_args()
    except SystemExit:
        return 2
    home = Path(a.home)
    if not home.is_dir() or not HEX64.fullmatch(a.fingerprint):
        print("custody: STOP (2): --home must be a folder and --fingerprint 64 hex digits")
        return 2
    try:
        H = Home(home, a.fingerprint)
        if H.h is None:
            print("custody: no wire/RUN.json.zz at home yet: nothing to do")
            return 0
        if a.confirm:
            return 0 if all([H.confirm(x) for x in a.confirm]) else 5
        p, c = H.receipts(), H.judge()
        print(f"custody: RECEIVED {c['received']} pieces {c['received_rows']} rows; C1 {c['c1']} pieces {c['c1_rows']} "
              f"rows; new receipts {p['new']}; not received {p['bad']}; waits {p['waits'] + c['waits']}; conflicts "
              f"{c['conflicts']}; forks {c['forks']}")
        return 0
    except Stop as e:
        print(f"custody: STOP ({e.code}): {e}")
        return e.code
    except (OSError, ValueError) as e:              # a receipt or fork record of ours that cannot be read: the disk
        print(f"custody: STOP (4): {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())

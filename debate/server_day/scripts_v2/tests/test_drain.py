"""test_drain.py: the home guard's DRAIN.json (home/drain.py) and credit version 3 (home/credit.py) against known
answers written BEFORE the code (tmp/opus_scratch/drain/KNOWN_ANSWERS_drain_by_opus.md on the PC).

    test_drain.py <a tree holding home/ run/ workloads/ known/> <engine exe> <net file> <converter exe> <a NEW folder>
                  [plantN]

The tree's home/, run/, workloads/ and known/ are copied into the new folder; a plant changes the copy only.
R3  the server from the day's REAL programs, as test_publish.py's R2: run "drn", slot 1, piece_games 2, the list rule
    with N12's six openings, pilot ranges round 1 = 1..4 and round 2 = 5..12; worker, fence, packer with the official
    converter, then terminal.py (the inventory). Each home is made by the real custody.py and content.py from a fetch
    that leaves something out: H_FULL, H_GAP (piece 3 not fetched), H_MEMBER (piece 3's binpack and meta.xz not
    fetched), H_RANGE (r0002's range seal not fetched), H_INV (H_GAP with the inventory). Every expected hash comes
    from the SERVER's own files, never from home.
D1 to D11 (drain.py), E1 to E6 (credit v3; E3 publish.py's own reader on drain.py's record) as the known answers.
PLANTS (each must make the test fail): plant1 to plant10 change drain.py, plant11 to plant17 credit.py.
Added 25 Nov (Fable's read FABLE-2511-READ-PKG9-DRAIN, D1; known answers first in
tmp/opus_scratch/fetch_fix/KNOWN_ANSWERS_fetch_fix_by_opus.md): D12, a range seal without a piece names no piece;
plant18 (drain.py) takes the repair back.
Added 25 Nov (v16; the clock known answers tmp/opus_scratch/clock/KNOWN_ANSWERS_clock_by_opus.md, D1 to D7 and
ADDENDUM 7): drain decides by the SERVER's time (home/clock.py's server_text). Every home gets ONE ok clock line
of its run in the test's world (the server's time = the PC's), so every check above keeps its meaning. CD1 to CD7
(the known answers' D1 to D7) make the PC 25,178 s AHEAD of the server: CD1 a lease that ends in 3 h by the
server's clock is refused; CD2 one that ended 60 s ago is accepted, at_utc the server's; CD3 source gone since
T, by the server's clock; CD4 no clock line: both reasons refused with the helper's text and D7's ending; CD5 a
declared stop without a line (the PC's at_utc) and with one (the server's); CD7 a line the helper refuses (a
restart): lease ended refused with D7's ending, a declared stop written. plant19 takes drain's now from the PC's
clock again (CD6: CD1 FAILs).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import types
import zlib
from pathlib import Path

if len(sys.argv) < 6:
    print("usage: test_drain.py <tree> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]")
    sys.exit(2)
TREE, EXE, NET, CONV, WORK = (Path(a).resolve() for a in sys.argv[1:6])
PLANT = sys.argv[6] if len(sys.argv) > 6 else None
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)

D, C = "home/drain.py", "home/credit.py"
PLANTS = {
    "plant1": (D, "        if now < end:\n", "        if False:\n"),
    "plant2": (D, "            if not (H.home / \"content\" / f\"w{k:03d}\" / f\"p{i:06d}.verdict.json\").exists():\n",
               "            if False:\n"),
    "plant3": (D, "    raise Wait(f\"w{k:03d}/p{i:06d}: its offer and every member are at home and intact, and it has no "
                  "receipt yet \"\n               \"(custody's next pass receipts it)\")\n",
               "    return None, None, None\n"),
    "plant4": (D, "            if len(vals) > 1 or any(type(v) is not str or not HEX64.fullmatch(v) for v in vals):\n",
               "            if False:\n"),
    "plant5": (D, "            gone.append({\"kind\": \"range_seal\", \"round\": r, \"slot\": k, \"first\": first, \"last\": last})\n",
               "            pass\n"),
    "plant6": (D, "        if got and got[1][\"run_fingerprint\"] != a.fingerprint:\n", "        if False:\n"),
    "plant7": (D, "                name(k, i, \"chain\", prev if type(prev) is str else None)\n", "                pass\n"),
    "plant8": (D, "            if not f.exists() or f.stat().st_size != m[\"wire_bytes\"] or sha256_bytes(f.read_bytes()) != "
                  "m[\"wire_sha256\"]:\n", "            if True:\n"),
    "plant9": (D, "            name(k, i, \"inventory\", seal, offer, offered_bytes=ib.get((k, i)))\n",
               "            name(k, i, \"inventory\", seal, offer)\n"),
    "plant10": (D, "        if got:\n", "        if False:\n"),
    "plant11": (C, "            self._drain = got is not None and got[1][\"run_fingerprint\"] == self.fp\n",
                "            self._drain = False\n"),
    "plant12": (C, "            self._drain = got is not None and got[1][\"run_fingerprint\"] == self.fp\n",
                "            self._drain = got is not None\n"),
    "plant13": (C, "                    if v is None:\n",
                "                    if v is None and self.drained():\n                        continue\n"
                "                    if v is None:\n"),
    "plant14": (C, "                raise Holds(f\"home/DRAIN.json: {e}\") from None\n", "                got = None\n"),
    "plant15": (C, "                out.append((k, None, {\"first\": first,", "                out.append((k, \"0\" * 64, {\"first\": first,"),
    "plant16": (C, "                if not left_out:                        # v3: only a piece the DRAIN left out skips the sums "
                   "(v2's guard)\n", "                if True:\n"),
    "plant17": (C, "                if s[\"through_index\"] in c1:\n", "                if True:\n"),
    "plant18": (D, "        for i in range(fi, ti + 1) if fi >= 0 else ():", "        for i in range(fi, ti + 1):"),
    "plant19": (D, "            now = server_text(home, a.fingerprint)      # v16 K1: the SERVER's time (late, never "
                  "early)\n", "            now = utc()\n"),
}
CP = WORK / "tree"
for sub in ("home", "run", "workloads", "known"):
    shutil.copytree(TREE / sub, CP / sub, ignore=shutil.ignore_patterns("__pycache__"))
if PLANT:
    f, old, new = PLANTS[PLANT]
    text = (CP / f).read_text(encoding="ascii")
    assert text.count(old) == 1, f"{PLANT}: the old text is not there exactly once"
    (CP / f).write_text(text.replace(old, new), encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy's {f}")
RUN, HOMEP = CP / "run", CP / "home"
DRAIN, CUST, CONT, CRED = (HOMEP / x for x in ("drain.py", "custody.py", "content.py", "credit.py"))
sys.path.insert(0, str(RUN))
import worker as W  # noqa: E402

RESULTS = []


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(("PASS " if ok else "FAIL ") + f"{name}: got {str(got)[:400]}" + ("" if ok else f"; want {str(want)[:400]}"))
    return ok


def safe(fn):
    try:
        fn()
    except (Exception, SystemExit):  # noqa: BLE001   a crash of a part is one FAIL, the other parts go on
        RESULTS.append((f"{fn.__name__} crashed", False))
        print(f"FAIL {fn.__name__} crashed:\n{traceback.format_exc()}")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fsha(p: Path) -> str:
    return sha(p.read_bytes())


def T(t: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def put(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_bytes(data)
    os.replace(part, path)


MAN_PATH, KNOWN = CP / "workloads" / "MANIFEST.json", CP / "known" / "startup.json"
MAN = json.loads(MAN_PATH.read_bytes())
N12 = [ln.split()[3:] for ln in (CP / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
OPENINGS = WORK / "n12_openings.txt"
OPENINGS.write_bytes("".join(" ".join(o) + "\n" for o in N12).encode("ascii"))
NOW = time.time()
SRV = WORK / "srv"
FP = {}
KEYS5 = sorted(("schema", "run_fingerprint", "at_utc", "why", "missing"))
CUST_COUNTS = re.compile(r"custody: RECEIVED (\d+) pieces (\d+) rows; C1 (\d+) pieces .*; forks (\d+)")
CONT_COUNTS = re.compile(r"content: judged (\d+) pieces \((\d+) refused\); accepted (\d+) games (\d+) rows; ")
CRED_LAST = re.compile(r"credit: decided (\d+) rounds \((\d+) complete, (\d+) partial\) this pass; credited (\d+) games "
                       r"(\d+) rows; waits: (.*); holds (\d)")
TERM = "TERMINAL.jsonl.zz"
P3 = {"p000003.offer.json.zz", "p000003.seal.json.zz", "p000003.binpack", "p000003.meta.xz"}
HOMES = {"H_FULL": ({TERM}, ("6", "6", "0", "6")), "H_GAP": ({TERM} | P3, ("5", "3", "0", "5")),
         "H_MEMBER": ({TERM, "p000003.binpack", "p000003.meta.xz"}, ("5", "3", "0", "5")),
         "H_RANGE": ({TERM, "r0002.w001.seal.json.zz"}, ("6", "6", "0", "6")), "H_INV": (P3, ("5", "3", "0", "5"))}


def gid(c: int) -> str:
    return f"drn-w001-g{c:08d}"


# ---- the fixture R3 --------------------------------------------------------------------------------------------------
def server() -> bool:
    put(SRV / "RUN.json", W.canon({
        "schema": 2, "run": "drn", "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
        "hard_cutoff_utc": T(NOW + 86400), "boot_id": W.boot_id(), "instance": "test-instance", "package": "0" * 64,
        "engine_sha256": sha(EXE.read_bytes()), "net_sha256": MAN["net_sha256"],
        "options_sha256": sha("".join(ln + "\n" for ln in MAN["options"]).encode("ascii")),
        "game_line": MAN["selfgame_line"], "opening_rule": {"kind": "list", "sha256": sha(OPENINGS.read_bytes()),
                                                             "count": len(N12)},
        "slots": [1], "piece_games": 2,
        "pilot_ranges": [{"slot": 1, "round": 1, "first": 1, "last": 4, "short": False, "schedule": 0},
                         {"slot": 1, "round": 2, "first": 5, "last": 12, "short": False, "schedule": 0}]}))
    FP["fp"] = fp = sha((SRV / "RUN.json").read_bytes())
    FP["hdr"] = hdr = json.loads((SRV / "RUN.json").read_bytes())
    cmd = [sys.executable, "-I", "-B", str(RUN / "worker.py"), "--root", str(SRV), "--slot", "1", "--exe", str(EXE),
           "--net", str(NET), "--manifest", str(MAN_PATH), "--known-startup", str(KNOWN), "--openings", str(OPENINGS)]
    log = WORK / "srv.out"
    with open(log, "wb") as f:
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        end = time.time() + 900
        while not (SRV / "ranges" / "r0002.w001.seal.json").exists() and p.poll() is None and time.time() < end:
            time.sleep(0.5)
        put(SRV / "FENCE.json", W.canon({"at_utc": T(time.time()), "cutoff_utc": hdr["hard_cutoff_utc"],
                                         "run_fingerprint": fp, "schema": 2, "why": "D"}))
        try:
            p.wait(timeout=120)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
    closed = SRV / "w001" / "closed"
    seals = [json.loads((closed / f"p{i:06d}.seal.json").read_bytes()) for i in range(6)
             if (closed / f"p{i:06d}.seal.json").exists()]
    if not check("R3 server: exit 0, six pieces of rounds 1 1 2 2 2 2, both range seals",
                 (p.returncode, [s["round"] for s in seals], sorted(x.name for x in (SRV / "ranges").glob("*.json"))),
                 (0, [1, 1, 2, 2, 2, 2], ["r0001.w001.seal.json", "r0002.w001.seal.json"])):
        print(log.read_text(encoding="utf-8", errors="replace")[-600:])
        return False
    rc = subprocess.run([sys.executable, "-I", "-B", str(RUN / "packer.py"), "--root", str(SRV), "--converter",
                         str(CONV), "--once"], capture_output=True, text=True, timeout=600).returncode
    q = subprocess.run([sys.executable, "-I", "-B", str(RUN / "terminal.py"), "--root", str(SRV)],
                       capture_output=True, text=True, timeout=300)
    forms = [json.loads((SRV / "out" / "w001" / f"p{i:06d}.offer.json").read_bytes())["form"] for i in range(6)]
    return check("R3 packer and terminal: exit 0, six binpack offers, TERMINAL.jsonl.zz",
                 (rc, forms, q.returncode, (SRV / TERM).exists()), (0, ["binpack"] * 6, 0, True))


def fetch(home: Path, leave: set) -> None:
    """Everything the server holds, under its wire names, but the names in `leave`."""
    for p in sorted(SRV.glob("*.zz")):
        if p.name not in leave:
            put(home / "wire" / p.name, p.read_bytes())
    for p in sorted((SRV / "ranges").glob("*.zz")):
        if p.name not in leave:
            put(home / "wire" / "ranges" / p.name, p.read_bytes())
    src, dst = SRV / "out" / "w001", home / "wire" / "out" / "w001"
    for i in range(6):
        oz = f"p{i:06d}.offer.json.zz"
        for m in json.loads(zlib.decompress((src / oz).read_bytes()))["members"]:
            if m["wire_name"] not in leave:
                put(dst / m["wire_name"], (src / m["wire_name"]).read_bytes())
        if oz not in leave:
            put(dst / oz, (src / oz).read_bytes())


def homes() -> bool:
    ok = True
    for name, (leave, want) in HOMES.items():
        h = WORK / name
        fetch(h, leave)
        p = subprocess.run([sys.executable, "-I", "-B", str(CUST), "--home", str(h), "--fingerprint", FP["fp"]],
                           capture_output=True, text=True, timeout=300)
        q = subprocess.run([sys.executable, "-I", "-B", str(CONT), "--home", str(h), "--fingerprint", FP["fp"],
                            "--converter", str(CONV), "--openings", str(OPENINGS)], capture_output=True, text=True,
                           timeout=900)
        m, n = CUST_COUNTS.search(p.stdout), CONT_COUNTS.search(q.stdout)
        ok = check(f"{name}: custody exit 0, RECEIVED {want[0]}, C1 {want[1]}, forks {want[2]}; content exit 0, judged "
                   f"{want[3]} (0 refused)", (p.returncode, m and (m[1], m[3], m[4]), q.returncode, n and (n[1], n[2])),
                   (0, want[:3], 0, (want[3], "0"))) and ok
    return ok


def clock_line(h: Path, fp: str, behind_s: float = 0.0, mono_ahead_s: float = 0.0) -> None:
    """v16 (ADDENDUM 7): ONE ok clock line of run fp in h/clock/journal.jsonl, as home/clock.py's measure writes
    it: the server's time = the PC's now - behind_s; its mono = the PC's monotonic clock now + mono_ahead_s.
    v17 (CL1): with mono0, the steady clock read right BEFORE (+ mono_ahead_s), as measure writes it."""
    mono0 = time.monotonic()
    wall, mono = time.time(), time.monotonic()
    line = W.canon({"impl": time.get_clock_info("monotonic").implementation, "look": 2, "mono0": mono0 + mono_ahead_s,
                    "mono": mono + mono_ahead_s, "n": 1, "ok": True, "platform": sys.platform, "run": fp,
                    "state": "play", "t": "clock", "utc_ms": int((wall - behind_s) * 1000), "wall": wall,
                    "why": None})
    (h / "clock").mkdir(parents=True, exist_ok=True)
    (h / "clock" / "journal.jsonl").write_bytes(line)


def copy(name: str, src: str) -> Path:
    shutil.copytree(WORK / src, WORK / name)
    clock_line(WORK / name, FP["fp"])               # v16: the server's time = the PC's (ADDENDUM 7)
    return WORK / name


def drain(h: Path, why: str, fp: str = None) -> tuple:
    p = subprocess.run([sys.executable, "-I", "-B", str(DRAIN), "--home", str(h), "--fingerprint", fp or FP["fp"],
                        "--why", why], capture_output=True, text=True, timeout=300)
    out = (p.stdout + p.stderr).strip()
    return p.returncode, (out.splitlines()[-1] if out else ""), out


def record(h: Path):
    p = h / "DRAIN.json"
    return W.parse_canon(p.read_bytes(), "DRAIN.json") if p.exists() else {}


def publish_drain(h: Path):
    """publish.py's OWN reader of DRAIN.json (Publisher.drain reads only self.home and self.fp)."""
    sys.path.insert(0, str(HOMEP))
    import publish  # noqa: E402
    return publish.Publisher.drain(types.SimpleNamespace(home=h, fp=FP["fp"]))


def srv_offer(i: int) -> dict:
    return json.loads((SRV / "out" / "w001" / f"p{i:06d}.offer.json").read_bytes())


def piece3(by: list, offer=False, wire=None, offered=None) -> dict:
    return {"kind": "piece", "slot": 1, "index": 3, "named_by": by,
            "seal_sha256": fsha(SRV / "w001" / "closed" / "p000003.seal.json"),
            "offer_sha256": fsha(SRV / "out" / "w001" / "p000003.offer.json") if offer else None, "wire": wire,
            "offered_bytes": offered}


# ---- the cases: drain.py ---------------------------------------------------------------------------------------------
def case_d1_d8():
    h = copy("d1", "H_FULL")
    t0 = T(time.time() - 1)
    rc, last, out = drain(h, "declared stop")
    t1 = T(time.time() + 1)
    d = record(h)
    check("D1 H_FULL, declared stop: exit 0, written, missing 0 pieces, 0 range seals",
          (rc, last.startswith("drain: written (sha256 "), last.endswith("missing 0 pieces, 0 range seals")),
          (0, True, True))
    check("D1 the record: the five keys, schema 2, this run, why, at_utc within the call, missing []",
          (sorted(d), d.get("schema"), d.get("run_fingerprint"), d.get("why"), t0 <= str(d.get("at_utc")) <= t1,
           d.get("missing")), (KEYS5, 2, FP["fp"], "declared stop", True, []))
    check("D1 publish.py's own drain() reads it: its sha256", publish_drain(h),
          fsha(h / "DRAIN.json") if (h / "DRAIN.json").exists() else "a DRAIN.json written by D1")
    b = (h / "DRAIN.json").read_bytes() if (h / "DRAIN.json").exists() else None
    rc, last, out = drain(h, "lease ended")
    check("D8 D1's home again, lease ended: exit 0, 'of this run is at home', the bytes unchanged",
          (rc, "DRAIN.json of this run is at home" in last, b is not None and (h / "DRAIN.json").read_bytes() == b),
          (0, True, True))
    h = copy("d8b", "H_FULL")
    other = W.canon({"schema": 2, "run_fingerprint": sha(b"another run"), "at_utc": T(time.time()),
                     "why": "declared stop", "missing": []})
    put(h / "DRAIN.json", other)
    rc, last, out = drain(h, "declared stop")
    check("D8b another run's DRAIN.json at home: exit 3, its bytes unchanged",
          (rc, (h / "DRAIN.json").read_bytes() == other), (3, True))


def case_d2_d4_d11():
    o3 = srv_offer(3)
    srvw = SRV / "out" / "w001"
    wire = [{"wire_name": x, "wire_bytes": len((srvw / x).read_bytes()), "wire_sha256": fsha(srvw / x)}
            for x in ("p000003.binpack", "p000003.meta.xz")]
    offered = sum(len((srvw / m["wire_name"]).read_bytes()) for m in o3["members"])
    for case, src, want in (
            ("D2", "H_GAP", [piece3(["chain", "range_seal"])]),
            ("D3", "H_MEMBER", [piece3(["chain", "offer", "range_seal"], offer=True, wire=wire)]),
            ("D4", "H_RANGE", [{"kind": "range_seal", "round": 2, "slot": 1, "first": 5, "last": 12}]),
            ("D11", "H_INV", [piece3(["chain", "inventory", "range_seal"], offer=True, offered=offered)])):
        h = copy(case.lower(), src)
        rc, last, out = drain(h, "declared stop")
        check(f"{case} {src}, declared stop: exit 0, the missing list", (rc, record(h).get("missing")), (0, want))


def case_d5_d6():
    h = copy("d5", "H_FULL")
    (h / "content" / "w001" / "p000005.verdict.json").unlink()
    rc, last, out = drain(h, "declared stop")
    check("D5 H_FULL without p000005's verdict: exit 0, waits naming w001/p000005 and its content verdict, no DRAIN.json",
          (rc, last.startswith("drain: waits:"), "w001/p000005" in last, "content verdict" in last,
           (h / "DRAIN.json").exists()), (0, True, True, True, False))
    h = copy("d6", "H_FULL")
    (h / "custody" / "w001" / "p000005.receipt.json").unlink()
    (h / "content" / "w001" / "p000005.verdict.json").unlink()
    rc, last, out = drain(h, "declared stop")
    check("D6 H_FULL without p000005's receipt and verdict: exit 0, waits naming w001/p000005 and receipt, no DRAIN.json",
          (rc, last.startswith("drain: waits:"), "w001/p000005" in last, "receipt" in last,
           (h / "DRAIN.json").exists()), (0, True, True, True, False))


def case_d7():
    now = time.time()
    hb = W.canon(dict(FP["hdr"], run="drn7", lease_start_utc=T(now - 3600), lease_end_utc=T(now - 60),
                      hard_cutoff_utc=T(now - 60),
                      pilot_ranges=[{"slot": 1, "round": 1, "first": 1, "last": 4, "short": False, "schedule": 0}]))
    h = WORK / "d7"
    put(h / "wire" / "RUN.json.zz", zlib.compress(hb, 6))
    clock_line(h, sha(hb))                            # v16: the server's time = the PC's (ADDENDUM 7)
    rc, last, out = drain(h, "lease ended", sha(hb))
    d = record(h)
    check("D7 only a header whose lease ended 60 s ago, lease ended: exit 0, why, missing round 1's range seal",
          (rc, d.get("run_fingerprint"), d.get("why"), d.get("missing")),
          (0, sha(hb), "lease ended", [{"kind": "range_seal", "round": 1, "slot": 1, "first": 1, "last": 4}]))
    h = copy("d7b", "H_FULL")
    rc, last, out = drain(h, "lease ended")
    check("D7b H_FULL, lease ended (it ends in a day): exit 4 naming the lease's end, no DRAIN.json",
          (rc, FP["hdr"]["lease_end_utc"] in out, (h / "DRAIN.json").exists()), (4, True, False))
    h = copy("d7c1", "H_FULL")
    rc, last, out = drain(h, "source gone since " + T(time.time() + 3600))
    check("D7c source gone since an hour AHEAD: exit 4, no DRAIN.json", (rc, (h / "DRAIN.json").exists()), (4, False))
    h = copy("d7c2", "H_FULL")
    why = "source gone since " + T(time.time() - 3600)
    rc, last, out = drain(h, why)
    check("D7c source gone since an hour ago: exit 0, why exactly that text, publish.py's drain() reads it",
          (rc, record(h).get("why"), publish_drain(h)),
          (0, why, fsha(h / "DRAIN.json") if (h / "DRAIN.json").exists() else "a DRAIN.json written by D7c"))
    h = copy("d7d", "H_FULL")
    got = [drain(h, w)[0] for w in ("stopped", "source gone since yesterday")]
    check("D7d --why stopped and source gone since yesterday: exit 2 each, no DRAIN.json",
          (got, (h / "DRAIN.json").exists()), ([2, 2], False))


AHEAD = 25178                                         # v16: the PC's clock ahead of the server's (measured 25 Nov)


def case_cd():
    """The clock known answers' D1 to D7 as CD1 to CD7 (ADDENDUM 7): the PC 25,178 s AHEAD of the server."""
    def fresh(name: str, end_from_server_s: int):
        srv = int(time.time()) - AHEAD
        end = T(srv + end_from_server_s)
        hb = W.canon(dict(FP["hdr"], run="drn" + name, lease_start_utc=T(srv - 3600), lease_end_utc=end,
                          hard_cutoff_utc=end,
                          pilot_ranges=[{"slot": 1, "round": 1, "first": 1, "last": 4, "short": False,
                                         "schedule": 0}]))
        h = WORK / name
        put(h / "wire" / "RUN.json.zz", zlib.compress(hb, 6))
        clock_line(h, sha(hb), behind_s=AHEAD)
        return h, sha(hb), end

    def srv_text(d: float) -> str:
        return T(time.time() - AHEAD + d)

    d7 = 'drain with --why "declared stop"'
    h, fp, end = fresh("cd1", 3 * 3600)
    rc, last, out = drain(h, "lease ended", fp)
    check("CD1 a lease that ends in 3 h by the server's clock (4 h before the PC's now): exit 4, 'the lease ends at "
          "<end>; the server's clock reads', no DRAIN.json",
          (rc, f"the lease ends at {end}; the server's clock reads " in out, (h / "DRAIN.json").exists()),
          (4, True, False))
    h, fp, end = fresh("cd2", -60)
    lo = srv_text(-2)
    rc, last, out = drain(h, "lease ended", fp)
    hi = srv_text(2)
    d = record(h)
    check("CD2 a lease that ended 60 s ago by the server's clock: exit 0, why, at_utc the server's time (within 2 s)",
          (rc, d.get("why"), lo <= str(d.get("at_utc")) <= hi), (0, "lease ended", True))
    h = copy("cd3a", "H_FULL")
    clock_line(h, FP["fp"], behind_s=AHEAD)
    rc, last, out = drain(h, "source gone since " + srv_text(3600))
    got = [rc, (h / "DRAIN.json").exists()]
    h = copy("cd3b", "H_FULL")
    clock_line(h, FP["fp"], behind_s=AHEAD)
    why = "source gone since " + srv_text(-3600)
    rc, last, out = drain(h, why)
    check("CD3 source gone since the server's now + 1 h (before the PC's now): exit 4, no DRAIN.json; since its now "
          "- 1 h: exit 0, why exactly that text", (got, rc, record(h).get("why")), ([4, False], 0, why))
    h = copy("cd4", "H_FULL")
    (h / "clock" / "journal.jsonl").unlink()
    got = []
    for w in ("lease ended", "source gone since " + srv_text(-3600)):
        rc, last, out = drain(h, w)
        got.append((rc, "no clock line of this run" in last, last.endswith(d7 + "; nothing written")))
    check("CD4 no clock line: lease ended and source gone since: exit 4 each, the helper's text and D7's ending "
          "named, no DRAIN.json", (got, (h / "DRAIN.json").exists()), ([(4, True, True), (4, True, True)], False))
    h = copy("cd5a", "H_FULL")
    (h / "clock" / "journal.jsonl").unlink()
    lo = T(time.time() - 1)
    rc1, last, out = drain(h, "declared stop")
    hi = T(time.time() + 1)
    pc = lo <= str(record(h).get("at_utc")) <= hi
    h = copy("cd5b", "H_FULL")
    clock_line(h, FP["fp"], behind_s=AHEAD)
    lo = srv_text(-2)
    rc2, last, out = drain(h, "declared stop")
    hi = srv_text(2)
    check("CD5 a declared stop without a clock line: exit 0, at_utc the PC's (within the call); with a line 25,178 s "
          "behind: exit 0, at_utc the server's (within 2 s)",
          (rc1, pc, rc2, lo <= str(record(h).get("at_utc")) <= hi), (0, True, 0, True))
    h = copy("cd7", "H_FULL")
    clock_line(h, FP["fp"], mono_ahead_s=3600)
    rc, last, out = drain(h, "lease ended")
    got = (rc, "the PC restarted since the last clock line" in last, last.endswith(d7 + "; nothing written"),
           (h / "DRAIN.json").exists())
    lo = T(time.time() - 1)
    rc, last, out = drain(h, "declared stop")
    hi = T(time.time() + 1)
    check("CD7 a line the helper refuses (its mono 1 h ahead: a restart): lease ended exit 4 with the restart text and "
          "D7's ending, no DRAIN.json; then declared stop: exit 0, at_utc the PC's",
          (got, rc, lo <= str(record(h).get("at_utc")) <= hi), ((4, True, True, False), 0, True))


def case_d9_d10():
    h = copy("d9", "H_GAP")
    o = srv_offer(3)
    o["seal_sha256"] = sha(b"another seal")
    put(h / "wire" / "out" / "w001" / "p000003.offer.json.zz", zlib.compress(W.canon(o), 6))
    rc, last, out = drain(h, "declared stop")
    check("D9 H_GAP + an offer of p000003 naming another seal, no member: exit 5, the alarm names p000003 and "
          "seal_sha256, no DRAIN.json",
          (rc, "ALARM drain HOLDS" in out and "p000003" in out and "seal_sha256" in out, (h / "DRAIN.json").exists()),
          (5, True, False))
    h = copy("d10", "H_FULL")
    rc, last, out = drain(h, "declared stop", sha(b"another run"))
    check("D10 the header at home is another run's: exit 3, no DRAIN.json", (rc, (h / "DRAIN.json").exists()), (3, False))
    h = WORK / "d10b"
    h.mkdir()
    rc, last, out = drain(h, "declared stop")
    check("D10b an empty home folder: exit 4, nothing written", (rc, sorted(h.iterdir())), (4, []))


def case_d12():
    """D12 (Fable's D1): a range seal WITHOUT a piece, as worker.py's range_seal() writes it for a slot that closed no
    piece in a round, names NO piece; the control, the server's REAL seal r0002.w001, names its pieces. The real
    drain.missing_list of the copy, with a stand-in for custody's Home that holds nothing in custody."""
    sys.path.insert(0, str(HOMEP))
    import drain as DR  # noqa: E402
    real = json.loads((SRV / "ranges" / "r0002.w001.seal.json").read_bytes())
    empty = dict(real, complete=False, first_index=-1, first_prev_seal=None, through_index=-1, through_seal=None,
                 games=0, rows=0, raw_bytes=0)

    class Stand:
        def __init__(self, name: str, seal: dict):
            self.fp, self.h, self.k, self.r = seal["run_fingerprint"], {"slots": [seal["slot"]]}, seal["slot"], seal["round"]
            self.home = WORK / name
            self.cust, self.wire = self.home / "custody", self.home / "wire"
            put(self.wire / "ranges" / f"r{self.r:04d}.w{self.k:03d}.seal.json.zz", zlib.compress(W.canon(seal), 6))

        def inventory(self):
            return None

        def ranges(self):
            return {0: {(self.k, self.r): (0, 0)}}

    fi, ti = real["first_index"], real["through_index"]
    got = DR.missing_list(Stand("d12_control", real))
    check(f"D12 control: the real range seal r0002.w001, nothing in custody: exactly its pieces {fi}..{ti} by the range "
          "seal, the last with its through_seal", [(e["index"], e["named_by"], e["seal_sha256"]) for e in got],
          [(i, ["range_seal"], real["through_seal"] if i == ti else None) for i in range(fi, ti + 1)])
    got = DR.missing_list(Stand("d12", empty))
    check("D12 a range seal without a piece (first_index -1, as the worker writes it) names no piece, not p-00001",
          got, [])


# ---- the cases: credit v3 --------------------------------------------------------------------------------------------
def credit(h: Path) -> tuple:
    p = subprocess.run([sys.executable, "-I", "-B", str(CRED), "--home", str(h), "--fingerprint", FP["fp"]],
                       capture_output=True, text=True, timeout=600)
    out = (p.stdout + p.stderr).strip()
    m = CRED_LAST.fullmatch(out.splitlines()[-1]) if out else None
    return p.returncode, (m.groups() if m else ("no last line",) * 7), out


def cj(h: Path, r: int):
    p = h / "stage" / f"r{r:04d}" / "credit.json"
    return p.read_bytes() if p.exists() else None


def with_drain(name: str, src: str, drain_from: str = None, data: bytes = None) -> Path:
    h = copy(name, src)
    if data is None and drain_from and (WORK / drain_from / "DRAIN.json").exists():
        data = (WORK / drain_from / "DRAIN.json").read_bytes()
    if data is not None:
        put(h / "DRAIN.json", data)
    return h


def case_e():
    ef = copy("ef", "H_FULL")
    rc, m, out = credit(ef)
    check("EF credit on H_FULL, no DRAIN.json: exit 0, decided 2 rounds (2 complete), waits none, holds 0",
          (rc, m[0], m[1], m[2], m[5], m[6]), (0, "2", "2", "0", "none", "0"))
    efc = json.loads(cj(ef, 2) or b"{}")
    rs2 = json.loads((SRV / "ranges" / "r0002.w001.seal.json").read_bytes())
    h = with_drain("e1", "H_GAP", "d2")
    rc, m, out = credit(h)
    check("E1 H_GAP + D2's DRAIN.json: exit 0, decided 2 rounds (1 complete, 1 partial), waits none, holds 0",
          (rc, m[0], m[1], m[2], m[5], m[6]), (0, "2", "1", "1", "none", "0"))
    check("E1 round 1: the credit.json bytes of EF's round 1", cj(h, 1) is not None and cj(h, 1) == cj(ef, 1), True)
    c = json.loads(cj(h, 2) or b"{}")
    check("E1 round 2: partial, missing g7 to g12, ids 5 and 6 as EF's, range_seals r0002's, games_in and raw_rows_in "
          "the range seal's",
          (c.get("status"), c.get("missing_ids"), [e for e in c.get("ids", []) if e["counter"] in (5, 6)],
           c.get("range_seals"), c.get("games_in"), c.get("raw_rows_in")),
          ("partial", [gid(x) for x in range(7, 13)], [e for e in efc.get("ids", []) if e["counter"] in (5, 6)],
           [{"slot": 1, "sha256": fsha(SRV / "ranges" / "r0002.w001.seal.json")}], rs2["games"], rs2["rows"]))
    for case, data in (("E1b", None), ("E1c", W.canon({"schema": 2, "run_fingerprint": sha(b"another run"),
                                                       "at_utc": T(time.time()), "why": "declared stop",
                                                       "missing": []}))):
        h = with_drain(case.lower(), "H_GAP", None, data)
        rc, m, out = credit(h)
        check(f"{case} H_GAP, {'no DRAIN.json' if data is None else 'another run' + chr(39) + 's DRAIN.json'}: exit 0, "
              "round 1 complete, round 2 waits for p000003 (C1)",
              (rc, m[0], m[1], m[2], m[6], m[5]),
              (0, "1", "1", "0", "0", "round 2: w001/p000003 of round 2 is not in custody's chain (C1) yet"))
    h = with_drain("e2", "H_RANGE", "d4")
    rc, m, out = credit(h)
    c = json.loads(cj(h, 2) or b"{}")
    check("E2 H_RANGE + D4's DRAIN.json: exit 0, 2 rounds (1 complete, 1 partial); round 2: ids 5 to 12 missing, "
          "range_seals sha256 null, games_in 0, raw_rows_in 0",
          (rc, m[0], m[1], m[2], m[6], c.get("status"), sorted({e["state"] for e in c.get("ids", [])}),
           c.get("missing_ids"), c.get("range_seals"), c.get("games_in"), c.get("raw_rows_in")),
          (0, "2", "1", "1", "0", "partial", ["missing"], [gid(x) for x in range(5, 13)], [{"slot": 1, "sha256": None}],
           0, 0))
    d2 = WORK / "d2" / "DRAIN.json"
    check("E3 publish.py's own drain() reads D2's DRAIN.json: its sha256", publish_drain(WORK / "d2"),
          fsha(d2) if d2.exists() else "a DRAIN.json written by D2")
    h = with_drain("e4", "H_FULL", "d1")
    rc, m, out = credit(h)
    check("E4 H_FULL + D1's DRAIN.json: exit 0, 2 rounds complete, both credit.json bytes EF's",
          (rc, m[0], m[1], m[2], cj(h, 1) == cj(ef, 1) and cj(h, 2) == cj(ef, 2) and cj(h, 2) is not None),
          (0, "2", "2", "0", True))
    h = with_drain("e5", "H_GAP", "d2")
    (h / "content" / "w001" / "p000002.verdict.json").unlink()
    rc, m, out = credit(h)
    check("E5 H_GAP + D2's DRAIN.json without p000002's verdict: exit 0, round 1 complete, round 2 waits for it",
          (rc, m[0], m[1], m[2], m[6], m[5]),
          (0, "1", "1", "0", "0", "round 2: w001/p000002 of round 2 has no content verdict yet"))
    damaged = d2.read_bytes().replace(b'{"', b'{ "', 1) if d2.exists() else None
    h = with_drain("e6", "H_GAP", None, damaged)
    rc, m, out = credit(h)
    check("E6 H_GAP + D2's DRAIN.json with a space: exit 5, round 1 complete, round 2 HOLDS naming DRAIN.json",
          (rc, m[0], m[1], m[6], "ALARM credit HOLDS round 2: home/DRAIN.json" in out), (5, "1", "1", "1", True))


def main() -> int:
    t0 = time.time()
    if not (server() and homes()):
        print("the fixture failed: no case can run")
    else:
        for fn in (case_d1_d8, case_d2_d4_d11, case_d5_d6, case_d7, case_cd, case_d9_d10, case_d12, case_e):
            safe(fn)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"{len(RESULTS) - len(bad)} of {len(RESULTS)} checks pass ({time.time() - t0:.0f} s)"
          + (f"; PLANT {PLANT}" if PLANT else ""))
    return 0 if RESULTS and not bad else 1


if __name__ == "__main__":
    sys.exit(main())

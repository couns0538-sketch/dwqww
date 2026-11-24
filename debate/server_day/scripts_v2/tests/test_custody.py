"""test_custody.py: stage a1 at home (A3d part 1, home/custody.py; FORMATS 2.1 and 2.4) against known answers written
BEFORE it (tmp/opus_scratch/home_a1/KNOWN_ANSWERS_by_opus.md on the PC). Standard library only.

    test_custody.py <home/custody.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]

The tree above home/ (home/, run/, workloads/, known/) is copied; a plant is applied to the copy's custody.py only.
The server side is made by the day's REAL programs: run "cust", slot 1, piece_games 2, the list rule with N12's six
openings (rows 86, 101, 0, 127, 81, 67). The worker plays round 1 (counters 1 to 4: pieces p0 = g1 g2, p1 = g3 g4) and
ends by the STOP file once its range seal is there; SCHEDULE.1 adds round 2 (5 to 6); the second start (epoch 2) plays
p2 = g5 g6 and ends by FENCE.json ("D"); the packer --once with the official converter (three binpack offers); the
terminal inventory. The fetch is stood in by a byte copy of the files a fetch takes (the root's and ranges' wire
copies, every offer's wire file LAST after the member files it names).
H1 the full home: 3 receipts as 2.1, RECEIVED 3/462, C1 3/462. H2 a second pass: nothing new, the receipts unchanged.
H3 p0 and p2 before p1: RECEIVED 2/335 and C1 1/187, then 3/462. H4 all six arrival orders: C1 after each arrival
is the longest held run from p0; the receipts equal at the end. H5 epochs [1, 2, 1] by index (forged): C1 never past
p1 (314) in all six orders. H6 a forged inventory naming another offer for p1: a fork record, C1 1/187; the same with
its footer not made right: no fork. R1 to R12 the refusals, waits, conflicts and confirmations of the known answers.
PLANTS (each must make the test fail): see PLANTS below; the numbers are those of the known answers.
VERSION 2 (tmp/opus_scratch/custody_v2/KNOWN_ANSWERS_custody_v2_by_opus.md on the PC, written before the code; the
seats' NOT YET, Astra 213621Z and Neon 223800Z): K1 a home folder that still holds run A's receipts, pointed at run B
(header B = A's with another run name): STOP 3, nothing counted, written or confirmed; run A again confirms; with no
header every --confirm is PENDING (exit 5). K2 a receipt not of its own name, kept path, form, members, schema or
slot: STOP 4. K3 a fork record of another run or index. K4 --confirm decodes the offer (2.4: wire and data); a key
of a slot the header lacks: exit 2. K5 headers of schema 1, a slot twice, a pilot row twice or not an int. K6 a
schedule of schema 1 or with a bad or repeated row: not used, its piece waits, no conflict. K7 an inventory naming a
piece twice or with a line not canonical: no fork. K8 a seal with rows -5: NOT RECEIVED.
"""
import hashlib
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import zlib
from pathlib import Path

if len(sys.argv) < 6:
    print("usage: test_custody.py <home/custody.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]")
    sys.exit(2)
SRC = Path(sys.argv[1]).resolve()
EXE, NET, CONV, WORK = (Path(a).resolve() for a in sys.argv[2:6])
PLANT = sys.argv[6] if len(sys.argv) > 6 else None
TREE = SRC.parent.parent
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)

PLANTS = {
    "plant1": ('            if (len(wb), sha256_bytes(wb)) != (m["wire_bytes"], m["wire_sha256"]):\n',
               '            if len(wb) != m["wire_bytes"]:\n'),
    "plant2": ('            if (len(data), sha256_bytes(data)) != (m["bytes"], m["sha256"]):\n', '            if False:\n'),
    "plant3": ('        if o["run_fingerprint"] != self.fp:\n', '        if False:\n'),
    "plant4": ('        if (o["slot"], o["index"]) != (k, i):\n', '        if False:\n'),
    "plant5": ('f"epoch {s[\'epoch\']} after epoch {ep}" if s["epoch"] < ep else ""',
               'f"epoch {s[\'epoch\']} after epoch {ep}" if False else ""'),
    "plant6": ('"prev_seal does not link to the seal before" if s["prev_seal"] != prev else',
               '"prev_seal does not link to the seal before" if False else'),
    "plant7": ("C1 {c['c1']} pieces {c['c1_rows']} \"", "C1 {c['received']} pieces {c['received_rows']} \""),
    "plant8": ("                if rp.exists():\n                    continue\n",
               "                if False:\n                    continue\n"),
    "plant9": ("                if r and i not in forks and (", "                if False and r and i not in forks and ("),
    "plant10": ('                if top is not None and r["first_counter"] <= rs[top]["last_counter"]:\n',
                '                if False:\n'),
    "plant11": ('                if not a <= r["first_counter"] <= r["last_counter"] <= b:\n', '                if False:\n'),
    "plant12": ('                have = rng.get(s["schedule"])\n', '                have = rng.get(s["schedule"], {})\n'),
    "plant13": ("            if (len(wb), sha256_bytes(wb)) != (wl, ws) or (dl is not None and len(data) != dl) or sha256_bytes(data) != ds:\n",
                "            if False:\n"),
    "plant14": ("        if sha256_bytes(hb) != fp:\n", "        if False:\n"),
    "plant15": ('"kept": f"wire/out/w{k:03d}"', '"kept": str(self.wire / "out" / f"w{k:03d}")'),
    "plant16": ('                and foot.get("fingerprint") == sha256_bytes(body) and body.startswith(self.hb)\n',
                '                and body.startswith(self.hb)\n'),
}
PLANTS.update({
    "plant17": ('        if r["run_fingerprint"] != self.fp:\n', '        if False:\n'),
    "plant18": ('        if not is_int(r["slot"], r["index"]) or (r["slot"], r["index"]) != (k, i):\n',
                '        if not is_int(r["slot"], r["index"]):\n'),
    "plant19": ('        if r["kept"] != f"wire/out/w{k:03d}" \\\n', '        if False \\\n'),
    "plant20": ('            r = parse_canon(p.read_bytes(), what)\n', '            r = json.loads(p.read_bytes())\n'),
    "plant21": ('                or not all(isinstance(m, dict) and sorted(m) == MEMBER_KEYS and is_int(m["bytes"], m["wire_bytes"])\n',
                '                or not all(True or isinstance(m, dict) and sorted(m) == MEMBER_KEYS and is_int(m["bytes"], m["wire_bytes"])\n'),
    "plant22": ('        H.check_records()\n', '        pass\n'),
    "plant23": ('                print(f"CONFIRM PENDING {x}: wire/RUN.json.zz is not at home yet; nothing is confirmed")\n            return 5\n',
                '                print(f"CONFIRM PENDING {x}: wire/RUN.json.zz is not at home yet; nothing is confirmed")\n            return 0\n'),
    "plant24": ('        want = [(f"p{i:06d}.offer.json.zz", True, r["offer_wire_bytes"], r["offer_wire_sha256"], None, r["offer_sha256"])]\n',
                '        want = [(f"p{i:06d}.offer.json.zz", False, r["offer_wire_bytes"], r["offer_wire_sha256"], None, r["offer_wire_sha256"])]\n'),
    "plant25": ('        if not is_int(h.get("schema")) or h["schema"] != 2:\n', '        if False:\n'),
    "plant26": ('        if len(set(h["slots"])) != len(h["slots"]):\n', '        if False:\n'),
    "plant27": ('        if self.pilot is None:\n', '        if False:\n'),
    "plant28": ('            if not isinstance(s, dict) or not is_int(s.get("schema"), s.get("n")) or (s["schema"], s["n"]) != (2, n) \\\n',
                '            if not isinstance(s, dict) or not is_int(s.get("n")) or s["n"] != n \\\n'),
    "plant29": ('                or (x["slot"], x["round"]) in out:\n', '                or False:\n'),
    "plant30": ('                if (o["slot"], o["index"]) in inv:\n', '                if False:\n'),
    "plant31": ('            lines = [parse_canon(ln + b"\\n", "TERMINAL.jsonl") for ln in body.split(b"\\n")[:-1]] if ok else []\n',
                '            lines = [json.loads(ln) for ln in body.split(b"\\n")[:-1]] if ok else []\n'),
    "plant32": ('                or s["rows"] < 0:\n', '                or False:\n'),
    "plant33": ('                or not is_int(r["schema"]) or r["schema"] != 2:\n', '                or not is_int(r["schema"]):\n'),
    "plant34": ('        if k not in self.h["slots"] or not self.rpath(k, i).exists():\n',
                '        if k is None or not self.rpath(k, i).exists():\n'),
    "plant35": ('        if [(m["name"], m["codec"]) for m in ms] not in [[(f"p{i:06d}" + x, c) for x, c in f] for f in FORMS.values()] \\\n',
                '        if False \\\n'),
    "plant36": ('        if ms[0]["sha256"] != r["seal_sha256"]:\n', '        if False:\n'),
})
if PLANT and PLANT not in PLANTS:
    print(f"STOP: no plant {PLANT}")
    sys.exit(2)
CP = WORK / "tree"
for sub in ("home", "run", "workloads", "known"):
    shutil.copytree(TREE / sub, CP / sub, ignore=shutil.ignore_patterns("__pycache__"))
if PLANT:
    old, new = PLANTS[PLANT]
    text = (CP / "home" / "custody.py").read_text(encoding="ascii")
    if text.count(old) != 1:                            # exit 2, never the 1 of a plant that made the test fail
        print(f"STOP: {PLANT}: the old text is not there exactly once")
        sys.exit(2)
    (CP / "home" / "custody.py").write_text(text.replace(old, new), encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy's custody.py")
RUN, CUST = CP / "run", CP / "home" / "custody.py"
sys.path.insert(0, str(RUN))
import worker as W  # noqa: E402

RESULTS = []


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(("PASS " if ok else "FAIL ") + f"{name}: got {str(got)[:300]}" + ("" if ok else f"; want {str(want)[:300]}"))
    return ok


def safe(fn):
    try:
        fn()
    except Exception:  # noqa: BLE001   a crash of a part is one FAIL, the other parts go on
        RESULTS.append((f"{fn.__name__} crashed", False))
        print(f"FAIL {fn.__name__} crashed:\n{traceback.format_exc()}")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


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
ROWS = [187, 127, 148]                                  # p0 = g1 g2 (86 + 101), p1 = g3 g4 (0 + 127), p2 = g5 g6 (81 + 67)
NOW = time.time()
SRV = WORK / "srv"
COUNTS = re.compile(r"custody: RECEIVED (\d+) pieces (\d+) rows; C1 (\d+) pieces (\d+) rows; new receipts (\d+); "
                    r"not received (\d+); waits (\d+); conflicts (\d+); forks (\d+)")


def row(rnd, first, last, n):
    return {"slot": 1, "round": rnd, "first": first, "last": last, "short": False, "schedule": n}


def wcmd():
    return [sys.executable, "-I", "-B", str(RUN / "worker.py"), "--root", str(SRV), "--slot", "1", "--exe", str(EXE),
            "--net", str(NET), "--manifest", str(MAN_PATH), "--known-startup", str(KNOWN), "--openings", str(OPENINGS)]


def play_until(seal_name: str, then) -> tuple:
    """The worker plays; once ranges/<seal_name> is there (create-only: whole), `then` writes STOP or FENCE.json and
    the worker ends by it. Its output goes to a file (no pipe to fill)."""
    log = WORK / f"srv.{seal_name}.out"
    with open(log, "wb") as f:
        p = subprocess.Popen(wcmd(), stdout=f, stderr=subprocess.STDOUT)
        end = time.time() + 600
        while not (SRV / "ranges" / seal_name).exists() and p.poll() is None and time.time() < end:
            time.sleep(0.5)
        then()
        try:
            p.wait(timeout=120)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
    return p.returncode, log.read_text(encoding="utf-8", errors="replace")[-400:]


def server() -> bool:
    put(SRV / "RUN.json", W.canon({
        "schema": 2, "run": "cust", "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
        "hard_cutoff_utc": T(NOW + 86400), "boot_id": W.boot_id(), "instance": "test-instance", "package": "0" * 64,
        "engine_sha256": sha(EXE.read_bytes()), "net_sha256": MAN["net_sha256"],
        "options_sha256": sha("".join(ln + "\n" for ln in MAN["options"]).encode("ascii")),
        "game_line": MAN["selfgame_line"], "opening_rule": {"kind": "list", "sha256": sha(OPENINGS.read_bytes()),
                                                             "count": len(N12)},
        "slots": [1], "piece_games": 2, "pilot_ranges": [row(1, 1, 4, 0)]}))
    FP["fp"] = fp = sha((SRV / "RUN.json").read_bytes())
    rc1, out1 = play_until("r0001.w001.seal.json", lambda: put(SRV / "STOP", b"stop\n"))
    put(SRV / "SCHEDULE.1.json", W.canon({"schema": 2, "run_fingerprint": fp, "n": 1, "prev": "first",
                                          "evidence": "0" * 64, "cutoff_utc": T(NOW + 3600),
                                          "dispatch_end_utc": T(NOW + 3540),
                                          "ranges": [row(1, 1, 4, 0), row(2, 5, 6, 1)]}))
    (SRV / "STOP").unlink()

    def fence():
        put(SRV / "FENCE.json", W.canon({"at_utc": T(time.time()), "cutoff_utc": T(NOW + 3600),
                                         "run_fingerprint": fp, "schema": 2, "why": "D"}))
    rc2, out2 = play_until("r0002.w001.seal.json", fence)
    closed = SRV / "w001" / "closed"
    seals = [json.loads((closed / f"p{i:06d}.seal.json").read_bytes()) for i in range(3)
             if (closed / f"p{i:06d}.seal.json").exists()]
    if not check("server: two starts exit 0, pieces of 187, 127, 148 rows, epochs [1, 1, 2], rounds [1, 1, 2], "
                 "schedules [0, 0, 1]",
                 (rc1, rc2, [s["rows"] for s in seals], [s["epoch"] for s in seals], [s["round"] for s in seals],
                  [s["schedule"] for s in seals]),
                 (0, 0, ROWS, [1, 1, 2], [1, 1, 2], [0, 0, 1])):
        print(out1, out2)
        return False
    p = subprocess.run([sys.executable, "-I", "-B", str(RUN / "packer.py"), "--root", str(SRV), "--converter",
                        str(CONV), "--once"], capture_output=True, text=True, timeout=600)
    q = subprocess.run([sys.executable, "-I", "-B", str(RUN / "terminal.py"), "--root", str(SRV)],
                       capture_output=True, text=True, timeout=300)
    forms = [json.loads((SRV / "out" / "w001" / f"p{i:06d}.offer.json").read_bytes())["form"] for i in range(3)
             if (SRV / "out" / "w001" / f"p{i:06d}.offer.json").exists()]
    return check("server: packer exit 0 with three binpack offers; terminal inventory exit 0 with its .zz",
                 (p.returncode, forms, q.returncode, (SRV / "TERMINAL.jsonl.zz").exists()),
                 (0, ["binpack"] * 3, 0, True))


FP = {}


def fetch_root(home: Path) -> None:
    for p in sorted(SRV.glob("*.zz")):
        put(home / "wire" / p.name, p.read_bytes())
    for p in sorted((SRV / "ranges").glob("*.zz")):
        put(home / "wire" / "ranges" / p.name, p.read_bytes())


def fetch_piece(home: Path, i: int) -> None:
    src, dst = SRV / "out" / "w001", home / "wire" / "out" / "w001"
    o = json.loads(zlib.decompress((src / f"p{i:06d}.offer.json.zz").read_bytes()))
    for m in o["members"]:
        put(dst / m["wire_name"], (src / m["wire_name"]).read_bytes())
    put(dst / f"p{i:06d}.offer.json.zz", (src / f"p{i:06d}.offer.json.zz").read_bytes())   # LAST, as a fetch does


def new_home(name: str, pieces=(0, 1, 2), inventory=True) -> Path:
    h = WORK / name
    fetch_root(h)
    if not inventory:
        (h / "wire" / "TERMINAL.jsonl.zz").unlink()
    for i in pieces:
        fetch_piece(h, i)
    return h


def custody(home: Path, *extra, fp=None):
    p = subprocess.run([sys.executable, "-I", "-B", str(CUST), "--home", str(home), "--fingerprint", fp or FP["fp"],
                        *extra], capture_output=True, text=True, timeout=300)
    out = (p.stdout + p.stderr).strip()
    m = COUNTS.search(out.splitlines()[-1]) if out else None
    return p.returncode, out, (tuple(int(x) for x in m.groups()) if m else None)


def receipts(home: Path) -> dict:
    d = home / "custody" / "w001"
    return {p.name: p.read_bytes() for p in sorted(d.glob("*.json"))} if d.is_dir() else {}


def no_time(rs: dict) -> dict:
    return {k: dict(json.loads(v), at_utc=None) for k, v in rs.items()}


def zz_rewrite(path: Path, fn) -> None:
    o = json.loads(zlib.decompress(path.read_bytes()))
    put(path, zlib.compress(W.canon(fn(o)), 6))


def reforge(home: Path, changes: dict) -> None:
    """Seals changed as `changes` says ({index: {field: value}}), every later prev_seal linked again unless the change
    names it, the seal's wire copy and the offer rewritten (a test helper, on a copy whose inventory was left out)."""
    d, prev = home / "wire" / "out" / "w001", None
    for i in range(3):
        s = json.loads(zlib.decompress((d / f"p{i:06d}.seal.json.zz").read_bytes()))
        if prev is not None:
            s["prev_seal"] = prev
        s.update(changes.get(i, {}))
        sb = W.canon(s)
        szz = zlib.compress(sb, 6)
        put(d / f"p{i:06d}.seal.json.zz", szz)

        def fix(o, sb=sb, szz=szz):
            o["seal_sha256"] = sha(sb)
            o["members"][0].update(bytes=len(sb), sha256=sha(sb), wire_bytes=len(szz), wire_sha256=sha(szz))
            return o
        zz_rewrite(d / f"p{i:06d}.offer.json.zz", fix)
        prev = sha(sb)


def counts_want(received, c1, new, bad=0, waits=0, conflicts=0, forks=0):
    return (len(received), sum(ROWS[i] for i in received), c1, sum(ROWS[:c1]), new, bad, waits, conflicts, forks)


# ---- the cases ---------------------------------------------------------------------------------------------------
def case_h1_h2():
    h = new_home("h")
    t0 = time.time()
    rc, out, c = custody(h)
    check("H1 the full home: exit 0, RECEIVED 3/462, C1 3/462, new 3, nothing else", (rc, c),
          (0, counts_want([0, 1, 2], 3, 3)))
    rs = receipts(h)
    check("H1 three receipt files, nothing else in custody/w001", sorted(rs), [f"p{i:06d}.receipt.json" for i in range(3)])
    for i in range(3):
        ob = (SRV / "out" / "w001" / f"p{i:06d}.offer.json").read_bytes()
        ow = (SRV / "out" / "w001" / f"p{i:06d}.offer.json.zz").read_bytes()
        seal = json.loads((SRV / "w001" / "closed" / f"p{i:06d}.seal.json").read_bytes())
        want = {"schema": 2, "run_fingerprint": FP["fp"], "slot": 1, "index": i, "epoch": [1, 1, 2][i],
                "first_counter": 2 * i + 1, "last_counter": 2 * i + 2, "offer_sha256": sha(ob),
                "offer_wire_bytes": len(ow), "offer_wire_sha256": sha(ow),
                "seal_sha256": sha((SRV / "w001" / "closed" / f"p{i:06d}.seal.json").read_bytes()),
                "members": json.loads(ob)["members"], "kept": "wire/out/w001", "at_utc": None}
        r = json.loads(rs[f"p{i:06d}.receipt.json"])
        at = r.get("at_utc")
        check(f"H1 receipt p{i:06d}: every field as 2.1 (seal epoch {seal['epoch']}, counters from the seal), canonical, "
              "at_utc inside the run",
              (dict(r, at_utc=None), W.canon(r) == rs[f"p{i:06d}.receipt.json"],
               isinstance(at, str) and T(t0 - 1) <= at <= T(time.time() + 1)), (want, True, True))
    time.sleep(1.1)
    rc2, out2, c2 = custody(h)
    check("H2 a second pass: exit 0, new 0, the same counts, every receipt's bytes unchanged",
          (rc2, c2, receipts(h) == rs), (0, counts_want([0, 1, 2], 3, 0), True))
    STATE["h_receipts"] = no_time(rs)
    STATE["h"] = h


def case_orders():
    for order in itertools.permutations(range(3)):
        h = WORK / ("o" + "".join(map(str, order)))
        fetch_root(h)
        got, held = [], set()
        for i in order:
            fetch_piece(h, i)
            held.add(i)
            rc, out, c = custody(h)
            got.append((rc, c[0] if c else None, c[2] if c else None))
        want, held = [], set()
        for i in order:
            held.add(i)
            run = 0
            while run in held:
                run += 1
            want.append((0, len(held), run))
        check(f"H4 arrival order {order}: (exit, RECEIVED pieces, C1 pieces) after each arrival", got, want)
        check(f"H4 arrival order {order}: the receipts at the end equal H1's (without at_utc)",
              no_time(receipts(h)), STATE.get("h_receipts"))
        if order == (0, 2, 1):
            h3 = new_home("h3", pieces=(0, 2))
            check("H3 p0 and p2 only: RECEIVED 2/335, C1 1/187", custody(h3)[2], counts_want([0, 2], 1, 2))
            fetch_piece(h3, 1)
            check("H3 then p1: RECEIVED 3/462, C1 3/462", custody(h3)[2], counts_want([0, 1, 2], 3, 1))


def case_h5():
    for order in itertools.permutations(range(3)):
        h = WORK / ("e" + "".join(map(str, order)))
        fetch_root(h)
        (h / "wire" / "TERMINAL.jsonl.zz").unlink()
        full = new_home("e_src" + "".join(map(str, order)), inventory=False)
        reforge(full, {1: {"epoch": 2}, 2: {"epoch": 1}})
        c1s, out = [], ""
        for i in order:
            for p in sorted((full / "wire" / "out" / "w001").glob(f"p{i:06d}.*")):
                if not p.name.endswith(".offer.json.zz"):
                    put(h / "wire" / "out" / "w001" / p.name, p.read_bytes())
            put(h / "wire" / "out" / "w001" / f"p{i:06d}.offer.json.zz",
                (full / "wire" / "out" / "w001" / f"p{i:06d}.offer.json.zz").read_bytes())
            rc, out, c = custody(h)
            c1s.append(c[2] if c else None)
        check(f"H5 epochs [1, 2, 1], order {order}: C1 never past p1, 2 pieces 314 rows at the end, the line names it",
              (max(x or 0 for x in c1s), custody(h)[2], "C1 w001 stops before p000002: epoch 1 after epoch 2" in out),
              (2, counts_want([0, 1, 2], 2, 0), True))


def forged_inventory(h: Path, fix_footer: bool) -> None:
    data = zlib.decompress((h / "wire" / "TERMINAL.jsonl.zz").read_bytes())
    lines = data.split(b"\n")[:-1]
    out = []
    for ln in lines[:-1]:
        o = json.loads(ln)
        if isinstance(o, dict) and o.get("t") == "piece" and o.get("index") == 1:
            ln = W.canon(dict(o, offer="f" * 64))[:-1]
        out.append(ln + b"\n")
    body = b"".join(out)
    foot = json.loads(lines[-1])
    if fix_footer:
        foot["fingerprint"] = sha(body)
    put(h / "wire" / "TERMINAL.jsonl.zz", zlib.compress(body + W.canon(foot), 6))


def case_h6():
    rc, out, c = custody(STATE["h"])
    check("H6 the real inventory: no fork (H's third pass)", (rc, c[8] if c else None,
                                                             (STATE["h"] / "custody" / "w001" / "p000001.fork.json").exists()),
          (0, 0, False))
    h = new_home("h6")
    forged_inventory(h, True)
    rc, out, c = custody(h)
    fork = h / "custody" / "w001" / "p000001.fork.json"
    f = json.loads(fork.read_bytes()) if fork.exists() else {}
    check("H6 an inventory naming another offer for p1 (footer made right): exit 0, a fork, C1 1/187, forks 1",
          (rc, c, f.get("found_offer_sha256"), f.get("receipt_offer_sha256") == STATE["h_receipts"]
           ["p000001.receipt.json"]["offer_sha256"]), (0, counts_want([0, 1, 2], 1, 3, forks=1), "f" * 64, True))
    check("H6 a third pass: the fork record unchanged, forks 1", (custody(h)[2], fork.read_bytes() == W.canon(f)),
          (counts_want([0, 1, 2], 1, 0, forks=1), True))
    h2 = new_home("h6b")
    forged_inventory(h2, False)
    rc, out, c = custody(h2)
    check("H6 the same with the footer NOT made right: no fork, C1 3/462, the line says it does not verify",
          (rc, c, "does not verify" in out), (0, counts_want([0, 1, 2], 3, 3), True))


def case_refusals():
    def one(name, prep, want_counts, text, pieces=(0, 1, 2), inventory=True):
        h = new_home(name, pieces=pieces, inventory=inventory)
        prep(h)
        rc, out, c = custody(h)
        check(f"{name}: exit 0, the counts, the line", (rc, c, text in out), (0, want_counts, True))
        if (rc, c) != (0, want_counts) or text not in out:
            print(out[-600:])
        return h
    d = ("wire", "out", "w001")

    def flip(h):
        p = h.joinpath(*d, "p000001.binpack")
        b = bytearray(p.read_bytes())
        b[len(b) // 2] ^= 1
        put(p, bytes(b))
    one("R1 one byte of p1.binpack", flip, counts_want([0, 2], 1, 2, bad=1),
        "NOT RECEIVED w001/p000001: p000001.binpack: the wire bytes are not the offer's")
    one("R2 p1.meta.xz not at home", lambda h: h.joinpath(*d, "p000001.meta.xz").unlink(),
        counts_want([0, 2], 1, 2, waits=1), "WAITS w001/p000001: p000001.meta.xz is not at home yet")

    def other_data(o):
        o["members"][0]["sha256"] = "0" * 64
        return o
    one("R3 the offer names another sha256 for the seal's data", lambda h: zz_rewrite(h.joinpath(*d, "p000001.offer.json.zz"),
        other_data), counts_want([0, 2], 1, 2, bad=1), "the decoded bytes are not the offer's")
    one("R4 the offer of another run", lambda h: zz_rewrite(h.joinpath(*d, "p000001.offer.json.zz"),
        lambda o: dict(o, run_fingerprint="1" * 64)), counts_want([0, 2], 1, 2, bad=1), "not this run's offer")
    one("R5 p1's offer with index 2", lambda h: zz_rewrite(h.joinpath(*d, "p000001.offer.json.zz"),
        lambda o: dict(o, index=2)), counts_want([0, 2], 1, 2, bad=1), "not of its own name")

    def spaces(h):
        p = h.joinpath(*d, "p000001.offer.json.zz")
        o = json.loads(zlib.decompress(p.read_bytes()))
        put(p, zlib.compress((json.dumps(o, sort_keys=True) + "\n").encode("ascii"), 6))
    one("R6 p1's offer not canonical", spaces, counts_want([0, 2], 1, 2, bad=1), "NOT RECEIVED w001/p000001")
    h7 = new_home("R7")
    rc, out, c = custody(h7, fp="2" * 64)
    check("R7 another --fingerprint: exit 3, no custody folder", (rc, (h7 / "custody").exists()), (3, False))
    (h7 / "wire" / "RUN.json.zz").unlink()
    rc, out, c = custody(h7)
    check("R7 no RUN.json.zz at home: exit 0, nothing to do, no custody folder",
          (rc, "nothing to do" in out, (h7 / "custody").exists()), (0, True, False))

    def level0(h):
        p = h.joinpath(*d, "p000001.seal.json.zz")
        put(p, zlib.compress(zlib.decompress(p.read_bytes()), 0))
    one("R8 p1's seal wire copy at another level", level0, counts_want([0, 2], 1, 2, bad=1),
        "p000001.seal.json.zz: the wire bytes are not the offer's")
    one("R9 p0 forged to last_counter 3", lambda h: reforge(h, {0: {"last_counter": 3}}),
        counts_want([0, 1, 2], 3, 3, conflicts=1), "CONFLICT w001: p000000 [1, 3] and p000001 [3, 4] overlap",
        inventory=False)
    one("R10 p2 forged to last_counter 7", lambda h: reforge(h, {2: {"last_counter": 7}}),
        counts_want([0, 1, 2], 3, 3, conflicts=1), "CONFLICT w001/p000002: [5, 7] is not inside round 2's range",
        inventory=False)

    def no_sched(h):
        reforge(h, {2: {"last_counter": 7}})
        (h / "wire" / "SCHEDULE.1.json.zz").unlink()
    one("R10 the same without SCHEDULE.1 at home", no_sched, counts_want([0, 1, 2], 3, 3, waits=1),
        "WAITS w001/p000002: schedule 1 is not at home yet", inventory=False)
    one("R12 p1 forged to prev_seal 0 x 64", lambda h: reforge(h, {1: {"prev_seal": "0" * 64}}),
        counts_want([0, 1, 2], 1, 3), "C1 w001 stops before p000001: prev_seal does not link", inventory=False)


def case_confirm():
    h = STATE["h"]
    before = receipts(h)
    rc, out, c = custody(h, "--confirm", "w001/p000001")
    check("R11 --confirm w001/p000001 on H: exit 0, CONFIRMED, no receipt added or changed",
          (rc, "CONFIRMED w001/p000001" in out, receipts(h) == before), (0, True, True))
    h2 = WORK / "R11"
    shutil.copytree(h, h2)
    p = h2 / "wire" / "out" / "w001" / "p000001.binpack"
    b = bytearray(p.read_bytes())
    b[7] ^= 1
    put(p, bytes(b))
    rc, out, c = custody(h2, "--confirm", "w001/p000001")
    check("R11 one byte of p1.binpack changed after its receipt: exit 5 naming the member",
          (rc, "CONFIRM FAILED w001/p000001: p000001.binpack" in out), (5, True))
    (h2 / "wire" / "out" / "w001" / "p000001.meta.xz").unlink()
    rc, out, c = custody(h2, "--confirm", "w001/p000000", "w001/p000001")
    check("R11 p1.meta.xz gone too, two keys: exit 5, p0 CONFIRMED", (rc, "CONFIRMED w001/p000000" in out), (5, True))
    rc, out, c = custody(h, "--confirm", "w001/p000009")
    check("R11 --confirm a key without a receipt: exit 2", rc, 2)


# ---- version 2 (KNOWN_ANSWERS_custody_v2_by_opus.md) -------------------------------------------------------------
def copy_h(name: str) -> Path:
    h = WORK / name
    shutil.copytree(STATE["h"], h)
    return h


def custody_bytes(h: Path) -> dict:
    return {str(p.relative_to(h)): p.read_bytes() for p in sorted((h / "custody").rglob("*")) if p.is_file()}


def header_b() -> tuple:
    hb = W.canon(dict(json.loads((SRV / "RUN.json").read_bytes()), run="cust-b"))
    return hb, sha(hb)


def r0(h: Path) -> dict:
    return json.loads((h / "custody" / "w001" / "p000000.receipt.json").read_bytes())


def last_line(out: str) -> str:
    return out.splitlines()[-1] if out else ""


def case_v2_run():
    hb_b, fp_b = header_b()
    h = copy_h("K1a")
    a_zz = (h / "wire" / "RUN.json.zz").read_bytes()
    before = custody_bytes(h)
    put(h / "wire" / "RUN.json.zz", zlib.compress(hb_b, 6))
    rc, out, c = custody(h, fp=fp_b)
    last = last_line(out)
    check("K1a run B on run A's receipts: exit 3, the STOP line names p000000.receipt.json and another run, no counts, "
          "custody/ unchanged", (rc, last.startswith("custody: STOP (3):") and "p000000.receipt.json" in last and
                                 "another run" in last, c, custody_bytes(h) == before), (3, True, None, True))
    rc, out, c = custody(h, "--confirm", "w001/p000000", fp=fp_b)
    check("K1a --confirm run A's key under run B: exit 3, nothing CONFIRMED", (rc, "CONFIRMED" in out), (3, False))
    put(h / "wire" / "RUN.json.zz", a_zz)
    rc, out, c = custody(h)
    rc2, out2, c2 = custody(h, "--confirm", "w001/p000000")
    check("K1a run A again: a pass exit 0, 3/462, C1 3/462, new 0; --confirm exit 0 CONFIRMED (control)",
          (rc, c, rc2, "CONFIRMED w001/p000000" in out2), (0, counts_want([0, 1, 2], 3, 0), 0, True))
    (h / "wire" / "RUN.json.zz").unlink()
    got = []
    for key in ("w001/p000009", "w001/p000000"):
        rc, out, c = custody(h, "--confirm", key)
        got.append((rc, f"CONFIRM PENDING {key}" in out, "CONFIRMED" in out))
    check("K1a no header: --confirm an unknown key, then a held key: exit 5 PENDING each, nothing CONFIRMED", got,
          [(5, True, False)] * 2)
    check("K1a no header: --confirm w1/p0 (not a key): exit 2", custody(h, "--confirm", "w1/p0")[0], 2)
    rc, out, c = custody(h)
    check("K1a no header, a pass: exit 0, nothing to do (control)", (rc, "nothing to do" in out), (0, True))
    h = new_home("K1b")
    r = dict(STATE["h_receipts"]["p000000.receipt.json"], run_fingerprint=fp_b, index=5, at_utc=T(NOW))
    put(h / "custody" / "w001" / "p000005.receipt.json", W.canon(r))
    rc, out, c = custody(h)
    check("K1b another run's receipt at p000005, run A's offers without receipts: exit 3, no receipt written",
          (rc, sorted(p.name for p in (h / "custody" / "w001").iterdir())), (3, ["p000005.receipt.json"]))


def case_v2_records():
    def one(name, rel, fn, *extra, want=4):
        h = copy_h(name.split()[0])
        fn(h, h / "custody" / rel)
        rc, out, c = custody(h, *extra)
        last = last_line(out)
        if not check(f"{name}: exit {want}, the STOP line names {rel}",
                     (rc, last.startswith(f"custody: STOP ({want}):") and rel in last), (want, True)):
            print(out[-600:])

    def rewrite(**over):
        return lambda h, p: put(p, W.canon(dict(r0(h), **over)))

    def no_wsha(h, p):
        r = r0(h)
        r["members"][0].pop("wire_sha256")
        put(p, W.canon(r))

    def fork(**over):
        f = {"schema": 2, "run_fingerprint": FP["fp"], "slot": 1, "index": 1, "receipt_seal_sha256": "1" * 64,
             "receipt_offer_sha256": "2" * 64, "found_seal_sha256": "3" * 64, "found_offer_sha256": "f" * 64,
             "at_utc": T(NOW), "how": "the terminal inventory names another seal or offer for a piece with a receipt"}
        return lambda h, p: put(p, W.canon(dict(f, **over)))
    one("K2a p0's receipt under the name p000001", "w001/p000001.receipt.json",
        lambda h, p: put(p, (h / "custody" / "w001" / "p000000.receipt.json").read_bytes()))
    one("K2b p0's receipt with kept wire/out/w002", "w001/p000000.receipt.json", rewrite(kept="wire/out/w002"))
    one("K2c p0's receipt with spaces (not canonical)", "w001/p000000.receipt.json",
        lambda h, p: put(p, (json.dumps(r0(h), sort_keys=True, indent=1) + "\n").encode("ascii")))
    one("K2d1 p0's receipt, members[0] without wire_sha256: a pass", "w001/p000000.receipt.json", no_wsha)
    one("K2d2 the same: --confirm w001/p000000", "w001/p000000.receipt.json", no_wsha, "--confirm", "w001/p000000")
    one("K2e p0's receipt of schema 1", "w001/p000000.receipt.json", rewrite(schema=1))
    one("K2f p0's receipt with slot 2", "w001/p000000.receipt.json", rewrite(slot=2))

    def member(j, **over):
        def fn(h, p):
            r = r0(h)
            r["members"][j].update(over)
            put(p, W.canon(r))
        return fn
    one("K2g p0's receipt, members[1] of codec lzma (no form of 1.6): a pass", "w001/p000000.receipt.json",
        member(1, codec="lzma"))
    one("K2h p0's receipt, members[0] sha256 0 x 64 (not its seal): a pass", "w001/p000000.receipt.json",
        member(0, sha256="0" * 64))
    one("K3a a fork record of another run at p000001", "w001/p000001.fork.json", fork(run_fingerprint=header_b()[1]),
        want=3)
    one("K3b a fork record of this run with index 2 at p000001", "w001/p000001.fork.json", fork(index=2))
    h = copy_h("K4a")
    put(h / "custody" / "w001" / "p000000.receipt.json", W.canon(dict(r0(h), offer_sha256="e" * 64)))
    rc, out, c = custody(h, "--confirm", "w001/p000000")
    check("K4a offer_sha256 not the kept offer's data: --confirm exit 5 naming the offer (2.4: wire and data)",
          (rc, "CONFIRM FAILED w001/p000000: p000000.offer.json.zz" in out), (5, True))
    h = copy_h("K4b")
    put(h / "custody" / "w002" / "p000000.receipt.json", (h / "custody" / "w001" / "p000000.receipt.json").read_bytes())
    check("K4b --confirm w002/p000000, a slot the header lacks (a receipt file lies there): exit 2",
          custody(h, "--confirm", "w002/p000000")[0], 2)


def case_v2_header():
    a = json.loads((SRV / "RUN.json").read_bytes())
    for name, hdr in (("K5a a header of schema 1", dict(a, schema=1)), ("K5b slots [1, 1]", dict(a, slots=[1, 1])),
                      ("K5c pilot_ranges with (1, 1) twice", dict(a, pilot_ranges=a["pilot_ranges"] * 2)),
                      ('K5d a pilot row with first "1"', dict(a, pilot_ranges=[dict(a["pilot_ranges"][0], first="1")]))):
        h = new_home(name.split()[0], pieces=())
        hb = W.canon(hdr)
        put(h / "wire" / "RUN.json.zz", zlib.compress(hb, 6))
        rc, out, c = custody(h, fp=sha(hb))
        check(f"{name}: exit 3, nothing written", (rc, (h / "custody").exists()), (3, False))


def case_v2_schedules():
    def extra_row(s):
        s["ranges"].append(dict(s["ranges"][1], last=5))
        return s

    def str_first(s):
        s["ranges"][1]["first"] = "5"
        return s
    for name, fn in (("K6a SCHEDULE.1 of schema 1", lambda s: dict(s, schema=1)),
                     ("K6b SCHEDULE.1 with a second (1, 2) row (5, 5)", extra_row),
                     ('K6c SCHEDULE.1 with the (1, 2) row first "5"', str_first)):
        h = new_home(name.split()[0], inventory=False)
        zz_rewrite(h / "wire" / "SCHEDULE.1.json.zz", fn)
        rc, out, c = custody(h)
        if not check(f"{name}: it does not verify, p2 WAITS, no conflict",
                     (rc, c, "is not schedule 1 of this run" in out), (0, counts_want([0, 1, 2], 3, 3, waits=1), True)):
            print(out[-600:])


def forged_inventory_v2(h: Path, mode: str) -> None:
    data = zlib.decompress((h / "wire" / "TERMINAL.jsonl.zz").read_bytes())
    lines = data.split(b"\n")[:-1]
    out = []
    for ln in lines[:-1]:
        o = json.loads(ln)
        if isinstance(o, dict) and o.get("t") == "piece" and o.get("index") == 1:
            other = dict(o, offer="f" * 64)
            if mode == "twice":
                out.append(ln + b"\n")
                ln = W.canon(other)[:-1]
            else:
                ln = json.dumps(other, sort_keys=True).encode("ascii")
        out.append(ln + b"\n")
    body = b"".join(out)
    put(h / "wire" / "TERMINAL.jsonl.zz",
        zlib.compress(body + W.canon(dict(json.loads(lines[-1]), fingerprint=sha(body))), 6))


def case_v2_inventory():
    for name, mode, text in (("K7a an inventory naming p1 twice, the second with another offer", "twice", "twice"),
                             ("K7b p1's inventory line with spaces naming another offer", "spaces", "does not verify")):
        h = new_home(name.split()[0])
        forged_inventory_v2(h, mode)
        rc, out, c = custody(h)
        if not check(f"{name} (footer made right): no fork, C1 3/462, the line says why", (rc, c, text in out),
                     (0, counts_want([0, 1, 2], 3, 3), True)):
            print(out[-600:])
    h = new_home("K8", inventory=False)
    reforge(h, {0: {"rows": -5}})
    rc, out, c = custody(h)
    check("K8 p0's seal forged to rows -5: NOT RECEIVED as not a seal of 1.5, RECEIVED 2/275, C1 0, new 2, bad 1",
          (rc, c, "NOT RECEIVED w001/p000000: the seal is not a seal of 1.5" in out),
          (0, counts_want([1, 2], 0, 2, bad=1), True))


def main() -> int:
    t0 = time.time()
    STATE["ok"] = False
    try:
        STATE["ok"] = server()
    except Exception:  # noqa: BLE001
        print(f"FAIL the server fixture crashed:\n{traceback.format_exc()}")
        RESULTS.append(("server fixture crashed", False))
    if STATE["ok"]:
        for fn in (case_h1_h2, case_orders, case_h5, case_h6, case_refusals, case_confirm, case_v2_run,
                   case_v2_records, case_v2_header, case_v2_schedules, case_v2_inventory):
            safe(fn)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)} of {len(RESULTS)} checks pass ({time.time() - t0:.0f} s)"
          + (f"; PLANT {PLANT}" if PLANT else ""))
    return 0 if not bad and RESULTS else 1


STATE = {}
if __name__ == "__main__":
    sys.exit(main())

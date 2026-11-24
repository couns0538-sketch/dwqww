"""test_fetch.py: A3f, the home fetch (home/fetch.py; FORMATS 0, 1.6, 2.1 [2.4] [2.7]; specs/home_fetch.md) against
known answers F1 to F21 written BEFORE it (tmp/opus_scratch/fetch/KNOWN_ANSWERS_fetch_by_opus.md on the PC; Opus,
24 Nov). Standard library only.

    test_fetch.py <home/fetch.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]

The tree above home/ (home/, run/, workloads/, known/, tests/) is copied; a plant is applied to the copy's fetch.py.
The transport is tests/fake_transport.py ("transport": "local"), which serves a folder and takes scripted pauses,
cuts and failures from a plan file. Two kinds of server folder:
SRV  a REAL run made as test_custody.py makes it (worker.py plays rounds 1 and 2, packer.py --once with the official
     converter, terminal.py): three binpack offers, the control files, two range seals. Custody judges what came.
SYN  a made-up run for the transfer-level answers: a header {"run": "syn", "schema": 2, "slots": [1]} and ONE raw
     offer p000000 whose members are a made-up seal and a 1,000-byte p000000.raw.zz (the fetch checks an offer's
     record and every member's wire length and sha256, never a member's content).
F8 also runs Windows' own ssh.exe -G (it reads the given files and prints the options; it connects to nothing).
F20 and F21 run the fetch's own sftp branch with the REAL client: Windows' own sftp.exe talks through -D to Git for
Windows' sftp-server.exe, which serves a folder of this test (no network, no key); only the command line is replaced.
"""
import datetime
import hashlib
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
    print("usage: test_fetch.py <home/fetch.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]")
    sys.exit(2)
SRC = Path(sys.argv[1]).resolve()
EXE, NET, CONV, WORK = (Path(a).resolve() for a in sys.argv[2:6])
PLANT = sys.argv[6] if len(sys.argv) > 6 else None
TREE = SRC.parent.parent
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)

PLANTS = {   # the stand-ins of the known answers' last section, one rule removed at a time
    "plant1": ("            start = 0 if attempt == 2 else old if old == whole else max(0, old - self.t.window)  # a whole "
               "one: check\n", "            start = 0\n"),                                    # no resume
    "plant2": ("                                  lambda x, s=m[\"wire_sha256\"]: file_sha256(x) == s, \"member\")\n",
               "                                  lambda x, s=m[\"wire_sha256\"]: True, \"member\")\n"),  # no hash
    "plant3": ("        if r is not None or final.exists():\n",
               "        if r is None and final.exists():\n"),                                    # re-read on listing
    "plant4": ("            self.keep_beside(p, final, n)\n", "            os.replace(p, final)\n"),   # no fork name
    "plant5": ("                elif silent > self.idle * 1000:\n", "                elif False:\n"),  # no idle cut
    "plant6": ("                    self.note(t=\"partial\", rel=rel, have=n, whole=whole, silent_ms=silent,\n",
               "                    self.note(t=\"partial\", rel=rel, have=n, whole=whole, silent_ms=silent, rows=n // 8,\n"),
    "plant7": ("            if sorted(m) != MEMBER_KEYS or m[\"wire_name\"] != m[\"name\"] + (\".zz\" if m[\"name\"]"
               ".endswith(\".seal.json\") else \"\") \\\n",
               "            if sorted(m) != MEMBER_KEYS or m[\"wire_name\"] not in (m[\"name\"], m[\"name\"] + \".zz\") \\\n"),
    "plant8": ("        short = [m[\"wire_name\"] for m in ms if listed.get(m[\"wire_name\"]) != m[\"wire_bytes\"]]\n",
               "        final.parent.mkdir(parents=True, exist_ok=True)\n        os.link(p, final)\n"
               "        short = [m[\"wire_name\"] for m in ms if listed.get(m[\"wire_name\"]) != m[\"wire_bytes\"]]\n"),
    "plant9": ("                [(m.get(\"name\"), m.get(\"codec\")) if isinstance(m, dict) else None for m in ms] != \\\n"
               "                [(name + x, c) for x, c in FORMS[o[\"form\"]]]:\n", "                False:\n"),
    "plant10": ("        if not self.binds and ((self.budget is not None and self.received + need > self.budget)\n",
                "        if False and ((self.budget is not None and self.received + need > self.budget)\n"),
    "plant11": ("            if sha256_bytes(data) != self.fp:\n", "            if False:\n"),
    "plant12": ("            if f.exists():\n                self.set_aside(f)\n",
                "            if False:\n                self.set_aside(f)\n"),
    "plant13": ("        if size(refused) == n and refused.exists():\n", "        if False:\n"),
    "plant14": ("            self.lock = SlotLock(fdir)                  # held until the process ends; the OS frees it\n",
                "            self.lock = None\n"),                                            # no lock
    "plant15": ("                elif time.monotonic() - t0 > self.cap:\n", "                elif False:\n"),  # no cap
}
CP = WORK / "tree"
for sub in ("home", "run", "workloads", "known", "tests"):
    shutil.copytree(TREE / sub, CP / sub, ignore=shutil.ignore_patterns("__pycache__"))
if PLANT:
    old, new = PLANTS[PLANT]
    text = (CP / "home" / "fetch.py").read_text(encoding="ascii")
    if text.count(old) != 1:                            # exit 2, never the 1 of a plant that made the test fail
        print(f"STOP: {PLANT}: the old text is not there exactly once")
        sys.exit(2)
    (CP / "home" / "fetch.py").write_text(text.replace(old, new), encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy's fetch.py")
RUN, FETCH, CUST, FAKE = CP / "run", CP / "home" / "fetch.py", CP / "home" / "custody.py", CP / "tests" / "fake_transport.py"
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


# ---- the real server, as test_custody.py makes it -----------------------------------------------------------------
MAN_PATH, KNOWN = CP / "workloads" / "MANIFEST.json", CP / "known" / "startup.json"
MAN = json.loads(MAN_PATH.read_bytes())
N12 = [ln.split()[3:] for ln in (CP / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
OPENINGS = WORK / "n12_openings.txt"
OPENINGS.write_bytes("".join(" ".join(o) + "\n" for o in N12).encode("ascii"))
ROWS = [187, 127, 148]
NOW = time.time()
SRV = WORK / "srv"
FP = {}
CCOUNTS = re.compile(r"custody: RECEIVED (\d+) pieces (\d+) rows; C1 (\d+) pieces (\d+) rows; new receipts (\d+); "
                     r"not received (\d+); waits (\d+); conflicts (\d+); forks (\d+)")


def row(rnd, first, last, n):
    return {"slot": 1, "round": rnd, "first": first, "last": last, "short": False, "schedule": n}


def wcmd():
    return [sys.executable, "-I", "-B", str(RUN / "worker.py"), "--root", str(SRV), "--slot", "1", "--exe", str(EXE),
            "--net", str(NET), "--manifest", str(MAN_PATH), "--known-startup", str(KNOWN), "--openings", str(OPENINGS)]


def play_until(seal_name: str, then) -> tuple:
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
        "schema": 2, "run": "fetch", "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
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
    if not check("server: two starts exit 0, pieces of 187, 127, 148 rows", (rc1, rc2, [s["rows"] for s in seals]),
                 (0, 0, ROWS)):
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


def stand_in_wire(srv: Path) -> dict:
    """What test_custody.py's stand-in fetch copies (the root's and ranges' .zz, every offer and the members it
    names): {path under wire/: sha256}. The known answer of F16, from another program than fetch.py."""
    out = {p.name: sha(p.read_bytes()) for p in srv.glob("*.zz")}
    out.update({f"ranges/{p.name}": sha(p.read_bytes()) for p in (srv / "ranges").glob("*.zz")})
    src = srv / "out" / "w001"
    for p in src.glob("p*.offer.json.zz"):
        o = json.loads(zlib.decompress(p.read_bytes()))
        for m in o["members"] + [{"wire_name": p.name}]:
            out[f"out/w001/{m['wire_name']}"] = sha((src / m["wire_name"]).read_bytes())
    return out


# ---- the made-up server ---------------------------------------------------------------------------------------------
RAW = bytes((i * 7 + 3) % 256 for i in range(1000))   # the 1,000-byte member


def syn(name: str, fix=None, plain=False) -> tuple:
    """A made-up run in WORK/<name>: (folder, fingerprint, {wire name: bytes}). fix(offer) may change the record;
    plain adds a plain p000000.seal.json and a plain p000001.offer.json (F9)."""
    srv = WORK / name
    hb = W.canon({"run": "syn", "schema": 2, "slots": [1]})
    fp = sha(hb)
    put(srv / "RUN.json.zz", zlib.compress(hb, 6))
    sb = W.canon({"made_up": "the seal of p000000"})
    szz = zlib.compress(sb, 6)
    ms = [{"name": "p000000.seal.json", "codec": "none", "bytes": len(sb), "sha256": sha(sb),
           "wire_name": "p000000.seal.json.zz", "wire_bytes": len(szz), "wire_sha256": sha(szz)},
          {"name": "p000000.raw.zz", "codec": "zlib", "bytes": len(RAW), "sha256": sha(RAW),
           "wire_name": "p000000.raw.zz", "wire_bytes": len(RAW), "wire_sha256": sha(RAW)}]
    o = {"schema": 2, "run_fingerprint": fp, "slot": 1, "index": 0, "seal_sha256": sha(sb), "form": "raw", "members": ms}
    if fix:
        fix(o)
    d = srv / "out" / "w001"
    files = {"RUN.json.zz": (srv / "RUN.json.zz").read_bytes(), "p000000.offer.json.zz": zlib.compress(W.canon(o), 6),
             "p000000.seal.json.zz": szz, "p000000.raw.zz": RAW}
    for n, b in list(files.items())[1:]:
        put(d / n, b)
    if plain:
        put(d / "p000000.seal.json", sb)
        put(d / "p000001.offer.json", W.canon(o))
    return srv, fp, files


# ---- running the programs -----------------------------------------------------------------------------------------
FCOUNTS = re.compile(r"fetch: listing (\d+) bytes; control (\d+) files (\d+) bytes; offers (\d+) files (\d+) bytes; "
                     r"members (\d+) files (\d+) bytes; sent again (\d+) bytes; partial (\d+); confirmations (\d+); "
                     r"forks (\d+); refused (\d+); incomplete (\d+); ignored (\d+); budget binds (yes|no)\Z")
KEYS = ("listing", "cf", "cb", "of", "ob", "mf", "mb", "again", "partial", "conf", "forks", "refused", "incomplete",
        "ignored", "binds")


def want(**kw) -> dict:
    """Every count 0 and "budget binds no" unless named; the listing's bytes are not compared."""
    return {k: kw.get(k, "no" if k == "binds" else 0) for k in KEYS if k != "listing"}


def config(srv: Path, idle: int = 10, window: int = 0, cap=None) -> Path:
    p = WORK / f"cfg_{srv.name}_{idle}_{window}_{cap}.json"
    if not p.exists():
        cfg = {"transport": "local", "remote_root": str(srv), "idle_s": idle, "python": sys.executable,
               "sender": str(FAKE), "window_bytes": window}
        if cap is not None:                             # without it the fetch takes its default (1800 s)
            cfg["transfer_s"] = cap
        p.write_text(json.dumps(cfg), encoding="ascii")
    return p


def fetch(home: Path, srv: Path, fp: str, *extra, idle: int = 10, window: int = 0, cap=None):
    t = time.time()
    p = subprocess.run([sys.executable, "-I", "-B", str(FETCH), "--home", str(home), "--fingerprint", fp, "--config",
                        str(config(srv, idle, window, cap)), *extra], capture_output=True, text=True, timeout=600)
    out = (p.stdout + p.stderr).strip()
    m = FCOUNTS.fullmatch(out.splitlines()[-1]) if out else None
    c = {k: (v if k == "binds" else int(v)) for k, v in zip(KEYS, m.groups())} if m else None
    if c:
        c.pop("listing")
    return p.returncode, out, c, time.time() - t


def plan(srv: Path, calls: dict) -> None:
    srv.with_name(srv.name + ".plan.json").write_text(json.dumps(calls), encoding="ascii")


def plan_left(srv: Path) -> dict:
    p = srv.with_name(srv.name + ".plan.json")
    return {k: v for k, v in json.loads(p.read_text(encoding="ascii")).items() if v} if p.exists() else {}


def wire(home: Path) -> dict:
    d = home / "wire"
    return {p.relative_to(d).as_posix(): sha(p.read_bytes()) for p in sorted(d.rglob("*")) if p.is_file()} \
        if d.is_dir() else {}


def journal(home: Path) -> list:
    p = home / "fetch" / "journal.jsonl"
    return [json.loads(ln) for ln in p.read_text(encoding="ascii").splitlines()] if p.exists() else []


def custody(home: Path, *extra):
    p = subprocess.run([sys.executable, "-I", "-B", str(CUST), "--home", str(home), "--fingerprint", FP["fp"], *extra],
                       capture_output=True, text=True, timeout=300)
    out = (p.stdout + p.stderr).strip()
    m = CCOUNTS.search(out.splitlines()[-1]) if out else None
    return p.returncode, out, (tuple(int(x) for x in m.groups()) if m else None)


def receipts(home: Path) -> dict:
    d = home / "custody" / "w001"
    return {p.name: p.read_bytes() for p in sorted(d.glob("*.json"))} if d.is_dir() else {}


def sizes(srv: Path, names) -> int:
    return sum((srv / n).stat().st_size for n in names)


STATE = {}


# ---- the cases ----------------------------------------------------------------------------------------------------
def case_full():
    """F16 and F15: one pass over the real run, custody on it, then a second pass that fetches nothing."""
    h = WORK / "H"
    rc, out, c, _ = fetch(h, SRV, FP["fp"])
    stand = stand_in_wire(SRV)
    ctl = sorted(n for n in stand if not n.startswith("out/"))
    offers = sorted(n for n in stand if n.endswith(".offer.json.zz"))
    mems = sorted(n for n in stand if n.startswith("out/") and n not in offers)
    check("F16 one pass over the real run: exit 0; control 6 files, offers 3, members 9, every byte count the server "
          "files' lengths, nothing sent again, ignored 9 (GUESS)",
          (rc, c), (0, want(cf=6, cb=sizes(SRV, ctl), of=3, ob=sizes(SRV, offers), mf=9, mb=sizes(SRV, mems), ignored=9)))
    check("F16 wire/ holds exactly what test_custody's stand-in fetch copies, byte for byte", wire(h), stand)
    check("F16 no partial is left", sorted(p.name for p in (h / "fetch" / "part").rglob("*") if p.is_file()), [])
    rc, out2, cc = custody(h)
    check("F16 custody afterwards: exit 0, RECEIVED and C1 3 pieces 462 rows, 3 new receipts", (rc, cc),
          (0, (3, 462, 3, 462, 3, 0, 0, 0, 0)))
    before = wire(h)
    rc, out, c, _ = fetch(h, SRV, FP["fp"])
    check("F15 a second pass over the complete fetch: exit 0, every count 0 (the 9 plain names ignored again)",
          (rc, c), (0, want(ignored=9)))
    check("F15 wire/ byte for byte unchanged by the second pass", wire(h) == before, True)
    STATE["H"] = h


def case_header():
    """F13: another run's header at home, or a server header that is not --fingerprint: exit 3, nothing placed."""
    h = WORK / "F13a"
    other = zlib.compress(W.canon({"run": "other", "schema": 2, "slots": [1]}), 6)
    put(h / "wire" / "RUN.json.zz", other)
    rc, out, c, _ = fetch(h, SRV, FP["fp"])
    j = journal(h)
    check("F13 another run's RUN.json.zz at home: exit 3, wire/ only that file, the journal's last line a stop 3",
          (rc, wire(h), j[-1].get("t") if j else None, j[-1].get("code") if j else None),
          (3, {"RUN.json.zz": sha(other)}, "stop", 3))
    h = WORK / "F13b"
    rc, out, c, _ = fetch(h, SRV, sha(b"another run"))
    left = sorted(p.name for p in (h / "fetch" / "part").rglob("*") if p.is_file())
    check("F13 the server's RUN.json.zz does not decode to --fingerprint: exit 3, wire/ empty, no partial left",
          (rc, wire(h), left), (3, {}, []))
    srv, fp, files = syn("syn_f17")
    h = WORK / "F17"
    put(h / "custody" / "w001" / "p000000.receipt.json",
        W.canon({"run_fingerprint": sha(b"another run"), "slot": 1, "index": 0, "schema": 2}))
    rc, out, c, _ = fetch(h, srv, fp)
    check("F17 a receipt of another run in custody/: exit 3, no offer or member placed (the header is)",
          (rc, wire(h)), (3, {"RUN.json.zz": sha(files["RUN.json.zz"])}))


def case_resume():
    """F1, F7, F2, F14 on the made-up run: a cut at 400 of 1,000 bytes, then the next pass."""
    srv, fp, files = syn("syn_f1")
    ob, sb = len(files["p000000.offer.json.zz"]), len(files["p000000.seal.json.zz"])
    plan(srv, {"get out/w001/p000000.raw.zz": [{"chunks": [[400, 0]], "hang_s": 3}]})
    h = WORK / "F1"
    rc, out, c, _ = fetch(h, srv, fp, idle=1)
    part = h / "fetch" / "part" / fp / "out" / "w001" / "p000000.raw.zz"
    check("F1 pass 1: exit 0; the header, the offer (kept in part) and the seal; 400 bytes of the member, partial 1, "
          "incomplete 1, nothing sent again", (rc, c, part.stat().st_size if part.exists() else None),
          (0, want(cf=1, cb=len(files["RUN.json.zz"]), ob=ob, mf=1, mb=sb + 400, partial=1, incomplete=1), 400))
    check("F1 pass 1: wire/ holds the header and the seal only (no offer before its members)", sorted(wire(h)),
          ["RUN.json.zz", "out/w001/p000000.seal.json.zz"])
    j = [x for x in journal(h) if x.get("t") == "partial"]
    check("F7 the cut is recorded as 400 partial bytes of 1,000 whole bytes, without any rows",
          [(x.get("rel"), x.get("have"), x.get("whole"), "rows" in x) for x in j],
          [("out/w001/p000000.raw.zz", 400, 1000, False)])
    rc, out, c, _ = fetch(h, srv, fp, idle=1)
    check("F1 pass 2: exit 0; the member resumes at byte 400 and receives 600; the offer placed LAST without a byte "
          "again; nothing sent again", (rc, c), (0, want(of=1, mf=1, mb=600)))
    check("F1 the member under its final name is the server's 1,000 bytes; the partial is gone",
          (wire(h).get("out/w001/p000000.raw.zz") == sha(RAW), part.exists(), len(wire(h))), (True, False, 4))

    srv, fp, files = syn("syn_f2")
    plan(srv, {"get out/w001/p000000.raw.zz": [{"chunks": [[400, 0]], "hang_s": 3}]})
    h = WORK / "F2"
    fetch(h, srv, fp, idle=1)
    part = h / "fetch" / "part" / fp / "out" / "w001" / "p000000.raw.zz"
    b = bytearray(part.read_bytes())
    b[100] ^= 0x55
    part.write_bytes(bytes(b))
    rc, out, c, _ = fetch(h, srv, fp, idle=1)
    check("F2 a corrupt 400-byte prefix: the resume brings 600, the hash fails, the member comes again from byte zero: "
          "member traffic 400 + 600 + 1,000, of which 1,000 sent again", (rc, c),
          (0, want(of=1, mf=1, mb=600, again=1000)))
    check("F2 only the good copy reached wire/; the journal names the discard",
          (wire(h).get("out/w001/p000000.raw.zz") == sha(RAW), len(wire(h)),
           [x.get("rel") for x in journal(h) if x.get("t") == "discarded"]),
          (True, 4, ["out/w001/p000000.raw.zz"]))

    srv, fp, files = syn("syn_f14")
    h = WORK / "F14"
    alien = h / "fetch" / "part" / sha(b"another run") / "out" / "w001" / "p000000.raw.zz"
    put(alien, bytes(400))
    rc, out, c, _ = fetch(h, srv, fp)
    check("F14 another run's 400-byte partial is never resumed: the member comes whole (1,000), nothing sent again; "
          "the other partial untouched", (rc, c["mb"] if c else None, c["again"] if c else None,
                                          wire(h).get("out/w001/p000000.raw.zz") == sha(RAW), alien.read_bytes()),
          (0, len(files["p000000.seal.json.zz"]) + 1000, 0, True, bytes(400)))

    srv, fp, files = syn("syn_f1b")
    plan(srv, {"get out/w001/p000000.raw.zz": [{"chunks": [[400, 0]], "hang_s": 3}]})
    h = WORK / "F1b"
    fetch(h, srv, fp, idle=1, window=300)
    rc, out, c, _ = fetch(h, srv, fp, idle=1, window=300)
    check("F1 with an in-flight window of 300 bytes: the resume steps back to byte 100: 900 received, 600 of them new, "
          "300 sent again", (rc, c["mb"] if c else None, c["again"] if c else None,
                             wire(h).get("out/w001/p000000.raw.zz") == sha(RAW)), (0, 600, 300, True))


def case_idle():
    """F6 and F7: a test-only idle bound of 5 s."""
    srv, fp, files = syn("syn_f6a")
    plan(srv, {"get out/w001/p000000.raw.zz": [{"chunks": [[1, 3.0], [1, 0]], "rest": True}]})
    h = WORK / "F6a"
    rc, out, c, secs = fetch(h, srv, fp, idle=5)
    check("F6 two bytes 3 s apart: the transfer stays live and completes (no partial; at least 3 s)",
          (rc, c["partial"] if c else None, wire(h).get("out/w001/p000000.raw.zz") == sha(RAW), secs >= 3),
          (0, 0, True, True))
    srv, fp, files = syn("syn_f6b")
    plan(srv, {"get out/w001/p000000.raw.zz": [{"chunks": [[400, 0]], "hang_s": 6.0}]})
    h = WORK / "F6b"
    rc, out, c, secs = fetch(h, srv, fp, idle=5)
    j = [x for x in journal(h) if x.get("t") == "partial"]
    s = j[0].get("silent_ms") if j else None
    check("F6 a sender silent for 6 s after its last byte is cut while still open, 5 to 6 s after that byte",
          (rc, len(j), j[0].get("why") if j else None, s is not None and 5000 < s <= 6000),
          (0, 1, "idle longer than 5 s", True))
    check("F7 that cut: 400 partial bytes of 1,000 whole, no rows field",
          (j[0].get("have"), j[0].get("whole"), "rows" in j[0]) if j else None, (400, 1000, False))


def case_refused():
    """F9 and F11: a plain wire name, and member names outside the allowed tree, refused before they are paths."""
    def seal_plain(o):
        o["members"][0]["wire_name"] = "p000000.seal.json"

    srv, fp, files = syn("syn_f9", fix=seal_plain, plain=True)
    h = WORK / "F9"
    rc, out, c, _ = fetch(h, srv, fp)
    check("F9 an offer whose seal's wire name is plain is refused whole; the plain names on the server are ignored",
          (rc, c, sorted(wire(h))),
          (0, want(cf=1, cb=len(files["RUN.json.zz"]), ob=len(files["p000000.offer.json.zz"]), refused=1, ignored=2),
           ["RUN.json.zz"]))
    rc, out, c, _ = fetch(h, srv, fp)
    check("F9 the refused offer is not fetched again at the same length", (rc, c), (0, want(ignored=2)))
    for tag, bad in (("dots", "../x"), ("slash", "a/b"), ("backslash", "p000000\\raw.zz"), ("index", "p000001.raw.zz")):
        def fix(o, bad=bad):
            o["members"][1]["name"] = o["members"][1]["wire_name"] = bad
        srv, fp, files = syn(f"syn_f11_{tag}", fix=fix)
        h = WORK / f"F11_{tag}"
        rc, out, c, _ = fetch(h, srv, fp)
        made = sorted(p.relative_to(WORK).as_posix() for p in WORK.rglob("*") if p.is_file()     # what the 4 names
                      and p.name in ("x", "b", "raw.zz", "p000001.raw.zz")) + \
            sorted(p.name for p in (h / "fetch" / "part").rglob("*") if p.is_file())             # would have made
        check(f"F11 a member named {bad!r}: the offer refused whole before the name is a path; wire/ the header only; "
              "no file made from the name", (rc, c["refused"] if c else None, sorted(wire(h)), made),
              (0, 1, ["RUN.json.zz"], []))


def case_incomplete():
    """F10: an offer whose member is missing or short on the server is not linked; it completes on a later pass."""
    for tag in ("missing", "short"):
        srv, fp, files = syn(f"syn_f10_{tag}")
        raw = srv / "out" / "w001" / "p000000.raw.zz"
        if tag == "missing":
            raw.unlink()
        else:
            put(raw, RAW[:999])
        h = WORK / f"F10_{tag}"
        rc, out, c, _ = fetch(h, srv, fp)
        check(f"F10 the raw member {tag} on the server: exit 0, incomplete 1, no member fetched, the offer not linked",
              (rc, c, sorted(wire(h))),
              (0, want(cf=1, cb=len(files["RUN.json.zz"]), ob=len(files["p000000.offer.json.zz"]), incomplete=1),
               ["RUN.json.zz"]))
        put(raw, RAW)
        rc, out, c, _ = fetch(h, srv, fp)
        check(f"F10 ({tag}) once the member is there: the next pass fetches the members, the offer from its part "
              "without a byte again, and links it last",
              (rc, c, sorted(wire(h))),
              (0, want(of=1, mf=2, mb=len(files["p000000.seal.json.zz"]) + 1000),
               ["RUN.json.zz", "out/w001/p000000.offer.json.zz", "out/w001/p000000.raw.zz",
                "out/w001/p000000.seal.json.zz"]))


def case_budget():
    """F12: --budget-bytes binds before the transfer that would pass it."""
    srv, fp, files = syn("syn_f12")
    h = WORK / "F12"
    budget = len(files["RUN.json.zz"]) + len(files["p000000.offer.json.zz"]) + len(files["p000000.seal.json.zz"]) + 999
    rc, out, c, _ = fetch(h, srv, fp, "--budget-bytes", str(budget))
    part = h / "fetch" / "part" / fp / "out" / "w001" / "p000000.raw.zz"
    check("F12 a budget 1 byte short of the 1,000-byte member: exit 0, budget binds, the member not started",
          (rc, c["binds"] if c else None, c["mb"] if c else None, part.exists(), sorted(wire(h))),
          (0, "yes", len(files["p000000.seal.json.zz"]), False, ["RUN.json.zz", "out/w001/p000000.seal.json.zz"]))
    rc, out, c, _ = fetch(h, srv, fp)
    check("F12 the next pass without a budget completes it", (rc, c["binds"] if c else None,
                                                             wire(h).get("out/w001/p000000.raw.zz") == sha(RAW)),
          (0, "no", True))


def case_confirm():
    """F3, F4: seeing again confirms nothing; an explicit confirmation repairs and custody confirms."""
    h = WORK / "F3"
    shutil.copytree(STATE["H"], h)
    meta = h / "wire" / "out" / "w001" / "p000001.meta.xz"
    b = bytearray(meta.read_bytes())
    b[5] ^= 1
    flipped = bytes(b)
    put(meta, flipped)
    before = receipts(h)
    results = [fetch(h, SRV, FP["fp"]) for _ in range(100)]
    check("F3 100 passes over receipted offers: every one exit 0 with every count 0 (ignored 9)",
          sorted({(r[0], json.dumps(r[2], sort_keys=True)) for r in results}),
          [(0, json.dumps(want(ignored=9), sort_keys=True))])
    rc, out, cc = custody(h)
    check("F3 the changed member was not noticed and nothing new was receipted", (meta.read_bytes() == flipped,
                                                                                 rc, cc[4] if cc else None,
                                                                                 receipts(h) == before), (True, 0, 0, True))
    rc, out, c, _ = fetch(h, SRV, FP["fp"], "--confirm", "w001/p000001")
    good = (SRV / "out" / "w001" / "p000001.meta.xz").read_bytes()
    aside = meta.with_name(f"p000001.meta.xz.damaged.{sha(flipped)[:12]}")
    check("F4 --confirm w001/p000001: exit 0, confirmations 1, the member fetched again (all of it sent again), the "
          "changed copy kept aside under a new name", (rc, c, meta.read_bytes() == good, aside.read_bytes() == flipped),
          (0, want(conf=1, again=len(good)), True, True))
    rc, out, cc = custody(h, "--confirm", "w001/p000001")
    check("F4 custody --confirm then says CONFIRMED; the receipts unchanged",
          (rc, "CONFIRMED w001/p000001" in out, receipts(h) == before), (0, True, True))
    binp = h / "wire" / "out" / "w001" / "p000002.binpack"
    binp.unlink()
    rc, out, c, _ = fetch(h, SRV, FP["fp"], "--confirm", "w001/p000002")
    rc2, out2, cc = custody(h, "--confirm", "w001/p000002")
    check("F4 a kept member removed: --confirm fetches it again, custody CONFIRMED, still 3 receipts",
          (rc, c["conf"] if c else None, binp.read_bytes() == (SRV / "out" / "w001" / "p000002.binpack").read_bytes(),
           rc2, "CONFIRMED w001/p000002" in out2, len(receipts(h))), (0, 1, True, 0, True, 3))
    gone = WORK / "srv_gone"
    shutil.copytree(SRV, gone)
    (gone / "out" / "w001" / "p000000.binpack").unlink()
    (h / "wire" / "out" / "w001" / "p000000.binpack").unlink()
    rc, out, c, _ = fetch(h, gone, FP["fp"], "--confirm", "w001/p000000")
    check("F4 a removed member that the server no longer has: exit 5, the journal names it",
          (rc, any(x.get("t") == "confirm" and "p000000.binpack" in x.get("why", "") for x in journal(h))), (5, True))


def case_fork():
    """F5: a receipted offer listed at another length: kept once beside, nothing replaced."""
    h = WORK / "F5"
    shutil.copytree(STATE["H"], h)
    srv = WORK / "srv_fork"
    shutil.copytree(SRV, srv)
    o = srv / "out" / "w001" / "p000000.offer.json.zz"
    new = zlib.compress(zlib.decompress(o.read_bytes()), 0)
    put(o, new)
    kept = (h / "wire" / "out" / "w001" / "p000000.offer.json.zz").read_bytes()
    rc, out, c, _ = fetch(h, srv, FP["fp"])
    side = h / "wire" / "out" / "w001" / f"p000000.offer.json.zz.conflict.{sha(new)[:12]}"
    check("F5 the listed length changed: exit 0, forks 1, the new bytes beside the receipted offer, which is untouched",
          (rc, c["forks"] if c else None, side.exists() and side.read_bytes() == new,
           (h / "wire" / "out" / "w001" / "p000000.offer.json.zz").read_bytes() == kept,
           [x.get("new") for x in journal(h) if x.get("t") == "fork"]),
          (0, 1, True, True, [side.name]))
    rc, out, c, _ = fetch(h, srv, FP["fp"])
    rc2, out2, cc = custody(h)
    check("F5 a second pass keeps it once (forks 0); custody never reads the .conflict name (no new receipt)",
          (rc, c["forks"] if c else None, rc2, cc[4] if cc else None), (0, 0, 0, 0))


def case_hostkey():
    """F8: the pinned host key and a refused login STOP (6) without a retry; an unreachable server is 7."""
    for tag, say, code in (("key", "Host key verification failed.", 6),
                           ("changed", "@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @", 6),
                           ("login", "tester@example.invalid: Permission denied (publickey).", 6),
                           ("refused", "ssh: connect to host example.invalid port 2222: Connection refused", 7)):
        srv, fp, files = syn(f"syn_f8_{tag}")
        plan(srv, {"list ": [{"say": say, "exit": 255}, {}]})   # a retry would take the second, a good listing
        h = WORK / f"F8_{tag}"
        rc, out, c, _ = fetch(h, srv, fp)
        j = journal(h)
        check(f"F8 the first listing fails ({tag}): exit {code}, no retry in the pass, nothing placed, the journal's "
              "last line the stop", (rc, plan_left(srv), wire(h), j[-1].get("code") if j else None),
              (code, {"list ": [{}]}, {}, code))
    ssh = Path("C:/Windows/System32/OpenSSH/ssh.exe")
    sys.path.insert(0, str(CP / "home"))
    import fetch as F  # noqa: E402
    pinned, empty = WORK / "pinned_known", WORK / "ssh_empty"
    pinned.write_text("[example.invalid]:2222 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeKeyForATestOnly000000000000000\n",
                      encoding="ascii")
    empty.write_bytes(b"")
    opts = F.Transport.ssh_options({"known_hosts": str(pinned), "identity": str(WORK / "no_key")}, empty)
    p = subprocess.run([str(ssh), "-G", *opts, "-p", "2222", "-l", "tester", "example.invalid"], capture_output=True,
                       text=True, timeout=60)
    g = dict(ln.split(" ", 1) for ln in p.stdout.lower().splitlines() if " " in ln)
    norm = lambda s: s.replace("\\", "/").lower()  # noqa: E731
    check("F8 ssh -G with the fetch's options: batchmode yes, stricthostkeychecking true, updatehostkeys false, "
          "identitiesonly yes, the pinned file and the empty global file; NF-18: connecttimeout 15, serveraliveinterval 15, "
          "serveralivecountmax 3",
          (p.returncode, g.get("batchmode"), g.get("stricthostkeychecking"), g.get("updatehostkeys"),
           g.get("identitiesonly"), norm(g.get("userknownhostsfile", "")), norm(g.get("globalknownhostsfile", "")),
           g.get("connecttimeout"), g.get("serveraliveinterval"), g.get("serveralivecountmax")),
          (0, "yes", "true", "false", "yes", norm(str(pinned)), norm(str(empty)), "15", "15", "3"))


def case_lock():
    """F18: one fetch at a time on a home folder (an OS lock on home/fetch/LOCK, held here by the test's process)."""
    srv, fp, files = syn("syn_f18")
    h = WORK / "F18"
    (h / "fetch").mkdir(parents=True)
    held = W.SlotLock(h / "fetch")
    try:
        rc, out, c, _ = fetch(h, srv, fp)
        last = out.splitlines()[-1] if out else ""
        check("F18 while another process holds home/fetch/LOCK: exit 8 at once, the last line names the lock; wire/, "
              "fetch/part/ and the journal unchanged (only the lock file under fetch/)",
              (rc, "LOCK" in last, wire(h), sorted(p.relative_to(h).as_posix() for p in h.rglob("*") if p.is_file())),
              (8, True, {}, ["fetch/LOCK"]))
    finally:
        held.release()
    rc, out, c, _ = fetch(h, srv, fp)
    check("F18 after the release the same call runs its pass", (rc, wire(h).get("out/w001/p000000.raw.zz") == sha(RAW)),
          (0, True))


def case_slow():
    """F19: NF-18's outer bound per transfer (transfer_s), apart from the idle cut."""
    srv, fp, files = syn("syn_f19")
    plan(srv, {"get out/w001/p000000.raw.zz": [{"chunks": [[1, 1.0]] * 20}]})
    h = WORK / "F19"
    rc, out, c, secs = fetch(h, srv, fp, idle=2, cap=3)
    j = [x for x in journal(h) if x.get("t") == "partial"]
    check("F19 one byte a second with transfer_s 3 and idle_s 2: exit 0, one partial of 3 or 4 bytes of 1,000, why "
          "\"longer than 3 s\", silent under 2 s (not the idle cut)",
          (rc, len(j), j[0].get("have") in (3, 4) if j else None, j[0].get("whole") if j else None,
           j[0].get("why") if j else None, (j[0].get("silent_ms") or 0) < 2000 if j else None),
          (0, 1, True, 1000, "longer than 3 s", True))
    plan(srv, {})
    rc, out, c, _ = fetch(h, srv, fp, idle=2, cap=3)
    check("F19 the next pass completes the member", (rc, wire(h).get("out/w001/p000000.raw.zz") == sha(RAW)), (0, True))


def case_real_sftp():
    """F20, F21: the sftp branch with the REAL client (hunt 0900, target 86); only the command line is replaced."""
    sftp = Path("C:/Windows/System32/OpenSSH/sftp.exe")
    server = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git" / "usr" / "lib" / "ssh" / "sftp-server.exe"
    if not (sftp.is_file() and server.is_file()):
        check("F20 and F21 need the real client and server", (sftp.is_file(), server.is_file()), (True, True))
        return
    sys.path.insert(0, str(CP / "home"))
    import fetch as F  # noqa: E402
    srv = WORK / "real_srv"
    w = srv / "run" / "w001"
    (w / "sub").mkdir(parents=True)
    data = bytes((i * 7 + 3) % 251 for i in range(1000))
    (w / "p000001.raw.zz").write_bytes(data)
    (w / "junk p000002.raw.zz").write_bytes(b"\0" * 99)
    (w / "p000004.raw.zz").write_bytes(b"\0" * 640)
    (w / "p000005.raw.zz").write_bytes(b"\0" * 12)
    old = time.time() - 400 * 86400                    # older than half a year: the client prints the year form
    os.utime(w / "p000004.raw.zz", (old, old))
    d = datetime.date.today()
    d4 = d.replace(day=4) if d.day > 4 else (d.replace(day=1) - datetime.timedelta(days=1)).replace(day=4)
    t4 = time.mktime(d4.timetuple()) + 8 * 3600        # a recent one-digit day: "Nov  4 08:00"
    os.utime(w / "p000005.raw.zz", (t4, t4))
    batch = WORK / "real_batch.txt"

    def transport(root: Path):
        t = F.Transport.__new__(F.Transport)
        s = root.as_posix()
        t.kind, t.idle, t.cap, t.root = "sftp", 30, 120, "/" + s[0].lower() + s[2:]   # Git's server reads /c/...
        t.batch, t.log = batch, WORK / "real_child.out"
        t.cmd = [str(sftp), "-b", str(batch), "-D", f'"{server}"']
        return t

    def get(name: str, part: Path):
        res = transport(srv / "run").get(f"w001/{name}", part, 1000)[0]
        return batch.read_text(encoding="ascii").split(" ", 1)[0], res, part.read_bytes() if part.exists() else b""

    listed = transport(srv / "run").list("w001")[0]
    check("F20a the real client lists a slot: the three members, not 'junk p000002.raw.zz' as p000002.raw.zz, not the "
          "folder; the line begins '-ls -ln \"'", (listed, batch.read_text(encoding="ascii").startswith('-ls -ln "')),
          ({"p000001.raw.zz": 1000, "p000004.raw.zz": 640, "p000005.raw.zz": 12}, True))
    op, res, got = get("p000001.raw.zz", WORK / "real_g1.part")
    check("F20b get into an empty partial: 'get', result 0, the member", (op, res, got == data), ("get", 0, True))
    (WORK / "real_g2.part").write_bytes(data[:400])
    op, res, got = get("p000001.raw.zz", WORK / "real_g2.part")
    check("F20c the first 400 bytes: 'reget', result 0, the member", (op, res, got == data), ("reget", 0, True))
    (WORK / "real_g3.part").write_bytes(b"\xff" * 400)
    op, res, got = get("p000001.raw.zz", WORK / "real_g3.part")
    check("F20d 400 wrong bytes: 'reget', result 0, 1,000 bytes that are not the member", (op, res, len(got), got == data),
          ("reget", 0, 1000, False))
    op, res, got = get("p000009.raw.zz", WORK / "real_g4.part")
    check("F20e a member not on the server: result not 0, no bytes", (res != 0, len(got)), (True, 0))
    try:
        transport(srv / "gone").list("")
        got = "listed with exit 0"
    except F.Stop as e:
        got = (e.code, "not found" in str(e))
    check("F21 a root that does not exist: Stop 7 naming 'not found'; the line begins 'ls -ln \"' (no '-')",
          (got, batch.read_text(encoding="ascii").startswith('ls -ln "')), ((7, True), True))
    try:
        got = transport(srv / "run").list("w002")[0]
    except F.Stop as e:
        got = (e.code, str(e)[:80])
    check("F21 the control: a missing slot under an existing root lists {}", got, {})


def main() -> int:
    t0 = time.time()
    STATE["ok"] = False
    try:
        STATE["ok"] = server()
    except Exception:  # noqa: BLE001
        print(f"FAIL the server fixture crashed:\n{traceback.format_exc()}")
        RESULTS.append(("server fixture crashed", False))
    if STATE["ok"]:
        for fn in (case_full, case_header, case_resume, case_idle, case_refused, case_incomplete, case_budget,
                   case_confirm, case_fork, case_hostkey, case_lock, case_slow, case_real_sftp):
            safe(fn)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)} of {len(RESULTS)} checks pass ({time.time() - t0:.0f} s)"
          + (f"; PLANT {PLANT}" if PLANT else ""))
    return 0 if not bad and RESULTS else 1


if __name__ == "__main__":
    sys.exit(main())

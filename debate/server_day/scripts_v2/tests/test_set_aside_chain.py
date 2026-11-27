"""test_set_aside_chain.py: RC1 (Fable's remark on v17): the REAL home/content.py writes a verdict with a set_aside
game, and the REAL home/credit.py reads that verdict. KNOWN ANSWERS written BEFORE this file and before any run:
tmp/fable_scratch/v17_rc1/KNOWN_ANSWERS_rc1_by_fable.md (Fable, 26 Nov 14:56, sha256 4119e8dab218...). The test was
written by Opus on 26 Nov from those answers and from test_content.py's and test_credit.py's own parts. Runs under a
Python with python-chess 1.11.2 (the lab's venv).

    test_set_aside_chain.py <home/content.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantA|plantB]

The tree above home/ (home/, run/, workloads/, known/) is copied; plantA changes the copy's content.py, plantB the
copy's credit.py. 15 checks:
R1, R2  the server, from the day's REAL programs: run "rc1", slot 1, piece_games 2, the list rule with N12's six
        openings, ONE pilot range (round 1, ids 1 to 4); the worker plays four games and ends by the fence; the packer
        runs WITHOUT a converter (two raw offers).
F1, F2  the forge's own controls (no home involved).
C1-C3   the PLAIN home (nothing changed): a1, a2, credit.
S1-S8   the FORGED home: before a1, in p1's raw piece, the record of id 4, row 0's position gets the last digit of its
        halfmove clock raised by one (9 becomes 0); the record's bind line made again with record.text; p1's seal
        (raw_sha256, raw_bytes, ids_digest), the offer and the range seal's through_seal fitted. Nothing else differs.
plantA  content.py sets nothing aside: S2 to S8 FAIL (7).  plantB  credit.py reads set_aside as noselfgame: S6 to S8
        FAIL (3). A plant whose old text is not there exactly once: exit 2, nothing run.
What RC1 does NOT prove: only ONE of check_game's refusals is carried through (a position that is not the board's);
no round of several slots; no piece that is not the range's last; a wire changed WITHOUT the bind, seal and range
seal fitted is refused earlier (test_content's P8a to P8d), not set aside.
"""
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import traceback
import zlib
from pathlib import Path

if len(sys.argv) < 6:
    print("usage: test_set_aside_chain.py <home/content.py> <engine exe> <net file> <converter exe> <a NEW folder> "
          "[plantA|plantB]")
    sys.exit(2)
SRC = Path(sys.argv[1]).resolve()
EXE, NET, CONV, WORK = (Path(a).resolve() for a in sys.argv[2:6])
PLANT = sys.argv[6] if len(sys.argv) > 6 else None
TREE = SRC.parent.parent
PLANTS = {   # KA-6: (the file under home/, its old text, the new text)
    "plantA": ("content.py", 'st, why = "set_aside", str(e)', 'st, why = "accepted", None'),
    "plantB": ("credit.py", 'e["state"] = g["state"]', 'e["state"] = "noselfgame"'),
}
if PLANT and PLANT not in PLANTS:
    print(f"STOP: no plant {PLANT}")
    sys.exit(2)
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
CP = WORK / "tree"
for sub in ("home", "run", "workloads", "known"):
    shutil.copytree(TREE / sub, CP / sub, ignore=shutil.ignore_patterns("__pycache__"))
if PLANT:
    fname, old, new = PLANTS[PLANT]
    text = (CP / "home" / fname).read_text(encoding="ascii")
    if text.count(old) != 1:
        print(f"STOP: {PLANT}: its old text is not there exactly once in home/{fname}")
        sys.exit(2)
    (CP / "home" / fname).write_text(text.replace(old, new), encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy's {fname}")
RUN, CUST, CONT, CRED = CP / "run", CP / "home" / "custody.py", CP / "home" / "content.py", CP / "home" / "credit.py"
sys.path.insert(0, str(RUN))
sys.path.insert(0, str(CP / "home"))
import content as C  # noqa: E402
import record as R  # noqa: E402
import worker as W  # noqa: E402

if C.chess is None or getattr(C.chess, "__version__", "") != "1.11.2":
    print("STOP: this test needs python-chess 1.11.2 (the lab's venv)")
    sys.exit(2)
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
NOW = time.time()
SRV = WORK / "srv"
FP = {}
STATE = {}
CUST_COUNTS = re.compile(r"custody: RECEIVED (\d+) pieces (\d+) rows; C1 (\d+) pieces")
COUNTS = re.compile(r"content: judged (\d+) pieces \((\d+) refused\); accepted (\d+) games (\d+) rows; "
                    r"noselfgame (\d+); set_aside (\d+); waits (\d+); conflicts (\d+)")
LAST = re.compile(r"credit: decided (\d+) rounds \((\d+) complete, (\d+) partial\) this pass; credited (\d+) games "
                  r"(\d+) rows; waits: (.*); holds (\d)")
WHY = "the position of row 0 is not the board's"
FORGED_COUNTS = (2, 0, 3, 104, 0, 1, 0, 0)


def gid(c: int) -> str:
    return f"rc1-w001-g{c:08d}"


# ---- the server (KA-1) ----------------------------------------------------------------------------------------------
def server() -> bool:
    put(SRV / "RUN.json", W.canon({
        "schema": 2, "run": "rc1", "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
        "hard_cutoff_utc": T(NOW + 86400), "boot_id": W.boot_id(), "instance": "test-instance", "package": "0" * 64,
        "engine_sha256": sha(EXE.read_bytes()), "net_sha256": MAN["net_sha256"],
        "options_sha256": sha("".join(ln + "\n" for ln in MAN["options"]).encode("ascii")),
        "game_line": MAN["selfgame_line"], "opening_rule": {"kind": "list", "sha256": sha(OPENINGS.read_bytes()),
                                                             "count": len(N12)},
        "slots": [1], "piece_games": 2, "pilot_ranges": [{"slot": 1, "round": 1, "first": 1, "last": 4,
                                                           "short": False, "schedule": 0}]}))
    FP["fp"] = fp = sha((SRV / "RUN.json").read_bytes())
    hdr = json.loads((SRV / "RUN.json").read_bytes())
    cmd = [sys.executable, "-I", "-B", str(RUN / "worker.py"), "--root", str(SRV), "--slot", "1", "--exe", str(EXE),
           "--net", str(NET), "--manifest", str(MAN_PATH), "--known-startup", str(KNOWN), "--openings", str(OPENINGS)]
    log = WORK / "srv.out"
    with open(log, "wb") as f:
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        end = time.time() + 600
        while not (SRV / "ranges" / "r0001.w001.seal.json").exists() and p.poll() is None and time.time() < end:
            time.sleep(0.5)
        put(SRV / "FENCE.json", W.canon({"at_utc": T(time.time()), "cutoff_utc": hdr["hard_cutoff_utc"],
                                         "run_fingerprint": fp, "schema": 2, "why": "D"}))
        try:
            p.wait(timeout=120)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
    closed = SRV / "w001" / "closed"
    seals = [json.loads((closed / f"p{i:06d}.seal.json").read_bytes()) for i in range(3)
             if (closed / f"p{i:06d}.seal.json").exists()]
    rows = {g["counter"]: len(g["rows"]) for i in range(len(seals))
            for g in R.parse((closed / f"p{i:06d}.raw").read_bytes(), fp)}
    if not check("R1 server: exit 0; two pieces of 104 and 112 rows, both round 1; ids 1 to 4 with 28, 76, 0, 112 rows "
                 "(a PREDICTION from test_content's run); the range seal r0001.w001",
                 (p.returncode, [s["rows"] for s in seals], [s["round"] for s in seals], rows,
                  sorted(x.name for x in (SRV / "ranges").glob("*.json"))),
                 (0, [104, 112], [1, 1], {1: 28, 2: 76, 3: 0, 4: 112}, ["r0001.w001.seal.json"])):
        print(log.read_text(encoding="utf-8", errors="replace")[-600:])
        return False
    rc = subprocess.run([sys.executable, "-I", "-B", str(RUN / "packer.py"), "--root", str(SRV), "--converter",
                         str(WORK / "no_converter.exe"), "--once"], capture_output=True, text=True, timeout=600).returncode
    forms = [json.loads((SRV / "out" / "w001" / f"p{i:06d}.offer.json").read_bytes())["form"] for i in range(3)
             if (SRV / "out" / "w001" / f"p{i:06d}.offer.json").exists()]
    return check("R2 the packer without a converter: exit 0, two raw offers", (rc, forms), (0, ["raw", "raw"]))


# ---- the homes ------------------------------------------------------------------------------------------------------
def fetch(home: Path) -> None:
    for p in sorted(SRV.glob("*.zz")):
        put(home / "wire" / p.name, p.read_bytes())
    for p in sorted((SRV / "ranges").glob("*.zz")):
        put(home / "wire" / "ranges" / p.name, p.read_bytes())
    src, dst = SRV / "out" / "w001", home / "wire" / "out" / "w001"
    for i in range(2):
        o = json.loads(zlib.decompress((src / f"p{i:06d}.offer.json.zz").read_bytes()))
        for m in o["members"]:
            put(dst / m["wire_name"], (src / m["wire_name"]).read_bytes())
        put(dst / f"p{i:06d}.offer.json.zz", (src / f"p{i:06d}.offer.json.zz").read_bytes())   # LAST, as a fetch does


def custody(home: Path) -> tuple:
    p = subprocess.run([sys.executable, "-I", "-B", str(CUST), "--home", str(home), "--fingerprint", FP["fp"]],
                       capture_output=True, text=True, timeout=300)
    m = CUST_COUNTS.search(p.stdout)
    return p.returncode, (m[1] if m else None)


def content(home: Path) -> tuple:
    """(exit code, the lines before the last, the last line's counts or None, the whole output)."""
    p = subprocess.run([sys.executable, "-I", "-B", str(CONT), "--home", str(home), "--fingerprint", FP["fp"],
                        "--converter", str(CONV), "--openings", str(OPENINGS)], capture_output=True, text=True,
                       timeout=900)
    out = (p.stdout + p.stderr).strip()
    lines = out.splitlines()
    m = COUNTS.fullmatch(lines[-1]) if lines else None
    return p.returncode, lines[:-1], (tuple(int(x) for x in m.groups()) if m else None), out


def credit(h: Path) -> tuple:
    p = subprocess.run([sys.executable, "-I", "-B", str(CRED), "--home", str(h), "--fingerprint", FP["fp"]],
                       capture_output=True, text=True, timeout=600)
    out = (p.stdout + p.stderr).strip()
    m = LAST.fullmatch(out.splitlines()[-1]) if out else None
    return p.returncode, out, (m.groups() if m else None)


def decided(h: Path) -> dict:
    d = h / "stage"
    return {p.parent.name: p.read_bytes() for p in sorted(d.glob("r*/credit.json"))} if d.is_dir() else {}


def verdicts(home: Path) -> dict:
    d = home / "content" / "w001"
    return {p.name: p.read_bytes() for p in sorted(d.glob("*.verdict.json"))} if d.is_dir() else {}


def index_rows(home: Path) -> list:
    p = home / "content" / "equal.sqlite"
    if not p.exists():
        return []
    con = sqlite3.connect(p)
    try:
        return [tuple(r) for r in con.execute("SELECT slot, counter, round, game, piece, state, rows_digest, bind "
                                              "FROM entries ORDER BY slot, counter")]
    finally:
        con.close()


def server_games() -> list:
    """(piece index, parsed record) of the SERVER's own raw pieces: the source of every known answer below."""
    return [(i, g) for i in range(2)
            for g in R.parse((SRV / "w001" / "closed" / f"p{i:06d}.raw").read_bytes(), FP["fp"])]


def raw_games() -> dict:
    return {g["counter"]: (len(g["rows"]), R.rows_digest(g["rows"], g["end"])) for _i, g in server_games()}


def rseal(h: Path) -> Path:
    return h / "wire" / "ranges" / "r0001.w001.seal.json.zz"


def zz_rewrite(path: Path, fn) -> None:
    put(path, zlib.compress(W.canon(fn(json.loads(zlib.decompress(path.read_bytes())))), 6))


def entry(c: int, state: str, games: dict) -> dict:
    rows, dg = games[c]
    return {"counter": c, "game": gid(c), "rows": rows, "rows_digest": dg, "same_rows_as": None, "slot": 1,
            "state": state}


def want_list(h: Path, ids: list, status: str, **over) -> bytes:
    s = json.loads(zlib.decompress(rseal(h).read_bytes()))
    c = {"schema": 2, "run_fingerprint": FP["fp"], "round": 1, "status": status,
         "range_seals": [{"slot": 1, "sha256": sha(zlib.decompress(rseal(h).read_bytes()))}],
         "games_in": s["games"], "raw_rows_in": s["rows"], "ids": ids, "missing_ids": [], "set_aside_ids": [],
         "conflict_ids": [], "repeat_games": sum(e["state"] == "repeat" for e in ids)}
    c.update(over)
    return W.canon(c)


# ---- the cases ------------------------------------------------------------------------------------------------------
def case_plain():
    """KA-3: the PLAIN home, nothing changed (the control)."""
    h = WORK / "plain"
    fetch(h)
    a1 = custody(h)
    rc, other, counts, out = content(h)
    if not check("C1 PLAIN: a1 exit 0, RECEIVED 2 pieces; a2 exit 0, counts (2 pieces, 0 refused, accepted 4 games, "
                 "216 rows, noselfgame 0, set_aside 0, waits 0, conflicts 0), no other line",
                 (a1, rc, other, counts), ((0, "2"), 0, [], (2, 0, 4, 216, 0, 0, 0, 0))):
        print(out[-800:])
    STATE["p0"] = verdicts(h).get("p000000.verdict.json")
    g = raw_games()
    rc, out, m = credit(h)
    check("C2 PLAIN credit: exit 0, decided 1 rounds (1 complete, 0 partial); credited 4 games 216 rows; waits: none; "
          "holds 0", (rc, m), (0, ("1", "1", "0", "4", "216", "none", "0")))
    check("C3 PLAIN stage/r0001/credit.json byte for byte: complete, ids 1 to 4 credited (id 3 rows 0, digest null)",
          decided(h), {"r0001": want_list(h, [entry(c, "credited", g) for c in range(1, 5)], "complete")})


def forge(h: Path) -> bytes:
    """KA's FORGED home, before a1 (F1 and F2 checked here); returns the forged p1 seal's bytes."""
    fp, d = FP["fp"], h / "wire" / "out" / "w001"
    srv_raw = (SRV / "w001" / "closed" / "p000001.raw").read_bytes()
    raw = zlib.decompress((d / "p000001.raw.zz").read_bytes())
    games = R.parse(raw, fp)
    check("F1 every record of the server's p1, written again with record.text from record.parse's parts, gives the "
          "server's bytes exactly",
          "".join(R.text(fp, g["id"], g["opening"], g["sent"], g["rows"], g["end"]) for g in games).encode("ascii")
          == srv_raw, True)
    recs = []
    for g in games:
        rows = list(g["rows"])
        if g["counter"] == 4:
            t = rows[0].split(" ")
            t[-2] = t[-2][:-1] + str((int(t[-2][-1]) + 1) % 10)        # the position's halfmove clock, its last digit
            rows[0] = " ".join(t)
        recs.append(R.text(fp, g["id"], g["opening"], g["sent"], rows, g["end"]))
    raw2 = "".join(recs).encode("ascii")
    g4 = [g for g in R.parse(srv_raw, fp) if g["counter"] == 4][0]
    at = srv_raw[:g4["first"]].count(b"\n")                            # the line of id 4's game line
    a, b = srv_raw.split(b"\n"), raw2.split(b"\n")
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y] if len(a) == len(b) else None
    check("F2 the forged piece: the same length; exactly 2 lines differ (row 0 of id 4 and id 4's bind line); it "
          "parses under the run's fingerprint: 2 games, 0 and 112 rows",
          (len(raw2) == len(srv_raw), diff, [len(x["rows"]) for x in R.parse(raw2, fp)]),
          (True, [at + 2, at + 3 + len(g4["rows"])], [0, 112]))
    zz = zlib.compress(raw2, 6)                                        # test_content's raw_forge
    put(d / "p000001.raw.zz", zz)

    def fix_raw(o):
        assert o["members"][1]["name"] == "p000001.raw.zz"
        o["members"][1].update(bytes=len(zz), sha256=sha(zz), wire_bytes=len(zz), wire_sha256=sha(zz))
        return o
    zz_rewrite(d / "p000001.offer.json.zz", fix_raw)
    ids = hashlib.sha256()                                             # content.py's ids digest (the bind is in it)
    for g in R.parse(raw2, fp):
        ids.update(f"{g['id']}\n{'noselfgame' if g['end'].startswith('openingend ') else 'done'}\n{g['bind']}\n"
                   .encode("ascii"))
    s = json.loads(zlib.decompress((d / "p000001.seal.json.zz").read_bytes()))
    s.update(raw_sha256=sha(raw2), raw_bytes=len(raw2), ids_digest=ids.hexdigest())
    sb = W.canon(s)
    szz = zlib.compress(sb, 6)                                         # test_content's reforge (p1 is the last piece)
    put(d / "p000001.seal.json.zz", szz)

    def fix_seal(o):
        o["seal_sha256"] = sha(sb)
        o["members"][0].update(bytes=len(sb), sha256=sha(sb), wire_bytes=len(szz), wire_sha256=sha(szz))
        return o
    zz_rewrite(d / "p000001.offer.json.zz", fix_seal)
    zz_rewrite(rseal(h), lambda r: dict(r, through_seal=sha(sb)))      # test_credit's K2d call
    STATE["bind4"] = [g for g in R.parse(raw2, fp) if g["counter"] == 4][0]["bind"]
    return sb


def case_forged():
    """KA-4 and KA-5: the FORGED home; content writes the set-aside, credit reads content's REAL verdict."""
    h = WORK / "forged"
    fetch(h)
    sb = forge(h)
    check("S1 FORGED: a1 exit 0, RECEIVED 2 pieces (the forged seal, offer and raw member receipted like real ones)",
          custody(h), (0, "2"))
    rc, other, counts, out = content(h)
    if not check("S2 FORGED a2: exit 0; counts (2, 0, accepted 3 games, 104 rows, noselfgame 0, set_aside 1, waits 0, "
                 f"conflicts 0); exactly one other line: SET ASIDE {gid(4)}: {WHY}",
                 (rc, other, counts), (0, [f"SET ASIDE {gid(4)}: {WHY}"], FORGED_COUNTS)):
        print(out[-800:])
    v1 = W.canon({"schema": 2, "run_fingerprint": FP["fp"], "slot": 1, "index": 1, "seal_sha256": sha(sb), "round": 1,
                  "piece": "judged", "why": None,
                  "games": [{"game": gid(3), "rows": 0, "rows_digest": None, "state": "accepted", "why": None},
                            {"game": gid(4), "rows": 112, "rows_digest": None, "state": "set_aside", "why": WHY}]})
    want_v = {"p000000.verdict.json": STATE.get("p0"), "p000001.verdict.json": v1}
    check("S3 FORGED verdicts byte for byte: p1 judged, id 3 accepted (rows 0, digest null), id 4 set_aside (rows 112, "
          "digest null, why the position); p0 the PLAIN home's", verdicts(h), want_v)
    entries = [(1, g["counter"], 1, g["id"], f"w001/p{i:06d}", "accepted", R.rows_digest(g["rows"], g["end"]),
                g["bind"]) for i, g in server_games()]
    entries[3] = entries[3][:5] + ("set_aside", None, STATE.get("bind4"))
    check("S4 FORGED content/equal.sqlite: ids 1, 2, 3 accepted with the server's digests and binds; id 4 set_aside, "
          "digest null, the FORGED record's bind", index_rows(h), entries)
    rc, other, counts, out = content(h)
    check("S5 FORGED a2 again: exit 0, the same counts, no other line, both verdicts unchanged",
          (rc, other, counts, verdicts(h)), (0, [], FORGED_COUNTS, want_v))
    g = raw_games()
    ids = [entry(1, "credited", g), entry(2, "credited", g), entry(3, "credited", g),
           dict(entry(4, "set_aside", g), rows_digest=None)]
    rc, out, m = credit(h)
    if not check("S6 FORGED credit reads content's REAL verdict: exit 0, decided 1 rounds (0 complete, 1 partial); "
                 "credited 0 games 0 rows; waits: none; holds 0", (rc, m), (0, ("1", "0", "1", "0", "0", "none", "0"))):
        print(out[-800:])
    want_c = {"r0001": want_list(h, ids, "partial", set_aside_ids=[gid(4)])}
    check("S7 FORGED stage/r0001/credit.json byte for byte: partial; ids 1 to 3 credited, id 4 set_aside (rows 112, "
          "digest null); set_aside_ids [id 4]; games_in 4, raw_rows_in 216; the FORGED range seal's sha256",
          decided(h), want_c)
    rc, out, m = credit(h)
    check("S8 FORGED credit again: exit 0, decided 0 rounds; credited 0 games 0 rows; the credit list as S7's",
          (rc, m, decided(h)), (0, ("0", "0", "0", "0", "0", "none", "0"), want_c))


def main() -> int:
    t0 = time.time()
    try:
        ok = server()
    except Exception:  # noqa: BLE001
        RESULTS.append(("the server crashed", False))
        print(f"FAIL the server crashed:\n{traceback.format_exc()}")
        ok = False
    if not ok:
        print("the server side failed: no home case can run")
    else:
        for fn in (case_plain, case_forged):
            safe(fn)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"{len(RESULTS) - len(bad)} of {len(RESULTS)} checks pass ({time.time() - t0:.0f} s)"
          + (f"; PLANT {PLANT}" if PLANT else ""))
    return 0 if RESULTS and not bad else 1


if __name__ == "__main__":
    sys.exit(main())

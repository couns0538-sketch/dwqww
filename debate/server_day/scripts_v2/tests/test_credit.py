"""test_credit.py: stage b part 1 at home (A3d part 3, home/credit.py; FORMATS 2.3, A26) against known answers written
BEFORE it (tmp/opus_scratch/home_b/KNOWN_ANSWERS_b1_by_opus.md on the PC). Runs under a Python with python-chess 1.11.2
(the fixture runs stage a2).

    test_credit.py <home/credit.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]

The tree above home/ (home/, run/, workloads/, known/) is copied; a plant is applied to the copy's credit.py only.
R2  the server from the day's REAL programs: run "cred", slot 1, piece_games 2, the list rule with N12's six openings,
    pilot ranges round 1 = 1..4 and round 2 = 5..12 (ids 7 to 12 take the openings of ids 1 to 6 again); the worker
    plays until round 2's range seal, then the fence; the packer with the official converter; the published a1
    (custody.py) and a2 (content.py) at home. Every case works on its own copy of that home.
F0  the fixture's own control: ids 7, 8, 10, 11, 12 have the rows_digest of ids 1, 2, 4, 5, 6 (the engine replays a
    game exactly); ids 3 and 9 have no rows.
K1 to K21 as the known answers (day size as CHANGED 21:4x: stage/credited.sqlite) (K8 as CHANGED 21:26: a2's own conflict record makes its round WAIT). A case that changes a2's output edits a2's REAL verdict file (one game's fields),
never a typed stand-in; a case that changes a range seal rewrites the worker's real one.
PLANTS (each must make the test fail): see PLANTS below.
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
    print("usage: test_credit.py <home/credit.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]")
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
    "plant1": ("                    if i not in c1:\n", "                    if False:\n"),
    "plant2": ("                    if v is None:\n", "                    if False:\n"),
    "plant3": ("                need(c1[s[\"through_index\"]][\"sha256\"] == s[\"through_seal\"],\n",
               "                need(True,\n"),
    "plant4": ("                        e[\"state\"], e[\"same_rows_as\"] = (\"repeat\", first) if first else (\"credited\", None)\n",
               "                        e[\"state\"], e[\"same_rows_as\"] = (\"credited\", None)\n"),
    "plant5": ("                \"repeat_games\": sum(e[\"state\"] == \"repeat\" for e in ids)}, ({} if partial else mine)\n",
               "                \"repeat_games\": sum(e[\"state\"] == \"repeat\" for e in ids)}, mine\n"),
    "plant6": ("                    print(f\"WAITS {waits}\")\n                    break\n",
               "                    print(f\"WAITS {waits}\")\n                    continue\n"),
    "plant7": ("                if gid in conflicts:\n", "                if False:\n"),
    "plant8": ("                    e[\"state\"] = \"missing\" if said == \"done\" else said\n",
               "                    e[\"state\"] = \"credited\" if said == \"done\" else said\n"),
    "plant9": ("                        need(known is not None, f\"stage/r{r:04d}/credit.json exists and stage/credited.sqlite has no \"\n",
               "                        need(True, f\"stage/r{r:04d}/credit.json exists and stage/credited.sqlite has no \"\n"),
    "plant10": ("             and is_int(*(d[x] for x in STATES)) and sum(d[x] for x in STATES) == last - first + 1,\n",
                "             and is_int(*(d[x] for x in STATES)),\n"),
    "plant11": ("                for i in range(s[\"first_index\"], s[\"through_index\"] + 1):\n",
                "                for i in range(s[\"first_index\"], s[\"through_index\"]):\n"),
    "plant12": ("        for r in sorted({rr for (_k, rr) in rows}):\n",
                "        for r in sorted({rr for (_k, rr) in rows}, reverse=True):\n"),
    "plant13": ("                if len(gs) > 1:\n", "                if False:\n"),
    "plant14": ("        if s[\"schedule\"] > self.newest:\n", "        if False:\n"),
    "plant15": ("                        need(top is None or top <= r, f\"round {r} has no credit list and stage/credited.sqlite holds \"\n",
                "                        need(True, f\"round {r} has no credit list and stage/credited.sqlite holds \"\n"),
    "plant16": ("            con.execute(\"DELETE FROM credited WHERE round = ?\", (r,))\n", "            con.execute(\"SELECT 1\")\n"),
    "plant17": ("        if any(self.stage.glob(\"r*/credit.json\")) and (not self.db.is_file() or self.db.stat().st_size == 0):\n",
                "        if False:\n"),
    "plant18": ("                    need(run == self.H.h[\"run\"] and kk == k and s[\"first\"] <= c <= s[\"last\"],\n",
                "                    need(run == self.H.h[\"run\"] and kk == k,\n"),
    "plant19": ("                     and v.get(\"seal_sha256\") == seal[\"sha256\"] and v.get(\"round\") == r,\n",
                "                     and v.get(\"round\") == r,\n"),
    "plant20": ("                need([s[\"games\"], s[\"rows\"], s[\"raw_bytes\"]] ==\n",
                "                need(True or [s[\"games\"], s[\"rows\"], s[\"raw_bytes\"]] ==\n"),
    "plant21": ("        elif row[0] != self.fp:\n", "        elif False:\n"),
    "plant22": ("        if row is None and con.execute(\"SELECT COUNT(*) FROM rounds\").fetchone()[0]:\n",
                "        if False:\n"),
}
CP = WORK / "tree"
for sub in ("home", "run", "workloads", "known"):
    shutil.copytree(TREE / sub, CP / sub, ignore=shutil.ignore_patterns("__pycache__"))
if PLANT:
    old, new = PLANTS[PLANT]
    text = (CP / "home" / "credit.py").read_text(encoding="ascii")
    assert text.count(old) == 1, f"{PLANT}: the old text is not there exactly once"
    (CP / "home" / "credit.py").write_text(text.replace(old, new), encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy's credit.py")
RUN, CUST, CONT, CRED = CP / "run", CP / "home" / "custody.py", CP / "home" / "content.py", CP / "home" / "credit.py"
sys.path.insert(0, str(RUN))
import record as R  # noqa: E402
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
NOW = time.time()
SRV, BASE = WORK / "srv", WORK / "base"
FP = {}
CUST_COUNTS = re.compile(r"custody: RECEIVED (\d+) pieces (\d+) rows; C1 (\d+) pieces")
CONT_COUNTS = re.compile(r"content: judged (\d+) pieces \((\d+) refused\); accepted (\d+) games (\d+) rows; ")
LAST = re.compile(r"credit: decided (\d+) rounds \((\d+) complete, (\d+) partial\) this pass; credited (\d+) games "
                  r"(\d+) rows; waits: (.*); holds (\d)")


def gid(c: int) -> str:
    return f"cred-w001-g{c:08d}"


# ---- the fixture R2 -------------------------------------------------------------------------------------------------
def server() -> bool:
    put(SRV / "RUN.json", W.canon({
        "schema": 2, "run": "cred", "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
        "hard_cutoff_utc": T(NOW + 86400), "boot_id": W.boot_id(), "instance": "test-instance", "package": "0" * 64,
        "engine_sha256": sha(EXE.read_bytes()), "net_sha256": MAN["net_sha256"],
        "options_sha256": sha("".join(ln + "\n" for ln in MAN["options"]).encode("ascii")),
        "game_line": MAN["selfgame_line"], "opening_rule": {"kind": "list", "sha256": sha(OPENINGS.read_bytes()),
                                                             "count": len(N12)},
        "slots": [1], "piece_games": 2,
        "pilot_ranges": [{"slot": 1, "round": 1, "first": 1, "last": 4, "short": False, "schedule": 0},
                         {"slot": 1, "round": 2, "first": 5, "last": 12, "short": False, "schedule": 0}]}))
    FP["fp"] = fp = sha((SRV / "RUN.json").read_bytes())
    hdr = json.loads((SRV / "RUN.json").read_bytes())
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
    if not check("R2 server: exit 0, six pieces of rounds 1 1 2 2 2 2, both range seals",
                 (p.returncode, [s["round"] for s in seals], sorted(x.name for x in (SRV / "ranges").glob("*.json"))),
                 (0, [1, 1, 2, 2, 2, 2], ["r0001.w001.seal.json", "r0002.w001.seal.json"])):
        print(log.read_text(encoding="utf-8", errors="replace")[-600:])
        return False
    rc = subprocess.run([sys.executable, "-I", "-B", str(RUN / "packer.py"), "--root", str(SRV), "--converter",
                         str(CONV), "--once"], capture_output=True, text=True, timeout=600).returncode
    forms = [json.loads((SRV / "out" / "w001" / f"p{i:06d}.offer.json").read_bytes())["form"] for i in range(6)]
    return check("R2 packer: exit 0, six binpack offers", (rc, forms), (0, ["binpack"] * 6))


def fetch(home: Path) -> None:
    for p in sorted(SRV.glob("*.zz")):
        put(home / "wire" / p.name, p.read_bytes())
    for p in sorted((SRV / "ranges").glob("*.zz")):
        put(home / "wire" / "ranges" / p.name, p.read_bytes())
    src, dst = SRV / "out" / "w001", home / "wire" / "out" / "w001"
    for i in range(6):
        o = json.loads(zlib.decompress((src / f"p{i:06d}.offer.json.zz").read_bytes()))
        for m in o["members"]:
            put(dst / m["wire_name"], (src / m["wire_name"]).read_bytes())
        put(dst / f"p{i:06d}.offer.json.zz", (src / f"p{i:06d}.offer.json.zz").read_bytes())


def content(h: Path) -> tuple:
    p = subprocess.run([sys.executable, "-I", "-B", str(CONT), "--home", str(h), "--fingerprint", FP["fp"],
                        "--converter", str(CONV), "--openings", str(OPENINGS)], capture_output=True, text=True, timeout=900)
    return p.returncode, p.stdout + p.stderr


def base() -> bool:
    fetch(BASE)
    p = subprocess.run([sys.executable, "-I", "-B", str(CUST), "--home", str(BASE), "--fingerprint", FP["fp"]],
                       capture_output=True, text=True, timeout=300)
    m = CUST_COUNTS.search(p.stdout)
    ok = check("R2 a1: exit 0, RECEIVED 6 pieces, C1 6", (p.returncode, m and (m[1], m[3])), (0, ("6", "6")))
    p = subprocess.run([sys.executable, "-I", "-B", str(CONT), "--home", str(BASE), "--fingerprint", FP["fp"],
                        "--converter", str(CONV), "--openings", str(OPENINGS)], capture_output=True, text=True, timeout=900)
    m = CONT_COUNTS.search(p.stdout)
    return check("R2 a2: exit 0, judged 6 pieces (0 refused), accepted 12 games",
                 (p.returncode, m and (m[1], m[2], m[3])), (0, ("6", "0", "12"))) and ok


def raw_games() -> dict:
    """counter -> (rows, rows_digest) from the SERVER's own raw pieces (the source of every known answer below)."""
    out = {}
    for i in range(6):
        for g in R.parse((SRV / "w001" / "closed" / f"p{i:06d}.raw").read_bytes(), FP["fp"]):
            out[g["counter"]] = (len(g["rows"]), R.rows_digest(g["rows"], g["end"]))
    return out


def home(name: str) -> Path:
    h = WORK / name
    shutil.copytree(BASE, h)
    return h


def credit(h: Path, fp=None) -> tuple:
    p = subprocess.run([sys.executable, "-I", "-B", str(CRED), "--home", str(h), "--fingerprint", fp or FP["fp"]],
                       capture_output=True, text=True, timeout=600)
    out = (p.stdout + p.stderr).strip()
    m = LAST.fullmatch(out.splitlines()[-1]) if out else None
    return p.returncode, out, (m.groups() if m else None)


def decided(h: Path) -> dict:
    d = h / "stage"
    return {p.parent.name: p.read_bytes() for p in sorted(d.glob("r*/credit.json"))} if d.is_dir() else {}


def rseal(h: Path, r: int) -> Path:
    return h / "wire" / "ranges" / f"r{r:04d}.w001.seal.json.zz"


def rseal_sha(h: Path, r: int) -> str:
    return sha(zlib.decompress(rseal(h, r).read_bytes()))


def zz_rewrite(path: Path, fn) -> None:
    put(path, zlib.compress(W.canon(fn(json.loads(zlib.decompress(path.read_bytes())))), 6))


def verdict_rewrite(h: Path, i: int, fn) -> None:
    p = h / "content" / "w001" / f"p{i:06d}.verdict.json"
    v = json.loads(p.read_bytes())
    fn(v)
    p.write_bytes(W.canon(v))


def entry(c: int, state: str, games: dict, same=None) -> dict:
    rows, dg = games[c]
    return {"counter": c, "game": gid(c), "rows": rows, "rows_digest": dg, "same_rows_as": same, "slot": 1,
            "state": state}


def want_list(h: Path, r: int, ids: list, status: str, games: dict, **over) -> bytes:
    s = json.loads(zlib.decompress(rseal(h, r).read_bytes()))
    c = {"schema": 2, "run_fingerprint": FP["fp"], "round": r, "status": status,
         "range_seals": [{"slot": 1, "sha256": rseal_sha(h, r)}], "games_in": s["games"], "raw_rows_in": s["rows"],
         "ids": ids, "missing_ids": [], "set_aside_ids": [], "conflict_ids": [],
         "repeat_games": sum(e["state"] == "repeat" for e in ids)}
    c.update(over)
    return W.canon(c)


def round1(games: dict, change=None) -> list:
    return [entry(c, (change or {}).get(c, "credited"), games) for c in range(1, 5)]


def round2(games: dict, eligible1: bool = True) -> list:
    rep = {7: 1, 8: 2, 10: 4, 11: 5, 12: 6} if eligible1 else {11: 5, 12: 6}
    return [entry(c, "repeat", games, gid(rep[c])) if c in rep else entry(c, "credited", games) for c in range(5, 13)]


# ---- the cases ------------------------------------------------------------------------------------------------------
def case_f0_k1_k3_k4():
    g = raw_games()
    check("F0 the fixture: ids 7 8 10 11 12 repeat the rows of 1 2 4 5 6 (same digest); ids 3 and 9 have no rows",
          ([g[c][1] == g[c - 6][1] for c in (7, 8, 10, 11, 12)], g[3][0], g[9][0], g[3][1], len({g[c][1] for c in (1, 2, 4, 5, 6)})),
          ([True] * 5, 0, 0, None, 5))
    h = home("k3")
    rc, out, m = credit(h, "0" * 64)
    check("K3 another fingerprint: exit 3, nothing written", (rc, out.splitlines()[-1].startswith("credit: STOP (3)"),
                                                              (h / "stage").exists()), (3, True, False))
    h = home("k1")
    rc, out, m = credit(h)
    rows = sum(g[c][0] for c in (1, 2, 3, 4, 5, 6, 9))
    check("K1/K5 one pass: exit 0, decided 2 rounds (2 complete), credited 7 games, waits none, holds 0",
          (rc, m), (0, ("2", "2", "0", "7", str(rows), "none", "0")))
    want = {"r0001": want_list(h, 1, round1(g), "complete", g), "r0002": want_list(h, 2, round2(g), "complete", g)}
    check("K1/K5 both credit lists byte for byte (round 2: 5 repeats of round 1 and of 5, 6; id 9 without rows credited)",
          decided(h), want)
    rc, out, m = credit(h)
    check("K4 a second pass: exit 0, decided 0 rounds, the same credit, the files unchanged",
          (rc, m, decided(h)), (0, ("0", "0", "0", "7", str(rows), "none", "0"), want))


def case_k2():
    h = home("k2a")
    rseal(h, 1).unlink()
    rc, out, m = credit(h)
    check("K2a round 1's range seal not at home: exit 0, WAITS round 1, nothing decided",
          (rc, m and m[0], m and m[5], decided(h)),
          (0, "0", "round 1: the range seal r0001.w001.seal.json is not at home", {}))
    h = home("k2b")
    (h / "content" / "w001" / "p000001.verdict.json").unlink()
    rc, out, m = credit(h)
    check("K2b/K6 p1 not judged: exit 0, WAITS round 1 naming p1's verdict; round 2 (all judged) not decided either",
          (rc, m and m[0], m and m[5], decided(h)),
          (0, "0", "round 1: w001/p000001 of round 1 has no content verdict yet", {}))
    h = home("k2c")
    (h / "custody" / "w001" / "p000001.receipt.json").unlink()
    rc, out, m = credit(h)
    check("K2c p1 without a receipt (C1 stops before it): exit 0, WAITS round 1, nothing decided",
          (rc, m and m[0], m and m[5], decided(h)),
          (0, "0", "round 1: w001/p000001 of round 1 is not in custody's chain (C1) yet", {}))
    h = home("k2d")
    s0 = sha(zlib.decompress((h / "wire" / "out" / "w001" / "p000000.seal.json.zz").read_bytes()))
    zz_rewrite(rseal(h, 1), lambda s: dict(s, through_seal=s0))
    rc, out, m = credit(h)
    check("K2d round 1's range seal names another through_seal: exit 5, an ALARM line naming it, nothing decided",
          (rc, m and m[6], "ALARM credit HOLDS round 1: r0001.w001: through_seal " + s0 in out, decided(h)),
          (5, "1", True, {}))


def case_k7_k8_k9():
    g = raw_games()

    def aside(v):
        x = [e for e in v["games"] if e["game"] == gid(2)][0]
        x.update(state="set_aside", rows_digest=None, why="test: a2 set this game aside")
    h = home("k7")
    verdict_rewrite(h, 0, aside)
    rc, out, m = credit(h)
    e1 = round1(g, {2: "set_aside"})
    e1[1]["rows_digest"] = None
    rows = sum(g[c][0] for c in (5, 6, 7, 8, 9, 10))
    check("K7 id 2 set aside: exit 0, 2 rounds (1 complete, 1 partial); credited 6 games (round 2 only)",
          (rc, m), (0, ("2", "1", "1", "6", str(rows), "none", "0")))
    check("K7 round 1 partial, set_aside_ids [id 2]; round 2 GUESS (Q5): copies of round 1's games credited",
          decided(h), {"r0001": want_list(h, 1, e1, "partial", g, set_aside_ids=[gid(2)]),
                       "r0002": want_list(h, 2, round2(g, eligible1=False), "complete", g)})
    h = home("k8")
    con = sqlite3.connect(h / "content" / "equal.sqlite")
    con.execute("UPDATE entries SET piece = 'w001/p000009', rows_digest = ?, bind = ? WHERE slot = 1 AND counter = 2",
                ("f" * 64, "f" * 64))
    con.commit()
    con.close()
    (h / "content" / "w001" / "p000000.verdict.json").unlink()
    arc, aout = content(h)
    rec = json.loads((h / "conflicts" / f"{gid(2)}.json").read_bytes()) if (h / "conflicts" / f"{gid(2)}.json").exists() else {}
    check("K8 control: a2 (its own run) writes the conflict record for id 2 and p0's verdict again",
          (arc, rec.get("game"), rec.get("how"), (h / "content" / "w001" / "p000000.verdict.json").exists()),
          (0, gid(2), "two records under one id", True))
    rc, out, m = credit(h)
    check("K8 a2's conflict record for id 2: exit 0, round 1 WAITS for A26, nothing decided (round 2 behind it)",
          (rc, m and m[0], m and m[5], decided(h)),
          (0, "0", f"round 1: {gid(2)} has a conflict record; A26's replay decides it (FORMATS 2.3)", {}))
    h = home("k9")
    verdict_rewrite(h, 1, lambda v: v.update(piece="refused", why="transport: test", games=[]))
    rc, out, m = credit(h)
    e1 = round1(g)
    for x in e1[2:]:
        x.update(state="missing", rows=0, rows_digest=None)
    check("K9 p1 refused by a2: ids 3 and 4 missing, round 1 partial; round 2 as K7",
          (rc, m and m[:3], decided(h)),
          (0, ("2", "1", "1"), {"r0001": want_list(h, 1, e1, "partial", g, missing_ids=[gid(3), gid(4)]),
                                "r0002": want_list(h, 2, round2(g, eligible1=False), "complete", g)}))


def case_k10_to_k13():
    g = raw_games()
    h = home("k10")
    seals = [json.loads(zlib.decompress((h / "wire" / "out" / "w001" / f"p{i:06d}.seal.json.zz").read_bytes()))
             for i in range(6)]
    s4 = sha(zlib.decompress((h / "wire" / "out" / "w001" / "p000004.seal.json.zz").read_bytes()))

    def cut(s):
        s.update(complete=False, through_index=4, through_seal=s4, games=sum(x["games"] for x in seals[2:5]),
                 rows=sum(x["rows"] for x in seals[2:5]), raw_bytes=sum(x["raw_bytes"] for x in seals[2:5]))
        s["dispositions"].update(done=6, never_dispatched=2, never_dispatched_first=11)
        return s
    zz_rewrite(rseal(h, 2), cut)
    rc, out, m = credit(h)
    e2 = round2(g)[:6] + [{"counter": c, "game": gid(c), "rows": 0, "rows_digest": None, "same_rows_as": None,
                           "slot": 1, "state": "never_dispatched"} for c in (11, 12)]
    check("K10 round 2 cut by D (ids 11 and 12 never dispatched, pieces 2 to 4): round 2 partial, missing_ids [11, 12]",
          (rc, m and m[:3], decided(h).get("r0002")),
          (0, ("2", "1", "1"), want_list(h, 2, e2, "partial", g, missing_ids=[gid(11), gid(12)])))
    h = home("k11")
    credit(h)
    sql(h, "DELETE FROM rounds WHERE round = 1")
    rc, out, m = credit(h)
    check("K11 round 1 decided, then its rounds row removed from the table: exit 5, ALARM naming it",
          (rc, m and m[6], "ALARM credit HOLDS round 1: stage/r0001/credit.json exists and stage/credited.sqlite has no "
                           "row for round 1" in out), (5, "1", True))
    h = home("k11b")
    credit(h)
    (h / "stage" / "r0001" / "credit.json").unlink()
    rc, out, m = credit(h)
    check("K11b round 1's credit list removed below the table's round 2: exit 5, ALARM naming it, nothing written",
          (rc, m and m[6], "ALARM credit HOLDS round 1: round 1 has no credit list and stage/credited.sqlite holds round 2"
                           in out, sorted(decided(h))), (5, "1", True, ["r0002"]))
    h = home("k12")
    v2 = json.loads((h / "content" / "w001" / "p000002.verdict.json").read_bytes())
    six = [e for e in v2["games"] if e["game"] == gid(6)][0]
    verdict_rewrite(h, 3, lambda v: v["games"].append(dict(six)))
    rc, out, m = credit(h)
    check("K12 id 6 in two pieces of round 2 with no conflict record: exit 5, ALARM naming it; round 1 decided",
          (rc, m and m[:3], f"ALARM credit HOLDS round 2: {gid(6)} is held by 2 pieces" in out, sorted(decided(h))),
          (5, ("1", "1", "0"), True, ["r0001"]))
    h = home("k13")
    zz_rewrite(rseal(h, 1), lambda s: (s["dispositions"].update(done=3), s)[1])
    rc, out, m = credit(h)
    check("K13 round 1's range seal counts 3 ids for a range of 4: exit 5, ALARM, nothing decided",
          (rc, "ALARM credit HOLDS round 1: r0001.w001.seal.json: the six counts do not sum" in out, decided(h)),
          (5, True, {}))


def case_k18_to_k20():
    h = home("k18")
    verdict_rewrite(h, 1, lambda v: [g.update(game=gid(5)) for g in v["games"] if g["game"] == gid(4)])
    rc, out, m = credit(h)
    check("K18 p1's verdict names id 4's game as id 5 (an interval outside round 1's range): exit 5, ALARM naming it, "
          "nothing decided", (rc, f"ALARM credit HOLDS round 1: {gid(5)} in w001/p000001 is not an id of r0001.w001"
                              in out, decided(h)), (5, True, {}))
    h = home("k19")
    verdict_rewrite(h, 0, lambda v: v.update(seal_sha256="0" * 64))
    rc, out, m = credit(h)
    check("K19 p0's verdict names another seal: exit 5, ALARM naming it, nothing decided",
          (rc, "ALARM credit HOLDS round 1: the verdict of w001/p000000 is not of its kept seal (round 1)" in out,
           decided(h)), (5, True, {}))
    h = home("k20")
    zz_rewrite(rseal(h, 1), lambda s: (s.update(rows=s["rows"] + 1), s)[1])
    rc, out, m = credit(h)
    check("K20 round 1's range seal says rows + 1: exit 5, ALARM naming it, nothing decided",
          (rc, "ALARM credit HOLDS round 1: r0001.w001: games, rows or raw_bytes are not the sums of its pieces' seals"
           in out, decided(h)), (5, True, {}))


def sql(h: Path, statement: str) -> None:
    con = sqlite3.connect(h / "stage" / "credited.sqlite")
    con.execute(statement)
    con.commit()
    con.close()


def table(h: Path) -> tuple:
    con = sqlite3.connect(h / "stage" / "credited.sqlite")
    try:
        return ([tuple(x) for x in con.execute("SELECT rows_digest, game, round FROM credited ORDER BY round, game")],
                [tuple(x) for x in con.execute("SELECT round, status, games, rows FROM rounds ORDER BY round")])
    finally:
        con.close()


def meta(h: Path) -> list:
    con = sqlite3.connect(h / "stage" / "credited.sqlite")
    try:
        return [tuple(x) for x in con.execute("SELECT key, value FROM meta ORDER BY key")]
    finally:
        con.close()


def case_k16_k17():
    g = raw_games()
    want_table = ([(g[c][1], gid(c), 1) for c in (1, 2, 4)] + [(g[c][1], gid(c), 2) for c in (5, 6)],
                  [(1, "complete", 4, 314), (2, "complete", 3, 148)])
    h = home("k16")
    credit(h)
    want = decided(h)
    check("K4b the table after K1: 5 credited digests (ids 1 2 4 of round 1, 5 6 of round 2); rounds (1, complete, 4, "
          "314) and (2, complete, 3, 148)", table(h), want_table)
    check("K4c the table names its run: meta holds exactly ('run_fingerprint', the pinned fingerprint)",
          meta(h), [("run_fingerprint", FP["fp"])])
    h21 = home("k21a")
    credit(h21)
    sql(h21, "UPDATE meta SET value = '" + "f" * 64 + "' WHERE key = 'run_fingerprint'")
    before = (decided(h21), table(h21))
    rc, out, m = credit(h21)
    check("K21a the table's run changed to 64 f: exit 3 naming another run, the lists and the table unchanged",
          (rc, out.splitlines()[-1].startswith("credit: STOP (3): stage/credited.sqlite belongs to another run"),
           (decided(h21), table(h21)) == before), (3, True, True))
    h21 = home("k21b")
    credit(h21)
    sql(h21, "DELETE FROM meta")
    before = (decided(h21), table(h21))
    rc, out, m = credit(h21)
    check("K21b the table's run row deleted while rounds are decided: exit 3, nothing changed, no run row written",
          (rc, out.splitlines()[-1].startswith("credit: STOP (3): stage/credited.sqlite holds decided rounds and names "
                                               "no run"), (decided(h21), table(h21)) == before, meta(h21)),
          (3, True, True, []))
    (h / "stage" / "credited.sqlite").unlink()
    rc, out, m = credit(h)
    check("K16 the table removed while credit lists exist: exit 4 naming it, no table made, the lists unchanged",
          (rc, out.splitlines()[-1].startswith("credit: STOP (4): stage/credited.sqlite is gone while decided rounds "
                                               "exist"), (h / "stage" / "credited.sqlite").exists(), decided(h)),
          (4, True, False, want))
    (h / "stage").rename(h / "stage.lost")
    rc, out, m = credit(h)
    check("K16 control: stage/ moved aside, a pass decides both rounds again with K1's bytes and table",
          (rc, m and m[0], decided(h), table(h)), (0, "2", want, want_table))
    h = home("k17")
    credit(h)
    (h / "stage" / "r0002" / "credit.json").unlink()
    rc, out, m = credit(h)
    check("K17 round 2's credit list missing after its commit (a crash): exit 0, round 2 decided again, the same "
          "bytes and the same table", (rc, m and m[0], decided(h), table(h)), (0, "1", want, want_table))


def case_k14_k15():
    g = raw_games()
    items = {"A": [Path("wire/ranges/r0001.w001.seal.json.zz")],
             "B": [Path("custody/w001/p000000.receipt.json"), Path("content/w001/p000000.verdict.json")],
             "C": [Path("custody/w001/p000001.receipt.json"), Path("content/w001/p000001.verdict.json")]}
    for order in ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA"):
        h, held = home(f"k14_{order}"), WORK / f"k14_{order}.held"
        for rel in sum(items.values(), []):
            put(held / rel, (h / rel).read_bytes())
            (h / rel).unlink()
        seen = []
        for x in order:
            for rel in items[x]:
                put(h / rel, (held / rel).read_bytes())
            rc, out, m = credit(h)
            seen.append((rc, m and m[0], m and m[5].startswith("round 1: ")))
        want = {"r0001": want_list(h, 1, round1(g), "complete", g), "r0002": want_list(h, 2, round2(g), "complete", g)}
        check(f"K14 order {order}: two passes WAIT on round 1 and decide nothing, the third decides both rounds as K1",
              (seen, decided(h)), ([(0, "0", True), (0, "0", True), (0, "2", False)], want))
    h = home("k15")
    zz_rewrite(rseal(h, 1), lambda s: dict(s, schedule=1))
    rc, out, m = credit(h)
    check("K15 round 1's range seal names schedule 1, home holds only the pilot (0): exit 0, WAITS, nothing decided",
          (rc, m and m[0], m and m[5], decided(h)),
          (0, "0", "round 1: r0001.w001.seal.json was written under schedule 1; home holds schedule 0", {}))


def main() -> int:
    t0 = time.time()
    if not (server() and base()):
        print("the fixture failed: no case can run")
    else:
        for fn in (case_f0_k1_k3_k4, case_k2, case_k7_k8_k9, case_k10_to_k13, case_k14_k15, case_k16_k17, case_k18_to_k20):
            safe(fn)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"{len(RESULTS) - len(bad)} of {len(RESULTS)} checks pass ({time.time() - t0:.0f} s)"
          + (f"; PLANT {PLANT}" if PLANT else ""))
    return 0 if RESULTS and not bad else 1


if __name__ == "__main__":
    sys.exit(main())

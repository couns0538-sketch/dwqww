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
VERSION 2 (credit v2; known answers tmp/opus_scratch/credit_v2/KNOWN_ANSWERS_credit_v2_by_opus.md on the PC, 01:04,
addenda 01:13 and 01:21): K22 to K27 as those known answers; K10 and K12 changed as the 01:21 addendum says (their
fixtures were not of the form the worker and content write). A negative case checks the exit code AND the rule's own
words, so that a plant whose case still HOLDS through another rule fails it.
R3  the second real fixture: run "crm", slots 1 and 2, piece_games 2, R2's six openings with entry 4 replaced by
    fool's mate plus one listed ply that can never be played (no legal move left inside the entry: ids 4 of both
    slots end openingend, noselfgame; 01:28 addendum), a real SCHEDULE.1 written before the workers start
    (the pilot rows again), pilot ranges round 1 = 1..4 and round 2 = 5..8 in both slots; both workers play until
    their round-2 range seals, then the fence; the packer (piece 1 of each slot holds no rows: form raw), a1 and a2.
F1  R3's own control; K28a and K28b on it (both pass on version 1 too).
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
    # version 2 (K22 to K27): each takes one rule out, or (41, 42, 44) gives version 1's WAIT back for it
    "plant23": ("        need(nd is None or all(c < nd for c in cs),\n", "        need(True,\n"),
    "plant24": ("        need(all(a < b for a, b in zip(cs, cs[1:])),\n", "        need(True,\n"),
    "plant25": ("        need(is_int(s[\"epoch\"]) and s[\"epoch\"] >= 1,\n", "        need(True,\n"),
    "plant26": ("        need(type(s[\"short\"]) is bool and s[\"short\"] is self.short.get((k, r)),\n", "        need(True,\n"),
    "plant27": ("        need(type(s[\"complete\"]) is bool and s[\"complete\"] == (sum(d[x] for x in NOT_COMPLETE) == 0),\n",
                "        need(True,\n"),
    "plant28": ("        need(s[\"first_index\"] >= -1,\n", "        need(True,\n"),
    "plant29": ("            if outside:\n", "            if False:\n"),
    "plant30": ("        need(v[\"piece\"] in (\"judged\", \"refused\"),\n", "        need(True,\n"),
    "plant31": ("        need(v[\"why\"] is None and isinstance(gs, list) and len(gs) == seal[\"games\"],\n", "        need(True,\n"),
    "plant32": ("            need(g[\"state\"] in (\"accepted\", \"noselfgame\", \"set_aside\"),\n", "            need(True,\n"),
    "plant33": ("                need(type(dg) is str and HEX64.fullmatch(dg) is not None if g[\"rows\"] else dg is None,\n",
                "                need(True,\n"),
    "plant34": ("            need(is_int(g[\"rows\"]) and g[\"rows\"] >= 0,\n", "            need(True,\n"),
    "plant35": ("        need(sum(g[\"rows\"] for g in gs) == seal[\"rows\"],\n", "        need(True,\n"),
    "plant36": ("            need(isinstance(g, dict) and sorted(g) == GAME_KEYS,\n", "            need(isinstance(g, dict),\n"),
    "plant37": ("        need(is_int(v[\"schema\"]) and v[\"schema\"] == 2,\n", "        need(True,\n"),
    "plant38": ("                need(g[\"rows\"] == 0 and dg is None,\n", "                need(True,\n"),
    "plant39": ("                need(dg is None,\n", "                need(True,\n"),
    "plant40": ("            if i in forks:\n", "            if False:\n"),
    "plant41": ("            return f\"has epoch {s['epoch']}, below 1 or below {ep}, the epoch of the piece before\", None\n",
                "            return None\n"),
    "plant42": ("            return f\"names prev_seal {s['prev_seal'][:16]}..., not the seal of the piece before\", None\n",
                "            return None\n"),
    "plant43": ("        if not (isinstance(s, dict) and s.get(\"run_fingerprint\") == self.fp and is_int(s.get(\"slot\"), "
                "s.get(\"index\"))\n",
                "        if False and (isinstance(s, dict) and s.get(\"run_fingerprint\") == self.fp and is_int(s.get(\"slot\"), "
                "s.get(\"index\"))\n"),
    "plant44": ("            return \"is not the bytes its receipt names (seal_sha256)\", None\n", "            return None\n"),
    "plant45": ("        self.H.check_records()                          # C3, C4: STOP 3 or 4 before anything is decided "
                "or written\n", "        pass\n"),
    "plant46": ("        names = sorted(p.name for p in self.H.wire.glob(\"SCHEDULE.*.json.zz\"))\n", "        names = []\n"),
    "plant47": ("        for p in sorted(self.stage.glob(\"*/credit.json\")):\n", "        for p in []:\n"),
    "plant48": ("        if stray_rounds:\n", "        if False:\n"),
    "plant49": ("            if not held:\n", "            if False:\n"),
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
    for p in [h / "custody" / "w001" / "p000005.receipt.json", h / "content" / "w001" / "p000005.verdict.json",
              *sorted((h / "wire" / "out" / "w001").glob("p000005.*"))]:
        p.unlink()                                      # 01:21 addendum: piece 5 never existed when D cut round 2
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
    verdict_rewrite(h, 3, lambda v: [e.update(game=gid(6)) for e in v["games"] if e["game"] == gid(8)])   # 01:21
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


# ---- version 2 -----------------------------------------------------------------------------------------------------
def hold(name: str, h: Path, words: str, keys=()) -> None:
    """A case that must HOLD: exit 5, holds 1, the rule's own words in the output, only `keys` decided."""
    rc, out, m = credit(h)
    check(name, (rc, m and m[6], words in out, sorted(decided(h))), (5, "1", True, sorted(keys)))
    if words not in out:
        print("   its output: " + out[-500:].replace("\n", " | "))


def kept_rewrite(h: Path, i: int, fn) -> None:
    """Piece i's kept seal rewritten (canonical) and its receipt made to name the new bytes as custody writes a
    receipt for them: seal_sha256, and the seal member's sha256, bytes, wire_bytes and wire_sha256."""
    kp = h / "wire" / "out" / "w001" / f"p{i:06d}.seal.json.zz"
    nb = W.canon(fn(json.loads(zlib.decompress(kp.read_bytes()))))
    zb = zlib.compress(nb, 6)
    put(kp, zb)
    rp = h / "custody" / "w001" / f"p{i:06d}.receipt.json"
    r = json.loads(rp.read_bytes())
    r["seal_sha256"] = sha(nb)
    r["members"][0].update(sha256=sha(nb), bytes=len(nb), wire_bytes=len(zb), wire_sha256=sha(zb))
    put(rp, W.canon(r))


def case_k22():
    seals = [json.loads(zlib.decompress((BASE / "wire" / "out" / "w001" / f"p{i:06d}.seal.json.zz").read_bytes()))
             for i in range(6)]
    p0, p2 = (sha(zlib.decompress((BASE / "wire" / "out" / "w001" / f"p{i:06d}.seal.json.zz").read_bytes()))
              for i in (0, 2))

    def k22a(s):
        s["dispositions"].update(done=2, refused=1, never_dispatched=1, never_dispatched_first=4,
                                 not_done=[[gid(4), "refused"]])
        return dict(s, complete=False)

    def k22b(s):
        s["dispositions"].update(done=6, refused=2, not_done=[[gid(10), "refused"], [gid(6), "refused"]])
        return s

    def sums(idx):
        return {x: sum(seals[i][x] for i in idx) for x in ("games", "rows", "raw_bytes")}
    empty = dict(first_prev_seal=None, through_seal=None, games=0, rows=0, raw_bytes=0)
    for name, r, fn, words, keys in (
            ("K22a round 1's not_done names id 4 (refused) at never_dispatched_first 4", 1, k22a,
             "not_done names an id at or after never_dispatched_first 4", ()),
            ("K22b round 2's not_done is [id 10, id 6] (refused 2, done 6); round 1 decided", 2, k22b,
             "not_done is not in rising counter order (1.7)", ("r0001",)),
            ("K22c round 1's range seal with epoch 0", 1, lambda s: dict(s, epoch=0),
             "r0001.w001.seal.json: its epoch 0 is not a number >= 1", ()),
            ("K22d round 1's range seal with short true (its row says false)", 1, lambda s: dict(s, short=True),
             "r0001.w001.seal.json: short True is not the short of its row in schedule 0 (False)", ()),
            ("K22e round 1's range seal with complete false (every id done)", 1, lambda s: dict(s, complete=False),
             "r0001.w001.seal.json: complete False is not what its counts say", ()),
            ("K22f round 1's range seal with first_index and through_index -2", 1,
             lambda s: dict(s, first_index=-2, through_index=-2, **empty),
             "r0001.w001.seal.json: first_index -2 is below -1", ()),
            ("K22g round 1's range seal an empty range while C1 holds p0 and p1 of round 1", 1,
             lambda s: dict(s, first_index=-1, through_index=-1, **empty),
             "r0001.w001: C1 holds w001/p000000 of round 1 outside its range seal's pieces [-1, -1]", ()),
            ("K22h round 1's range seal through p0 (p1 of round 1 left out)", 1,
             lambda s: dict(s, through_index=0, through_seal=p0, **sums((0,))),
             "r0001.w001: C1 holds w001/p000001 of round 1 outside its range seal's pieces [0, 0]", ()),
            ("K22i round 2's range seal from p3 (p2 of round 2 left out); round 1 decided", 2,
             lambda s: dict(s, first_index=3, first_prev_seal=p2, **sums((3, 4, 5))),
             "r0002.w001: C1 holds w001/p000002 of round 2 outside its range seal's pieces [3, 5]", ("r0001",))):
        h = home(name.split()[0].lower())
        zz_rewrite(rseal(h, r), fn)
        hold(f"{name}: exit 5, ALARM naming the rule", h, words, keys)


def case_k23():
    def g_of(v, c):
        return [e for e in v["games"] if e["game"] == gid(c)][0]
    v0 = "content/w001/p000000.verdict.json"
    for name, i, fn, words in (
            ("K23a p0's verdict: piece corrupt_unknown", 0, lambda v: v.update(piece="corrupt_unknown"),
             f"{v0}: piece is 'corrupt_unknown', not judged or refused"),
            ("K23b p0's verdict: judged with games []", 0, lambda v: v.update(games=[]),
             f"{v0}: judged with 0 games, its kept seal holds 2"),
            ("K23c p0's verdict: id 1's state credited", 0, lambda v: g_of(v, 1).update(state="credited"),
             f"the state 'credited' of {gid(1)} is not accepted, noselfgame or set_aside"),
            ("K23d p0's verdict: id 1 accepted with rows and no rows_digest", 0,
             lambda v: g_of(v, 1).update(rows_digest=None), f"the rows_digest of {gid(1)} is not what 2.2 writes"),
            ("K23e p0's verdict: id 1's rows true", 0, lambda v: g_of(v, 1).update(rows=True),
             f"the rows of {gid(1)} are True, not a number >= 0"),
            ("K23f p0's verdict: id 2's rows + 1 (digest kept)", 0,
             lambda v: g_of(v, 2).update(rows=g_of(v, 2)["rows"] + 1),
             f"{v0}: the rows of its games do not sum to its kept seal's"),
            ("K23g p0's verdict: a game key x more", 0, lambda v: g_of(v, 1).update(x=1),
             f"{v0}: a game record whose keys are not content's (2.2)"),
            ("K23h p0's verdict: schema 1", 0, lambda v: v.update(schema=1), f"{v0}: its schema is 1, not 2"),
            ("K23i p1's verdict: id 3 noselfgame with a rows_digest", 1,
             lambda v: g_of(v, 3).update(state="noselfgame", rows_digest="a" * 64),
             f"{gid(3)} is noselfgame with rows or a rows_digest"),
            ("K23j p1's verdict: id 3 set_aside with a rows_digest", 1,
             lambda v: g_of(v, 3).update(state="set_aside", rows_digest="a" * 64),
             f"{gid(3)} is set_aside with a rows_digest")):
        h = home(name.split()[0].lower())
        verdict_rewrite(h, i, fn)
        hold(f"{name}: exit 5, ALARM naming the rule, nothing decided", h, words)
    h = home("k23k")
    p = h / "content" / "w001" / "p000000.verdict.json"
    p.write_bytes(p.read_bytes()[:40])
    hold("K23k p0's verdict truncated to 40 bytes: exit 5, ALARM naming the file, nothing decided (version 1: a "
         "traceback)", h, f"{v0} is not a canonical record")


def case_k24():
    h = home("k24a")
    rec = json.loads((h / "custody" / "w001" / "p000001.receipt.json").read_bytes())
    put(h / "custody" / "w001" / "p000001.fork.json", W.canon({
        "schema": 2, "run_fingerprint": FP["fp"], "slot": 1, "index": 1, "receipt_seal_sha256": rec["seal_sha256"],
        "receipt_offer_sha256": rec["offer_sha256"], "found_seal_sha256": "0" * 64, "found_offer_sha256": "0" * 64,
        "at_utc": T(NOW), "how": "test: a second offer of index 1"}))
    hold("K24a a fork record for p1 in custody's form: exit 5, ALARM naming it, nothing decided", h,
         "w001/p000001 has a fork record at home")
    for name, fn, words in (
            ("K24b p1's kept seal with epoch 0", lambda s: dict(s, epoch=0),
             "the kept seal of w001/p000001 has epoch 0, below 1"),
            ("K24c p1's kept seal with prev_seal f x 64", lambda s: dict(s, prev_seal="f" * 64),
             "the kept seal of w001/p000001 names prev_seal ffffffffffffffff..., not the seal of the piece before"),
            ("K24d p1's kept seal naming index 7", lambda s: dict(s, index=7),
             "the kept seal of w001/p000001 names another run, slot or index than its receipt")):
        h = home(name.split()[0].lower())
        kept_rewrite(h, 1, fn)
        hold(f"{name}, its receipt naming the new bytes: exit 5, ALARM naming the rule, nothing decided", h, words)
    h = home("k24e")
    put(h / "wire" / "out" / "w001" / "p000001.seal.json.zz",
        (h / "wire" / "out" / "w001" / "p000000.seal.json.zz").read_bytes())
    hold("K24e p1's kept seal replaced by p0's bytes, the receipt as it was: exit 5, ALARM naming it, nothing decided",
         h, "the kept seal of w001/p000001 is not the bytes its receipt names (seal_sha256)")
    h = home("k24f")
    (h / "wire" / "out" / "w001" / "p000001.seal.json.zz").unlink()
    rc, out, m = credit(h)
    check("K24f control: p1's kept seal not at home: exit 0, WAITS round 1 naming p1, nothing decided",
          (rc, m and m[0], m and m[5], decided(h)),
          (0, "0", "round 1: w001/p000001 of round 1 is not in custody's chain (C1) yet", {}))


def case_k25():
    for name, i, src, change, code in (
            ("K25a p0's receipt truncated to 40 bytes", 0, 0, lambda b: b[:40], 4),
            ("K25b p0's receipt naming another run (canonical)", 0, 0,
             lambda b: W.canon(dict(json.loads(b), run_fingerprint="e" * 64)), 3),
            ("K25c a truncated receipt as p9, beyond the chain (no p6 to p8)", 9, 0, lambda b: b[:40], 4)):
        h = home(name.split()[0].lower())
        rp = h / "custody" / "w001" / f"p{i:06d}.receipt.json"
        put(rp, change((h / "custody" / "w001" / f"p{src:06d}.receipt.json").read_bytes()))
        rc, out, m = credit(h)
        last = out.splitlines()[-1] if out else ""
        check(f"{name}: exit {code}, the STOP line naming custody/w001/p{i:06d}.receipt.json, nothing written",
              (rc, last.startswith(f"credit: STOP ({code}): custody/w001/p{i:06d}.receipt.json"), (h / "stage").exists()),
              (code, True, False))


def case_k26_k27():
    h = home("k26a")
    put(h / "wire" / "SCHEDULE.1.json.zz", b"abc")
    hold("K26a wire/SCHEDULE.1.json.zz present and not verifying: exit 5, ALARM naming it, nothing decided", h,
         "wire/SCHEDULE.1.json.zz is at home and custody's chain stopped before it")
    h = home("k26b")
    put(h / "wire" / "SCHEDULE.2.json.zz", b"abc")
    rc, out, m = credit(h)
    check("K26b SCHEDULE.2 at home and SCHEDULE.1 not: exit 0, WAITS naming the gap, nothing decided",
          (rc, m and m[0], m and m[5], decided(h)),
          (0, "0", "schedule: the schedule chain at home has a gap: SCHEDULE.1.json.zz is not at home, "
                   "SCHEDULE.2.json.zz is", {}))
    h = home("k26c")
    put(h / "wire" / "SCHEDULE.01.json.zz", b"abc")
    hold("K26c wire/SCHEDULE.01.json.zz (outside the chain's grammar): exit 5, ALARM naming it, nothing decided", h,
         "wire/SCHEDULE.01.json.zz is not a name of the schedule chain")
    for name, plant, words in (
            ("K26d a credit list stage/r0003 that no schedule row names",
             lambda h: put(h / "stage" / "r0003" / "credit.json", (h / "stage" / "r0001" / "credit.json").read_bytes()),
             "stage/r0003/credit.json is not a round of schedule 0"),
            ("K26e a rounds row 3 that no schedule row names",
             lambda h: sql(h, "INSERT INTO rounds VALUES (3, 'complete', 0, 0)"),
             "stage/credited.sqlite holds round 3, not a round of schedule 0")):
        h = home(name.split()[0].lower())
        credit(h)
        plant(h)
        before = (decided(h), table(h))
        rc, out, m = credit(h)
        check(f"{name}, after a first pass: exit 5, ALARM naming it, the lists and the table unchanged",
              (rc, m and m[6], words in out, (decided(h), table(h)) == before), (5, "1", True, True))
    h = home("k27a")
    credit(h)
    db = h / "stage" / "credited.sqlite"
    db.unlink()
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE credited (rows_digest TEXT PRIMARY KEY, game TEXT NOT NULL, round INTEGER NOT NULL)")
    con.execute("CREATE TABLE rounds (round INTEGER PRIMARY KEY, status TEXT NOT NULL, games INTEGER NOT NULL, "
                "rows INTEGER NOT NULL)")
    con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    con.commit()
    con.close()
    b = db.read_bytes()
    rc, out, m = credit(h)
    check("K27a the table replaced by a schema-only one while credit lists exist: exit 4 naming it, the table byte for "
          "byte as before", (rc, (out.splitlines() or [""])[-1].startswith(
              "credit: STOP (4): stage/credited.sqlite holds no decided round"), db.read_bytes() == b), (4, True, True))


SRV3, BASE3, OPEN3 = WORK / "srv3", WORK / "base3", WORK / "r3_openings.txt"


def gid3(k: int, c: int) -> str:
    return f"crm-w{k:03d}-g{c:08d}"


def server3() -> bool:
    ops = [list(o) for o in N12]
    ops[3] = ["f2f3", "e7e5", "g2g4", "d8h4", "a2a3"]       # 01:28 addendum: no legal move left INSIDE the entry
                                                            # (after the mate at ply 4): openingend, noselfgame
    OPEN3.write_bytes("".join(" ".join(o) + "\n" for o in ops).encode("ascii"))
    pilot = [{"slot": k, "round": r, "first": f, "last": la, "short": False, "schedule": 0}
             for k in (1, 2) for r, f, la in ((1, 1, 4), (2, 5, 8))]
    put(SRV3 / "RUN.json", W.canon({
        "schema": 2, "run": "crm", "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
        "hard_cutoff_utc": T(NOW + 86400), "boot_id": W.boot_id(), "instance": "test-instance", "package": "0" * 64,
        "engine_sha256": sha(EXE.read_bytes()), "net_sha256": MAN["net_sha256"],
        "options_sha256": sha("".join(ln + "\n" for ln in MAN["options"]).encode("ascii")),
        "game_line": MAN["selfgame_line"], "opening_rule": {"kind": "list", "sha256": sha(OPEN3.read_bytes()),
                                                             "count": len(ops)},
        "slots": [1, 2], "piece_games": 2, "pilot_ranges": pilot}))
    FP["fp3"] = fp = sha((SRV3 / "RUN.json").read_bytes())
    hdr = json.loads((SRV3 / "RUN.json").read_bytes())
    put(SRV3 / "SCHEDULE.1.json", W.canon({
        "schema": 2, "n": 1, "run_fingerprint": fp, "prev": "first", "evidence": "e" * 64,
        "cutoff_utc": hdr["hard_cutoff_utc"], "dispatch_end_utc": hdr["hard_cutoff_utc"], "ranges": pilot}))
    ps, logs = [], []
    for k in (1, 2):
        logs.append(open(WORK / f"srv3_w{k}.out", "wb"))
        ps.append(subprocess.Popen(
            [sys.executable, "-I", "-B", str(RUN / "worker.py"), "--root", str(SRV3), "--slot", str(k), "--exe", str(EXE),
             "--net", str(NET), "--manifest", str(MAN_PATH), "--known-startup", str(KNOWN), "--openings", str(OPEN3)],
            stdout=logs[-1], stderr=subprocess.STDOUT))
    end = time.time() + 900
    last_seals = [SRV3 / "ranges" / f"r0002.w{k:03d}.seal.json" for k in (1, 2)]
    while not all(x.exists() for x in last_seals) and all(p.poll() is None for p in ps) and time.time() < end:
        time.sleep(0.5)
    put(SRV3 / "FENCE.json", W.canon({"at_utc": T(time.time()), "cutoff_utc": hdr["hard_cutoff_utc"],
                                      "run_fingerprint": fp, "schema": 2, "why": "D"}))
    for p in ps:
        try:
            p.wait(timeout=120)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
    for f in logs:
        f.close()
    rounds = [[json.loads((SRV3 / f"w{k:03d}" / "closed" / f"p{i:06d}.seal.json").read_bytes())["round"]
               for i in range(4) if (SRV3 / f"w{k:03d}" / "closed" / f"p{i:06d}.seal.json").exists()] for k in (1, 2)]
    if not check("R3 server: both workers exit 0, four pieces each of rounds 1 1 2 2, four range seals",
                 ([p.returncode for p in ps], rounds, sorted(x.name for x in (SRV3 / "ranges").glob("*.json"))),
                 ([0, 0], [[1, 1, 2, 2]] * 2, ["r0001.w001.seal.json", "r0001.w002.seal.json", "r0002.w001.seal.json",
                                               "r0002.w002.seal.json"])):
        for k in (1, 2):
            print((WORK / f"srv3_w{k}.out").read_text(encoding="utf-8", errors="replace")[-600:])
        return False
    rc = subprocess.run([sys.executable, "-I", "-B", str(RUN / "packer.py"), "--root", str(SRV3), "--converter",
                         str(CONV), "--once"], capture_output=True, text=True, timeout=600).returncode
    forms = [[json.loads((SRV3 / "out" / f"w{k:03d}" / f"p{i:06d}.offer.json").read_bytes())["form"] for i in range(4)]
             for k in (1, 2)]
    return check("R3 packer: exit 0; per slot binpack, raw (piece 1: ids 3 and 4, no rows), binpack, binpack",
                 (rc, forms), (0, [["binpack", "raw", "binpack", "binpack"]] * 2))


def base3() -> bool:
    for p in sorted(SRV3.glob("*.zz")):
        put(BASE3 / "wire" / p.name, p.read_bytes())
    for p in sorted((SRV3 / "ranges").glob("*.zz")):
        put(BASE3 / "wire" / "ranges" / p.name, p.read_bytes())
    for k in (1, 2):
        src, dst = SRV3 / "out" / f"w{k:03d}", BASE3 / "wire" / "out" / f"w{k:03d}"
        for i in range(4):
            o = json.loads(zlib.decompress((src / f"p{i:06d}.offer.json.zz").read_bytes()))
            for mm in o["members"]:
                put(dst / mm["wire_name"], (src / mm["wire_name"]).read_bytes())
            put(dst / f"p{i:06d}.offer.json.zz", (src / f"p{i:06d}.offer.json.zz").read_bytes())
    p = subprocess.run([sys.executable, "-I", "-B", str(CUST), "--home", str(BASE3), "--fingerprint", FP["fp3"]],
                       capture_output=True, text=True, timeout=300)
    m = CUST_COUNTS.search(p.stdout)
    ok = check("R3 a1: exit 0, RECEIVED 8 pieces, C1 8", (p.returncode, m and (m[1], m[3])), (0, ("8", "8")))
    p = subprocess.run([sys.executable, "-I", "-B", str(CONT), "--home", str(BASE3), "--fingerprint", FP["fp3"],
                        "--converter", str(CONV), "--openings", str(OPEN3)], capture_output=True, text=True, timeout=900)
    m = CONT_COUNTS.search(p.stdout)
    return check("R3 a2: exit 0, judged 8 pieces (0 refused), accepted 14 games (ids 4 of both slots noselfgame)",
                 (p.returncode, m and (m[1], m[2], m[3])), (0, ("8", "0", "14"))) and ok


def case_k28():
    g = {}
    for k in (1, 2):
        for i in range(4):
            for x in R.parse((SRV3 / f"w{k:03d}" / "closed" / f"p{i:06d}.raw").read_bytes(), FP["fp3"]):
                g[(k, x["counter"])] = (len(x["rows"]), R.rows_digest(x["rows"], x["end"]), x["end"])
    check("F1 R3's own control: slot 2's rows_digest is slot 1's at every counter; id 3 without rows; ids 4 end "
          "openingend in both slots; ids 7 and 8 repeat 1 and 2",
          ([g[(2, c)][1] == g[(1, c)][1] for c in range(1, 9)], g[(1, 3)][0],
           [g[(k, 4)][2].startswith("openingend ") for k in (1, 2)], [g[(1, c)][1] == g[(1, c - 6)][1] for c in (7, 8)]),
          ([True] * 8, 0, [True, True], [True, True]))

    def e3(k, c, state, same=None):
        rows, dg, _end = g[(k, c)]
        return {"counter": c, "game": gid3(k, c), "rows": rows, "rows_digest": dg, "same_rows_as": same, "slot": k,
                "state": state}

    def want3(h, r, ids):
        bs = [zlib.decompress((h / "wire" / "ranges" / f"r{r:04d}.w{k:03d}.seal.json.zz").read_bytes()) for k in (1, 2)]
        ss = [json.loads(b) for b in bs]
        return W.canon({"schema": 2, "run_fingerprint": FP["fp3"], "round": r, "status": "complete",
                        "range_seals": [{"slot": k, "sha256": sha(b)} for k, b in zip((1, 2), bs)],
                        "games_in": sum(s["games"] for s in ss), "raw_rows_in": sum(s["rows"] for s in ss), "ids": ids,
                        "missing_ids": [], "set_aside_ids": [], "conflict_ids": [],
                        "repeat_games": sum(e["state"] == "repeat" for e in ids)})
    r1 = [e3(1, 1, "credited"), e3(1, 2, "credited"), e3(1, 3, "credited"), e3(1, 4, "noselfgame"),
          e3(2, 1, "repeat", gid3(1, 1)), e3(2, 2, "repeat", gid3(1, 2)), e3(2, 3, "credited"), e3(2, 4, "noselfgame")]
    r2 = [e3(1, 5, "credited"), e3(1, 6, "credited"), e3(1, 7, "repeat", gid3(1, 1)), e3(1, 8, "repeat", gid3(1, 2)),
          e3(2, 5, "repeat", gid3(1, 5)), e3(2, 6, "repeat", gid3(1, 6)), e3(2, 7, "repeat", gid3(1, 1)),
          e3(2, 8, "repeat", gid3(1, 2))]
    h = WORK / "k28a"
    shutil.copytree(BASE3, h)
    rc, out, m = credit(h, FP["fp3"])
    rows = sum(g[x][0] for x in ((1, 1), (1, 2), (1, 3), (2, 3), (1, 5), (1, 6)))
    check("K28a R3 (two slots, a real noselfgame, schedule 1): exit 0, 2 rounds complete, credited 6 games",
          (rc, m), (0, ("2", "2", "0", "6", str(rows), "none", "0")))
    check("K28a both credit lists byte for byte (frozen order slot, counter; slot 2 repeats slot 1; ids 4 noselfgame)",
          decided(h), {"r0001": want3(h, 1, r1), "r0002": want3(h, 2, r2)})
    rs3 = {(r, k): json.loads(zlib.decompress((h / "wire" / "ranges" / f"r{r:04d}.w{k:03d}.seal.json.zz").read_bytes()))
           for r in (1, 2) for k in (1, 2)}
    check("K28a the four range seals: schedule 1; not_done [[id 4, noselfgame]] in round 1 and [] in round 2",
          [(rs3[(r, k)]["schedule"], rs3[(r, k)]["dispositions"]["not_done"]) for r in (1, 2) for k in (1, 2)],
          [(1, [[gid3(k, 4), "noselfgame"]]) for k in (1, 2)] + [(1, [])] * 2)
    h = WORK / "k28b"
    shutil.copytree(BASE3, h)
    (h / "wire" / "ranges" / "r0001.w002.seal.json.zz").unlink()
    rc, out, m = credit(h, FP["fp3"])
    check("K28b R3 without slot 2's round-1 range seal: exit 0, WAITS round 1 naming it, nothing decided",
          (rc, m and m[0], m and m[5], decided(h)),
          (0, "0", "round 1: the range seal r0001.w002.seal.json is not at home", {}))


def main() -> int:
    t0 = time.time()
    if not (server() and base()):
        print("the fixture failed: no case can run")
    else:
        for fn in (case_f0_k1_k3_k4, case_k2, case_k7_k8_k9, case_k10_to_k13, case_k14_k15, case_k16_k17, case_k18_to_k20,
                   case_k22, case_k23, case_k24, case_k25, case_k26_k27):
            safe(fn)
        if server3() and base3():
            safe(case_k28)
        else:
            print("the fixture R3 failed: K28 cannot run")
    bad = [n for n, ok in RESULTS if not ok]
    print(f"{len(RESULTS) - len(bad)} of {len(RESULTS)} checks pass ({time.time() - t0:.0f} s)"
          + (f"; PLANT {PLANT}" if PLANT else ""))
    return 0 if RESULTS and not bad else 1


if __name__ == "__main__":
    sys.exit(main())

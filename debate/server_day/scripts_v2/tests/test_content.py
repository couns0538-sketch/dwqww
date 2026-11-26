"""test_content.py: stage a2 at home (A3d part 2, home/content.py; FORMATS 2.2) against known answers written BEFORE it
(tmp/opus_scratch/home_a2/KNOWN_ANSWERS_by_opus.md on the PC). Runs under a Python with python-chess 1.11.2.

    test_content.py <home/content.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]

The tree above home/ (home/, run/, workloads/, known/) is copied; a plant is applied to the copy's content.py only.
U  the rules replay alone (content.reserve and content.check_game of the copy) on the 13 authentic records of
   known/rules_records.txt (Astra's reference fixtures, byte for byte; their bind lines are of other runs, so each is
   bound again under this test's own fingerprint): 12 accepted, 1 noselfgame; G1 to G9 the negatives.
S  the server, from the day's REAL programs: run "cont", slot 1, piece_games 2, the list rule with N12's six openings,
   pilot range 1..6; the worker plays the six games and ends by the fence; a copy of the root is packed WITHOUT a
   converter (Z: three raw offers), the root WITH the official converter (S: three binpack offers); the published a1
   (custody.py) receipts every home before content.py judges it.
P1 to P12, P4b, P9b, P9c, X0 to X3: the pipeline cases of the known answers (D6 as CHANGED 20:37, D4 20:46, the
lost index 20:54).
PLANTS (each must make the test fail): see PLANTS below; the numbers are those of the known answers.
VERSION 2 (Opus 23 Nov; tmp/opus_scratch/content_v2/KNOWN_ANSWERS_content_v2_by_opus.md on the PC, 22:54 and 23:03,
written BEFORE the code): V1a, V1b another run's receipts (exit 3, nothing written); V2, V2b, V2c, V2d a verdict of
another run, of another seal, of another slot, not canonical; V3a, V3b, V3c, V3e an empty index, an older index put
back, another run's index (twice); V4 a receipt custody did not write; V5 drawcount 0 acts as 1 (uci.cpp 543-551);
V6a to V6e the opening rule as the worker reads it, and --convert-seconds inf; V7 no scratch folder after a WAITS.
Plants 22 to 37; plant 13 moves with the index() call. A plant whose text is not there exactly once: exit 2.
VERSION 2.1 (Opus 24 Nov; Neon 20261124T004000Z; tmp/opus_scratch/content_v21/KNOWN_ANSWERS_content_v21_by_opus.md
on the PC, written BEFORE the code): V3d, V3d2, V3d3 an index that holds rows and names no run (exit 3, content/
byte for byte as before); V3d0 the control, an index of one empty table (a crash before the first COMMIT): judged
as the base. Plant 38. P9's hand-made index carries its run row as index() writes it (00:51: R-T8 rightly refuses
version 1's form, an entry and no run).
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
    print("usage: test_content.py <home/content.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]")
    sys.exit(2)
SRC = Path(sys.argv[1]).resolve()
EXE, NET, CONV, WORK = (Path(a).resolve() for a in sys.argv[2:6])
PLANT = sys.argv[6] if len(sys.argv) > 6 else None
TREE = SRC.parent.parent
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)

REBIND = '''            _lines, _body = [], []           # PLANT 12: every bind line made the binding of its record here
            for _ln in raw.decode("ascii").split("\\n")[:-1]:
                if _ln.startswith("bind "):
                    _b = "".join(x + "\\n" for x in _body).encode("ascii")
                    _ln = "bind " + hashlib.sha256(record.TAG + self.fp.encode("ascii") + b"\\n" + _b).hexdigest()
                    _lines, _body = _lines + _body + [_ln], []
                else:
                    _body.append(_ln)
            raw = "".join(x + "\\n" for x in _lines + _body).encode("ascii")
            games = record.parse(raw, self.fp)
'''
PLANTS = {
    "plant1": ('    need(g["opening"] == moves, "the opening is not the one reserved for this id")\n',
               '    need(True, "the opening is not the one reserved for this id")\n'),
    "plant2": ('            need(r[4] == board.fen(), f"the position of row {ri - 1} is not the board\'s")\n',
               '            need(True, f"the position of row {ri - 1} is not the board\'s")\n'),
    "plant3": ('            need(abs(score) < v["evallimit"], f"row {ri - 1}\'s score is at or past evallimit")\n',
               '            need(True, f"row {ri - 1}\'s score is at or past evallimit")\n'),
    "plant4": ('            drun = drun + 1 if ply >= v["drawply"] and abs(score) <= v["drawscore"] else 0\n',
               '            drun = 0\n'),
    "plant5": ('    need(m.uci() == tok, f"{tok} is not written in standard form (home writes {m.uci()})")\n',
               '    need(True, f"{tok} is not written in standard form (home writes {m.uci()})")\n'),
    "plant6": ('    need(searches == m_ + int(extra), f"searches {searches} is not the table\'s for {reason} with {m_} moves")\n',
               '    need(True, f"searches {searches} is not the table\'s for {reason} with {m_} moves")\n'),
    "plant7": ('    need(ri == len(rows), "rows beyond the game")\n', '    need(True, "rows beyond the game")\n'),
    "plant8": ('    need(e[7] == board.fen(), "the end line\'s position is not the board\'s")\n',
               '    need(True, "the end line\'s position is not the board\'s")\n'),
    "plant9": ('        need(result == (-1 if board.turn == chess.WHITE else 1), "the mate result has the wrong sign")\n',
               '        need(result in (-1, 1), "the mate result has the wrong sign")\n'),
    "plant10": ('        if (len(raw), sha256_bytes(raw)) != (s["raw_bytes"], s["raw_sha256"]):\n', '        if False:\n'),
    "plant11": ('"ids_digest": ids.hexdigest(),', '"ids_digest": s.get("ids_digest"),'),
    "plant12": ('            games = record.parse(raw, self.fp)\n', REBIND),
    "plant13": ("                self.out.mkdir(exist_ok=True)\n"
                "                for first, second in self.index(entries, (k, i, verdict[\"seal_sha256\"])):\n"
                "                    self.conflict(first, second)\n                vp.parent.mkdir(exist_ok=True)\n"
                "                create_only(vp, canon(verdict))\n",
                "                self.out.mkdir(exist_ok=True)\n                vp.parent.mkdir(exist_ok=True)\n"
                "                create_only(vp, canon(verdict))\n"
                "                for first, second in self.index(entries, (k, i, verdict[\"seal_sha256\"])):\n"
                "                    self.conflict(first, second)\n"),
    "plant14": ('            raise Waits(f"the converter failed here, a local outage: {e}") from None\n',
                '            raise ValueError(f"the converter failed here, a local outage: {e}") from None\n'),
    "plant15": ("            if (len(wb), sha256_bytes(wb), len(data), sha256_bytes(data)) != \\\n",
                "            if False and (len(wb), sha256_bytes(wb), len(data), sha256_bytes(data)) != \\\n"),
    "plant16": ('        need(not whole and num(oe[1]) == k, "an opening end, but home\'s board has a legal move after this opening")\n',
                '        need(num(oe[1]) == k, "an opening end, but home\'s board has a legal move after this opening")\n'),
    "plant17": ("                    clashes.append((tuple(old), e))\n",
                '                    con.execute("INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?)", e)\n'),
    "plant18": ("                    self.conflict(first, second)\n", "                    pass\n"),
    "plant19": ('            if ".binpack" in files:\n', "            if False:\n"),
    "plant20": ('            raise Waits(f"the binpack does not rebuild here, a local outage (home\'s converter differs): {e}") from None\n',
                '            raise ValueError(f"the binpack does not rebuild here, a local outage (home\'s converter differs): {e}") from None\n'),
    "plant21": ('        if (not self.db.is_file() or self.db.stat().st_size == 0) and any(self.out.glob("w*/p*.verdict.json")):\n',
                "        if False:\n"),
    "plant22": ("        self.H.check_records()\n", ""),
    "plant23": ("        if run is not None and run[0] != self.fp:\n", "        if False:\n"),
    "plant24": ('                if v["seal_sha256"] != seal:\n', "                if False:\n"),
    "plant25": ("                if seen.get((k, i)) != seal:\n", "                if False:\n"),
    "plant26": ('                if isinstance(v, dict) and sorted(v) == VERDICT_KEYS and v["run_fingerprint"] != self.fp:\n',
                "                if False:\n"),
    "plant27": ('need((drun > 0 and drun >= v["drawcount"]) == last,', 'need((drun >= v["drawcount"]) == last,'),
    "plant28": ('            if type(rule["plies"]) is not int or not 0 <= rule["plies"] <= 64 \\\n',
                '            if type(rule["plies"]) is not int \\\n'),
    "plant29": ('                    or not (isinstance(rule["root_seed"], str) and re.fullmatch(r"[A-Za-z0-9_]{1,64}", rule["root_seed"])):\n',
                '                    or not isinstance(rule["root_seed"], str):\n'),
    "plant30": ("            if openings:\n", "            if False:\n"),
    "plant31": ('sorted(rule) == ["count", "kind", "sha256"] and ', ""),
    "plant32": ("not (math.isfinite(a.convert_seconds) and a.convert_seconds > 0)", "not a.convert_seconds > 0"),
    "plant33": ('        finally:\n            shutil.rmtree(self.out / "scratch" / f"w{k:03d}.{name}", ignore_errors=True)'
                '   # every exit, a WAITS too\n', ""),
    "plant34": ('            con.execute("INSERT OR REPLACE INTO judged VALUES (?, ?, ?)", judged)\n', ""),
    "plant35": ("            con.execute(\"INSERT OR IGNORE INTO meta VALUES ('run_fingerprint', ?)\", (self.fp,))\n", ""),
    "plant36": ("                    v = parse_canon(p.read_bytes(), what)\n",
                "                    v = json.loads(p.read_bytes())\n"),
    "plant37": ('                if not (isinstance(v, dict) and sorted(v) == VERDICT_KEYS and is_int(v["schema"], v["slot"], v["index"])\n',
                '                if False and not (isinstance(v, dict) and sorted(v) == VERDICT_KEYS and is_int(v["schema"], v["slot"], v["index"])\n'),
    "plant38": ("        if run is None and held:", "        if False:"),
}
CP = WORK / "tree"
for sub in ("home", "run", "workloads", "known"):
    shutil.copytree(TREE / sub, CP / sub, ignore=shutil.ignore_patterns("__pycache__"))
if PLANT:
    if PLANT not in PLANTS:
        print(f"STOP: no plant {PLANT}")
        sys.exit(2)
    old, new = PLANTS[PLANT]
    text = (CP / "home" / "content.py").read_text(encoding="ascii")
    if text.count(old) != 1:
        print(f"STOP: {PLANT}: its old text is not there exactly once")
        sys.exit(2)
    (CP / "home" / "content.py").write_text(text.replace(old, new), encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy's content.py")
RUN, CUST, CONT = CP / "run", CP / "home" / "custody.py", CP / "home" / "content.py"
sys.path.insert(0, str(RUN))
sys.path.insert(0, str(CP / "home"))
import content as C  # noqa: E402
import record as R  # noqa: E402
import worker as W  # noqa: E402

if C.chess is None or getattr(C.chess, "__version__", "") != "1.11.2":
    print("STOP: this test needs python-chess 1.11.2 (the lab's venv)")
    sys.exit(2)
chess = C.chess
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
V = C.game_values(MAN["selfgame_line"])

# ---- U: the rules replay alone --------------------------------------------------------------------------------------
RECS_PATH, RECS_SHA = CP / "known" / "rules_records.txt", "d30ef62f137a7579198f6ac1fd6134b0098f48bf2321363e6f565846089fbd20"
TFP = sha(b"test_content: the rules records' own run")
SEEDS = {6: "edge2715", 12: "edge2649"}                 # record index -> its root seed (Astra's cases.json)


def records() -> list:
    data = RECS_PATH.read_bytes()
    assert sha(data) == RECS_SHA, "known/rules_records.txt is not Astra's fixture file"
    out, cur = [], []
    for ln in data.decode("ascii").split("\n"):
        if ln:
            cur.append(ln)
            if ln.startswith("bind "):
                out.append(cur)
                cur = []
    assert not cur and len(out) == 13, "13 whole records"
    return [{"id": r[0].split(" ")[1], "opening": r[0].split(" ")[3:], "sent": r[1][5:], "rows": r[2:-2], "end": r[-2]}
            for r in out]


def parsed(rec: dict, **change) -> dict:
    x = dict(rec, **change)
    return R.parse(R.text(TFP, x["id"], x["opening"], x["sent"], x["rows"], x["end"]).encode("ascii"), TFP)[0]


def rule_of(i: int, rec: dict, seed=None) -> tuple:
    if seed or i in SEEDS:
        return {"kind": "seed", "plies": 8, "root_seed": seed or SEEDS[i]}, None
    return {"kind": "list"}, (N12 if rec["id"].startswith("n12-") else [rec["opening"]])


def judge(g: dict, rule: tuple) -> tuple:
    try:
        return C.check_game(g, C.reserve(rule[0], rule[1], g["id"], g["counter"]), V), None
    except C.SetAside as e:
        return "set_aside", str(e)


def end_line(end: str, **over) -> str:
    m = R.END.fullmatch(end)
    f = dict(zip(("result", "reason", "plies", "run", "searches", "nodes", "fen", "moves"), m.groups()))
    f["moves"] = f["moves"].split()
    f.update(over)
    return (f"sgend result {f['result']} reason {f['reason']} plies {f['plies']} run {f['run']} searches {f['searches']}"
            f" nodes {f['nodes']} fen {f['fen']} moves" + "".join(" " + x for x in f["moves"]))


def case_u():
    recs = records()
    check("U0 end_line() writes every sgend line of the records back unchanged",
          [end_line(r["end"]) == r["end"] for r in recs if r["end"].startswith("sgend ")], [True] * 12)
    states = [judge(parsed(r), rule_of(i, r)) for i, r in enumerate(recs)]
    check("U1 the 13 records: 12 accepted, the last noselfgame (Astra's openingend of edge2649)",
          states, [("accepted", None)] * 12 + [("noselfgame", None)])
    check("U2 home's seed reservation gives the records' openings: edge2715 whole (8 plies), edge2649 cut after 5",
          (C.reserve(rule_of(6, recs[6])[0], None, recs[6]["id"], 1), C.reserve(rule_of(12, recs[12])[0], None,
                                                                                    recs[12]["id"], 1)),
          ((recs[6]["opening"], True), (recs[12]["opening"], False)))
    r0, r3 = recs[0], recs[3]
    m0 = R.END.fullmatch(r0["end"])
    last_mv = r0["rows"][-1].split(" ", 4)[3]
    b = chess.Board(m0[7])
    b.push_uci(last_mv)
    moves0 = m0[8].split()
    assert r0["rows"][4].split(" ")[1:4:2] == ["12", "e1g1"] and moves0[4] == "e1g1", "n12 g1 castles at ply 12"
    row0 = r0["rows"][0].split(" ", 4)
    fen0 = row0[4].split(" ")
    rec11 = recs[11]
    b11 = chess.Board(R.END.fullmatch(rec11["end"])[7])
    m3 = R.END.fullmatch(r3["end"])
    cases = [
        ("G1 the drawadj move applied to the end position", parsed(r0, end=end_line(r0["end"], fen=b.fen())),
         rule_of(0, r0), "the end line's position is not the board's"),
        ("G1b the same move also in the end line, plies + 1",
         parsed(r0, end=end_line(r0["end"], fen=b.fen(), moves=moves0 + [last_mv], plies=str(int(m0[3]) + 1))),
         rule_of(0, r0), "searches 86 is not the table's"),
        ("G2 a row after a matescore end",
         parsed(rec11, rows=[f"sg 8 100 {sorted(x.uci() for x in b11.legal_moves)[0]} {b11.fen()}"]),
         rule_of(11, rec11), "rows beyond the game"),
        ("G3a searches + 1 (evallimit)", parsed(r3, end=end_line(r3["end"], searches=str(int(m3[5]) + 1))),
         rule_of(3, r3), "searches 129 is not the table's"),
        ("G3b the last row removed (evallimit)", parsed(r3, rows=r3["rows"][:-1]), rule_of(3, r3), "a row is missing"),
        ("G3c the last move removed from the end line, plies - 1",
         parsed(r3, end=end_line(r3["end"], moves=m3[8].split()[:-1], plies=str(int(m3[3]) - 1))),
         rule_of(3, r3), "searches 128 is not the table's"),
        ("G4a e1h1 in the row only", parsed(r0, rows=r0["rows"][:4] + [r0["rows"][4].replace(" e1g1 ", " e1h1 ", 1)]
                                            + r0["rows"][5:]), rule_of(0, r0), "e1h1 is not written in standard form"),
        ("G4b e1h1 in the end line only", parsed(r0, end=end_line(r0["end"], moves=moves0[:4] + ["e1h1"] + moves0[5:])),
         rule_of(0, r0), "row 4's move is not the move played"),
        ("G4c e1h1 in the row and in the end line",
         parsed(r0, rows=r0["rows"][:4] + [r0["rows"][4].replace(" e1g1 ", " e1h1 ", 1)] + r0["rows"][5:],
                end=end_line(r0["end"], moves=moves0[:4] + ["e1h1"] + moves0[5:])),
         rule_of(0, r0), "e1h1 is not written in standard form"),
        ("G5 n12 g2's record under the id of g1", parsed(recs[1], id="n12-w001-g00000001"), rule_of(1, recs[1]),
         "the opening is not the one reserved"),
        ("G6a a row score of 2000 (= evallimit)",
         parsed(r0, rows=[" ".join(row0[:2] + ["2000"] + row0[3:])] + r0["rows"][1:]), rule_of(0, r0),
         "score is at or past evallimit"),
        ("G6b the end line's run 7 (drawadj)", parsed(r0, end=end_line(r0["end"], run="7")), rule_of(0, r0),
         "the end line's run 7 is not the draw counter 8"),
        ("G6c result 1 on the stalemate", parsed(recs[7], end=end_line(recs[7]["end"], result="1")),
         rule_of(7, recs[7]), "a stalemate ending with a win"),
        ("G6d the openingend record of edge2649 under seed edge2715", parsed(recs[12]),
         rule_of(12, recs[12], seed="edge2715"), "the opening is not the one reserved"),
        ("G7 row 0's position with its halfmove clock + 1",
         parsed(r0, rows=[" ".join(row0[:4] + [" ".join(fen0[:4] + [str(int(fen0[4]) + 1)] + fen0[5:])])]
                + r0["rows"][1:]), rule_of(0, r0), "the position of row 0 is not the board's"),
        ("G8 the mate of edge2715 with result 1 (White is mated)", parsed(recs[6], end=end_line(recs[6]["end"],
                                                                                               result="1")),
         rule_of(6, recs[6]), "the mate result has the wrong sign"),
        ("G9 n12 g3 written as an opening end", parsed(recs[2], sent="none", rows=[],
                                                       end="openingend plies 8 reason nomoves"),
         rule_of(2, recs[2]), "an opening end, but home's board has a legal move"),
    ]
    for name, g, rule, key in cases:
        st, why = judge(g, rule)
        check(f"{name}: set_aside, naming the check", (st, key in (why or "")), ("set_aside", True))
        print(f"     why: {why}")


# ---- S: the server and the homes -----------------------------------------------------------------------------------
NOW = time.time()
SRV, SRVZ = WORK / "srv", WORK / "srvz"
ROWS = [104, 112, 477]                                  # p0 = g1 g2 (28 + 76), p1 = g3 g4 (0 + 112), p2 = g5 g6 (256 + 221)
FP = {}
CUST_COUNTS = re.compile(r"custody: RECEIVED (\d+) pieces (\d+) rows; C1 (\d+) pieces")
COUNTS = re.compile(r"content: judged (\d+) pieces \((\d+) refused\); accepted (\d+) games (\d+) rows; "
                    r"noselfgame (\d+); set_aside (\d+); waits (\d+); conflicts (\d+)")


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


def packer(root: Path, conv: Path) -> int:
    return subprocess.run([sys.executable, "-I", "-B", str(RUN / "packer.py"), "--root", str(root), "--converter",
                           str(conv), "--once"], capture_output=True, text=True, timeout=600).returncode


def forms(root: Path) -> list:
    return [json.loads((root / "out" / "w001" / f"p{i:06d}.offer.json").read_bytes())["form"] for i in range(3)
            if (root / "out" / "w001" / f"p{i:06d}.offer.json").exists()]


def server() -> bool:
    put(SRV / "RUN.json", W.canon({
        "schema": 2, "run": "cont", "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
        "hard_cutoff_utc": T(NOW + 86400), "boot_id": W.boot_id(), "instance": "test-instance", "package": "0" * 64,
        "engine_sha256": sha(EXE.read_bytes()), "net_sha256": MAN["net_sha256"],
        "options_sha256": sha("".join(ln + "\n" for ln in MAN["options"]).encode("ascii")),
        "game_line": MAN["selfgame_line"], "opening_rule": {"kind": "list", "sha256": sha(OPENINGS.read_bytes()),
                                                             "count": len(N12)},
        "slots": [1], "piece_games": 2, "pilot_ranges": [{"slot": 1, "round": 1, "first": 1, "last": 6,
                                                           "short": False, "schedule": 0}]}))
    FP["fp"] = fp = sha((SRV / "RUN.json").read_bytes())
    FP["header"] = json.loads((SRV / "RUN.json").read_bytes())
    rc, out = play_until("r0001.w001.seal.json", lambda: put(SRV / "FENCE.json", W.canon({
        "at_utc": T(time.time()), "cutoff_utc": FP["header"]["hard_cutoff_utc"], "run_fingerprint": fp, "schema": 2,
        "why": "D"})))
    closed = SRV / "w001" / "closed"
    seals = [json.loads((closed / f"p{i:06d}.seal.json").read_bytes()) for i in range(3)
             if (closed / f"p{i:06d}.seal.json").exists()]
    if not check("server: exit 0, pieces of 104, 112, 477 rows, epoch 1, round 1, schedule 0",
                 (rc, [s["rows"] for s in seals], [(s["epoch"], s["round"], s["schedule"]) for s in seals]),
                 (0, ROWS, [(1, 1, 0)] * 3)):
        print(out)
        return False
    shutil.copytree(SRV, SRVZ)
    return check("server: the packer exit 0 twice: S three binpack offers, Z (no converter) three raw offers",
                 (packer(SRV, CONV), forms(SRV), packer(SRVZ, WORK / "no_converter.exe"), forms(SRVZ)),
                 (0, ["binpack"] * 3, 0, ["raw"] * 3))


def fetch(home: Path, srv: Path) -> None:
    for p in sorted(srv.glob("*.zz")):
        put(home / "wire" / p.name, p.read_bytes())
    for p in sorted((srv / "ranges").glob("*.zz")):
        put(home / "wire" / "ranges" / p.name, p.read_bytes())
    src, dst = srv / "out" / "w001", home / "wire" / "out" / "w001"
    for i in range(3):
        o = json.loads(zlib.decompress((src / f"p{i:06d}.offer.json.zz").read_bytes()))
        for m in o["members"]:
            put(dst / m["wire_name"], (src / m["wire_name"]).read_bytes())
        put(dst / f"p{i:06d}.offer.json.zz", (src / f"p{i:06d}.offer.json.zz").read_bytes())   # LAST, as a fetch does


def custody(home: Path) -> bool:
    p = subprocess.run([sys.executable, "-I", "-B", str(CUST), "--home", str(home), "--fingerprint", FP["fp"]],
                       capture_output=True, text=True, timeout=300)
    m = CUST_COUNTS.search(p.stdout)
    return check(f"a1 on {home.name}: exit 0, RECEIVED 3 pieces", (p.returncode, m and m[1]), (0, "3"))


def new_home(name: str, srv: Path = SRV, receipts: bool = True) -> Path:
    h = WORK / name
    fetch(h, srv)
    if receipts:
        custody(h)
    return h


def content(home: Path, conv=None, openings=True, fp=None, extra=()) -> tuple:
    cmd = [sys.executable, "-I", "-B", str(CONT), "--home", str(home), "--fingerprint", fp or FP["fp"], "--converter",
           str(conv or CONV)] + (["--openings", str(OPENINGS if openings is True else openings)] if openings else []) \
        + list(extra)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    out = (p.stdout + p.stderr).strip()
    m = COUNTS.fullmatch(out.splitlines()[-1]) if out else None
    return p.returncode, out, (tuple(int(x) for x in m.groups()) if m else None)


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


def expected() -> tuple:
    """The verdicts (bytes by name) and index entries the known answers give, from the SERVER's own raw pieces."""
    want, entries = {}, []
    for i in range(3):
        sb = (SRV / "w001" / "closed" / f"p{i:06d}.seal.json").read_bytes()
        games = R.parse((SRV / "w001" / "closed" / f"p{i:06d}.raw").read_bytes(), FP["fp"])
        gs = [{"game": g["id"], "rows": len(g["rows"]), "rows_digest": R.rows_digest(g["rows"], g["end"]),
               "state": "accepted", "why": None} for g in games]
        want[f"p{i:06d}.verdict.json"] = W.canon({"schema": 2, "run_fingerprint": FP["fp"], "slot": 1, "index": i,
                                                  "seal_sha256": sha(sb), "round": 1, "piece": "judged", "why": None,
                                                  "games": gs})
        entries += [(1, g["counter"], 1, g["id"], f"w001/p{i:06d}", "accepted", x["rows_digest"], g["bind"])
                    for g, x in zip(games, gs)]
    return want, entries


def only(want: dict, *names) -> dict:
    return {k: v for k, v in want.items() if k in names}


def zz_rewrite(path: Path, fn) -> None:
    put(path, zlib.compress(W.canon(fn(json.loads(zlib.decompress(path.read_bytes())))), 6))


def reforge(home: Path, changes: dict) -> None:
    """Seals changed as `changes` says ({index: {field: value}}), every later prev_seal linked again, the seal's wire
    copy and the offer rewritten, so that a1 receipts the forged pieces (a test helper, before a1 runs)."""
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


def raw_forge(home: Path, fn) -> bytes:
    """p1's raw piece (raw form) changed by fn, its .zz and the offer's raw member made to fit."""
    d = home / "wire" / "out" / "w001"
    raw2 = fn(zlib.decompress((d / "p000001.raw.zz").read_bytes()))
    zz = zlib.compress(raw2, 6)
    put(d / "p000001.raw.zz", zz)

    def fix(o):
        assert o["members"][1]["name"] == "p000001.raw.zz"
        o["members"][1].update(bytes=len(zz), sha256=sha(zz), wire_bytes=len(zz), wire_sha256=sha(zz))
        return o
    zz_rewrite(d / "p000001.offer.json.zz", fix)
    return raw2


# ---- the pipeline cases ---------------------------------------------------------------------------------------------
def case_p1_to_p4():
    want, entries = expected()
    h = new_home("s")
    rc, out, c = content(h)
    check("P1 S home: exit 0, judged 3 (0 refused), accepted 6 games 693 rows, nothing set aside or waiting",
          (rc, c, out.splitlines()[:-1]), (0, (3, 0, 6, 693, 0, 0, 0, 0), []))
    check("P1 the three verdicts, byte for byte as the known answers (rows 28 76 0 112 256 221, the server's digests)",
          verdicts(h), want)
    check("P2 the index: 6 entries, g3 with a null digest, each with its state and bind", index_rows(h), entries)
    time.sleep(1.1)
    rc, out, c = content(h)
    check("P3 a second pass: exit 0, the same counts, the verdicts and the index unchanged",
          (rc, c, out.splitlines()[:-1], verdicts(h), index_rows(h)),
          (0, (3, 0, 6, 693, 0, 0, 0, 0), [], want, entries))
    (h / "content" / "w001" / "p000001.verdict.json").unlink()
    rc, out, c = content(h)
    check("P4 p1's verdict removed: a pass writes the same bytes again, still 6 entries",
          (rc, c, verdicts(h), index_rows(h)), (0, (3, 0, 6, 693, 0, 0, 0, 0), want, entries))


def case_p4b():
    want, entries = expected()
    h = new_home("s4b")
    blocker = h / "content" / "w001" / "p000001.verdict.json.tmp"
    blocker.mkdir(parents=True)
    rc, out, c = content(h)
    check("P4b p1's verdict cannot be written: exit 4, STOP (4), p0's verdict only, the index holds p1's entries (4)",
          (rc, out.splitlines()[-1].startswith("content: STOP (4)"), sorted(verdicts(h)), index_rows(h)),
          (4, True, ["p000000.verdict.json"], [e for e in entries if e[1] <= 4]))
    blocker.rmdir()
    rc, out, c = content(h)
    check("P4b the folder removed: exit 0, p1's and p2's verdicts as P1's, 6 entries",
          (rc, c, verdicts(h), index_rows(h)), (0, (3, 0, 6, 693, 0, 0, 0, 0), want, entries))


def case_p5_p6_p7():
    want, entries = expected()
    z = new_home("z", SRVZ)
    rc, out, c = content(z)
    check("P5 Z home (raw offers): exit 0, the same verdicts as S's byte for byte, the same index",
          (rc, c, verdicts(z), index_rows(z)), (0, (3, 0, 6, 693, 0, 0, 0, 0), want, entries))
    h = new_home("s6")
    rc, out, c = content(h, conv=WORK / "no_converter.exe")
    check("P6 the converter missing: exit 0, waits 3 (a local outage), no verdict, no index entry",
          (rc, c, sum("the converter failed here" in ln for ln in out.splitlines()), verdicts(h), index_rows(h)),
          (0, (0, 0, 0, 0, 0, 0, 3, 0), 3, {}, []))
    rc, out, c = content(h)
    check("P6 then with the converter: the three verdicts as P1's", (rc, c, verdicts(h)),
          (0, (3, 0, 6, 693, 0, 0, 0, 0), want))
    h = new_home("s7")
    p = h / "wire" / "out" / "w001" / "p000001.binpack"
    b = bytearray(p.read_bytes())
    b[len(b) // 2] ^= 0x01
    put(p, bytes(b))
    rc, out, c = content(h)
    check("P7 a kept member changed after a1: WAITS for p1 naming its kept bytes, p0 and p2 judged",
          (rc, c, "WAITS w001/p000001: the kept member p000001.binpack is not the bytes of its receipt" in out,
           sorted(verdicts(h))),
          (0, (2, 0, 4, 581, 0, 0, 1, 0), True, ["p000000.verdict.json", "p000002.verdict.json"]))


def refused_case(name: str, forge, key: str, prefix: bool = False):
    h = new_home(name, SRVZ, receipts=False)
    forge(h)
    custody(h)
    rc, out, c = content(h)
    v = json.loads(verdicts(h).get("p000001.verdict.json", b"{}"))
    why = v.get("why") or ""
    check(f"{name}: exit 0, judged 3 (1 refused), accepted 4 games 581 rows; p1 refused, no game, the why names it",
          (rc, c, v.get("piece"), v.get("games"), why.startswith(key) if prefix else key in why),
          (0, (3, 1, 4, 581, 0, 0, 0, 0), "refused", [], True))
    print(f"     why: {why}")


def flip_ply(raw: bytes) -> bytes:
    i = raw.index(b"\nsg 8 ") + 4
    return raw[:i] + b"9" + raw[i + 1:]


def flip_bind(raw: bytes) -> bytes:
    i = raw.index(b"\nbind ", raw.index(b"\nbind ") + 1) + 6
    return raw[:i] + (b"0" if raw[i:i + 1] != b"0" else b"1") + raw[i + 1:]


def case_p8():
    refused_case("P8a", lambda h: raw_forge(h, flip_ply), "transport", prefix=True)
    refused_case("P8b", lambda h: reforge(h, {1: {"rows": 128}}), "the seal's fields do not describe its bytes: rows")
    refused_case("P8c", lambda h: reforge(h, {1: {"raw_sha256": sha(raw_forge(h, flip_bind))}}), "records: binding",
                 prefix=True)
    refused_case("P8d", lambda h: reforge(h, {1: {"ids_digest": "0" * 64}}), "ids_digest")


def case_p9():
    want, entries = expected()
    games = R.parse((SRV / "w001" / "closed" / "p000001.raw").read_bytes(), FP["fp"])
    g4 = [g for g in games if g["counter"] == 4][0]
    planted = (1, 4, 1, "cont-w001-g00000004", "w001/p000009", "accepted", "f" * 64, "f" * 64)
    second = {"piece": "w001/p000001", "seal_sha256": sha((SRV / "w001" / "closed" / "p000001.seal.json").read_bytes()),
              "state": "accepted", "rows_digest": R.rows_digest(g4["rows"], g4["end"]), "bind": g4["bind"]}

    def rec(first_digest):
        return W.canon({"schema": 2, "run_fingerprint": FP["fp"], "game": "cont-w001-g00000004",
                        "how": "two records under one id",
                        "first": {"piece": "w001/p000009", "seal_sha256": None, "state": "accepted",
                                  "rows_digest": first_digest, "bind": "f" * 64}, "second": second})
    h = new_home("s9")
    (h / "content").mkdir()
    con = sqlite3.connect(h / "content" / "equal.sqlite")
    con.execute("CREATE TABLE entries (slot INTEGER, counter INTEGER, round INTEGER, game TEXT, piece TEXT, state TEXT, "
                "rows_digest TEXT, bind TEXT, PRIMARY KEY (slot, counter))")
    con.execute("INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?, ?)", planted)
    con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")     # as index() makes it (2.1, R-T8)
    con.execute("INSERT INTO meta VALUES ('run_fingerprint', ?)", (FP["fp"],))
    con.commit()
    con.close()
    kept = [e if e[1] != 4 else planted for e in entries]
    cdir = h / "conflicts"
    one, two = cdir / "cont-w001-g00000004.json", cdir / "cont-w001-g00000004.2.json"

    def read(p):
        return p.read_bytes() if p.is_file() else None
    rc, out, c = content(h)
    check("P9 another record under (1, 4) in the index: exit 0, conflicts 1, the three verdicts as P1's, the index "
          "keeps the planted entry, one CONFLICT line",
          (rc, c, verdicts(h), index_rows(h),
           sum(ln.startswith("CONFLICT cont-w001-g00000004:") for ln in out.splitlines())),
          (0, (3, 0, 6, 693, 0, 0, 0, 1), want, kept, 1))
    check("P9 the conflict record: first the planted entry (no receipt: seal null), second p1's g4 with its seal",
          read(one), rec("f" * 64))
    rc, out, c = content(h)
    check("P9 a second pass: exit 0, nothing judged again, the record unchanged, conflicts 1",
          (rc, c, out.splitlines()[:-1], read(one)), (0, (3, 0, 6, 693, 0, 0, 0, 1), [], rec("f" * 64)))
    (h / "content" / "w001" / "p000001.verdict.json").unlink()
    one.unlink()
    rc, out, c = content(h)
    check("P9b p1's verdict and the record removed: the pass finds the conflict again, the same bytes, conflicts 1",
          (rc, c, read(one), verdicts(h), index_rows(h)), (0, (3, 0, 6, 693, 0, 0, 0, 1), rec("f" * 64), want, kept))
    con = sqlite3.connect(h / "content" / "equal.sqlite")
    con.execute("UPDATE entries SET rows_digest = ? WHERE slot = 1 AND counter = 4", ("d" * 64,))
    con.commit()
    con.close()
    (h / "content" / "w001" / "p000001.verdict.json").unlink()
    rc, out, c = content(h)
    check("P9c the first entry changed, p1 judged again: conflicts 2, the first record unchanged, the second name "
          "holds the new pair",
          (rc, c, sorted(p.name for p in cdir.iterdir()), read(one), read(two)),
          (0, (3, 0, 6, 693, 0, 0, 0, 2), ["cont-w001-g00000004.2.json", "cont-w001-g00000004.json"], rec("f" * 64),
           rec("d" * 64)))


STOPPER = """import os, sqlite3, sys
con = sqlite3.connect(sys.argv[1], isolation_level=None)
con.execute("BEGIN IMMEDIATE")
con.execute("INSERT INTO entries VALUES (1, 99, 1, 'cont-w001-g00000099', 'w001/p000009', 'accepted', ?, ?)",
            ("e" * 64, "e" * 64))
os._exit(0)
"""


def case_p10():
    want, entries = expected()
    h = new_home("s10")
    rc, out, c = content(h)
    stopper = WORK / "stopper.py"
    stopper.write_text(STOPPER, encoding="ascii")
    p = subprocess.run([sys.executable, "-I", "-B", str(stopper), str(h / "content" / "equal.sqlite")],
                       capture_output=True, text=True, timeout=60)
    journal = (h / "content" / "equal.sqlite-journal").exists()
    (h / "content" / "w001" / "p000001.verdict.json").unlink()
    rc2, out2, c2 = content(h)
    check("P10 a process stopped inside an index transaction (its journal left): the next pass exit 0, P1's 6 entries "
          "without the stopped one, p1's verdict as P1's",
          (rc, p.returncode, p.stderr, journal, rc2, c2, index_rows(h), verdicts(h)),
          (0, 0, "", True, 0, (3, 0, 6, 693, 0, 0, 0, 0), entries, want))


CONV_SCORE = """import re, subprocess, sys
from pathlib import Path
text = sys.stdin.read()
p = subprocess.run([@@REAL@@], input=text.encode("ascii"))
dst = Path(text.split()[2])
data = dst.read_bytes()
m = re.search(rb"(?m)^score (-?[0-9]+)", data)
dst.write_bytes(data[:m.start()] + b"score " + str(int(m[1]) + 1).encode("ascii") + data[m.end():])
sys.exit(p.returncode)
"""
CONV_GARBAGE = """import sys
from pathlib import Path
Path(sys.stdin.read().split()[2]).write_bytes(b"not a plain text\\n")
"""


def case_p11():
    want, entries = expected()
    h = new_home("s11")
    score, garbage = WORK / "conv_score.py", WORK / "conv_garbage.py"
    score.write_text(CONV_SCORE.replace("@@REAL@@", repr(str(CONV))), encoding="ascii")
    garbage.write_text(CONV_GARBAGE, encoding="ascii")
    for name, conv in (("P11a a converter that changes one score of its text", score),
                       ("P11b a converter that writes no plain text and ends 0", garbage)):
        rc, out, c = content(h, conv=conv)
        waits = [ln for ln in out.splitlines() if ln.startswith("WAITS ")]
        check(f"{name}: exit 0, waits 3, each naming 'does not rebuild here', no verdict, no index entry",
              (rc, c, len(waits), all("does not rebuild here" in ln for ln in waits), verdicts(h), index_rows(h)),
              (0, (0, 0, 0, 0, 0, 0, 3, 0), 3, True, {}, []))
        print(f"     {waits[0] if waits else out[-300:]}")
    rc, out, c = content(h)
    check("P11c then the official converter: P1's three verdicts and index, conflicts 0",
          (rc, c, verdicts(h), index_rows(h)), (0, (3, 0, 6, 693, 0, 0, 0, 0), want, entries))


def case_p12():
    want, entries = expected()
    h = new_home("s12")
    rc, out, c = content(h)
    (h / "content" / "equal.sqlite").unlink()
    (h / "content" / "w001" / "p000002.verdict.json").unlink()
    rc2, out2, c2 = content(h)
    check("P12 the index and p2's verdict removed: exit 4 naming the lost index, no index made, no p2 verdict",
          (rc, rc2, out2.splitlines()[-1].startswith("content: STOP (4): content/equal.sqlite is gone"),
           (h / "content" / "equal.sqlite").exists(), sorted(verdicts(h))),
          (0, 4, True, False, ["p000000.verdict.json", "p000001.verdict.json"]))
    (h / "content").rename(h / "content.lost")
    rc3, out3, c3 = content(h)
    check("P12 content/ moved aside: a pass judges again, P1's verdicts byte for byte and P2's 6 entries",
          (rc3, c3, verdicts(h), index_rows(h)), (0, (3, 0, 6, 693, 0, 0, 0, 0), want, entries))


def case_x():
    x0 = WORK / "x0"
    x0.mkdir()
    rc, out, c = content(x0)
    check("X0 no RUN.json.zz at home: exit 0, nothing to do",
          (rc, out.splitlines()[-1]), (0, "content: no wire/RUN.json.zz at home yet: nothing to do"))
    x1 = WORK / "x1"
    line = FP["header"]["game_line"]
    assert " drawply 80 " in line and " writeminply 8 " in line
    hb = W.canon(dict(FP["header"], game_line=line.replace(" drawply 80 ", " drawply 7 ")))
    put(x1 / "wire" / "RUN.json.zz", zlib.compress(hb, 6))
    rc, out, c = content(x1, fp=sha(hb))
    check("X1 game_line with drawply 7 (below writeminply 8): exit 3, nothing written",
          (rc, (x1 / "content").exists()), (3, False))
    x2 = new_home("x2")
    rc, out, c = content(x2, openings=None)
    check("X2 the list rule and no --openings: exit 3, nothing written", (rc, (x2 / "content").exists()), (3, False))
    plus = WORK / "openings_plus.txt"
    plus.write_bytes(OPENINGS.read_bytes() + b"\n")
    rc, out, c = content(x2, openings=plus)
    check("X3 --openings with one byte more: exit 3, nothing written", (rc, (x2 / "content").exists()), (3, False))


# ---- VERSION 2 (KNOWN_ANSWERS_content_v2_by_opus.md, 22:54 and 23:03) ----------------------------------------------
def header_b() -> tuple:
    hb = W.canon(dict(FP["header"], run="contb"))
    return hb, sha(hb)


def judged_copy(name: str) -> Path:
    base = WORK / "v_base"
    if not base.exists():
        new_home("v_base")
        rc, out, c = content(base)
        check("V0 the base home of the V cases: exit 0, judged as P1", (rc, c), (0, (3, 0, 6, 693, 0, 0, 0, 0)))
    h = WORK / name
    shutil.copytree(base, h)
    return h


def stop_line(out: str, code: int, rel: str) -> bool:
    last = out.splitlines()[-1] if out else ""
    return last.startswith(f"content: STOP ({code}):") and rel in last


def case_v1():
    hb, fpb = header_b()
    h = new_home("v1a")
    put(h / "wire" / "RUN.json.zz", zlib.compress(hb, 6))
    rc, out, c = content(h, fp=fpb)
    check("V1a run A's receipts under header B (another run in a reused home): exit 3 naming p0's receipt, no content/",
          (rc, stop_line(out, 3, "custody/w001/p000000.receipt.json"), (h / "content").exists()), (3, True, False))
    h = new_home("v1b")
    r = json.loads((h / "custody" / "w001" / "p000000.receipt.json").read_bytes())
    put(h / "custody" / "w001" / "p000005.receipt.json", W.canon(dict(r, run_fingerprint=fpb, index=5)))
    rc, out, c = content(h)
    check("V1b A's receipts and one of run B at p000005: exit 3 naming it, nothing judged (no content/)",
          (rc, stop_line(out, 3, "custody/w001/p000005.receipt.json"), (h / "content").exists()), (3, True, False))


def case_v2():
    rel = "content/w001/p000001.verdict.json"

    def one(name, fn, want):
        h = judged_copy(name.split()[0])
        p = h / "content" / "w001" / "p000001.verdict.json"
        fn(p, json.loads(p.read_bytes()))
        rc, out, c = content(h)
        check(f"{name}: exit {want}, the STOP line names {rel}", (rc, stop_line(out, want, rel)), (want, True))
    one("V2 p1's verdict of another run (run_fingerprint b x 64)",
        lambda p, v: put(p, W.canon(dict(v, run_fingerprint="b" * 64))), 3)
    one("V2b p1's verdict with seal_sha256 c x 64, the index untouched",
        lambda p, v: put(p, W.canon(dict(v, seal_sha256="c" * 64))), 4)
    one("V2c p1's verdict with slot 2", lambda p, v: put(p, W.canon(dict(v, slot=2))), 4)
    one("V2d p1's verdict written with spaces (not canonical)",
        lambda p, v: put(p, (json.dumps(v, sort_keys=True, indent=1) + "\n").encode("ascii")), 4)


def case_v3():
    def sql(h, *stmts):
        con = sqlite3.connect(h / "content" / "equal.sqlite")
        for s, args in stmts:
            con.execute(s, args)
        con.commit()
        con.close()
    h = judged_copy("V3a")
    (h / "content" / "equal.sqlite").unlink()
    sql(h, ("CREATE TABLE entries (slot INTEGER, counter INTEGER, round INTEGER, game TEXT, piece TEXT, state TEXT, "
            "rows_digest TEXT, bind TEXT, PRIMARY KEY (slot, counter))", ()))
    rc, out, c = content(h)
    check("V3a P1's home with an index of no row (Astra's 0-row index): exit 4 naming p0's verdict",
          (rc, stop_line(out, 4, "content/w001/p000000.verdict.json")), (4, True))
    h = new_home("v3b")
    keep, wo = WORK / "v3b_keep", h / "wire" / "out" / "w001"
    keep.mkdir()
    for i in (1, 2):
        os.replace(wo / f"p{i:06d}.binpack", keep / f"p{i:06d}.binpack")
    rc1, out1, c1 = content(h)
    shutil.copy2(h / "content" / "equal.sqlite", keep / "equal.sqlite")
    for i in (1, 2):
        os.replace(keep / f"p{i:06d}.binpack", wo / f"p{i:06d}.binpack")
    rc2, out2, c2 = content(h)
    shutil.copy2(keep / "equal.sqlite", h / "content" / "equal.sqlite")
    rc3, out3, c3 = content(h)
    check("V3b p0 judged (p1, p2 WAIT), the index copied aside, p1 and p2 judged, the older index put back: exit 4 "
          "naming p1's verdict",
          (rc1, c1, rc2, c2, rc3, stop_line(out3, 4, "content/w001/p000001.verdict.json")),
          (0, (1, 0, 2, 104, 0, 0, 2, 0), 0, (3, 0, 6, 693, 0, 0, 0, 0), 4, True))
    h = judged_copy("V3c")
    sql(h, ("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)", ()),
        ("INSERT OR REPLACE INTO meta VALUES ('run_fingerprint', ?)", ("b" * 64,)))
    rc, out, c = content(h)
    check("V3c P1's home, the index's run row b x 64 (another run's index): exit 3 naming equal.sqlite",
          (rc, stop_line(out, 3, "content/equal.sqlite")), (3, True))
    hb, fpb = header_b()
    h = WORK / "v3e"
    put(h / "wire" / "RUN.json.zz", zlib.compress(hb, 6))
    put(h / "content" / "equal.sqlite", (WORK / "v_base" / "content" / "equal.sqlite").read_bytes())
    rc, out, c = content(h, fp=fpb)
    check("V3e header B and run A's judged index, no receipts: exit 3 naming equal.sqlite",
          (rc, stop_line(out, 3, "content/equal.sqlite")), (3, True))


def case_v3d():
    """R-T8 (Neon 004000Z): an index that holds rows and names no run: exit 3, content/ byte for byte as before.
    V3d0, the control: an index of one empty table (a crash before the first COMMIT of index()) is this run's."""
    def sql(h, *stmts):
        con = sqlite3.connect(h / "content" / "equal.sqlite")
        for s in stmts:
            con.execute(s)
        con.commit()
        con.close()

    def tree(h):
        return {str(p.relative_to(h)): p.read_bytes() for p in sorted((h / "content").rglob("*")) if p.is_file()}

    def no_verdicts(h):
        for p in (h / "content").glob("w*/p*.verdict.json"):
            p.unlink()

    def one(name, what, prep):
        h = judged_copy(name)
        prep(h)
        before = tree(h)
        rc, out, c = content(h)
        check(f"{name} {what}: exit 3 naming content/equal.sqlite; content/ byte for byte as before",
              (rc, stop_line(out, 3, "content/equal.sqlite"), tree(h) == before), (3, True, True))
    one("V3d", "P1's judged home, the meta row deleted (the table stays)", lambda h: sql(h, "DELETE FROM meta"))
    one("V3d2", "the meta table dropped and every verdict removed (a version-1 index of another run)",
        lambda h: (sql(h, "DROP TABLE meta"), no_verdicts(h)))
    one("V3d3", "the meta row and every entry deleted (judged rows only)",
        lambda h: sql(h, "DELETE FROM meta", "DELETE FROM entries"))
    h = judged_copy("V3d0")
    no_verdicts(h)
    (h / "content" / "equal.sqlite").unlink()
    sql(h, "CREATE TABLE entries (slot INTEGER, counter INTEGER, round INTEGER, game TEXT, piece TEXT, state TEXT, "
           "rows_digest TEXT, bind TEXT, PRIMARY KEY (slot, counter))")
    rc, out, c = content(h)
    con = sqlite3.connect(h / "content" / "equal.sqlite")
    try:
        run = con.execute("SELECT value FROM meta WHERE key = 'run_fingerprint'").fetchone()
    finally:
        con.close()
    check("V3d0 control: every verdict removed, an index of the empty entries table only: exit 0, judged as the base, "
          "the index then names this run", (rc, c, run), (0, (3, 0, 6, 693, 0, 0, 0, 0), (FP["fp"],)))


def case_v4():
    h = new_home("v4")
    p = h / "custody" / "w001" / "p000000.receipt.json"
    put(p, W.canon(dict(json.loads(p.read_bytes()), kept="wire/out/w002")))
    rc, out, c = content(h)
    check("V4 p0's receipt with kept wire/out/w002 (not as custody writes it): exit 4 naming it, no content/",
          (rc, stop_line(out, 4, "custody/w001/p000000.receipt.json"), (h / "content").exists()), (4, True, False))


def case_v5():
    recs = records()

    def states(dc):
        out = []
        for i, r in enumerate(recs):
            g, rule = parsed(r), rule_of(i, r)
            try:
                out.append((C.check_game(g, C.reserve(rule[0], rule[1], g["id"], g["counter"]), dict(V, drawcount=dc)),
                            None))
            except C.SetAside as e:
                out.append(("set_aside", str(e)))
        return out
    one = states(1)
    check("V5 control: under drawcount 1 at least one record is accepted", any(s == "accepted" for s, w in one), True)
    check("V5 the 13 records judged under drawcount 0 and under 1: the same (state, why) record by record "
          "(uci.cpp 543-551: the run is compared only after a ply that qualified, so 0 acts as 1)", states(0), one)


def case_v6():
    def rule_home(name, rule, openings):
        h = WORK / name
        hb = W.canon(dict(FP["header"], opening_rule=rule))
        put(h / "wire" / "RUN.json.zz", zlib.compress(hb, 6))
        rc, out, c = content(h, fp=sha(hb), openings=openings)
        return rc, (h / "content").exists()
    seed = {"kind": "seed", "plies": 8, "root_seed": "edge2715"}
    for name, rule, openings, want in (
            ("V6a the seed rule with plies -5", dict(seed, plies=-5), None, 3),
            ('V6b the seed rule with root_seed "bad seed!"', dict(seed, root_seed="bad seed!"), None, 3),
            ("V6c a valid seed rule WITH --openings", seed, True, 2),
            ("V6c0 control: the same rule without --openings", seed, None, 0),
            ("V6d the list rule with an extra key x", dict(FP["header"]["opening_rule"], x=1), True, 3)):
        check(f"{name}: exit {want}, nothing written", rule_home(name.split()[0], rule, openings), (want, False))
    h = WORK / "v6e"
    h.mkdir()
    check("V6e --convert-seconds inf: exit 2", content(h, extra=["--convert-seconds", "inf"])[0], 2)


def case_v7():
    h = new_home("v7")
    rc, out, c = content(h, conv=WORK / "no_converter.exe")
    sc = h / "content" / "scratch"
    check("V7 the converter missing (P6): waits 3, and content/scratch holds nothing after the pass",
          (rc, c, sorted(p.name for p in sc.iterdir()) if sc.is_dir() else []), (0, (0, 0, 0, 0, 0, 0, 3, 0), []))


def main() -> int:
    t0 = time.time()
    safe(case_u)
    safe(case_v5)
    if not server():
        print("the server side failed: no pipeline case can run")
    else:
        for fn in (case_p1_to_p4, case_p4b, case_p5_p6_p7, case_p8, case_p9, case_p10, case_p11, case_p12,
                   case_x, case_v1, case_v2, case_v3, case_v3d, case_v4, case_v6, case_v7):
            safe(fn)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"{len(RESULTS) - len(bad)} of {len(RESULTS)} checks pass ({time.time() - t0:.0f} s)"
          + (f"; PLANT {PLANT}" if PLANT else ""))
    return 0 if RESULTS and not bad else 1


if __name__ == "__main__":
    sys.exit(main())

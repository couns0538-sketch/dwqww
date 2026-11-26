"""test_publish.py: stage b part 2 at home (home/publish.py; FORMATS 2.3, 2.4) against known answers written BEFORE it
(tmp/opus_scratch/home_b2/KNOWN_ANSWERS_b2_by_opus.md on the PC). Runs under a Python with python-chess 1.11.2.

    test_publish.py <home/publish.py> <engine exe> <net file> <converter exe> <the loop's config> <the folder holding
                    nnloop/> <a Syzygy folder> <a NEW folder> [plantN]

The config, the loop's code and the Syzygy folder are only READ; the tables a case uses are COPIED into the new folder
(a case removes or changes files only in its own copy). The tree above home/ (home/, run/, workloads/, known/) is
copied; a plant is applied to the copy's publish.py only.
R2  the server from the day's REAL programs, as test_credit.py builds it: run "pub", slot 1, piece_games 2, the list
    rule with N12's six openings, pilot ranges round 1 = 1..4 and round 2 = 5..12; worker, fence, packer with the
    official converter, a1 (custody.py) and a2 (content.py) at home (BASE), then credit.py on a copy (BASEC).
FP  the fixture's own control: credit decided rounds 1 and 2 complete; ids 1, 2, 4, 5, 6 are the credited games with
    rows; the after-game rules can touch exactly two of them (P1, 25 Nov): game 4 ends drawn by the draw
    adjudication in 8/4K3/8/2p5/5B2/7k/8/8 b - - 0 60 (KBvKP), game 5 by the fifty-move rule in
    8/8/k7/8/8/5B2/1b6/5K2 w - - 100 133 (KBvKB); none can be left out by the ply-limit rule. The loop's rule
    (nnloop/datagen_uci.py lines 336 to 339: result 0 and adjudicate_bare_king or adjudicate_tablebase; publish's
    draw_adjudicated is reason drawadj AND the game line's drawcount > 0, 8 here) probes WDL twice for each game: its
    end with the clock set to 0, and its start after the last capture or pawn move. All four are 0 (a table draw), so
    no DTZ probe, no outcome changes, no game is left out: every count of C3 is known, probes_made 2 in round 1 and 2
    in round 2 (PROBES). Derived outside the test: tmp/opus_scratch/v15/p1/derive_fixture.py on the PC.
    THESE FACTS BELONG TO THE INPUTS: the workloads of the frozen config d3c4f4eec16e (51 option lines), and the
    engine and net the chains pass (v3-r15dsg-sp-clang, round 67's net). Other inputs, another engine or another net
    play other games: then FP FAILS, and the facts are derived again before any other case is believed (the inputs of
    23 November touched no game; P1 made the fixture again for the new ones).
B1 to B9, U1 to U4 as the known answers (CHANGED before the first run: B4b, B4c, B4d, B5b, B5c, U4; see that file).
PLANTS (each must make the test fail): see PLANTS below.
"""
import gzip
import hashlib
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import tomllib
import traceback
import zlib
from pathlib import Path

if len(sys.argv) < 9:
    print("usage: test_publish.py <home/publish.py> <engine exe> <net file> <converter exe> <config> <pipeline> "
          "<syzygy folder> <a NEW folder> [plantN]")
    sys.exit(2)
SRC = Path(sys.argv[1]).resolve()
EXE, NET, CONV, CONFIG, PIPE, TBSRC, WORK = (Path(a).resolve() for a in sys.argv[2:9])
PLANT = sys.argv[9] if len(sys.argv) > 9 else None
TREE = SRC.parent.parent
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)

PLANTS = {
    "plant1": ("            self.failed.append(f\"{type(e).__name__}: {e} (board {board.fen()})\")\n", "            pass\n"),
    "plant2": ("            if file_sha256(self.tables / name) != sha:\n", "            if False:\n"),
    "plant3": ("        if have != set(want):\n", "        if False:\n"),
    "plant4": ("            if free < need:\n", "            if False:\n"),
    "plant5": ("                    if ds is None:\n", "                    if False:\n"),
    "plant6": ("        return sha256_bytes(b) if d[\"run_fingerprint\"] == self.fp else None\n",
               "        return sha256_bytes(b)\n"),
    "plant7": ("                    if x is None or x[1] != e[\"game\"] or x[2] != e[\"rows_digest\"]:\n",
               "                    if x is None:\n"),
    "plant8": ("                    if g is None or g[\"id\"] != e[\"game\"] or len(g[\"rows\"]) != e[\"rows\"] \\\n"
               "                            or record.rows_digest(g[\"rows\"], g[\"end\"]) != e[\"rows_digest\"]:\n",
               "                    if False:\n"),
    "plant9": ("        cmd = [sys.executable, \"-s\", \"-B\",", "        cmd = [sys.executable, \"-I\", \"-B\","),
    "plant10": ("\"attempts_failed\": before, \"drain_sha256\": None}\n",
                "\"attempts_failed\": before, \"drain_sha256\": None, \"made_utc\": utc_now()}\n"),
    "plant11": ("with gzip.GzipFile(filename=\"\", mode=\"wb\", compresslevel=6, fileobj=o, mtime=0) as z:",
                "with gzip.GzipFile(filename=\"\", mode=\"wb\", compresslevel=6, fileobj=o, mtime=None) as z:"),
    "plant12": ("                self.failed_line(r, str(e))\n", "                pass\n"),
    "plant13": ("        if examined >= self.alarm_games and changed == 0:\n", "        if False:\n"),
    "plant14": ("    if sys.flags.hash_randomization != 0 or len(argv) != 5:\n", "    if len(argv) != 5:\n"),
    "plant15": ("                raise Hold(f\"{what}: an entry of ids is not as credit.py writes it: {str(e)[:160]}\")\n",
                "                pass\n"),
    "plant16": ("\"probes_made\": corr.rec.made, ", "\"probes_made\": 0, "),     # P1: the report's probe count
}
CP = WORK / "tree"
for sub in ("home", "run", "workloads", "known"):
    shutil.copytree(TREE / sub, CP / sub, ignore=shutil.ignore_patterns("__pycache__"))
if PLANT:
    old, new = PLANTS[PLANT]
    text = (CP / "home" / "publish.py").read_text(encoding="ascii")
    assert text.count(old) == 1, f"{PLANT}: the old text is not there exactly once"
    (CP / "home" / "publish.py").write_text(text.replace(old, new), encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy's publish.py")
RUN, CUST, CONT, CRED, PUB = (CP / "run", CP / "home" / "custody.py", CP / "home" / "content.py",
                              CP / "home" / "credit.py", CP / "home" / "publish.py")
sys.path.insert(0, str(RUN))
import record as R  # noqa: E402
import worker as W  # noqa: E402
import chess  # noqa: E402

CFG = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
RESULTS = []


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(("PASS " if ok else "FAIL ") + f"{name}: got {str(got)[:300]}" + ("" if ok else f"; want {str(want)[:300]}"))
    return ok


def safe(fn):
    try:
        fn()
    except (Exception, SystemExit):  # noqa: BLE001   a crash of a part is one FAIL, the other parts go on; also a
        # sys.exit inside an imported program (24 Nov: a stand-in's exit 0 at import ended the test with exit 0 and no
        # verdict, so both ways read it as a pass)
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
SRV, BASE, BASEC = WORK / "srv", WORK / "base", WORK / "basec"
FP = {}
CUST_COUNTS = re.compile(r"custody: RECEIVED (\d+) pieces (\d+) rows; C1 (\d+) pieces")
CONT_COUNTS = re.compile(r"content: judged (\d+) pieces \((\d+) refused\); accepted (\d+) games (\d+) rows; ")
CRED_LAST = re.compile(r"credit: decided (\d+) rounds \((\d+) complete, (\d+) partial\) this pass; credited (\d+) games "
                       r"(\d+) rows; waits: (.*); holds (\d)")
LAST = re.compile(r"publish: published (\d+) rounds \((\d+) complete, (\d+) partial\) this pass; kept rows (\d+); "
                  r"waits: (.*); failed: (.*)")
REPORT_KEYS = sorted(("schema", "run_fingerprint", "round", "status", "credit_sha256", "range_seals", "games_in",
                      "raw_rows_in", "missing_ids", "set_aside_ids", "conflict_ids", "repeat_games", "games_examined",
                      "outcomes_changed", "games_left_out", "probes_made", "probes_failed", "raw_rows", "kept_rows",
                      "marked", "kept_form", "kept_sha256", "frozen", "attempts_failed", "drain_sha256"))
# the tables the cases use: COPIES of these files of the Syzygy folder (U1 Astra 151513Z's board and its two child
# tables; U2 K+Q against K; KRvK only so that the B cases' folder holds more than one ending; P1: KBvKP and KBvKB, the
# tables of the fixture's two drawn endings, games 4 and 5, whose probed positions hold no capture: no other table)
TB_FILES = ["KQPvKQ", "KQvKP", "KPvK", "KQvK", "KRvK", "KBvKP", "KBvKB"]
TB = WORK / "tb"


def gid(c: int) -> str:
    return f"pub-w001-g{c:08d}"


# ---- the fixture R2 (test_credit.py's, run "pub") -------------------------------------------------------------------
def server() -> bool:
    put(SRV / "RUN.json", W.canon({
        "schema": 2, "run": "pub", "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
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
    FP["hdr"] = hdr
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


def credit(h: Path) -> tuple:
    p = subprocess.run([sys.executable, "-I", "-B", str(CRED), "--home", str(h), "--fingerprint", FP["fp"]],
                       capture_output=True, text=True, timeout=600)
    out = (p.stdout + p.stderr).strip()
    m = CRED_LAST.fullmatch(out.splitlines()[-1]) if out else None
    return p.returncode, m.groups() if m else out[-400:]


def base() -> bool:
    fetch(BASE)
    p = subprocess.run([sys.executable, "-I", "-B", str(CUST), "--home", str(BASE), "--fingerprint", FP["fp"]],
                       capture_output=True, text=True, timeout=300)
    m = CUST_COUNTS.search(p.stdout)
    ok = check("R2 a1: exit 0, RECEIVED 6 pieces, C1 6", (p.returncode, m and (m[1], m[3])), (0, ("6", "6")))
    p = subprocess.run([sys.executable, "-I", "-B", str(CONT), "--home", str(BASE), "--fingerprint", FP["fp"],
                        "--converter", str(CONV), "--openings", str(OPENINGS)], capture_output=True, text=True, timeout=900)
    m = CONT_COUNTS.search(p.stdout)
    ok = check("R2 a2: exit 0, judged 6 pieces (0 refused), accepted 12 games",
               (p.returncode, m and (m[1], m[2], m[3])), (0, ("6", "0", "12"))) and ok
    shutil.copytree(BASE, BASEC)
    rc, m = credit(BASEC)
    return check("R2 credit: exit 0, decided 2 rounds (2 complete), waits none, holds 0",
                 (rc, m if isinstance(m, str) else (m[0], m[1], m[2], m[5], m[6])), (0, ("2", "2", "0", "none", "0"))) \
        and ok


def raw_games() -> dict:
    """counter -> game, from the SERVER's own raw pieces (the source of every known answer below)."""
    out = {}
    for i in range(6):
        for g in R.parse((SRV / "w001" / "closed" / f"p{i:06d}.raw").read_bytes(), FP["fp"]):
            out[g["counter"]] = g
    return out


def home(name: str, src: Path = None) -> Path:
    h = WORK / name
    shutil.copytree(src or BASEC, h)
    return h


def tables(name: str, files=None, drop=(), extra=()) -> Path:
    d = WORK / name
    d.mkdir()
    for t in (TB_FILES if files is None else files):
        for ext in (".rtbw", ".rtbz"):
            if t + ext not in drop:
                shutil.copyfile(TBSRC / (t + ext), d / (t + ext))
    for t in extra:
        shutil.copyfile(TBSRC / t, d / t)
    return d


def listing(d: Path, name: str) -> Path:
    p = WORK / name
    p.write_bytes("".join(f"{fsha(f)}  {f.name}\n" for f in sorted(d.iterdir())).encode("ascii"))
    return p


def publish(h: Path, *extra, tb: Path = None, lst: Path = None) -> tuple:
    cmd = [sys.executable, "-I", "-B", str(PUB), "--home", str(h), "--fingerprint", FP["fp"], "--config", str(CONFIG),
           "--pipeline", str(PIPE), "--tables", str(tb or TB), "--tables-list", str(lst or FP["list"]), "--converter",
           str(CONV), "--openings", str(OPENINGS), *extra]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    out = (p.stdout + p.stderr).strip()
    m = LAST.fullmatch(out.splitlines()[-1]) if out else None
    return p.returncode, out, m.groups() if m else None


def folder(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()} if d.is_dir() else {}


def report(h: Path, r: int) -> dict:
    return W.parse_canon((h / "rounds" / f"r{r:04d}" / "report.json").read_bytes(), f"r{r:04d}/report.json")


def lines(h: Path) -> list:
    p = h / "progress.jsonl"
    return [json.loads(x) for x in p.read_bytes().split(b"\n") if x.strip()] if p.exists() else []


# ---- the known answers from the server's own records ----------------------------------------------------------------
ROUND_GAMES = {1: [1, 2, 4], 2: [5, 6]}           # the credited ids with rows (ids 3, 9 have none; 7, 8, 10, 11, 12 repeat)
TOUCHED = {4: "drawn end 8/4K3/8/2p5/5B2/7k/8/8 b - - 0 60", 5: "drawn end 8/8/k7/8/8/5B2/1b6/5K2 w - - 100 133"}  # P1
PROBES = {1: 2, 2: 2}                             # P1: the loop's probes per round (games 4 and 5: two WDL each)


def end_of(g: dict) -> tuple:
    f = g["end"].split()
    return int(f[f.index("result") + 1]), f[f.index("reason") + 1], f[f.index("moves") + 1:]


def my_text(counters, games) -> str:
    """The loop's record text of these games as the loop writes them (datagen_uci.py 352 to 356), written again here."""
    out = []
    for c in counters:
        result = end_of(games[c])[0]
        for row in games[c]["rows"]:
            _, ply, score, bm, fen = row.split(" ", 4)
            res = result if fen.split(" ")[1] == "w" else -result
            out.append(f"fen {fen}\nmove {bm}\nscore {score}\nply {ply}\nresult {res}\ne\n")
    return "".join(out)


def my_filter(text: str) -> tuple:
    """The seven rules of the config's [filter], written again (exact keys, no hash): (text with 32002 on the filtered
    rows, kept, marked)."""
    f = CFG["filter"]
    max_abs, min_ply, max_ply = int(f.get("max_abs_score", 3000)), int(f.get("min_ply", 0)), int(f.get("max_ply", 10**9))
    dedup, conflict = bool(f.get("dedup", True)), int(f.get("conflict_score", 0))
    max_r50, min_pieces = int(f.get("max_halfmove_clock", 1000)), int(f.get("min_pieces", 0))
    marked = {k: 0 for k in ("score_limit", "ply", "duplicate", "score_result_conflict", "rule50", "few_pieces",
                             "already_none")}
    seen, out, kept, rec = set(), [], 0, {}
    for ln in text.split("\n")[:-1]:
        if ln != "e":
            k, v = ln.split(" ", 1)
            rec[k] = v
            continue
        fen, score, ply, result = rec["fen"], int(rec["score"]), int(rec["ply"]), int(rec["result"])
        parts = fen.split(" ")
        why = None
        if score == 32002:
            why = "already_none"
        elif abs(score) > max_abs:
            why = "score_limit"
        elif ply < min_ply or ply > max_ply:
            why = "ply"
        elif conflict and result != 0 and abs(score) >= conflict and (score > 0) != (result > 0):
            why = "score_result_conflict"
        elif len(parts) > 4 and parts[4].isdigit() and int(parts[4]) > max_r50:
            why = "rule50"
        elif sum(ch.isalpha() for ch in parts[0]) < min_pieces:
            why = "few_pieces"
        elif dedup and " ".join(parts[:4]) in seen:
            why = "duplicate"
        elif dedup:
            seen.add(" ".join(parts[:4]))
        if why:
            marked[why] += 1
        else:
            kept += 1
        out.append(f"fen {fen}\nmove {rec['move']}\nscore {32002 if why else score}\nply {ply}\nresult {result}\ne\n")
        rec = {}
    return "".join(out), kept, marked


def changeable(g: dict) -> str:
    """Why the after-game rules MIGHT touch this game ('' when they cannot): a drawn end with 5 pieces or fewer or a
    lone king (bare_king_adjudication), or the ply-limit rule's six one-sided scores."""
    result, reason, moves = end_of(g)
    b = chess.Board()
    for m in g["opening"] + moves:
        b.push_uci(m)
    if result == 0 and (chess.popcount(b.occupied) <= 5 or any(b.occupied_co[c] == b.kings & b.occupied_co[c]
                                                                    for c in (chess.WHITE, chess.BLACK))):
        return f"drawn end {b.fen()}"
    n = int(CFG["datagen"].get("ply_limit_skip_count", 6))
    s = int(CFG["datagen"].get("ply_limit_skip_score", 0))
    tail = [(int(r.split(" ")[2]) if r.split(" ")[4 + 1] == "w" else -int(r.split(" ")[2])) for r in g["rows"][-n:]]
    if reason == "plylimit" and s > 0 and len(tail) >= n and (min(tail) >= s or max(tail) <= -s):
        return "ply-limit rule"
    return ""


def frozen_want() -> dict:
    nl = PIPE / "nnloop"
    hdr = FP["hdr"]
    return {"filter_code": fsha(nl / "filterqc.py"), "correction_code": fsha(nl / "datagen_uci.py"),
            "loop_common": fsha(nl / "common.py"), "config": fsha(CONFIG), "tables_list": fsha(FP["list"]),
            "converter": fsha(CONV), "publisher": fsha(PUB), "python": platform.python_version(),
            "net": hdr["net_sha256"], "options": hdr["options_sha256"], "engine": hdr["engine_sha256"]}


# ---- the cases ------------------------------------------------------------------------------------------------------
def case_fp_b1_b2_b3_b9():
    g = raw_games()
    c1 = json.loads((BASEC / "stage" / "r0001" / "credit.json").read_bytes())
    c2 = json.loads((BASEC / "stage" / "r0002" / "credit.json").read_bytes())
    got = {r: [e["counter"] for e in c["ids"] if e["state"] == "credited" and e["rows"]] for r, c in ((1, c1), (2, c2))}
    check("FP credit's credited ids with rows are ids 1 2 4 | 5 6", got, ROUND_GAMES)
    check("FP the after-game rules can touch exactly games 4 and 5 (drawn, four pieces), none by the ply-limit rule "
          "(else the fixture is not the one of these inputs: derive it again, see the docstring, before a B case)",
          {c: changeable(g[c]) for c in (1, 2, 4, 5, 6)}, {c: TOUCHED.get(c, "") for c in (1, 2, 4, 5, 6)})
    want = {}
    for r in (1, 2):
        text = my_text(ROUND_GAMES[r], g)
        filtered, kept, marked = my_filter(text)
        want[r] = (text, filtered, kept, marked)
    h = home("b1")
    rc, out, m = publish(h)
    total = want[1][2] + want[2][2]
    check("B1 one pass: exit 0, published 2 rounds (2 complete), kept rows as the test's own filter, waits none",
          (rc, m), (0, ("2", "2", "0", str(total), "none", "none")))
    check("B1 rounds/ holds r0001 and r0002 with exactly kept.plain.gz and report.json; .staging is empty",
          (sorted(p.name for p in (h / "rounds").iterdir()), [sorted(x.name for x in (h / "rounds" / d).iterdir())
                                                               for d in ("r0001", "r0002", ".staging")]),
          ([".staging", "r0001", "r0002"], [["kept.plain.gz", "report.json"], ["kept.plain.gz", "report.json"], []]))
    for r, c in ((1, c1), (2, c2)):
        rep = report(h, r)
        kb = (h / "rounds" / f"r{r:04d}" / "kept.plain.gz").read_bytes()
        text, filtered, kept, marked = want[r]
        check(f"B1 round {r}: report.json is canonical with exactly the keys of 2.3", sorted(rep), REPORT_KEYS)
        check(f"B1 round {r}: kept.plain.gz unpacks to the test's own filter of its own text (32002 on filtered rows)",
              gzip.decompress(kb) == filtered.encode("ascii"), True)
        check(f"B1 round {r}: gzip header without a name and with mtime 0", (kb[3], kb[4:8]), (0, b"\0\0\0\0"))
        cb = (h / "stage" / f"r{r:04d}" / "credit.json").read_bytes()
        check(f"B1 round {r}: the report's fields", rep, {
            "schema": 2, "run_fingerprint": FP["fp"], "round": r, "status": "complete", "credit_sha256": sha(cb),
            "range_seals": c["range_seals"], "games_in": c["games_in"], "raw_rows_in": c["raw_rows_in"],
            "missing_ids": [], "set_aside_ids": [], "conflict_ids": [], "repeat_games": c["repeat_games"],
            "games_examined": len(ROUND_GAMES[r]), "outcomes_changed": {}, "games_left_out": {}, "probes_made": PROBES[r],
            "probes_failed": 0, "raw_rows": text.count("\ne\n"), "kept_rows": kept, "marked": marked,
            "kept_form": "plain.gz", "kept_sha256": sha(kb), "frozen": frozen_want(), "attempts_failed": 0,
            "drain_sha256": None})
    before = folder(h / "rounds")
    rc, out, m = publish(h)
    check("B2 a second pass: exit 0, nothing published, both round folders byte for byte as before",
          (rc, m, folder(h / "rounds") == before), (0, ("0", "0", "0", "0", "none", "none"), True))
    h3 = home("b3")
    rc, out, m = publish(h3)
    check("B3 a second home published by a fresh pass: the same two round folders byte for byte",
          (rc, folder(h3 / "rounds") == before), (0, True))
    h9 = home("b9")
    rc, out, m = publish(h9, "--alarm-games", "1")
    check("B9 the ALARM with --alarm-games 1: exit 5, its line, both rounds published all the same",
          (rc, "ALARM publish: no outcome changed in 5 examined games" in out, m and m[:3]), (5, True, ("2", "2", "0")))


def case_b4():
    for name, fn, words in (
            ("B4", "credit", "content index does not hold it with credit.json's rows digest"),
            ("B4b", "index", "content index does not hold it with credit.json's rows digest"),
            ("B4c", "piece", "custody bytes do not give credit.json's rows and rows digest")):
        h = home(name.lower())
        if fn == "credit":
            p = h / "stage" / "r0001" / "credit.json"
            c = json.loads(p.read_bytes())
            c["ids"][0]["rows_digest"] = "f" * 64
            p.write_bytes(W.canon(c))
        else:
            con = sqlite3.connect(h / "content" / "equal.sqlite")
            col = "rows_digest = ?" if fn == "index" else "piece = ?"
            con.execute(f"UPDATE entries SET {col} WHERE slot = 1 AND counter = 1",
                        ("f" * 64 if fn == "index" else "w001/p000001",))
            con.commit()
            con.close()
        rc, out, m = publish(h)
        check(f"{name} ({fn} changed for id 1): exit 5 HOLDS naming id 1 and the rule's words; nothing published, "
              "no attempt line",
              (rc, f"ALARM publish HOLDS round 1: {gid(1)}: " in out, words in out, (h / "rounds" / "r0001").exists(),
               lines(h)), (5, True, True, False, []))
    h = home("b4d")
    p = h / "stage" / "r0001" / "credit.json"
    c = json.loads(p.read_bytes())
    c["ids"][0]["rows"] = str(c["ids"][0]["rows"])
    p.write_bytes(W.canon(c))
    rc, out, m = publish(h)
    check("B4d (credit.json's rows of id 1 written as text): exit 5 HOLDS with the entry rule's words, naming id 1; "
          "nothing published, no attempt line",
          (rc, "ALARM publish HOLDS round 1: stage/r0001/credit.json: an entry of ids is not as credit.py writes it"
           in out, gid(1) in out, (h / "rounds" / "r0001").exists(), lines(h)), (5, True, True, False, []))


def case_b5():
    for name, how in (("B5", "missing"), ("B5b", "changed"), ("B5c", "extra")):
        tb = tables(f"tb_{name.lower()}")
        lst = listing(tb, f"list_{name.lower()}.txt")
        if how == "missing":
            (tb / "KRvK.rtbz").unlink()
            words = "KRvK.rtbz"
        elif how == "changed":
            (tb / "KRvK.rtbz").write_bytes((tb / "KRvK.rtbz").read_bytes() + b"\0")
            words = "the table file KRvK.rtbz is not the list's bytes"
        else:
            shutil.copyfile(TBSRC / "KBNvK.rtbw", tb / "KBNvK.rtbw")
            words = "not on the list ['KBNvK.rtbw']"
        h = home(name.lower())
        rc, out, m = publish(h, tb=tb, lst=lst)
        ln = lines(h)
        check(f"{name} the tables' list against a folder with a table {how}: exit 6, ONE attempt line for round 1 "
              "naming it, nothing published, staging empty",
              (rc, len(ln), ln and (ln[0]["t"], ln[0]["round"], ln[0]["result"], words in ln[0]["why"]),
               (h / "rounds" / "r0001").exists(), sorted(x.name for x in (h / "rounds" / ".staging").iterdir())),
              (6, 1, ("stage_b_attempt", 1, "failed", True), False, []))
        rc, out, m = publish(h)
        check(f"{name} the same inputs back (the right folder and list): exit 0, both published; round 1 counts 1 "
              "failed attempt, round 2 none",
              (rc, m and m[:3], report(h, 1)["attempts_failed"] if rc == 0 else None,
               report(h, 2)["attempts_failed"] if rc == 0 else None), (0, ("2", "2", "0"), 1, 0))


def case_b6():
    h = home("b6")
    rc, out, m = publish(h, "--floor-gb", "1000000000")
    ln = lines(h)
    check("B6 the staging volume too small (floor 10^9 GiB): exit 6, the attempt line names the staging volume",
          (rc, len(ln), ln and "staging volume: needs" in ln[0]["why"], (h / "rounds" / "r0001").exists()),
          (6, 1, True, False))
    rc, out, m = publish(h)
    check("B6 then the normal floor: published, round 1 counts 1 failed attempt",
          (rc, m and m[:3], report(h, 1)["attempts_failed"] if rc == 0 else None), (0, ("2", "2", "0"), 1))


def case_b7_b8():
    h = home("b7", BASE)
    p = h / "content" / "w001" / "p000002.verdict.json"
    v = json.loads(p.read_bytes())
    x = [e for e in v["games"] if e["game"] == gid(5)][0]
    x.update(state="set_aside", rows_digest=None, why="test: a2 set this game aside")
    p.write_bytes(W.canon(v))
    rc, m = credit(h)
    check("B7 credit with id 5 set aside: exit 0, decided 2 rounds (1 complete, 1 partial)",
          (rc, m if isinstance(m, str) else m[:3]), (0, ("2", "1", "1")))
    rc, out, m = publish(h)
    check("B7 without DRAIN.json: exit 0, round 1 published, round 2 WAITS (named), not published",
          (rc, m and m[:3], m and "round 2 (partial" in m[4], (h / "rounds" / "r0002").exists()),
          (0, ("1", "1", "0"), True, False))
    drain = {"schema": 2, "run_fingerprint": "0" * 64, "at_utc": "2026-11-24T05:00:00Z", "why": "lease ended",
             "missing": []}
    put(h / "DRAIN.json", W.canon(drain))
    rc, out, m = publish(h)
    check("B8 a DRAIN.json of another run: exit 0, round 2 still waits",
          (rc, m and m[:3], m and "round 2 (partial" in m[4], (h / "rounds" / "r0002").exists()),
          (0, ("0", "0", "0"), True, False))
    drain["run_fingerprint"] = FP["fp"]
    db = W.canon(drain)     # a TYPED stand-in: the home guard that writes DRAIN.json does not exist yet
    put(h / "DRAIN.json", db)
    rc, out, m = publish(h)
    rep = report(h, 2) if (h / "rounds" / "r0002" / "report.json").exists() else {}
    check("B7 with this run's DRAIN.json: exit 0, round 2 published partial: report.json alone, kept_rows 0, the "
          "drain's sha256, set_aside_ids [id 5]",
          (rc, m and m[:3], sorted(x.name for x in (h / "rounds" / "r0002").iterdir()) if rep else None,
           rep.get("status"), rep.get("kept_rows"), rep.get("kept_sha256"), rep.get("drain_sha256"),
           rep.get("set_aside_ids")),
          (0, ("1", "0", "1"), ["report.json"], "partial", 0, None, sha(db), [gid(5)]))


def case_u():
    sys.path.insert(0, str(CP / "home"))
    sys.path.insert(0, str(PIPE))
    import publish as PB
    from nnloop import datagen_uci as DG
    G = dict(CFG["datagen"])

    def run(tb, fen, recs, result, limit, plies):
        corr = PB.Correction(DG, G, tb, 8)
        try:
            return corr, corr.game(chess.Board(fen), recs, result, limit, False, plies), None
        except PB.Failed as e:
            return corr, None, str(e)
        finally:
            corr.close()
    q = "8/8/8/3Qqk2/6p1/8/6K1/8 w - - 15 91"            # Astra 151513Z: KQPvKQ intact, two child tables needed
    corr, got, err = run(tables("tb_u1", ["KQPvKQ", "KQvKP", "KPvK"]), q, [], 0, True, 90)
    check("U1 the queen ending, the three tables: no failure, no change (WDL draw), 1 probe made",
          (err, DG.LAST_ADJ, corr.changed, corr.rec.made, corr.rec.failed), (None, None, {}, 1, []))
    # python-chess names a missing table by the probed position's key, White's pieces first (measured 05:56 on the
    # first run's copies: 'did not find wdl table KvKP' for the file KPvK, 'KQvKP' for KQvKP)
    for child, key in (("KPvK", "KvKP"), ("KQvKP", "KQvKP")):
        corr, got, err = run(tables(f"tb_u1_{child}", ["KQPvKQ", "KQvKP", "KPvK"], drop=(child + ".rtbw",
                                                                                     child + ".rtbz")), q, [], 0, True, 90)
        check(f"U1 without the child table {child}: FAILED naming it ('did not find wdl table {key}'), the result "
              "unchanged (no lone king)",
              (err is not None and f"did not find wdl table {key}" in err, DG.LAST_ADJ), (True, None))
    k = "8/8/8/4k3/8/8/8/KQ6 w - - 0 1"
    corr, got, err = run(tables("tb_u2", ["KQvK"]), k, [], 0, True, 300)
    check("U2 K+Q against K at the ply limit, with KQvK: +1 'ply limit, tablebase', 4 probes, no failure",
          (err, DG.LAST_ADJ and DG.LAST_ADJ[1:3], corr.changed, corr.rec.made), (None, ("ply limit, tablebase", 1),
                                                                                  {"ply limit, tablebase": 1}, 4))
    corr, got, err = run(tables("tb_u2_none", ["KRvK"]), k, [], 0, True, 300)
    check("U2 without KQvK: FAILED naming it although the material rule decided +1 'ply limit'",
          (err is not None and "KQvK" in err, DG.LAST_ADJ and DG.LAST_ADJ[1:3]), (True, ("ply limit", 1)))
    f12 = "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 4 4"
    recs = [(f12, "a2a3", 400 if i % 2 == 0 else -400, 100 + i, i % 2 == 0) for i in range(6)]
    corr, got, err = run(TB, f12, recs, 0, True, 300)
    check("U3 the ply limit with six scores of +400 for White and 32 pieces: left out once, no text, no probe",
          (err, got, corr.left_out, corr.changed, corr.rec.made), (None, ("", 0), {"ply limit skip": 1}, {}, 0))
    raw = WORK / "u4_raw"
    raw.mkdir()
    (raw / "round.plain").write_bytes(f"fen {f12}\nmove a2a3\nscore 10\nply 9\nresult 0\ne\n".encode("ascii"))
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PYTHON")}
    for seed, want in (("5", 6), ("0", 0)):
        p = subprocess.run([sys.executable, "-s", "-B", str(PUB), "--filter-child", str(CONFIG), str(PIPE), str(raw),
                            str(WORK / f"u4_out_{seed}"), str(CONV)], env=dict(env, PYTHONHASHSEED=seed),
                           capture_output=True, text=True, timeout=600)
        check(f"U4 the filter child with PYTHONHASHSEED={seed}: exit {want}" + (", refusing by its own words" if want
                                                                               else ", qc.json written"),
              (p.returncode, "PYTHONHASHSEED=0" in p.stdout if want else (WORK / f"u4_out_{seed}" / "qc.json").exists()),
              (want, True))
        if seed == "5":
            check("U4 the refusing child left the raw text in place (it refused before the filter ran)",
                  (raw / "round.plain").exists(), True)


def main() -> int:
    t0 = time.time()
    TB.mkdir()
    for t in TB_FILES:
        for ext in (".rtbw", ".rtbz"):
            shutil.copyfile(TBSRC / (t + ext), TB / (t + ext))
    FP["list"] = listing(TB, "tables.sha256")
    if not (server() and base()):
        print("the fixture failed: no case can run")
    else:
        for fn in (case_fp_b1_b2_b3_b9, case_b4, case_b5, case_b6, case_b7_b8, case_u):
            safe(fn)
    bad = [n for n, ok in RESULTS if not ok]
    print(f"{len(RESULTS) - len(bad)} of {len(RESULTS)} checks pass ({time.time() - t0:.0f} s)"
          + (f"; PLANT {PLANT}" if PLANT else ""))
    return 0 if RESULTS and not bad else 1


if __name__ == "__main__":
    sys.exit(main())

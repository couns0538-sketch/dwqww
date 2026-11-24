"""test_terminal.py: the terminal inventory (A3c, run/terminal.py; FORMATS 1.9 after 1.8) against known answers written
BEFORE it (tmp/opus_scratch/terminal/KNOWN_ANSWERS_by_opus.md on the PC). Standard library only.

    test_terminal.py <run/terminal.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]

The run folder of terminal.py is copied; a plant is applied to the copy's terminal.py only. The fixtures are made by the
REAL worker of that folder (the real engine, N12's openings: rows 86, 101, 0, 127, 81, 67 for games 1 to 6), its REAL
finalizer (the worker's seal_only start) and the REAL packer (the official converter, or none): the inventory reads
what the day's own programs write. <tree> = the folder above run/ holds workloads/ and known/.

A  run "term", list rule, piece_games 2, slots [1, 2] (counters 1 to 6 and 1 to 3), SCHEDULE.1: slot 1 plays all six
   (pieces 187, 127, 148 rows), FENCE.json (why "D"), slot 2's start under the fence (seal_only: never_dispatched 3),
   the packer --once with the official converter (three offers, binpack). 11 lines; footer: slots ended 2, pieces 3,
   offered 3, raw_rows 462, ids done 6 and never_dispatched 3, cutoff_reached true, stop_reason "D".
K  the state a kill of slot 1 leaves while g4 plays (a copy of A once slot 1 ended by the fence, FENCE.json removed:
   the journal cut after g3's done line, p1's raw moved back to open/ and cut to g3's end, the later seals, p2's raw
   and the range seal removed). Slots 1 and N end by a fence written once their range seal is there: no dispatch end.
U  K + fence + slot 2 finalized, slot 1 left: unreconciled, last_index 0, one piece not offered. 8 lines.
B  K + the start of g4's record in the open piece + a control fence + slot 1 restarted (the finalizer: failed g4, p1
   closed with g3) + slot 2 finalized + the packer with no converter (two raw offers): id line g4 unfinished. 11 lines.
C  K + fence + slot 1 restarted with nothing after g3 (the finalizer doubts g4) + slot 2 finalized: id line g4
   dispatch_unknown. 11 lines.
N  run "edge", seed rule edge2649, slot 0, the pilot range 1 to 1 and NO schedule: g1 noselfgame; 8 lines, line 2
   {"n":0,"t":"schedule"}, id line noselfgame "nomoves".
R  refusals, exit 4, nothing written, each naming its own cause: R1 a seal changed, R2 an offer of another seal, R3 an
   offer's .zz of other bytes, R4 a seal missing before later ones, R5 a range seal's through_seal, R6 an ended line
   beyond the chain, R7 no fence, R8 a schedule's prev, R9 an offer outside the chain, R10 another TERMINAL.jsonl
   there (no .zz made), R13 a decimal number in a journal line, R14 a dispatch_unknown id with a journal line. R11 a
   finished root without its .zz: exit 0, the .zz made again, TERMINAL.jsonl unchanged. R12 a second run: exit 0,
   nothing changed. E1 a root that is not a folder: exit 2.
PLANTS (each must make the test fail): 1 the ended line not compared with the chain (R6's cause); 2 a gap in the seals
not refused (R4's cause); 3 the offer's seal_sha256 not compared (R2); 4 the .zz not compared (R3); 5 offered_bytes
from `bytes` (A); 6 packed_bytes with the seal member (A); 7 every slot with a journal "ended" (U); 8 an unfinished
id's why always "cutoff" (B); 9 the fingerprint over less than the body (A); 10 a schedule's prev not checked (R8);
11 another TERMINAL.jsonl accepted (R10); 12 the .zz never written (A, R11); 13 through_seal not checked (R5); 14 an
offer outside the chain not refused (R9); 15 no {"n":0} record (N); 16 a dispatch_unknown id with a line (R14).
VERSION 2 (Opus 2026-11-24; KNOWN_ANSWERS_terminal_v2_by_opus.md on the PC, with its CHANGED section of 03:36), part V:
T-A VA1 to VA5 (the ranges against the schedule each seal names; VA4 a seal read from its wire copy), VL (a schedule the
guard's own new_schedule writes after slot 1 ended: exit 0 and a note), VL2, VL3 (a later schedule shortens a row a
slot sealed: exit 0), VS1, VS2 (A0, the worker's check_rows); T-B VB1 to VB4; T-C VC1 to VC5b with VC4b; T-D VD1, VD2;
T-F VF1 (control VF1c), VF2, VF3; T-E VE1 (control VE1c), VE2. PLANTS 17 to 44, each must fail its named case: 17 A1
(VA1), 18 A2 (VA2), 19 A3 (VA3, VA3b, VL2), 20 the wire copy not read (VA4), 21 A5 (VA5), 22 to 25 B1 to B4 (VB1 to
VB4), 26 to 29 C1 to C4 (VC1 to VC4), 30 C5a (VC5a), 31 C5b (VC5b), 32 D1 (VD1), 33 D2 (VD2), 34 to 36 F1 to F3 (VF1
to VF3), 37 E1 (VE1), 38 E2 (VE2), 39 C4's null branch (VC4b), 40 A3 against the FINAL schedule (VL), 41 L always 0
(VL2), 42 A1 and A2 against the FINAL schedule (VL3), 43 A0 on the schedules (VS1), 44 A0 on the pilot ranges (VS2).
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import zlib
from pathlib import Path

if len(sys.argv) < 6:
    print("usage: test_terminal.py <run/terminal.py> <engine exe> <net file> <converter exe> <a NEW folder> [plantN]")
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
    "plant1": ('        need(jl[-1].get("last_index") == last_index and jl[-1].get("last_seal") == last_seal,\n',
               '        need(True,\n'),
    "plant2": ("    if beyond:\n", "    if False:\n"),
    "plant3": ('                 and o.get("seal_sha256") == x and isinstance(o.get("members"), list),\n',
               '                 and isinstance(o.get("members"), list),\n'),
    "plant4": ('            need(same_zz(odir / f"p{ix:06d}.offer.json.zz", b), ',
               '            need(True or same_zz(odir / f"p{ix:06d}.offer.json.zz", b), '),
    "plant5": ('osha, ob = sha256_bytes(b), sum(m["wire_bytes"] for m in ms)',
               'osha, ob = sha256_bytes(b), sum(m["bytes"] for m in ms)'),
    "plant6": ('            pb = sum(m["bytes"] for m in ms if m["name"] != f"p{ix:06d}.seal.json")\n',
               '            pb = sum(m["bytes"] for m in ms)\n'),
    "plant7": ('    ended = bool(jl) and jl[-1]["t"] == "ended"\n', '    ended = bool(jl)\n'),
    "plant8": ('            need(isinstance(why, str), f"{name}: {g} is {st} without a journal line that says why")\n',
               '            why = "cutoff"\n'),
    "plant9": ('"fingerprint": sha256_bytes(data),', '"fingerprint": sha256_bytes(data[:-2]),'),
    "plant10": ('s.get("run_fingerprint") == fp and s.get("prev") == prev,', 's.get("run_fingerprint") == fp,'),
    "plant11": ('        need(isinstance(old, dict) and dict(old, completed_at_utc=None) == dict(foot, completed_at_utc=None),\n',
                '        need(True,\n'),
    "plant12": ('        create_only(zz, zlib.compress(full, 6))\n', '        pass\n'),
    "plant13": ('                 and rs.get("through_seal") == chain[ti][0]\n', '                 and True\n'),
    "plant14": ("    if stray:\n", "    if False:\n"),
    "plant15": ('        lines.append(canon({"n": 0, "t": "schedule"}))\n', '        pass\n'),
    "plant16": ('            need(not mine, f"{name}: {g} is dispatch_unknown and has a journal line")\n',
                '            pass\n'),
    # version 2 (part V): one exact replacement each
    "plant17": ('need(row, f"{what}: no range', 'need(True, f"{what}: no range'),
    "plant18": ('need(canon({x: rs.get(x) for x in ROWF}) == canon({x: row.get(x) for x in ROWF}),', 'need(True,'),
    "plant19": ('need(want["round"] in sealed,', 'need(True,'),
    "plant20": (r'rpat = re.compile(rf"r([0-9]{{4}})\.{name}\.seal\.json(?:\.zz)?")',
                r'rpat = re.compile(rf"r([0-9]{{4}})\.{name}\.seal\.json")'),
    "plant21": ('need(not plain.exists() or not twin.exists() or same_zz(twin, b),', 'need(True,'),
    "plant22": ('            need(fi == -1\n', '            need(True\n'),
    "plant23": ('                 and rs.get("first_prev_seal") is None\n', '                 and True\n'),
    "plant24": ('                 and rs.get("through_seal") is None, f', '                 and True, f'),
    "plant25": ('need(d["done"] + d["noselfgame"] == 0,', 'need(True,'),
    "plant26": ('need(all(d[st] >= 0 for st in STATES),', 'need(True,'),
    "plant27": ('need(sum(d[st] for st in STATES) == rs["last"] - rs["first"] + 1,', 'need(True,'),
    "plant28": ('need(all(d[st] == sum(p[1] == st for p in nd) for st in', 'need(all(True for st in'),
    "plant29": ('(type(ndf) is int and d["never_dispatched"] == rs["last"] - ndf + 1)', 'True'),
    "plant30": ('need(part is not None and part[:2] == (run, k) and rs["first"] <= part[2] <= rs["last"],',
                'need(part is not None,'),
    "plant31": ('need(all(x < y for x, y in zip(ctr, ctr[1:])),', 'need(True,'),
    "plant32": (r'OFFER = re.compile(r"p([0-9]{6})\.offer\.json(?:\.zz)?")',
                r'OFFER = re.compile(r"p([0-9]{6})\.offer\.json")'),
    "plant33": ('    if bad:', '    if False:'),
    "plant34": ('need(type(h.get("schema")) is int and h["schema"] == 2,', 'need(True,'),
    "plant35": ('need(sorted(f) == FENCE_KEYS,', 'need(True,'),
    "plant36": ('need(type(f.get("schema")) is int and f["schema"] == 2,', 'need(True,'),
    "plant37": ('need(f1 > t0,', 'need(True,'),
    "plant38": ('        if miss:', '        if False:'),
    "plant39": ('need(ndf is None if', 'need(True if'),
    "plant40": ('scheds[L]', 'scheds[-1]'),
    "plant41": ('L = max(named, default=0)', 'L = 0'),
    "plant42": ('rows = scheds[s] if', 'rows = scheds[-1] if'),
    "plant43": ('scheds.append(check_rows(s.get("ranges"), h["slots"], n, f"SCHEDULE.{n}.json"))',
                'scheds.append(s.get("ranges"))'),
    "plant44": ('scheds = [check_rows(h.get("pilot_ranges"), h["slots"], 0, "RUN.json pilot_ranges")]',
                'scheds = [h.get("pilot_ranges")]'),
}
RUN = WORK / "run"
shutil.copytree(SRC.parent, RUN, ignore=shutil.ignore_patterns("__pycache__"))
if PLANT:
    old, new = PLANTS[PLANT]
    text = (RUN / "terminal.py").read_text(encoding="ascii")
    assert text.count(old) == 1, f"{PLANT}: the old text is not there exactly once"
    (RUN / "terminal.py").write_text(text.replace(old, new), encoding="ascii", newline="\n")
    print(f"PLANT {PLANT} applied to the copy's terminal.py")
sys.path.insert(0, str(RUN))
import worker as W  # noqa: E402
import guard as G  # noqa: E402   part V: SCHEDULE.2 of VL is made by the guard's own new_schedule

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


MAN_PATH, KNOWN = TREE / "workloads" / "MANIFEST.json", TREE / "known" / "startup.json"
MAN = json.loads(MAN_PATH.read_bytes())
N12 = [ln.split()[3:] for ln in (TREE / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
OPENINGS = WORK / "n12_openings.txt"
OPENINGS.write_bytes("".join(" ".join(o) + "\n" for o in N12).encode("ascii"))
GAME_ROWS = [86, 101, 0, 127, 81, 67]                  # N12's six games (known/n12_batch.json: 462 rows)
DOUBT = "no line: in doubt after an earlier play epoch (1.8 point 3)"
CUT = "its bytes lay beyond the journal's end and were cut at a restart"
NOW = time.time()


def header(root: Path, run: str, slots: list, rows: list, piece_games: int, rule: dict) -> str:
    put(root / "RUN.json", W.canon({
        "schema": 2, "run": run, "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
        "hard_cutoff_utc": T(NOW + 86400), "boot_id": W.boot_id(), "instance": "test-instance", "package": "0" * 64,
        "engine_sha256": sha(EXE.read_bytes()), "net_sha256": MAN["net_sha256"],
        "options_sha256": sha("".join(ln + "\n" for ln in MAN["options"]).encode("ascii")),
        "game_line": MAN["selfgame_line"], "opening_rule": rule, "slots": slots, "piece_games": piece_games,
        "pilot_ranges": rows}))
    return sha((root / "RUN.json").read_bytes())


def row(slot, first, last):
    return {"slot": slot, "round": 1, "first": first, "last": last, "short": False, "schedule": 0}


def fence(root: Path, why: str) -> None:
    s = sorted(root.glob("SCHEDULE.*.json"), key=lambda p: int(p.name.split(".")[1]))
    d = json.loads((s[-1] if s else root / "RUN.json").read_bytes())["cutoff_utc" if s else "hard_cutoff_utc"]
    put(root / "FENCE.json", W.canon({"at_utc": T(time.time()), "cutoff_utc": d,
                                      "run_fingerprint": sha((root / "RUN.json").read_bytes()), "schema": 2, "why": why}))


def worker(root: Path, slot: int, openings=True):
    cmd = [sys.executable, "-I", "-B", str(RUN / "worker.py"), "--root", str(root), "--slot", str(slot), "--exe",
           str(EXE), "--net", str(NET), "--manifest", str(MAN_PATH), "--known-startup", str(KNOWN)]
    p = subprocess.run(cmd + (["--openings", str(OPENINGS)] if openings else []), capture_output=True, text=True,
                       timeout=600)
    return p.returncode, (p.stdout + p.stderr)[-400:]


def play_then_fence(root: Path, slot: int, why: str, openings=True):
    """The worker plays its ranges; once its range seal is there (create-only: whole), FENCE.json is written and the
    worker ends by it (`ranges done`): no wait for a dispatch end. Its output goes to a file (no pipe to fill)."""
    cmd = [sys.executable, "-I", "-B", str(RUN / "worker.py"), "--root", str(root), "--slot", str(slot), "--exe",
           str(EXE), "--net", str(NET), "--manifest", str(MAN_PATH), "--known-startup", str(KNOWN)]
    log = WORK / f"{root.name}.w{slot:03d}.out"
    seal = root / "ranges" / f"r0001.w{slot:03d}.seal.json"
    with open(log, "wb") as f:
        p = subprocess.Popen(cmd + (["--openings", str(OPENINGS)] if openings else []), stdout=f,
                             stderr=subprocess.STDOUT)
        end = time.time() + 600
        while not seal.exists() and p.poll() is None and time.time() < end:
            time.sleep(0.5)
        fence(root, why)
        try:
            p.wait(timeout=120)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
    return p.returncode, log.read_text(encoding="utf-8", errors="replace")[-400:]


def packer(root: Path, conv: Path):
    p = subprocess.run([sys.executable, "-I", "-B", str(RUN / "packer.py"), "--root", str(root), "--converter",
                        str(conv), "--once"], capture_output=True, text=True, timeout=600)
    return p.returncode, (p.stdout + p.stderr).strip()[-300:]


def terminal(root: Path):
    p = subprocess.run([sys.executable, "-I", "-B", str(RUN / "terminal.py"), "--root", str(root)],
                       capture_output=True, text=True, timeout=300)
    return p.returncode, (p.stdout + p.stderr).strip()


def jlines(root: Path, k: int) -> list:
    return [json.loads(ln) for ln in (root / f"w{k:03d}" / "journal.txt").read_bytes().split(b"\n")[:-1]]


def copy(src: Path, name: str) -> Path:
    shutil.copytree(src, WORK / name)
    return WORK / name


# ---- the expected inventory, from the files by the rules of 1.9 (not by terminal.py's code) ----------------------
def piece_line(root: Path, k: int, i: int) -> bytes:
    sb = (root / f"w{k:03d}" / "closed" / f"p{i:06d}.seal.json").read_bytes()
    o_path = root / "out" / f"w{k:03d}" / f"p{i:06d}.offer.json"
    offered = o_path.with_name(o_path.name + ".zz").exists()
    o = json.loads(o_path.read_bytes()) if offered else None
    return W.canon({"index": i, "offer": sha(o_path.read_bytes()) if offered else None,
                    "offered_bytes": sum(m["wire_bytes"] for m in o["members"]) if offered else 0,
                    "packed_bytes": sum(m["bytes"] for m in o["members"] if m["name"] != f"p{i:06d}.seal.json")
                    if offered else None, "raw_bytes": json.loads(sb)["raw_bytes"], "seal": sha(sb), "slot": k,
                    "t": "piece"})


def slot_line(root: Path, k: int, state: str, last_index: int) -> bytes:
    fp = sha((root / "RUN.json").read_bytes())
    seal = root / f"w{k:03d}" / "closed" / f"p{last_index:06d}.seal.json"
    return W.canon({"epochs": [ln for ln in jlines(root, k) if ln["t"] == "epoch"], "last_index": last_index,
                    "last_seal": sha(seal.read_bytes()) if last_index >= 0 else f"genesis:{fp}:w{k:03d}",
                    "slot": k, "state": state, "t": "slot"})


def ids(**kw) -> dict:
    return {s: kw.get(s, 0) for s in ("dispatch_unknown", "done", "never_dispatched", "noselfgame", "refused",
                                      "unfinished")}


def inventory(name: str, root: Path, lines: list, n_lines: int, foot: dict, t0: float):
    """Run the tool; TERMINAL.jsonl = the expected lines + a footer with the fingerprint of their bytes and the known
    counts; its .zz decodes to it; the tool's line names its sha256."""
    rc, out = terminal(root)
    t1 = time.time()
    check(f"{name} exit 0", (rc, out[-200:] if rc else ""), (0, ""))
    path = root / "TERMINAL.jsonl"
    data = path.read_bytes() if path.exists() else b""
    body = b"".join(lines)
    got_lines = data.split(b"\n")[:-1]
    check(f"{name} {n_lines} lines", (len(got_lines), len(lines) + 1), (n_lines, n_lines))
    if not check(f"{name} every line before the footer as the rules of 1.9 give it", data[:len(body)] == body, True):
        diff = [(i, a, b) for i, (a, b) in enumerate(zip(data.split(b"\n"), body.split(b"\n"))) if a != b]
        if diff:
            i, a, b = diff[0]
            print(f"   first different line {i + 1}: got {a[:300]!r}\n   want {b[:300]!r}")
    try:
        f = W.parse_canon(data[len(body):], "the footer")
    except ValueError as e:
        f = {"error": str(e)}
    t = f.get("completed_at_utc", "")
    check(f"{name} the footer: canonical, the known counts, fingerprint = sha256 of the lines before it",
          dict(f, completed_at_utc=None), dict(foot, completed_at_utc=None, fingerprint=sha(body), t="footer"))
    check(f"{name} completed_at_utc inside the run", isinstance(t, str) and T(t0 - 1) <= t <= T(t1 + 1), True)
    zz = root / "TERMINAL.jsonl.zz"
    check(f"{name} TERMINAL.jsonl.zz decodes to TERMINAL.jsonl; the tool names its sha256",
          (zz.exists() and zlib.decompress(zz.read_bytes()) == data, sha(data) in out), (True, True))


STATE = {}


# ---- the fixtures ------------------------------------------------------------------------------------------------
def fixtures():
    a = WORK / "a"
    fp = header(a, "term", [1, 2], [row(1, 1, 6), row(2, 1, 3)], 2,
                {"kind": "list", "sha256": sha(OPENINGS.read_bytes()), "count": len(N12)})
    t = time.time()
    put(a / "SCHEDULE.1.json", W.canon({"schema": 2, "run_fingerprint": fp, "n": 1, "prev": "first",
                                        "evidence": "0" * 64, "cutoff_utc": T(t + 3600),
                                        "dispatch_end_utc": T(t + 3540), "ranges": [row(1, 1, 6), row(2, 1, 3)]}))
    rc, out = play_then_fence(a, 1, "D")
    closed = a / "w001" / "closed"
    rows = [json.loads((closed / f"p{i:06d}.seal.json").read_bytes())["rows"] for i in range(3)
            if (closed / f"p{i:06d}.seal.json").exists()]
    if not check("fixture A: slot 1 exit 0, three pieces of 187, 127, 148 rows, ended \"ranges done\"",
                 (rc, rows, jlines(a, 1)[-1].get("why") if (a / "w001" / "journal.txt").exists() else None),
                 (0, [187, 127, 148], "ranges done")):
        print(out)
        return
    k = copy(a, "k_base")                               # slot 1 ended, slot 2 untouched; K's fence goes below
    (k / "FENCE.json").unlink()
    STATE["l0"] = copy(k, "l0")                         # part V's VL starts here (version 2)
    rc2, out2 = worker(a, 2)
    if not check("fixture A: slot 2 under the fence: exit 0, one seal_only epoch, ended \"finalizer\", "
                 "never_dispatched 3",
                 (rc2, [ln.get("mode") for ln in jlines(a, 2) if ln["t"] == "epoch"], jlines(a, 2)[-1].get("why"),
                  json.loads((a / "ranges" / "r0001.w002.seal.json").read_bytes())["dispositions"]["never_dispatched"]),
                 (0, ["seal_only"], "finalizer", 3)):
        print(out2)
    rc3, out3 = packer(a, CONV)
    check("fixture A: the packer --once with the official converter: exit 0, 3 binpack, 0 raw",
          (rc3, "offered 3 pieces as binpack and 0 as raw" in out3), (0, True))
    STATE["a"] = copy(a, "a_base")                     # the refusals start from this (no inventory yet)
    # K: the state a kill of slot 1 leaves while g4 plays
    j = (k / "w001" / "journal.txt").read_bytes().split(b"\n")[:-1]
    g3 = [i for i, ln in enumerate(j) if json.loads(ln).get("game") == "term-w001-g00000003"]
    end3 = json.loads(j[g3[0]])["end"]
    (k / "w001" / "journal.txt").write_bytes(b"\n".join(j[:g3[0] + 1]) + b"\n")
    (k / "w001" / "open").mkdir(exist_ok=True)
    (k / "w001" / "open" / "p000001.raw").write_bytes((k / "w001" / "closed" / "p000001.raw").read_bytes()[:end3])
    for n in ("p000001.raw", "p000001.seal.json", "p000002.raw", "p000002.seal.json"):
        (k / "w001" / "closed" / n).unlink()
    (k / "ranges" / "r0001.w001.seal.json").unlink()
    check("fixture K: the journal ends with g3's done line, p0 sealed alone, p1 open with g3's bytes",
          (json.loads(j[g3[0]])["t"], sorted(p.name for p in (k / "w001" / "closed").iterdir()),
           (k / "w001" / "open" / "p000001.raw").stat().st_size == end3),
          ("done", ["p000000.raw", "p000000.seal.json"], True))
    u = copy(k, "u")
    fence(u, "D")
    check("fixture U: slot 2 finalized, exit 0", worker(u, 2)[0], 0)
    STATE["u"] = u
    b = copy(k, "b")
    with open(b / "w001" / "open" / "p000001.raw", "ab") as f:
        f.write(f"game term-w001-g00000004 opening {' '.join(N12[3])}\n".encode("ascii"))
    fence(b, "control 1 " + "f" * 64 + ": target REACHED")
    rb = worker(b, 1)
    rs = json.loads((b / "ranges" / "r0001.w001.seal.json").read_bytes()) if (b / "ranges" / "r0001.w001.seal.json").exists() else {}
    check("fixture B: slot 1's finalizer: exit 0, failed g4 (cut), range seal done 3, unfinished 1, never_dispatched 2",
          (rb[0], [ln.get("why") for ln in jlines(b, 1) if ln["t"] == "failed"], {s: rs.get("dispositions", {}).get(s)
           for s in ("done", "unfinished", "dispatch_unknown", "never_dispatched")}),
          (0, [CUT], {"done": 3, "unfinished": 1, "dispatch_unknown": 0, "never_dispatched": 2}))
    rw2 = worker(b, 2)[0]                               # every slot ended first, then the packer's last pass (1.8.4)
    rpk, opk = packer(b, WORK / "no_such_converter.exe")
    check("fixture B: slot 2 finalized, exit 0; the packer with no converter: exit 0, 0 binpack, 2 raw",
          (rw2, rpk, "offered 0 pieces as binpack and 2 as raw" in opk, opk[-120:]), (0, 0, True, opk[-120:]))
    STATE["b"] = b
    c = copy(k, "c")
    fence(c, "D")
    rc_ = worker(c, 1)
    rs = json.loads((c / "ranges" / "r0001.w001.seal.json").read_bytes()) if (c / "ranges" / "r0001.w001.seal.json").exists() else {}
    check("fixture C: slot 1's finalizer: exit 0, dispatch_unknown 1, never_dispatched 2, no failed line",
          (rc_[0], {s: rs.get("dispositions", {}).get(s) for s in ("done", "unfinished", "dispatch_unknown",
                                                                     "never_dispatched")},
           [ln for ln in jlines(c, 1) if ln["t"] == "failed"]),
          (0, {"done": 3, "unfinished": 0, "dispatch_unknown": 1, "never_dispatched": 2}, []))
    check("fixture C: slot 2 finalized, exit 0", worker(c, 2)[0], 0)
    STATE["c"] = copy(c, "c_base")
    STATE["c_run"] = c
    n = WORK / "n"
    header(n, "edge", [0], [row(0, 1, 1)], 1, {"kind": "seed", "plies": 8, "root_seed": "edge2649"})
    rn = play_then_fence(n, 0, "D", openings=False)    # no schedule: the pilot; the fence copies the hard cutoff
    if not check("fixture N: exit 0, g1 noselfgame, ended \"ranges done\"",
                 (rn[0], [ln["t"] for ln in jlines(n, 0) if ln.get("game")], jlines(n, 0)[-1].get("why")),
                 (0, ["noselfgame"], "ranges done")):
        print(rn[1])
    STATE["n"] = n


# ---- the inventories ---------------------------------------------------------------------------------------------
def part_inventories():
    a = copy(STATE["a"], "a_inv")
    t0 = time.time()
    rd = lambda r, rel: (r / rel).read_bytes()  # noqa: E731
    inventory("A", a, [rd(a, "RUN.json"), rd(a, "SCHEDULE.1.json"), rd(a, "FENCE.json"), slot_line(a, 1, "ended", 2),
                       piece_line(a, 1, 0), piece_line(a, 1, 1), piece_line(a, 1, 2), rd(a, "ranges/r0001.w001.seal.json"),
                       slot_line(a, 2, "ended", -1), rd(a, "ranges/r0001.w002.seal.json")], 11,
              {"cutoff_reached": True, "ids": ids(done=6, never_dispatched=3),
               "offered_bytes": sum(json.loads(piece_line(a, 1, i))["offered_bytes"] for i in range(3)), "pieces": 3,
               "pieces_offered": 3, "raw_rows": 462, "slots": {"ended": 2, "unreconciled": 0}, "stop_reason": "D"}, t0)
    STATE["a_inv"] = a
    u = STATE["u"]
    inventory("U", u, [rd(u, "RUN.json"), rd(u, "SCHEDULE.1.json"), rd(u, "FENCE.json"),
                       slot_line(u, 1, "unreconciled", 0), piece_line(u, 1, 0), slot_line(u, 2, "ended", -1),
                       rd(u, "ranges/r0001.w002.seal.json")], 8,
              {"cutoff_reached": True, "ids": ids(never_dispatched=3), "offered_bytes": 0, "pieces": 1,
               "pieces_offered": 0, "raw_rows": 187, "slots": {"ended": 1, "unreconciled": 1}, "stop_reason": "D"},
              time.time())
    check("U the unoffered piece: offer null, offered_bytes 0, packed_bytes null",
          {k: json.loads(piece_line(u, 1, 0))[k] for k in ("offer", "offered_bytes", "packed_bytes")},
          {"offer": None, "offered_bytes": 0, "packed_bytes": None})
    b = STATE["b"]
    why_b = json.loads((b / "FENCE.json").read_bytes())["why"]
    inventory("B", b, [rd(b, "RUN.json"), rd(b, "SCHEDULE.1.json"), rd(b, "FENCE.json"), slot_line(b, 1, "ended", 1),
                       piece_line(b, 1, 0), piece_line(b, 1, 1), rd(b, "ranges/r0001.w001.seal.json"),
                       W.canon({"game": "term-w001-g00000004", "state": "unfinished", "t": "id", "why": CUT}),
                       slot_line(b, 2, "ended", -1), rd(b, "ranges/r0001.w002.seal.json")], 11,
              {"cutoff_reached": False, "ids": ids(done=3, unfinished=1, never_dispatched=5),
               "offered_bytes": sum(json.loads(piece_line(b, 1, i))["offered_bytes"] for i in range(2)), "pieces": 2,
               "pieces_offered": 2, "raw_rows": 187, "slots": {"ended": 2, "unreconciled": 0}, "stop_reason": why_b},
              time.time())
    c = STATE["c_run"]
    inventory("C", c, [rd(c, "RUN.json"), rd(c, "SCHEDULE.1.json"), rd(c, "FENCE.json"), slot_line(c, 1, "ended", 1),
                       piece_line(c, 1, 0), piece_line(c, 1, 1), rd(c, "ranges/r0001.w001.seal.json"),
                       W.canon({"game": "term-w001-g00000004", "state": "dispatch_unknown", "t": "id", "why": DOUBT}),
                       slot_line(c, 2, "ended", -1), rd(c, "ranges/r0001.w002.seal.json")], 11,
              {"cutoff_reached": True, "ids": ids(done=3, dispatch_unknown=1, never_dispatched=5), "offered_bytes": 0,
               "pieces": 2, "pieces_offered": 0, "raw_rows": 187, "slots": {"ended": 2, "unreconciled": 0},
               "stop_reason": "D"}, time.time())
    n = STATE["n"]
    inventory("N", n, [rd(n, "RUN.json"), W.canon({"n": 0, "t": "schedule"}), rd(n, "FENCE.json"),
                       slot_line(n, 0, "ended", 0), piece_line(n, 0, 0), rd(n, "ranges/r0001.w000.seal.json"),
                       W.canon({"game": "edge-w000-g00000001", "state": "noselfgame", "t": "id", "why": "nomoves"})], 8,
              {"cutoff_reached": True, "ids": ids(noselfgame=1), "offered_bytes": 0, "pieces": 1, "pieces_offered": 0,
               "raw_rows": 0, "slots": {"ended": 1, "unreconciled": 0}, "stop_reason": "D"}, time.time())


# ---- refusals and the rest ---------------------------------------------------------------------------------------
def rewrite(path: Path, fn) -> None:
    path.write_bytes(W.canon(fn(json.loads(path.read_bytes()))))


def refused(name: str, root: Path, why: str):
    rc, out = terminal(root)
    check(f"{name}: exit 4, nothing written", (rc, (root / "TERMINAL.jsonl").exists(),
                                               (root / "TERMINAL.jsonl.zz").exists()), (4, False, False))
    check(f"{name}: the refusal names its own cause", (why in out, out[-200:]), (True, out[-200:]))


def part_refusals():
    a = STATE["a"]
    r = copy(a, "r1")
    rewrite(r / "w001" / "closed" / "p000000.seal.json", lambda s: dict(s, rows=s["rows"] + 1))
    refused("R1 slot 1's p000000 seal changed", r, "p000001.seal.json does not descend")
    r = copy(a, "r2")
    o = r / "out" / "w001" / "p000001.offer.json"
    rewrite(o, lambda x: dict(x, seal_sha256="0" * 64))
    (o.with_name(o.name + ".zz")).write_bytes(zlib.compress(o.read_bytes(), 6))
    refused("R2 p000001's offer naming another seal", r, "is not the offer of this seal")
    r = copy(a, "r3")
    (r / "out" / "w001" / "p000002.offer.json.zz").write_bytes(zlib.compress(b"other\n", 6))
    refused("R3 p000002's offer .zz of other bytes", r, "does not decode to the plain offer")
    r = copy(a, "r4")
    (r / "w001" / "closed" / "p000000.seal.json").unlink()
    refused("R4 p000000's seal missing before later ones", r, "p000000.seal.json is missing before later seals")
    r = copy(a, "r5")
    rewrite(r / "ranges" / "r0001.w001.seal.json", lambda s: dict(s, through_seal="0" * 64))
    refused("R5 r0001.w001's through_seal another sha256", r, "its pieces are not the chain's")
    r = copy(a, "r6")
    (r / "w001" / "closed" / "p000002.seal.json").unlink()
    j = (r / "w001" / "journal.txt").read_bytes().split(b"\n")[:-1]
    j = [ln for ln in j if not (json.loads(ln)["t"] == "closed" and json.loads(ln)["index"] == 2)]
    (r / "w001" / "journal.txt").write_bytes(b"\n".join(j) + b"\n")
    refused("R6 the ended line names p000002, whose seal is gone", r, "the ended line names index 2")
    r = copy(a, "r7")
    (r / "FENCE.json").unlink()
    refused("R7 no FENCE.json", r, "no FENCE.json")
    r = copy(a, "r8")
    rewrite(r / "SCHEDULE.1.json", lambda s: dict(s, prev="x"))
    refused("R8 SCHEDULE.1 with prev x", r, "linked to the one before it")
    r = copy(a, "r9")
    shutil.copyfile(r / "out" / "w001" / "p000000.offer.json", r / "out" / "w001" / "p000007.offer.json")
    refused("R9 an offer of p000007", r, "an offer of p000007")
    r = copy(a, "r13")
    j = (r / "w001" / "journal.txt").read_bytes().split(b"\n")
    j[1] = j[1].replace(b'"rows":86', b'"rows":86.0')
    (r / "w001" / "journal.txt").write_bytes(b"\n".join(j))
    refused("R13 a decimal number in slot 1's journal line 2", r, "w001/journal.txt line 2")
    r = copy(STATE["c"], "r14")
    j = (r / "w001" / "journal.txt").read_bytes().split(b"\n")[:-1]
    j.insert(len(j) - 1, W.canon({"game": "term-w001-g00000004", "t": "failed", "why": "x"})[:-1])
    (r / "w001" / "journal.txt").write_bytes(b"\n".join(j) + b"\n")
    refused("R14 a dispatch_unknown id with a journal line", r, "is dispatch_unknown and has a journal line")
    done = STATE.get("a_inv")
    if done is None:
        check("R10 to R12: the finished root A", False, True)
        return
    r = copy(done, "r10")
    (r / "TERMINAL.jsonl").write_bytes(b"other\n")
    (r / "TERMINAL.jsonl.zz").unlink()
    rc, out = terminal(r)
    check("R10 another TERMINAL.jsonl there: exit 4, it is unchanged, no .zz made, the cause named",
          (rc, (r / "TERMINAL.jsonl").read_bytes(), (r / "TERMINAL.jsonl.zz").exists(),
           "is not this spool's inventory" in out), (4, b"other\n", False, True))
    r = copy(done, "r11")
    before = (r / "TERMINAL.jsonl").read_bytes()
    (r / "TERMINAL.jsonl.zz").unlink()
    rc, out = terminal(r)
    check("R11 a finished root without its .zz: exit 0, the .zz made again, TERMINAL.jsonl unchanged",
          (rc, (r / "TERMINAL.jsonl").read_bytes() == before, (r / "TERMINAL.jsonl.zz").exists()
           and zlib.decompress((r / "TERMINAL.jsonl.zz").read_bytes()) == before), (0, True, True))
    r = copy(done, "r12")
    files = {p.name: p.read_bytes() for p in (r / "TERMINAL.jsonl", r / "TERMINAL.jsonl.zz")}
    rc, out = terminal(r)
    check("R12 a second run: exit 0, both files unchanged",
          (rc, {p.name: p.read_bytes() for p in (r / "TERMINAL.jsonl", r / "TERMINAL.jsonl.zz")} == files), (0, True))
    rc, out = terminal(WORK / "n12_openings.txt")
    check("E1 a root that is not a folder: exit 2", rc, 2)


# ---- part V: version 2 (the known answers' CHANGED section) ----------------------------------------------------
def forge(root: Path, rel: str, fn) -> None:
    """A range seal changed by fn and written canonical; its .zz, where there is one, written again from the new
    bytes, so that A5 does not refuse first."""
    p = root / rel
    p.write_bytes(W.canon(fn(json.loads(p.read_bytes()))))
    z = p.with_name(p.name + ".zz")
    if z.exists():
        z.write_bytes(zlib.compress(p.read_bytes(), 6))


def disp(**kw):
    """For forge(): the dispositions changed by kw, nothing else."""
    return lambda s: dict(s, dispositions=dict(s["dispositions"], **kw))


def bare_n(name: str, fn) -> Path:
    """A root holding N's RUN.json changed by fn and a FENCE.json for its fingerprint, nothing else (slot 0 never ran)."""
    r = WORK / name
    put(r / "RUN.json", W.canon(fn(json.loads((STATE["n"] / "RUN.json").read_bytes()))))
    fence(r, "D")
    return r


def gid(k: int, c: int) -> str:
    return f"term-w{k:03d}-g{c:08d}"


def part_v():
    a, rd = STATE["a"], (lambda r, rel: (r / rel).read_bytes())
    R1, R2 = "ranges/r0001.w001.seal.json", "ranges/r0001.w002.seal.json"
    check("part V: fixture A's two range seals have their wire copies (the packer's)",
          [(a / (x + ".zz")).exists() for x in (R1, R2)], [True, True])
    foot_a = {"cutoff_reached": True, "ids": ids(done=6, never_dispatched=3),
              "offered_bytes": sum(json.loads(piece_line(a, 1, i))["offered_bytes"] for i in range(3)), "pieces": 3,
              "pieces_offered": 3, "raw_rows": 462, "slots": {"ended": 2, "unreconciled": 0}, "stop_reason": "D"}
    # T-A: each seal against the schedule it names; an ended slot against schedule L
    r = copy(a, "va1")
    put(r / "ranges" / "r0002.w001.seal.json", W.canon(dict(json.loads(rd(r, R1)), round=2)))
    refused("VA1 a seal of round 2, of which schedule 1 has no row", r, "no range of round 2")
    r = copy(a, "va2")
    forge(r, R2, lambda s: dict(s, last=2, dispositions=dict(s["dispositions"], never_dispatched=2,
                                                              never_dispatched_first=1)))
    refused("VA2 r0001.w002 with last 2", r, "not the schedule's range")
    for name, rel in (("VA3", R1), ("VA3b", R2)):
        r = copy(a, name.lower())
        (r / rel).unlink()
        (r / (rel + ".zz")).unlink()
        refused(f"{name} {rel} and its wire copy gone", r, f"{rel[7:]} is missing")
    r = copy(a, "va4")
    (r / R1).unlink()
    inventory("VA4", r, [rd(a, "RUN.json"), rd(a, "SCHEDULE.1.json"), rd(a, "FENCE.json"), slot_line(r, 1, "ended", 2),
                         piece_line(r, 1, 0), piece_line(r, 1, 1), piece_line(r, 1, 2), rd(a, R1),
                         slot_line(r, 2, "ended", -1), rd(a, R2)], 11, foot_a, time.time())
    r = copy(a, "va5")
    (r / (R1 + ".zz")).write_bytes(zlib.compress(rd(r, R2), 6))
    refused("VA5 r0001.w001's wire copy holds r0001.w002's bytes", r, "does not decode to the plain range seal")
    # T-B: a range without a piece
    for name, fn, why in (("VB1 r0001.w002 first_index 42", lambda s: dict(s, first_index=42), "a range without a piece"),
                          ("VB2 r0001.w002 first_prev_seal 64 zeros", lambda s: dict(s, first_prev_seal="0" * 64),
                           "a range without a piece"),
                          ("VB3 r0001.w002 through_seal BOGUS", lambda s: dict(s, through_seal="BOGUS"),
                           "a range without a piece"),
                          ("VB4 r0001.w002 done 3, never_dispatched 0",
                           disp(done=3, never_dispatched=0, never_dispatched_first=None), "no game")):
        r = copy(a, name.split()[0].lower())
        forge(r, R2, fn)
        refused(name, r, why)
    # T-C: the counts
    r = copy(STATE["c"], "vc1")
    forge(r, R1, disp(done=-1, never_dispatched=6, never_dispatched_first=1))
    refused("VC1 C's r0001.w001 done -1 (never_dispatched 6 from 1, g4 dispatch_unknown kept)", r, ">= 0")
    for name, rel, fn, why in (
            ("VC2 r0001.w001 done 5", R1, disp(done=5), "sum"),
            ("VC3 r0001.w002 dispatch_unknown 1 without its pair", R2,
             disp(never_dispatched=2, never_dispatched_first=2, dispatch_unknown=1, not_done=[]), "pairs"),
            ("VC4 r0001.w002 never_dispatched_first 2", R2, disp(never_dispatched_first=2), "never_dispatched_first"),
            ("VC4b r0001.w002 never_dispatched 0 with never_dispatched_first 3", R2,
             disp(dispatch_unknown=3, never_dispatched=0, never_dispatched_first=3,
                  not_done=[[gid(2, c), "dispatch_unknown"] for c in (1, 2, 3)]), "never_dispatched_first"),
            ("VC5a r0001.w002 an id of counter 9", R2,
             disp(dispatch_unknown=1, never_dispatched=2, never_dispatched_first=2,
                  not_done=[[gid(2, 9), "dispatch_unknown"]]), "not an id of the range"),
            ("VC5b r0001.w002 g1 twice", R2,
             disp(dispatch_unknown=2, never_dispatched=1, never_dispatched_first=3,
                  not_done=[[gid(2, 1), "dispatch_unknown"]] * 2), "rise")):
        r = copy(a, name.split()[0].lower())
        forge(r, rel, fn)
        refused(name, r, why)
    # T-D: strays
    r = copy(a, "vd1")
    (r / "out" / "w001" / "p000099.offer.json.zz").write_bytes(b"x")
    refused("VD1 out/w001/p000099.offer.json.zz beyond the chain", r, "an offer of p000099")
    r = copy(a, "vd2")
    shutil.copyfile(r / "SCHEDULE.1.json", r / "SCHEDULE.01.json")
    refused("VD2 SCHEDULE.01.json beside SCHEDULE.1.json", r, "SCHEDULE.01.json")
    # T-F: schema
    r = bare_n("vf1", lambda h: dict(h, schema=1))
    refused("VF1 RUN.json schema 1", r, "RUN.json: not schema 2")
    r = bare_n("vf1c", lambda h: h)
    rc, out = terminal(r)
    want = W.canon({"epochs": [], "last_index": -1, "last_seal": f"genesis:{sha(rd(r, 'RUN.json'))}:w000", "slot": 0,
                    "state": "unreconciled", "t": "slot"})
    check("VF1c control: N's RUN.json unchanged, no slot file: exit 0, slot 0 unreconciled",
          (rc, (r / "TERMINAL.jsonl").exists() and want in rd(r, "TERMINAL.jsonl"), out[-160:] if rc else ""),
          (0, True, ""))
    r = copy(a, "vf2")
    rewrite(r / "FENCE.json", lambda f: dict(f, extra=1))
    refused("VF2 FENCE.json with a key more", r, "FENCE.json: not the keys of a fence")
    r = copy(a, "vf3")
    rewrite(r / "FENCE.json", lambda f: dict(f, schema=1))
    refused("VF3 FENCE.json schema 1", r, "FENCE.json: not schema 2")
    # T-E: coverage
    r = copy(a, "ve1")
    j = rd(r, "w001/journal.txt").split(b"\n")[:-1]
    check("VE1: slot 1's journal ends with its ended line", json.loads(j[-1])["t"], "ended")
    (r / "w001" / "journal.txt").write_bytes(b"\n".join(j[:-1]) + b"\n")
    rewrite(r / "SCHEDULE.1.json", lambda s: dict(s, ranges=s["ranges"] + [
        {"first": 7, "last": 9, "round": 2, "schedule": 1, "short": False, "slot": 1}]))
    c_ = copy(r, "ve1c")
    s = json.loads(rd(r, R1))
    put(r / "ranges" / "r0002.w001.seal.json", W.canon(dict(s, round=2, first=7, last=9, dispositions=dict(
        s["dispositions"], done=0, never_dispatched=3, never_dispatched_first=7))))
    refused("VE1 r0002.w001 names slot 1's pieces 0 to 2 again", r, "in two range seals")
    rc, out = terminal(c_)
    check("VE1c control (VE1 without r0002.w001): exit 0, slot 1 unreconciled to p000002",
          (rc, (c_ / "TERMINAL.jsonl").exists() and slot_line(c_, 1, "unreconciled", 2) in rd(c_, "TERMINAL.jsonl"),
           out[-160:] if rc else ""), (0, True, ""))
    r = copy(a, "ve2")
    p0 = sha(rd(r, "w001/closed/p000000.seal.json"))
    forge(r, R1, lambda s: dict(s, first_index=1, first_prev_seal=p0))
    refused("VE2 r0001.w001 from p000001: p000000 in no range", r, "not in a range")
    # the late schedule (CHANGED section): VL, VL2, VL3
    v = copy(STATE["l0"], "vl")
    s1b = rd(v, "SCHEDULE.1.json")
    s1 = json.loads(s1b)
    g = object.__new__(G.Guard)                         # the guard's own new_schedule writes SCHEDULE.2
    g.sched, g.h, g.fp = [(s1b, s1)], json.loads(rd(v, "RUN.json")), sha(rd(v, "RUN.json"))
    put(v / "SCHEDULE.2.json", g.new_schedule("0" * 64, 2, s1["cutoff_utc"], s1["dispatch_end_utc"]))
    fence(v, "D")
    rc, out = worker(v, 2)
    seals = [json.loads(rd(v, f"ranges/r000{x}.w002.seal.json")) if (v / f"ranges/r000{x}.w002.seal.json").exists()
             else {} for x in (1, 2)]
    if not check("fixture VL: SCHEDULE.2 (new_schedule) adds round 2, slot 1 7 to 12 and slot 2 4 to 6; slot 2's start "
                 "under the fence: exit 0, seal_only, seals of rounds 1 and 2 naming schedule 2, never_dispatched 3 each",
                 (rc, sorted((x["slot"], x["first"], x["last"], x["schedule"], x["short"])
                             for x in json.loads(rd(v, "SCHEDULE.2.json"))["ranges"] if x["round"] == 2),
                  [ln.get("mode") for ln in jlines(v, 2) if ln["t"] == "epoch"],
                  [(x.get("schedule"), x.get("dispositions", {}).get("never_dispatched")) for x in seals]),
                 (0, [(1, 7, 12, 2, False), (2, 4, 6, 2, False)], ["seal_only"], [(2, 3), (2, 3)])):
        print(out)
        return
    r = copy(v, "vl2")
    (r / "ranges" / "r0002.w002.seal.json").unlink()
    refused("VL2 VL without r0002.w002.seal.json (r0001.w002 names schedule 2)", r, "r0002.w002.seal.json is missing")
    inventory("VL", v, [rd(v, "RUN.json"), s1b, rd(v, "SCHEDULE.2.json"), rd(v, "FENCE.json"),
                        slot_line(v, 1, "ended", 2), piece_line(v, 1, 0), piece_line(v, 1, 1), piece_line(v, 1, 2),
                        rd(v, R1), slot_line(v, 2, "ended", -1), rd(v, R2), rd(v, "ranges/r0002.w002.seal.json")], 13,
              {"cutoff_reached": True, "ids": ids(done=6, never_dispatched=6), "offered_bytes": 0, "pieces": 3,
               "pieces_offered": 0, "raw_rows": 462, "slots": {"ended": 2, "unreconciled": 0}, "stop_reason": "D"},
              time.time())
    rc, out = terminal(v)
    check("VL a second run: exit 0, the output names slot 1's round 2 as without a range seal",
          (rc, "w001 ended without a range seal of round(s) [2]" in out), (0, True))
    r = copy(a, "vl3")
    s1b = rd(r, "SCHEDULE.1.json")
    s1 = json.loads(s1b)
    rows = [dict(x, last=2, short=True, schedule=2) if x["slot"] == 2 else x for x in s1["ranges"]]
    put(r / "SCHEDULE.2.json", W.canon(dict(s1, n=2, prev=sha(s1b), ranges=rows)))
    check("fixture VL3: SCHEDULE.2 has the schedule keys and passes the worker's check_rows",
          (sorted(json.loads(rd(r, "SCHEDULE.2.json"))) == W.SCHEDULE_KEYS, W.check_rows(rows, [1, 2], 2, "VL3") == rows),
          (True, True))
    inventory("VL3", r, [rd(r, "RUN.json"), s1b, rd(r, "SCHEDULE.2.json"), rd(r, "FENCE.json"),
                         slot_line(r, 1, "ended", 2), piece_line(r, 1, 0), piece_line(r, 1, 1), piece_line(r, 1, 2),
                         rd(r, R1), slot_line(r, 2, "ended", -1), rd(r, R2)], 12, foot_a, time.time())
    # A0: the worker's check_rows
    r = copy(a, "vs1")
    rewrite(r / "SCHEDULE.1.json", lambda s: dict(s, ranges=[dict(x, round="1") if x["slot"] == 1 else x
                                                             for x in s["ranges"]]))
    refused("VS1 SCHEDULE.1's slot 1 row with round \"1\" (a text)", r, "a range row that is not 1.2's")
    r = bare_n("vs2", lambda h: dict(h, pilot_ranges=[dict(h["pilot_ranges"][0], last=0)]))
    refused("VS2 RUN.json's pilot row with last 0", r, "a range row that is not 1.2's")


safe(fixtures)
if "n" in STATE:
    safe(part_inventories)
    safe(part_refusals)
    safe(part_v)
else:
    check("the fixtures were made", False, True)
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)

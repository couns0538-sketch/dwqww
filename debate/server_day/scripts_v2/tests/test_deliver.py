"""test_deliver.py: home/deliver.py (the home delivery of the owner's decisions) against known answers written BEFORE
the code (tmp/opus_scratch/deliver/KNOWN_ANSWERS_deliver_by_opus.md on the PC, with Fable's H1 to H4). Standard
library only; a PLAIN interpreter (it starts python processes itself); Windows (the home PC).

    test_deliver.py <tree> <a NEW folder> [plantN]

<tree> holds home/ (deliver.py, fetch.py), tools/ (make_control.py, budget.py) and run/ (worker.py, guard.py); it is
copied into the new folder and a plant changes the copy's home/deliver.py only. Every transfer goes through the REAL
client: Windows' own sftp.exe talks through -D to Git for Windows' sftp-server.exe, which serves this test's folders
(no network, no key); only the command line is replaced, as in test_fetch.py F20. The decisions come from the REAL
budget tool and the REAL make_control.py (--accepted DIR/deliver/sent: the sent chain); the REAL server guard
(run/guard.py in-process, no worker; test_make_control.py's fixture) takes what arrived in its inbox; "the fetch" is a
copy of the guard's SCHEDULE.<n>.json and FENCE.json into DIR/wire as .zz files.
P   P1 the probe through the real client: passed, both names gone, a journal line passed true; P3 a send without a
    probe: exit 3 "no passed probe", nothing in the inbox.
U   (U1, D6, H1) UNQUALIFIED pilot_decision 1: sent (the inbox holds exactly its two .zz, equal; no dot-name; the
    evidence put before the control); the guard accepts it (no schedule); observe: not seen, nothing written. A target
    SELF_PLAY 2 built on the sent chain: NOT held; 1's files "there already", 2's put; the guard accepts it and writes
    SCHEDULE.1 naming 2; after the fetch, observe records 1 AND 2 (the sent bytes and both evidence files); a second
    observe changes nothing; a fence 3: sent, the guard's FENCE.json names it, observe records 3.
U2  the same start on a guard whose policy file differs (G3 c holds control 1 for good): 2 is sent, never read; no
    schedule; observe records nothing.
W   (DV2's waiting rule) SELF_PLAY 1 sent, not seen: a target 2 is HELD naming control 1 (nothing new in the inbox); a
    fence 2 is sent.
R   (re-delivery) control 1 with the server unreachable (a stand-in client: "Connection refused"): exit 7, sent/
    holds it, the inbox empty; a fence 2 built on it: exit 0, the journal's file lines EVIDENCE(1), CONTROL.1,
    EVIDENCE(2), CONTROL.2, all put; the inbox holds the four.
C   C1 CONFLICT: the inbox holds CONTROL.1.json.zz with other bytes: exit 3 naming it, its bytes unchanged. C2 the race
    (the final name appears just before the rename): exit 3 CONFLICT, the other bytes unchanged. C3 (H3) the dot-name
    read back with other bytes: exit 7, no final name. C4 the sender stopped before the control: the inbox holds the
    evidence only; the retry: exit 0, evidence there already, control put, each final file equal. C5 a stale dot-name:
    overwritten, the final equal, no dot-name left. C6 (H4) a two-space HOME and NEWDIR: probe and send exit 0.
D1  refused input, exit 4, sent/ and the inbox empty: a fifth file; a missing .zz; a .zz of the other file; a short
    evidence (name not its sha256); another run's control; an evidence with local_only; owner_policy not the
    evidence's plan; a home whose wire/RUN.json.zz is another run's (and nothing made by that refusal: Fable's D2).
D2  k 2 on an empty sent chain: HELD; another control under the same k: HELD; a retry of the same bytes: exit 0, no
    `put` line in its batches.
D3  a cutoff one second later than the one in force: HELD; D come (a schedule in wire/ whose cutoff passed): a
    SELF_PLAY control HELD "D has come", a fence with the same bounds sent.
D5  the host key and the refused login (a stand-in client printing ssh's texts): exit 6, the ONLY batch line an
    `ls -ln "`, the inbox empty, sent/ holds the decision (written before the first byte), no file line.
L   the process: observe while the test holds DIR/deliver/LOCK: exit 8; send without --config: exit 2; observe:
    exit 0 and a line "deliver: observe". L4 to L6 (Fable's D2): a new empty folder, another run's header, a header
    that is not zlib: exit 4 and nothing made there; L7 the control: this run's header alone, the folders are made.
    L4b (Fable) a --home that does not exist: exit 2, still not there; L6b (Fable) a header that is zlib and has the
    fingerprint but is no record: exit 4, no traceback, nothing made.
v16 (25 Nov; the clock known answers tmp/opus_scratch/clock/KNOWN_ANSWERS_clock_by_opus.md, DL1 to DL3, ADDENDUM 2's
P3 and ADDENDUM 7): deliver's D check takes the SERVER's time (home/clock.py's server_now). Every home gets ONE ok
clock line of its run in the test's world (the server's time = the PC's), so every check above keeps its meaning.
P3b the probe's positive step through the real client: moved true, exactly two `rename -l` lines (a onto b, a
    onto the free c), the inbox empty. P3c a client whose every `rename -l` fails: the probe FAILS, exit 3, naming
    the move onto a free name (v15's probe passed it).
DL  the PC 25,178 s AHEAD of the server; a schedule in wire/ whose cutoff is 30 s after the server's now (25,148 s
    before the PC's): DL1 a SELF_PLAY control with those bounds is SENT (v15: HELD); DL1b the server's clock 1 s
    past the cutoff: HELD "D has come", a fence with the same bounds sent; DL2 no clock line: HELD naming "no clock
    line of this run", a fence sent without a clock.
PLANTS: see PLANTS below (each must make the test fail). v16: plant14 the move forced true (P3d: P3c FAILs);
plant15 deliver's now from the PC's clock again (DL3: DL1 FAILs).
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
from types import SimpleNamespace

if len(sys.argv) < 3:
    print("usage: test_deliver.py <tree> <a NEW folder> [plantN]")
    sys.exit(2)
SRC_TREE, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
PLANT = sys.argv[3] if len(sys.argv) > 3 else None
SFTP = Path("C:/Windows/System32/OpenSSH/sftp.exe")
SERVER = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git" / "usr" / "lib" / "ssh" / "sftp-server.exe"
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
if not (SFTP.is_file() and SERVER.is_file()):
    print(f"STOP: the real client {SFTP} and Git's server {SERVER} are needed")
    sys.exit(2)
WORK.mkdir(parents=True)
TREE = WORK / "tree"
shutil.copytree(SRC_TREE, TREE, ignore=shutil.ignore_patterns("__pycache__", "MANIFEST.sha256"))
PLANTS = {
    "plant1": [("w.run([f'rename -l \"{dot}\"", "w.run([f'rename \"{dot}\"")],
    "plant2": [("(f\"EVIDENCE.{c['evidence']}.json.zz\", f\"CONTROL.{c['k']}.json.zz\")",
                "(f\"CONTROL.{c['k']}.json.zz\", f\"EVIDENCE.{c['evidence']}.json.zz\")")],
    "plant3": [('        if res == "long" or (res == 0 and got != data):\n', "        if False:\n")],
    "plant4": [('            if sent[k - 1][0] != d["plain"]:\n', "            if False:\n")],
    "plant5": [("        if c_cut > cut or c_disp > disp or c_disp > c_cut:\n", "        if c_disp > c_cut:\n")],
    "plant6": [("        listed = self.listing(w)                        # DV5", "        listed = {}  # DV5")],
    "plant7": [("if sha256_bytes(cb) in named or (why and sha256_bytes(cb) in why)]", "if True]")],
    "plant8": [('    for name, data in d["files"]:                       # the sent chain, BEFORE the first byte travels\n'
                '        create_only(home.sent / name, data)\n', ""),
               ('    home.note(t="sent", k=d["k"]', '    [create_only(home.sent / n, b) for n, b in d["files"]]\n'
                                                 '    home.note(t="sent", k=d["k"]')],
    "plant9": [('c["kind"] != "fence" and visible(sent[-1][1]) and', 'c["kind"] != "fence" and')],
    "plant10": [('c["kind"] != "fence" and visible(sent[-1][1]) and', "visible(sent[-1][1]) and")],
    "plant11": [("            if got != data:\n"
                 "                raise Stop(7, f\".{name}.part read back with other bytes ({len(got)} of {len(data)}): no "
                 "rename\")\n"
                 "            rc, text = w.run([f'rename -l \"{dot}\" \"{w.inbox}/{name}\"'])\n",
                 "            rc, text = w.run([f'rename -l \"{dot}\" \"{w.inbox}/{name}\"'])\n"
                 "            if got != data:\n"
                 "                raise Stop(7, f\".{name}.part read back with other bytes ({len(got)} of {len(data)}): no "
                 "rename\")\n")],
    "plant12": [("w.run([f'rename -l \"{w.inbox}/{a}\" \"{w.inbox}/{b}\"'])",
                 "w.run([f'rename \"{w.inbox}/{a}\" \"{w.inbox}/{b}\"'])")],
    "plant13": [('        p = self.wire / "RUN.json.zz"\n',
                 '        self.ddir.mkdir(exist_ok=True)\n        self.seen.mkdir(exist_ok=True)\n'
                 '        p = self.wire / "RUN.json.zz"\n')],   # the folders before the header (D2)
    "plant14": [("    moved = rc == 0 and b in after and c in after and a not in after\n", "    moved = True\n")],
    "plant15": [("                now = CK.server_now(self.home, self.fp)\n",
                 "                now = __import__(\"time\").time()\n")],
}
DP = TREE / "home" / "deliver.py"
text = DP.read_bytes().decode("ascii")
if PLANT:
    if PLANT not in PLANTS or any(text.count(old) != 1 for old, _ in PLANTS[PLANT]):
        print(f"STOP: {PLANT}: no such plant, or one of its texts does not stand exactly once")
        sys.exit(2)
    for old, new in PLANTS[PLANT]:
        text = text.replace(old, new)
    DP.write_bytes(text.encode("ascii"))
    print(f"PLANT {PLANT} applied to the copy")
sys.path.insert(0, str(TREE / "run"))
sys.path.insert(0, str(TREE / "tools"))
sys.path.insert(0, str(TREE / "home"))
import guard as G  # noqa: E402
import worker as W  # noqa: E402
import fetch as F  # noqa: E402
import deliver as D  # noqa: E402
RESULTS = []


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {str(got)[:300]}" + ("" if ok else f"; want {str(want)[:300]}"),
          flush=True)
    return ok


def safe(name, fn):
    try:
        fn()
    except Exception:  # noqa: BLE001   a crash inside a part is one FAIL, and the other parts still run
        check(f"{name} ran to its end", traceback.format_exc().rstrip()[-290:], "no exception")  # ends with the error


def sha(b):
    return hashlib.sha256(b).hexdigest()


def T(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t)))


# ---- the budget tool's inputs and the day (test_make_control.py's fixture, version 3) ---------------------------------
PLAN = {"target_rows": 2000000000, "lease_end_s": 90000, "closing_s": 1800, "game_margin_s": 300,
        "pilot_rounds_declared": 1, "floor_fraction": 0.5, "match_margin": 1.10,
        "owner_choice": {"name": "reduced target", "reduced_target_rows": 1546400000, "action": "reduced_target",
                         "if_uncovered": "stop"},
        "match_queue": [["a", 2000], ["b", 2000], ["big", 100000], ["c", 2000]]}
STATE = {"now_s": 7200, "c4_rows": 34400000}
PILOT = {"rounds_whole": 1, "queues_empty_at_start": True, "carry_in_rows": 0, "cohort_games": 125000,
         "cohort_raw_rows": 16000000, "cohort_c4_rows": 15200000, "cohort_seconds": 500, "games_per_h": 2000000,
         "c1_raw_rows_per_s": 100000, "c2_raw_rows_per_s": 100000, "c3_games_per_s": 1000,
         "c4_kept_rows_per_s": 90000, "longest_game_s": 300, "match_games_per_h": 12000}
RAW = WORK / "raw_measurements.txt"
RAW.write_bytes(b"stand-in raw file: every measured input of these cases names it\n")
SRC = {"path": str(RAW), "sha256": sha(RAW.read_bytes())}
NEEDS = {"plan": ("lease_end_s", "closing_s"), "state": ("c4_rows",), "pilot": tuple(PILOT)}
L = int(time.time()) // 60 * 60 - 600
PILOT_ROWS = [{"first": 1, "last": 4, "round": 1, "schedule": 0, "short": False, "slot": k} for k in (1, 2)]


def header(instance="test-instance"):
    return W.canon({"schema": 2, "run": "dv", "lease_start_utc": T(L), "lease_end_utc": T(L + 90000),
                    "hard_cutoff_utc": T(L + 82800), "boot_id": W.boot_id(), "instance": instance,
                    "package": "0" * 64, "engine_sha256": "1" * 64, "net_sha256": "2" * 64,
                    "options_sha256": "3" * 64, "game_line": "go nodes 1",
                    "opening_rule": {"kind": "seed", "plies": 8, "root_seed": "s"}, "slots": [1, 2], "piece_games": 4,
                    "pilot_ranges": PILOT_ROWS})


HB, HB2 = header(), header(instance="substitute")
FP, FP2 = sha(HB), sha(HB2)


def budget(name, plan=PLAN, state=STATE, pilot=PILOT):
    paths = {}
    for kind, obj in (("plan", plan), ("state", state), ("pilot", pilot)):
        o = dict(obj, sources={k: SRC for k in NEEDS[kind]})
        if kind != "plan":
            o["run_fingerprint"] = FP
        paths[kind] = WORK / f"{name}.{kind}.json"
        paths[kind].write_text(json.dumps(o), encoding="ascii")
    r = subprocess.run([sys.executable, "-I", "-B", str(TREE / "tools" / "budget.py"),
                        *[str(paths[k]) for k in ("plan", "state", "pilot")]], capture_output=True)
    rp = WORK / f"{name}.report.json"
    rp.write_bytes(r.stdout)
    return rp, paths


def make_root(name):
    """A day's root with one sealed piece of slot 1 (the guard's room test) and an empty inbox."""
    root = WORK / name
    (root / "w001" / "closed").mkdir(parents=True)
    (root / "inbox").mkdir()
    (root / "RUN.json").write_bytes(HB)
    (root / "w001" / "closed" / "p000000.seal.json").write_bytes(W.canon({
        "epoch": 1, "first_counter": 1, "first_game": "dv-w001-g00000001", "games": 4, "ids_digest": "4" * 64,
        "index": 0, "last_counter": 4, "last_game": "dv-w001-g00000004", "prev_seal": f"genesis:{FP}:w001",
        "raw_bytes": 4000, "raw_sha256": "5" * 64, "round": 1, "rows": 100, "run": "dv", "run_fingerprint": FP,
        "schedule": 0, "schema": 2, "slot": 1}))
    return root


def guard(root, pol):
    a = SimpleNamespace(root=str(root), exe=str(WORK / "no_engine.exe"), net="n", manifest="m", known_startup="k",
                        converter=str(WORK / "no_converter"), policy=str(pol), floor_bytes=0, openings="",
                        game_seconds=600.0, horizon=2, tick=0.1, allowance=2.0, end_grace=2.0, python=sys.executable)
    g = G.Guard(a)
    g.replay_controls()
    return g


def done(g):
    g.lock.release()
    g.log.close()


def clock_line(h: Path, fp: str, behind_s: float = 0.0) -> None:
    """v16 (ADDENDUM 7): ONE ok clock line of run fp in h/clock/journal.jsonl, as home/clock.py's measure writes
    it: the server's time = the PC's now - behind_s.
    v17 (CL1): with mono0, the steady clock read right BEFORE, as measure writes it."""
    mono0 = time.monotonic()
    wall, mono = time.time(), time.monotonic()
    line = W.canon({"impl": time.get_clock_info("monotonic").implementation, "look": 2, "mono0": mono0, "mono": mono, "n": 1,
                    "ok": True, "platform": sys.platform, "run": fp, "state": "play", "t": "clock",
                    "utc_ms": int((wall - behind_s) * 1000), "wall": wall, "why": None})
    (h / "clock").mkdir(parents=True, exist_ok=True)
    (h / "clock" / "journal.jsonl").write_bytes(line)


def new_home(name, hb=HB) -> Path:
    h = WORK / name
    (h / "wire").mkdir(parents=True)
    (h / "deliver" / "sent").mkdir(parents=True)
    (h / "wire" / "RUN.json.zz").write_bytes(zlib.compress(hb, 6))
    clock_line(h, sha(hb))                            # v16: the server's time = the PC's (ADDENDUM 7)
    return h


def mk(rp, paths, home, kind, out):
    """The REAL make_control.py on the sent chain: (exit code, text)."""
    extra = [] if kind == "fence" else ["--state", str(paths["state"]), "--pilot", str(paths["pilot"])]
    r = subprocess.run([sys.executable, "-I", "-B", str(TREE / "tools" / "make_control.py"), "--report", str(rp),
                        "--header", str(WORK / "RUN.json"), "--policy", str(paths["plan"]), "--accepted",
                        str(home / "deliver" / "sent"), "--kind", kind, "--out", str(out), *extra],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


(WORK / "RUN.json").write_bytes(HB)


def msys(p: Path) -> str:
    s = p.as_posix()
    return "/" + s[0].lower() + s[2:]                   # Git's server reads /c/...


def wire(home: Path, root: Path, cmd=None):
    """deliver.py's Wire with the command line replaced; every batch line is recorded in w.lines; w.hook(lines, when)
    runs before and after each batch of run()."""
    w = D.Wire.__new__(D.Wire)
    w.kind, w.idle, w.cap, w.window = "sftp", 30, 120, F.SFTP_WINDOW
    w.root = w.inbox = msys(root / "inbox")
    w.batch, w.log = home / "deliver" / "sftp_batch.txt", home / "deliver" / "child.out"
    w.cmd = cmd or [str(SFTP), "-b", str(w.batch), "-D", f'"{SERVER}"']
    w.lines, w.hook = [], None
    run0, call0 = w.run, w.call

    def run(lines):
        w.lines.extend(lines)
        if w.hook:
            w.hook(lines, "before")
        res = run0(lines)
        if w.hook:
            w.hook(lines, "after")
        return res

    def call(op, rel, part=None):
        c = call0(op, rel, part)
        w.lines.extend(w.batch.read_text(encoding="ascii").splitlines())
        return c

    w.run, w.call = run, call
    return w


def stand_in(text):
    return [sys.executable, "-I", "-B", "-c", f"import sys; print({text!r}, file=sys.stderr); sys.exit(255)"]


def call(what, home, w=None, newdir=None, fp=FP):
    """One in-process run of probe, send or observe: (exit code, its line); the lock is released after it."""
    h = None
    try:
        h = D.Home(home, fp)
        out = D.probe(h, w) if what == "probe" else D.send(h, w, newdir) if what == "send" else D.observe(h)
        return 0, out
    except W.Stop as e:
        return e.code, str(e)
    finally:
        if h is not None:
            h.lock.release()


def inbox(root) -> dict:
    return {p.name: p.read_bytes() for p in sorted((root / "inbox").iterdir())} if (root / "inbox").exists() else {}


def zz(out: Path) -> dict:
    return {p.name: p.read_bytes() for p in sorted(out.glob("*.zz"))}


def short(name: str) -> str:
    """A journal file name as the checks name it: EVIDENCE, or CONTROL.<k>."""
    return "EVIDENCE" if name.startswith("EVIDENCE.") else name.replace(".json.zz", "")


def files(home) -> list:
    return [(short(r["name"]), r["how"]) for r in journal(home, "file")]


def journal(home, t=None) -> list:
    j = home / "deliver" / "journal.jsonl"
    rows = [json.loads(ln) for ln in j.read_bytes().splitlines()] if j.exists() else []
    return [r for r in rows if t is None or r.get("t") == t]


def fetched(root, home) -> None:
    """The fetch, as far as observe needs it: the guard's SCHEDULE.<n>.json and FENCE.json into wire/ as .zz."""
    for p in list(root.glob("SCHEDULE.*.json")) + ([root / "FENCE.json"] if (root / "FENCE.json").exists() else []):
        (home / "wire" / (p.name + ".zz")).write_bytes(zlib.compress(p.read_bytes(), 6))


def tree(folder: Path) -> dict:
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def ready(name):
    """A fresh root and home with a passed probe: (root, home)."""
    root, home = make_root(f"root_{name}"), new_home(f"home_{name}")
    rc, out = call("probe", home, wire(home, root))
    if rc:
        check(f"{name} the probe passes first", (rc, out), (0, "probe passed"))
    return root, home


RP_U, P_U = budget("U", pilot=dict(PILOT, rounds_whole=0))               # UNQUALIFIED
RP_S, P_S = budget("S", pilot=dict(PILOT, cohort_seconds=560))           # SELF_PLAY
check("instrument: the budget tool's outcomes U and S",
      (json.loads(RP_U.read_bytes()).get("outcome"), json.loads(RP_S.read_bytes()).get("outcome")),
      ("UNQUALIFIED", "SELF_PLAY"))


def part_p():
    root, home = make_root("root_p"), new_home("home_p")
    w = wire(home, root)
    rc, out = call("probe", home, w)
    j = journal(home, "probe")
    check("P1 the probe through the real client: exit 0; `rename -l` refused; both names gone; a journal line "
          "passed true", (rc, out.startswith("deliver: probe passed"),
                          [(r.get("passed"), r.get("refused"), r.get("gone")) for r in j], inbox(root)),
          (0, True, [(True, True, True)], {}))
    check("P1 its batch lines name `rename -l`", any(ln.startswith('rename -l "') for ln in w.lines), True)
    pre = f"{w.inbox}/probe.{os.getpid()}."
    check("P3b (v16) the positive step through the real client: the line's passed and moved true; exactly two "
          "`rename -l` lines (a onto b, a onto the free c); the inbox empty",
          ([(r.get("passed"), r.get("moved")) for r in j], [ln for ln in w.lines if ln.startswith("rename -l")],
           inbox(root)), ([(True, True)], [f'rename -l "{pre}a" "{pre}b"', f'rename -l "{pre}a" "{pre}c"'], {}))
    root3, home3 = make_root("root_p3"), new_home("home_p3")
    mk(RP_S, P_S, home3, "pilot_decision", WORK / "out_p3")
    rc, out = call("send", home3, wire(home3, root3), WORK / "out_p3")
    check("P3 a send without a passed probe: exit 3 naming the probe, nothing in the inbox, sent/ empty",
          (rc, "no passed probe" in out, inbox(root3), tree(home3 / "deliver" / "sent")), (3, True, {}, {}))
    fails = WORK / "rename_fails.py"
    fails.write_text("import subprocess, sys\n"
                     "args = sys.argv[1:]\n"
                     "lines = open(args[args.index('-b') + 1], encoding='ascii').read().splitlines()\n"
                     "if any(ln.startswith('rename -l') for ln in lines):\n"
                     "    print(\"Couldn't rename file\", file=sys.stderr)\n"
                     "    sys.exit(1)\n"
                     "sys.exit(subprocess.run(args).returncode)\n", encoding="ascii")
    root, home = make_root("root_p3c"), new_home("home_p3c")
    w = wire(home, root, cmd=[sys.executable, "-I", "-B", str(fails), str(SFTP), "-b",
                              str(home / "deliver" / "sftp_batch.txt"), "-D", f'"{SERVER}"'])
    rc, out = call("probe", home, w)
    check("P3c (v16) a client whose every `rename -l` fails: the probe FAILS, exit 3, naming the move onto a free "
          "name; the line passed false, moved false; the inbox empty",
          (rc, "the move onto a free name failed" in out,
           [(r.get("passed"), r.get("moved")) for r in journal(home, "probe")], inbox(root)),
          (3, True, [(False, False)], {}))


def part_u():
    root, home = ready("u")
    g = guard(root, P_U["plan"])
    try:
        o1, o2, o3 = WORK / "out_u1", WORK / "out_u2", WORK / "out_u3"
        check("U the tool makes control 1 (UNQUALIFIED pilot_decision)", mk(RP_U, P_U, home, "pilot_decision", o1)[0], 0)
        w = wire(home, root)
        rc, out = call("send", home, w, o1)
        check("U1a control 1 sent: exit 0; the inbox holds exactly its two .zz, byte for byte; no dot-name",
              (rc, inbox(root)), (0, zz(o1)))
        check("U1a the evidence put before the control (journal), and `rename -l` from a dot-name",
              (files(home), any(ln.startswith('rename -l "') and "/.CONTROL.1.json.zz.part\"" in ln for ln in w.lines)),
              ([("EVIDENCE", "put"), ("CONTROL.1", "put")], True))
        g.take_controls()
        c1 = (o1 / "CONTROL.1.json").read_bytes()
        check("U1b the real guard accepts 1 (no effect): control/CONTROL.1.json = the sent bytes, no SCHEDULE.1",
              ((root / "control" / "CONTROL.1.json").exists() and (root / "control" / "CONTROL.1.json").read_bytes()
               == c1, (root / "SCHEDULE.1.json").exists(), g.alarms.get("control")), (True, False, None))
        fetched(root, home)
        rc, out = call("observe", home)
        check("D6a observe: not seen yet, nothing written", (rc, "not seen yet" in out, tree(home / "control")),
              (0, True, {}))
        check("U the tool makes control 2 (target SELF_PLAY) on the sent chain", mk(RP_S, P_S, home, "target", o2)[0], 0)
        w = wire(home, root)
        rc, out = call("send", home, w, o2)
        check("U1c control 2 after an UNQUALIFIED one is NOT held (H1): exit 0; 1's two files there already, 2's put",
              (rc, files(home)[2:]), (0, [("EVIDENCE", "there already"), ("CONTROL.1", "there already"),
                                          ("EVIDENCE", "put"), ("CONTROL.2", "put")]))
        g.take_controls()
        c2 = (o2 / "CONTROL.2.json").read_bytes()
        s1 = json.loads((root / "SCHEDULE.1.json").read_bytes()) if (root / "SCHEDULE.1.json").exists() else {}
        check("U1d the guard accepts 2 and SCHEDULE.1 names it", ((root / "control" / "CONTROL.2.json").exists(),
                                                                   s1.get("evidence") == sha(c2)), (True, True))
        fetched(root, home)
        rc, out = call("observe", home)
        e1, e2 = json.loads(c1)["evidence"], json.loads(c2)["evidence"]
        want = {"CONTROL.1.json": c1, "CONTROL.2.json": c2, f"EVIDENCE.{e1}.json": (o1 / f"EVIDENCE.{e1}.json").read_bytes(),
                f"EVIDENCE.{e2}.json": (o2 / f"EVIDENCE.{e2}.json").read_bytes()}
        check("U1e/D6b observe records 1 AND 2 (the sent bytes, both evidence files)",
              (rc, out.startswith("deliver: observe: controls 1 to 2 accepted"), tree(home / "control")), (0, True, want))
        before = tree(home)
        rc, out = call("observe", home)
        after = tree(home)
        check("D6c a second observe changes nothing in the home: no file, no journal line",
              (rc, "all 2 sent control(s) seen" in out, after == before), (0, True, True))
        check("U the tool makes control 3 (fence)", mk(RP_S, P_S, home, "fence", o3)[0], 0)
        rc, out = call("send", home, wire(home, root), o3)
        g.take_controls()
        c3 = (o3 / "CONTROL.3.json").read_bytes()
        fence = json.loads((root / "FENCE.json").read_bytes()) if (root / "FENCE.json").exists() else {}
        check("U1f the fence is sent and the guard's FENCE.json names it", (rc, sha(c3) in str(fence.get("why"))),
              (0, True))
        fetched(root, home)
        rc, out = call("observe", home)
        check("D6d observe records the fence 3", (rc, (home / "control" / "CONTROL.3.json").exists() and
                                                  (home / "control" / "CONTROL.3.json").read_bytes() == c3), (0, True))
    finally:
        done(g)


def part_u2():
    root, home = ready("u2")
    other = WORK / "U2.other_plan.json"
    other.write_text(json.dumps(dict(PLAN, target_rows=1999999999)), encoding="ascii")
    g = guard(root, other)                              # G3 c: owner_policy is not this guard's policy: held for good
    try:
        o1, o2 = WORK / "out_v1", WORK / "out_v2"
        mk(RP_U, P_U, home, "pilot_decision", o1)
        r1 = call("send", home, wire(home, root), o1)[0]
        g.take_controls()
        mk(RP_S, P_S, home, "target", o2)
        r2 = call("send", home, wire(home, root), o2)[0]
        g.take_controls()
        g.take_controls()
        fetched(root, home)
        rc, out = call("observe", home)
        check("U2 control 1 held on the server: 1 and 2 sent (0, 0); the guard accepts neither, no schedule, its alarm "
              "names the hold; observe records nothing",
              (r1, r2, (root / "control" / "CONTROL.1.json").exists(), (root / "control" / "CONTROL.2.json").exists(),
               (root / "SCHEDULE.1.json").exists(), "control" in g.alarms, rc, tree(home / "control")),
              (0, 0, False, False, False, True, 0, {}))
    finally:
        done(g)


def part_w():
    root, home = ready("w")
    o1, o2, o2f = WORK / "out_w1", WORK / "out_w2", WORK / "out_w2f"
    mk(RP_S, P_S, home, "pilot_decision", o1)
    r1 = call("send", home, wire(home, root), o1)[0]
    mk(RP_S, P_S, home, "target", o2)
    rc, out = call("send", home, wire(home, root), o2)
    check("W1 SELF_PLAY 1 sent and not seen: a target 2 is HELD naming control 1; nothing new in the inbox",
          (r1, rc, "sent control 1" in out, sorted(inbox(root))), (0, 3, True, sorted(zz(o1))))
    mk(RP_S, P_S, home, "fence", o2f)
    rc, out = call("send", home, wire(home, root), o2f)
    check("W2 a fence 2 in the same place is sent (a stop is never held at home)",
          (rc, (root / "inbox" / "CONTROL.2.json.zz").exists() and (root / "inbox" / "CONTROL.2.json.zz").read_bytes()
           == (o2f / "CONTROL.2.json.zz").read_bytes()), (0, True))


def part_r():
    root, home = ready("r")
    o1, o2 = WORK / "out_r1", WORK / "out_r2"
    mk(RP_S, P_S, home, "pilot_decision", o1)
    rc, out = call("send", home, wire(home, root, cmd=stand_in("ssh: connect to host x port 22: Connection refused")), o1)
    check("R1 the server unreachable: exit 7; sent/ holds control 1 (written before the first byte); the inbox empty",
          (rc, (home / "deliver" / "sent" / "CONTROL.1.json").exists(), inbox(root)), (7, True, {}))
    mk(RP_S, P_S, home, "fence", o2)
    rc, out = call("send", home, wire(home, root), o2)
    check("R2 a fence 2 built on it carries control 1 first: exit 0; the journal's file lines in order; the inbox holds "
          "the four", (rc, files(home), inbox(root)),
          (0, [("EVIDENCE", "put"), ("CONTROL.1", "put"), ("EVIDENCE", "put"), ("CONTROL.2", "put")],
           dict(zz(o1), **zz(o2))))


def part_c():
    root, home = ready("c1")
    o = WORK / "out_c1"
    mk(RP_S, P_S, home, "pilot_decision", o)
    (root / "inbox" / "CONTROL.1.json.zz").write_bytes(b"other bytes")
    rc, out = call("send", home, wire(home, root), o)
    check("C1 CONFLICT: the inbox's CONTROL.1.json.zz holds other bytes: exit 3 naming it; its bytes unchanged",
          (rc, "CONFLICT" in out and "CONTROL.1.json.zz" in out, inbox(root).get("CONTROL.1.json.zz")),
          (3, True, b"other bytes"))

    root, home = ready("c2")
    o = WORK / "out_c2"
    mk(RP_S, P_S, home, "pilot_decision", o)
    w = wire(home, root)

    def race(lines, when):
        if when == "before" and lines[0].startswith("rename") and "CONTROL.1.json.zz" in lines[0]:
            (root / "inbox" / "CONTROL.1.json.zz").write_bytes(b"made meanwhile")
    w.hook = race
    rc, out = call("send", home, w, o)
    check("C2 the final name made just before the rename: exit 3 CONFLICT; the other bytes stay (create-only)",
          (rc, "CONFLICT" in out, inbox(root).get("CONTROL.1.json.zz")), (3, True, b"made meanwhile"))

    root, home = ready("c3")
    o = WORK / "out_c3"
    mk(RP_S, P_S, home, "pilot_decision", o)
    w = wire(home, root)

    def bad_back(lines, when):
        if when == "after" and lines[0].startswith("put") and "CONTROL.1.json.zz" in lines[0]:
            Path(lines[1].split('"')[3]).write_bytes(b"not what was put")
    w.hook = bad_back
    rc, out = call("send", home, w, o)
    check("C3 (H3) the dot-name read back with other bytes: exit 7, no rename, no final CONTROL.1.json.zz",
          (rc, "read back with other bytes" in out, "CONTROL.1.json.zz" in inbox(root),
           any(ln.startswith("rename") and "CONTROL" in ln for ln in w.lines)), (7, True, False, False))

    root, home = ready("c4")
    o = WORK / "out_c4"
    mk(RP_S, P_S, home, "pilot_decision", o)
    w = wire(home, root)

    def stop_before_control(lines, when):
        if when == "before" and lines[0].startswith("put") and "CONTROL." in lines[0]:
            raise W.Stop(7, "the test stops the sender before the control")
    w.hook = stop_before_control
    rc, out = call("send", home, w, o)
    names = sorted(inbox(root))
    check("C4 the sender stopped before the control: the inbox holds the evidence and no control",
          (rc, [n[:9] for n in names if not n.startswith(".")]), (7, ["EVIDENCE."]))
    rc, out = call("send", home, wire(home, root), o)
    check("C4 the retry: exit 0; the evidence there already, the control put; each final file equal to NEWDIR's .zz",
          (rc, files(home)[-2:], {n: b for n, b in inbox(root).items() if not n.startswith(".")}),
          (0, [("EVIDENCE", "there already"), ("CONTROL.1", "put")], zz(o)))

    root, home = ready("c5")
    o = WORK / "out_c5"
    mk(RP_S, P_S, home, "pilot_decision", o)
    (root / "inbox" / ".CONTROL.1.json.zz.part").write_bytes(b"a killed run's stale bytes" * 40)
    rc, out = call("send", home, wire(home, root), o)
    check("C5 a stale dot-name: overwritten by the put; the final equal; no dot-name left",
          (rc, inbox(root)), (0, zz(o)))

    root, home = make_root("root_c6"), new_home("home two  spaces")
    o = WORK / "made two  spaces"
    mk(RP_S, P_S, home, "pilot_decision", o)
    r0 = call("probe", home, wire(home, root))[0]
    rc, out = call("send", home, wire(home, root), o)
    check("C6 (H4) a HOME and a NEWDIR whose names hold two spaces: probe and send exit 0, the inbox equal",
          (r0, rc, inbox(root)), (0, 0, zz(o)))


def rewrite(src: Path, name: str, control=None, evidence=None, extra=None, drop=None) -> Path:
    """A copy of a made NEWDIR with the control or the evidence record changed (both .zz made again, names kept right
    unless the case wants them wrong)."""
    out = WORK / name
    shutil.copytree(src, out)
    if evidence is not None:
        for p in out.glob("EVIDENCE.*"):
            p.unlink()
        eb = W.canon(evidence)
        (out / f"EVIDENCE.{sha(eb)}.json").write_bytes(eb)
        (out / f"EVIDENCE.{sha(eb)}.json.zz").write_bytes(zlib.compress(eb, 6))
    if control is not None:
        k = control["k"]
        for p in out.glob("CONTROL.*"):
            p.unlink()
        cb = W.canon(control)
        (out / f"CONTROL.{k}.json").write_bytes(cb)
        (out / f"CONTROL.{k}.json.zz").write_bytes(zlib.compress(cb, 6))
    if extra:
        (out / extra).write_bytes(b"x")
    if drop:
        (out / drop).unlink()
    return out


def part_d1():
    root, home = ready("d1")
    o = WORK / "out_d1"
    mk(RP_S, P_S, home, "pilot_decision", o)
    c = json.loads((o / "CONTROL.1.json").read_bytes())
    ev = json.loads((o / f"EVIDENCE.{c['evidence']}.json").read_bytes())
    e_name = f"EVIDENCE.{c['evidence']}.json"
    short = WORK / "d1_short"
    shutil.copytree(o, short)
    half = (o / e_name).read_bytes()[:40]
    (short / e_name).write_bytes(half)
    (short / (e_name + ".zz")).write_bytes(zlib.compress(half, 6))
    swapped = WORK / "d1_swapped"
    shutil.copytree(o, swapped)
    (swapped / "CONTROL.1.json.zz").write_bytes((o / (e_name + ".zz")).read_bytes())
    lo = dict(ev, local_only={"x": 1})
    cases = [("D1a a fifth file", rewrite(o, "d1_fifth", extra="notes.txt"), "not exactly the four files"),
             ("D1b a missing .zz", rewrite(o, "d1_missing", drop="CONTROL.1.json.zz"), "not exactly the four files"),
             ("D1c a .zz of the other file", swapped, "does not decode to its .json"),
             ("D1d a short evidence (its name is not its sha256)", short, "its name is not its sha256"),
             ("D1e another run's control", rewrite(o, "d1_run", control=dict(c, run_fingerprint=FP2)),
              "not a control of FORMATS 1.2 of this run"),
             ("D1f an evidence with local_only", rewrite(o, "d1_local", evidence=lo, control=dict(
                 c, evidence=sha(W.canon(lo)))), "holds local_only"),
             ("D1g owner_policy not the evidence's plan", rewrite(o, "d1_policy", control=dict(c, owner_policy="0" * 64)),
              "inputs.plan_sha256")]
    for name, newdir, words in cases:
        rc, out = call("send", home, wire(home, root), newdir)
        check(f"{name}: exit 4 naming it; sent/ and the inbox empty",
              (rc, words in out, tree(home / "deliver" / "sent"), inbox(root)), (4, True, {}, {}))
    hx = new_home("home_d1h", hb=HB2)
    before = sorted(str(p.relative_to(hx)) for p in hx.rglob("*"))
    rc, out = call("send", hx, wire(hx, root), o)
    check("D1h a home whose wire/RUN.json.zz is another run's: exit 4", (rc, "not this run's header" in out), (4, True))
    check("D1h nothing made by that refusal: the home's whole listing unchanged (Fable's D2)",
          sorted(str(p.relative_to(hx)) for p in hx.rglob("*")), before)


def part_d2():
    root, home = ready("d2")
    rc, out = call("send", home, wire(home, root), WORK / "out_u2")
    check("D2a k 2 on an empty sent chain: HELD (not the next of the sent chain)", (rc, "not the next" in out, inbox(root)),
          (3, True, {}))
    o, ox = WORK / "out_d2", WORK / "out_d2x"
    mk(RP_S, P_S, home, "pilot_decision", o)
    r1 = call("send", home, wire(home, root), o)[0]
    (WORK / "d2_empty").mkdir()
    subprocess.run([sys.executable, "-I", "-B", str(TREE / "tools" / "make_control.py"), "--report", str(RP_U),
                    "--header", str(WORK / "RUN.json"), "--policy", str(P_U["plan"]), "--accepted",
                    str(WORK / "d2_empty"), "--kind", "pilot_decision", "--out", str(ox), "--state", str(P_U["state"]),
                    "--pilot", str(P_U["pilot"])], capture_output=True)
    before = inbox(root)
    rc, out = call("send", home, wire(home, root), ox)
    check("D2b another control under the same k 1: HELD; the inbox unchanged", (r1, rc, "same sequence" in out,
                                                                             inbox(root) == before), (0, 3, True, True))
    w = wire(home, root)
    rc, out = call("send", home, w, o)
    check("D2e a retry of the same bytes: exit 0 (retry), no `put` line in its batches, the inbox unchanged",
          (rc, " retry:" in out, [ln for ln in w.lines if ln.startswith("put")], inbox(root) == before),
          (0, True, [], True))


def part_d3():
    root, home = ready("d3")
    o = WORK / "out_d3"
    mk(RP_S, P_S, home, "pilot_decision", o)
    c = json.loads((o / "CONTROL.1.json").read_bytes())
    late = rewrite(o, "d3_late", control=dict(c, cutoff_utc=T(L + 82801)))
    rc, out = call("send", home, wire(home, root), late)
    check("D3a a cutoff one second later than the one in force: HELD, the inbox empty",
          (rc, "later than the one in force" in out, inbox(root)), (3, True, {}))
    root, home = ready("d3b")
    now = int(time.time())
    (home / "wire" / "SCHEDULE.1.json.zz").write_bytes(zlib.compress(W.canon({
        "cutoff_utc": T(now - 60), "dispatch_end_utc": T(now - 120), "evidence": "0" * 64, "n": 1, "prev": "first",
        "ranges": [], "run_fingerprint": FP, "schema": 2}), 6))
    past = rewrite(o, "d3_past", control=dict(c, cutoff_utc=T(now - 60), dispatch_end_utc=T(now - 120)))
    rc, out = call("send", home, wire(home, root), past)
    check("D3b D has come: a SELF_PLAY control is HELD", (rc, "D has come" in out, inbox(root)), (3, True, {}))
    of = WORK / "out_d3f"
    subprocess.run([sys.executable, "-I", "-B", str(TREE / "tools" / "make_control.py"), "--report", str(RP_S),
                    "--header", str(WORK / "RUN.json"), "--policy", str(P_S["plan"]), "--accepted",
                    str(home / "deliver" / "sent"), "--kind", "fence", "--out", str(of)], capture_output=True)
    cf = json.loads((of / "CONTROL.1.json").read_bytes())
    fence = rewrite(of, "d3_fence", control=dict(cf, cutoff_utc=T(now - 60), dispatch_end_utc=T(now - 120)))
    rc, out = call("send", home, wire(home, root), fence)
    check("D3c a fence with the same bounds is sent", (rc, sorted(inbox(root)) == sorted(zz(fence))), (0, True))


def part_d5():
    for name, text in (("D5a the host key", "Host key verification failed."),
                       ("D5b the refused login", "tester@example.invalid: Permission denied (publickey).")):
        root, home = ready("d5" + name[2])
        o = WORK / f"out_d5{name[2]}"
        mk(RP_S, P_S, home, "pilot_decision", o)
        w = wire(home, root, cmd=stand_in(text))
        rc, out = call("send", home, w, o)
        check(f"{name}: exit 6; the ONLY batch line an `ls -ln`; the inbox empty; sent/ holds the decision; no file "
              f"line", (rc, len(w.lines), w.lines[0][:8] if w.lines else None, inbox(root),
                        (home / "deliver" / "sent" / "CONTROL.1.json").exists(), journal(home, "file")),
              (6, 1, 'ls -ln "', {}, True, []))


AHEAD = 25178                                         # v16: the PC's clock ahead of the server's (measured 25 Nov)


def part_dl():
    """DL1, DL1b, DL2 (ADDENDUM 7): the PC 25,178 s AHEAD of the server; the schedule's cutoff 30 s after the
    server's now, 25,148 s before the PC's."""
    def setup(name):
        root, home = ready(name)
        o = WORK / f"out_{name}"
        mk(RP_S, P_S, home, "pilot_decision", o)
        c = json.loads((o / "CONTROL.1.json").read_bytes())
        now = int(time.time())
        cut, disp = T(now - AHEAD + 30), T(now - AHEAD - 30)
        (home / "wire" / "SCHEDULE.1.json.zz").write_bytes(zlib.compress(W.canon({
            "cutoff_utc": cut, "dispatch_end_utc": disp, "evidence": "0" * 64, "n": 1, "prev": "first",
            "ranges": [], "run_fingerprint": FP, "schema": 2}), 6))
        ctl = rewrite(o, f"{name}_ctl", control=dict(c, cutoff_utc=cut, dispatch_end_utc=disp))
        of = WORK / f"out_{name}_f"
        subprocess.run([sys.executable, "-I", "-B", str(TREE / "tools" / "make_control.py"), "--report",
                        str(RP_S), "--header", str(WORK / "RUN.json"), "--policy", str(P_S["plan"]), "--accepted",
                        str(home / "deliver" / "sent"), "--kind", "fence", "--out", str(of)], capture_output=True)
        cf = json.loads((of / "CONTROL.1.json").read_bytes())
        fence = rewrite(of, f"{name}_fence", control=dict(cf, cutoff_utc=cut, dispatch_end_utc=disp))
        return root, home, ctl, fence

    root, home, ctl, fence = setup("dl1")
    clock_line(home, FP, behind_s=AHEAD)              # the server's now = the cutoff - 30 s
    rc, out = call("send", home, wire(home, root), ctl)
    check("DL1 the server's clock 30 s before the cutoff in force, the PC 25,178 s ahead (past it): a SELF_PLAY "
          "control is SENT, the inbox holds its two .zz", (rc, sorted(inbox(root)) == sorted(zz(ctl))), (0, True))
    root, home, ctl, fence = setup("dl1b")
    clock_line(home, FP, behind_s=AHEAD - 31)         # the server's now = the cutoff + 1 s
    rc, out = call("send", home, wire(home, root), ctl)
    got = (rc, "D has come" in out, inbox(root))
    rc, out = call("send", home, wire(home, root), fence)
    check("DL1b the server's clock 1 s past the cutoff: the same control HELD 'D has come', the inbox empty; a fence "
          "with the same bounds is sent", (got, rc, sorted(inbox(root)) == sorted(zz(fence))),
          ((3, True, {}), 0, True))
    root, home, ctl, fence = setup("dl2")
    (home / "clock" / "journal.jsonl").unlink()
    rc, out = call("send", home, wire(home, root), ctl)
    got = (rc, "no clock line of this run" in out, inbox(root))
    rc, out = call("send", home, wire(home, root), fence)
    check("DL2 no clock line: the SELF_PLAY control HELD naming 'no clock line of this run', the inbox empty; a "
          "fence with the same bounds is sent without a clock", (got, rc, sorted(inbox(root)) == sorted(zz(fence))),
          ((3, True, {}), 0, True))


def part_l():
    home = new_home("home_l")
    lock = W.SlotLock(home / "deliver")
    try:
        r = subprocess.run([sys.executable, "-I", "-B", str(DP), "observe", "--home", str(home), "--fingerprint", FP],
                           capture_output=True, text=True)
        check("L1 observe while the test holds DIR/deliver/LOCK: exit 8", (r.returncode, "another delivery" in r.stdout),
              (8, True))
    finally:
        lock.release()
    r = subprocess.run([sys.executable, "-I", "-B", str(DP), "send", "--home", str(home), "--fingerprint", FP,
                        "--made", str(WORK)], capture_output=True, text=True)
    check("L2 send without --config: exit 2", r.returncode, 2)
    r = subprocess.run([sys.executable, "-I", "-B", str(DP), "observe", "--home", str(home), "--fingerprint", FP],
                       capture_output=True, text=True)
    check("L3 observe: exit 0, its line", (r.returncode, r.stdout.startswith("deliver: observe")), (0, True))
    for name, made, words in (("L4 a NEW EMPTY folder", None, "not this run's header"),
                              ("L5 a folder with another run's header", zlib.compress(HB2, 6), "not this run's header"),
                              ("L6 a folder with a header that is not zlib", b"not zlib at all\n", "not a zlib stream")):
        h = WORK / ("home_" + name[:2].lower())
        h.mkdir()
        if made is not None:
            (h / "wire").mkdir()
            (h / "wire" / "RUN.json.zz").write_bytes(made)
        before = sorted(str(p.relative_to(h)) for p in h.rglob("*"))
        r = subprocess.run([sys.executable, "-I", "-B", str(DP), "observe", "--home", str(h), "--fingerprint", FP],
                           capture_output=True, text=True)
        check(f"{name}: exit 4 naming it, and nothing made there (Fable's D2)",
              (r.returncode, words in r.stdout, sorted(str(p.relative_to(h)) for p in h.rglob("*")) == before),
              (4, True, True))
    h = WORK / "home_l7"
    (h / "wire").mkdir(parents=True)
    (h / "wire" / "RUN.json.zz").write_bytes(zlib.compress(HB, 6))
    r = subprocess.run([sys.executable, "-I", "-B", str(DP), "observe", "--home", str(h), "--fingerprint", FP],
                       capture_output=True, text=True)
    check("L7 control: this run's header alone: exit 0, and deliver/ (sent/, back/, LOCK) and control/ are made",
          (r.returncode, [n for n in ("deliver", "deliver/sent", "deliver/back", "deliver/LOCK", "control")
                          if not (h / n).exists()]), (0, []))
    nr = b"not a record\n"
    h = WORK / "home_l6b"
    (h / "wire").mkdir(parents=True)
    (h / "wire" / "RUN.json.zz").write_bytes(zlib.compress(nr, 6))
    before = sorted(str(p.relative_to(h)) for p in h.rglob("*"))
    r = subprocess.run([sys.executable, "-I", "-B", str(DP), "observe", "--home", str(h), "--fingerprint", sha(nr)],
                       capture_output=True, text=True)
    check("L6b a header that is zlib and has the fingerprint but is no record: exit 4, no traceback, nothing made",
          (r.returncode, "Traceback" in r.stdout + r.stderr,
           sorted(str(p.relative_to(h)) for p in h.rglob("*")) == before), (4, False, True))
    h = WORK / "home_l4b_does_not_exist"
    r = subprocess.run([sys.executable, "-I", "-B", str(DP), "observe", "--home", str(h), "--fingerprint", FP],
                       capture_output=True, text=True)
    check("L4b a --home that does not exist: exit 2 naming it, and it is still not there",
          (r.returncode, "no such home folder" in r.stdout, h.exists()), (2, True, False))


for nm, fn in (("P", part_p), ("U", part_u), ("U2", part_u2), ("W", part_w), ("R", part_r), ("C", part_c),
               ("D1", part_d1), ("D2", part_d2), ("D3", part_d3), ("D5", part_d5), ("DL", part_dl),
               ("L", part_l)):
    safe(nm, fn)
leftover = [str(p) for p in TREE.rglob("__pycache__")]
check("no __pycache__ in the copied tree", leftover, [])
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)

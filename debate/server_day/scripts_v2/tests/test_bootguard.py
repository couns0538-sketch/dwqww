"""test_bootguard.py: the boot guard (A3b, run/bootguard.py) against known answers written BEFORE it ran
(tmp/opus_scratch/bootguard/KNOWN_ANSWERS_by_opus.md on the PC; FORMATS.md 1.1, 1.3, 1.8.1; SETUP_PLAN D5, D15).

    test_bootguard.py <run/bootguard.py> <a NEW folder> exe=<engine> net=<net> pkg=<package folder with its
                      MANIFEST.sha256> [only=U,B,E,V] [plantN]

The run folder is copied; a plant is applied to the copy's bootguard.py only. The REAL worker (with the real engine)
makes the day's files; a test wrapper gives the worker a planted boot id (worker.boot_id replaced, nothing else).
The boot guard runs in this process with planted readers (boot id, synchronised, UTC).

U  units: read_instance on fixture folders (values are sha256 of the texts; placeholders null); the equality rule
   of 1.1 [2.4] case by case; the package's hash list as the publisher writes it (its last line `digest`).
   The day's package is the given one with the owner's plan.json added and listed (the test's fixture); U6 the
   given list without plan.json: held 5 naming plan.json (FORMATS 1.2, D6; bug hunt 23 Nov 19:30, F74-1).
PHASE A (boot "boot-a", the header's): slots 0, 1, 2, piece_games 1, pilot ranges 1 to 8; workers 0 and 1 play until
   each journal has two `closed` lines, then STOP: both exit 0, no `ended` line. Slot 2 never starts. A copy of this
   state is the start of every B case. The heads h0, h1 are read from the journals by 1.4's rule alone (the last
   `closed` line, or -1 and "genesis:<fingerprint>:w<NNN>").
E  E1 boot-b, no RESUME: worker 0 exits 4, its journal unchanged. E2 boot-b: the boot guard writes RESUME.1 (11
   keys, canonical, n 1, prev first, old boot-a, new boot-b, the instance read now, slots [h0, h1, genesis of 2],
   the seven checks), journals unchanged. E3 worker 0 under boot-b: accepted, its epoch line names sha256(RESUME.1)
   and h0; it closes a new piece; STOP: exit 0. E4 worker 0 again: its epoch line's resume is null; exit 0.
   E5 the boot guard again under boot-b: exit 0, no RESUME.2, RESUME.1 unchanged. E6 boot-c: RESUME.2, prev =
   sha256(RESUME.1), old boot-b, new boot-c, slot 0's row its head NOW (moved on), slot 1's h1. E7 worker 1 under
   boot-c: accepted, its epoch line names sha256(RESUME.2) and h1. E8 FENCE.json, boot-d: exit 5, no RESUME.3.
B  each on a copy of the phase A state, boot-b unless named: B1 boot-a: 0, no RESUME. B2 another machine id: 5.
   B3 no product uuid now: 5. B6 never synchronised (sync-wait 1 s): 5. B7 UTC 100 s before the newest journal: 5.
   B8 the engine one byte changed: 5. B9 the net one byte changed: 5. B10 a listed package file changed: 5.
   B11 a self-consistent list that is not the header's: 5. B12 FENCE.json: 5. B13 slot 0's first seal one byte
   changed: 4. B14 slot 1's IDENTITY.json of another run: 4. B15 a RESUME.1 whose prev is not first: 4.
   B16 slot 0's lock held: 3. B17 guard/LOCK held: 3. B18 the same hold twice: ONE alarm line. B19 a header
   without `package`: 4, the alarm names the missing key. B20 the manifest missing (an OSError inside the worker's
   reading): 4, the alarm names FileNotFoundError, no traceback. B21 a RESUME.1 whose old_boot_id is not the
   header's boot: 4.
   Every case that is not 0: no RESUME file, no .tmp, every journal's bytes unchanged, and EVERY file of the root
   unchanged but guard/bootguard.log (and guard/LOCK, a lock file: its presence is compared, not its bytes).
   Every admitted case (B1, E2, E5, E6, T1): every file of the root unchanged but the new RESUME (and guard/LOCK).
   T1 a run whose slots never started, board serial null on both sides: RESUME.1 with genesis rows. T2 the same with
   the header's instance_provable false: 5. T3 the header's hardware values both null: 5.

V  version 2 (24 November; known answers tmp/opus_scratch/bootguard_v2/KNOWN_ANSWERS_bootguard_v2_by_opus.md on the PC,
   written before the code, with its CHANGED section of 02:30). R1 = phase A + RESUME.1 by the guard under boot-b.
   Holds (exit, what the alarm names; RESUMEs as before, no .tmp, every file unchanged but the alarm log):
   V1 w000's journal removed beside its pieces: 4 (w000/closed/p000000.raw). V2 R1, w000 withheld, boot-c: 4 (w000,
   RESUME.1). V4 R1, w000's journal cut before its last closed line: 4. V5 R1, slot 1's admitted seal forged: 4.
   V6 a stray closed piece in w001: 4. V7 a stale open/p000000.raw in w000: 4. V7c w001 with no journal and no closed
   piece, only open/p000000.raw: 4. V8 the package's run folder a junction (Windows) or link (Linux): 5. V9 slots []:
   4. V10 guard/CLOSED.json without FENCE.json: 4. V11 RESUME.1 written at newest + 3600, boot-c at newest + 1800: 5.
   V12 a fresh run, UTC 100 s before the lease start: 5. V13a to V13i R1 with RESUME.1 rewritten (a forged genesis,
   instance_provable false, at_utc "yesterday", old_boot_id boot-z, new = old boot, an extra key, instance null, no
   `clock` check) and V13d a hand-made RESUME.2 50 s before RESUME.1: 4. V14 a journal 7,200 s ahead, UTC newest +
   3,600: 5 (the journal; plant5's case). Admitted controls: V3 R1 intact, boot-c (RESUME.2 rows [h0, h1, genesis]);
   V7b the open piece with bytes not journalled (RESUME.1 rows [h0, h1, genesis]); V11b boot-c at newest + 3610.

PLANTS (each must make the test fail; the check expected to fail is named):
  plant1 machine ids not compared (U3, B2)          plant2 null on one side not a difference (U3 header-null case)
  plant3 null on both sides a difference (U3, T1)   plant4 no wait for synchronisation (B6)
  plant5 UTC before the newest journal allowed (B7)  plant6 engine and net not hashed (B8, B9)
  plant7 package files not hashed (B10)              plant8 the fence not looked at (B12, E8)
  plant9 the journals not replayed (B13, E2 rows)    plant10 prev always first (E6)
  plant11 old_boot_id always the header's (E6)       plant12 guard/LOCK not taken (B17)
  plant13 an admitted boot not seen (E5)             plant14 the alarm line repeated (B18)
  plant15 a slot's lock not taken (B16)              plant16 the list's sha256 not compared (B11)
  plant17 the identity not checked (B14)             plant18 the header's instance_provable ignored (T2)
  plant19 the digest line not checked (U4)          plant20 the header's keys not checked (B19)
  plant21 no catch-all: a traceback (B20)           plant22 old_boot_id not compared in the chain (B21)
  plant23 plan.json not required in the list (U6)
  plant24 closed/ rule gone (V1, V6)                plant25 open/ index rule gone (V7)
  plant26 open/ epoch rule gone (V7c)               plant27 the ancestry check gone (V2, V4, V5)
  plant28 earlier RESUMEs out of the floor (V11)     plant29 the lease start out of the floor (V12)
  plant30 a RESUME's keys not checked (V13g)         plant31 its instance_provable not checked (V13b)
  plant32 its instance not checked (V13h)            plant33 its checks not checked (V13i)
  plant34 new = old boot not refused (V13f)          plant35 its rows not checked (V13a)
  plant36 its at_utc not parsed (V13c, V13d)         plant37 its at_utc order not checked (V13d)
  plant38 package paths not resolved (V8)            plant39 the slots rule gone (V9)
  plant40 CLOSED.json not looked at (V10)
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

if len(sys.argv) < 3:
    print("usage: test_bootguard.py <run/bootguard.py> <a NEW folder> exe=.. net=.. pkg=.. [only=U,B,E,V] [plantN]")
    sys.exit(2)
BG_PATH, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
OPTS, PLANT = {}, None
for x in sys.argv[3:]:
    if x.startswith("plant"):
        PLANT = x
    elif "=" in x and x.split("=", 1)[0] in ("exe", "net", "pkg", "only"):
        OPTS[x.split("=", 1)[0]] = x.split("=", 1)[1]
    else:
        print(f"STOP: not understood: {x}")
        sys.exit(2)
ONLY = set(OPTS.get("only", "U,B,E,V").split(","))
if not all(k in OPTS for k in ("exe", "net", "pkg")):
    print("STOP: exe=, net= and pkg= are needed (the real worker makes the day's files)")
    sys.exit(2)
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
TREE = BG_PATH.parent.parent
shutil.copytree(BG_PATH.parent, WORK / "run", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

PLANTS = {
    "plant1": ('    if header_inst["machine_id"] != now_inst["machine_id"]:\n', '    if False:\n'),
    "plant2": ('        if (a is None) != (b is None):\n', '        if False:\n'),
    "plant3": ('        if (a is None) != (b is None):\n', '        if a is None or b is None:\n'),
    "plant4": ('        while not self.rd.synced():\n', '        while False:\n'),
    "plant5": ('        if now < newest:\n', '        if False:\n'),
    "plant6": ('            if not p.is_file() or file_sha256(p) != h[key]:\n', '            if not p.is_file():\n'),
    "plant7": ('            if not f.is_file() or f.is_symlink() or file_sha256(f) != m[1]:\n',
               '            if not f.is_file():\n'),
    "plant8": ('        if (self.root / "FENCE.json").exists():\n', '        if False:\n'),
    "plant9": ('            w.read_journal()\n', '            pass\n'),
    "plant10": ('"prev": "first" if n == 1 else sha256_bytes(chain[-1][1]), ', '"prev": "first", '),
    "plant11": ('"old_boot_id": h["boot_id"] if n == 1 else chain[-1][2]["new_boot_id"],', '"old_boot_id": h["boot_id"],'),
    "plant12": ('        glock = SlotLock(self.gdir)                     # Stop 3: a server guard runs\n',
                '        glock = SimpleNamespace(release=lambda: None)\n'),
    "plant13": ('        if chain and chain[-1][2]["new_boot_id"] == boot:\n', '        if False:\n'),
    "plant14": ('        if last.split("] ", 1)[-1] != body:\n', '        if True:\n'),
    "plant15": ('            lock = SlotLock(w.dir)                      # Stop 3: a worker runs\n',
                '            pass\n'),
    "plant16": ('        if sha256_bytes(data) != h["package"]:\n', '        if False:\n'),
    "plant23": ('        if not any(ln.endswith("  plan.json") for ln in body[:-1]):\n', '        if False:\n'),
    "plant17": ('            w.check_identity(canon({"run": h["run"], "run_fingerprint": fp, "schema": 2, "slot": k}))\n',
                '            pass\n'),
    "plant18": (' if h.get("instance_provable") is True ', ' if True '),
    "plant19": ('len(body) < 2 or body[-1] != "digest "', 'len(body) < 2 or False and body[-1] != "digest "'),
    "plant20": ('        if miss:\n', '        if False:\n'),
    "plant21": ('        except Exception as e:  # noqa: BLE001   never a traceback and exit 1: every other fault is a 4\n',
                '        except ZeroDivisionError as e:\n'),
    "plant22": ('                    or r.get("old_boot_id") != (boot0 if k == 1 else out[-1][2]["new_boot_id"]):\n',
                '                    or False:\n'),
    "plant24": ('                    ok = i <= w.last_index or (i == o and named)\n', '                    ok = True\n'),
    "plant25": ('                    ok = i == o and m[2] == "raw"\n', '                    ok = True\n'),
    "plant26": ('                    ok = ok and w.epoch > 0\n', '                    pass\n'),
    "plant27": ('            if row["last_index"] >= 0 and w.seal_sha.get(row["last_index"]) != row["last_seal"]:\n',
                '            if False:\n'),
    "plant28": ('            if at > floor:\n', '            if False:\n'),
    "plant29": ('W.utc(h["lease_start_utc"], "RUN.json lease_start_utc"), "the lease start"', '0.0, "the lease start"'),
    "plant30": ('            if sorted(r) != RESUME_KEYS:\n', '            if False:\n'),
    "plant31": ('            if r["instance_provable"] is not True:\n', '            if False:\n'),
    "plant32": ('            if not isinstance(r["instance"], dict):\n', '            if False:\n'),
    "plant33": ('            if not isinstance(r["checks"], dict) or sorted(r["checks"]) != list(CHECKS):\n',
                '            if False:\n'),
    "plant34": ('            if r["new_boot_id"] == r["old_boot_id"]:\n', '            if False:\n'),
    "plant35": ('            if not self.rows_ok(r["slots"], slots, fp):\n', '            if False:\n'),
    "plant36": ('            at = W.utc(r["at_utc"], f"{p.name} at_utc")\n', '            at = 0.0\n'),
    "plant37": ('            if out and at < out[-1][3]:\n', '            if False:\n'),
    "plant38": ('            if f.resolve() != lst.parent.resolve() / m[2]:\n', '            if False:\n'),
    "plant39": ('        if not (s and all(type(x) is int and 0 <= x <= 999 for x in s) and all(x < y for x, y in '
                'zip(s, s[1:]))):\n', '        if False:\n'),
    "plant40": ('        if (self.gdir / "CLOSED.json").exists():\n', '        if False:\n'),
}
if PLANT:
    if PLANT not in PLANTS:
        print(f"STOP: no plant {PLANT}")
        sys.exit(2)
    old, new = PLANTS[PLANT]
    gp = WORK / "run" / "bootguard.py"
    text = gp.read_text(encoding="utf-8")
    if text.count(old) != 1:
        print(f"STOP: {PLANT}: its text stands {text.count(old)} times in the boot guard")
        sys.exit(2)
    gp.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print(f"PLANT {PLANT} applied to the copy")

sys.path.insert(0, str(WORK / "run"))
import bootguard as BG  # noqa: E402
import worker as W  # noqa: E402

RESULTS, PROCS = [], []
EXE, NET = Path(OPTS["exe"]).resolve(), Path(OPTS["net"]).resolve()
MAN, KNOWN = TREE / "workloads" / "MANIFEST.json", TREE / "known" / "startup.json"


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {str(got)[:300]}" + ("" if ok else f"; want {str(want)[:300]}"),
          flush=True)
    return ok


def true(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'} {name}" + ("" if cond else f": {str(detail)[:400]}"), flush=True)
    return bool(cond)


def T(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t)))


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---- fixtures: the instance folders (raw texts by hand), the package, the openings ----------------------------
M, M2 = "0123456789abcdef0123456789abcdef", "fedcba9876543210fedcba9876543210"
U, S = "4c4c4544-0042-3510-8051-b4c04f4e3132", "BSN-12345-X"
INST = WORK / "inst"
for name, files in {"ok": {"etc/machine-id": M, "dmi/product_uuid": U, "dmi/board_serial": S},
                    "m2": {"etc/machine-id": M2, "dmi/product_uuid": U, "dmi/board_serial": S},
                    "nouuid": {"etc/machine-id": M, "dmi/board_serial": S},
                    "noserial": {"etc/machine-id": M, "dmi/product_uuid": U},
                    "ph1": {"etc/machine-id": "uninitialized", "dmi/product_uuid": "00000000-0000-0000-0000-000000000000",
                            "dmi/board_serial": "To Be Filled By O.E.M."},
                    "ph2": {"etc/machine-id": M.upper(), "dmi/product_uuid": "Not Specified",
                            "dmi/board_serial": "  Default string "},
                    "ph3": {"dmi/product_uuid": "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF", "dmi/board_serial": "None"}}.items():
    for rel, text in files.items():
        p = INST / name / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((text + "\n").encode("ascii"))
    for sub in ("etc", "dmi"):
        (INST / name / sub).mkdir(parents=True, exist_ok=True)
INST_H = {"machine_id": sha(M.encode()), "product_uuid": sha(U.encode()), "board_serial": sha(S.encode())}
PKG = WORK / "pkg"
shutil.copytree(Path(OPTS["pkg"]).resolve(), PKG)
PKG_LIST = PKG / "MANIFEST.sha256"
NOPOL = PKG / "MANIFEST.nopolicy.sha256"     # F74-1 (bug hunt 23 Nov 19:30): the published list, no policy in it
NOPOL.write_bytes(PKG_LIST.read_bytes())
(PKG / "plan.json").write_bytes(b'{"owner_choice":{"name":"the test policy"}}\n')   # the day adds the owner's
_rows = PKG_LIST.read_text(encoding="ascii").split("\n")[:-2] + [f"{sha((PKG / 'plan.json').read_bytes())}  plan.json"]
_body = "\n".join(sorted(_rows, key=lambda ln: ln.split("  ", 1)[1])) + "\n"           # the publisher's form
PKG_LIST.write_bytes((_body + "digest " + sha(_body.encode("ascii")) + "\n").encode("ascii"))
man = json.loads(MAN.read_bytes())
n12 = [ln.split()[3:] for ln in (TREE / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
OPEN = WORK / "n12_openings.txt"
OPEN.write_bytes("".join(" ".join(o) + "\n" for o in n12).encode("ascii"))
WRAP = WORK / "worker_boot.py"
WRAP.write_text("import os, sys\nsys.path.insert(0, sys.argv.pop(1))\nimport worker\n"
                "worker.boot_id = lambda: os.environ['BOOTGUARD_TEST_BOOT']\nsys.exit(worker.main())\n",
                encoding="ascii", newline="\n")


def header(slots, boot="boot-a", inst=None, provable=True):
    now = int(time.time())
    return {"schema": 2, "run": "bg", "lease_start_utc": T(now - 60), "lease_end_utc": T(now + 86400),
            "hard_cutoff_utc": T(now + 900), "boot_id": boot, "instance": dict(inst or INST_H),
            "instance_provable": provable, "package": sha(PKG_LIST.read_bytes()), "engine_sha256": sha(EXE.read_bytes()),
            "net_sha256": man["net_sha256"],
            "options_sha256": sha("".join(ln + "\n" for ln in man["options"]).encode("ascii")),
            "game_line": man["selfgame_line"],
            "opening_rule": {"kind": "list", "sha256": sha(OPEN.read_bytes()), "count": len(n12)},
            "slots": slots, "piece_games": 1,
            "pilot_ranges": [{"first": 1, "last": 8, "round": 1, "schedule": 0, "short": False, "slot": k}
                             for k in slots]}


def new_run(name, slots, **kw):
    root = WORK / name
    root.mkdir()
    (root / "RUN.json").write_bytes(W.canon(header(slots, **kw)))
    return root


def fp_of(root):
    return sha((root / "RUN.json").read_bytes())


def jlines(root, k):
    j = root / f"w{k:03d}" / "journal.txt"
    return [json.loads(ln) for ln in j.read_bytes().split(b"\n")[:-1]] if j.exists() else []


def head(root, k):
    """1.4 by hand: the last `closed` line's index and seal, or -1 and the genesis text."""
    last = (-1, f"genesis:{fp_of(root)}:w{k:03d}")
    for r in jlines(root, k):
        if r["t"] == "closed":
            last = (r["index"], r["seal"])
    return {"last_index": last[0], "last_seal": last[1], "slot": k}


def snap(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.glob("w*/journal.txt"))}


def whole(root):
    """Every file under the root: its bytes; a LOCK file by its presence only (Fable's BG3)."""
    return {p.relative_to(root).as_posix(): (b"<lock>" if p.name == "LOCK" else p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()}


def changed(before, after, but=("guard/LOCK",)):
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k) and k not in but)


def safe(fn):
    """The exit code, or the name of an exception that escaped (BG1: never a traceback)."""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        return f"escaped {type(e).__name__}"


def resumes(root):
    return sorted(p.name for p in root.glob("RESUME.*"))


def worker(root, k, boot):
    log = open(WORK / f"{root.name}.w{k}.{boot}.out", "ab")
    p = subprocess.Popen([sys.executable, "-I", "-B", str(WRAP), str(WORK / "run"), "--root", str(root), "--exe",
                          str(EXE), "--net", str(NET), "--manifest", str(MAN), "--known-startup", str(KNOWN),
                          "--openings", str(OPEN), "--slot", str(k)],
                         env={**os.environ, "BOOTGUARD_TEST_BOOT": boot}, stdout=log, stderr=subprocess.STDOUT)
    log.close()
    PROCS.append(p)
    return p


def wait_until(cond, limit):
    end = time.monotonic() + limit
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.1)
    return cond()


def finish(root, procs, limit=180):
    (root / "STOP").write_bytes(b"")
    codes = []
    for p in procs:
        try:
            codes.append(p.wait(timeout=limit))
        except subprocess.TimeoutExpired:
            p.kill()
            codes.append(None)
    (root / "STOP").unlink()
    return codes


def bg(root, boot, synced=True, utc=None, sync_wait=900.0, inst="ok", exe=None, net=None, pkg_list=None, man=None):
    a = SimpleNamespace(root=str(root), exe=str(exe or EXE), net=str(net or NET), manifest=str(man or MAN),
                        known_startup=str(KNOWN), openings=str(OPEN), package_list=str(pkg_list or PKG_LIST),
                        sync_wait=sync_wait, etc=str(INST / inst / "etc"), dmi=str(INST / inst / "dmi"))
    rd = SimpleNamespace(boot=lambda: boot, synced=lambda: synced, utc=utc or time.time, sleep=time.sleep)
    return BG.BootGuard(a, rd).run()


def held_case(name, root, got, want_code):
    before, every = snap(root), whole(root)
    check(f"{name} exit {want_code}, no RESUME, no .tmp", (safe(got), resumes(root), sorted(p.name for p in root.glob("*.tmp"))),
          (want_code, [], []))
    check(f"{name} every journal unchanged", snap(root) == before, True)
    check(f"{name} every file of the root unchanged but the alarm log", changed(every, whole(root)),
          ["guard/bootguard.log"])


def part_u():
    check("U1 read_instance: sha256 of the texts", BG.read_instance(INST / "ok" / "etc", INST / "ok" / "dmi"), INST_H)
    none3 = {"machine_id": None, "product_uuid": None, "board_serial": None}
    for name in ("ph1", "ph2", "ph3"):
        check(f"U2 placeholders and missing files are null ({name})",
              BG.read_instance(INST / name / "etc", INST / name / "dmi"), none3)
    i = lambda m, u, s: {"machine_id": m, "product_uuid": u, "board_serial": s}  # noqa: E731
    cases = [("all equal", i("m", "u", "s"), i("m", "u", "s"), None),
             ("board serial null on both sides (B4)", i("m", "u", None), i("m", "u", None), None),
             ("both hardware values null: not provable (B5)", i("m", None, None), i("m", None, None), "not provable"),
             ("board serial null in the header only (B3b)", i("m", "u", None), i("m", "u", "s"), "one side only"),
             ("product uuid null now only (B3)", i("m", "u", "s"), i("m", None, "s"), "one side only"),
             ("another machine id (B2)", i("m2", "u", "s"), i("m", "u", "s"), "machine id differs"),
             ("another board serial", i("m", "u", "s"), i("m", "u", "s2"), "board_serial differs"),
             ("no machine id: not provable", i(None, "u", "s"), i(None, "u", "s"), "not provable")]
    for name, a, b, want in cases:
        got = BG.differs(a, b)
        check(f"U3 {name}", None if got is None else want if want and want in got else got, want)
    lst = PKG_LIST.read_bytes()
    g = BG.BootGuard(SimpleNamespace(root=str(WORK), package_list=str(PKG_LIST)))
    check("U5 the publisher's own list passes", g.package({"package": sha(lst)}),
          {"package": sha(lst), "package_files": lst.count(b"\n") - 1})
    bad = PKG / "MANIFEST.bad.sha256"
    bad.write_bytes(lst[:lst.rindex(b"digest ")] + b"digest " + b"0" * 64 + b"\n")
    try:
        BG.BootGuard(SimpleNamespace(root=str(WORK), package_list=str(bad))).package({"package": sha(bad.read_bytes())})
        got = "no hold"
    except BG.Held as e:
        got = (e.code, "digest" in e.text)
    check("U4 a list whose digest line is wrong (its own sha256 in the header): held 5", got, (5, True))
    bad.unlink()
    try:
        BG.BootGuard(SimpleNamespace(root=str(WORK), package_list=str(NOPOL))).package(
            {"package": sha(NOPOL.read_bytes())})
        got = "no hold"
    except BG.Held as e:
        got = (e.code, "plan.json" in e.text)
    check("U6 the given list without plan.json (its own sha256 in the header): held 5 naming plan.json", got,
          (5, True))


STATE = {}


def phase_a():
    root = new_run("day", [0, 1, 2])
    ps = [worker(root, 0, "boot-a"), worker(root, 1, "boot-a")]
    closed = lambda k: sum(r["t"] == "closed" for r in jlines(root, k))  # noqa: E731
    ok = wait_until(lambda: closed(0) >= 2 and closed(1) >= 2, 300)
    codes = finish(root, ps)
    true("A both workers closed two pieces", ok, [closed(0), closed(1)])
    check("A both exit 0 at STOP, no ended line", (codes, [r["t"] for k in (0, 1) for r in jlines(root, k)
                                                         if r["t"] == "ended"]), ([0, 0], []))
    check("A slot 2 never started", (root / "w002").exists(), False)
    shutil.copytree(root, WORK / "state_a")
    STATE.update(root=root, h0=head(root, 0), h1=head(root, 1), g2=head(root, 2))


def part_e():
    root, h0, h1, g2 = STATE["root"], STATE["h0"], STATE["h1"], STATE["g2"]
    before = snap(root)
    p = worker(root, 0, "boot-b")
    try:
        code = p.wait(timeout=120)
    except subprocess.TimeoutExpired:
        p.kill()
        code = None
    check("E1 boot-b without a RESUME: worker 0 exits 4, its journal unchanged", (code, snap(root) == before),
          (4, True))
    before, every = snap(root), whole(root)
    check("E2 the boot guard under boot-b: exit 0", bg(root, "boot-b"), 0)
    check("E2 every file of the root unchanged but the new RESUME.1", changed(every, whole(root)), ["RESUME.1.json"])
    r1b = (root / "RESUME.1.json").read_bytes() if (root / "RESUME.1.json").exists() else b"{}\n"
    r1 = json.loads(r1b)
    check("E2 RESUME.1: canonical, its 11 keys", (W.canon(r1) == r1b, sorted(r1)),
          (True, ["at_utc", "checks", "instance", "instance_provable", "n", "new_boot_id", "old_boot_id", "prev",
                  "run_fingerprint", "schema", "slots"]))
    check("E2 RESUME.1: n, prev, boot ids, run, instance, provable",
          (r1.get("n"), r1.get("prev"), r1.get("old_boot_id"), r1.get("new_boot_id"), r1.get("run_fingerprint"),
           r1.get("instance"), r1.get("instance_provable"), r1.get("schema")),
          (1, "first", "boot-a", "boot-b", fp_of(root), INST_H, True, 2))
    check("E2 RESUME.1: the rows are the journals' heads (slot 2: genesis)", r1.get("slots"), [h0, h1, g2])
    check("E2 RESUME.1: the seven checks", sorted(r1.get("checks", {})),
          ["boot", "chains", "clock", "fence", "hashes", "instance", "lease"])
    check("E2 the journals unchanged by the boot guard", snap(root) == before, True)
    n_ep = len([r for r in jlines(root, 0) if r["t"] == "epoch"])
    n_cl = len([r for r in jlines(root, 0) if r["t"] == "closed"])
    p = worker(root, 0, "boot-b")
    ok = wait_until(lambda: len([r for r in jlines(root, 0) if r["t"] == "closed"]) > n_cl, 180)
    codes = finish(root, [p])
    eps = [r for r in jlines(root, 0) if r["t"] == "epoch"]
    e3 = eps[n_ep] if len(eps) > n_ep else {}
    check("E3 worker 0 under boot-b: accepted, a new piece closed, exit 0 at STOP", (ok, codes), (True, [0]))
    check("E3 its epoch line names sha256(RESUME.1) and h0",
          (e3.get("resume"), e3.get("boot_id"), e3.get("last_index"), e3.get("last_seal")),
          (sha(r1b), "boot-b", h0["last_index"], h0["last_seal"]))
    p = worker(root, 0, "boot-b")
    ok = wait_until(lambda: len([r for r in jlines(root, 0) if r["t"] == "epoch"]) > n_ep + 1, 120)
    codes = finish(root, [p])
    eps = [r for r in jlines(root, 0) if r["t"] == "epoch"]
    check("E4 worker 0 again under boot-b: rule (b), resume null, exit 0",
          (ok, codes, eps[-1].get("resume") if eps else "none", eps[-1].get("boot_id") if eps else None),
          (True, [0], None, "boot-b"))
    every = whole(root)
    check("E5 the boot guard again under boot-b: exit 0, no RESUME.2, RESUME.1 unchanged",
          (bg(root, "boot-b"), resumes(root), (root / "RESUME.1.json").read_bytes() == r1b),
          (0, ["RESUME.1.json"], True))
    check("E5 every file of the root unchanged", changed(every, whole(root), but=()), [])
    h0b = head(root, 0)
    true("E6 slot 0's head moved on since RESUME.1", h0b["last_index"] > h0["last_index"], (h0, h0b))
    every = whole(root)
    check("E6 the boot guard under boot-c: exit 0", bg(root, "boot-c"), 0)
    check("E6 every file of the root unchanged but the new RESUME.2", changed(every, whole(root)), ["RESUME.2.json"])
    r2b = (root / "RESUME.2.json").read_bytes() if (root / "RESUME.2.json").exists() else b"{}\n"
    r2 = json.loads(r2b)
    check("E6 RESUME.2: n 2, prev = sha256(RESUME.1), old boot-b, new boot-c, rows now",
          (r2.get("n"), r2.get("prev"), r2.get("old_boot_id"), r2.get("new_boot_id"), r2.get("slots")),
          (2, sha(r1b), "boot-b", "boot-c", [h0b, h1, g2]))
    n_ep1 = len([r for r in jlines(root, 1) if r["t"] == "epoch"])
    p = worker(root, 1, "boot-c")
    ok = wait_until(lambda: len([r for r in jlines(root, 1) if r["t"] == "epoch"]) > n_ep1, 120)
    codes = finish(root, [p])
    eps = [r for r in jlines(root, 1) if r["t"] == "epoch"]
    e7 = eps[n_ep1] if len(eps) > n_ep1 else {}
    check("E7 worker 1 under boot-c: its epoch line names sha256(RESUME.2) and h1, exit 0",
          (ok, codes, e7.get("resume"), e7.get("last_index"), e7.get("last_seal")),
          (True, [0], sha(r2b), h1["last_index"], h1["last_seal"]))
    hd = json.loads((root / "RUN.json").read_bytes())
    (root / "FENCE.json").write_bytes(W.canon({"at_utc": T(time.time()), "cutoff_utc": hd["hard_cutoff_utc"],
                                               "run_fingerprint": fp_of(root), "why": "the test's fence"}))
    check("E8 a fence, boot-d: exit 5, no RESUME.3", (bg(root, "boot-d"), resumes(root)),
          (5, ["RESUME.1.json", "RESUME.2.json"]))


def case(name):
    c = WORK / name
    shutil.copytree(WORK / "state_a", c)
    return c


def flip(src: Path, dst: Path):
    data = bytearray(src.read_bytes())
    data[-1] ^= 1
    dst.write_bytes(bytes(data))
    return dst


def part_b():
    c = case("b1")
    every = whole(c)
    check("B1 the header's boot: exit 0, no RESUME", (bg(c, "boot-a"), resumes(c)), (0, []))
    check("B1 every file of the root unchanged", changed(every, whole(c), but=()), [])
    c = case("b2")
    held_case("B2 another machine id", c, lambda: bg(c, "boot-b", inst="m2"), 5)
    c = case("b3")
    held_case("B3 no product uuid now", c, lambda: bg(c, "boot-b", inst="nouuid"), 5)
    c = case("b6")
    held_case("B6 never synchronised", c, lambda: bg(c, "boot-b", synced=False, sync_wait=1.0), 5)
    c = case("b7")
    newest = max(p.stat().st_mtime for p in c.glob("w*/journal.txt"))
    held_case("B7 UTC 100 s before the newest journal", c, lambda: bg(c, "boot-b", utc=lambda: newest - 100), 5)
    c = case("b8")
    held_case("B8 the engine one byte changed", c, lambda: bg(c, "boot-b", exe=flip(EXE, WORK / "bad_engine.exe")), 5)
    c = case("b9")
    held_case("B9 the net one byte changed", c, lambda: bg(c, "boot-b", net=flip(NET, WORK / "bad.net")), 5)
    c = case("b10")
    pk = WORK / "pkg10"
    shutil.copytree(PKG, pk)
    f = sorted(p for p in (pk / "run").glob("*.py"))[0]
    f.write_bytes(f.read_bytes() + b"# changed\n")
    held_case("B10 a listed package file changed", c, lambda: bg(c, "boot-b", pkg_list=pk / "MANIFEST.sha256"), 5)
    c = case("b11")
    pk = WORK / "pkg11"
    shutil.copytree(PKG, pk)
    f = pk / "run" / "worker.py"
    f.write_bytes(f.read_bytes() + b"# changed\n")
    rows = [ln for ln in (pk / "MANIFEST.sha256").read_text(encoding="ascii").split("\n")[:-1]
            if not ln.startswith("digest ")]
    rows = [(f"{sha(f.read_bytes())}  run/worker.py" if ln.endswith("  run/worker.py") else ln) for ln in rows]
    rows.append("digest " + sha(("\n".join(rows) + "\n").encode("ascii")))
    (pk / "MANIFEST.sha256").write_bytes(("\n".join(rows) + "\n").encode("ascii"))
    held_case("B11 a self-consistent list that is not the header's", c,
              lambda: bg(c, "boot-b", pkg_list=pk / "MANIFEST.sha256"), 5)
    c = case("b12")
    hd = json.loads((c / "RUN.json").read_bytes())
    (c / "FENCE.json").write_bytes(W.canon({"at_utc": T(time.time()), "cutoff_utc": hd["hard_cutoff_utc"],
                                            "run_fingerprint": fp_of(c), "why": "the test's fence"}))
    held_case("B12 FENCE.json", c, lambda: bg(c, "boot-b"), 5)
    c = case("b13")
    s = c / "w000" / "closed" / "p000000.seal.json"
    flip(s, s)
    held_case("B13 slot 0's first seal one byte changed", c, lambda: bg(c, "boot-b"), 4)
    c = case("b14")
    (c / "w001" / "IDENTITY.json").write_bytes(W.canon({"run": "other", "run_fingerprint": "0" * 64, "schema": 2,
                                                        "slot": 1}))
    held_case("B14 slot 1's IDENTITY.json of another run", c, lambda: bg(c, "boot-b"), 4)
    c = case("b15")
    (c / "RESUME.1.json").write_bytes(W.canon({"n": 1, "new_boot_id": "boot-x", "prev": "x",
                                               "run_fingerprint": fp_of(c), "schema": 2}))
    before = snap(c)
    check("B15 a RESUME.1 whose prev is not first: exit 4, nothing new",
          (bg(c, "boot-b"), resumes(c), snap(c) == before), (4, ["RESUME.1.json"], True))
    c = case("b16")
    lk = W.SlotLock(c / "w000")
    try:
        held_case("B16 slot 0's lock held", c, lambda: bg(c, "boot-b"), 3)
    finally:
        lk.release()
    c = case("b17")
    (c / "guard").mkdir()
    lk = W.SlotLock(c / "guard")
    try:
        held_case("B17 guard/LOCK held", c, lambda: bg(c, "boot-b"), 3)
    finally:
        lk.release()
    c = case("b18")
    codes = (bg(c, "boot-b", inst="m2"), bg(c, "boot-b", inst="m2"))
    log = (c / "guard" / "bootguard.log").read_bytes().decode("ascii").splitlines() \
        if (c / "guard" / "bootguard.log").exists() else []
    check("B18 the same hold twice: two exits 5, ONE alarm line naming the machine id",
          (codes, len(log), "machine id" in (log[0] if log else "")), ((5, 5), 1, True))
    t = new_run("t1", [5, 6], inst={"machine_id": INST_H["machine_id"], "product_uuid": INST_H["product_uuid"],
                                    "board_serial": None})
    g, every = f"genesis:{fp_of(t)}", whole(t)
    code = bg(t, "boot-b", inst="noserial")
    check("T1 every file of the root unchanged but the new RESUME.1", changed(every, whole(t)), ["RESUME.1.json"])
    r = json.loads((t / "RESUME.1.json").read_bytes()) if (t / "RESUME.1.json").exists() else {}
    check("T1 board serial null on both sides: EQUAL, RESUME.1 with genesis rows",
          (code, r.get("slots")), (0, [{"last_index": -1, "last_seal": f"{g}:w005", "slot": 5},
                                       {"last_index": -1, "last_seal": f"{g}:w006", "slot": 6}]))
    t = new_run("b19", [5, 6])
    hd = json.loads((t / "RUN.json").read_bytes())
    del hd["package"]
    (t / "RUN.json").write_bytes(W.canon(hd))
    held_case("B19 a header without `package`", t, lambda: bg(t, "boot-b"), 4)
    log = (t / "guard" / "bootguard.log").read_bytes().decode("ascii") if (t / "guard" / "bootguard.log").exists() else ""
    true("B19 the alarm line names the missing key", "RUN.json lacks package" in log, log)
    c = case("b20")
    held_case("B20 the manifest missing", c, lambda: bg(c, "boot-b", man=WORK / "no_such_manifest.json"), 4)
    log = (c / "guard" / "bootguard.log").read_bytes().decode("ascii") if (c / "guard" / "bootguard.log").exists() else ""
    true("B20 the alarm line names FileNotFoundError", "HELD exit 4: FileNotFoundError" in log, log)
    c = case("b21")
    (c / "RESUME.1.json").write_bytes(W.canon({"n": 1, "new_boot_id": "boot-x", "old_boot_id": "boot-z",
                                               "prev": "first", "run_fingerprint": fp_of(c), "schema": 2}))
    before, every = snap(c), whole(c)
    check("B21 a RESUME.1 whose old_boot_id is not the header's boot: exit 4, nothing new",
          (safe(lambda: bg(c, "boot-b")), resumes(c), snap(c) == before), (4, ["RESUME.1.json"], True))
    check("B21 every file of the root unchanged but the alarm log", changed(every, whole(c)), ["guard/bootguard.log"])
    t = new_run("t2", [5, 6], provable=False)
    held_case("T2 the header's instance_provable false", t, lambda: bg(t, "boot-b"), 5)
    t = new_run("t3", [5, 6], inst={"machine_id": INST_H["machine_id"], "product_uuid": None, "board_serial": None})
    held_case("T3 the header's hardware values both null", t, lambda: bg(t, "boot-b", inst="noserial"), 5)


# ---- part V: version 2 (Astra 7334dbd6, Neon 222600Z) ---------------------------------------------------------
def held_v(name, root, fn, want, words):
    """A hold of version 2: the exit, the alarm naming `words`, the RESUMEs as before, no .tmp, every journal and
    every file of the root unchanged but the alarm log."""
    before, every, rs = snap(root), whole(root), resumes(root)
    code = safe(fn)
    log = root / "guard" / "bootguard.log"
    last = log.read_bytes().decode("ascii", "replace").rstrip("\n").rsplit("\n", 1)[-1] if log.exists() else ""
    check(f"{name}: exit {want} naming {', '.join(words)}, RESUMEs as before, no .tmp",
          (code, "named" if all(w in last for w in words) else last[-200:], resumes(root),
           sorted(p.name for p in root.glob("*.tmp"))), (want, "named", rs, []))
    check(f"{name}: every journal unchanged", snap(root) == before, True)
    check(f"{name}: every file of the root unchanged but the alarm log", changed(every, whole(root)),
          ["guard/bootguard.log"])


def admitted_v(name, root, fn, new_resume, rows=None):
    every = whole(root)
    check(f"{name}: exit 0, every file of the root unchanged but the new {new_resume}",
          (safe(fn), changed(every, whole(root))), (0, [new_resume]))
    if rows is not None:
        r = json.loads((root / new_resume).read_bytes()) if (root / new_resume).exists() else {}
        check(f"{name}: {new_resume}'s rows", r.get("slots"), rows)


def case_of(src, name):
    c = WORK / name
    shutil.copytree(WORK / src, c)
    return c


def rewrite(root, k, fn):
    """RESUME.k rewritten canonically after fn(record) changed it."""
    p = root / f"RESUME.{k}.json"
    r = json.loads(p.read_bytes())
    fn(r)
    p.write_bytes(W.canon(r))


def dir_link(link: Path, target: Path) -> None:
    """A folder link inside the test's own folder: a junction on Windows (no rights needed), a symlink on Linux."""
    if sys.platform == "win32":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


def part_v():
    h0, h1, g2 = STATE["h0"], STATE["h1"], STATE["g2"]
    r1 = case_of("state_a", "state_r1")
    check("V0 state R1: the guard under boot-b writes RESUME.1", (safe(lambda: bg(r1, "boot-b")), resumes(r1)),
          (0, ["RESUME.1.json"]))
    c = case("v1")
    (c / "w000" / "journal.txt").unlink()
    held_v("V1 w000's journal removed beside its pieces", c, lambda: bg(c, "boot-b"), 4, ("w000/closed/p000000.raw",))
    c = case_of("state_r1", "v2")
    shutil.rmtree(c / "w000")
    held_v("V2 R1, w000 withheld, boot-c", c, lambda: bg(c, "boot-c"), 4, ("w000", "RESUME.1"))
    c = case_of("state_r1", "v3")
    admitted_v("V3 control: R1 intact, boot-c", c, lambda: bg(c, "boot-c"), "RESUME.2.json", [h0, h1, g2])
    c = case_of("state_r1", "v4")
    j = c / "w000" / "journal.txt"
    lines = j.read_bytes().split(b"\n")[:-1]
    cut = max(i for i, ln in enumerate(lines) if json.loads(ln)["t"] == "closed")
    j.write_bytes(b"".join(ln + b"\n" for ln in lines[:cut]))
    held_v("V4 R1, w000's journal cut before its last closed line", c, lambda: bg(c, "boot-c"), 4, ("w000", "RESUME.1"))
    c = case_of("state_r1", "v5")
    rewrite(c, 1, lambda r: r["slots"][1].update(last_seal="ab" * 32))
    held_v("V5 R1, slot 1's admitted seal forged", c, lambda: bg(c, "boot-c"), 4, ("w001", "RESUME.1", "another seal"))
    c = case("v6")
    stray = f"p{h1['last_index'] + 5:06d}.raw"
    shutil.copyfile(c / "w001" / "closed" / "p000000.raw", c / "w001" / "closed" / stray)
    held_v("V6 a stray closed piece in w001", c, lambda: bg(c, "boot-b"), 4, (f"w001/closed/{stray}",))
    c = case("v7")
    shutil.copyfile(c / "w000" / "closed" / "p000000.raw", c / "w000" / "open" / "p000000.raw")
    held_v("V7 a stale open/p000000.raw in w000", c, lambda: bg(c, "boot-b"), 4, ("w000/open/p000000.raw",))
    c = case("v7b")
    (c / "w000" / "open" / f"p{h0['last_index'] + 1:06d}.raw").write_bytes(b"game written, not journalled\n")
    admitted_v("V7b control: the open piece with bytes not journalled", c, lambda: bg(c, "boot-b"), "RESUME.1.json",
               [h0, h1, g2])
    c = case("v7c")
    (c / "w001" / "journal.txt").unlink()
    for f in (c / "w001" / "closed").iterdir():
        f.unlink()
    (c / "w001" / "open" / "p000000.raw").write_bytes(b"game bytes\n")
    held_v("V7c w001: no journal, no closed piece, only open/p000000.raw", c, lambda: bg(c, "boot-b"), 4,
           ("w001/open/p000000.raw",))
    c = case("v8")
    pk, away = WORK / "pkg8", WORK / "pkg8_run_elsewhere"
    shutil.copytree(PKG, pk)
    (pk / "run").rename(away)
    dir_link(pk / "run", away)
    true("V8 setup: pkg8/run is a link to a folder with the same bytes",
         (pk / "run" / "worker.py").read_bytes() == (PKG / "run" / "worker.py").read_bytes()
         and (pk / "run").resolve() == away.resolve(), (pk / "run").resolve())
    held_v("V8 a junction (Windows) or link (Linux) inside the package", c,
           lambda: bg(c, "boot-b", pkg_list=pk / "MANIFEST.sha256"), 5, ("run/", "link or junction"))
    t = new_run("v9", [])
    held_v("V9 a header with slots []", t, lambda: bg(t, "boot-b"), 4, ("slots",))
    c = case("v10")
    (c / "guard").mkdir(exist_ok=True)
    (c / "guard" / "CLOSED.json").write_bytes(b"{}\n")
    held_v("V10 guard/CLOSED.json without FENCE.json", c, lambda: bg(c, "boot-b"), 4, ("CLOSED.json",))
    for name, later in (("v11", 1800), ("v11b", 3610)):
        c = case(name)
        newest = max(p.stat().st_mtime for p in c.glob("w*/journal.txt"))
        check(f"{name.upper()} setup: RESUME.1 written at UTC newest + 3600",
              safe(lambda: bg(c, "boot-b", utc=lambda: newest + 3600)), 0)
        if later < 3600:
            held_v("V11 boot-c at newest + 1800, before RESUME.1's at_utc", c,
                   lambda: bg(c, "boot-c", utc=lambda: newest + later), 5, ("RESUME.1.json's at_utc",))
        else:
            admitted_v("V11b control: boot-c at newest + 3610", c, lambda: bg(c, "boot-c", utc=lambda: newest + later),
                       "RESUME.2.json")
    t = new_run("v12", [5, 6])
    ls = W.utc(json.loads((t / "RUN.json").read_bytes())["lease_start_utc"], "the test's lease start")
    held_v("V12 a fresh run, UTC 100 s before the lease start", t, lambda: bg(t, "boot-b", utc=lambda: ls - 100), 5,
           ("the lease start",))
    for name, fn, words in (
            ("V13a slot 2's genesis forged as 64 zeros", lambda r: r["slots"][2].update(last_seal="0" * 64), ("slots",)),
            ("V13b instance_provable false", lambda r: r.update(instance_provable=False), ("instance_provable",)),
            ("V13c at_utc yesterday", lambda r: r.update(at_utc="yesterday"), ("at_utc",)),
            ("V13e old_boot_id boot-z", lambda r: r.update(old_boot_id="boot-z"), ("old_boot_id",)),
            ("V13f new_boot_id = old_boot_id", lambda r: r.update(new_boot_id="boot-a"), ("new_boot_id is its old",)),
            ("V13g an extra key", lambda r: r.update(note="x"), ("eleven",)),
            ("V13h instance null", lambda r: r.update(instance=None), ("instance is not",)),
            ("V13i no clock check", lambda r: r["checks"].pop("clock"), ("seven",))):
        c = case_of("state_r1", name.split()[0].lower())
        rewrite(c, 1, fn)
        held_v(f"{name} in RESUME.1, boot-c", c, lambda: bg(c, "boot-c"), 4, ("RESUME.1.json",) + words)
    c = case_of("state_r1", "v13d")
    r1b = (c / "RESUME.1.json").read_bytes()
    r1r = json.loads(r1b)
    r2 = dict(r1r, n=2, prev=sha(r1b), old_boot_id="boot-b", new_boot_id="boot-c",
              at_utc=T(W.utc(r1r["at_utc"], "RESUME.1 at_utc") - 50))
    (c / "RESUME.2.json").write_bytes(W.canon(r2))
    held_v("V13d a hand-made RESUME.2 50 s before RESUME.1, boot-d", c, lambda: bg(c, "boot-d"), 4,
           ("RESUME.2.json", "at_utc"))
    c = case("v14")
    newest = max(p.stat().st_mtime for p in c.glob("w*/journal.txt"))
    os.utime(c / "w000" / "journal.txt", (newest + 7200, newest + 7200))
    held_v("V14 a journal 7,200 s ahead, UTC newest + 3,600", c, lambda: bg(c, "boot-b", utc=lambda: newest + 3600),
           5, ("newest journal",))


try:
    for part, fn in (("U", part_u), ("A", phase_a), ("E", part_e), ("B", part_b), ("V", part_v)):
        if part in ONLY or (part == "A" and ONLY & {"E", "B", "V"}):
            try:
                fn()
            except Exception as e:  # noqa: BLE001   one failed check, its traceback printed, the next part runs
                traceback.print_exc()
                true(f"part {part} ended by {type(e).__name__}: {str(e)[:200]}", False)
finally:
    for p in PROCS:
        if p.poll() is None:
            p.kill()
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)

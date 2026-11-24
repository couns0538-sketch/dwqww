"""test_launcher.py: the launcher (A3b, part 2, run/launcher.py) against known answers written BEFORE it ran
(tmp/opus_scratch/launcher/KNOWN_ANSWERS_by_opus.md on the PC; FORMATS 1.1, 1.2, 0; SETUP_PLAN D3, D5, D15).

    test_launcher.py <run/launcher.py> <a NEW folder> exe=<engine> net=<net> pkg=<package folder with its
                     MANIFEST.sha256> [only=L,W] [plantN]

The run folder is copied; a plant is applied to the copy's launcher.py only. The launcher runs in this process with
planted readers (boot id, synchronised, UTC) and fixture folders for /etc and the DMI files; the expected headers
are written out here by hand, not computed by the launcher's code.
L  L0 the full launch, every key; L1 the same launch again: the same bytes, no conflict; L2 another seed: exit 4,
   RUN.json unchanged, the conflict file; L3 a lease that ends in 2 h and two pilot rounds; L4 the list rule with
   one slot, refused with two; L5 the five holds (exit 5): another pinned sha256, a package file changed, the net
   changed, an unprovable instance, a clock never synchronised; L6 the arguments (exit 2). Every refusal: the root
   stays empty.
W  the header in use: W1 the REAL worker of slot 0 with the real engine accepts it, closes a piece and stops at
   STOP with exit 0; W2 the boot guard: the header's boot 0 and nothing written; a new boot RESUME.1 whose rows are
   slot 0's head and the genesis rows of slots 1 and 2.

PLANTS (each must make the test fail; the check expected to fail is named):
  plant1 hard cutoff = start + 23 h only (L3)          plant2 hard cutoff = end - 1 h only (L0)
  plant3 a list rule with two slots allowed (L4)       plant4 no wait for synchronisation (L5)
  plant5 the package not checked (L5)                  plant6 the net not compared (L5)
  plant7 an unprovable instance written (L5)           plant8 now before the lease start allowed (L6)
  plant9 a hard cutoff in the past allowed (L6)        plant10 the pilot counters from 0 (L0, W1)
  plant11 instance_provable left out (L0, W2)          plant12 the option lines hashed without their LF (L0, W1)
  plant13 RUN.json overwritten, not create-only (L2)   plant14 the boot id not read (L0, W1)
"""
import calendar
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
    print("usage: test_launcher.py <run/launcher.py> <a NEW folder> exe=.. net=.. pkg=.. [only=L,W] [plantN]")
    sys.exit(2)
LA_PATH, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
OPTS, PLANT = {}, None
for x in sys.argv[3:]:
    if x.startswith("plant"):
        PLANT = x
    elif "=" in x and x.split("=", 1)[0] in ("exe", "net", "pkg", "only"):
        OPTS[x.split("=", 1)[0]] = x.split("=", 1)[1]
    else:
        print(f"STOP: not understood: {x}")
        sys.exit(2)
ONLY = set(OPTS.get("only", "L,W").split(","))
if not all(k in OPTS for k in ("exe", "net", "pkg")):
    print("STOP: exe=, net= and pkg= are needed")
    sys.exit(2)
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
TREE = LA_PATH.parent.parent
shutil.copytree(LA_PATH.parent, WORK / "run", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

PLANTS = {
    "plant1": ("    now, cut = rd.utc(), min(start + 23 * HOUR, end - HOUR)\n", "    now, cut = rd.utc(), start + 23 * HOUR\n"),
    "plant2": ("    now, cut = rd.utc(), min(start + 23 * HOUR, end - HOUR)\n", "    now, cut = rd.utc(), end - HOUR\n"),
    "plant3": ("        if a.slots > 1:\n", "        if False:\n"),
    "plant4": ("    while not rd.synced():\n", "    while False:\n"),
    "plant5": ("    BG.BootGuard(a, rd).package({\"package\": a.pinned})\n", "    pass\n"),
    "plant6": ("    if net != want:\n", "    if False:\n"),
    "plant7": ("    if not BG.provable(inst):\n", "    if False:\n"),
    "plant8": ("    if now < start:\n", "    if False:\n"),
    "plant9": ("    if cut <= now:\n", "    if False:\n"),
    "plant10": ("\"first\": (r - 1) * a.round_games + 1,", "\"first\": (r - 1) * a.round_games,"),
    "plant11": ("\"instance\": inst, \"instance_provable\": True,", "\"instance\": inst,"),
    "plant12": ("sha256_bytes(\"\".join(ln + \"\\n\" for ln in opts).encode(\"ascii\"))",
                "sha256_bytes(\"\".join(opts).encode(\"ascii\"))"),
    "plant13": ("        create_only(Path(a.root) / \"RUN.json\", data)\n",
                "        (Path(a.root) / \"RUN.json\").write_bytes(data)\n"),
    "plant14": ("\"boot_id\": rd.boot(),", "\"boot_id\": \"none\","),
}
if PLANT:
    if PLANT not in PLANTS:
        print(f"STOP: no plant {PLANT}")
        sys.exit(2)
    old, new = PLANTS[PLANT]
    lp = WORK / "run" / "launcher.py"
    text = lp.read_text(encoding="utf-8")
    if text.count(old) != 1:
        print(f"STOP: {PLANT}: its text stands {text.count(old)} times in the launcher")
        sys.exit(2)
    lp.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print(f"PLANT {PLANT} applied to the copy")

sys.path.insert(0, str(WORK / "run"))
import bootguard as BG  # noqa: E402
import launcher as LA  # noqa: E402
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


def secs(text):
    return calendar.timegm(time.strptime(text, "%Y-%m-%dT%H:%M:%SZ"))


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---- fixtures (by hand) ------------------------------------------------------------------------------------------
M, U, S = "0123456789abcdef0123456789abcdef", "4c4c4544-0042-3510-8051-b4c04f4e3132", "BSN-12345-X"
INST = WORK / "inst"
for name, files in {"ok": {"etc/machine-id": M, "dmi/product_uuid": U, "dmi/board_serial": S},
                    "unprov": {"etc/machine-id": M, "dmi/product_uuid": "Not Specified"}}.items():
    for sub in ("etc", "dmi"):
        (INST / name / sub).mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        (INST / name / rel).write_bytes((text + "\n").encode("ascii"))
INST_H = {"board_serial": sha(S.encode()), "machine_id": sha(M.encode()), "product_uuid": sha(U.encode())}
PKG = WORK / "pkg"
shutil.copytree(Path(OPTS["pkg"]).resolve(), PKG)
PKG_LIST = PKG / "MANIFEST.sha256"
PINNED = sha(PKG_LIST.read_bytes())
MANI = json.loads(MAN.read_bytes())
OPTIONS_SHA = sha("".join(ln + "\n" for ln in MANI["options"]).encode("ascii"))
n12 = [ln.split()[3:] for ln in (TREE / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
OPEN = WORK / "openings.txt"
OPEN.write_bytes("".join(" ".join(o) + "\n" for o in n12).encode("ascii"))
WRAP = WORK / "worker_boot.py"
WRAP.write_text("import os, sys\nsys.path.insert(0, sys.argv.pop(1))\nimport worker\n"
                "worker.boot_id = lambda: os.environ['LAUNCHER_TEST_BOOT']\nsys.exit(worker.main())\n",
                encoding="ascii", newline="\n")
NOW = int(time.time())


def ns(root, **kw):
    a = dict(root=str(root), exe=str(EXE), net=str(NET), manifest=str(MAN), package_list=str(PKG_LIST),
             pinned=PINNED, run="lt", lease_start=T(NOW - 60), lease_end=T(NOW + 86400), slots=3, piece_games=1,
             round_games=8, pilot_rounds=1, root_seed="s1", openings=None, sync_wait=900.0,
             etc=str(INST / "ok" / "etc"), dmi=str(INST / "ok" / "dmi"))
    a.update(kw)
    return SimpleNamespace(**a)


def rd(boot="boot-a", synced=True, utc=None):
    return SimpleNamespace(boot=lambda: boot, synced=lambda: synced, utc=utc or time.time, sleep=time.sleep)


def fresh(name):
    p = WORK / name
    p.mkdir()
    return p


def head_of(root):
    b = (root / "RUN.json").read_bytes() if (root / "RUN.json").exists() else b"{}\n"
    return b, json.loads(b)


def row(k, r, first, last):
    return {"first": first, "last": last, "round": r, "schedule": 0, "short": False, "slot": k}


def by_slot(rows):
    return sorted(rows, key=lambda x: (x["slot"], x["round"])) if isinstance(rows, list) else rows


def held(name, root, code, want):
    check(f"{name}: exit {want}, the root stays empty", (code, sorted(os.listdir(root))), (want, []))


def part_l():
    r0 = fresh("l0")
    code = LA.launch(ns(r0), rd())
    b, h = head_of(r0)
    check("L0 the full launch: exit 0", code, 0)
    check("L0 RUN.json canonical, its 17 keys", (W.canon(h) == b, sorted(h)),
          (True, ["boot_id", "engine_sha256", "game_line", "hard_cutoff_utc", "instance", "instance_provable",
                  "lease_end_utc", "lease_start_utc", "net_sha256", "opening_rule", "options_sha256", "package",
                  "piece_games", "pilot_ranges", "run", "schema", "slots"]))
    want = {"schema": 2, "run": "lt", "lease_start_utc": T(NOW - 60), "lease_end_utc": T(NOW + 86400),
            "hard_cutoff_utc": T(NOW - 60 + 23 * 3600), "boot_id": "boot-a", "instance": INST_H,
            "instance_provable": True, "package": PINNED, "engine_sha256": sha(EXE.read_bytes()),
            "net_sha256": sha(NET.read_bytes()), "options_sha256": OPTIONS_SHA, "game_line": MANI["selfgame_line"],
            "opening_rule": {"kind": "seed", "plies": 8, "root_seed": "s1"}, "slots": [0, 1, 2], "piece_games": 1}
    for k, v in want.items():
        check(f"L0 {k}", h.get(k), v)
    check("L0 the pilot rows: one round of 8 games a slot", by_slot(h.get("pilot_ranges")),
          [row(0, 1, 1, 8), row(1, 1, 1, 8), row(2, 1, 1, 8)])
    check("L0 the root holds RUN.json alone", sorted(os.listdir(r0)), ["RUN.json"])
    check("L1 the same launch again: exit 0, the same bytes, no conflict file",
          (LA.launch(ns(r0), rd()), (r0 / "RUN.json").read_bytes() == b, sorted(os.listdir(r0))), (0, True, ["RUN.json"]))
    other = dict(h, opening_rule={"kind": "seed", "plies": 8, "root_seed": "s2"})
    conflict = f"RUN.json.conflict.{sha(W.canon(other))[:12]}"
    code = LA.launch(ns(r0, root_seed="s2"), rd())
    check("L2 another seed into the same root: exit 4, RUN.json unchanged, the conflict file with the new bytes",
          (code, (r0 / "RUN.json").read_bytes() == b, sorted(os.listdir(r0)),
           (r0 / conflict).read_bytes() == W.canon(other) if (r0 / conflict).exists() else False),
          (4, True, sorted(["RUN.json", conflict]), True))
    r3 = fresh("l3")
    check("L3 a lease that ends in 2 h, two pilot rounds: exit 0",
          LA.launch(ns(r3, lease_end=T(NOW + 7200), pilot_rounds=2), rd()), 0)
    _, h3 = head_of(r3)
    check("L3 hard cutoff = end - 1 h", h3.get("hard_cutoff_utc"), T(NOW + 3600))
    check("L3 six rows: round 2 holds the counters 9 to 16", by_slot(h3.get("pilot_ranges")),
          [row(0, 1, 1, 8), row(0, 2, 9, 16), row(1, 1, 1, 8), row(1, 2, 9, 16), row(2, 1, 1, 8), row(2, 2, 9, 16)])
    r4 = fresh("l4")
    check("L4 the list rule with one slot: exit 0", LA.launch(ns(r4, slots=1, root_seed=None, openings=str(OPEN)), rd()),
          0)
    _, h4 = head_of(r4)
    check("L4 the list rule: kind, sha256 of the file, count of its lines", (h4.get("opening_rule"), h4.get("slots")),
          ({"kind": "list", "sha256": sha(OPEN.read_bytes()), "count": len(n12)}, [0]))
    r = fresh("l4b")
    held("L4 the list rule with two slots", r, LA.launch(ns(r, slots=2, root_seed=None, openings=str(OPEN)), rd()), 2)
    r = fresh("l5a")
    held("L5 another pinned sha256", r, LA.launch(ns(r, pinned="0" * 64), rd()), 5)
    pk = WORK / "pkg5"
    shutil.copytree(PKG, pk)
    f = pk / "run" / "worker.py"
    f.write_bytes(f.read_bytes() + b"# changed\n")
    r = fresh("l5b")
    held("L5 a listed package file changed", r, LA.launch(ns(r, package_list=str(pk / "MANIFEST.sha256")), rd()), 5)
    bad = WORK / "bad.net"
    data = bytearray(NET.read_bytes())
    data[-1] ^= 1
    bad.write_bytes(bytes(data))
    r = fresh("l5c")
    held("L5 the net one byte changed", r, LA.launch(ns(r, net=str(bad)), rd()), 5)
    r = fresh("l5d")
    held("L5 an unprovable instance", r, LA.launch(ns(r, etc=str(INST / "unprov" / "etc"),
                                                     dmi=str(INST / "unprov" / "dmi")), rd()), 5)
    r = fresh("l5e")
    held("L5 a clock never synchronised (sync-wait 1 s)", r, LA.launch(ns(r, sync_wait=1.0), rd(synced=False)), 5)
    for name, kw in (("run name Bad", {"run": "Bad"}),
                     ("lease end before its start", {"lease_end": T(NOW - 120)}),
                     ("a hard cutoff already past", {"lease_start": T(NOW - 30 * 3600), "lease_end": T(NOW + 36000)}),
                     ("now before the lease start", {"lease_start": T(NOW + 600)}),
                     ("slots 0", {"slots": 0}),
                     ("a root seed with a space", {"root_seed": "s 1"}),
                     ("both opening rules", {"openings": str(OPEN)}),
                     ("a lease time that does not exist", {"lease_end": "2026-11-31T00:00:00Z"})):
        r = fresh("l6_" + str(len(RESULTS)))
        held(f"L6 {name}", r, LA.launch(ns(r, **kw), rd()), 2)
    code = LA.launch(ns(WORK / "no_such_root"), rd())
    check("L6 the root missing: exit 2, nothing made", (code, (WORK / "no_such_root").exists()), (2, False))


def worker(root, k, boot):
    log = open(WORK / f"{root.name}.w{k}.{boot}.out", "ab")
    p = subprocess.Popen([sys.executable, "-I", "-B", str(WRAP), str(WORK / "run"), "--root", str(root), "--exe",
                          str(EXE), "--net", str(NET), "--manifest", str(MAN), "--known-startup", str(KNOWN),
                          "--slot", str(k)],
                         env={**os.environ, "LAUNCHER_TEST_BOOT": boot}, stdout=log, stderr=subprocess.STDOUT)
    log.close()
    PROCS.append(p)
    return p


def jlines(root, k):
    j = root / f"w{k:03d}" / "journal.txt"
    return [json.loads(ln) for ln in j.read_bytes().split(b"\n")[:-1]] if j.exists() else []


def part_w():
    root = fresh("w")
    check("W the launch for the workers: exit 0", LA.launch(ns(root), rd()), 0)
    p = worker(root, 0, "boot-a")
    end = time.monotonic() + 180
    while time.monotonic() < end and p.poll() is None and not any(x["t"] == "closed" for x in jlines(root, 0)):
        time.sleep(0.1)
    closed = any(x["t"] == "closed" for x in jlines(root, 0))
    (root / "STOP").write_bytes(b"")
    try:
        code = p.wait(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
        code = None
    (root / "STOP").unlink()
    check("W1 the real worker of slot 0 under the launched header: a piece closed, exit 0 at STOP", (closed, code),
          (True, 0))
    fp = sha((root / "RUN.json").read_bytes())
    last = (-1, f"genesis:{fp}:w000")
    for x in jlines(root, 0):
        if x["t"] == "closed":
            last = (x["index"], x["seal"])
    a = SimpleNamespace(root=str(root), exe=str(EXE), net=str(NET), manifest=str(MAN), known_startup=str(KNOWN),
                        openings="", package_list=str(PKG_LIST), sync_wait=900.0, etc=str(INST / "ok" / "etc"),
                        dmi=str(INST / "ok" / "dmi"))
    before = sorted(os.listdir(root))
    check("W2 the boot guard under the header's boot: exit 0, nothing written",
          (BG.BootGuard(a, rd("boot-a")).run(), sorted(os.listdir(root))), (0, before))
    code = BG.BootGuard(a, rd("boot-b")).run()
    r1 = json.loads((root / "RESUME.1.json").read_bytes()) if (root / "RESUME.1.json").exists() else {}
    check("W2 the boot guard under a new boot: RESUME.1, rows = slot 0's head and the genesis of slots 1 and 2",
          (code, r1.get("old_boot_id"), r1.get("new_boot_id"), r1.get("slots")),
          (0, "boot-a", "boot-b", [{"last_index": last[0], "last_seal": last[1], "slot": 0},
                                   {"last_index": -1, "last_seal": f"genesis:{fp}:w001", "slot": 1},
                                   {"last_index": -1, "last_seal": f"genesis:{fp}:w002", "slot": 2}]))
    true("W2 slot 0's head is a closed piece", last[0] >= 0, last)


try:
    for part, fn in (("L", part_l), ("W", part_w)):
        if part in ONLY:
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

"""test_clock_use.py: no DECISION at home takes the PC's clock (v16; part U of the clock known answers,
tmp/opus_scratch/clock/KNOWN_ANSWERS_clock_by_opus.md on the PC: Fable's guard against a place to forget). Standard
library only; a PLAIN interpreter.

    test_clock_use.py <tree> <a NEW folder> [plant3|plant4|plant5|plant6|plant7|plant8|plant9|plant10|plant11|list]

The PC's clock runs about 25,178 s (7 hours) ahead of real UTC. Home's DECISIONS take the server's time (home/clock.py,
server_now and server_text); STAMPS for people stay on the PC's clock, each one allow-listed here with the reader that
checks its form only. The test copies <tree>'s home/, tools/ and run/ into the new folder (a plant changes the copy
only) and reads with ast every .py of home/ and tools/, and every run/ file that one of them imports. It FAILs on:
- a call that reads the wall clock, outside home/clock.py and the allow-list: time.time, time.time_ns, datetime.now,
  datetime.utcnow, datetime.today, date.today; gmtime, localtime, ctime or asctime with NO argument; strftime with ONE
  argument (imports and aliases are followed: `import time as T`, `from time import time`, `from datetime import
  datetime`, `__import__("time")`);
- a call of a stamp function (custody.utc, fetch.utc, publish.utc_now) from a place that is not allow-listed;
- (stricter than part U) any of these functions handed on UNCALLED (`wall=time.time`), outside the allow-list.
An allow-list row is (file, the line's exact text, the reason); each row must stand exactly once in its file.
U1  v16: ALL PASS.
U2  v15 (the proof runs it on v15's tree): the unlisted calls are exactly deliver.py:252 (time.time, the D check) and
    drain.py:248 (custody's utc() for the decision); the rows v16 added are missing there.
U3  plant3: a bare time.time() added to drain.py FAILs, naming drain.py.
U4  plant4: a call of custody's utc() added to deliver.py FAILs, naming deliver.py.
plant5 (for the stricter rule): `time.time` handed on uncalled in deliver.py FAILs, naming deliver.py.
list: prints every call found (allowed or not) and exits 0: for building and reading the allow-list.

v17 (RU1 and RU2: Fable's remarks on v16's test, taken by Opus on 25 Nov; written by Fable on 26 Nov 2026; known
answers tmp/fable_scratch/v17_ru/KNOWN_ANSWERS_ru_by_fable.md on the PC):
U5  a star import (`from x import *`) in a scanned file FAILs: it leaves names the resolver cannot follow (`from time
    import *` then `time()`; `from custody import *` then `utc()`). plant6.
U6  a FILE's time is the PC's clock too: st_mtime, st_ctime, st_atime, st_birthtime (and their _ns forms), getmtime,
    getctime, getatime FAIL as an attribute or as a name imported from a module, outside the allow-list (no row
    today). plant7.
RU2 the scan's field is also every run/ file that a home/ or tools/ file imports (today worker, packer, record): all
    of it but the bodies of the SERVER classes below (the server's own programs; they run on the server, on the
    server's clock). plant8 (module level), plant9 (a class that is not a server class).
U7  each SERVER class stands exactly once, at the top level of a scanned run/ file. plant11.
U8  no home/ or tools/ file names a SERVER class, so the exemption cannot be reached from home. plant10.
NOT seen, by intent of a writer and not by forgetting (left as it is): a module handed on under another name (`m =
time; m.time()`), `getattr(__import__("time"), "time")()`, a name built from text, a clock read inside a run/ file
that home does not import itself.
"""
import ast
import shutil
import sys
from pathlib import Path

MODES = (None, "plant3", "plant4", "plant5", "plant6", "plant7", "plant8", "plant9", "plant10", "plant11", "list")
if len(sys.argv) < 3:
    print("usage: test_clock_use.py <tree> <a NEW folder> [plant3|...|plant11|list]")
    sys.exit(2)
SRC, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
MODE = sys.argv[3] if len(sys.argv) > 3 else None
if MODE not in MODES:
    print(f"STOP: not understood: {MODE}")
    sys.exit(2)
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
for sub in ("home", "tools", "run"):
    shutil.copytree(SRC / sub, WORK / sub, ignore=shutil.ignore_patterns("__pycache__"))

WALL = {("time", "time"), ("time", "time_ns"), ("datetime", "now"), ("datetime", "utcnow"), ("datetime", "today"),
        ("date", "today")}
NOARG = {"gmtime", "localtime", "ctime", "asctime"}
STAMPS = {("custody", "utc"), ("fetch", "utc"), ("publish", "utc_now")}
FILETIME = {"st_mtime", "st_ctime", "st_atime", "st_birthtime", "st_mtime_ns", "st_ctime_ns", "st_atime_ns",
            "st_birthtime_ns", "getmtime", "getctime", "getatime"}
SKIP = {"home/clock.py"}                                # the clock itself: its wall readings are the C3 check's

# (file, the class, the reason): the server's own programs in run/ files that home imports helpers from
SERVER = [
    ("run/worker.py", "Worker", "the worker itself: it runs on the server, on the server's clock; home takes only "
                                "functions, constants and small classes from this file"),
    ("run/packer.py", "Packer", "the packer itself: it runs on the server, on the server's clock; home takes only "
                                "functions and key lists from this file"),
]

# (file, the line's exact text, the reason); the text is the whole line without its line end
GMT = '    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())'
CUSTODY_READ = "custody's reader of its own records (custody.py, the hashes and at_utc check) asks only that it is a text"
ALLOW = [
    ("home/custody.py", GMT, "custody.utc's own body: the stamp function; its callers are rows of their own"),
    ("home/custody.py", '                "members": ms, "kept": f"wire/out/w{k:03d}", "at_utc": utc()}',
     "a custody record's at_utc, a stamp: " + CUSTODY_READ),
    ("home/custody.py", '                        "found_seal_sha256": seal, "found_offer_sha256": offer, "at_utc": utc(),',
     "a custody record's at_utc, a stamp: " + CUSTODY_READ),
    ("home/deliver.py", '        rec["at_utc"] = F.utc()',
     "deliver's journal line, for people: its one reader in the package (deliver.py probed) reads t, "
     "run_fingerprint and passed only"),
    ("home/drain.py", "            now = utc()                                 # D5: a person's word; the PC's clock, a "
                      "stamp only",
     "D5: a declared stop (a person's word) when the helper gives no time; DRAIN.json's at_utc is checked for its "
     "form only (drain.py's own reader of DRAIN.json, publish.py's)"),
    ("home/fetch.py", GMT, "fetch.utc's own body: the stamp function; its callers are rows of their own"),
    ("home/fetch.py", '        rec["at_utc"] = utc()',
     "fetch's journal line, for people: nothing in the package reads fetch/journal.jsonl"),
    # v17 (26 Nov evening, Neon's catch): home/loop.py came into the package after chain_v17
    ("home/loop.py", '        append(self.f["loop.log"], f"{datetime.now():%Y-%m-%d %H:%M:%S} {printable(msg, 2000)}'
                     '\\n".encode("ascii"))',
     "loop.log's stamp, for people: only loop.py reads loop.log, and only for the words \"probe passed (run <fp>)\" "
     "(R7), never its time"),
    ("home/publish.py", GMT, "publish.utc_now's own body: the stamp function; its callers are rows of their own"),
    ("home/publish.py", '        line = canon({"t": "stage_b_attempt", "round": r, "at_utc": utc_now(), "result": '
                        '"failed", "why": why[:2000]})',
     "the stage_b_attempt line of home/progress.jsonl: its reader (publish.py) counts t, round and result only"),
    ("home/state.py", "def run(home, fp: str, mono=time.monotonic, wall=time.time) -> str:",
     "v17: the one seam a test plants. The wall reading is read once and handed only to clock.reading (state.py's "
     "one use of self.wall), where home/clock.py uses it for the C3 check alone (the PC restarted or its clock was "
     "set); now_s comes from the server's time"),
    ("tools/make_control.py", '    c = {"at_utc": T(int(time.time())), "cutoff_utc": T(cut),',
     "a control's at_utc, a stamp: the server's guard checks only that it is an existing UTC time (guard.py, the "
     "control check d); the bounds come from the header's lease start and the report's floors, not from a clock"),
]

PLANTS = {
    "plant3": ("home/drain.py", "time.time()\n"),
    "plant4": ("home/deliver.py", "from custody import utc as _u4\n_u4()\n"),
    "plant5": ("home/deliver.py", "import time as _t5\n_w5 = _t5.time\n"),
    "plant6": ("home/drain.py", "from time import *\ntime()\n"),
    "plant7": ("home/deliver.py", "import os as _o7\n_m7 = _o7.stat(__file__).st_mtime\n"),
    "plant8": ("run/worker.py", "time.time()\n"),
    "plant9": ("run/packer.py", "class _P9:\n    def f(self):\n        return time.time()\n"),
    "plant10": ("home/fetch.py", "from worker import Worker as _W10\n"),
    "plant11": ("run/worker.py", "class Worker:\n    def f(self):\n        return time.time()\n"),
}

RESULTS = []


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {str(got)[:2000]}" + ("" if ok else f"; want {str(want)[:600]}"),
          flush=True)
    return ok


def names_of(tree: ast.Module, module: str) -> dict:
    """Local name -> a module name (str) or (module, attribute); the file's own top-level defs as (module, name)."""
    names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names[(a.asname or a.name).split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for a in node.names:
                names[a.asname or a.name] = (node.module.split(".")[-1], a.name)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names[node.name] = (module, node.name)
    return names


def base_module(node, names):
    """The module a call's base names: a Name of an imported module, `__import__("x")`, or a class imported from one
    (datetime, date)."""
    if isinstance(node, ast.Name):
        v = names.get(node.id)
        if isinstance(v, str):
            return v
        if isinstance(v, tuple):
            return v[1]                                 # from datetime import datetime: datetime.now -> datetime.now
        return node.id if node.id in ("time", "datetime") else None     # not imported in this file: still the module
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "__import__"
            and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
        return node.args[0].value
    if isinstance(node, ast.Attribute) and base_module(node.value, names) is not None:
        return node.attr                                # datetime.datetime.now -> datetime.now
    return None


def resolve(func, names):
    if isinstance(func, ast.Name):
        v = names.get(func.id)
        return v if isinstance(v, tuple) else None
    if isinstance(func, ast.Attribute):
        m = base_module(func.value, names)
        return (m, func.attr) if m else None
    return None


def kind_of(node, names, called):
    """("wall" | "stamp" | "ref", what) for a node that reads the wall clock or a stamp function, else None."""
    if isinstance(node, ast.Call):
        r = resolve(node.func, names)
        if r is None:
            return None
        nargs = len(node.args) + len(node.keywords)
        if r in WALL or (r[0] == "time" and r[1] in NOARG and nargs == 0) or (r == ("time", "strftime") and nargs == 1):
            return "wall", r
        return ("stamp", r) if r in STAMPS else None
    if isinstance(node, (ast.Attribute, ast.Name)) and isinstance(node.ctx, ast.Load) and id(node) not in called:
        r = resolve(node, names)                        # a wall-clock or stamp function handed on uncalled
        if r is not None and (r in WALL or r in STAMPS):
            return "ref", r
    return None


def imported(tree: ast.Module) -> set:
    """The first name of every module a file imports (absolute imports)."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module.split(".")[0])
    return out


def scan(root: Path):
    """Reads home/, tools/ and the run/ files they import. Returns found (wall, stamp, ref: file, line, kind, what,
    text), stars (file, line, what), filetimes (file, line, name, text), exempt (the same as found, inside a SERVER
    class), run_files, class_counts {(file, class): how often at the top level}, named (file, line, class)."""
    server = {(f, c) for f, c, _ in SERVER}
    server_names = {c for _, c, _ in SERVER}
    home = sorted(list((root / "home").rglob("*.py")) + list((root / "tools").rglob("*.py")))
    trees, mods = {}, set()
    for p in home:
        rel = p.relative_to(root).as_posix()
        src = p.read_text(encoding="utf-8")
        trees[rel] = (p, src, ast.parse(src, filename=rel))
        mods |= imported(trees[rel][2])
    run_files = sorted(f"run/{m}.py" for m in mods if (root / "run" / f"{m}.py").is_file())
    for rel in run_files:
        p = root / rel
        src = p.read_text(encoding="utf-8")
        trees[rel] = (p, src, ast.parse(src, filename=rel))
    found, stars, filetimes, exempt, named = [], [], [], [], []
    class_counts = {key: 0 for key in server}
    for rel, (p, src, tree) in trees.items():
        lines = src.split("\n")

        def text(n):
            return lines[n - 1].rstrip("\r")

        if not rel.startswith("run/"):                  # U8: also in clock.py
            for node in ast.walk(tree):
                hit = None
                if isinstance(node, ast.Name) and node.id in server_names:
                    hit = node.id
                elif isinstance(node, ast.Attribute) and node.attr in server_names:
                    hit = node.attr
                elif isinstance(node, ast.ImportFrom):
                    hit = next((a.name for a in node.names if a.name in server_names), None)
                if hit:
                    named.append((rel, node.lineno, hit))
        if rel in SKIP:
            continue
        inside = set()
        if rel.startswith("run/"):
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and (rel, node.name) in server:
                    class_counts[(rel, node.name)] += 1
                    inside.update(id(n) for n in ast.walk(node))
        names = names_of(tree, p.stem)
        called = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for node in ast.walk(tree):
            if id(node) in inside:
                k = kind_of(node, names, called)
                if k:
                    exempt.append((rel, node.lineno, k[0], ".".join(k[1]), text(node.lineno)))
                continue
            if isinstance(node, ast.ImportFrom):
                if any(a.name == "*" for a in node.names):
                    stars.append((rel, node.lineno, f"from {'.' * node.level}{node.module or ''} import *"))
                for a in node.names:
                    if a.name in FILETIME:
                        filetimes.append((rel, node.lineno, a.name, text(node.lineno)))
            elif isinstance(node, ast.Attribute) and node.attr in FILETIME:
                filetimes.append((rel, node.lineno, node.attr, text(node.lineno)))
            k = kind_of(node, names, called)
            if k:
                found.append((rel, node.lineno, k[0], ".".join(k[1]), text(node.lineno)))
    return found, stars, filetimes, exempt, run_files, class_counts, named


if MODE in PLANTS:
    rel, add = PLANTS[MODE]
    p = WORK / rel
    before = p.read_text(encoding="utf-8")
    p.write_text(before + ("" if before.endswith("\n") else "\n") + add, encoding="utf-8", newline="\n")
    print(f"PLANT {MODE}: appended to the copy's {rel}: {add!r}")

found, stars, filetimes, exempt, run_files, class_counts, named = scan(WORK)
allowed = {(f, t) for f, t, _ in ALLOW}
if MODE == "list":
    for f, n, kind, what, text in found:
        print(f"{'allowed' if (f, text) in allowed else 'NOT LISTED'} {f}:{n} {kind} {what}: {text.strip()}")
    print(f"{len(found)} calls")
    print(f"run files scanned: {run_files}")
    for f, n, kind, what, text in exempt:
        print(f"exempt (a server class) {f}:{n} {kind} {what}: {text.strip()}")
    print(f"{len(exempt)} in server classes")
    for f, n, what in stars:
        print(f"star import {f}:{n} {what}")
    print(f"{len(stars)} star imports")
    for f, n, name, text in filetimes:
        print(f"{'allowed' if (f, text) in allowed else 'NOT LISTED'} file time {f}:{n} {name}: {text.strip()}")
    print(f"{len(filetimes)} file-time names")
    sys.exit(0)
check("U1 every wall-clock call and every stamp-function call in home/, tools/ (but clock.py) and the run/ files "
      "they import (but the server classes) is allow-listed",
      [f"{f}:{n} {what}" for f, n, kind, what, text in found if (f, text) not in allowed], [])
counts = []
for f, t, _ in ALLOW:
    p = WORK / f
    k = p.read_text(encoding="utf-8").split("\n").count(t) if p.exists() else 0
    if k != 1:
        counts.append((f, t.strip()[:60], k))
check("U1b every allow-list row stands exactly once in its file", counts, [])
check("U1c every allow-list row and every server-class row has a reason",
      [(f, t.strip()[:60]) for f, t, why in ALLOW + SERVER if not why.strip()], [])
check("U5 no star import in a scanned file", [f"{f}:{n} {what}" for f, n, what in stars], [])
check("U6 no file-time name (st_mtime, getmtime and the like) outside the allow-list",
      [f"{f}:{n} {name}" for f, n, name, text in filetimes if (f, text) not in allowed], [])
check("U7 each server class stands exactly once at the top level of a scanned run/ file",
      [(f, c, class_counts[(f, c)]) for f, c, _ in SERVER if class_counts[(f, c)] != 1], [])
check("U8 no home/ or tools/ file names a server class", [f"{f}:{n} {c}" for f, n, c in named], [])
leftover = [str(p) for p in WORK.rglob("__pycache__")]
check("no __pycache__ in the copy", leftover, [])
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)

"""test_clock_use.py: no DECISION at home takes the PC's clock (v16; part U of the clock known answers,
tmp/opus_scratch/clock/KNOWN_ANSWERS_clock_by_opus.md on the PC: Fable's guard against a place to forget). Standard
library only; a PLAIN interpreter.

    test_clock_use.py <tree> <a NEW folder> [plant3|plant4|list]

The PC's clock runs about 25,178 s (7 hours) ahead of real UTC. Home's DECISIONS take the server's time (home/clock.py,
server_now and server_text); STAMPS for people stay on the PC's clock, each one allow-listed here with the reader that
checks its form only. The test copies <tree>'s home/ and tools/ into the new folder (a plant changes the copy only)
and reads every .py there with ast. It FAILs on two kinds of call:
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
"""
import ast
import shutil
import sys
from pathlib import Path

if len(sys.argv) < 3:
    print("usage: test_clock_use.py <tree> <a NEW folder> [plant3|plant4|plant5|list]")
    sys.exit(2)
SRC, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
MODE = sys.argv[3] if len(sys.argv) > 3 else None
if MODE not in (None, "plant3", "plant4", "plant5", "list"):
    print(f"STOP: not understood: {MODE}")
    sys.exit(2)
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
for sub in ("home", "tools"):
    shutil.copytree(SRC / sub, WORK / sub, ignore=shutil.ignore_patterns("__pycache__"))

WALL = {("time", "time"), ("time", "time_ns"), ("datetime", "now"), ("datetime", "utcnow"), ("datetime", "today"),
        ("date", "today")}
NOARG = {"gmtime", "localtime", "ctime", "asctime"}
STAMPS = {("custody", "utc"), ("fetch", "utc"), ("publish", "utc_now")}
SKIP = {"home/clock.py"}                                # the clock itself: its wall readings are the C3 check's

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
    ("home/publish.py", GMT, "publish.utc_now's own body: the stamp function; its callers are rows of their own"),
    ("home/publish.py", '        line = canon({"t": "stage_b_attempt", "round": r, "at_utc": utc_now(), "result": '
                        '"failed", "why": why[:2000]})',
     "the stage_b_attempt line of home/progress.jsonl: its reader (publish.py) counts t, round and result only"),
    ("tools/make_control.py", '    c = {"at_utc": T(int(time.time())), "cutoff_utc": T(cut),',
     "a control's at_utc, a stamp: the server's guard checks only that it is an existing UTC time (guard.py, the "
     "control check d); the bounds come from the header's lease start and the report's floors, not from a clock"),
]

PLANTS = {
    "plant3": ("home/drain.py", "time.time()\n"),
    "plant4": ("home/deliver.py", "from custody import utc as _u4\n_u4()\n"),
    "plant5": ("home/deliver.py", "import time as _t5\n_w5 = _t5.time\n"),
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


def calls(root: Path):
    """Every wall-clock or stamp call in home/ and tools/ (but clock.py): (file, line, kind, what, the line's text)."""
    found = []
    for p in sorted(list((root / "home").rglob("*.py")) + list((root / "tools").rglob("*.py"))):
        rel = p.relative_to(root).as_posix()
        if rel in SKIP:
            continue
        src = p.read_text(encoding="utf-8")
        lines = src.split("\n")
        tree = ast.parse(src, filename=rel)
        names = names_of(tree, p.stem)
        called = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                r = resolve(node.func, names)
                if r is None:
                    continue
                nargs = len(node.args) + len(node.keywords)
                if r in WALL or (r[0] == "time" and r[1] in NOARG and nargs == 0) or (r == ("time", "strftime")
                                                                                     and nargs == 1):
                    kind = "wall"
                elif r in STAMPS:
                    kind = "stamp"
                else:
                    continue
            elif (isinstance(node, (ast.Attribute, ast.Name)) and isinstance(node.ctx, ast.Load)
                  and id(node) not in called):
                r = resolve(node, names)                # a wall-clock or stamp function handed on uncalled
                if r is None or not (r in WALL or r in STAMPS):
                    continue
                kind = "ref"
            else:
                continue
            found.append((rel, node.lineno, kind, ".".join(r), lines[node.lineno - 1].rstrip("\r")))
    return found


if MODE in PLANTS:
    rel, add = PLANTS[MODE]
    p = WORK / rel
    p.write_text(p.read_text(encoding="utf-8") + add, encoding="utf-8", newline="\n")
    print(f"PLANT {MODE}: appended to the copy's {rel}: {add!r}")

found = calls(WORK)
if MODE == "list":
    allowed = {(f, t) for f, t, _ in ALLOW}
    for f, n, kind, what, text in found:
        print(f"{'allowed' if (f, text) in allowed else 'NOT LISTED'} {f}:{n} {kind} {what}: {text.strip()}")
    print(f"{len(found)} calls")
    sys.exit(0)
allowed = {(f, t) for f, t, _ in ALLOW}
check("U1 every wall-clock call and every stamp-function call in home/ and tools/ (but clock.py) is allow-listed",
      [f"{f}:{n} {what}" for f, n, kind, what, text in found if (f, text) not in allowed], [])
counts = []
for f, t, _ in ALLOW:
    p = WORK / f
    k = p.read_text(encoding="utf-8").split("\n").count(t) if p.exists() else 0
    if k != 1:
        counts.append((f, t.strip()[:60], k))
check("U1b every allow-list row stands exactly once in its file", counts, [])
check("U1c every allow-list row has a reason", [(f, t.strip()[:60]) for f, t, why in ALLOW if not why.strip()], [])
leftover = [str(p) for p in WORK.rglob("__pycache__")]
check("no __pycache__ in the copy", leftover, [])
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)

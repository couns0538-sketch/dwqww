"""Opus 2026-11-23: the test of run/packer.py version 2 (FORMATS 2.2 sections 0, 0.1, 1.5, 1.6 and 1.8.4, with the 2.3
points of Fable's 13:5x message: the offer's wire copy LAST, the wire copies of the other files), on pieces made by the
tree's own worker (the real engine, N12's six openings, one game a piece) and the official converter. Standard
library only.

    test_packer.py <engine exe> <net file> <converter exe> <tree> <NEW work folder> [only=K1,K2,...]

<tree> holds run/ (packer.py, worker.py, record.py, uciproc.py, engine_lines.py), workloads/ and known/. Run it with
a PLAIN interpreter, not a venv launcher: the packer runs a .py stand-in converter with its own interpreter, and on
Windows a timeout kills that one process only. One engine for the fixture (about 30 s), then one converter at a time.

THE FIXTURE R6: the worker, slot 0, run "pk", piece_games 1, counters 1 to 6: six pieces p000000 to p000005 with 86,
101, 0, 127, 81 and 67 rows (N12's games, known/n12_batch.json), the range seal r0001.w000, the journal ended
"ranges done". Every case works on a copy of it.

Known answers, written before the first run:
 K1  the official converter, --once: exit 0 "offered 5 pieces as binpack and 1 as raw"; p000002 (no rows) raw, the
     other five binpack; every offer canonical with exactly the keys of 1.6, schema 2, the run's fingerprint, slot 0,
     its index and its seal's sha256, and its wire copy offer.json.zz gives it back; the members by form (seal.json
     none + binpack none + meta.xz lzma, or seal.json none + raw.zz zlib), seven keys each, wire_name seal.json.zz
     for the seal and the member's own name for the others; every wire file has the bytes and sha256 named and
     decodes to the member named; the seal member is the seal; binpack: the official converter gives every row back
     (all five fields, against the six-line text made here) and rebuild(meta, rows) is the piece; raw: raw.zz is the
     piece; RUN.json.zz, SCHEDULE.1.json.zz and ranges/r0001.w000.seal.json.zz give their files back (2.3); out/w000
     holds exactly the offers, their wire copies and the members' files; no index file, no temporary file; w000 byte
     for byte as before (D2); no mode file; the scratch folder empty.
 K2  no converter (a path that is not there), --once: exit 0, all six raw; the attempts counted 1, 2, 3 at p000000,
     p000001 and p000003 (p000002 has no rows and is not counted); one mode line, `fallback` at w000/p000003, naming
     the missing converter; p000004 and p000005 raw at once (fallback mode).
 K3  a converter that never answers, --convert-seconds 3, --once: exit 0, all six raw, `fallback` at w000/p000003
     naming "no end within 3 s"; the run takes at least 9 s and less than 30 s; the stand-in was started three times
     and none of them is alive after the packer's end.
 K4  the fallback survives a restart and a probe brings `normal` back: pieces 4 and 5 held back, no converter ->
     fallback at p000003; pieces 4 and 5 back, the official converter, --probe-every 0: exit 0 "offered 0 pieces as
     binpack and 2 as raw" (fallback at the start); the mode lines are fallback (p000003), normal (p000005, "a probe
     passed"); the probe wrote in out/scratch only: no binpack or meta.xz of p000004/5 in out/w000, scratch empty.
 K5  case 12: a converter that gives ONE result back changed (the first `result` line of every text it writes):
     every piece with rows travels raw and the log names p000000's changed result line; and the premise: the
     morning's proof (rebuild alone) accepts the changed text (rebuild(meta, changed) is the piece).
 K6  Neon N7, an empty seal p000002.seal.json: exit 3 naming "p000002.seal.json is empty"; p000000 and p000001
     offered, nothing of p000002 to p000005 in out/w000.
 K7  one digit of a row of p000001.raw changed: exit 3 naming "w000/p000001: the piece's bytes are not the sealed
     ones"; p000000 offered, nothing of p000001.
 K8  one digit of a score in p000000.raw changed and its seal made to fit (raw_sha256, raw_bytes): exit 3 naming
     w000/p000000 and the binding; nothing offered.
 K9  out/w000/p000000.meta.xz there with other bytes: exit 4 naming "p000000.meta.xz exists with other bytes"; the old
     bytes stay, the new as p000000.meta.xz.conflict.<12 hex> (lzma of the meta text); no offer file of p000000.
 K10 a restart after a crash, on a copy of K1's result: p000000.offer.json.zz removed (the crash between the offer and
     its wire copy) and p000001's two offer files removed: exit 0 "offered 2 pieces as binpack and 0 as raw"; out/w000
     byte for byte K1's (the converter, lzma and zlib give the same bytes again; no conflict file).
 K11 FENCE.json missing: three seconds after the last offer the packer still runs; FENCE.json written: exit 0 within
     10 s, and FENCE.json.zz gives it back. K12, meanwhile: a second packer on the same root: exit 3 naming the lock.
 K13 FENCE.json there but the slot's `ended` line cut off: still running three seconds after the last offer;
     STOP_PACKER: exit 0 within 10 s.
 K14 p000002's seal and piece moved away: exit 3 naming "p000002.seal.json is missing while 3 later seals are there";
     p000000 and p000001 offered.
 K15 PACKER_MODE.jsonl = one fallback line + an unfinished line of 8 bytes: the official converter, --probe-every 0:
     exit 0, all six raw (fallback at the start), packer.log names the 8 bytes dropped, the file afterwards is the old
     line + one `normal` line.
 K16 wrong calls: --convert-seconds 0 -> exit 2 naming --convert-seconds, no out/ made; a root without RUN.json ->
     exit 2 naming RUN.json.
B1 to B3 (Fable's read of c8e47afa89af, 14:43, his wanted cases 14:56; Neon 153530Z). Known answers written before
the first run:
 K17 B1, on a copy of K1's result: p000000.offer.json.zz removed (a stop between the offer and its wire copy; K1 made
     p000000 binpack), restarted with NO converter, --once: exit 0 "offered 1 pieces as binpack and 0 as raw" (the
     form not decided again); out/w000 byte for byte K1's (no raw.zz, no conflict file); the log names p000000
     finished from the files on disk. The packer before: raw, then "exists with other bytes", exit 4.
 K18 B1 the other way: pieces 2 to 5 held back, no converter: p000000 and p000001 raw (two failed attempts, no mode
     file: a raw offer made in fallback mode would be made raw again by either packer, so that could not tell);
     then p000000.offer.json.zz removed and the official converter, --once: exit 0 "offered 0 pieces as binpack and
     1 as raw"; out/w000 byte for byte the first run's (no binpack or meta.xz of p000000).
 K19 B1's refusals (Neon), each on a copy of K1's result with p000000.offer.json.zz removed, no converter, --once:
     (a) the offer file rewritten not canonical (spaces after the separators), (b) canonical but naming another
     seal sha256, (c) p000000.binpack removed: exit 4 naming "w000/p000000: p000000.offer.json is there without its
     wire copy", with (a) "not in canonical form", (b) "it is not this piece's offer", (c) "the member
     p000000.binpack"; out/w000 unchanged byte for byte (no wire copy, no raw.zz, no conflict file).
 K20 a member of the other form left by a stop before any offer existed (Fable: neither a stop nor offered; left and
     named): (a) K1's result with both offer files of p000000 removed (its binpack and meta.xz stay), no converter,
     --once: exit 0 "offered 0 pieces as binpack and 1 as raw", p000000's offer raw, its binpack and meta.xz unchanged
     and each named in the log "is left as it is: no offer names it"; (b) K18's first run with both offer files of
     p000000 removed (its raw.zz stays), the official converter, --once: exit 0 "offered 1 pieces as binpack and 0
     as raw", the offer binpack, the raw.zz unchanged and named the same way.
 K21 B2: a stand-in converter (the official one; while it converts p000000 it first puts a FILE where p000001's
     scratch folder goes), --once: exit 0 "offered 4 pieces as binpack and 2 as raw"; p000001 raw and the log names
     its failed attempt (1 in a row) with that folder; no mode file. The packer before: exit 4 (FileExistsError).
 K22 B3, names outside the worker's grammar: (a) SCHEDULE.0.json, SCHEDULE.01.json, SCHEDULE.<Arabic-Indic one>.json,
     RESUME.0.json, RESUME.0001.json in the root and ranges/r<four Arabic-Indic digits>.w000.seal.json, the official
     converter, --once: exit 0 "offered 5 pieces as binpack and 1 as raw"; none of them has a wire copy, RUN.json,
     SCHEDULE.1.json and r0001.w000.seal.json have theirs; (b) w000/closed/p<six Arabic-Indic digits: 7>.seal.json:
     exit 0 "offered 5 pieces as binpack and 1 as raw" (not a seal of the grammar; the packer before: exit 3, a
     seal "missing while 1 later seals are there").
"""
import hashlib
import json
import lzma
import os
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path

if len(sys.argv) < 6:
    print(__doc__)
    sys.exit(2)
EXE, NET, CONV, TREE, WORK = (Path(x).resolve() for x in sys.argv[1:6])
ONLY = set()
for extra in sys.argv[6:]:
    if not extra.startswith("only="):
        print(f"STOP: not understood: {extra}")
        sys.exit(2)
    ONLY |= set(extra[5:].split(","))
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW work folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
sys.path.insert(0, str(TREE / "run"))
import record  # noqa: E402   the reader's side of the record, from the tree under test
import worker as W  # noqa: E402   its boot id, for the fixture's header
try:
    import packer as P  # noqa: E402   rebuild and meta_of: home's side of the proof
except Exception as e:  # noqa: BLE001
    print(f"(the tree's packer does not import: {type(e).__name__}: {e})")
    P = None

MEMBER_KEYS = sorted(["name", "codec", "bytes", "sha256", "wire_name", "wire_bytes", "wire_sha256"])
OFFER_KEYS = sorted(["schema", "run_fingerprint", "slot", "index", "seal_sha256", "form", "members"])
results = []


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canon(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def check(name, ok, detail="") -> bool:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:300]}" if detail != "" and not ok else ""), flush=True)
    return bool(ok)


def want(*cases) -> bool:
    return not ONLY or bool(ONLY & set(cases))


def T(t: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def put(path: Path, data: bytes) -> None:
    part = path.with_name(path.name + ".part")
    part.write_bytes(data)
    os.replace(part, path)


def unz(data: bytes):
    try:
        return zlib.decompress(data)
    except zlib.error:
        return None


def tree_bytes(folder: Path) -> dict:
    return {str(f.relative_to(folder)): f.read_bytes() for f in sorted(folder.rglob("*")) if f.is_file()}


def six_lines(games) -> str:
    """The loop's six-line text of the rows, written here from the record's own fields (not the packer's code)."""
    out = []
    for g in games:
        for r in g["rows"]:
            _, ply, score, move, fen = r.split(" ", 4)
            res = int(g["end"].split()[2])
            out.append(f"fen {fen}\nmove {move}\nscore {score}\nply {ply}\n"
                       f"result {res if fen.split(' ')[1] == 'w' else -res}\ne\n")
    return "".join(out)


def run_conv(cmd, src: Path, dst: Path) -> bool:
    p = subprocess.run(cmd, input=f"convert {src.name} {dst.name}\nquit\n", capture_output=True, text=True,
                       cwd=str(dst.parent), timeout=300)
    return p.returncode == 0 and dst.is_file() and dst.stat().st_size > 0


def alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        k.OpenProcess.restype = ctypes.c_void_p
        h = k.OpenProcess(0x100000 | 0x1000, False, pid)
        if not h:
            return False
        try:
            return k.WaitForSingleObject(ctypes.c_void_p(h), 0) == 258
        finally:
            k.CloseHandle(ctypes.c_void_p(h))
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# ================================================================ the fixture R6, made by the tree's own worker
MAN_PATH, KNOWN = TREE / "workloads" / "MANIFEST.json", TREE / "known" / "startup.json"
MAN = json.loads(MAN_PATH.read_bytes())
N12 = [ln.split()[3:] for ln in (TREE / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
OPENINGS = WORK / "n12_openings.txt"
OPENINGS.write_bytes("".join(" ".join(o) + "\n" for o in N12).encode("ascii"))
R6 = WORK / "r6"
R6.mkdir()
NOW = time.time()
ROWS6 = [{"slot": 0, "round": 1, "first": 1, "last": 6, "short": False, "schedule": 0}]
put(R6 / "RUN.json", canon({
    "schema": 2, "run": "pk", "lease_start_utc": T(NOW - 3600), "lease_end_utc": T(NOW + 86400),
    "hard_cutoff_utc": T(NOW + 86400), "boot_id": W.boot_id(), "instance": "test-instance", "package": "0" * 64,
    "engine_sha256": sha(EXE.read_bytes()), "net_sha256": MAN["net_sha256"],
    "options_sha256": sha("".join(ln + "\n" for ln in MAN["options"]).encode("ascii")),
    "game_line": MAN["selfgame_line"],
    "opening_rule": {"kind": "list", "sha256": sha(OPENINGS.read_bytes()), "count": len(N12)},
    "slots": [0], "piece_games": 1, "pilot_ranges": ROWS6}))
FP = sha((R6 / "RUN.json").read_bytes())
put(R6 / "SCHEDULE.1.json", canon({
    "schema": 2, "run_fingerprint": FP, "n": 1, "prev": "first", "evidence": "0" * 64,
    "cutoff_utc": T(NOW + 45), "dispatch_end_utc": T(NOW + 30), "ranges": ROWS6}))
fx = subprocess.run([sys.executable, "-I", "-B", str(TREE / "run" / "worker.py"), "--root", str(R6), "--slot", "0",
                     "--exe", str(EXE), "--net", str(NET), "--manifest", str(MAN_PATH), "--known-startup", str(KNOWN),
                     "--openings", str(OPENINGS)], capture_output=True, text=True, timeout=600)
CLOSED = R6 / "w000" / "closed"
ROWS = [sum(len(g["rows"]) for g in record.parse((CLOSED / f"p{i:06d}.raw").read_bytes(), FP))
        if (CLOSED / f"p{i:06d}.raw").is_file() else None for i in range(6)]
JOURNAL = (R6 / "w000" / "journal.txt").read_bytes() if (R6 / "w000" / "journal.txt").is_file() else b""
if not check("fixture: the worker made six pieces with 86, 101, 0, 127, 81, 67 rows, a range seal, and ended",
             fx.returncode == 0 and ROWS == [86, 101, 0, 127, 81, 67] and b'"t":"ended"' in JOURNAL.splitlines()[-1:][0]
             and (R6 / "ranges" / "r0001.w000.seal.json").is_file(), (fx.returncode, ROWS, fx.stdout[-300:])):
    print("STOP: no fixture, no case can run")
    sys.exit(1)
W000 = tree_bytes(R6 / "w000")


def copy(name: str) -> Path:
    dst = WORK / name
    shutil.copytree(R6, dst)
    return dst


def packer_cmd(root, conv, *extra):
    return [sys.executable, "-I", "-B", str(TREE / "run" / "packer.py"), "--root", str(root), "--converter", str(conv),
            *extra]


def run_packer(root, conv, *extra):
    t0 = time.time()
    p = subprocess.run(packer_cmd(root, conv, *extra), capture_output=True, text=True, timeout=300)
    return p.returncode, (p.stdout + p.stderr).strip(), time.time() - t0


def end_of(p, secs=10.0):
    try:
        out, _ = p.communicate(timeout=secs)
        return p.returncode, (out or "").strip()
    except subprocess.TimeoutExpired:
        p.kill()
        out, _ = p.communicate()
        return -999, (out or "").strip() + "\n(killed by the test: no end in time)"


def common(name, rc, out, rc_want, text=""):
    check(f"{name} no traceback", "Traceback" not in out, out[-300:])
    return check(f"{name} exit {rc_want}" + (f" naming `{text}`" if text else ""), rc == rc_want and text in out, out[-400:])


def offer(root, i):
    try:
        return json.loads((root / "out" / "w000" / f"p{i:06d}.offer.json").read_bytes())
    except (OSError, ValueError):
        return None


def forms(root):
    return [(offer(root, i) or {}).get("form") for i in range(6)]


def offered(root):
    return [i for i in range(6) if (root / "out" / "w000" / f"p{i:06d}.offer.json.zz").is_file()]


def names_of(root, i):
    d = root / "out" / "w000"
    return sorted(f.name for f in d.glob(f"p{i:06d}.*")) if d.is_dir() else []


def mode_lines(root):
    f = root / "out" / "PACKER_MODE.jsonl"
    out = []
    for ln in (f.read_bytes().decode("ascii", "replace").splitlines() if f.is_file() else []):
        try:
            out.append(json.loads(ln))
        except ValueError:
            out.append({"raw": ln})
    return out


def logtext(root) -> str:
    f = root / "out" / "packer.log"
    return f.read_text(encoding="ascii", errors="replace") if f.is_file() else ""


def wait_offers(root, p, n=6, secs=120.0):
    t_end = time.time() + secs
    while time.time() < t_end and len(offered(root)) < n and p.poll() is None:
        time.sleep(0.2)


NO_CONV = WORK / "no_such_converter.exe"
FENCE = lambda: canon({"run_fingerprint": FP, "at_utc": T(time.time()), "cutoff_utc": T(time.time()), "why": "a test"})  # noqa: E731

# ================================================================ K1 and K10
K1 = None
if want("K1", "K10", "K17", "K19", "K20"):
    K1 = copy("k1")
    rc, out, _ = run_packer(K1, CONV, "--once")
    common("K1", rc, out, 0, "offered 5 pieces as binpack and 1 as raw")
    d = K1 / "out" / "w000"
    ok_offer = ok_members = ok_wire = ok_seal = ok_content = True
    expect = set()
    for i in range(6):
        name = f"p{i:06d}"
        of = d / f"{name}.offer.json"
        ob = of.read_bytes() if of.is_file() else b""
        o = offer(K1, i) or {}
        sb = (CLOSED / f"{name}.seal.json").read_bytes()
        ozz = d / f"{name}.offer.json.zz"
        ok_offer &= (bool(ob) and ob == canon(o) and sorted(o) == OFFER_KEYS and o.get("schema") == 2
                     and o.get("run_fingerprint") == FP and o.get("slot") == 0 and o.get("index") == i
                     and o.get("seal_sha256") == sha(sb) and ozz.is_file() and unz(ozz.read_bytes()) == ob)
        form = o.get("form")
        want_m = ([(f"{name}.seal.json", "none"), (f"{name}.binpack", "none"), (f"{name}.meta.xz", "lzma")]
                  if form == "binpack" else [(f"{name}.seal.json", "none"), (f"{name}.raw.zz", "zlib")])
        ms = o.get("members") or []
        ok_members &= (bool(ms) and [(m.get("name"), m.get("codec")) for m in ms] == want_m
                       and all(sorted(m) == MEMBER_KEYS for m in ms) and ms[0].get("wire_name") == f"{name}.seal.json.zz"
                       and all(m.get("wire_name") == m.get("name") for m in ms[1:]))
        files = {}
        for m in ms:
            wf = d / str(m.get("wire_name"))
            wb = wf.read_bytes() if wf.is_file() else b""
            mb = unz(wb) if m.get("wire_name") != m.get("name") else wb
            ok_wire &= (len(wb) == m.get("wire_bytes") and sha(wb) == m.get("wire_sha256") and mb is not None
                        and len(mb) == m.get("bytes") and sha(mb) == m.get("sha256"))
            files[m.get("name")] = mb
            expect.add(str(m.get("wire_name")))
        expect |= {f"{name}.offer.json", f"{name}.offer.json.zz"}
        ok_seal &= files.get(f"{name}.seal.json") == sb
        raw = (CLOSED / f"{name}.raw").read_bytes()
        games = record.parse(raw, FP)
        try:
            if form == "raw":
                ok_content &= unz(files.get(f"{name}.raw.zz") or b"") == raw
            elif form == "binpack":
                meta = lzma.decompress(files[f"{name}.meta.xz"]).decode("ascii")
                cd = WORK / "k1_check" / name
                cd.mkdir(parents=True)
                (cd / "p.binpack").write_bytes(files[f"{name}.binpack"])
                back = ((cd / "p.plain").read_bytes().decode("ascii").replace("\r\n", "\n")
                        if run_conv([str(CONV)], cd / "p.binpack", cd / "p.plain") else "")
                ok_content &= back == six_lines(games) and P is not None and P.rebuild(meta, back) == raw
            else:
                ok_content = False
        except Exception as e:  # noqa: BLE001
            print(f"(K1 {name}: {type(e).__name__}: {e})")
            ok_content = False
    check("K1 the forms: p000002 (no rows) raw, the other five binpack", forms(K1) == ["binpack"] * 2 + ["raw"] + ["binpack"] * 3,
          forms(K1))
    check("K1 every offer canonical with the keys of 1.6, its run, slot, index and seal's sha256; offer.json.zz gives it back",
          ok_offer)
    check("K1 the members by form, seven keys each, codecs and wire names (1.6)", ok_members)
    check("K1 every wire file has the bytes and sha256 named and decodes to the member named", ok_wire)
    check("K1 the seal member is the seal byte for byte", ok_seal)
    check("K1 binpack: the official converter gives every row back (all five fields) and rebuild(meta, rows) is the "
          "piece; raw: raw.zz is the piece", ok_content)
    wired = [K1 / "RUN.json", K1 / "SCHEDULE.1.json", K1 / "ranges" / "r0001.w000.seal.json"]
    check("K1 RUN.json.zz, SCHEDULE.1.json.zz and ranges/r0001.w000.seal.json.zz give their files back (2.3)",
          all(f.with_name(f.name + ".zz").is_file() and unz(f.with_name(f.name + ".zz").read_bytes()) == f.read_bytes()
              for f in wired))
    check("K1 out/w000 holds exactly the offers, their wire copies and the members' files; no index file, no temporary file",
          d.is_dir() and sorted(f.name for f in d.iterdir()) == sorted(expect)
          and not [f for f in K1.rglob("*") if f.name.startswith("PIECES") or f.name.endswith((".tmp", ".part"))],
          sorted(set(f.name for f in d.iterdir()) ^ expect) if d.is_dir() else "no out/w000")
    check("K1 nothing sealed changed or removed (D2): w000 byte for byte as before", tree_bytes(K1 / "w000") == W000)
    sc = K1 / "out" / "scratch"
    check("K1 no mode file (no failure), the scratch folder empty",
          not (K1 / "out" / "PACKER_MODE.jsonl").exists() and not (sc.is_dir() and any(sc.iterdir())))

# ================================================================ K2: no converter
if want("K2"):
    K2 = copy("k2")
    rc, out, _ = run_packer(K2, NO_CONV, "--once")
    common("K2", rc, out, 0, "offered 0 pieces as binpack and 6 as raw")
    check("K2 all six raw", forms(K2) == ["raw"] * 6, forms(K2))
    log = logtext(K2)
    check("K2 the attempts counted 1, 2, 3 at p000000, p000001, p000003; p000002 (no rows) not counted; p000004/5 raw at once",
          all(s in log for s in ("w000/p000000: the converter's attempt failed (1 in a row)",
                                 "w000/p000001: the converter's attempt failed (2 in a row)",
                                 "w000/p000003: the converter's attempt failed (3 in a row)",
                                 "w000/p000002: offered as raw (no rows)", "w000/p000004: offered as raw (fallback mode)",
                                 "w000/p000005: offered as raw (fallback mode)")) and "(4 in a row)" not in log, log[-600:])
    ml = mode_lines(K2)
    check("K2 one mode line: fallback at w000/p000003, naming the missing converter",
          [(r.get("t"), r.get("mode"), r.get("piece")) for r in ml] == [("mode", "fallback", "w000/p000003")]
          and "missing" in ml[0].get("why", ""), ml)

# ================================================================ K3: a converter that never answers
if want("K3"):
    pid_file = WORK / "hang_pids.txt"
    hang = WORK / "hang_converter.py"
    hang.write_text(f"import os, time\nwith open({pid_file.as_posix()!r}, 'a') as f:\n    f.write(str(os.getpid()) + chr(10))\n"
                    f"time.sleep(600)\n", encoding="ascii")
    K3 = copy("k3")
    rc, out, secs = run_packer(K3, hang, "--once", "--convert-seconds", "3")
    common("K3", rc, out, 0, "offered 0 pieces as binpack and 6 as raw")
    ml = mode_lines(K3)
    check("K3 fallback at w000/p000003, naming `no end within 3 s`",
          [(r.get("mode"), r.get("piece")) for r in ml] == [("fallback", "w000/p000003")]
          and "no end within 3 s" in ml[0].get("why", ""), ml)
    check("K3 three attempts of 3 s each: at least 9 s and less than 30 s", 9 <= secs < 30, f"{secs:.1f} s")
    pids = [int(x) for x in pid_file.read_text(encoding="ascii").split()] if pid_file.is_file() else []
    t_end = time.time() + 10
    while time.time() < t_end and any(alive(p) for p in pids):
        time.sleep(0.5)
    check("K3 the stand-in was started three times and none of them is alive after the packer's end",
          len(pids) == 3 and not any(alive(p) for p in pids), pids)

# ================================================================ K4: the fallback survives a restart; a probe
if want("K4"):
    K4 = copy("k4")
    held = WORK / "k4_held"
    held.mkdir()
    for i in (4, 5):
        for ext in ("raw", "seal.json"):
            os.replace(K4 / "w000" / "closed" / f"p{i:06d}.{ext}", held / f"p{i:06d}.{ext}")
    rc1, out1, _ = run_packer(K4, NO_CONV, "--once")
    ml1 = mode_lines(K4)
    check("K4 the first run (no converter, pieces 0 to 3): exit 0, fallback at w000/p000003",
          rc1 == 0 and [(r.get("mode"), r.get("piece")) for r in ml1] == [("fallback", "w000/p000003")], (rc1, out1[-200:], ml1))
    for f in sorted(held.iterdir()):
        os.replace(f, K4 / "w000" / "closed" / f.name)
    rc, out, _ = run_packer(K4, CONV, "--once", "--probe-every", "0")
    common("K4", rc, out, 0, "offered 0 pieces as binpack and 2 as raw")
    log = logtext(K4)
    check("K4 the fallback survived the restart: p000004 and p000005 raw at once (fallback mode)",
          "w000/p000004: offered as raw (fallback mode)" in log and "w000/p000005: offered as raw (fallback mode)" in log,
          log[-400:])
    ml = mode_lines(K4)
    check("K4 the probe brought normal back: fallback (p000003), then normal (p000005, `a probe passed`)",
          [(r.get("mode"), r.get("piece")) for r in ml] == [("fallback", "w000/p000003"), ("normal", "w000/p000005")]
          and ml[1].get("why") == "a probe passed", ml)
    sc = K4 / "out" / "scratch"
    check("K4 the probe wrote in out/scratch only: no binpack or meta.xz of p000004/5 in out/w000, scratch empty",
          not [n for i in (4, 5) for n in names_of(K4, i) if n.endswith((".binpack", ".meta.xz"))]
          and not (sc.is_dir() and any(sc.iterdir())), [names_of(K4, i) for i in (4, 5)])

# ================================================================ K5: case 12, one result changed on the way back
if want("K5"):
    flip = WORK / "flip_converter.py"
    flip.write_text(f"""import subprocess, sys
text = sys.stdin.read()
p = subprocess.run([{CONV.as_posix()!r}], input=text, capture_output=True, text=True)
sys.stdout.write(p.stdout + p.stderr)
words = text.split()
if p.returncode == 0 and len(words) >= 3 and words[0] == "convert" and words[2].endswith(".plain"):
    data = open(words[2], "rb").read()
    i = data.index(b"result ")
    value = data[i + 7:data.index(b"\\n", i)].rstrip(b"\\r")
    data = data[:i + 7] + (b"-1" if value == b"1" else b"1") + data[i + 7 + len(value):]
    open(words[2], "wb").write(data)
sys.exit(p.returncode)
""", encoding="ascii")
    K5 = copy("k5")
    rc, out, _ = run_packer(K5, flip, "--once")
    common("K5", rc, out, 0, "offered 0 pieces as binpack and 6 as raw")
    line = next((ln for ln in logtext(K5).splitlines() if "w000/p000000: the converter's attempt failed" in ln), "")
    check("K5 p000000 travels raw: the log names its changed result line",
          "came back changed" in line and "result" in line.split("came back changed", 1)[-1], line)
    cd = WORK / "k5_premise"
    cd.mkdir()
    raw0 = (CLOSED / "p000000.raw").read_bytes()
    g0 = record.parse(raw0, FP)
    (cd / "p.plain").write_bytes(six_lines(g0).encode("ascii"))
    fcmd = [sys.executable, "-I", "-B", str(flip)]
    ok = run_conv(fcmd, cd / "p.plain", cd / "p.binpack") and run_conv(fcmd, cd / "p.binpack", cd / "q.plain")
    changed = (cd / "q.plain").read_bytes().decode("ascii").replace("\r\n", "\n") if ok else ""
    try:
        premise = ok and changed != six_lines(g0) and P is not None and P.rebuild(P.meta_of(g0), changed) == raw0
    except Exception as e:  # noqa: BLE001
        premise = False
        print(f"(K5 premise: {type(e).__name__}: {e})")
    check("K5 the premise: one result came back changed, and rebuild alone (the morning's proof) still gives the piece",
          premise)

# ================================================================ K6 to K9: pieces and files that cannot be trusted
if want("K6"):
    K6 = copy("k6")
    (K6 / "w000" / "closed" / "p000002.seal.json").write_bytes(b"")
    rc, out, _ = run_packer(K6, CONV, "--once")
    common("K6", rc, out, 3, "p000002.seal.json is empty")
    check("K6 p000000 and p000001 offered, nothing of p000002 to p000005 in out/w000",
          offered(K6) == [0, 1] and not any(names_of(K6, i) for i in range(2, 6)), offered(K6))
if want("K7"):
    K7 = copy("k7")
    pf = K7 / "w000" / "closed" / "p000001.raw"
    data = bytearray(pf.read_bytes())
    k = data.index(b"\nsg ") + 4                             # the first digit of the first row's ply
    data[k] = ord("1") if data[k] != ord("1") else ord("2")
    pf.write_bytes(bytes(data))
    rc, out, _ = run_packer(K7, CONV, "--once")
    common("K7", rc, out, 3, "w000/p000001: the piece's bytes are not the sealed ones")
    check("K7 p000000 offered, nothing of p000001", offered(K7) == [0] and not names_of(K7, 1), offered(K7))
if want("K8"):
    K8 = copy("k8")
    pf = K8 / "w000" / "closed" / "p000000.raw"
    data = pf.read_bytes()
    k = data.index(b"\nsg ") + 1
    e = data.index(b"\n", k)
    parts = data[k:e].decode("ascii").split(" ", 4)
    parts[2] = parts[2][:-1] + ("1" if parts[2][-1] != "1" else "2")
    data = data[:k] + " ".join(parts).encode("ascii") + data[e:]
    pf.write_bytes(data)
    sp = K8 / "w000" / "closed" / "p000000.seal.json"
    s = json.loads(sp.read_bytes())
    s["raw_sha256"], s["raw_bytes"] = sha(data), len(data)
    sp.write_bytes(canon(s))
    rc, out, _ = run_packer(K8, CONV, "--once")
    common("K8", rc, out, 3, "w000/p000000: ")
    check("K8 the stop names the binding; nothing offered", "bind" in out and offered(K8) == [] and not names_of(K8, 0),
          out[-300:])
if want("K9"):
    K9 = copy("k9")
    d = K9 / "out" / "w000"
    d.mkdir(parents=True)
    (d / "p000000.meta.xz").write_bytes(b"other bytes")
    rc, out, _ = run_packer(K9, CONV, "--once")
    common("K9", rc, out, 4, "p000000.meta.xz exists with other bytes")
    conf = list(d.glob("p000000.meta.xz.conflict.*"))
    try:
        meta0 = lzma.decompress(conf[0].read_bytes()) if len(conf) == 1 else b""
    except lzma.LZMAError:
        meta0 = b""
    check("K9 both kept: the old bytes stay, the new as p000000.meta.xz.conflict.<12 hex> (the meta text); no offer file",
          (d / "p000000.meta.xz").read_bytes() == b"other bytes" and len(conf) == 1
          and meta0.startswith(b"game pk-w000-g00000001 opening ")
          and not (d / "p000000.offer.json").exists() and not (d / "p000000.offer.json.zz").exists(), [c.name for c in conf])

# ================================================================ K10: a restart after a crash, on K1's result
if want("K10") and K1 is not None:
    K10 = WORK / "k10"
    shutil.copytree(K1, K10)
    before = tree_bytes(K1 / "out" / "w000")
    d = K10 / "out" / "w000"
    for n in ("p000000.offer.json.zz", "p000001.offer.json", "p000001.offer.json.zz"):
        (d / n).unlink()
    rc, out, _ = run_packer(K10, CONV, "--once")
    common("K10", rc, out, 0, "offered 2 pieces as binpack and 0 as raw")
    after = tree_bytes(d)
    check("K10 out/w000 is K1's byte for byte again (the same bytes from the converter, lzma and zlib; no conflict file)",
          after == before, sorted(set(after) ^ set(before)) or [n for n in after if after[n] != before.get(n)])

# ================================================================ K11 to K13: when the packer ends; the lock
if want("K11", "K12"):
    K11 = copy("k11")
    p = subprocess.Popen(packer_cmd(K11, CONV, "--poll", "0.5"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    wait_offers(K11, p)
    time.sleep(3)
    still = p.poll() is None
    rc2, out2, _ = run_packer(K11, CONV, "--once")
    common("K12", rc2, out2, 3, "lock")
    put(K11 / "FENCE.json", FENCE())
    rc, out = end_of(p)
    check("K11 without FENCE.json the packer does not end: three seconds after the last offer it still runs", still)
    common("K11", rc, out, 0, "offered 5 pieces as binpack and 1 as raw")
    fz = K11 / "FENCE.json.zz"
    check("K11 FENCE.json.zz gives FENCE.json back", fz.is_file() and unz(fz.read_bytes()) == (K11 / "FENCE.json").read_bytes())
if want("K13"):
    K13 = copy("k13")
    jf = K13 / "w000" / "journal.txt"
    lines = jf.read_bytes().split(b"\n")[:-1]
    jf.write_bytes(b"".join(ln + b"\n" for ln in lines[:-1]))   # the ended line cut off
    put(K13 / "FENCE.json", FENCE())
    p = subprocess.Popen(packer_cmd(K13, CONV, "--poll", "0.5"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    wait_offers(K13, p)
    time.sleep(3)
    still = p.poll() is None
    put(K13 / "STOP_PACKER", b"")
    rc, out = end_of(p)
    check("K13 FENCE.json there but the slot without its ended line: still running three seconds after the last offer",
          still)
    common("K13", rc, out, 0, "offered 5 pieces as binpack and 1 as raw")

# ================================================================ K14 to K16
if want("K14"):
    K14 = copy("k14")
    held = WORK / "k14_held"
    held.mkdir()
    for ext in ("raw", "seal.json"):
        os.replace(K14 / "w000" / "closed" / f"p000002.{ext}", held / f"p000002.{ext}")
    rc, out, _ = run_packer(K14, CONV, "--once")
    common("K14", rc, out, 3, "p000002.seal.json is missing while 3 later seals are there")
    check("K14 p000000 and p000001 offered", offered(K14) == [0, 1], offered(K14))
if want("K15"):
    K15 = copy("k15")
    (K15 / "out").mkdir()
    old = canon({"t": "mode", "mode": "fallback", "at_utc": "2026-11-23T00:00:00Z", "why": "a test", "piece": "w000/p000000"})
    (K15 / "out" / "PACKER_MODE.jsonl").write_bytes(old + b'{"t":"mo')
    rc, out, _ = run_packer(K15, CONV, "--once", "--probe-every", "0")
    common("K15", rc, out, 0, "offered 0 pieces as binpack and 6 as raw")
    data = (K15 / "out" / "PACKER_MODE.jsonl").read_bytes()
    rest = data[len(old):] if data.startswith(old) else b""
    try:
        last = json.loads(rest) if rest.count(b"\n") == 1 and rest.endswith(b"\n") else {}
    except ValueError:
        last = {}
    check("K15 the 8 unfinished bytes dropped (packer.log names them), the file is the old line + one `normal` line",
          last.get("mode") == "normal" and "an unfinished last line of 8 bytes dropped" in logtext(K15), data[-200:])
if want("K16"):
    K16 = copy("k16")
    rc, out, _ = run_packer(K16, CONV, "--once", "--convert-seconds", "0")
    common("K16a", rc, out, 2, "--convert-seconds")
    check("K16a no out/ made", not (K16 / "out").exists())
    nr = WORK / "k16_not_a_run"
    nr.mkdir()
    rc, out, _ = run_packer(nr, CONV, "--once")
    common("K16b", rc, out, 2, "RUN.json")

# ================================================================ K17 to K22: B1 to B3
def held_back(name):
    """A copy with pieces 2 to 5 held back, packed once with no converter: p000000 and p000001 raw, no mode file."""
    root = copy(name)
    held = WORK / f"{name}_held"
    held.mkdir()
    for i in (2, 3, 4, 5):
        for ext in ("raw", "seal.json"):
            os.replace(root / "w000" / "closed" / f"p{i:06d}.{ext}", held / f"p{i:06d}.{ext}")
    rc, out, _ = run_packer(root, NO_CONV, "--once")
    check(f"{name.upper()} the first run (no converter, pieces 0 and 1): exit 0, both raw, no mode file",
          rc == 0 and forms(root)[:2] == ["raw", "raw"] and not (root / "out" / "PACKER_MODE.jsonl").exists(),
          (rc, out[-200:], forms(root)))
    return root


def diff(a, b):
    return [ascii(n) for n in sorted(set(a) ^ set(b))] or [ascii(n) for n in a if a[n] != b.get(n)]


if want("K17") and K1 is not None:
    K17 = WORK / "k17"
    shutil.copytree(K1, K17)
    d = K17 / "out" / "w000"
    before = tree_bytes(d)
    (d / "p000000.offer.json.zz").unlink()
    rc, out, _ = run_packer(K17, NO_CONV, "--once")
    common("K17", rc, out, 0, "offered 1 pieces as binpack and 0 as raw")
    check("K17 out/w000 is K1's byte for byte again (no raw.zz, no conflict file)", tree_bytes(d) == before,
          diff(tree_bytes(d), before))
    check("K17 the log names p000000 finished from the files on disk",
          "w000/p000000: offered as binpack, finished from the files on disk" in logtext(K17), logtext(K17)[-400:])
if want("K18"):
    K18 = held_back("k18")
    d = K18 / "out" / "w000"
    before = tree_bytes(d)
    (d / "p000000.offer.json.zz").unlink()
    rc, out, _ = run_packer(K18, CONV, "--once")
    common("K18", rc, out, 0, "offered 0 pieces as binpack and 1 as raw")
    check("K18 out/w000 is the first run's byte for byte again (no binpack or meta.xz of p000000)",
          tree_bytes(d) == before, diff(tree_bytes(d), before))
if want("K19") and K1 is not None:
    def reoffer(d, **kv):
        o = json.loads((d / "p000000.offer.json").read_bytes())
        o.update(kv)
        return o

    for tag, change, text in (
            ("a", lambda d: put(d / "p000000.offer.json", (json.dumps(reoffer(d), sort_keys=True) + "\n").encode(
                "ascii")), "not in canonical form"),
            ("b", lambda d: put(d / "p000000.offer.json", canon(reoffer(d, seal_sha256="0" * 64))),
             "it is not this piece's offer"),
            ("c", lambda d: (d / "p000000.binpack").unlink(), "the member p000000.binpack")):
        root = WORK / f"k19{tag}"
        shutil.copytree(K1, root)
        d = root / "out" / "w000"
        (d / "p000000.offer.json.zz").unlink()
        change(d)
        before = tree_bytes(d)
        rc, out, _ = run_packer(root, NO_CONV, "--once")
        common(f"K19{tag}", rc, out, 4, "w000/p000000: p000000.offer.json is there without its wire copy")
        check(f"K19{tag} the stop names `{text}`", text in out, out[-400:])
        check(f"K19{tag} out/w000 unchanged byte for byte (no wire copy, no raw.zz, no conflict file)",
              tree_bytes(d) == before, diff(tree_bytes(d), before))
if want("K20") and K1 is not None:
    K20 = WORK / "k20a"
    shutil.copytree(K1, K20)
    d = K20 / "out" / "w000"
    keep = {n: (d / n).read_bytes() for n in ("p000000.binpack", "p000000.meta.xz")}
    for n in ("p000000.offer.json", "p000000.offer.json.zz"):
        (d / n).unlink()
    rc, out, _ = run_packer(K20, NO_CONV, "--once")
    common("K20a", rc, out, 0, "offered 0 pieces as binpack and 1 as raw")
    lg = logtext(K20)
    check("K20a p000000 offered raw; its binpack and meta.xz unchanged and each named in the log",
          (offer(K20, 0) or {}).get("form") == "raw" and (d / "p000000.offer.json.zz").is_file()
          and all((d / n).read_bytes() == b for n, b in keep.items())
          and all(f"w000/p000000: {n} is left as it is: no offer names it" in lg for n in keep), lg[-500:])
if want("K20"):
    K20b = held_back("k20b")
    d = K20b / "out" / "w000"
    keep = (d / "p000000.raw.zz").read_bytes()
    for n in ("p000000.offer.json", "p000000.offer.json.zz"):
        (d / n).unlink()
    rc, out, _ = run_packer(K20b, CONV, "--once")
    common("K20b", rc, out, 0, "offered 1 pieces as binpack and 0 as raw")
    lg = logtext(K20b)
    check("K20b p000000 offered binpack; its raw.zz unchanged and named in the log",
          (offer(K20b, 0) or {}).get("form") == "binpack" and (d / "p000000.offer.json.zz").is_file()
          and (d / "p000000.raw.zz").read_bytes() == keep
          and "w000/p000000: p000000.raw.zz is left as it is: no offer names it" in lg, lg[-500:])
if want("K21"):
    plant = WORK / "plant_converter.py"
    plant.write_text(f"""import os, subprocess, sys
if os.path.basename(os.getcwd()) == "w000.p000000" and not os.path.exists(os.path.join("..", "w000.p000001")):
    open(os.path.join("..", "w000.p000001"), "wb").close()     # a FILE where p000001's scratch folder goes
text = sys.stdin.read()
p = subprocess.run([{CONV.as_posix()!r}], input=text, capture_output=True, text=True)
sys.stdout.write(p.stdout + p.stderr)
sys.exit(p.returncode)
""", encoding="ascii")
    K21 = copy("k21")
    rc, out, _ = run_packer(K21, plant, "--once")
    common("K21", rc, out, 0, "offered 4 pieces as binpack and 2 as raw")
    lg = logtext(K21)
    line = next((ln for ln in lg.splitlines() if "w000/p000001: the converter's attempt failed (1 in a row)" in ln), "")
    check("K21 p000001 raw, the others as in K1; the log names its failed attempt with the folder; no mode file",
          forms(K21) == ["binpack", "raw", "raw", "binpack", "binpack", "binpack"] and "w000.p000001" in line
          and not (K21 / "out" / "PACKER_MODE.jsonl").exists(), (forms(K21), line, lg[-400:]))
if want("K22"):
    K22 = copy("k22a")
    odd = ["SCHEDULE.0.json", "SCHEDULE.01.json", "SCHEDULE.\u0661.json", "RESUME.0.json", "RESUME.0001.json"]
    for n in odd:
        put(K22 / n, b"{}\n")
    rng = K22 / "ranges" / "r\u0661\u0662\u0663\u0664.w000.seal.json"
    put(rng, b"{}\n")
    rc, out, _ = run_packer(K22, CONV, "--once")
    common("K22a", rc, out, 0, "offered 5 pieces as binpack and 1 as raw")
    check("K22a no wire copy of a name outside the grammar; RUN.json, SCHEDULE.1.json and r0001.w000.seal.json have "
          "theirs", not any((K22 / (n + ".zz")).exists() for n in odd) and not rng.with_name(rng.name + ".zz").exists()
          and all((K22 / n).is_file() for n in ("RUN.json.zz", "SCHEDULE.1.json.zz", "ranges/r0001.w000.seal.json.zz")),
          [ascii(f.name) for f in sorted(K22.iterdir()) + sorted((K22 / "ranges").iterdir())])
    K22b = copy("k22b")
    put(K22b / "w000" / "closed" / ("p" + "\u0660" * 5 + "\u0667.seal.json"), b"{}\n")
    rc, out, _ = run_packer(K22b, CONV, "--once")
    common("K22b", rc, out, 0, "offered 5 pieces as binpack and 1 as raw")

bad = [n for n, ok in results if not ok]
print(f"{len(results) - len(bad)} of {len(results)} checks pass" + (f"; FAILED: {bad}" if bad else ""))
sys.exit(1 if bad else 0)

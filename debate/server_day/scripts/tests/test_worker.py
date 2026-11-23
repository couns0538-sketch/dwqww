"""Fable 2026-11-23, W5 of FINAL_PLAN_2311.md: the test of run/worker.py and run/record.py.

    test_worker.py <engine exe> <net file> <serverday folder> <NEW work folder> [only=T1,T4,...]

Everything is played with the real engine and the frozen texts of <serverday folder>/workloads and /known. The
serverday folder is an argument so that a COPY with one planted change can be tested the same way (the test of
this test: tests/mutants.py). One engine thread; T9 runs two workers at once for a few seconds.

 T1  N12's six games through the worker: rows, end line and digest of every game as known/n12_batch.json; two
     pieces (4 + 2, the last one sealed at the end), their checksum files, the journal, every record's binding
 T2  plant no_newgame at game 2: game 2 as known/n12_no_newgame.json, the other five unchanged
 T3  plant writeminply9 at game 2: game 2 as known/n12_writeminply9.json, the other five unchanged
 T4  restart after a crash, four constructed states (a half-written third game; a journal without its piece;
     a piece shorter than its journal; ended between a game and its piece's closing; ended inside the closing):
     pieces byte for byte as T1, or exit code 4 where the spool cannot be trusted
 T5  a REAL kill of the worker in a run of 30 games with openings by seed, then a restart: pieces byte for byte
     as an uninterrupted run, every game id once, no engine process left
 T6  the start-up refuses (exit 5, no game, the reason named): eleven changed inputs
 T7  three engine failures in a row: exit 6, no game
 T8  openings: same seed = same pieces; another seed, another worker = other openings; every opening computed
     again with a rules library of the tester's own
 T9  A23 at the worker: two workers at once with the two histories that end in the same position, the final
     writes exchanged; a misspelt `moves`; two plies cut off; the same after a restart: exit 7, nothing credited
 T10 A23 at the reader: results, ids, sent lines exchanged in a piece; a consistent rewrite; a record cut off
 T11 a legitimate retry (the engine ended once in the middle of a game) is credited once and is the same game
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if len(sys.argv) < 5:
    print(__doc__)
    sys.exit(2)
EXE, NET, SD, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve()
ONLY = set()
for extra in sys.argv[5:]:
    if not extra.startswith("only="):
        print(f"STOP: not understood: {extra}")
        sys.exit(2)
    ONLY |= set(extra[5:].split(","))
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW work folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
sys.path.insert(0, str(SD / "run"))
import record  # noqa: E402   the reader's side of the record, from the tree under test

MAN, KNOWN = SD / "workloads" / "MANIFEST.json", SD / "known" / "startup.json"
results = []


def check(name: str, ok, detail="") -> bool:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:300]}" if detail != "" and not ok else ""), flush=True)
    return bool(ok)


def want(case: str) -> bool:
    return not ONLY or case in ONLY


def worker_cmd(spool, worker=1, games=0, piece_games=4, openings=None, seed="seedA", run_id="n12", plant=None,
               manifest=MAN, known=KNOWN, net=NET, game_seconds=None):
    cmd = [sys.executable, "-I", "-B", str(SD / "run" / "worker.py"), "--exe", str(EXE), "--net", str(net),
           "--manifest", str(manifest), "--known-startup", str(known), "--spool", str(spool), "--run-id", run_id,
           "--worker", str(worker), "--root-seed", seed, "--piece-games", str(piece_games)]
    if games:
        cmd += ["--games", str(games)]
    if openings:
        cmd += ["--openings", str(openings)]
    if plant:
        cmd += ["--rehearsal", "--plant", plant]
    if game_seconds is not None:
        cmd += ["--game-seconds", str(game_seconds)]
    return cmd


def run_worker(spool, **kw):
    p = subprocess.run(worker_cmd(spool, **kw), capture_output=True, text=True, timeout=1200)
    return p.returncode, (p.stdout + p.stderr).strip()


def wdir(spool, worker=1) -> Path:
    return Path(spool) / f"w{worker:03d}"


def journal(spool, worker=1) -> list:
    f = wdir(spool, worker) / "journal.txt"
    return f.read_text(encoding="utf-8").splitlines() if f.exists() else []


def done_ids(spool, worker=1) -> list:
    return [ln.split()[1] for ln in journal(spool, worker) if ln.startswith("done ")]


def closed_pieces(spool, worker=1) -> dict:
    d = wdir(spool, worker) / "closed"
    return {f.name: f.read_bytes() for f in sorted(d.glob("*.raw"))} if d.exists() else {}


def records(spool, worker=1) -> list:
    out = []
    for data in closed_pieces(spool, worker).values():
        out += record.parse(data)
    return out


def credited_bytes(spool, worker=1) -> int:
    d = wdir(spool, worker)
    return sum(f.stat().st_size for sub in ("open", "closed") for f in (d / sub).glob("*.raw"))


def field_digest(g: dict) -> str:
    """The digest of the plan's N12 fixture, as tools/check_run.py computes it: every row, a space, the result."""
    res = g["end"].split()[2]
    h = hashlib.sha256()
    for row in g["rows"]:
        h.update((row + " " + res + "\n").encode("ascii"))
    return h.hexdigest()


def as_known(g: dict) -> list:
    return [len(g["rows"]), g["end"], field_digest(g)]


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


def engines_gone(spool, worker=1, secs=60.0) -> list:
    """The engine pids of the journal that are still alive after at most secs."""
    pids = [int(ln.split()[ln.split().index("pid") + 1]) for ln in journal(spool, worker) if ln.startswith("engine_started ")]
    end = time.time() + secs
    while time.time() < end and any(alive(p) for p in pids):
        time.sleep(0.5)
    return [p for p in pids if alive(p)]


def pieces_checksums_ok(spool, worker=1) -> bool:
    d = wdir(spool, worker) / "closed"
    raws = sorted(d.glob("*.raw"))
    for f in raws:
        s = f.with_suffix(".sha256")
        if not s.exists() or s.read_text(encoding="ascii").split()[0] != hashlib.sha256(f.read_bytes()).hexdigest():
            return False
    return len(raws) == len(list(d.glob("*.sha256"))) and not list(d.glob("*.part"))


# ---- the fixed openings and the known answers, read from the frozen files (nothing typed again) ---------------
N12 = [ln.split()[3:] for ln in (SD / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
assert len(N12) == 6 and all(len(o) == 8 for o in N12), N12
OPENINGS = WORK / "n12_openings.txt"
OPENINGS.write_text("".join(" ".join(o) + "\n" for o in N12), encoding="ascii")
K_BATCH = json.loads((SD / "known" / "n12_batch.json").read_text(encoding="ascii"))["games"]
K_NONEW = json.loads((SD / "known" / "n12_no_newgame.json").read_text(encoding="ascii"))["games"]
K_WMP9 = json.loads((SD / "known" / "n12_writeminply9.json").read_text(encoding="ascii"))["games"]
HIST_A, HIST_B = N12[4], N12[5]          # A23's two histories: the same position after 8 plies, other games

T1 = WORK / "t1"
t1_needed = any(want(c) for c in ("T1", "T4", "T10", "T11"))
if t1_needed:
    rc, out = run_worker(T1, games=6, openings=OPENINGS)
    recs = records(T1) if rc == 0 else []
    if want("T1"):
        check("T1 exit code 0", rc == 0, out)
        check("T1 six games, each as the known answers (rows, end line, digest)",
              [as_known(g) for g in recs] == K_BATCH, [(len(g["rows"]), field_digest(g)[:10]) for g in recs])
        cp = closed_pieces(T1)
        check("T1 two closed pieces (4 + 2 games), nothing left open",
              list(cp) == ["p000000.raw", "p000001.raw"] and [len(record.parse(b)) for b in cp.values()] == [4, 2]
              and not list((wdir(T1) / "open").glob("*")), list(cp))
        check("T1 every piece has its checksum file and it fits", pieces_checksums_ok(T1))
        j = journal(T1)
        check("T1 journal: one start, six games in order, two closings",
              [ln.split()[0] for ln in j] == ["engine_started"] + ["done"] * 4 + ["closed"] + ["done"] * 2 + ["closed"]
              and done_ids(T1) == [f"n12-w001-g{k:08d}" for k in range(1, 7)], [ln[:40] for ln in j])
        check("T1 every record's binding holds against the opening of the file",
              all(record.faults(g, N12[k]) == [] for k, g in enumerate(recs)) and len(recs) == 6,
              [record.faults(g, N12[k]) for k, g in enumerate(recs)])
        check("T1 the journal's digest of every game is the digest of its record's bytes",
              [ln.split()[-1] for ln in j if ln.startswith("done ")] ==
              [hashlib.sha256(data[g["first"]:g["last"]]).hexdigest() for data in cp.values() for g in record.parse(data)])
        log = (wdir(T1) / "worker.log").read_text(encoding="utf-8")
        m = re.search(r"sent_kept (\d+)", log)
        check("T1 no sent line is kept from game to game", m is not None and int(m[1]) <= 1, log[-200:])
        check("T1 the heartbeat names six games", " games 6 " in (wdir(T1) / "heartbeat").read_text(encoding="ascii"))
        check("T1 no engine process is left", engines_gone(T1) == [])
T1_BYTES = closed_pieces(T1) if t1_needed else {}
T1_RECS = records(T1) if t1_needed and T1_BYTES else []

for case, plant, known in (("T2", "no_newgame:2", K_NONEW), ("T3", "writeminply9:2", K_WMP9)):
    if not want(case):
        continue
    sp = WORK / case.lower()
    rc, out = run_worker(sp, games=6, openings=OPENINGS, plant=plant)
    got = [as_known(g) for g in records(sp)] if rc == 0 else []
    check(f"{case} exit code 0 with the plant {plant}", rc == 0, out)
    check(f"{case} game 2 is the planted game of the known answers", len(got) == 6 and got[1] == known[1],
          got[1][:1] if len(got) > 1 else got)
    check(f"{case} game 2 is NOT the clean game", len(got) == 6 and got[1] != K_BATCH[1])
    check(f"{case} the other five games are unchanged", len(got) == 6 and [g for k, g in enumerate(got) if k != 1] ==
          [g for k, g in enumerate(K_BATCH) if k != 1])
    check(f"{case} the journal says that this run is a rehearsal with a plant", any(ln.startswith("PLANT ") for ln in journal(sp)))


def constructed(name: str, done_lines: int, open_bytes=None, closed_bytes=None) -> Path:
    """A spool as a crash would leave it, made from T1's journal and pieces."""
    sp = WORK / name
    d = wdir(sp)
    (d / "open").mkdir(parents=True)
    (d / "closed").mkdir(parents=True)
    keep, n = [], 0
    for ln in journal(T1):
        if ln.startswith("closed "):
            break
        if ln.startswith("done "):
            if n == done_lines:
                break
            n += 1
        keep.append(ln)
    (d / "journal.txt").write_bytes(("\n".join(keep) + "\n").encode("utf-8"))
    if open_bytes is not None:
        (d / "open" / "p000000.raw").write_bytes(open_bytes)
    if closed_bytes is not None:
        (d / "closed" / "p000000.raw").write_bytes(closed_bytes)
    return sp


if want("T4") and T1_RECS:
    p0 = T1_BYTES["p000000.raw"]
    two, third = T1_RECS[1]["last"], T1_RECS[2]
    half = p0[:two + (third["last"] - third["first"]) // 2]
    for name, sp, word in (
            ("T4a a half-written third game", constructed("t4a", 2, open_bytes=half), "cut back"),
            ("T4c ended between a game and its piece's closing", constructed("t4c", 4, open_bytes=p0), ""),
            ("T4d ended inside the closing (piece moved, no line in the journal)", constructed("t4d", 4, closed_bytes=p0), "closing is finished")):
        rc, out = run_worker(sp, games=6, openings=OPENINGS)
        check(f"{name}: exit code 0", rc == 0, out)
        check(f"{name}: pieces byte for byte as T1", closed_pieces(sp) == T1_BYTES and pieces_checksums_ok(sp))
        check(f"{name}: every game id once, in order", done_ids(sp) == done_ids(T1), done_ids(sp))
        if word:
            check(f"{name}: the log names what was repaired", word in (wdir(sp) / "worker.log").read_text(encoding="utf-8"))
    for name, sp, word in (("T4b a journal without its piece", constructed("t4b", 2), "is missing"),
                           ("T4b2 a piece shorter than its journal", constructed("t4b2", 2, open_bytes=p0[:two - 7]), "the file holds")):
        before = (wdir(sp) / "journal.txt").read_bytes()
        rc, out = run_worker(sp, games=6, openings=OPENINGS)
        check(f"{name}: exit code 4 and the reason named", rc == 4 and word in out, (rc, out))
        check(f"{name}: nothing was played or written", (wdir(sp) / "journal.txt").read_bytes() == before and not closed_pieces(sp))

if want("T5") or want("T8"):
    A = WORK / "t5_whole"
    rcA, outA = run_worker(A, games=30, piece_games=7, run_id="rnd", seed="seedA")
    A_BYTES, A_RECS = closed_pieces(A), (records(A) if rcA == 0 else [])
if want("T5"):
    check("T5 the uninterrupted run: exit code 0, 30 games, five pieces", rcA == 0 and len(A_RECS) == 30 and len(A_BYTES) == 5, outA)
    B = WORK / "t5_killed"
    p = subprocess.Popen(worker_cmd(B, games=30, piece_games=7, run_id="rnd", seed="seedA"),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time() + 300
    while time.time() < end and len(done_ids(B)) < 9 and p.poll() is None:
        time.sleep(0.02)
    was_running = p.poll() is None
    p.kill()
    p.wait(timeout=60)
    at_kill = len(done_ids(B))
    check("T5 the worker was killed in the middle (between 9 and 29 games journalled)", was_running and 9 <= at_kill < 30, at_kill)
    check("T5 the engine of the killed worker ends by itself", engines_gone(B) == [])
    rc, out = run_worker(B, games=30, piece_games=7, run_id="rnd", seed="seedA")
    check("T5 the restart: exit code 0", rc == 0, out)
    check("T5 pieces byte for byte as the uninterrupted run", closed_pieces(B) == A_BYTES and pieces_checksums_ok(B))
    check("T5 every game id once, in order", done_ids(B) == done_ids(A) and len(set(done_ids(B))) == 30)
    check("T5 two engine starts in the journal, no engine process left",
          sum(ln.startswith("engine_started ") for ln in journal(B)) == 2 and engines_gone(B) == [])

if want("T6"):
    man = json.loads(MAN.read_text(encoding="ascii"))
    known = json.loads(KNOWN.read_text(encoding="ascii"))
    opts = man["options"]
    i_hash = opts.index("setoption name Hash value 16")
    i_true = next(k for k, o in enumerate(opts) if o.endswith(" value true") and "NNUEArch " not in o)
    i_file, i_arch = next(k for k, o in enumerate(opts) if " NNUEArchFile " in o), next(k for k, o in enumerate(opts) if " NNUEArch " in o)
    bad_net = WORK / "t6_other_net.fnn3"
    data = bytearray(NET.read_bytes())
    data[len(data) // 2] ^= 0x01
    bad_net.write_bytes(bytes(data))

    def with_options(new):
        return dict(man, options=new)

    swapped = list(opts)
    swapped[i_file], swapped[i_arch] = swapped[i_arch], swapped[i_file]
    more = json.loads(json.dumps(known))
    more["search"][0][1] += 1
    cases = [
        ("Hash 32 instead of 16", with_options(opts[:i_hash] + ["setoption name Hash value 32"] + opts[i_hash + 1:]), known, NET, "start-up search gave"),
        ("a misspelt option name", with_options(["setoption name Thraeds value 1"] + opts[1:]), known, NET, "has no option Thraeds"),
        ("a value out of range", with_options(opts[:i_hash] + ["setoption name Hash value 99999999"] + opts[i_hash + 1:]), known, NET, "is outside"),
        ("True with a capital", with_options(opts[:i_true] + [opts[i_true][:-4] + "True"] + opts[i_true + 1:]), known, NET, "neither true nor false"),
        ("a line twice", with_options(opts + [opts[i_hash]]), known, NET, "stands twice"),
        ("UseNNUE false", with_options(opts + ["setoption name UseNNUE value false"]), known, NET, "UseNNUE false"),
        ("the two net lines the other way round", with_options(swapped), known, NET, "NNUEArchFile before NNUEArch"),
        ("another net file (one bit changed)", man, known, bad_net, "is not the manifest's"),
        ("another net file that the manifest names", dict(man, net_sha256=hashlib.sha256(bytes(data)).hexdigest()), known, bad_net, "START REFUSED"),
        ("a missing net file", man, known, WORK / "no_such_net.fnn3", "is missing or is not"),
        ("a known answer with one node more", man, more, NET, "start-up search gave"),
    ]
    assert opts[0] == "setoption name Threads value 1", opts[0]
    for k, (name, m, kn, net, word) in enumerate(cases):
        mf, kf, sp = WORK / f"t6_{k}_manifest.json", WORK / f"t6_{k}_known.json", WORK / f"t6_{k}"
        mf.write_text(json.dumps(m), encoding="ascii")
        kf.write_text(json.dumps(kn), encoding="ascii")
        rc, out = run_worker(sp, games=1, openings=OPENINGS, manifest=mf, known=kf, net=net)
        check(f"T6 refused, exit 5, reason named: {name}", rc == 5 and word in out, (rc, out))
        check(f"T6 no game and no piece: {name}", done_ids(sp) == [] and credited_bytes(sp) == 0 and engines_gone(sp) == [])

if want("T7"):
    sp = WORK / "t7"
    rc, out = run_worker(sp, games=2, openings=OPENINGS, game_seconds=0.001)
    log = (wdir(sp) / "worker.log").read_text(encoding="utf-8")
    check("T7 three failures in a row: exit code 6", rc == 6, (rc, out))
    check("T7 three games thrown away, none credited, no engine left",
          log.count("thrown away") == 3 and done_ids(sp) == [] and credited_bytes(sp) == 0 and engines_gone(sp) == [], log[-300:])

if want("T8"):
    def spelt_again(seed: str, gid: str, ply: int, n: int) -> int:
        return int.from_bytes(hashlib.sha256(f"{seed}|{gid}|{ply}".encode("ascii")).digest()[:8], "big") % n

    runs = {}
    for name, kw in (("again", dict(seed="seedA")), ("seedB", dict(seed="seedB")), ("worker2", dict(seed="seedA", worker=2))):
        sp = WORK / f"t8_{name}"
        rc, out = run_worker(sp, games=8, piece_games=7, run_id="rnd", **kw)
        runs[name] = (rc, closed_pieces(sp, kw.get("worker", 1)), records(sp, kw.get("worker", 1)) if rc == 0 else [])
    first8 = [g["opening"] for g in A_RECS[:8]]
    check("T8 the same seed, run id and worker: the same pieces, byte for byte",
          runs["again"][0] == 0 and b"".join(runs["again"][1].values()) == b"".join(A_BYTES.values())[:len(b"".join(runs["again"][1].values()))]
          and len(runs["again"][2]) == 8)
    check("T8 another root seed: other openings", runs["seedB"][0] == 0 and len(runs["seedB"][2]) == 8
          and all(a != b for a, b in zip(first8, [g["opening"] for g in runs["seedB"][2]])))
    check("T8 another worker number: other openings", runs["worker2"][0] == 0 and len(runs["worker2"][2]) == 8
          and all(a != b for a, b in zip(first8, [g["opening"] for g in runs["worker2"][2]])))
    check("T8 30 games have 30 different openings", len({tuple(g["opening"]) for g in A_RECS}) == 30)
    try:
        import chess
    except ImportError:
        chess = None
    if chess is None:
        check("T8 openings computed again with a rules library (NOT RUN: no python-chess in this Python)", False)
    else:
        def reserve(seed: str, gid: str) -> list:
            b, moves = chess.Board(), []
            for ply in range(8):
                legal = sorted(m.uci() for m in b.legal_moves)
                if not legal:
                    break
                moves.append(legal[spelt_again(seed, gid, ply, len(legal))])
                b.push_uci(moves[-1])
            return moves
        allr = [("seedA", g) for g in A_RECS] + [("seedB", g) for g in runs["seedB"][2]] + [("seedA", g) for g in runs["worker2"][2]]
        bad = [(g["id"], record.faults(g, reserve(s, g["id"]))) for s, g in allr if record.faults(g, reserve(s, g["id"]))]
        check(f"T8 every one of {len(allr)} openings is the one a rules library gives for root seed and game id", len(allr) == 46 and not bad, bad[:2])
        g = A_RECS[0]
        check("T8 planted: with another root seed the reader refuses the same record",
              record.faults(g, reserve("seedB", g["id"])) == ["the opening is not the one reserved for this game id"])

if want("T9"):
    ab, ba = WORK / "t9_ab.txt", WORK / "t9_ba.txt"
    ab.write_text(" ".join(HIST_A) + "\n" + " ".join(HIST_B) + "\n", encoding="ascii")
    ba.write_text(" ".join(HIST_B) + "\n" + " ".join(HIST_A) + "\n", encoding="ascii")
    for name, plant in (("control, no plant", None), ("the final writes exchanged", "swap_final:1")):
        sp = WORK / ("t9_ctl" if plant is None else "t9_swap")
        ps = [subprocess.Popen(worker_cmd(sp, worker=w, games=2, openings=f, run_id="a23", plant=plant),
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) for w, f in ((1, ab), (2, ba))]
        outs = [p.communicate(timeout=600)[0] for p in ps]
        rcs = [p.returncode for p in ps]
        if plant is None:
            r1, r2 = records(sp, 1), records(sp, 2)
            check("T9 control: two workers at once, exit 0, history A gives the 81-row game and B the 67-row game",
                  rcs == [0, 0] and [as_known(g) for g in r1] == [K_BATCH[4], K_BATCH[5]] and [as_known(g) for g in r2] == [K_BATCH[5], K_BATCH[4]],
                  (rcs, outs))
            check("T9 control: the two histories really end in the same position (first row equal, games differ)",
                  len(r1) == 2 and r1[0]["rows"][0] == r1[1]["rows"][0] and r1[0]["rows"] != r1[1]["rows"])
        else:
            check("T9 the final writes exchanged between two workers: both end with exit code 7",
                  rcs == [7, 7] and all("BINDING REFUSED" in o for o in outs), (rcs, outs))
            check("T9 neither wrong game is credited (no game in a journal, no byte in a piece), a REFUSED line in both journals",
                  all(done_ids(sp, w) == [] and credited_bytes(sp, w) == 0 and any(ln.startswith("REFUSED a23-") for ln in journal(sp, w)) for w in (1, 2)))
            check("T9 no engine process is left", engines_gone(sp, 1) == [] and engines_gone(sp, 2) == [])
    for plant, word in (("mvoes:1", "mvoes"), ("cut2:1", "written `position startpos moves " + " ".join(HIST_A[:-2]) + "`")):
        sp = WORK / f"t9_{plant.split(':')[0]}"
        rc, out = run_worker(sp, games=2, openings=ab, run_id="a23", plant=plant)
        check(f"T9 plant {plant}: exit code 7, the written line named, nothing credited",
              rc == 7 and word in out and done_ids(sp) == [] and credited_bytes(sp) == 0, (rc, out))
    sp = WORK / "t9_restart"
    rc1, out1 = run_worker(sp, games=2, openings=ab, run_id="a23")
    rc2, out2 = run_worker(sp, games=4, openings=ab, run_id="a23", plant="swap_final:3")
    check("T9 after a restart: the exchange at game 3 is refused (exit 7), games 1 and 2 stay credited and sealed",
          rc1 == 0 and rc2 == 7 and done_ids(sp) == ["a23-w001-g00000001", "a23-w001-g00000002"]
          and [as_known(g) for g in records(sp)] == [K_BATCH[4], K_BATCH[5]] and pieces_checksums_ok(sp), (rc1, rc2, out2))

if want("T10") and T1_RECS:
    g5, g6 = T1_RECS[4], T1_RECS[5]

    def piece_of(*games) -> bytes:
        """The lines of the given records AS THEY STAND (the bind line is not computed again)."""
        return "".join(f"game {g['id']} opening {' '.join(g['opening'])}\nsent {g['sent']}\n" + "".join(r + "\n" for r in g["rows"])
                       + g["end"] + "\n" + f"bind {g['bind']}\n" for g in games).encode("ascii")

    def refused(data: bytes, reserved) -> list:
        return [bool(record.faults(g, r)) for g, r in zip(record.parse(data), reserved)]

    check("T10 control: the two records as written are credited", piece_of(g5, g6) == T1_BYTES["p000001.raw"]
          and refused(piece_of(g5, g6), [HIST_A, HIST_B]) == [False, False])
    check("T10 the two results exchanged (rows and end lines): both refused",
          refused(piece_of(dict(g5, rows=g6["rows"], end=g6["end"]), dict(g6, rows=g5["rows"], end=g5["end"])), [HIST_A, HIST_B]) == [True, True])
    check("T10 the two game ids exchanged: both refused",
          refused(piece_of(dict(g5, id=g6["id"]), dict(g6, id=g5["id"])), [HIST_B, HIST_A]) == [True, True])
    check("T10 the two sent lines exchanged: both refused",
          refused(piece_of(dict(g5, sent=g6["sent"]), dict(g6, sent=g5["sent"])), [HIST_A, HIST_B]) == [True, True])
    forged = record.text(g5["id"], g6["opening"], g6["sent"], g6["rows"], g6["end"]).encode("ascii")
    check("T10 a consistent rewrite (B's whole game under A's id, bind computed again) passes WITHOUT the reader's own reservation",
          [record.faults(g) for g in record.parse(forged)] == [[]])
    check("T10 ... and is refused WITH it", [record.faults(g, HIST_A) for g in record.parse(forged)] ==
          [["the opening is not the one reserved for this game id"]])
    mv = record.text(g5["id"], g5["opening"], g5["sent"].replace(" moves ", " mvoes "), g5["rows"], g5["end"]).encode("ascii")
    check("T10 a misspelt `moves` in the sent line, bind computed again: refused", refused(mv, [HIST_A]) == [True])
    cut = record.text(g5["id"], g5["opening"], record.position_line(g5["opening"][:-2]), g5["rows"], g5["end"]).encode("ascii")
    check("T10 a sent line two plies short, bind computed again: refused", refused(cut, [HIST_A]) == [True])
    for name, data in (("a record cut off in a row", T1_BYTES["p000001.raw"][:g5["last"] - 200]),
                       ("a record without its bind line", T1_BYTES["p000001.raw"][:g5["last"] - 70]),
                       ("a row outside a record", b"sg 1 2 3\n" + T1_BYTES["p000001.raw"])):
        try:
            record.parse(data)
            ok = False
        except record.RecordError:
            ok = True
        check(f"T10 {name}: the piece is not read at all", ok)

if want("T11") and T1_RECS:
    sp = WORK / "t11"
    rc, out = run_worker(sp, games=3, openings=OPENINGS, plant="kill_engine:1")
    log = (wdir(sp) / "worker.log").read_text(encoding="utf-8")
    check("T11 the engine ended once in the middle of game 1: exit code 0", rc == 0, out)
    check("T11 the first try was thrown away and the engine started again (two starts in the journal)",
          log.count("thrown away (1 in a row)") == 1 and sum(ln.startswith("engine_started ") for ln in journal(sp)) == 2, log[-300:])
    check("T11 the retry is credited ONCE", done_ids(sp) == [f"n12-w001-g{k:08d}" for k in (1, 2, 3)])
    check("T11 and it is the same game: the three records byte for byte as T1's first three",
          b"".join(closed_pieces(sp).values()) == T1_BYTES["p000000.raw"][:T1_RECS[2]["last"]] and engines_gone(sp) == [])

bad = [n for n, ok in results if not ok]
print(f"{'ALL ' + str(len(results)) + ' CHECKS PASS' if not bad else 'FAILED ' + str(len(bad)) + ' of ' + str(len(results))}"
      + (f" (only {sorted(ONLY)})" if ONLY else ""))
sys.exit(1 if bad or not results else 0)

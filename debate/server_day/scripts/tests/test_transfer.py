"""Fable 2026-11-23, W5 (d), (e) with A23 and A11 of FINAL_PLAN_2311.md: the test of run/packer.py and
home/receiver.py, with real games of the real engine and the official converter.

    test_transfer.py <engine exe> <net file> <converter exe> <serverday folder> <NEW work folder> [only=P1,P7,...]

Needs python-chess (it forges a legal wrong move, and the receiver needs it). A delivery is a folder copy here;
the transport and its ten-minute cut belong to the rehearsal.

 P1  packing: N12's six games, two pieces, both offered packed; the raw pieces stay on the server
 P2  receiving: every game credited once, the game without rows keeps its id, the pieces built again at home are
     the workers' pieces byte for byte, a confirmation for each
 P3  the same pieces delivered a second time: credited once
 P4  the same payload under fresh ids (another worker, the same openings): recognised by its rows, credited once
 P5  a dropped piece is asked for again and the gap in the game numbers is reported; delivered later: credited
 P6  one byte changed on the way: asked for again for THAT reason, nothing of it credited; the good one: credited
 P7  one wrong final move with correct checksums of the packed files: asked for again; with the piece's own
     sha256 forged too: that game is refused by its binding, the others are credited
 P8  A23: the two results exchanged, every checksum made to fit: both refused, also in a later pass
 P9  another root seed at the receiver: every opening is refused as not reserved
 P10 confirmations: held back = the server removes nothing; a confirmation naming another sha256 = nothing
     removed; the real one = the piece is removed on the server
 P11 a converter that writes a position its own way: the packer's proof catches it, the piece travels as raw text,
     and the receiver credits the very same games
 P12 the packer refuses a piece whose bytes changed after closing, and one whose record does not carry its binding
 P13 a receiver pass cut off after crediting and before the piece's line: the next pass credits nothing twice
"""
import hashlib
import json
import lzma
import shutil
import subprocess
import sys
from pathlib import Path

if len(sys.argv) < 6:
    print(__doc__)
    sys.exit(2)
EXE, NET, CONV, SD, WORK = (Path(x).resolve() for x in sys.argv[1:6])
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
sys.path.insert(0, str(SD / "run"))
import packer  # noqa: E402
import record  # noqa: E402
import chess  # noqa: E402

MAN, KNOWN = SD / "workloads" / "MANIFEST.json", SD / "known" / "startup.json"
results = []


def check(name: str, ok, detail="") -> bool:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:400]}" if detail != "" and not ok else ""), flush=True)
    return bool(ok)


def want(case: str) -> bool:
    return not ONLY or case in ONLY


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def run(cmd, **kw):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=1800, **kw)
    return p.returncode, (p.stdout + p.stderr).strip()


def play(spool, worker, games, piece_games, run_id, openings=None, seed="seedA"):
    cmd = [sys.executable, "-I", "-B", SD / "run" / "worker.py", "--exe", EXE, "--net", NET, "--manifest", MAN,
           "--known-startup", KNOWN, "--spool", spool, "--run-id", run_id, "--worker", worker, "--root-seed", seed,
           "--piece-games", piece_games, "--games", games] + (["--openings", openings] if openings else [])
    rc, out = run(cmd)
    assert rc == 0, out
    return spool


def pack(spool, out, converter=CONV, confirmed=None):
    return run([sys.executable, "-I", "-B", SD / "run" / "packer.py", "--spool", spool, "--out", out, "--converter", converter,
                "--once"] + (["--confirmed", confirmed] if confirmed else []))


def receive(inbox, state, seed="seedA", openings=None, hold=False):
    rc, out = run([sys.executable, "-I", "-B", SD / "home" / "receiver.py", "--inbox", inbox, "--state", state, "--converter", CONV,
                   "--root-seed", seed] + (["--openings", openings] if openings else []) + (["--hold"] if hold else []))
    s = json.loads((Path(state) / "summary.json").read_text(encoding="ascii")) if rc == 0 else {"this_pass": {}, "in_all": {}}
    return rc, out, s["this_pass"], s["in_all"]


def jl(path: Path) -> list:
    return [json.loads(x) for x in path.read_text(encoding="ascii").splitlines()] if path.exists() else []


def deliver(src: Path, inbox: Path, only=None):
    """A folder copy as the transport: the whole out folder, or only the named pieces (wNNN/pNNNNNN) + PIECES.txt."""
    for f in sorted(src.rglob("*")):
        if f.is_dir() or f.name in ("packer.log",):
            continue
        rel = f.relative_to(src)
        if only is not None and f.name != "PIECES.txt" and f"{rel.parent.as_posix()}/{f.name.split('.')[0]}" not in only:
            continue
        (inbox / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, inbox / rel)


def offer(out: Path, w: str, name: str, raw: bytes, raw_sha=None):
    """A piece offered by a FORGER: packed with the real converter, every file checksum correct; the raw piece's
    sha256 is the true one of these bytes unless another is given."""
    d = out / w
    d.mkdir(parents=True, exist_ok=True)
    games = record.parse(raw)
    (d / f"{name}.tmp.plain").write_bytes(packer.plain_of(games).encode("ascii"))
    packer.convert(str(CONV), d / f"{name}.tmp.plain", d / f"{name}.binpack")
    (d / f"{name}.tmp.plain").unlink()
    (d / f"{name}.meta.xz").write_bytes(lzma.compress(packer.meta_of(games).encode("ascii")))
    files = [d / f"{name}.binpack", d / f"{name}.meta.xz"]
    rows = sum(len(g["rows"]) for g in games)
    (d / f"{name}.packed").write_text("".join(f"{sha(f.read_bytes())}  {f.stat().st_size}  {f.name}\n" for f in files)
                                      + f"form binpack games {len(games)} rows {rows} raw_bytes {len(raw)} raw_sha256 {raw_sha or sha(raw)}\n",
                                      encoding="ascii")


def lines_of(g: dict) -> str:
    """One record's text AS ITS FIELDS STAND (the bind line is not computed again)."""
    return (f"game {g['id']} opening {' '.join(g['opening'])}\nsent {g['sent']}\n" + "".join(r + "\n" for r in g["rows"])
            + g["end"] + "\n" + f"bind {g['bind']}\n")


N12 = [ln.split()[3:] for ln in (SD / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
OPENINGS = WORK / "n12_openings.txt"
OPENINGS.write_text("".join(" ".join(o) + "\n" for o in N12), encoding="ascii")
K_ROWS = json.loads((SD / "known" / "n12_batch.json").read_text(encoding="ascii"))["totals"]["rows"]

# ---- the games: N12's six by worker 1 and again by worker 2 (the same payload under other ids), 12 by seed -----
S1 = play(WORK / "spool_n12", 1, 6, 4, "n12", OPENINGS)
S2 = play(WORK / "spool_n12_w2", 2, 6, 4, "n12", OPENINGS)
SR = play(WORK / "spool_rnd", 1, 12, 5, "rnd")
RAW1 = {f.stem: f.read_bytes() for f in sorted((S1 / "w001" / "closed").glob("*.raw"))}
OUT1 = WORK / "out_n12"
rc_pack, out_pack = pack(S1, OUT1)
INBOX, STATE = WORK / "inbox_n12", WORK / "state_n12"

if want("P1"):
    packed = sorted(p.name for p in (OUT1 / "w001").glob("*"))
    check("P1 the packer ends with 0 and offers both pieces packed", rc_pack == 0 and "offered 2 pieces packed and 0 as raw text" in out_pack, out_pack)
    check("P1 each piece: its packed rows, its compressed meta text, its .packed file; nothing half-made left",
          packed == ["p000000.binpack", "p000000.meta.xz", "p000000.packed", "p000001.binpack", "p000001.meta.xz", "p000001.packed"], packed)
    check("P1 the list for the receiver names both pieces with the workers' own sha256",
          [ln.split()[0] + " " + ln.split()[-1] for ln in (OUT1 / "PIECES.txt").read_text(encoding="ascii").splitlines()] ==
          [f"w001/{n} {sha(b)}" for n, b in RAW1.items()])
    check("P1 nothing was removed on the server (no confirmation yet)", sorted(f.stem for f in (S1 / "w001" / "closed").glob("*.raw")) == sorted(RAW1))
    bp = sum((OUT1 / "w001" / f"{n}.binpack").stat().st_size for n in RAW1)
    check("P1 the packed rows take under 3 bytes a row", bp / K_ROWS < 3.0, bp / K_ROWS)

deliver(OUT1, INBOX)
rc2, out2, pass2, all2 = receive(INBOX, STATE, openings=OPENINGS)
if want("P2"):
    check("P2 the pass ends with 0: two pieces confirmed, nothing asked again, nothing refused",
          rc2 == 0 and pass2.get("confirmed") == 2 and pass2.get("asked_again") == 0 and all2.get("refused") == 0, out2)
    check(f"P2 five games credited with all {K_ROWS} rows of the known answers; the game without rows keeps its id and credits nothing",
          all2.get("credited_games") == 5 and all2.get("credited_rows") == K_ROWS and all2.get("no_rows") == 1 and all2.get("missing_game_numbers") == 0, all2)
    check("P2 the pieces built again at home are the workers' pieces, byte for byte",
          {f.stem: f.read_bytes() for f in (STATE / "raw" / "w001").glob("*.raw")} == RAW1)
    check("P2 each confirmation names the worker's sha256 of its piece",
          [(STATE / "confirmed" / "w001" / f"{n}.confirmed").read_text(encoding="ascii").split()[0] for n in RAW1] == [sha(b) for b in RAW1.values()])
    ids = [c["id"] for c in jl(STATE / "credited.jsonl")]
    check("P2 the ledger: five ids, each once", len(ids) == 5 and len(set(ids)) == 5 and "n12-w001-g00000003" not in ids, ids)
LEDGER1 = sorted(c["identity"] for c in jl(STATE / "credited.jsonl"))

if want("P3"):
    rc, out, now, tot = receive(INBOX, STATE, openings=OPENINGS)
    check("P3 the same pieces delivered again: both recognised, credited once",
          rc == 0 and now.get("delivered_again") == 2 and now.get("credited_rows") == 0 and tot.get("credited_rows") == K_ROWS
          and len(jl(STATE / "credited.jsonl")) == 5, (now, tot))

if want("P4"):
    out_w2 = WORK / "out_n12_w2"
    pack(S2, out_w2)
    deliver(out_w2, INBOX)
    rc, out, now, tot = receive(INBOX, STATE, openings=OPENINGS)
    dup = jl(STATE / "duplicates.jsonl")
    check("P4 the same payload under fresh ids: confirmed, five copies recognised by their rows, credited rows unchanged",
          rc == 0 and now.get("confirmed") == 2 and now.get("duplicates") == 5 and now.get("credited_rows") == 0
          and tot.get("credited_rows") == K_ROWS and tot.get("refused") == 0, (now, tot))
    check("P4 each copy is named with the id it copies",
          sorted((d["id"], d["same_rows_as"]) for d in dup) == sorted((f"n12-w002-g{k:08d}", f"n12-w001-g{k:08d}") for k in (1, 2, 4, 5, 6)), dup)

OUTR = WORK / "out_rnd"
pack(SR, OUTR)
RAWR = {f.stem: f.read_bytes() for f in sorted((SR / "w001" / "closed").glob("*.raw"))}
ROWS_R = sum(len(g["rows"]) for b in RAWR.values() for g in record.parse(b))

if want("P5"):
    inbox, state = WORK / "inbox_p5", WORK / "state_p5"
    deliver(OUTR, inbox, only={"w001/p000000", "w001/p000002"})
    rc, out, now, tot = receive(inbox, state)
    ask = state / "ask_again" / "w001" / "p000001.txt"
    check("P5 a dropped piece is asked for again, by name, and the gap is five game numbers",
          rc == 0 and now.get("confirmed") == 2 and now.get("asked_again") == 1 and ask.exists()
          and "not delivered" in ask.read_text(encoding="ascii") and tot.get("missing_game_numbers") == 5, (now, tot))
    deliver(OUTR, inbox)
    rc, out, now, tot = receive(inbox, state)
    check("P5 delivered later: confirmed, the request is gone, no gap, every row credited once",
          rc == 0 and now.get("confirmed") == 1 and not ask.exists() and tot.get("missing_game_numbers") == 0
          and tot.get("credited_rows") == ROWS_R and tot.get("asked_again_open") == 0, (now, tot))

if want("P6"):
    inbox, state = WORK / "inbox_p6", WORK / "state_p6"
    deliver(OUTR, inbox)
    f = inbox / "w001" / "p000001.binpack"
    good = f.read_bytes()
    f.write_bytes(good[:100] + bytes([good[100] ^ 0x10]) + good[101:])
    rc, out, now, tot = receive(inbox, state)
    why = (state / "ask_again" / "w001" / "p000001.txt")
    check("P6 one byte changed on the way: asked for again because of the checksum of the packed file",
          rc == 0 and now.get("asked_again") == 1 and why.exists() and "size and sha256 its .packed file names" in why.read_text(encoding="ascii"), (now, out))
    check("P6 nothing of that piece is credited or confirmed",
          not any(c["piece"] == "w001/p000001" for c in jl(state / "credited.jsonl")) and not (state / "confirmed" / "w001" / "p000001.confirmed").exists())
    f.write_bytes(good)
    rc, out, now, tot = receive(inbox, state)
    check("P6 the good bytes: confirmed, every row credited once", rc == 0 and now.get("confirmed") == 1 and tot.get("credited_rows") == ROWS_R, (now, tot))


def wrong_final_move(raw: bytes):
    """The piece with ONE changed move: the last row of its first game with rows gets another legal move."""
    games = record.parse(raw)
    k = next(i for i, g in enumerate(games) if g["rows"])
    _, ply, score, move, fen = games[k]["rows"][-1].split(" ", 4)
    other = sorted(m.uci() for m in chess.Board(fen).legal_moves if m.uci() != move)[0]
    games[k]["rows"][-1] = f"sg {ply} {score} {other} {fen}"
    return "".join(lines_of(g) for g in games).encode("ascii"), games[k]["id"]


if want("P7"):
    forged, victim = wrong_final_move(RAWR["p000001"])
    inbox, state = WORK / "inbox_p7a", WORK / "state_p7a"
    deliver(OUTR, inbox, only={"w001/p000000", "w001/p000002"})
    offer(inbox, "w001", "p000001", forged, raw_sha=sha(RAWR["p000001"]))
    rc, out, now, tot = receive(inbox, state)
    why = state / "ask_again" / "w001" / "p000001.txt"
    check("P7 one wrong final move, every checksum of the packed files correct: the piece is asked for again (content check)",
          rc == 0 and why.exists() and "does not have the sha256 the worker gave it" in why.read_text(encoding="ascii")
          and not any(c["piece"] == "w001/p000001" for c in jl(state / "credited.jsonl")), (now, out))
    inbox, state = WORK / "inbox_p7b", WORK / "state_p7b"
    deliver(OUTR, inbox, only={"w001/p000000", "w001/p000002"})
    offer(inbox, "w001", "p000001", forged)
    rc, out, now, tot = receive(inbox, state)
    ref = jl(state / "refused.jsonl")
    check("P7 with the piece's own sha256 forged too: exactly the changed game is refused by its binding",
          rc == 0 and [r["id"] for r in ref] == [victim] and "bind digest" in ref[0]["why"][0], ref)
    check("P7 ... and every other game of the run is credited",
          tot.get("refused") == 1 and victim not in [c["id"] for c in jl(state / "credited.jsonl")]
          and tot.get("credited_games") + tot.get("no_rows") == 11, tot)

if want("P8"):
    g = record.parse(RAW1["p000001"])
    a, b = g[0], g[1]                                           # A23's two histories, games 5 and 6
    swapped = (lines_of(dict(a, rows=b["rows"], end=b["end"])) + lines_of(dict(b, rows=a["rows"], end=a["end"]))).encode("ascii")
    inbox, state = WORK / "inbox_p8", WORK / "state_p8"
    deliver(OUT1, inbox, only={"w001/p000000"})
    offer(inbox, "w001", "p000001", swapped)
    rc, out, now, tot = receive(inbox, state, openings=OPENINGS)
    check("P8 the two results exchanged, every checksum made to fit: both games refused, neither credited",
          rc == 0 and sorted(r["id"] for r in jl(state / "refused.jsonl")) == [a["id"], b["id"]]
          and not {a["id"], b["id"]} & {c["id"] for c in jl(state / "credited.jsonl")} and tot.get("credited_games") == 3, (now, tot))
    rc, out, now, tot = receive(inbox, state, openings=OPENINGS)
    check("P8 in a later pass (the state read again from its files) they are still not credited",
          rc == 0 and tot.get("credited_games") == 3 and tot.get("refused") == 2, tot)
    whole = "".join(lines_of(x) for x in (dict(a, id=b["id"]), dict(b, id=a["id"]))).encode("ascii")
    offer(inbox, "w001", "p000001", whole)
    rc, out, now, tot = receive(inbox, state, openings=OPENINGS)
    check("P8 the two ids exchanged instead (another forged piece under the same name): refused again, nothing credited",
          rc == 0 and tot.get("credited_games") == 3 and tot.get("refused") == 4, tot)

if want("P9"):
    inbox, state = WORK / "inbox_p9", WORK / "state_p9"
    deliver(OUTR, inbox)
    rc, out, now, tot = receive(inbox, state, seed="seedB")
    ref = jl(state / "refused.jsonl")
    check("P9 another root seed at the receiver: all 12 games refused as not reserved, none credited",
          rc == 0 and tot.get("refused") == 12 and tot.get("credited_games") == 0
          and all(r["why"] == ["the opening is not the one reserved for this game id"] for r in ref), tot)

if want("P10"):
    spool, out, inbox, state = WORK / "spool_p10", WORK / "out_p10", WORK / "inbox_p10", WORK / "state_p10"
    shutil.copytree(SR, spool)
    pack(spool, out)
    deliver(out, inbox)
    rc, o, now, tot = receive(inbox, state, hold=True)
    rcp, op = pack(spool, out, confirmed=state / "confirmed")
    check("P10 confirmations held back: the pieces are checked and credited at home, the server removes nothing",
          rc == 0 and now.get("confirmed") == 3 and len(list((state / "held" / "w001").glob("*.confirmed"))) == 3
          and rcp == 0 and "removed 0" in op and len(list((spool / "w001" / "closed").glob("*.raw"))) == 3, (now, op))
    bad = WORK / "confirmed_wrong" / "w001"
    bad.mkdir(parents=True)
    (bad / "p000000.confirmed").write_text("0" * 64 + " games 5 rows 1 credited_rows 1\n", encoding="ascii")
    rcp, op = pack(spool, out, confirmed=WORK / "confirmed_wrong")
    check("P10 a confirmation that names another sha256: nothing removed, the log says so",
          rcp == 0 and "removed 0" in op and (spool / "w001" / "closed" / "p000000.raw").exists()
          and "NOTHING removed" in (out / "packer.log").read_text(encoding="utf-8"), op)
    rc, o, now, tot = receive(inbox, state)
    rcp, op = pack(spool, out, confirmed=state / "confirmed")
    check("P10 the real confirmations: all three pieces removed on the server, raw files and offered files",
          rc == 0 and now.get("delivered_again") == 3 and rcp == 0 and "removed 3" in op
          and not list((spool / "w001" / "closed").glob("*")) and not list((out / "w001").glob("*")), (now, op))
    check("P10 and at home every row is credited once", tot.get("credited_rows") == ROWS_R, tot)

if want("P11"):
    fake = WORK / "own_way_converter.py"
    fake.write_text(
        "import subprocess, sys\n"
        "from pathlib import Path\n"
        "text = sys.stdin.read()\n"
        f"p = subprocess.run([{str(CONV)!r}], input=text, capture_output=True, text=True)\n"
        "sys.stdout.write(p.stdout)\n"
        "dst = Path(text.split()[2])\n"
        "if dst.suffix == '.plain' and dst.exists():      # on the way back: the move counter of one position its own way\n"
        "    b = dst.read_bytes().split(b'\\n')\n"
        "    f = b[0].rstrip(b'\\r').split(b' ')\n"
        "    f[-1] = str(int(f[-1]) + 1).encode()\n"
        "    b[0] = b' '.join(f) + (b'\\r' if b[0].endswith(b'\\r') else b'')\n"
        "    dst.write_bytes(b'\\n'.join(b))\n"
        "sys.exit(p.returncode)\n", encoding="ascii")
    out, inbox, state = WORK / "out_p11", WORK / "inbox_p11", WORK / "state_p11"
    rcp, op = pack(S1, out, converter=fake)
    check("P11 a converter that writes one position its own way: the packer's proof catches it, both pieces travel as raw text",
          rcp == 0 and "offered 0 pieces packed and 2 as raw text" in op and "FALLBACK" in (out / "packer.log").read_text(encoding="utf-8")
          and sorted(p.name for p in (out / "w001").glob("*")) == ["p000000.packed", "p000000.raw.xz", "p000001.packed", "p000001.raw.xz"], op)
    deliver(out, inbox)
    rc, o, now, tot = receive(inbox, state, openings=OPENINGS)
    check("P11 the receiver credits the very same games as from the packed form",
          rc == 0 and sorted(c["identity"] for c in jl(state / "credited.jsonl")) == LEDGER1 and len(LEDGER1) == 5
          and tot.get("pieces_as_raw_text") == 2 and tot.get("credited_rows") == K_ROWS, tot)

if want("P12"):
    for name, change in (("bytes changed after closing", lambda b: b[:500] + bytes([b[500] ^ 1]) + b[501:]),
                         ("a record that does not carry its binding (the piece's sha256 fits)", lambda b: wrong_final_move(b)[0])):
        spool, out = WORK / f"spool_p12_{len(results)}", WORK / f"out_p12_{len(results)}"
        shutil.copytree(S1, spool)
        f = spool / "w001" / "closed" / "p000000.raw"
        f.write_bytes(change(f.read_bytes()))
        if "binding" in name:
            (spool / "w001" / "closed" / "p000000.sha256").write_text(f"{sha(f.read_bytes())}  p000000.raw\n", encoding="ascii")
        rcp, op = pack(spool, out)
        check(f"P12 the packer refuses with exit code 3 and offers nothing of it: {name}",
              rcp == 3 and "STOP" in op and not (out / "w001" / "p000000.packed").exists() and not (out / "PIECES.txt").exists(), (rcp, op))

if want("P13"):
    inbox, state = WORK / "inbox_p13", WORK / "state_p13"
    deliver(OUTR, inbox)
    rc, o, now, tot = receive(inbox, state)
    before = len(jl(state / "credited.jsonl"))
    lines = (state / "pieces.jsonl").read_text(encoding="ascii").splitlines()
    (state / "pieces.jsonl").write_text("\n".join(lines[:-1]) + "\n", encoding="ascii")   # as if cut off before the piece's line
    (state / "confirmed" / "w001" / "p000002.confirmed").unlink()
    rc, o, now, tot = receive(inbox, state)
    check("P13 a pass cut off after crediting and before the piece's line: the next pass confirms the piece and credits nothing twice",
          rc == 0 and now.get("confirmed") == 1 and now.get("credited_rows") == 0 and len(jl(state / "credited.jsonl")) == before
          and tot.get("credited_rows") == ROWS_R and tot.get("duplicates") == 0 and (state / "confirmed" / "w001" / "p000002.confirmed").exists(), (now, tot))

bad = [n for n, ok in results if not ok]
print(f"{'ALL ' + str(len(results)) + ' CHECKS PASS' if not bad else 'FAILED ' + str(len(bad)) + ' of ' + str(len(results))}"
      + (f" (only {sorted(ONLY)})" if ONLY else ""))
sys.exit(1 if bad or not results else 0)

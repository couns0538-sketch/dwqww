"""Fable 2026-11-23, W5 (d) and (e) of FINAL_PLAN_2311.md, the SERVER side: closed pieces of the workers into the
packed transfer form, proven lossless on the server before a piece is offered. Standard library only.

    packer.py --spool DIR --out DIR --converter EXE_OR_PY [--confirmed DIR] [--once] [--poll S = 5] [--until EPOCH]

For every closed piece <spool>/wNNN/closed/pNNNNNN.raw that has its checksum file and no .packed file yet:
 1 the piece's bytes must have the worker's sha256; every record must parse and carry its own bind digest
   (run/record.py). A piece that fails is NOT packed: exit code 3, the piece is named (a fault of ours or of the
   disk: nothing of it may be sent as data).
 2 the rows go into the loop's own six-line text (fen, move, score, ply, result as the side to move sees it, with
   the engine's OWN result of the end line: the PC applies the rules that correct a result, the plan's A14) and
   through the official converter into <out>/wNNN/pNNNNNN.binpack.
 3 the records WITHOUT their rows (game line, sent line, `rows N`, end line, bind line) go, compressed, into
   pNNNNNN.meta.xz (measured on 30 games: rows 1.99 bytes a row packed; this text 7.6 a row plain, 2.6 compressed:
   the end line holds the moves after the opening, which the PC needs for the rule that corrects a result).
 4 THE PROOF: the binpack is converted back, the piece is built again from the unpacked rows and the meta, and
   its sha256 must be the worker's. Then, and only then, form `binpack` is offered. If the proof fails (a
   converter that writes a position its own way), the piece is offered as form `rawxz` (the raw text, compressed)
   and the log counts it: the day never depends on the converter being exact.
 5 pNNNNNN.packed is written LAST, by a rename: sha256 and size of every offered file, the form, games, rows and
   the worker's sha256 of the raw piece. A piece without its .packed file is not there for the transport. One
   line per offered piece is appended to <out>/PIECES.txt (the receiver asks again for what is listed and missing).
 6 With --confirmed: a file <confirmed>/wNNN/pNNNNNN.confirmed whose first word is the raw piece's sha256 lets the
   packer remove that piece's raw file, checksum file and offered files. Nothing is removed without it (W5 (c)).
Exit codes: 0; 2 wrong call; 3 a piece that cannot be trusted.
"""
import argparse
import hashlib
import lzma
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def convert(converter: str, src: Path, dst: Path, secs: float = 1800.0) -> None:
    """The official converter's own command, fed on its input: `convert <src> <dst>`, both in one folder."""
    assert src.parent == dst.parent, (src, dst)
    if dst.exists():
        dst.unlink()
    cmd = [sys.executable, "-I", "-B", converter] if converter.endswith(".py") else [converter]
    p = subprocess.run(cmd, input=f"convert {src.name} {dst.name}\nquit\n", capture_output=True, text=True,
                       cwd=str(dst.parent), timeout=secs)
    if p.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError(f"convert {src.name} -> {dst.name} failed (exit {p.returncode}): {(p.stdout + p.stderr)[-400:]}")


def plain_of(games: list) -> str:
    """The loop's six-line text of every row, with the engine's own result (pipeline/nnloop/datagen_uci.py)."""
    out = []
    for g in games:
        if not g["rows"]:
            continue
        result = int(g["end"].split()[2])
        for row in g["rows"]:
            _, ply, score, move, fen = row.split(" ", 4)
            res = result if fen.split(" ", 2)[1] == "w" else -result
            out.append(f"fen {fen}\nmove {move}\nscore {score}\nply {ply}\nresult {res}\ne\n")
    return "".join(out)


def meta_of(games: list) -> str:
    return "".join(f"game {g['id']} opening {' '.join(g['opening'])}".rstrip() + f"\nsent {g['sent']}\nrows {len(g['rows'])}\n"
                   f"{g['end']}\nbind {g['bind']}\n" for g in games)


def rebuild(meta: str, plain: str) -> bytes:
    """The raw piece again, from the meta text and the unpacked six-line text. Raises ValueError when they do
    not fit together. Used here for the proof and by the receiver at home."""
    m = meta.split("\n")
    if m and m[-1] == "":
        m.pop()
    if len(m) % 5:
        raise ValueError("the meta text is not five lines a game")
    p = plain.replace("\r\n", "\n").split("\n")    # the converter on Windows writes CR LF: text is never hashed
    if p and p[-1] == "":
        p.pop()
    if len(p) % 6:
        raise ValueError("the unpacked text is not six lines a row")
    out, at = [], 0
    for k in range(0, len(m), 5):
        game, sent, rows, end, bind = m[k:k + 5]
        if not rows.startswith("rows ") or not rows[5:].isdigit():
            raise ValueError(f"meta line {k + 3} is not a row count")
        out += [game, sent]
        for _ in range(int(rows[5:])):
            r = p[at:at + 6]
            if len(r) != 6 or not (r[0].startswith("fen ") and r[1].startswith("move ") and r[2].startswith("score ")
                                   and r[3].startswith("ply ") and r[4].startswith("result ") and r[5] == "e"):
                raise ValueError(f"unpacked row at line {at + 1} is missing or not a row")
            out.append(f"sg {r[3][4:]} {r[2][6:]} {r[1][5:]} {r[0][4:]}")
            at += 6
        out += [end, bind]
    if at != len(p):
        raise ValueError(f"the unpacked text has {(len(p) - at) // 6} rows more than the meta names")
    return ("\n".join(out) + "\n").encode("ascii") if out else b""


def pack_piece(raw: Path, out: Path, converter: str, log) -> str:
    """Offers one piece; returns its form. Raises RuntimeError for a piece that cannot be trusted."""
    name = raw.stem
    want = (raw.with_suffix(".sha256")).read_text(encoding="ascii").split()[0]
    data = raw.read_bytes()
    if sha(data) != want:
        raise RuntimeError(f"{raw}: the bytes do not have the worker's sha256")
    try:
        games = record.parse(data)
    except record.RecordError as e:
        raise RuntimeError(f"{raw}: {e}") from None
    bad = [(g["id"], record.faults(g)) for g in games if record.faults(g)]
    if bad:
        raise RuntimeError(f"{raw}: {len(bad)} records do not carry their own binding, first {bad[0]}")
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob(name + ".*"):                           # what an earlier, cut-off try left (never a .packed)
        old.unlink()
    rows = sum(len(g["rows"]) for g in games)
    files, form = [], "binpack"
    meta, plain = meta_of(games), plain_of(games)
    (out / f"{name}.meta.xz").write_bytes(lzma.compress(meta.encode("ascii"), preset=6))
    if lzma.decompress((out / f"{name}.meta.xz").read_bytes()).decode("ascii") != meta:
        raise RuntimeError(f"{raw}: the compressed meta text does not come back")
    why = ""
    if rows:
        src, binp, back = out / f"{name}.tmp.plain", out / f"{name}.binpack", out / f"{name}.back.plain"
        src.write_bytes(plain.encode("ascii"))
        try:
            convert(converter, src, binp)
            convert(converter, binp, back)
            again = rebuild(meta, back.read_bytes().decode("ascii", "replace"))
            if sha(again) != want:
                why = "the piece built again from the packed rows is not the piece"
        except (RuntimeError, ValueError, subprocess.TimeoutExpired, OSError) as e:
            why = str(e)[:300]
        for f in (src, back):
            if f.exists():
                f.unlink()
    elif rebuild(meta, "") != data:
        why = "the piece built again from the meta alone is not the piece"
    if why:
        form = "rawxz"
        for f in (out / f"{name}.binpack", out / f"{name}.meta.xz"):
            if f.exists():
                f.unlink()
        (out / f"{name}.raw.xz").write_bytes(lzma.compress(data, preset=6))
        if lzma.decompress((out / f"{name}.raw.xz").read_bytes()) != data:
            raise RuntimeError(f"{raw}: the compressed copy does not give the piece back")
        files = [out / f"{name}.raw.xz"]
        log(f"{raw.parent.parent.name}/{name}: FALLBACK to the raw text ({why})")
    else:
        files = ([out / f"{name}.binpack"] if rows else []) + [out / f"{name}.meta.xz"]
    text = "".join(f"{sha(f.read_bytes())}  {f.stat().st_size}  {f.name}\n" for f in files)
    text += f"form {form} games {len(games)} rows {rows} raw_bytes {len(data)} raw_sha256 {want}\n"
    part = out / f"{name}.packed.part"
    part.write_bytes(text.encode("ascii"))
    os.replace(part, out / f"{name}.packed")
    return form


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("spool", "out", "converter"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--confirmed", default="")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--poll", type=float, default=5.0)
    ap.add_argument("--until", type=float, default=0.0)
    a = ap.parse_args()
    spool, out = Path(a.spool), Path(a.out)
    conv = str(Path(a.converter).resolve())
    if not spool.is_dir() or not Path(conv).is_file():
        print("STOP: --spool must be a folder and --converter a file")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / "packer.log", "a", encoding="utf-8", buffering=1)

    def log(text: str) -> None:
        logf.write(f"[{now()}] {text}\n")

    counts = {"binpack": 0, "rawxz": 0, "removed": 0}
    while True:
        for wd in sorted(d for d in spool.iterdir() if d.is_dir() and (d / "closed").is_dir()):
            for s in sorted((wd / "closed").glob("p*.sha256")):
                raw = s.with_suffix(".raw")
                if not raw.exists() or (out / wd.name / f"{raw.stem}.packed").exists():
                    continue
                try:
                    form = pack_piece(raw, out / wd.name, conv, log)
                except RuntimeError as e:
                    log(f"STOP: {e}")
                    print(f"packer: STOP: {e}")
                    return 3
                counts[form] += 1
                with open(out / "PIECES.txt", "ab") as f:
                    f.write(f"{wd.name}/{raw.stem} {(out / wd.name / (raw.stem + '.packed')).read_text(encoding='ascii').splitlines()[-1]}\n".encode("ascii"))
                    f.flush()
                    os.fsync(f.fileno())
                log(f"{wd.name}/{raw.stem}: offered as {form}")
        if a.confirmed and Path(a.confirmed).is_dir():
            for c in sorted(Path(a.confirmed).glob("w*/p*.confirmed")):
                w, name = c.parent.name, c.stem
                packed, raw = out / w / f"{name}.packed", spool / w / "closed" / f"{name}.raw"
                if not packed.exists() or not raw.exists():
                    continue
                words = c.read_text(encoding="ascii").split()
                if not words or words[0] != packed.read_text(encoding="ascii").split()[-1]:
                    log(f"{w}/{name}: a confirmation that does not name this piece's sha256: NOTHING removed")
                    continue
                for f in [raw, raw.with_suffix(".sha256")] + sorted((out / w).glob(name + ".*")):
                    f.unlink()
                counts["removed"] += 1
                log(f"{w}/{name}: confirmed at home, removed here")
        if a.once or (a.until and time.time() >= a.until) or (spool / "STOP_PACKER").exists():
            break
        time.sleep(a.poll)
    log(f"ended: {counts}")
    print(f"packer: offered {counts['binpack']} pieces packed and {counts['rawxz']} as raw text; removed {counts['removed']} confirmed pieces")
    return 0


if __name__ == "__main__":
    sys.exit(main())

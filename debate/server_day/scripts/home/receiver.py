"""Fable 2026-11-23, W5 (d), (e) with A23 and A11 of FINAL_PLAN_2311.md, the HOME side: what the transport
delivered is checked, built back into the workers' own pieces, and credited game by game, once.

    receiver.py --inbox DIR --state DIR --converter EXE_OR_PY --root-seed S [--openings FILE] [--hold]

It needs python-chess (the reader's OWN move rules for the reservation) and the package's run/ folder.
One call is one pass over the inbox (the packer's out folder as the transport delivered it). For every piece
wNNN/pNNNNNN that has its .packed file:
 1 every offered file has the size and sha256 the .packed file names (taken over the packed bytes, never over
   text); otherwise the piece is ASKED FOR AGAIN (state/ask_again/wNNN/pNNNNNN.txt says why).
 2 the worker's raw piece is built again (binpack through the official converter + the meta text; or the
   compressed raw text of the packer's fallback) and must have the sha256 the WORKER gave it when it closed the
   piece; games and rows as named. Otherwise: asked for again. So the content check does not rest on the
   packed files' own checksums: a copy with one changed move and correct checksums fails here.
 3 every game: its bind digest; its sent line against its own opening; and its opening against the
   RESERVATION this reader computes by itself from the root seed and the game id with a rules library (with
   --openings: from that file by the game's number). A game that fails is REFUSED (state/refused.jsonl), never
   credited; the piece is still confirmed (sending it again cannot cure it), the number is reported.
 4 credit: a game's identity is the sha256 of its ordered five-field rows (position, move, score, ply, result).
   A game whose identity is already in the ledger is not credited again (the same piece delivered twice, a
   retry, the same payload under another id): state/duplicates.jsonl. One game id with two different row sets
   is refused. Credited games: state/credited.jsonl, one line each.
 5 the built-again piece is kept in state/raw/ (the input of the step that applies the loop's own after-game
   rule and writes the round files), the piece gets its line in state/pieces.jsonl, and LAST its confirmation
   state/confirmed/wNNN/pNNNNNN.confirmed (first word: the raw piece's sha256), which lets the server remove
   the piece. With --hold the confirmation goes to state/held/ instead: the server must then keep the piece.
 6 pieces that <inbox>/PIECES.txt lists and that are not there are asked for again; for every worker the game
   numbers seen so far are checked for gaps (A11: what is missing is reported as a number).
The ledger files are the state: a second pass, also after this program was ended in the middle, reads them first.
Exit codes: 0 a pass was done (the numbers are printed and in state/summary.json); 2 wrong call; 3 the state
cannot be read.
"""
import argparse
import hashlib
import json
import lzma
import os
import shutil
import sys
import time
from pathlib import Path

RUN = Path(__file__).resolve().parent.parent / "run"
sys.path.insert(0, str(RUN))
import packer  # noqa: E402
import record  # noqa: E402

try:
    import chess
except ImportError:
    chess = None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reserve(root_seed: str, gid: str) -> list:
    """The opening of a game id, computed here a second time with other move rules than the engine's."""
    board, moves = chess.Board(), []
    for ply in range(8):
        legal = sorted(m.uci() for m in board.legal_moves)
        if not legal:
            break
        pick = int.from_bytes(hashlib.sha256(f"{root_seed}|{gid}|{ply}".encode("ascii")).digest()[:8], "big") % len(legal)
        moves.append(legal[pick])
        board.push_uci(legal[pick])
    return moves


def append(path: Path, obj: dict) -> None:
    with open(path, "ab") as f:
        f.write((json.dumps(obj, sort_keys=True) + "\n").encode("ascii"))
        f.flush()
        os.fsync(f.fileno())


def lines_of(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    for n, ln in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        try:
            out.append(json.loads(ln))
        except ValueError:
            raise SystemExit(f"STOP: {path} line {n} cannot be read") from None
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("inbox", "state", "converter", "root-seed"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--openings", default="")
    ap.add_argument("--hold", action="store_true")
    a = ap.parse_args()
    inbox, state = Path(a.inbox), Path(a.state)
    conv = str(Path(a.converter).resolve())
    if chess is None or not inbox.is_dir() or not Path(conv).is_file():
        print("STOP: the receiver needs python-chess, --inbox as a folder and --converter as a file")
        return 2
    fixed = [ln.split() for ln in Path(a.openings).read_text(encoding="ascii").splitlines() if ln.strip()] if a.openings else None
    state.mkdir(parents=True, exist_ok=True)
    try:
        credited, pieces = lines_of(state / "credited.jsonl"), lines_of(state / "pieces.jsonl")
    except SystemExit as e:
        print(e)
        return 3
    by_identity = {c["identity"]: c["id"] for c in credited}
    by_id = {c["id"]: c["identity"] for c in credited}
    rows_total = sum(c["rows"] for c in credited)             # from the ledger: a pass cut off in the middle loses nothing
    done = {p["piece"]: p for p in pieces}
    seen = {}                                                   # run-wNNN -> set of game numbers in confirmed pieces
    for p in pieces:
        for gid in p["ids"]:
            seen.setdefault(gid[:-10], set()).add(int(gid[-8:]))
    now = {"confirmed": 0, "delivered_again": 0, "asked_again": 0, "credited_games": 0, "credited_rows": 0,
           "duplicates": 0, "refused": 0, "no_rows": 0}

    def ask(key: str, why: str) -> None:
        f = state / "ask_again" / (key + ".txt")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {why}\n", encoding="ascii")
        now["asked_again"] += 1

    def confirm(key: str, p: dict) -> None:
        f = state / ("held" if a.hold else "confirmed") / (key + ".confirmed")
        f.parent.mkdir(parents=True, exist_ok=True)
        part = f.with_suffix(".part")
        part.write_text(f"{p['raw_sha256']} games {p['games']} rows {p['rows']} credited_rows {p['credited_rows']}\n", encoding="ascii")
        os.replace(part, f)
        (state / "ask_again" / (key + ".txt")).unlink(missing_ok=True)

    for packed in sorted(inbox.glob("w*/p*.packed")):
        key = f"{packed.parent.name}/{packed.stem}"
        try:
            text = packed.read_text(encoding="ascii").splitlines()
            last = text[-1].split()
            form, games, rows, raw_bytes, raw_sha = last[1], int(last[3]), int(last[5]), int(last[7]), last[9]
            files = [(ln.split()[0], int(ln.split()[1]), ln.split()[2]) for ln in text[:-1]]
            assert last[0] == "form" and form in ("binpack", "rawxz") and len(raw_sha) == 64
        except (ValueError, IndexError, AssertionError, UnicodeDecodeError):
            ask(key, "the .packed file cannot be read")
            continue
        if key in done and done[key]["raw_sha256"] == raw_sha:
            confirm(key, done[key])                             # the same piece again: credited once, confirmed again
            now["delivered_again"] += 1
            continue
        why = ""
        for want, size, name in files:
            f = packed.parent / name
            if "/" in name or "\\" in name or not f.is_file() or f.stat().st_size != size or sha(f.read_bytes()) != want:
                why = f"{name} is missing or does not have the size and sha256 its .packed file names"
                break
        raw = b""
        if not why:
            try:
                names = [n for _, _, n in files]
                if form == "rawxz":
                    raw = lzma.decompress((packed.parent / f"{packed.stem}.raw.xz").read_bytes())
                else:
                    meta = lzma.decompress((packed.parent / f"{packed.stem}.meta.xz").read_bytes()).decode("ascii")
                    plain = ""
                    if f"{packed.stem}.binpack" in names:
                        work = state / "work" / packed.parent.name
                        work.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(packed.parent / f"{packed.stem}.binpack", work / f"{packed.stem}.binpack")
                        packer.convert(conv, work / f"{packed.stem}.binpack", work / f"{packed.stem}.plain")
                        plain = (work / f"{packed.stem}.plain").read_bytes().decode("ascii", "replace")
                        for f in work.glob(packed.stem + ".*"):
                            f.unlink()
                    raw = packer.rebuild(meta, plain)
            except (lzma.LZMAError, ValueError, RuntimeError, OSError, UnicodeDecodeError) as e:
                why = f"the piece cannot be built again: {str(e)[:200]}"
        if not why and (len(raw) != raw_bytes or sha(raw) != raw_sha):
            why = "the piece built again does not have the sha256 the worker gave it"
        recs = []
        if not why:
            try:
                recs = record.parse(raw)
            except record.RecordError as e:
                why = f"the piece built again is not a sequence of records: {e}"
        if not why and (len(recs) != games or sum(len(g["rows"]) for g in recs) != rows):
            why = "games or rows are not as the .packed file names them"
        if why:
            ask(key, why)
            continue
        p = {"piece": key, "raw_sha256": raw_sha, "form": form, "games": games, "rows": rows, "ids": [g["id"] for g in recs],
             "credited_games": 0, "credited_rows": 0, "duplicates": 0, "refused": 0, "no_rows": 0, "seen_again": 0}
        for g in recs:
            gid = g["id"]
            n = int(gid[-8:])
            bad = record.faults(g, fixed[(n - 1) % len(fixed)] if fixed else reserve(a.root_seed, gid))
            identity = sha(packer.plain_of([g]).encode("ascii")) if g["rows"] else ""
            if not bad and gid in by_id and by_id[gid] != identity:
                bad = ["this game id was credited before with other rows"]
            if bad:
                append(state / "refused.jsonl", {"id": gid, "piece": key, "why": bad})
                p["refused"] += 1
            elif not g["rows"]:
                p["no_rows"] += 1                               # keeps its id; nothing to credit
            elif identity in by_identity:
                if by_identity[identity] != gid:                # another id with the same rows: a copy
                    append(state / "duplicates.jsonl", {"id": gid, "piece": key, "same_rows_as": by_identity[identity]})
                    p["duplicates"] += 1
                else:                                           # this very game again (a pass that was cut off)
                    p["seen_again"] += 1
            else:
                t = g["end"].split()
                append(state / "credited.jsonl", {"identity": identity, "id": gid, "piece": key, "rows": len(g["rows"]),
                                                  "result": int(t[2]), "reason": t[4], "plies": int(t[6])})
                by_identity[identity], by_id[gid] = gid, identity
                p["credited_games"] += 1
                p["credited_rows"] += len(g["rows"])
                rows_total += len(g["rows"])
            seen.setdefault(gid[:-10], set()).add(n)
        keep = state / "raw" / (key + ".raw")
        keep.parent.mkdir(parents=True, exist_ok=True)
        keep.write_bytes(raw)
        append(state / "pieces.jsonl", p)
        done[key] = p
        confirm(key, p)
        now["confirmed"] += 1
        for k in ("credited_games", "credited_rows", "duplicates", "refused", "no_rows"):
            now[k] += p[k]

    listed = set()
    if (inbox / "PIECES.txt").exists():
        listed = {ln.split()[0] for ln in (inbox / "PIECES.txt").read_text(encoding="ascii").splitlines() if ln.strip()}
    missing_pieces = sorted(k for k in listed if k not in done and not (state / "ask_again" / (k + ".txt")).exists())
    for k in missing_pieces:
        ask(k, "listed by the server and not delivered")
    allp = list(done.values())
    total = {"pieces_confirmed": len(allp), "credited_games": len(by_identity),
             "credited_rows": rows_total, "duplicates": len(lines_of(state / "duplicates.jsonl")),
             "refused": len(lines_of(state / "refused.jsonl")), "no_rows": sum(p["no_rows"] for p in allp),
             "asked_again_open": len(list((state / "ask_again").glob("w*/*.txt"))) if (state / "ask_again").is_dir() else 0,
             "missing_game_numbers": sum(max(s) - len(s) for s in seen.values()),
             "pieces_as_raw_text": sum(p["form"] == "rawxz" for p in allp)}
    (state / "summary.json").write_text(json.dumps({"this_pass": now, "in_all": total}, indent=1, sort_keys=True) + "\n", encoding="ascii")
    print(f"receiver: this pass {now}")
    print(f"receiver: in all {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

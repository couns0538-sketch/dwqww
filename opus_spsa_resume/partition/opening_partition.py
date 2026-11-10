"""opening_partition.py - freeze train / screen / holdout opening partitions of 8moves_v3 BEFORE any fitting.

usage: python -I -B opening_partition.py <book.pgn> <book_sha256> <out_dir> <manifest.json> [--uho <uho.epd> <uho_sha256>]
                                         [--created "<Vienna time>"]
Rule (deterministic, order-independent):
  * every game block of the book (split at '[Event ') is replayed with python-chess (external GPL-3.0 dependency,
    unmodified, see IDEA_SOURCE.md); its final position key = board.epd() (pieces, side, castling, legal e.p.);
  * a key seen before (transposition or duplicate) is dropped at its later occurrences, so no position can be in two
    partitions; blocks that do not parse are dropped and listed;
  * bucket = int(sha256(key)[:8], 16) % 100: train 0-69, screen 70-79, holdout G1 80-86, G2 87-93, G3 94-99;
  * each partition file is the byte-exact concatenation of its original blocks in book order; a .keys file lists its
    position keys (sorted). The manifest records counts and sha256 of every file, the pairwise-disjointness check,
    and (with --uho) how many keys of each partition also occur in QA's UHO book, compared on pieces/side/castling
    (conservative: e.p. ignored, so a match may over-count).
Writes only into <out_dir> (refuses existing files) and the manifest path (refuses to overwrite)."""
import hashlib
import io
import json
import sys
from pathlib import Path

import chess
import chess.pgn

BUCKETS = [("train", 0, 70), ("screen", 70, 80), ("holdout_G1", 80, 87), ("holdout_G2", 87, 94),
           ("holdout_G3", 94, 100)]


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main(argv):
    if len(argv) < 5:
        raise SystemExit(__doc__)
    book, book_sha, out_dir, manifest = Path(argv[1]), argv[2].lower(), Path(argv[3]), Path(argv[4])
    uho = uho_sha = None
    if "--uho" in argv:
        i = argv.index("--uho")
        uho, uho_sha = Path(argv[i + 1]), argv[i + 2].lower()
    created = argv[argv.index("--created") + 1] if "--created" in argv else None
    data = book.read_bytes()
    if sha_bytes(data) != book_sha:
        raise SystemExit(f"book sha256 {sha_bytes(data)} != pinned {book_sha}")
    if manifest.exists():
        raise SystemExit(f"refusing to overwrite {manifest}")
    out_dir.mkdir(parents=True, exist_ok=True)
    text = data.decode("utf-8")
    pieces = text.split("[Event ")
    head, blocks = pieces[0], ["[Event " + b for b in pieces[1:]]
    seen, dropped_dup, bad = {}, [], []
    parts = {name: [] for name, _, _ in BUCKETS}
    for idx, block in enumerate(blocks):
        try:
            game = chess.pgn.read_game(io.StringIO(block))
            if game is None or game.errors:
                raise ValueError(str(game.errors[:1]) if game is not None else "empty")
            board = game.end().board()
            key = board.epd()
        except Exception as e:  # noqa: BLE001 - every unparsable block is reported, never guessed
            bad.append({"index": idx, "error": str(e)[:120]})
            continue
        if key in seen:
            dropped_dup.append({"index": idx, "first": seen[key]})
            continue
        seen[key] = idx
        b = int(sha_bytes(key.encode("ascii"))[:8], 16) % 100
        for name, lo, hi in BUCKETS:
            if lo <= b < hi:
                parts[name].append((idx, key, block))
                break
    files = {}
    keysets = {}
    for name, _, _ in BUCKETS:
        pgn_path, keys_path = out_dir / f"{name}.pgn", out_dir / f"{name}.keys"
        for p in (pgn_path, keys_path):
            if p.exists():
                raise SystemExit(f"refusing to overwrite {p}")
        body = "".join(blk for _, _, blk in parts[name]).encode("utf-8")
        pgn_path.write_bytes(body)
        keys = sorted(k for _, k, _ in parts[name])
        keys_path.write_bytes(("\n".join(keys) + "\n").encode("ascii"))
        keysets[name] = set(keys)
        files[name] = {"pgn": pgn_path.name, "count": len(parts[name]), "pgn_sha256": sha_bytes(body),
                       "keys": keys_path.name, "keys_sha256": sha_bytes(keys_path.read_bytes()),
                       "first_book_index": parts[name][0][0] if parts[name] else None}
    names = [n for n, _, _ in BUCKETS]
    disjoint = all(not (keysets[a] & keysets[b]) for i, a in enumerate(names) for b in names[i + 1:])
    out = {"schema": "opus3-partition/1", "created_vienna": created, "book": str(book), "book_sha256": book_sha,
           "book_blocks": len(blocks), "book_header_bytes": len(head), "python_chess": chess.__version__,
           "rule": "key = python-chess board.epd() of the final position; later duplicates dropped; "
                   "bucket = int(sha256(key)[:8],16) % 100; train 0-69, screen 70-79, holdout_G1 80-86, "
                   "holdout_G2 87-93, holdout_G3 94-99; files keep book order and original bytes",
           "unique_positions": len(seen), "dropped_duplicates": len(dropped_dup), "unparsable": bad,
           "partitions": files, "pairwise_disjoint": disjoint}
    if uho is not None:
        ud = uho.read_bytes()
        if sha_bytes(ud) != uho_sha:
            raise SystemExit(f"UHO sha256 {sha_bytes(ud)} != pinned {uho_sha}")
        short = {name: {" ".join(k.split()[:3]) for k in keysets[name]} for name in names}
        hits = {name: 0 for name in names}
        lines = 0
        for line in ud.decode("ascii", "replace").splitlines():
            f = line.split()
            if len(f) < 3:
                continue
            lines += 1
            k3 = " ".join(f[:3])
            for name in names:
                if k3 in short[name]:
                    hits[name] += 1
        out["uho_overlap"] = {"uho": str(uho), "uho_sha256": uho_sha, "uho_lines": lines,
                              "compare": "pieces side castling (e.p. ignored: conservative)",
                              "uho_lines_matching_a_partition_key": hits}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(out, indent=1) + "\n", encoding="ascii")
    print(json.dumps({k: v for k, v in out.items() if k != "unparsable"} | {"unparsable": len(bad)}, indent=1))
    return 0 if disjoint else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

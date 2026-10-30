"""R8: global de-duplication of forge_selfplay_fast output against forge_selfplay.py hash databases. The live
database is only ever READ (sqlite ?mode=ro&immutable=1: no locks, no -wal/-shm access, nothing written).

usage 1 (v5, run by the driver after every finished shard; safe to run again):
  python -I -B dedup_against_db.py --shard <dir>\\<prefix>_NNN --live-db <forge_seen_hashes.sqlite3|none> --own-db <own.sqlite3>
  reads <base>.txt (and <base>.pos when it exists), writes <base>.dedup.txt, <base>.dedup.pos + .dedup.pos.info (when
  there is a .pos) and, last, <base>.dedup.json (the completion marker). A position is dropped when it is in the live
  DB, in the own DB from another shard, or earlier in the same shard; the kept keys go into the own DB (table hashes,
  with the shard id), so later shards of the driver are checked against earlier ones. The own DB is written only by
  this tool, one shard at a time (the driver runs post-steps one after another). Outputs are written as .part files
  and renamed; an existing output is never replaced. Exit 0 = done or already done, 3 = bad input, 4 = refused.
usage 2 (R8, ad hoc):
  python -I -B dedup_against_db.py <forge_seen_hashes.sqlite3> <out.txt> <in.txt> [<in2.txt> ...] [--count-only]
  A line is kept when its key is neither in the database nor already kept in this run; --count-only measures the
  duplicate rate without writing <out.txt>. Prints lines read, kept, duplicates vs the database and inside the input.
Key = blake2b-128 of the first four FEN fields, exactly forge_selfplay.position_hash(). With immutable=1, rows that
are still only in the live DB's WAL are not seen, and the file must not change while it is read: when the live
pipeline runs at the same time a lookup can fail (exit 3; the driver retries the shard on --resume)."""
import hashlib
import json
import os
import sqlite3
import struct
import sys
import time
from array import array
from pathlib import Path


def position_key(fen_bytes):
    return hashlib.blake2b(b" ".join(fen_bytes.split()[:4]), digest_size=16).digest()


def open_live(path):
    uri = Path(path).resolve().as_uri() + "?mode=ro&immutable=1"
    con = sqlite3.connect(uri, uri=True)
    con.execute("PRAGMA query_only=1")
    return con


def publish(part, final):
    os.rename(part, final)  # Windows: fails if final exists (never replaces)


def write_part(path, data):
    with open(path, "wb") as f:  # the tool's own temp file: rewritten by a retry
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def shard_mode(base, live_db, own_db):
    txt, pos = base + ".txt", base + ".pos"
    out_txt, out_pos, out_info, done = base + ".dedup.txt", base + ".dedup.pos", base + ".dedup.pos.info", base + ".dedup.json"
    if os.path.exists(done):
        print(f"{done} exists: already done")
        return 0
    stale = [p for p in (out_txt, out_pos, out_info) if os.path.exists(p)]
    if stale:
        print(f"REFUSED: {stale} exist without {done} (killed between renames?): check them, then rename them away")
        return 4
    if not os.path.exists(txt):
        print(f"ERROR: {txt} not found")
        return 3
    t0 = time.time()
    live = None if live_db.lower() == "none" else open_live(live_db)
    own = sqlite3.connect(own_db)
    own.execute("PRAGMA journal_mode=WAL")
    own.execute("PRAGMA synchronous=FULL")
    own.executescript("""
        CREATE TABLE IF NOT EXISTS shards (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS hashes (hash BLOB PRIMARY KEY, shard INTEGER NOT NULL) WITHOUT ROWID;
    """)
    name = os.path.basename(base)
    with own:
        own.execute("INSERT OR IGNORE INTO shards(name) VALUES (?)", (name,))
    sid = own.execute("SELECT id FROM shards WHERE name = ?", (name,)).fetchone()[0]
    seen, keep = set(), array("L")
    read = dup_live = dup_own = dup_self = 0
    with open(txt, "rb") as f, open(out_txt + ".part", "wb") as w:  # the .part is the tool's own temp file
        for raw in f:
            if not raw.endswith(b"\n"):
                print(f"ERROR: unterminated last line in {txt}")
                return 3
            key = position_key(raw.split(b"|", 1)[0].strip())
            if key in seen:
                dup_self += 1
            elif live is not None and live.execute("SELECT 1 FROM hashes WHERE hash = ?", (key,)).fetchone():
                dup_live += 1
            else:
                row = own.execute("SELECT shard FROM hashes WHERE hash = ?", (key,)).fetchone()
                if row is not None and row[0] != sid:  # rows of this shard itself come from an earlier, killed attempt
                    dup_own += 1
                else:
                    seen.add(key)
                    keep.append(read)
                    w.write(raw)
            read += 1
        w.flush()
        os.fsync(w.fileno())
    have_pos = os.path.exists(pos)
    if have_pos:
        data = Path(pos).read_bytes()
        magic, ver, n = struct.unpack_from("<4sIQ", data, 0)
        if magic != b"FPOS" or ver != 1 or n != read or len(data) != 16 + 35 * n:
            print(f"ERROR: {pos} is not an FPOS v1 file with the text's {read} records (n={n}, {len(data)} bytes)")
            return 3
        b0, s0, m0 = 16, 16 + 32 * n, 16 + 34 * n
        boards = b"".join(data[b0 + 32 * i:b0 + 32 * i + 32] for i in keep)
        scores = b"".join(data[s0 + 2 * i:s0 + 2 * i + 2] for i in keep)
        metas = bytes(data[m0 + i] for i in keep)
        write_part(out_pos + ".part", struct.pack("<4sIQ", b"FPOS", 1, len(keep)) + boards + scores + metas)
        data = boards = scores = metas = None
    with own:  # one transaction: the kept keys of this shard
        own.executemany("INSERT OR IGNORE INTO hashes(hash, shard) VALUES (?, ?)", ((k, sid) for k in seen))
    own.close()
    if live is not None:
        live.close()
    if have_pos:
        info = (f"source={out_txt}\nlines={len(keep)}\nrecords={len(keep)}\nbad=0\n"
                f"dedup_of={pos}\nglobal_dedup=live DB {live_db} + own DB {own_db}\n")
        write_part(out_info + ".part", info.encode("ascii"))
        publish(out_pos + ".part", out_pos)
        publish(out_info + ".part", out_info)
    publish(out_txt + ".part", out_txt)
    el = time.time() - t0
    live_stat = None if live is None else {"path": live_db, "bytes": os.path.getsize(live_db),
                                           "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(live_db)))}
    summary = {"shard": name, "txt": txt, "pos": pos if have_pos else None, "read": read, "kept": len(keep),
               "dup_live": dup_live, "dup_own": dup_own, "dup_self": dup_self, "seconds": round(el, 1),
               "live_db": live_stat, "own_db": own_db, "tool": "dedup_against_db.py --shard (R8 v5)"}
    write_part(done + ".part", (json.dumps(summary, indent=1) + "\n").encode("ascii"))
    publish(done + ".part", done)
    print(f"{name}: read {read}, kept {len(keep)}, duplicates: live DB {dup_live}, own DB {dup_own}, inside {dup_self}; "
          f"{el:.1f} s")
    return 0


def adhoc_mode(argv):
    db_path, out_path = argv[1], argv[2]
    inputs = [a for a in argv[3:] if not a.startswith("--")]
    count_only = "--count-only" in argv
    con = open_live(db_path)
    seen = set()
    read = kept = dup_db = dup_self = 0
    t0 = time.time()
    out = None if count_only else open(out_path, "x", encoding="ascii", newline="\n")
    for fn in inputs:
        with open(fn, encoding="ascii") as f:
            for line in f:
                read += 1
                fen = line.split("|", 1)[0].strip()
                key = hashlib.blake2b(" ".join(fen.split()[:4]).encode("ascii"), digest_size=16).digest()
                if key in seen:
                    dup_self += 1
                    continue
                if con.execute("SELECT 1 FROM hashes WHERE hash = ?", (key,)).fetchone() is not None:
                    dup_db += 1
                    continue
                seen.add(key)
                kept += 1
                if out:
                    out.write(line)
    if out:
        out.close()
    con.close()
    el = time.time() - t0
    print(f"read {read}, kept {kept}, duplicates vs database {dup_db} ({100 * dup_db / max(read, 1):.2f}%), "
          f"duplicates inside the input {dup_self}; {el:.1f} s ({read / max(el, 1e-9):.0f} lines/s)")
    return 0


if __name__ == "__main__":
    a = sys.argv
    if "--shard" in a:
        def arg(name):
            return a[a.index(name) + 1]
        sys.exit(shard_mode(arg("--shard"), arg("--live-db"), arg("--own-db")))
    if len(a) < 4:
        raise SystemExit(__doc__)
    sys.exit(adhoc_mode(a))

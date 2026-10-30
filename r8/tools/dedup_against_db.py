"""R8: global de-duplication of forge_selfplay_fast output against a forge_selfplay.py hash database, READ ONLY.
usage: python -I -B dedup_against_db.py <forge_seen_hashes.sqlite3> <out.txt> <in.txt> [<in2.txt> ...] [--count-only]
Key = blake2b-128 of the first four FEN fields, exactly forge_selfplay.position_hash(). A line is kept when its key
is neither in the database nor already kept in this run. The database is opened with ?mode=ro&immutable=1: no
locks, no -wal/-shm access, nothing is ever written to it (the live pipeline is not affected; rows still only in
its WAL are not seen). --count-only measures the duplicate rate without writing <out.txt>.
Prints lines read, kept, duplicates vs the database and inside the input."""
import hashlib
import sqlite3
import sys
import time

db_path, out_path = sys.argv[1], sys.argv[2]
inputs = [a for a in sys.argv[3:] if not a.startswith("--")]
count_only = "--count-only" in sys.argv
uri = "file:" + db_path.replace("\\", "/") + "?mode=ro&immutable=1"
con = sqlite3.connect(uri, uri=True)
con.execute("PRAGMA query_only=1")
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

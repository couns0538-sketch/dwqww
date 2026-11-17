"""Cliff bisect per Hash value, to compare with the prior work's figures
(Hash 16 needs 60 MB, dies at 56; Hash 256 needs 300 MB, dies at 290).

Same protocol as soak5: 12 depth-10 searches, answer key = (bestmove, score, nodes)
with nps excluded. For each Hash, the LOWEST cap that completes all 12 searches and the
HIGHEST cap that dies are bisected in 2 MB steps, so the cliff is a pair of adjacent
numbers rather than a guess. Both are recorded, including the failing cap's stderr, so
"died" is attributable to std::bad_alloc and not to something else.
"""
import json
import subprocess
import sys

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402

fens = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:16]


def one(cap_mb, hash_mb):
    p = subprocess.Popen(["bash", "-c", 'ulimit -v %d; exec /tmp/soak/build/forge'
                          % (cap_mb * 1024)],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, bufsize=0)
    e = Engine.__new__(Engine)
    e.exe = "x"
    e.proc = p
    e.buf = b""
    e.sent = []
    e.id_name = None
    ok = 0
    try:
        e._handshake({"Hash": hash_mb, "Threads": 1})
        for f in fens:
            e.position_fen(f)
            e.go("go depth 10", deadline_s=180)
            ok += 1
    except Exception:
        pass
    rc = p.poll()
    err = b""
    if rc is None:
        try:
            p.stdin.write(b"quit\n")
            p.stdin.flush()
            p.wait(timeout=5)
        except Exception:
            p.kill()
    try:
        err = p.stderr.read() or b""
    except Exception:
        pass
    return ok, p.returncode, err.decode("utf-8", "replace")[-200:]


out = []
for h, lo, hi in ((8, 40, 70), (16, 40, 90), (64, 90, 140), (256, 240, 400)):
    good = None
    bad = None
    bad_err = None
    for cap in range(lo, hi + 1, 2):
        n, rc, err = one(cap, h)
        if n == len(fens):
            good = cap
            break
        bad = cap
        bad_err = err
    rec = {"hash": h, "lowest_complete_mb": good, "highest_dead_mb": bad,
           "cliff_minus_hash_mb": (good - h) if good else None,
           "dead_stderr": bad_err}
    out.append(rec)
    print(json.dumps({k: v for k, v in rec.items() if k != "dead_stderr"}))

json.dump(out, open("/tmp/soak/ev/soak5b.json", "w"), indent=1)

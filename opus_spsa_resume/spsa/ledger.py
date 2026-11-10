"""ledger.py - append-only hash-chained ledger, atomic versioned checkpoints, identity hashing and crash hooks.

Ledger (<run>/ledger.jsonl): one canonical-JSON record per line,
  {"v":1, "seq":n, "type":..., "run_id":..., "prev":<h of record n-1 or "genesis">, ...payload..., "h":<sha256>}
where h = sha256 of the canonical JSON of the record without "h". Records carry no wall-clock time, so a resumed run
writes the same bytes as an uninterrupted one. Verification refuses: a bad hash, a broken chain or sequence, a
malformed line, a record of another run. The only tolerated damage is an unterminated last line (a write cut off by
a crash): if it parses and verifies it is kept (newline added); otherwise its bytes are moved to
ledger.torn.<n>.bin and the run continues from the last good record.
Checkpoints (<run>/ckpt/ckpt_<seq:06d>.json, <run>/HEAD.json): written as tmp + flush + fsync + os.replace; HEAD
names the newest checkpoint and its sha256; every checkpoint names its predecessor's sha256. The ledger is the
source of truth; a checkpoint is a verified summary of a ledger prefix (records count and head hash).
Crash hooks: OPUS3_CRASH_AT="<boundary>@<batch>[:<j>]" makes the process exit with code 77 at that point."""
import hashlib
import json
import os
import time
from pathlib import Path

EXIT_CONFIG = 10
EXIT_CONFIG_CHANGED = 11
EXIT_IDENTITY = 20
EXIT_CORRUPT = 30
EXIT_RESULTS = 31
EXIT_LIVE_GUARD = 40
EXIT_HOLDOUT = 41
EXIT_CRASH = 77


class Refuse(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_retry(src, dst, tries=120):
    """os.replace with bounded retries: on Windows another process (virus scanner, indexer) may hold the target open
    for a moment, which makes the rename fail with PermissionError. Gives up after about 30 s and re-raises."""
    for i in range(tries):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if i == tries - 1:
                raise
            time.sleep(min(0.05 * (i + 1), 0.5))


def write_atomic(path, data, crash=None):
    """tmp + flush + fsync + os.replace. `crash`, if given, is called between the steps with "tmp" and "renamed"."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    if crash:
        crash("tmp")
    replace_retry(tmp, path)
    if crash:
        crash("renamed")


# --- crash hooks (tests only) ------------------------------------------------------------------------------------
def crash_spec():
    raw = os.environ.get("OPUS3_CRASH_AT", "")
    if not raw:
        return None
    b, _, rest = raw.partition("@")
    batch, _, j = rest.partition(":")
    return b, int(batch) if batch else None, int(j) if j else None


def crash_point(boundary, batch=None, j=None):
    spec = crash_spec()
    if not spec:
        return
    b, sb, sj = spec
    if b == boundary and (sb is None or sb == batch) and (sj is None or sj == j):
        os._exit(EXIT_CRASH)


# --- ledger ------------------------------------------------------------------------------------------------------
class Ledger:
    def __init__(self, run_dir, run_id):
        self.dir = Path(run_dir)
        self.path = self.dir / "ledger.jsonl"
        self.run_id = run_id
        self.records = []
        self.repairs = []

    @property
    def head(self):
        return self.records[-1]["h"] if self.records else "genesis"

    def load(self, readonly=False):
        """Verify the whole ledger. A damaged unterminated last line is repaired only when readonly is False."""
        self.records = []
        if not self.path.exists():
            return self
        raw = self.path.read_bytes()
        lines = raw.split(b"\n")
        tail = lines.pop()  # b"" when the file ends with a newline
        for n, line in enumerate(lines):
            self.records.append(self._verify(line, n))
        if tail and readonly:
            raise Refuse(EXIT_CORRUPT, "ledger has an unterminated last line (a resume repairs it; read-only does not)")
        if tail:
            try:
                rec = self._verify(tail, len(lines))
            except Refuse:
                k = len(list(self.dir.glob("ledger.torn.*.bin")))
                torn = self.dir / f"ledger.torn.{k}.bin"
                torn.write_bytes(tail)
                with open(self.path, "r+b") as f:
                    f.truncate(len(raw) - len(tail))
                    f.flush()
                    os.fsync(f.fileno())
                self.repairs.append({"torn_bytes": len(tail), "sha256": sha256_bytes(tail), "kept_as": torn.name})
            else:
                self.records.append(rec)
                with open(self.path, "ab") as f:
                    f.write(b"\n")
                    f.flush()
                    os.fsync(f.fileno())
        return self

    def _verify(self, line, n):
        try:
            rec = json.loads(line.decode("ascii"))
        except (UnicodeDecodeError, ValueError):
            raise Refuse(EXIT_CORRUPT, f"ledger line {n + 1} is malformed")
        if not isinstance(rec, dict) or "h" not in rec:
            raise Refuse(EXIT_CORRUPT, f"ledger line {n + 1} has no hash")
        body = {k: v for k, v in rec.items() if k != "h"}
        if sha256_bytes(canon(body)) != rec["h"] or canon(rec) != line:
            raise Refuse(EXIT_CORRUPT, f"ledger line {n + 1}: hash or encoding mismatch")
        prev = self.records[-1]["h"] if self.records else "genesis"
        if rec.get("seq") != n or rec.get("prev") != prev:
            raise Refuse(EXIT_CORRUPT, f"ledger line {n + 1}: broken sequence or chain")
        if rec.get("run_id") != self.run_id:
            raise Refuse(EXIT_RESULTS, f"ledger line {n + 1} belongs to run {rec.get('run_id')} (stale)")
        return rec

    def append(self, rtype, payload):
        rec = {"v": 1, "seq": len(self.records), "type": rtype, "run_id": self.run_id, "prev": self.head}
        for k, v in payload.items():
            if k in rec or k == "h":
                raise ValueError(f"reserved ledger key {k}")
            rec[k] = v
        rec["h"] = sha256_bytes(canon(rec))
        with open(self.path, "ab") as f:
            f.write(canon(rec) + b"\n")
            f.flush()
            os.fsync(f.fileno())
        self.records.append(rec)
        return rec


# --- checkpoints -------------------------------------------------------------------------------------------------
class Checkpoints:
    def __init__(self, run_dir):
        self.dir = Path(run_dir) / "ckpt"
        self.head_path = Path(run_dir) / "HEAD.json"

    def files(self):
        return sorted(self.dir.glob("ckpt_*.json"))

    def read(self, seq):
        p = self.dir / f"ckpt_{seq:06d}.json"
        data = p.read_bytes()
        try:
            obj = json.loads(data.decode("ascii"))
        except (UnicodeDecodeError, ValueError):
            raise Refuse(EXIT_CORRUPT, f"{p.name} is malformed")
        if canon(obj) != data:
            raise Refuse(EXIT_CORRUPT, f"{p.name} is not canonical")
        return obj, sha256_bytes(data)

    def head(self):
        """(seq, checkpoint, sha256) named by HEAD.json; None when HEAD.json was never written."""
        if not self.head_path.exists():
            return None
        try:
            h = json.loads(self.head_path.read_bytes().decode("ascii"))
            seq, want = int(h["seq"]), h["sha256"]
        except (UnicodeDecodeError, ValueError, KeyError, TypeError):
            raise Refuse(EXIT_CORRUPT, "HEAD.json is malformed")
        obj, got = self.read(seq)
        if got != want:
            raise Refuse(EXIT_CORRUPT, f"checkpoint {seq} does not match HEAD (sha256 {got} != {want})")
        return seq, obj, got

    def write(self, seq, state, prev_sha, crash=None):
        self.dir.mkdir(parents=True, exist_ok=True)
        obj = dict(state, seq=seq, prev_ckpt_sha256=prev_sha)
        data = canon(obj)
        write_atomic(self.dir / f"ckpt_{seq:06d}.json", data, crash)
        sha = sha256_bytes(data)
        write_atomic(self.head_path, canon({"seq": seq, "sha256": sha}))
        return sha

    def clean_tmp(self):
        out = []
        for p in list(self.dir.glob("*.tmp")) + ([self.head_path.with_name("HEAD.json.tmp")]
                                                 if self.head_path.with_name("HEAD.json.tmp").exists() else []):
            out.append(p.name)
            p.unlink()
        return out

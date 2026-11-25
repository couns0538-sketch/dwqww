"""Opus 2026-11-24, A3f (specs/home_fetch.md; FORMATS 0 [2.1], 1.6, 2.1 [2.4] [2.7]; SETUP_PLAN row 30): the home
FETCH. Standard library only; nothing is installed. Home starts every connection; the server never connects back.

    fetch.py --home DIR --fingerprint HEX64 --config FILE [--budget-bytes N] [--confirm w<NNN>/p<NNNNNN> ...]

ONE PASS a call (the home guard calls it again). ONE FETCH AT A TIME on a home folder: an OS lock on
home/fetch/LOCK, taken before any other file is touched (else exit 8), because a placed file is a hard link of its
checked partial: a second fetch writing into that partial would change bytes already in wire/.
THE TRANSPORT is a child process that appends bytes to a private partial file from the partial's length. On the day
it is Windows' own OpenSSH sftp.exe in batch mode, pinned to ONE host key: -F <an empty file>, BatchMode=yes,
StrictHostKeyChecking=yes, UserKnownHostsFile=<the config's file of ONE key line>, GlobalKnownHostsFile=<the empty
file>, UpdateHostKeys=no, IdentitiesOnly=yes, and ConnectTimeout=15, ServerAliveInterval=15, ServerAliveCountMax=3
(NF-18). An unknown or changed key, or a refused login, STOPS the pass (exit 6) without a question. In the tests it is
a local sender (tests/fake_transport.py) with scripted pauses. The fetch watches the partial's LENGTH: a file whose
last byte is older than the config's idle bound is cut (FORMATS [2.7]: a connected fetch is not progress), and so is
a transfer older than the config's transfer_s (default 1800; NF-18's outer bound: a server that trickles a byte inside
every idle bound cannot hold the pass); its partial stays for the next pass. A listing is bounded by max(idle, 30) s.
THE HOME FOLDER: wire/ gets only COMPLETE files that were checked (an offer's member: its wire_bytes and wire_sha256;
any other file: its listed length and one whole zlib stream), each linked create-only (FORMATS 0), an offer's
members first and the offer LAST; custody reads wire/ and never writes there. fetch/part/<fingerprint>/ holds the
partials (a partial of another run is never resumed), fetch/refused/<fingerprint>/ the offers refused (not fetched
again at the same length), fetch/journal.jsonl one line a pass and one for each partial, fork, refusal and stop.
WHAT IS FETCHED: RUN.json.zz first (it must decode to bytes whose sha256 is --fingerprint, or exit 3, nothing
placed); the control files of the root and ranges/; for every slot of the run header, out/w<NNN>/p<N>.offer.json.zz
and the members its decoded record names (the fixed names of 1.6 for its form and its own index, checked BEFORE a
name becomes a path). Any other listed name is ignored.
SEEING AGAIN IS NOT CONFIRMING (2.4): an offer with a receipt whose listed length is the receipt's offer_wire_bytes
causes no transfer and no read; another length is a possible FORK: the new bytes are kept once beside the old ones
as <name>.conflict.<sha12>, nothing is replaced. --confirm KEY (an explicit confirmation): the kept offer and members
of that receipt are opened and hashed; a missing one is fetched again, a different one is first renamed aside to
<name>.damaged.<sha12> (a new name) and then fetched again. Custody's own --confirm then confirms; never a second
receipt.
RESUME: a partial continues where it ends, after stepping back by the transport's in-flight window (sftp writes its
64 outstanding requests of 32 KiB out of order); it earns its place only by the whole file's check; a failed check
throws the partial away and fetches the file again from byte zero (once a pass).
BUDGET: with --budget-bytes N a transfer starts only while the bytes received in this pass plus what it still needs
stay within N; the first that would pass it is not started ("budget binds", exit 0). The config's floor_bytes keeps
that much of the home disk free in the same way.
THE COUNTS, apart (specs/home_fetch.md): listing bytes; control, offer and member files placed and bytes received for
the first time; bytes sent again (a discarded partial, the window, a repair); partials; confirmations; forks;
refused; incomplete offers; ignored names.
Exit codes: 0 a pass; 2 a wrong call; 3 the run header cannot be trusted, or custody/ holds another run's receipt;
4 a home file that cannot be read or written; 5 a confirmation that could not be repaired; 6 the host key or the
login failed (STOP); 7 the server cannot be reached; 8 another fetch holds home/fetch/LOCK (nothing done). The last
line: fetch: listing .. bytes; control .. files ..
bytes; offers .. files .. bytes; members .. files .. bytes; sent again .. bytes; partial ..; confirmations ..; forks
..; refused ..; incomplete ..; ignored ..; budget binds yes|no
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "run"))
from packer import FORMS, MEMBER_KEYS, OFFER_KEYS  # noqa: E402
from worker import SlotLock, Stop, canon, file_sha256, fsync_dir, parse_canon, sha256_bytes  # noqa: E402

HEX64 = re.compile(r"[0-9a-f]{64}")
KEY = re.compile(r"w([0-9]{3})/p([0-9]{6})")
OFFER = re.compile(r"p([0-9]{6})\.offer\.json\.zz")
ROOT_WIRE = re.compile(r"(RUN|FENCE|SCHEDULE\.[1-9][0-9]{0,2}|RESUME\.[1-9][0-9]{0,2})\.json\.zz|TERMINAL\.jsonl\.zz")
RANGE_WIRE = re.compile(r"r[0-9]{4}\.w[0-9]{3}\.seal\.json\.zz")
MEMBER_WIRE = re.compile(r"p[0-9]{6}\.(seal\.json\.zz|binpack|meta\.xz|raw\.zz)")
LISTED = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
HOSTKEY = ("Host key verification failed", "REMOTE HOST IDENTIFICATION HAS CHANGED", "host key is known",
           "Permission denied (", "Too many authentication failures")   # R1: the login form only, "<user>@<host>:
#            Permission denied (publickey)."; a local partial that cannot be opened says `...": Permission denied`
UNREACHABLE = ("Connection refused", "Connection timed out", "Could not resolve hostname", "Network is unreachable",
               "No route to host", "Connection closed", "Connection reset", "Broken pipe")
SFTP_WINDOW = 64 * 32768                                # -R 64 -B 32768: the bytes sftp may have in flight


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def whole_zlib(data: bytes) -> bytes:
    d = zlib.decompressobj()
    out = d.decompress(data) + d.flush()
    if not d.eof or d.unused_data:
        raise ValueError("not one whole zlib stream")
    return out


def zlib_ok(p: Path) -> bool:
    try:
        whole_zlib(p.read_bytes())
        return True
    except (ValueError, zlib.error):
        return False


def nat(*xs) -> bool:
    return all(type(x) is int and x >= 0 for x in xs)


def size(p: Path) -> int:
    try:
        return os.stat(p).st_size
    except FileNotFoundError:
        return 0


def judge(text: str) -> None:
    """A failed child: the host key or the login is a STOP (6), an unreachable server is 7; anything else returns."""
    last = " | ".join(ln.strip() for ln in text.strip().splitlines()[-3:])
    if any(s in text for s in HOSTKEY):
        raise Stop(6, f"the host key or the login failed: {last}")
    if any(s in text for s in UNREACHABLE):
        raise Stop(7, f"the server cannot be reached: {last}")


class Transport:
    """The child process. list(dir) -> ({name: length}, listing bytes); get(rel, partial, whole) -> (the child's exit
    code or "idle" or "long", its last text, the silence in ms at a cut)."""

    def __init__(self, cfg: dict, fdir: Path):
        self.kind, self.root, self.idle = cfg.get("transport"), cfg.get("remote_root"), cfg.get("idle_s")
        self.cap = cfg.get("transfer_s", 1800)
        if type(self.root) is not str or not self.root or not nat(self.idle, self.cap) or min(self.idle, self.cap) < 1:
            raise Stop(2, "the config needs remote_root (text), idle_s and transfer_s (whole seconds, at least 1)")
        self.log = fdir / "child.out"
        if self.kind == "sftp":
            known = Path(str(cfg.get("known_hosts", "")))
            keys = [ln for ln in (known.read_text(encoding="ascii").splitlines() if known.is_file() else [])
                    if ln.strip() and not ln.lstrip().startswith("#")]
            if len(keys) != 1 or len(keys[0].split()) < 3:
                raise Stop(2, "known_hosts must be a file of exactly ONE pinned key line")
            if not (type(cfg.get("host")) is str and type(cfg.get("user")) is str and nat(cfg.get("port"))
                    and type(cfg.get("identity")) is str and type(cfg.get("sftp")) is str):
                raise Stop(2, "the config needs host, user, port, identity and sftp for the sftp transport")
            empty = fdir / "ssh_empty"
            if not empty.exists():
                empty.write_bytes(b"")
            if size(empty):
                raise Stop(4, f"{empty} is not empty")
            self.window, self.batch = SFTP_WINDOW, fdir / "sftp_batch.txt"
            self.cmd = [cfg["sftp"], "-b", str(self.batch), *self.ssh_options(cfg, empty), "-R", "64", "-B", "32768",
                        "-P", str(cfg["port"]), f"{cfg['user']}@{cfg['host']}"]
        elif self.kind == "local":
            if not (type(cfg.get("python")) is str and type(cfg.get("sender")) is str):
                raise Stop(2, "the config needs python and sender for the local transport")
            self.window = cfg.get("window_bytes", 0)
            if not nat(self.window):
                raise Stop(2, "window_bytes must be a whole number")
            self.cmd = [cfg["python"], "-I", "-B", cfg["sender"]]
        else:
            raise Stop(2, "the config's transport must be sftp or local")

    @staticmethod
    def ssh_options(cfg: dict, empty: Path) -> list:
        return ["-F", str(empty), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                "-o", f'UserKnownHostsFile="{cfg["known_hosts"]}"',   # R2: quoted, or ssh splits the path at spaces
                "-o", f'GlobalKnownHostsFile="{empty}"',
                "-o", "UpdateHostKeys=no", "-o", "IdentitiesOnly=yes", "-o", "ConnectTimeout=15",
                "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3", "-i", str(cfg["identity"])]

    def call(self, op: str, rel: str, part: Path = None) -> list:
        if self.kind == "local":
            return self.cmd + [op, self.root, rel] + ([str(part)] if part else [])
        remote = f"{self.root.rstrip('/')}/{rel}" if rel else self.root
        # the root without "-": a missing root is a failed listing, not an empty one; a slot or ranges/ may not exist yet
        line = f'{"-" if rel else ""}ls -ln "{remote}"' if op == "list" else \
            f'{"reget" if size(part) else "get"} "{remote}" "{part.as_posix()}"'   # sftp's batch reads "\" as an escape
        self.batch.write_text(line + "\n", encoding="ascii")
        return self.cmd

    def list(self, d: str):
        try:
            p = subprocess.run(self.call("list", d), capture_output=True, timeout=max(self.idle, 30))
        except subprocess.TimeoutExpired:
            raise Stop(7, f"the listing of '{d}' took longer than {max(self.idle, 30)} s") from None
        text = (p.stdout + p.stderr).decode("utf-8", "replace")
        if p.returncode:
            judge(text)
            raise Stop(7, f"the listing of '{d}' failed (exit {p.returncode}): {text.strip()[-200:]}")
        out = {}
        for ln in p.stdout.decode("utf-8", "replace").splitlines():
            f = ln.split()
            if self.kind == "local" and len(f) == 2 and f[0].isdigit():
                n, name = int(f[0]), f[1]
            elif self.kind == "sftp" and len(f) >= 9 and ln.startswith("-") and f[4].isdigit():
                n, name = int(f[4]), ln.split(None, 8)[8].rsplit("/", 1)[-1]   # the whole name, spaces kept
            else:
                continue
            if LISTED.fullmatch(name) and ".." not in name:
                out[name] = n
        return out, len(p.stdout)

    def get(self, rel: str, part: Path, whole: int):
        with open(self.log, "wb") as log:
            p = subprocess.Popen(self.call("get", rel, part), stdout=log, stderr=subprocess.STDOUT)
            last_n, last_t, cut, silent = size(part), time.monotonic(), None, 0
            t0 = last_t
            while p.poll() is None:
                time.sleep(0.2)
                n = size(part)
                if n != last_n:
                    last_n, last_t = n, time.monotonic()
                silent = int((time.monotonic() - last_t) * 1000)
                if n > whole:
                    cut = "long"
                elif silent > self.idle * 1000:
                    cut = "idle"
                elif time.monotonic() - t0 > self.cap:
                    cut = "slow"
                if cut:
                    p.kill()
                    p.wait()
                    break
        text = self.log.read_text(encoding="utf-8", errors="replace")[-3000:]
        return (cut or p.returncode), text, silent


class Fetch:
    def __init__(self, home: Path, fp: str, cfg: dict, budget):
        self.home, self.fp, self.budget = home, fp, budget
        self.wire, fdir = home / "wire", home / "fetch"
        self.part, self.refd = fdir / "part" / fp, fdir / "refused" / fp
        fdir.mkdir(parents=True, exist_ok=True)
        try:
            self.lock = SlotLock(fdir)                  # held until the process ends; the OS frees it
        except Stop:
            raise Stop(8, f"another fetch holds {fdir / 'LOCK'}: nothing done") from None
        for d in (self.wire, self.part, self.refd):
            d.mkdir(parents=True, exist_ok=True)
        self.journal = fdir / "journal.jsonl"
        self.t = Transport(cfg, fdir)
        self.floor = cfg.get("floor_bytes", 0)
        if not nat(self.floor):
            raise Stop(2, "floor_bytes must be a whole number")
        self.c = dict(listing=0, control_files=0, control_bytes=0, offer_files=0, offer_bytes=0, member_files=0,
                      member_bytes=0, again=0, partial=0, confirmations=0, forks=0, refused=0, incomplete=0, ignored=0)
        self.received, self.binds, self.confirm_failed = 0, False, False

    def note(self, **rec) -> None:
        rec["at_utc"] = utc()
        with open(self.journal, "ab") as f:
            f.write(canon(rec))
            f.flush()
            os.fsync(f.fileno())

    def listing(self, d: str) -> dict:
        out, n = self.t.list(d)
        self.c["listing"] += n
        return out

    def room(self, need: int) -> bool:
        if not self.binds and ((self.budget is not None and self.received + need > self.budget)
                               or shutil.disk_usage(self.home).free - need < self.floor):
            self.binds = True
            self.note(t="budget", need=need, received=self.received)
        return not self.binds

    # ---- one file into its partial, checked ------------------------------------------------------------------
    def transfer(self, rel: str, whole: int, check, kind: str, part: Path = None, again: bool = False):
        """("ok", the checked partial) or ("partial" | "bad" | "budget" | "failed", None)."""
        part = part or self.part / rel
        part.parent.mkdir(parents=True, exist_ok=True)
        old = size(part)
        if old > whole:
            part.unlink()
            old = 0
        seen = whole if again else old                  # bytes of this file that arrived before
        for attempt in (1, 2):
            start = 0 if attempt == 2 else old if old == whole else max(0, old - self.t.window)  # a whole one: check
            if part.exists() and size(part) > start:
                os.truncate(part, start)
            if start < whole:
                if not self.room(whole - start):
                    return "budget", None
                code, text, silent = self.t.get(rel, part, whole)
                n = size(part)
                got = max(0, n - start)
                first = max(0, n - max(seen, start))
                self.received += got
                self.c[f"{kind}_bytes"] += first
                self.c["again"] += got - first
                seen = max(seen, n)
                if code == "long" or n > whole:             # also when the child ended before the watcher looked
                    part.unlink()
                    self.c["refused"] += 1
                    self.note(t="refused", rel=rel, why=f"longer than its whole length {whole}")
                    return "bad", None
                if code != 0 or n < whole:
                    if code not in (0, "idle", "slow"):
                        judge(text)
                    self.c["partial"] += 1
                    self.note(t="partial", rel=rel, have=n, whole=whole, silent_ms=silent,
                              why=f"idle longer than {self.t.idle} s" if code == "idle" else
                              f"longer than {self.t.cap} s" if code == "slow" else
                              f"the child ended ({code}) short: {text.strip()[-160:]}")
                    return ("partial" if n or code in ("idle", "slow") else "failed"), None
            if check(part):
                return "ok", part
            part.unlink()
            self.note(t="discarded", rel=rel, bytes=whole, why="the whole file's check failed; again from byte zero")
            old, seen = 0, whole
        return "bad", None

    def place(self, part: Path, final: Path, kind) -> str:
        """Create-only (FORMATS 0): equal bytes under the final name = done; other bytes = both kept, a fork."""
        final.parent.mkdir(parents=True, exist_ok=True)
        if final.exists():
            if size(final) == size(part) and file_sha256(final) == file_sha256(part):
                part.unlink()
                return "same"
            self.keep_beside(part, final, size(part))
            return "fork"
        os.link(part, final)
        fsync_dir(final.parent)
        part.unlink()
        if kind:
            self.c[f"{kind}_files"] += 1
        return "placed"

    def keep_beside(self, part: Path, final: Path, n: int) -> None:
        other = final.with_name(f"{final.name}.conflict.{file_sha256(part)[:12]}")
        if not other.exists():
            os.link(part, other)
            fsync_dir(other.parent)
        part.unlink()
        self.c["forks"] += 1
        self.note(t="fork", rel=str(final.relative_to(self.wire).as_posix()), kept=final.name, new=other.name,
                  new_bytes=n)

    def fork(self, rel: str, n: int, kind: str, check) -> None:
        """A listed length that is not the one held: the new bytes once beside the old (2.4), nothing replaced."""
        final = self.wire / rel
        if any(size(p) == n for p in final.parent.glob(final.name + ".conflict.*")):
            return
        st, p = self.transfer(rel, n, check, kind, part=self.part / (rel + ".fork"))
        if st == "ok":
            self.keep_beside(p, final, n)

    def set_aside(self, f: Path) -> None:
        new = f.with_name(f"{f.name}.damaged.{file_sha256(f)[:12]}")
        if new.exists():
            f.unlink()
        else:
            os.rename(f, new)
        self.note(t="damaged", rel=str(f.relative_to(self.wire).as_posix()), kept_as=new.name)

    # ---- the pass ---------------------------------------------------------------------------------------------
    def header(self):
        hz = self.wire / "RUN.json.zz"
        self.root = self.listing("")
        if not hz.exists():
            if "RUN.json.zz" not in self.root:
                return None

            def this_run(p: Path) -> bool:
                try:
                    return sha256_bytes(whole_zlib(p.read_bytes())) == self.fp
                except (ValueError, zlib.error):
                    return False
            st, p = self.transfer("RUN.json.zz", self.root["RUN.json.zz"], this_run, "control")
            if st == "bad":
                self.note(t="stop", why="RUN.json.zz on the server is not this run")
                raise Stop(3, "RUN.json.zz on the server does not decode to --fingerprint: another run, nothing placed")
            if st != "ok":
                return None
            self.place(p, hz, "control")
        try:
            data = whole_zlib(hz.read_bytes())
            if sha256_bytes(data) != self.fp:
                raise ValueError("its decoded sha256 is not --fingerprint")
            h = parse_canon(data, "RUN.json")
        except (ValueError, zlib.error) as e:
            raise Stop(3, f"the run header at home cannot be trusted: {e}") from None
        sl = h.get("slots") if isinstance(h, dict) else None
        if not isinstance(sl, list) or not sl or not all(nat(k) and k <= 999 for k in sl) or len(set(sl)) != len(sl):
            raise Stop(3, "the run header's slots are not distinct slot numbers")
        return h

    def controls(self) -> None:
        for d, rx in (("", ROOT_WIRE), ("ranges", RANGE_WIRE)):
            for name, n in sorted((self.root if d == "" else self.listing(d)).items()):
                if not rx.fullmatch(name):
                    self.c["ignored"] += 1                  # a listing holds files only (sftp's "d" lines are skipped)
                    continue
                rel = f"{d}/{name}" if d else name
                final = self.wire / rel
                if final.exists():
                    if size(final) != n:
                        self.fork(rel, n, "control", zlib_ok)
                    continue
                st, p = self.transfer(rel, n, zlib_ok, "control")
                if st == "ok":
                    self.place(p, final, "control")

    def receipt(self, k: int, i: int):
        p = self.home / "custody" / f"w{k:03d}" / f"p{i:06d}.receipt.json"
        if not p.exists():
            return None
        try:
            r = parse_canon(p.read_bytes(), p.name)
        except ValueError as e:
            raise Stop(4, str(e)) from None
        if not isinstance(r, dict) or r.get("run_fingerprint") != self.fp or (r.get("slot"), r.get("index")) != (k, i):
            raise Stop(3, f"custody/w{k:03d}/{p.name} is not a receipt of this run, slot and index")
        if not nat(r.get("offer_wire_bytes")) or type(r.get("offer_wire_sha256")) is not str \
                or not isinstance(r.get("members"), list):
            raise Stop(4, f"custody/w{k:03d}/{p.name}: not a receipt as 2.1 writes it")
        return r

    def members(self, p: Path, k: int, i: int) -> list:
        """The offer's record checked as custody checks it (1.6), before any member name becomes a path."""
        try:
            o = parse_canon(whole_zlib(p.read_bytes()), f"p{i:06d}.offer.json")
        except zlib.error as e:
            raise ValueError(f"not one whole zlib stream ({e})") from None
        if not isinstance(o, dict) or sorted(o) != OFFER_KEYS or o["schema"] != 2 or not nat(o["slot"], o["index"]):
            raise ValueError("the offer has not the keys and schema of 1.6")
        if o["run_fingerprint"] != self.fp:
            raise ValueError("not this run's offer (run_fingerprint)")
        if (o["slot"], o["index"]) != (k, i):
            raise ValueError(f"the offer is of slot {o['slot']} index {o['index']}, not of its own name")
        ms, name = o["members"], f"p{i:06d}"
        if type(o["form"]) is not str or o["form"] not in FORMS or not isinstance(ms, list) or \
                [(m.get("name"), m.get("codec")) if isinstance(m, dict) else None for m in ms] != \
                [(name + x, c) for x, c in FORMS[o["form"]]]:
            raise ValueError("its members are not those of a form of 1.6")
        for m in ms:
            if sorted(m) != MEMBER_KEYS or m["wire_name"] != m["name"] + (".zz" if m["name"].endswith(".seal.json") else "") \
                    or not nat(m["bytes"], m["wire_bytes"]) \
                    or not all(type(m[x]) is str and HEX64.fullmatch(m[x]) for x in ("sha256", "wire_sha256")):
                raise ValueError(f"the member {m['name']} is not written as 1.6 says")
        return ms

    def offers(self, h: dict) -> None:
        for k in h["slots"]:
            d = f"out/w{k:03d}"
            listed = self.listing(d)
            for name, n in sorted(listed.items()):
                if m := OFFER.fullmatch(name):
                    self.offer(k, int(m[1]), n, listed)
                elif not MEMBER_WIRE.fullmatch(name):
                    self.c["ignored"] += 1

    def offer(self, k: int, i: int, n: int, listed: dict) -> None:
        d, name = f"out/w{k:03d}", f"p{i:06d}.offer.json.zz"
        rel, final = f"{d}/{name}", self.wire / d / name
        r = self.receipt(k, i)
        if r is not None or final.exists():
            if n != (r["offer_wire_bytes"] if r is not None else size(final)):
                self.fork(rel, n, "offer", zlib_ok)
            return                                      # 2.4: seeing a held name again confirms nothing
        refused = self.refd / rel
        if size(refused) == n and refused.exists():
            return
        st, p = self.transfer(rel, n, zlib_ok, "offer")
        if st != "ok":
            return
        try:
            ms = self.members(p, k, i)
        except ValueError as e:
            refused.parent.mkdir(parents=True, exist_ok=True)
            os.replace(p, refused)                      # our own scratch name, never a file of wire/
            self.c["refused"] += 1
            self.note(t="refused", rel=rel, why=str(e))
            return
        short = [m["wire_name"] for m in ms if listed.get(m["wire_name"]) != m["wire_bytes"]]
        if short:
            self.c["incomplete"] += 1
            self.note(t="incomplete", rel=rel, why=f"not on the server at their length: {', '.join(short)}")
            return
        for m in ms:
            mf = self.wire / d / m["wire_name"]
            if mf.exists():
                if size(mf) == m["wire_bytes"] and file_sha256(mf) == m["wire_sha256"]:
                    continue
                self.set_aside(mf)
            st, q = self.transfer(f"{d}/{m['wire_name']}", m["wire_bytes"],
                                  lambda x, s=m["wire_sha256"]: file_sha256(x) == s, "member")
            if st != "ok":
                self.c["incomplete"] += 1
                self.note(t="incomplete", rel=rel, why=f"{m['wire_name']}: {st}")
                return
            self.place(q, mf, "member")
        self.place(p, final, "offer")                   # LAST, as the packer publishes it

    def confirm(self, key: str) -> None:
        m = KEY.fullmatch(key)
        if not m:
            raise Stop(2, f"{key}: not a key w<NNN>/p<NNNNNN>")
        k, i = int(m[1]), int(m[2])
        r = self.receipt(k, i)
        if r is None:
            raise Stop(2, f"{key}: no receipt of this run")
        d = f"out/w{k:03d}"
        want = [(x.get("wire_name"), x.get("wire_bytes"), x.get("wire_sha256")) for x in r["members"] if isinstance(x, dict)]
        want.append((f"p{i:06d}.offer.json.zz", r["offer_wire_bytes"], r["offer_wire_sha256"]))
        listed, ok = None, len(want) == len(r["members"]) + 1
        for wn, wb, ws in want:
            if not (type(wn) is str and (MEMBER_WIRE.fullmatch(wn) or OFFER.fullmatch(wn)) and wn.startswith(f"p{i:06d}.")
                    and nat(wb) and type(ws) is str and HEX64.fullmatch(ws)):
                raise Stop(4, f"{key}: the receipt names a member that is not as 2.1 writes it")
            f = self.wire / d / wn
            if f.exists() and size(f) == wb and file_sha256(f) == ws:
                continue
            if f.exists():
                self.set_aside(f)
            listed = listed if listed is not None else self.listing(d)
            st = "gone"
            if listed.get(wn) == wb:
                st, q = self.transfer(f"{d}/{wn}", wb, lambda x, s=ws: file_sha256(x) == s, "member", again=True)
                if st == "ok":
                    self.place(q, f, None)
                    continue
            ok = False
            self.note(t="confirm", key=key, why=f"{wn} could not be fetched again ({st})")
        self.c["confirmations"] += 1
        self.confirm_failed |= not ok

    def finish(self) -> None:
        c = self.c
        self.note(t="pass", binds=self.binds, **c)
        print(f"fetch: listing {c['listing']} bytes; control {c['control_files']} files {c['control_bytes']} bytes; "
              f"offers {c['offer_files']} files {c['offer_bytes']} bytes; members {c['member_files']} files "
              f"{c['member_bytes']} bytes; sent again {c['again']} bytes; partial {c['partial']}; "
              f"confirmations {c['confirmations']}; forks {c['forks']}; refused {c['refused']}; "
              f"incomplete {c['incomplete']}; ignored {c['ignored']}; budget binds {'yes' if self.binds else 'no'}")


def main() -> int:
    ap = argparse.ArgumentParser(description="The home fetch, one pass (A3f).")
    ap.add_argument("--home", required=True)
    ap.add_argument("--fingerprint", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--budget-bytes", type=int, default=None)
    ap.add_argument("--confirm", nargs="*", default=[])
    a = ap.parse_args()
    if not HEX64.fullmatch(a.fingerprint) or (a.budget_bytes is not None and a.budget_bytes < 0):
        print("fetch: --fingerprint must be 64 hex digits and --budget-bytes not negative")
        return 2
    f = None
    try:
        try:
            cfg = json.loads(Path(a.config).read_text(encoding="ascii"))
        except (OSError, ValueError) as e:
            raise Stop(2, f"the config cannot be read: {e}") from None
        if not isinstance(cfg, dict):
            raise Stop(2, "the config is not one JSON object")
        f = Fetch(Path(a.home).resolve(), a.fingerprint, cfg, a.budget_bytes)
        h = f.header()
        if h is not None:
            if a.confirm:
                for key in a.confirm:
                    f.confirm(key)
            else:
                f.controls()
                f.offers(h)
        elif a.confirm:
            raise Stop(5, "no run header at home or on the server: nothing is confirmed")
        f.finish()
        return 5 if f.confirm_failed else 0
    except Stop as e:
        print(f"fetch: STOP {e.code}: {e}")
        if f is not None:
            try:
                f.note(t="stop", code=e.code, why=str(e)[:300])
            except OSError:
                pass
        return e.code
    except OSError as e:
        print(f"fetch: STOP 4: a home file cannot be read or written: {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())

"""bootguard.py: the boot guard of the server day (A3b; FORMATS.md 1.1, 1.3, 1.8 point 1; SETUP_PLAN D5, D15).

Started by the system at EVERY boot, before the server guard, with the guard's own arguments, by the package's one
unit file. Standard library and the worker module only.

    bootguard.py --root DIR --exe ENGINE --net NET --manifest MANIFEST.json --known-startup FILE [--openings FILE]
                 --package-list MANIFEST.sha256 [--sync-wait 900] [--etc /etc] [--dmi /sys/class/dmi/id]

1. The machine's boot id is the header's (RUN.json `boot_id`): nothing to do.
2. The highest RESUME of a valid chain (1.3: every RESUME.1 to n there, canonical, schema 2, this run's, n = its
   name, prev = sha256 of RESUME n-1's bytes, `first` for 1, old_boot_id = the header's boot for 1, else RESUME
   n-1's new_boot_id) names this boot as `new_boot_id`: nothing to do.
3. A NEW boot: it takes guard/LOCK (the server guard's own lock: it never runs beside a server guard) and writes
   RESUME.<n>.json, create-only, ONLY when every check holds (1.3 [2.2]), each with its evidence in `checks`:
   fence     FENCE.json is not there ("no fence exists"; a restart after the fence is held for a person);
   instance  the header's and the one read now are EQUAL by 1.1 [2.4]: both provable; the machine ids equal; per
             hardware field, null on both sides is neither evidence nor a difference, null on one side only is a
             difference, values on both sides must be the same;
   hashes    sha256 of the package's hash list is the header's `package`; the list is in the publisher's form
             (`<sha256>  <relative path>` lines, the last line `digest <sha256 of the lines before it>`) and every
             file it names has its sha256; it names `plan.json`, the owner's policy (FORMATS 1.2: owner_policy
             is the package's; D6; bug hunt 23 Nov 19:30); the engine file is `engine_sha256`, the net file
             `net_sha256`;
   chains    every slot of the header is read by the WORKER'S OWN code: the header and manifest checks, the slot's
             identity, the schedule chain, the journal replayed (every seal descends from the one before, from the
             genesis), its lock free; the slot's row is the (last_index, last_seal) that reading leaves, which is what
             the worker compares at its next start (1.3 [2.4] a); a slot with no folder: -1 and the genesis text;
   lease     RUN.json is the file every identity and schedule names (its sha256 is the run fingerprint): the lease,
             the hard cutoff and the D in force are the day's, recorded; a restart never buys a fresh 23 hours;
   clock     the kernel says the clock is synchronised (waited for, at most --sync-wait seconds, looked at every 5 s)
             and UTC now is not before the newest modification time of a slot's journal (D5).
   The RESUME's keys (1.3 [2.3]): schema 2, run_fingerprint, n, prev, old_boot_id (the header's for n = 1, else
   RESUME n-1's new_boot_id), new_boot_id, instance (as read now), instance_provable (true), slots (one row a
   header slot, in the header's order), checks, at_utc. Then the workers go on under a new epoch; after D a worker's
   start is seal_only by its own clocks, never a search.
Instance values are the sha256 of the texts read (/etc/machine-id, DMI product_uuid and board_serial); missing,
unreadable, empty or a placeholder (FORMATS 1.1's list, and Neon's reference's extras, without case; a UUID of
zeros or of f only; a machine id that is not 32 lower hex) is null. Synchronised: Linux adjtimex() does not return
TIME_ERROR; where it cannot be read, the clock is not synchronised.

Exit codes: 0 admitted (the header's boot, admitted already, or RESUME.<n> written now); 3 a lock is held (a server
guard or a worker runs); 4 the run's own files contradict themselves (the header lacks a key the worker needs, the
RESUME chain, schedule chain, a slot's identity or journal), or an error the boot guard does not know (an OSError
while a file is read; the ALARM line names it: never a traceback); 5 this machine, its clock, the package or the fence do not qualify (held: for a person, or
for the unit's next try); 2 arguments. A run that is not 0 writes no RESUME and changes no file of the run; it
writes one ALARM line to guard/bootguard.log, not again while the reason stays the same."""
import argparse
import ctypes
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worker as W  # noqa: E402
from worker import SlotLock, Stop, canon, create_only, file_sha256, parse_canon, sha256_bytes  # noqa: E402

PLACEHOLDERS = {"", "none", "n/a", "na", "not specified", "to be filled by o.e.m.", "default string",
                "system serial number"}
TIME_ERROR = 5                          # adjtimex(2): the clock is not synchronised
CHECKS = ("boot", "chains", "clock", "fence", "hashes", "instance", "lease")


def T(t) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t)))


def clean(text):
    v = text.strip()
    if v.lower() in PLACEHOLDERS or re.fullmatch(r"[0-]+|[fF-]+", v):
        return None
    return v


def read_instance(etc: Path, dmi: Path) -> dict:
    def rd(p: Path):
        try:
            return clean(p.read_bytes().decode("ascii"))
        except (OSError, UnicodeDecodeError):
            return None
    mid = rd(etc / "machine-id")
    if mid is not None and not re.fullmatch(r"[0-9a-f]{32}", mid):
        mid = None
    vals = {"machine_id": mid, "product_uuid": rd(dmi / "product_uuid"), "board_serial": rd(dmi / "board_serial")}
    return {k: (sha256_bytes(v.encode("ascii")) if v is not None else None) for k, v in vals.items()}


def provable(inst) -> bool:
    return (isinstance(inst, dict) and sorted(inst) == ["board_serial", "machine_id", "product_uuid"]
            and inst["machine_id"] is not None and (inst["product_uuid"] is not None or inst["board_serial"] is not None))


def differs(header_inst, now_inst):
    """None when EQUAL by 1.1 [2.4], else the reason."""
    if not provable(header_inst):
        return "the header's instance is not provable"
    if not provable(now_inst):
        return "the instance read now is not provable"
    if header_inst["machine_id"] != now_inst["machine_id"]:
        return "the machine id differs"
    for k in ("product_uuid", "board_serial"):
        a, b = header_inst[k], now_inst[k]
        if (a is None) != (b is None):
            return f"{k} is there on one side only"
        if a is not None and a != b:
            return f"{k} differs"
    return None


def kernel_synchronised() -> bool:
    if not sys.platform.startswith("linux"):
        return False
    try:
        buf = ctypes.create_string_buffer(512)          # struct timex, modes 0: read only (512 > its size)
        st = ctypes.CDLL(None, use_errno=True).adjtimex(buf)
    except (OSError, AttributeError):
        return False
    return st >= 0 and st != TIME_ERROR


def readers():
    return SimpleNamespace(boot=W.boot_id, synced=kernel_synchronised, utc=time.time, sleep=time.sleep)


class Held(Exception):
    def __init__(self, code: int, text: str):
        super().__init__(text)
        self.code, self.text = code, text


class BootGuard:
    def __init__(self, a, rd=None):
        self.a, self.rd = a, rd or readers()
        self.root = Path(a.root)
        self.gdir = self.root / "guard"

    def say(self, text: str) -> None:
        print(text, flush=True)

    def alarm(self, code: int, text: str) -> None:
        """One ALARM line in guard/bootguard.log, not repeated while the reason stays the same."""
        body = f"HELD exit {code}: {text}"
        log = self.gdir / "bootguard.log"
        last = log.read_bytes().decode("ascii", "replace").rstrip("\n").rsplit("\n", 1)[-1] if log.exists() else ""
        if last.split("] ", 1)[-1] != body:
            self.gdir.mkdir(exist_ok=True)
            with open(log, "a", encoding="ascii", errors="replace", newline="\n") as f:
                f.write(f"[{T(time.time())}] {body}\n")
        self.say(f"ALARM bootguard: {body}")

    def resumes(self, fp: str, boot0: str) -> list:
        """The RESUME chain as the worker reads it (1.3): [(name, bytes, record)]; a break is exit 4."""
        names = [p.name for p in self.root.glob("RESUME.*.json")]
        if any(not re.fullmatch(r"RESUME\.[1-9][0-9]{0,2}\.json", x) for x in names):
            raise Held(4, f"a RESUME file name outside the grammar: {sorted(names)[:5]}")
        out, prev = [], b""
        for k in range(1, len(names) + 1):
            p = self.root / f"RESUME.{k}.json"
            if not p.exists():
                raise Held(4, f"there are {len(names)} RESUME files and RESUME.{k}.json is not one of them")
            data = p.read_bytes()
            try:
                r = parse_canon(data, p.name)
            except ValueError as e:
                raise Held(4, str(e)) from None
            if not isinstance(r, dict) or r.get("schema") != 2 or r.get("n") != k or r.get("run_fingerprint") != fp \
                    or r.get("prev") != ("first" if k == 1 else sha256_bytes(prev)) \
                    or not isinstance(r.get("new_boot_id"), str) \
                    or r.get("old_boot_id") != (boot0 if k == 1 else out[-1][2]["new_boot_id"]):
                raise Held(4, f"{p.name}: not RESUME {k} of this run (schema, n, run_fingerprint, prev, old_boot_id, "
                              f"new_boot_id)")
            out.append((p.name, data, r))
            prev = data
        return out

    def package(self, h: dict) -> dict:
        lst = Path(self.a.package_list)
        try:
            data = lst.read_bytes()
        except OSError:
            raise Held(5, f"the package's hash list {lst.name} cannot be read") from None
        if sha256_bytes(data) != h["package"]:
            raise Held(5, f"the package's hash list {lst.name} is not the header's `package`")
        try:
            body = data.decode("ascii").split("\n")
        except UnicodeDecodeError:
            raise Held(5, f"{lst.name}: a byte that is not ASCII") from None
        if body.pop() != "" or len(body) < 2 or body[-1] != "digest " + sha256_bytes(
                ("\n".join(body[:-1]) + "\n").encode("ascii")):
            raise Held(5, f"{lst.name}: no line end, no file, or a last line that is not `digest <sha256 of the "
                          f"lines before it>` (the publisher's form)")
        for ln in body[:-1]:
            m = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_./-]+)", ln)
            if not m or m[2].startswith("/") or ".." in m[2].split("/"):
                raise Held(5, f"{lst.name}: a line that is not `<sha256>  <relative path>`: {ln[:80]}")
            f = lst.parent / m[2]
            if not f.is_file() or f.is_symlink() or file_sha256(f) != m[1]:
                raise Held(5, f"the package file {m[2]} is not there or not the bytes its hash list names")
        if not any(ln.endswith("  plan.json") for ln in body[:-1]):
            raise Held(5, "the package's hash list names no plan.json: the owner's policy is not a file of the "
                          "package (FORMATS 1.2, D6)")
        return {"package": h["package"], "package_files": len(body) - 1}

    def slot_row(self, h: dict, fp: str, k: int) -> tuple:
        """The worker's own reading of slot k: (row, D in force as written, schedules)."""
        a = self.a
        ns = SimpleNamespace(root=a.root, exe=a.exe, net=a.net, manifest=a.manifest, known_startup=a.known_startup,
                             openings=a.openings, slot=k, plant="", rehearsal=False, game_seconds=600.0, trace=False)
        w = W.Worker(ns)
        lock = None
        if w.dir.exists():
            lock = SlotLock(w.dir)                      # Stop 3: a worker runs
        try:
            w.check_identity(canon({"run": h["run"], "run_fingerprint": fp, "schema": 2, "slot": k}))
            w.load_schedules(start=True)
            w.read_journal()
        finally:
            if lock is not None:
                lock.release()
        return {"last_index": w.last_index, "last_seal": w.last_seal, "slot": k}, w.d_text, w.sched_n

    def run(self) -> int:
        try:
            return self.decide()
        except Held as e:
            self.alarm(e.code, e.text)
            return e.code
        except Stop as e:
            code = e.code if e.code in (2, 3) else 4
            self.alarm(code, str(e))
            return code
        except Exception as e:  # noqa: BLE001   never a traceback and exit 1: every other fault is a 4
            self.alarm(4, f"{type(e).__name__}: {e}")
            return 4

    def decide(self) -> int:
        try:
            hb = (self.root / "RUN.json").read_bytes()
        except OSError as e:
            raise Held(4, f"RUN.json cannot be read: {e}") from None
        fp = sha256_bytes(hb)
        try:
            h = parse_canon(hb, "RUN.json")
        except ValueError as e:
            raise Held(4, str(e)) from None
        if not isinstance(h, dict):
            raise Held(4, "RUN.json is not an object")
        miss = [k for k in W.HEADER_KEYS if k not in h]      # the worker's own list, before any key is read
        if miss:
            raise Held(4, f"RUN.json lacks {', '.join(miss)}")
        if h["schema"] != 2 or not isinstance(h["boot_id"], str) or not isinstance(h["slots"], list):
            raise Held(4, "RUN.json: schema 2, a boot_id and the slots are needed")
        boot = self.rd.boot()
        if boot == h["boot_id"]:
            self.say(f"bootguard: the header's boot ({boot}); nothing to do")
            return 0
        chain = self.resumes(fp, h["boot_id"])
        if chain and chain[-1][2]["new_boot_id"] == boot:
            self.say(f"bootguard: {chain[-1][0]} admits this boot ({boot}) already; nothing to do")
            return 0
        self.gdir.mkdir(exist_ok=True)
        glock = SlotLock(self.gdir)                     # Stop 3: a server guard runs
        try:
            return self.new_boot(h, fp, boot, chain)
        finally:
            glock.release()

    def new_boot(self, h: dict, fp: str, boot: str, chain: list) -> int:
        a, checks = self.a, {}
        checks["boot"] = {"header_boot_id": h["boot_id"], "new_boot_id": boot, "resumes_before": len(chain)}
        if (self.root / "FENCE.json").exists():
            raise Held(5, "FENCE.json exists: no RESUME after the fence (1.3); held for a person")
        checks["fence"] = "absent"
        now_inst = read_instance(Path(a.etc), Path(a.dmi))
        why = differs(h.get("instance"), now_inst) if h.get("instance_provable") is True \
            else "the header's instance_provable is not true"
        if why is not None:
            raise Held(5, f"the instance: {why}; held for a person (another or an unprovable machine)")
        checks["instance"] = "equal"
        hashes = self.package(h)
        for key, path in (("engine_sha256", a.exe), ("net_sha256", a.net)):
            p = Path(path)
            if not p.is_file() or file_sha256(p) != h[key]:
                raise Held(5, f"the {key[:-7]} file is not the header's {key}")
            hashes[key] = h[key]
        checks["hashes"] = hashes
        rows, d_text, top = [], None, -1
        for k in h["slots"]:
            row, d_text, top = self.slot_row(h, fp, k)
            rows.append(row)
        checks["chains"] = {"slots": len(rows), "verified": "every slot, by the worker's own reading"}
        checks["lease"] = {"d_in_force_utc": d_text, "hard_cutoff_utc": h["hard_cutoff_utc"],
                           "lease_end_utc": h["lease_end_utc"], "lease_start_utc": h["lease_start_utc"],
                           "run_fingerprint": fp, "schedules": top}
        newest, newest_name = 0.0, None
        for k in h["slots"]:
            j = self.root / f"w{k:03d}" / "journal.txt"
            if j.exists() and j.stat().st_mtime > newest:
                newest, newest_name = j.stat().st_mtime, f"w{k:03d}/journal.txt"
        t0 = time.monotonic()
        while not self.rd.synced():
            left = a.sync_wait - (time.monotonic() - t0)
            if left <= 0:
                raise Held(5, f"the clock is not synchronised after {a.sync_wait:g} s (D5: held until it is)")
            self.rd.sleep(min(5.0, left))
        now = self.rd.utc()
        if now < newest:
            raise Held(5, f"UTC now ({T(now)}) is before the newest journal time ({T(newest)}, {newest_name})")
        checks["clock"] = {"newest_journal": newest_name, "newest_journal_utc": T(newest) if newest_name else None,
                           "synchronised": True, "utc": T(now)}
        n = len(chain) + 1
        if n > 999:
            raise Held(4, "the RESUME grammar ends at 999")
        rec = {"at_utc": T(now), "checks": checks, "instance": now_inst, "instance_provable": True, "n": n,
               "new_boot_id": boot, "old_boot_id": h["boot_id"] if n == 1 else chain[-1][2]["new_boot_id"],
               "prev": "first" if n == 1 else sha256_bytes(chain[-1][1]), "run_fingerprint": fp, "schema": 2,
               "slots": rows}
        assert sorted(checks) == list(CHECKS)
        create_only(self.root / f"RESUME.{n}.json", canon(rec))
        self.say(f"bootguard: RESUME.{n}.json written for boot {boot} ({len(rows)} slots)")
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("root", "exe", "net", "manifest", "known-startup", "package-list"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--openings", default="")
    ap.add_argument("--sync-wait", type=float, default=900.0)
    ap.add_argument("--etc", default="/etc")
    ap.add_argument("--dmi", default="/sys/class/dmi/id")
    a = ap.parse_args()
    if not 0 <= a.sync_wait <= 86400:
        print("STOP: --sync-wait is 0 to 86400 seconds")
        return 2
    return BootGuard(a).run()


if __name__ == "__main__":
    sys.exit(main())

"""machine.py: the server day's machine check (specs/machine_qualification.md; SETUP_PLAN.md [2.3] "Section 4, what
the machine check reads", and section 4's table). It READS the machine and writes ONE record. Its only other write is
a create-only link probe in each volume, in a folder of its own that is removed after.

    python3 -I -B machine.py --request FILE --out FILE

The request (canonical JSON, integers only): flags (the variant's instruction flags), threads (CPUs needed),
extra_memory_bytes and extra_tasks (the day's EXTRA peak), nofile (open files a process needs), unit (the unit file,
forgeday.service), floor_bytes (kept free on every device), volumes (each: label, path, mount_point, need_bytes,
need_entries, exec; optional need_bytes_fallback, the packer's fallback envelope).

What is measured is the UNIT's chain, before it runs: the unit's own limits from `systemctl show` (its use is 0 while
it is not active, its own cgroup folder is read when it is), then every cgroup v2 level from its slice up to
/sys/fs/cgroup, each as limit minus current use (a ceiling is not headroom), and the host's available memory.
Processors: the check's own affinity (systemd starts the unit with PID 1's) cut by every level's cpuset and the
unit's AllowedCPUs, then the smallest quota. So the check runs after the unit is installed and enabled; it installs
nothing. Volumes are budgeted per device (summed), on ext4 and xfs only.

Exit: 0 QUALIFIED, 1 UNQUALIFIED, 2 a wrong call (an --out that exists, a request that is not the form, not Linux),
4 the record cannot be written. Every failure is one line naming the minimum, the value read and the value needed,
in the table's order (processor, memory, room, processes and files, service, kernel, tools): the first line is the
first failing minimum. A value that cannot be read or parsed fails, naming its file; it is never "no limit".
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker import canon, fsync_dir, parse_canon, write_new  # noqa: E402

PID_MAX_NEED = 4194304                  # process start times and pids must not wrap inside a day
SYSTEMD_MIN = 254
BUDGETED_FS = ("ext4", "xfs")           # st_dev is the free-space pool there (not on btrfs subvolumes)
CG = "/sys/fs/cgroup"
LEVEL_FILES = ("cpu.max", "cpu.stat", "cpuset.cpus.effective", "memory.current", "memory.max", "pids.current",
               "pids.max")
UNIT_PROPS = ("ActiveState", "AllowedCPUs", "CPUQuotaPerSecUSec", "ControlGroup", "LimitCORESoft",
              "LimitNOFILESoft", "LoadState", "MemoryMax", "Slice", "TasksMax", "UnitFileState", "User")
REQUEST_INTS = ("extra_memory_bytes", "extra_tasks", "floor_bytes", "nofile", "threads")
VOLUME_KEYS = ["exec", "label", "mount_point", "need_bytes", "need_entries", "path"]
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
UNREAD = "!"                            # a value that begins with it could not be read; the rest says why


class Ops:
    """The machine, read only (a test passes its own with the same methods)."""
    root = "/"

    def read(self, p: str):
        try:
            return (Path(self.root) / p.lstrip("/")).read_bytes().decode("ascii", "replace").strip()
        except FileNotFoundError:
            return None
        except OSError as e:
            return f"{UNREAD}unreadable: {e}"

    def exists(self, p: str) -> bool:
        return (Path(self.root) / p.lstrip("/")).exists()

    def run(self, argv) -> str:
        try:
            p = subprocess.run(argv, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired) as e:
            return f"{UNREAD}{argv[0]}: {e}"
        out = p.stdout.decode("ascii", "replace")
        return out if p.returncode == 0 else f"{UNREAD}{argv[0]} exit {p.returncode}: {out.strip()[-200:]}"

    def affinity(self):
        return sorted(os.sched_getaffinity(0))

    def realpath(self, p: str) -> str:
        return os.path.realpath(p)

    def space(self, p: str):
        s = os.statvfs(p)
        return {"dev": os.stat(p).st_dev, "free_bytes": s.f_bavail * s.f_frsize, "free_entries": s.f_favail}

    def pidfd(self) -> str:
        try:
            os.close(os.pidfd_open(os.getpid()))
            return "ok"
        except (AttributeError, OSError) as e:
            return f"{UNREAD}{e}"

    def which(self, name: str) -> str:
        return shutil.which(name) or (f"/usr/sbin/{name}" if os.path.isfile(f"/usr/sbin/{name}") else "")

    def own_limits(self) -> dict:
        import resource
        return {k: list(resource.getrlimit(getattr(resource, "RLIMIT_" + k.upper()))) for k in ("core", "nofile", "nproc")}

    def now(self) -> int:
        return int(time.time())

    def link_probe(self, folder: str) -> str:
        """Durable create-only publication on this volume: a link to a new name works, a second one is refused."""
        d = Path(folder) / f".machine_check_probe_{os.getpid()}"
        try:
            d.mkdir()                                   # create-only: an existing folder of that name is not ours
        except OSError as e:
            return f"{UNREAD}{e}"
        a, b = d / "a", d / "b"
        try:
            with open(a, "xb") as f:
                f.write(b"probe\n")
                f.flush()
                os.fsync(f.fileno())
            os.link(a, b)
            try:
                os.link(a, b)
                res = f"{UNREAD}a second link to an existing name was not refused"
            except FileExistsError:
                res = "ok"
            fsync_dir(d)
        except OSError as e:
            res = f"{UNREAD}{e}"
        for q in (b, a):
            try:
                q.unlink()
            except FileNotFoundError:
                pass
        try:
            d.rmdir()
        except OSError as e:
            res = res if res != "ok" else f"{UNREAD}the probe folder could not be removed: {e}"
        return res


# ---- reading ----------------------------------------------------------------------------------------------------
def unescape(s: str) -> str:
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), s)


def mounts(text):
    """(mount point, fstype, options) per line of /proc/self/mountinfo, in its order (the last of equals is on top)."""
    out = []
    for ln in (text or "").splitlines():
        a, sep, b = ln.partition(" - ")
        f, g = a.split(), b.split()
        if sep and len(f) >= 6 and len(g) >= 3:
            out.append((unescape(f[4]), g[0], sorted(set(f[5].split(",")) | set(g[2].split(",")))))
    return out


def mount_of(ms, path: str):
    best = None
    for mp, fs, opts in ms:
        if path == mp or mp == "/" or path.startswith(mp + "/"):
            if best is None or len(mp) >= len(best[0]):
                best = (mp, fs, opts)
    return best or ("", "", [])


def slice_path(name: str):
    """systemd's rule: a-b.slice lies in /a.slice/a-b.slice; -.slice is the root."""
    if name == "-.slice":
        return ""
    if not re.fullmatch(r"[A-Za-z0-9_]+(-[A-Za-z0-9_]+)*\.slice", name):
        return None
    parts = name[:-6].split("-")
    return "".join("/" + "-".join(parts[:i + 1]) + ".slice" for i in range(len(parts)))


def probe(ops, req) -> dict:
    rd = {"clock_utc": ops.now(), "boot_id": ops.read("/proc/sys/kernel/random/boot_id"),
          "pid1": ops.read("/proc/1/comm"), "affinity": ops.affinity(), "own_limits": ops.own_limits(),
          "pidfd": ops.pidfd(), "sshd": ops.which("sshd")}
    ms = mounts(ops.read("/proc/self/mountinfo"))
    rd["cgroup2"] = any(mp == CG and fs == "cgroup2" for mp, fs, _ in ms)
    groups: dict = {}
    for block in (ops.read("/proc/cpuinfo") or "").split("\n\n"):
        kv = dict((k.strip(), v.strip()) for k, _, v in (ln.partition(":") for ln in block.splitlines()))
        if kv.get("processor", "").isdigit():
            groups.setdefault(kv.get("flags", ""), []).append(int(kv["processor"]))
    rd["cpu_flags"] = groups
    mi = {}
    for ln in (ops.read("/proc/meminfo") or "").splitlines():
        k, _, v = ln.partition(":")
        if k in ("MemAvailable", "MemTotal"):
            mi[k] = v.strip()
    rd["meminfo"] = mi
    rd["kernel"] = {"loadavg": ops.read("/proc/loadavg"), "nr_open": ops.read("/proc/sys/fs/nr_open"),
                    "pid_max": ops.read("/proc/sys/kernel/pid_max"),
                    "threads_max": ops.read("/proc/sys/kernel/threads-max")}
    ver = ops.run(["systemctl", "--version"])
    rd["systemd_version"] = ver if ver.startswith(UNREAD) else (ver.splitlines() or [""])[0]
    show = ops.run(["systemctl", "show", req["unit"]] + [x for p in UNIT_PROPS for x in ("-p", p)])
    unit = {}
    if show.startswith(UNREAD):
        unit["error"] = show
    else:
        for ln in show.splitlines():
            k, _, v = ln.partition("=")
            if k in UNIT_PROPS:
                unit[k] = v
    rd["unit"] = unit
    cgp = unit.get("ControlGroup", "")
    rd["unit_current"] = {n: ops.read(CG + cgp + "/" + n) for n in ("cpu.stat", "memory.current", "pids.current")} \
        if unit.get("ActiveState") == "active" and cgp.startswith("/") else {}
    sp = slice_path(unit.get("Slice", ""))
    levels = []
    if sp is not None:
        while True:
            d = CG + sp
            lv = {"path": sp or "/", "exists": ops.exists(d)}
            lv.update({n: v for n in LEVEL_FILES for v in [ops.read(d + "/" + n)] if v is not None})
            levels.append(lv)
            if not sp:
                break
            sp = sp.rsplit("/", 1)[0]
    rd["levels"] = levels
    comp = {}
    for c in ("g++", "clang++"):
        out = ops.run([c, "--version"])
        comp[c] = "" if out.startswith(UNREAD) else (out.splitlines() or [""])[0]
    rd["compiler"] = comp
    rd["codecs"] = codecs()
    vols = []
    for v in req["volumes"]:
        p = ops.realpath(v["path"])
        mp, fs, opts = mount_of(ms, p)
        r = {"label": v["label"], "path": p, "mount_point_read": mp, "fstype": fs, "options": opts}
        try:
            r.update(ops.space(p))
        except OSError as e:
            r["space_error"] = f"{UNREAD}{e}"
        r["link_probe"] = ops.link_probe(p)
        vols.append(r)
    rd["volumes"] = vols
    return rd


def codecs() -> dict:
    data = bytes(range(256)) * 64
    out = {}
    for name, enc, dec in (("lzma", "compress", "decompress"), ("zlib", "compress", "decompress")):
        try:
            m = __import__(name)
            out[name] = getattr(m, dec)(getattr(m, enc)(data)) == data
        except Exception:  # noqa: BLE001 (a missing or broken codec is a failure, not a crash)
            out[name] = False
    out["sha256"] = hashlib.sha256(b"abc").hexdigest() == \
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    return out


# ---- deciding (a pure function of the readings and the request) --------------------------------------------------
class Bad(ValueError):
    pass


def limit(text, word=None):
    """An integer, None for `word` (no limit; a value without one has word None), or Bad: a missing, empty or
    unreadable value is never 'no limit'."""
    if text is None:
        raise Bad("was not read")
    if text.startswith(UNREAD):
        raise Bad(f"could not be read ({text[1:]})")
    if word is not None and text == word:
        return None
    if not re.fullmatch(r"[0-9]+", text):
        raise Bad(f"reads {text!r}, not a number" + (f" or {word!r}" if word else ""))
    return int(text)


def count(text) -> int:
    """A value that has no 'no limit' form (a current use, threads-max, pid_max, MemAvailable)."""
    v = limit(text)
    assert v is not None
    return v


def cpulist(text) -> set:
    if text is None or text.startswith(UNREAD) or not re.fullmatch(r"[0-9]+(-[0-9]+)?([, ][0-9]+(-[0-9]+)?)*", text):
        raise Bad(f"reads {text!r}, not a CPU list")
    out = set()
    for part in re.split(r"[, ]", text):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def quota_usec(text):
    """CPUQuotaPerSecUSec: 'infinity' or a span of whole s / ms / us (shortcut: a decimal span is refused, never guessed;
    the package's unit sets no quota)."""
    if text == "infinity":
        return None
    toks = re.findall(r"([0-9]+)(ms|us|s)(?: |$)", text or "")
    if not toks or " ".join(n + u for n, u in toks) != text:
        raise Bad(f"reads {text!r}, not a span this check reads")
    return sum(int(n) * {"s": 1000000, "ms": 1000, "us": 1}[u] for n, u in toks)


def admit(rd, req):
    """(failure lines in the table's order, notes)."""
    fails, notes = [], {}
    unit, uname = rd.get("unit", {}), req["unit"]
    cur = rd.get("unit_current", {})
    levels = rd.get("levels", [])

    def bad(row, where, name, e):
        fails.append(f"{row}: {where} {name} {e}")

    # processor
    if not rd.get("cgroup2"):
        fails.append(f"processor: no cgroup2 mount at {CG} (cgroup v1 or hybrid): this check reads v2 limits only")
    if "error" in unit or not levels:
        fails.append(f"processor: the unit {uname} or its slice could not be read "
                     f"({unit.get('error', 'Slice ' + repr(unit.get('Slice')))}): no limit of the chain is known")
    for lv in levels:
        if not lv["exists"]:
            fails.append(f"processor: the level {lv['path']} does not exist: its limits cannot be read")
    cpus, cwhere = set(rd.get("affinity", [])), "the affinity"
    try:
        if unit.get("AllowedCPUs"):
            cpus &= cpulist(unit["AllowedCPUs"])
            cwhere = f"{uname} AllowedCPUs"
    except Bad as e:
        bad("processor", uname, "AllowedCPUs", e)
    for lv in levels:
        if "cpuset.cpus.effective" in lv:
            try:
                s = cpulist(lv["cpuset.cpus.effective"])
                if not cpus <= s:
                    cwhere = f"{lv['path']} cpuset.cpus.effective"
                cpus &= s
            except Bad as e:
                bad("processor", lv["path"], "cpuset.cpus.effective", e)
    milli, where = 1000 * len(cpus), f"{len(cpus)} CPUs ({cwhere})"
    try:
        q = quota_usec(unit.get("CPUQuotaPerSecUSec"))
        if q is not None and q // 1000 < milli:
            milli, where = q // 1000, f"{uname} CPUQuotaPerSecUSec {unit['CPUQuotaPerSecUSec']}"
    except Bad as e:
        bad("processor", uname, "CPUQuotaPerSecUSec", e)
    for lv in levels:
        if "cpu.max" in lv:
            f = lv["cpu.max"].split()
            if len(f) != 2 or not re.fullmatch(r"max|[0-9]+", f[0]) or not re.fullmatch(r"[1-9][0-9]*", f[1]):
                bad("processor", lv["path"], "cpu.max", f"reads {lv['cpu.max']!r}, not 'QUOTA PERIOD' or 'max PERIOD'")
            elif f[0] != "max" and int(f[0]) * 1000 // int(f[1]) < milli:
                milli, where = int(f[0]) * 1000 // int(f[1]), f"{lv['path']} cpu.max {lv['cpu.max']!r}"
    notes["cpus"], notes["milli_cpus"] = sorted(cpus), milli
    if milli < 1000 * req["threads"]:
        fails.append(f"processor: {where} gives {milli} milli-CPUs < {1000 * req['threads']} needed")
    have = {c: set(line.split()) for line, cs in rd.get("cpu_flags", {}).items() for c in cs}
    for c in sorted(cpus - set(have)):
        fails.append(f"processor: CPU {c} is allowed but has no entry in /proc/cpuinfo")
    for flag in req["flags"]:
        miss = [c for c in sorted(cpus) if c in have and flag not in have[c]]
        if miss:
            fails.append(f"processor: flag {flag} missing on CPU {','.join(map(str, miss))}")

    # memory and tasks: limit minus current use at EVERY level
    chain = [(uname, unit.get("MemoryMax"), cur.get("memory.current", "0") if cur else "0",
              unit.get("TasksMax"), cur.get("pids.current", "0") if cur else "0", "infinity", "MemoryMax", "TasksMax")]
    chain += [(lv["path"], lv.get("memory.max"), lv.get("memory.current"), lv.get("pids.max"), lv.get("pids.current"),
               "max", "memory.max", "pids.max") for lv in levels]
    rooms = {"memory": [], "processes": []}
    for where, mmax, mcur, pmax, pcur, word, mname, pname in chain:
        for row, mx, cu, name, need, unitname in (("memory", mmax, mcur, mname, req["extra_memory_bytes"], "bytes"),
                                                  ("processes", pmax, pcur, pname, req["extra_tasks"], "tasks")):
            if mx is None and where != uname:
                continue                                # no file at this level: no limit there (the root has none)
            try:
                m = limit(mx, word)
            except Bad as e:
                bad(row, where, name, e)
                continue
            if m is None:
                continue
            curname = name.replace(".max", ".current").replace("MemoryMax", "memory.current").replace("TasksMax",
                                                                                                    "pids.current")
            try:
                c = count(cu)
            except Bad as e:
                bad(row, where, curname, e)
                continue
            rooms[row].append(m - c)
            if m - c < need:
                fails.append(f"{row}: {where} has {m - c} {unitname} free ({m} - {c}) < {need} needed")
    try:
        avail = count(rd.get("meminfo", {}).get("MemAvailable", "").removesuffix(" kB"))
        rooms["memory"].append(avail * 1024)
        if avail * 1024 < req["extra_memory_bytes"]:
            fails.append(f"memory: the host's MemAvailable {avail * 1024} bytes < {req['extra_memory_bytes']} needed")
    except Bad as e:
        bad("memory", "/proc/meminfo", "MemAvailable", e)
    notes["memory_room_bytes"] = min(rooms["memory"]) if rooms["memory"] else 0

    # room: per device, every volume on it summed, plus the floor once
    devs: dict = {}
    for v in req["volumes"]:
        r = next((x for x in rd.get("volumes", []) if x["label"] == v["label"]), None)
        if r is None:
            fails.append(f"room: volume {v['label']} was not read")
            continue
        tag = f"volume {v['label']} ({r['path']})"
        if r["mount_point_read"] != v["mount_point"]:
            fails.append(f"room: {tag} lies on the mount {r['mount_point_read']!r}, not on {v['mount_point']!r}")
        if r["fstype"] not in BUDGETED_FS:
            fails.append(f"room: {tag} is on {r['fstype']!r}: free space per device is budgeted on ext4 and xfs only")
        if "ro" in r["options"]:
            fails.append(f"room: {tag} is mounted read-only")
        if v["exec"] and "noexec" in r["options"]:
            fails.append(f"room: {tag} holds the engine and is mounted noexec")
        if r["link_probe"] != "ok":
            fails.append(f"room: {tag}: create-only publication (the link probe) failed: {r['link_probe'][1:]}")
        if "space_error" in r:
            fails.append(f"room: {tag}: its free space could not be read ({r['space_error'][1:]})")
            continue
        d = devs.setdefault(r["dev"], {"labels": [], "free": r["free_bytes"], "entries": r["free_entries"],
                                       "need": req["floor_bytes"], "need_fb": req["floor_bytes"], "need_entries": 0})
        d["labels"].append(v["label"])
        d["free"], d["entries"] = min(d["free"], r["free_bytes"]), min(d["entries"], r["free_entries"])
        d["need"] += v["need_bytes"]
        d["need_fb"] += v.get("need_bytes_fallback", v["need_bytes"])
        d["need_entries"] += v["need_entries"]
    notes["devices"] = {}
    for dev, d in sorted(devs.items()):
        names = " and ".join(d["labels"])
        if d["free"] < d["need"]:
            fails.append(f"room: device {dev} ({names}) has {d['free']} bytes free < {d['need']} needed "
                         f"(floor {req['floor_bytes']} included); short by {d['need'] - d['free']}")
        if d["entries"] < d["need_entries"]:
            fails.append(f"room: device {dev} ({names}) has {d['entries']} free entries < {d['need_entries']} needed")
        notes["devices"][str(dev)] = {"free_bytes": d["free"], "need_bytes": d["need"], "volumes": d["labels"],
                                      "fallback_covered": d["free"] >= d["need_fb"],
                                      "fallback_short_bytes": max(0, d["need_fb"] - d["free"])}

    # processes and files (the group limits are above; here the kernel and the unit's own)
    k = rd.get("kernel", {})
    try:
        tmax = count(k.get("threads_max"))
        la = (k.get("loadavg") or "").split()
        if len(la) < 4 or not re.fullmatch(r"[0-9]+/[0-9]+", la[3]):
            raise Bad(f"/proc/loadavg reads {k.get('loadavg')!r}, not five fields with R/N fourth")
        running = int(la[3].split("/")[1])
        if tmax - running < req["extra_tasks"]:
            fails.append(f"processes: the kernel's threads-max {tmax} - {running} running = {tmax - running} < "
                         f"{req['extra_tasks']} needed")
    except Bad as e:
        bad("processes", "the kernel", "threads-max", e)
    if unit.get("User", "") not in ("", "root"):
        fails.append(f"processes: {uname} runs as {unit['User']!r}: this check does not read that user's process "
                     f"count (the kernel does not limit root's)")
    try:
        nf = limit(unit.get("LimitNOFILESoft"), "infinity")
        if nf is not None and nf < req["nofile"]:
            fails.append(f"files: {uname} LimitNOFILESoft {nf} < {req['nofile']} needed")
    except Bad as e:
        bad("files", uname, "LimitNOFILESoft", e)
    if unit.get("LimitCORESoft") != "0":
        fails.append(f"files: {uname} LimitCORESoft reads {unit.get('LimitCORESoft')!r}: core dumps must be off (0)")

    # service
    if rd.get("pid1") != "systemd":
        fails.append(f"service: process 1 is {rd.get('pid1')!r}, not systemd")
    m = re.match(r"systemd ([0-9]+)( |$)", rd.get("systemd_version") or "")
    if not m or int(m.group(1)) < SYSTEMD_MIN:
        fails.append(f"service: systemctl --version reads {rd.get('systemd_version')!r}: systemd {SYSTEMD_MIN} or "
                     f"newer needed")
    if unit.get("LoadState") != "loaded" or unit.get("UnitFileState") != "enabled":
        fails.append(f"service: {uname} is LoadState {unit.get('LoadState')!r}, UnitFileState "
                     f"{unit.get('UnitFileState')!r}: the system manager would not start it after a reboot")

    # kernel
    try:
        pm = count(k.get("pid_max"))
        if pm < PID_MAX_NEED:
            fails.append(f"kernel: pid_max {pm} < {PID_MAX_NEED} needed")
    except Bad as e:
        bad("kernel", "/proc/sys/kernel", "pid_max", e)
    if rd.get("pidfd") != "ok":
        fails.append(f"kernel: os.pidfd_open does not work here ({rd.get('pidfd')!r}); the guard and the worker need it")
    if not UUID.fullmatch(rd.get("boot_id") or ""):
        fails.append(f"kernel: boot_id reads {rd.get('boot_id')!r}, not a UUID")

    # tools
    if not rd.get("sshd"):
        fails.append("tools: no sshd found (PATH and /usr/sbin)")
    if not any((rd.get("compiler") or {}).values()):
        fails.append("tools: no C++ compiler (g++ or clang++) answers --version")
    for c, ok in sorted((rd.get("codecs") or {}).items()):
        if not ok:
            fails.append(f"tools: the {c} round trip failed")
    if sorted(rd.get("codecs") or {}) != ["lzma", "sha256", "zlib"]:
        fails.append("tools: the codec checks are missing")
    return fails, notes


# ---- the call ---------------------------------------------------------------------------------------------------
def request_error(req):
    if not isinstance(req, dict) or sorted(req) != sorted(REQUEST_INTS + ("flags", "unit", "volumes")):
        return "the request needs exactly the keys " + ", ".join(sorted(REQUEST_INTS + ("flags", "unit", "volumes")))
    if any(type(req[k]) is not int or req[k] < 0 for k in REQUEST_INTS) or req["threads"] < 1:
        return "extra_memory_bytes, extra_tasks, floor_bytes, nofile: integers >= 0; threads: an integer >= 1"
    if not isinstance(req["flags"], list) or not all(isinstance(f, str) and re.fullmatch(r"[a-z0-9_]+", f)
                                                     for f in req["flags"]):
        return "flags: a list of instruction flag names"
    if not isinstance(req["unit"], str) or not re.fullmatch(r"[A-Za-z0-9_.@-]+\.service", req["unit"]):
        return "unit: a unit file name ending in .service"
    vs = req["volumes"]
    if not isinstance(vs, list) or not vs:
        return "volumes: a non-empty list"
    for v in vs:
        if not isinstance(v, dict) or sorted(set(v) - {"need_bytes_fallback"}) != VOLUME_KEYS:
            return "a volume needs exactly " + ", ".join(VOLUME_KEYS) + " (need_bytes_fallback optional)"
        if not (isinstance(v["label"], str) and re.fullmatch(r"[A-Za-z0-9_-]+", v["label"])
                and all(isinstance(v[k], str) and v[k].startswith("/") for k in ("path", "mount_point"))
                and all(type(v[k]) is int and v[k] >= 0 for k in ("need_bytes", "need_entries"))
                and type(v["exec"]) is bool
                and (type(v.get("need_bytes_fallback", 0)) is int and v.get("need_bytes_fallback", 0) >= 0)):
            return f"volume {v.get('label')!r}: label [A-Za-z0-9_-], absolute path and mount_point, integers >= 0, exec true/false"
    if len({v["label"] for v in vs}) != len(vs):
        return "volumes: a label stands twice"
    return None


def main(argv=None, ops=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--request", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists() or out.is_symlink():
        print(f"STOP: {out} exists; the record is written once, to a new name")
        return 2
    try:
        req = parse_canon(Path(a.request).read_bytes(), "the request")
    except (OSError, ValueError) as e:
        print(f"STOP: {e}")
        return 2
    err = request_error(req)
    if err:
        print(f"STOP: {err}")
        return 2
    if ops is None:
        if not sys.platform.startswith("linux"):
            print(f"STOP: the machine check reads a Linux machine; this is {sys.platform}")
            return 2
        ops = Ops()
    rd = probe(ops, req)
    fails, notes = admit(rd, req)
    verdict = "UNQUALIFIED" if fails else "QUALIFIED"
    rec = {"failures": fails, "notes": notes, "readings": rd, "request": req, "schema": 1, "verdict": verdict}
    try:
        write_new(out, canon(rec))
    except OSError as e:
        print(f"STOP: the record could not be written: {e}")
        return 4
    print(verdict)
    for ln in fails:
        print(ln)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

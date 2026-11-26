"""test_machine.py: A3g part 1, the machine check (run/machine.py; specs/machine_qualification.md; SETUP_PLAN.md
[2.3] "Section 4, what the machine check reads") against the known answers MQ1 to MQ24 written BEFORE it
(tmp/opus_scratch/a3g/KNOWN_ANSWERS_machine_by_opus.md on the PC, with its addendum 1; Opus, 24 Nov). Standard
library only.

    test_machine.py <run/machine.py> <a NEW folder> [plantN]

The folder of machine.py (it imports worker.py beside it) is copied into the new folder; a plant is applied to the
copy's machine.py. The machine is a FakeOps with the methods of machine.Ops, built from ONE clean fixture (MQ17)
and one change a case: probe() reads it (mountinfo, cpuinfo, meminfo, loadavg, the cgroup levels, systemctl's
lines, which answer only the properties asked for) and admit() decides, so the reading is tested together with the
decision. MQ15's codecs and MQ16's counters are also checked on the readings themselves. Two cases use the REAL
Ops: the create-only link probe in a folder of this test (it answers ok and leaves nothing behind) and in a folder
that does not exist (it answers with the reason, never ok). MQ18 (the live probe on a real Linux) is not this file's.
Added with this test, before its first run (not in the known answers file): MQ3e (threads-max 400 with 398 threads
existing and 4 needed: the existing threads are subtracted), MQ14b (an EMPTY memory.current, MemAvailable,
threads-max or pid_max fails naming its file: the fix of 09:37; machine_before_count.py, the file before that fix,
must fail here), MQ23b (an ACTIVE unit: its own cgroup's memory.current is subtracted from MemoryMax).
PLANTS (each must make the test fail): plant1 cpuset ignored (MQ1c); plant2 only the leaf's cpu.max (MQ1b); plant3
CPU 0's flags for every CPU (MQ2, the stand-in); plant4 ceilings alone (MQ3, the stand-in); plant5 the host's
MemAvailable not compared (MQ3c); plant6 threads-max without the existing threads (MQ3e); plant7 the floor once per
VOLUME (MQ4); plant8 room per volume, not summed per device (MQ4); plant9 the per-mount options dropped (MQ5);
plant10 entries not compared (MQ6); plant11 the link probe's answer ignored (MQ7); plant12 btrfs budgeted (MQ8);
plant13 the mount point not compared (MQ9); plant14 systemd 253 accepted (MQ10); plant15 UnitFileState not read
(MQ10); plant16 pid_max 32768 accepted (MQ11); plant17 the check's own nofile instead of the unit's (MQ12); plant18
a value that is not a number read as no limit (MQ14); plant19 cgroup2 not demanded (MQ19); plant20 the fallback
note from the normal need (MQ20); plant21 LimitCORE infinity accepted (MQ21); plant22 User not read (MQ22); plant23
the unit level skipped (MQ23); plant24 an existing --out checked only as a link (MQ24); plant25 negative integers
accepted (MQ24); plant26 cpu.stat not recorded (MQ16); plant27 any boot_id accepted (MQ13); plant28 an empty sshd
path accepted (MQ15); plant29 an active unit's own use not read (MQ23b); plant30 an empty value read as no limit
(MQ14b); plant32 PID 1 not read (MQ10); plant33 pidfd not read (MQ11); plant34 a float in the record (MQ17); plant35
the link probe leaves its files (the real probe); plant36 a clang++ alone accepted (MQ15b, Fable's M3); plant37 a
crash inside the check let out (Fable's M2). There is no plant31 (the number was never used): the plants are 1 to 30
and 32 to 37.
"""
import copy
import hashlib
import os
import shutil
import sys
import traceback
from pathlib import Path

if len(sys.argv) < 3:
    print("usage: test_machine.py <run/machine.py> <a NEW folder> [plantN]")
    sys.exit(2)
SRC, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
PLANT = sys.argv[3] if len(sys.argv) > 3 else None
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
shutil.copytree(SRC.parent, WORK / "run", ignore=shutil.ignore_patterns("__pycache__"))
MOD = WORK / "run" / "machine.py"
shutil.copyfile(SRC, MOD)
PLANTS = {
    "plant1": ("                cpus &= s\n", "                pass\n"),
    "plant2": ('    for lv in levels:\n        if "cpu.max" in lv:', '    for lv in levels[:1]:\n        if "cpu.max" in lv:'),
    "plant3": ('    have = {c: set(line.split()) for line, cs in rd.get("cpu_flags", {}).items() for c in cs}',
               '    have = {c: set(next(iter(rd.get("cpu_flags", {}))).split()) for line, cs in rd.get("cpu_flags", {}).items() for c in cs}'),
    "plant4": ("            if m - c < need:", "            if m < need:"),
    "plant5": ('        if avail * 1024 < req["extra_memory_bytes"]:', "        if avail * 1024 < 0:"),
    "plant6": ('        if tmax - running < req["extra_tasks"]:', '        if tmax < req["extra_tasks"]:'),
    "plant7": ('        d["need"] += v["need_bytes"]\n', '        d["need"] += v["need_bytes"] + req["floor_bytes"]\n'),
    "plant8": ('        d["need"] += v["need_bytes"]\n', '        d["need"] = max(d["need"], req["floor_bytes"] + v["need_bytes"])\n'),
    "plant9": ('sorted(set(f[5].split(",")) | set(g[2].split(",")))', 'sorted(set(g[2].split(",")))'),
    "plant10": ('        if d["entries"] < d["need_entries"]:', '        if d["entries"] < 0:'),
    "plant11": ('        if r["link_probe"] != "ok":', '        if r["link_probe"] is None:'),
    "plant12": ('BUDGETED_FS = ("ext4", "xfs")', 'BUDGETED_FS = ("ext4", "xfs", "btrfs")'),
    "plant13": ('        if r["mount_point_read"] != v["mount_point"]:', '        if not r["mount_point_read"]:'),
    "plant14": ("SYSTEMD_MIN = 254", "SYSTEMD_MIN = 253"),
    "plant15": ('    if unit.get("LoadState") != "loaded" or unit.get("UnitFileState") != "enabled":',
                '    if unit.get("LoadState") != "loaded":'),
    "plant16": ("PID_MAX_NEED = 4194304", "PID_MAX_NEED = 32768"),
    "plant17": ('        nf = limit(unit.get("LimitNOFILESoft"), "infinity")', '        nf = rd["own_limits"]["nofile"][0]'),
    "plant18": ('    if not re.fullmatch(r"[0-9]+", text):\n        raise Bad(',
                '    if not re.fullmatch(r"[0-9]+", text):\n        return None\n        raise Bad('),
    "plant19": ('    if not rd.get("cgroup2"):', '    if rd.get("cgroup2") is None:'),
    "plant20": ('"fallback_covered": d["free"] >= d["need_fb"],', '"fallback_covered": d["free"] >= d["need"],'),
    "plant21": ('    if unit.get("LimitCORESoft") != "0":', '    if unit.get("LimitCORESoft") not in ("0", "infinity"):'),
    "plant22": ('    if unit.get("User", "") not in ("", "root"):', "    if False:"),
    "plant23": ('    chain = [(uname, unit.get("MemoryMax"),', '    chain = [] and [(uname, unit.get("MemoryMax"),'),
    "plant24": ("    if out.exists() or out.is_symlink():", "    if out.is_symlink():"),
    "plant25": ("    if any(type(req[k]) is not int or req[k] < 0 for k in REQUEST_INTS)",
                "    if any(type(req[k]) is not int for k in REQUEST_INTS)"),
    "plant26": ('LEVEL_FILES = ("cpu.max", "cpu.stat", "cpuset.cpus.effective",', 'LEVEL_FILES = ("cpu.max", "cpuset.cpus.effective",'),
    "plant27": ('UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")', 'UUID = re.compile(r".+")'),
    "plant28": ('    if not rd.get("sshd"):', '    if rd.get("sshd") is None:'),
    "plant29": ('if unit.get("ActiveState") == "active" and cgp.startswith("/") else {}',
                'if unit.get("ActiveState") == "running" and cgp.startswith("/") else {}'),
    "plant30": ("    v = limit(text)\n", '    v = limit(text, "")\n'),
    "plant32": ('    if rd.get("pid1") != "systemd":', '    if rd.get("pid1") is None:'),
    "plant33": ('    if rd.get("pidfd") != "ok":', '    if rd.get("pidfd") is None:'),
    "plant34": ('"schema": 1, "verdict": verdict}', '"schema": 1.0, "verdict": verdict}'),
    "plant35": ("                q.unlink()\n", "                pass\n"),
    "plant36": ('    if not (rd.get("compiler") or {}).get("g++"):', '    if not any((rd.get("compiler") or {}).values()):'),
    "plant37": ('        print(f"STOP: the machine check failed inside itself, no record: {type(e).__name__}: {e}")\n'
                '        return 4\n', "        raise\n"),
}
if PLANT:
    text = MOD.read_bytes().decode("utf-8")
    if PLANT not in PLANTS or text.count(PLANTS[PLANT][0]) != 1:
        print(f"STOP: {PLANT}: no such plant, or its text does not stand exactly once")
        sys.exit(2)
    MOD.write_bytes(text.replace(*PLANTS[PLANT]).encode("utf-8"))
    print(f"PLANT {PLANT} applied to the copy")
print(f"testing {SRC} (copy sha256 {hashlib.sha256(MOD.read_bytes()).hexdigest()[:16]}, worker.py "
      f"{hashlib.sha256((WORK / 'run' / 'worker.py').read_bytes()).hexdigest()[:16]})", flush=True)
sys.path.insert(0, str(WORK / "run"))
import machine as M  # noqa: E402
from worker import canon, parse_canon  # noqa: E402

RESULTS = []


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {str(got)[:400]}" + ("" if ok else f"; want {str(want)[:400]}"),
          flush=True)
    return ok


# ---- the machine ------------------------------------------------------------------------------------------------
GB, GiB = 10 ** 9, 2 ** 30
V4 = ["avx2", "avx512bw", "avx512f", "avx512vl", "bmi2", "fma"]
AVX2 = ["avx2", "bmi2", "fma"]
F_V4 = ("fpu vme de pse tsc msr sse sse2 ssse3 fma cx16 sse4_1 sse4_2 movbe popcnt aes xsave avx f16c bmi1 avx2 bmi2 "
        "avx512f avx512dq avx512cd avx512bw avx512vl")
F_NO512 = "fpu vme de pse tsc msr sse sse2 ssse3 fma cx16 sse4_1 sse4_2 movbe popcnt aes xsave avx f16c bmi1 avx2 bmi2"
STAT_S = "usage_usec 9000\nuser_usec 6000\nsystem_usec 3000\nnr_periods 0\nnr_throttled 0\nthrottled_usec 0"
STAT_R = "usage_usec 90000\nuser_usec 60000\nsystem_usec 30000"
MOUNTS = {
    "/": "22 1 8:1 / / rw,relatime shared:1 - ext4 /dev/sda1 rw,errors=remount-ro",
    "/sys": "25 22 0:23 / /sys rw,nosuid,nodev,noexec,relatime shared:7 - sysfs sysfs rw",
    "/sys/fs/cgroup": "30 25 0:26 / /sys/fs/cgroup rw,nosuid,nodev,noexec,relatime shared:9 - cgroup2 cgroup2 "
                      "rw,nsdelegate,memory_recursiveprot",
    "/srv/day": "40 22 259:1 / /srv/day rw,relatime shared:20 - ext4 /dev/nvme0n1p1 rw",
    "/srv/data": "41 22 259:2 / /srv/data rw,relatime shared:21 - xfs /dev/nvme1n1p1 rw,attr2,inode64",
}
REQ = {"extra_memory_bytes": 2 * GiB, "extra_tasks": 4, "flags": V4, "floor_bytes": 10 * GB, "nofile": 4096,
       "threads": 4, "unit": "forgeday.service",
       "volumes": [{"exec": True, "label": "A", "mount_point": "/srv/day", "need_bytes": 60 * GB, "need_entries": 1000,
                    "path": "/srv/day/a"},
                   {"exec": False, "label": "B", "mount_point": "/srv/data", "need_bytes": 55 * GB,
                    "need_entries": 1000, "path": "/srv/data/b"}]}


def cpuinfo(flags_by_cpu):
    return "\n\n".join(f"processor\t: {c}\nvendor_id\t: AuthenticAMD\nflags\t\t: {fl}\nbugs\t\t: sysret_ss_attrs"
                       for c, fl in sorted(flags_by_cpu.items())) + "\n\n"


def clean():
    """MQ17's machine: v4 flags on 8 CPUs, no quota, no group limits, ext4 and xfs devices, systemd 255 with the
    unit loaded and enabled, pid_max 4194304, pidfd, sshd, a compiler."""
    return {
        "files": {
            "/proc/sys/kernel/random/boot_id": "6f1c2a9e-3b4d-4e5f-8a7b-9c0d1e2f3a4b",
            "/proc/1/comm": "systemd",
            "/proc/self/mountinfo": "\n".join(MOUNTS.values()),
            "/proc/cpuinfo": cpuinfo({c: F_V4 for c in range(8)}),
            "/proc/meminfo": "MemTotal:       65536000 kB\nMemFree:        30000000 kB\nMemAvailable:   60000000 kB",
            "/proc/loadavg": "0.50 0.40 0.30 2/400 12345",
            "/proc/sys/fs/nr_open": "1048576",
            "/proc/sys/kernel/pid_max": "4194304",
            "/proc/sys/kernel/threads-max": "254000",
            "/sys/fs/cgroup/system.slice/cpu.max": "max 100000",
            "/sys/fs/cgroup/system.slice/cpu.stat": STAT_S,
            "/sys/fs/cgroup/system.slice/cpuset.cpus.effective": "0-7",
            "/sys/fs/cgroup/system.slice/memory.current": "1000000000",
            "/sys/fs/cgroup/system.slice/memory.max": "max",
            "/sys/fs/cgroup/system.slice/pids.current": "60",
            "/sys/fs/cgroup/system.slice/pids.max": "max",
            "/sys/fs/cgroup/cpu.stat": STAT_R,
            "/sys/fs/cgroup/cpuset.cpus.effective": "0-7",
        },
        "dirs": {"/sys/fs/cgroup", "/sys/fs/cgroup/system.slice"},
        "unit": {"ActiveState": "inactive", "AllowedCPUs": "", "CPUQuotaPerSecUSec": "infinity", "ControlGroup": "",
                 "LimitCORESoft": "0", "LimitNOFILESoft": "65536", "LoadState": "loaded", "MemoryMax": "infinity",
                 "Slice": "system.slice", "TasksMax": "infinity", "UnitFileState": "enabled", "User": ""},
        "systemd": "systemd 255 (255.4-1ubuntu8)\n+PAM +AUDIT +SELINUX +APPARMOR\n",
        "compilers": {"g++": "g++ (Ubuntu 13.2.0-23ubuntu4) 13.2.0\nCopyright (C) 2023\n"},
        "affinity": list(range(8)),
        "space": {"/srv/day/a": {"dev": 66305, "free_bytes": 200 * GB, "free_entries": 10 ** 7},
                  "/srv/data/b": {"dev": 66306, "free_bytes": 200 * GB, "free_entries": 10 ** 7}},
        "probes": {}, "pidfd": "ok", "sshd": "/usr/sbin/sshd",
    }


class FakeOps:
    """machine.Ops's methods over a fixture; every call is recorded (MQ24: nothing is read before the call is
    found right)."""
    root = "/"

    def __init__(self, fx):
        self.fx, self.calls = fx, []

    def read(self, p):
        self.calls.append(("read", p))
        return self.fx["files"].get(p)

    def exists(self, p):
        self.calls.append(("exists", p))
        return p in self.fx["dirs"]

    def run(self, argv):
        argv = list(argv)
        self.calls.append(("run", tuple(argv)))
        if argv == ["systemctl", "--version"]:
            return self.fx["systemd"]
        if argv[:3] == ["systemctl", "show", "forgeday.service"]:
            rest = argv[3:]
            if len(rest) % 2 or any(rest[i] != "-p" for i in range(0, len(rest), 2)):
                return "!systemctl exit 1: bad arguments"
            u = self.fx["unit"]
            return "".join(f"{k}={u[k]}\n" for k in sorted(u) if k in rest[1::2])   # only what was asked for
        if len(argv) == 2 and argv[1] == "--version" and argv[0] in self.fx["compilers"]:
            return self.fx["compilers"][argv[0]]
        return f"!{argv[0]}: [Errno 2] No such file or directory"

    def affinity(self):
        self.calls.append(("affinity",))
        return list(self.fx["affinity"])

    def realpath(self, p):
        self.calls.append(("realpath", p))
        return p

    def space(self, p):
        self.calls.append(("space", p))
        if p not in self.fx["space"]:
            raise OSError(f"[Errno 2] No such file or directory: {p!r}")
        return dict(self.fx["space"][p])

    def pidfd(self):
        self.calls.append(("pidfd",))
        return self.fx["pidfd"]

    def which(self, name):
        self.calls.append(("which", name))
        return self.fx["sshd"] if name == "sshd" else ""

    def own_limits(self):
        self.calls.append(("own_limits",))
        return {"core": [0, 0], "nofile": [65536, 65536], "nproc": [127000, 127000]}

    def now(self):
        self.calls.append(("now",))
        return 1764000000

    def link_probe(self, folder):
        self.calls.append(("link_probe", folder))
        return self.fx["probes"].get(folder, "ok")


def req_with(**kw):
    r = copy.deepcopy(REQ)
    r.update(kw)
    return r


def case(name, fx, want, req=None, notes=None, after=None):
    """probe + admit on fx; `after(rd)` may change the readings before the decision (MQ15's codecs)."""
    req = REQ if req is None else req
    try:
        rd = M.probe(FakeOps(fx), req)
        if after:
            after(rd)
        fails, nt = M.admit(rd, req)
    except Exception as e:  # noqa: BLE001 (a crash is a FAIL of this case, never of the whole test)
        return check(name, f"CRASH {type(e).__name__}: {e}", want)
    ok = check(name, fails, want)
    for k, v in (notes or {}).items():
        ok = check(f"{name} notes[{k!r}]", nt.get(k), v) and ok
    return ok


def nested(fx):
    """The unit in forge-day.slice: levels /forge.slice/forge-day.slice (leaf), /forge.slice (parent), / (root)."""
    fx["unit"]["Slice"] = "forge-day.slice"
    fx["dirs"] = {"/sys/fs/cgroup", "/sys/fs/cgroup/forge.slice", "/sys/fs/cgroup/forge.slice/forge-day.slice"}
    for lv in ("/sys/fs/cgroup/forge.slice", "/sys/fs/cgroup/forge.slice/forge-day.slice"):
        fx["files"][lv + "/cpuset.cpus.effective"] = "0-7"
        fx["files"][lv + "/cpu.stat"] = STAT_S
    return fx


def lv_files(fx, level, **kw):
    for k, v in kw.items():
        fx["files"][f"/sys/fs/cgroup{level}/{k.replace('_', '.')}"] = v
    return fx


# ---- the cases --------------------------------------------------------------------------------------------------
def cases():
    # MQ17: the clean machine (decision and notes; the call itself below)
    fx = clean()
    rd = M.probe(FakeOps(fx), REQ)
    fails, nt = M.admit(rd, REQ)
    check("MQ17 clean: no failure", fails, [])
    check("MQ17 clean: notes", nt, {"cpus": list(range(8)), "milli_cpus": 8000, "memory_room_bytes": 60000000 * 1024,
                                    "devices": {"66305": {"fallback_covered": True, "fallback_short_bytes": 0,
                                                          "free_bytes": 200 * GB, "need_bytes": 70 * GB,
                                                          "volumes": ["A"]},
                                                "66306": {"fallback_covered": True, "fallback_short_bytes": 0,
                                                          "free_bytes": 200 * GB, "need_bytes": 65 * GB,
                                                          "volumes": ["B"]}}})
    # MQ16: cpu.stat of EVERY level recorded; a throttle count changes no verdict
    check("MQ16 cpu.stat at every level", [lv.get("cpu.stat") for lv in rd["levels"]], [STAT_S, STAT_R])
    check("MQ16 levels read", [lv["path"] for lv in rd["levels"]], ["/system.slice", "/"])
    fx = clean()
    fx["files"]["/sys/fs/cgroup/system.slice/cpu.stat"] = STAT_S.replace("nr_throttled 0", "nr_throttled 999")
    case("MQ16 throttled 999: no verdict", fx, [])
    # MQ1, MQ1b, MQ1c: processors
    fx = clean()
    fx["affinity"] = [0, 1, 2, 3, 4]
    lv_files(fx, "/system.slice", cpu_max="400000 100000")
    case("MQ1 quota 4,000 milli-CPUs, 5 needed", fx,
         ["processor: /system.slice cpu.max '400000 100000' gives 4000 milli-CPUs < 5000 needed"], req_with(threads=5))
    case("MQ1 quota 4,000 milli-CPUs, 4 needed", copy.deepcopy(fx), [])
    fx = nested(clean())
    fx["affinity"] = [0, 1, 2, 3, 4]
    lv_files(fx, "/forge.slice/forge-day.slice", cpu_max="max 100000")
    lv_files(fx, "/forge.slice", cpu_max="400000 100000")
    case("MQ1b the parent's quota binds", fx,
         ["processor: /forge.slice cpu.max '400000 100000' gives 4000 milli-CPUs < 5000 needed"], req_with(threads=5))
    fx = clean()
    fx["affinity"] = [0, 1, 2, 3, 4]
    lv_files(fx, "/system.slice", cpuset_cpus_effective="0-2")
    case("MQ1c cpuset 0-2 of affinity 0-4", fx,
         ["processor: 3 CPUs (/system.slice cpuset.cpus.effective) gives 3000 milli-CPUs < 4000 needed"],
         notes={"cpus": [0, 1, 2], "milli_cpus": 3000})
    # MQ2: flags on EVERY allowed CPU
    fx = clean()
    fx["affinity"] = [0, 1, 2, 3]
    fx["files"]["/proc/cpuinfo"] = cpuinfo({c: (F_NO512 if c == 2 else F_V4) for c in range(8)})
    case("MQ2 v4 requested, CPU 2 without avx512", fx,
         ["processor: flag avx512bw missing on CPU 2", "processor: flag avx512f missing on CPU 2",
          "processor: flag avx512vl missing on CPU 2"])
    case("MQ2 AVX2 requested", copy.deepcopy(fx), [], req_with(flags=AVX2))
    # MQ3 to MQ3e: memory and tasks, limit minus current use at every level, the host, the kernel
    fx = nested(clean())
    lv_files(fx, "/forge.slice/forge-day.slice", memory_max=str(4 * GiB), memory_current="0", pids_max="512",
             pids_current="1")
    lv_files(fx, "/forge.slice", memory_max=str(8 * GiB), memory_current=str(7 * GiB), pids_max="512",
             pids_current="510")
    fx["files"]["/proc/meminfo"] = "MemTotal:       67108864 kB\nMemAvailable:   33554432 kB"
    case("MQ3 the parent's headroom binds", fx,
         [f"memory: /forge.slice has {GiB} bytes free ({8 * GiB} - {7 * GiB}) < {2 * GiB} needed",
          "processes: /forge.slice has 2 tasks free (512 - 510) < 4 needed"], notes={"memory_room_bytes": GiB})
    lv_files(fx, "/forge.slice", memory_current=str(5 * GiB), pids_current="506")
    case("MQ3b 3 GiB and 6 tasks free", fx, [])
    fx = clean()
    fx["files"]["/proc/meminfo"] = "MemTotal:       2097152 kB\nMemAvailable:   1048576 kB"
    case("MQ3c the host's MemAvailable", fx, [f"memory: the host's MemAvailable {GiB} bytes < {2 * GiB} needed"])
    fx = clean()
    fx["files"]["/proc/sys/kernel/threads-max"] = "3"
    fx["files"]["/proc/loadavg"] = "0.00 0.00 0.00 1/2 999"
    case("MQ3d the kernel's threads-max", fx, ["processes: the kernel's threads-max 3 - 2 running = 1 < 4 needed"])
    fx = clean()
    fx["files"]["/proc/sys/kernel/threads-max"] = "400"
    fx["files"]["/proc/loadavg"] = "1.00 1.00 1.00 3/398 999"
    case("MQ3e threads-max 400 with 398 existing", fx,
         ["processes: the kernel's threads-max 400 - 398 running = 2 < 4 needed"])
    # MQ4: room per device, summed, the floor once
    one = req_with(volumes=[dict(REQ["volumes"][0]), dict(REQ["volumes"][1], mount_point="/srv/day", path="/srv/day/b")])
    fx = clean()
    fx["space"] = {"/srv/day/a": {"dev": 66305, "free_bytes": 120 * GB, "free_entries": 10 ** 7},
                   "/srv/day/b": {"dev": 66305, "free_bytes": 120 * GB, "free_entries": 10 ** 7}}
    case("MQ4 one device, 120 GB for 60 + 55 + 10", fx,
         ["room: device 66305 (A and B) has 120000000000 bytes free < 125000000000 needed "
          "(floor 10000000000 included); short by 5000000000"], one)
    fx = clean()
    for p in fx["space"]:
        fx["space"][p]["free_bytes"] = 120 * GB
    case("MQ4 two devices of 120 GB", fx, [])
    # MQ5: noexec matters for the engine's volume only
    fx = clean()
    fx["files"]["/proc/self/mountinfo"] = "\n".join(MOUNTS.values()).replace(
        "/srv/day rw,relatime shared:20", "/srv/day rw,noexec,relatime shared:20")
    case("MQ5 the engine's volume noexec", fx, ["room: volume A (/srv/day/a) holds the engine and is mounted noexec"])
    fx = clean()
    fx["files"]["/proc/self/mountinfo"] = "\n".join(MOUNTS.values()).replace(
        "/srv/data rw,relatime shared:21", "/srv/data rw,nosuid,noexec,relatime shared:21")
    case("MQ5 a data volume noexec", fx, [])
    # MQ6: entries
    fx = clean()
    fx["space"]["/srv/day/a"]["free_entries"] = 100
    case("MQ6 free entries 100 < 1000", fx, ["room: device 66305 (A) has 100 free entries < 1000 needed"])
    # MQ7: the create-only link probe
    fx = clean()
    fx["probes"]["/srv/day/a"] = "!a second link to an existing name was not refused"
    case("MQ7 the link probe fails", fx, ["room: volume A (/srv/day/a): create-only publication (the link probe) "
                                          "failed: a second link to an existing name was not refused"])
    # MQ8: btrfs is not budgeted (xfs is: the clean machine's B)
    fx = clean()
    fx["files"]["/proc/self/mountinfo"] = "\n".join(MOUNTS.values()).replace(
        "40 22 259:1 / /srv/day rw,relatime shared:20 - ext4 /dev/nvme0n1p1 rw",
        "40 22 0:45 /day /srv/day rw,relatime shared:20 - btrfs /dev/nvme0n1p1 rw,ssd,space_cache=v2,subvol=/day")
    case("MQ8 btrfs", fx, ["room: volume A (/srv/day/a) is on 'btrfs': free space per device is budgeted on ext4 and "
                           "xfs only"])
    # MQ9: the volume did not mount
    fx = clean()
    fx["files"]["/proc/self/mountinfo"] = "\n".join(v for k, v in MOUNTS.items() if k != "/srv/day")
    case("MQ9 /srv/day not mounted", fx, ["room: volume A (/srv/day/a) lies on the mount '/', not on '/srv/day'"])
    # MQ10: the service manager
    fx = clean()
    fx["files"]["/proc/1/comm"] = "init"
    case("MQ10 PID 1 not systemd", fx, ["service: process 1 is 'init', not systemd"])
    fx = clean()
    fx["systemd"] = "systemd 253 (253.5-1)\n+PAM\n"
    case("MQ10 systemd 253", fx, ["service: systemctl --version reads 'systemd 253 (253.5-1)': systemd 254 or newer "
                                  "needed"])
    fx = clean()
    fx["unit"]["LoadState"] = "not-found"
    case("MQ10 unit not loaded", fx, ["service: forgeday.service is LoadState 'not-found', UnitFileState 'enabled': the "
                                      "system manager would not start it after a reboot"])
    fx = clean()
    fx["unit"]["UnitFileState"] = "disabled"
    case("MQ10 unit not enabled", fx, ["service: forgeday.service is LoadState 'loaded', UnitFileState 'disabled': the "
                                       "system manager would not start it after a reboot"])
    # MQ11: the kernel
    fx = clean()
    fx["files"]["/proc/sys/kernel/pid_max"] = "32768"
    case("MQ11 pid_max 32768", fx, ["kernel: pid_max 32768 < 4194304 needed"])
    fx = clean()
    fx["pidfd"] = "![Errno 38] Function not implemented"
    case("MQ11 no pidfd", fx, ["kernel: os.pidfd_open does not work here ('![Errno 38] Function not implemented'); the "
                               "guard and the worker need it"])
    # MQ12: the unit's EFFECTIVE limits, not the check's own (its own nofile is 65536)
    fx = clean()
    fx["unit"]["LimitNOFILESoft"] = "1024"
    case("MQ12 the unit's nofile 1024", fx, ["files: forgeday.service LimitNOFILESoft 1024 < 4096 needed"])
    fx = clean()
    fx["unit"]["TasksMax"] = "3"
    case("MQ12 the unit's TasksMax 3", fx, ["processes: forgeday.service has 3 tasks free (3 - 0) < 4 needed"])
    fx = clean()
    fx["unit"]["LimitNOFILESoft"] = "infinity"
    case("MQ12 nofile infinity", fx, [])
    # MQ13
    fx = clean()
    fx["files"]["/proc/sys/kernel/random/boot_id"] = "not-a-uuid"
    case("MQ13 boot_id", fx, ["kernel: boot_id reads 'not-a-uuid', not a UUID"])
    # MQ14: a value that is not a number fails, naming its file; it is never "no limit"
    for name, kw, want in (
            ("memory.max", {"memory_max": "12abc"}, "memory: /system.slice memory.max reads '12abc', not a number or 'max'"),
            ("memory.current", {"memory_max": str(8 * GiB), "memory_current": "12abc"},
             "memory: /system.slice memory.current reads '12abc', not a number"),
            ("pids.max", {"pids_max": "12abc"}, "processes: /system.slice pids.max reads '12abc', not a number or 'max'"),
            ("pids.current", {"pids_max": "512", "pids_current": "12abc"},
             "processes: /system.slice pids.current reads '12abc', not a number"),
            ("cpu.max", {"cpu_max": "12abc 100000"},
             "processor: /system.slice cpu.max reads '12abc 100000', not 'QUOTA PERIOD' or 'max PERIOD'")):
        case(f"MQ14 {name} '12abc'", lv_files(clean(), "/system.slice", **kw), [want])
    # MQ14b (added with the test): an EMPTY value fails the same way (the fix of 09:37)
    case("MQ14b memory.current ''", lv_files(clean(), "/system.slice", memory_max=str(8 * GiB), memory_current=""),
         ["memory: /system.slice memory.current reads '', not a number"])
    fx = clean()
    fx["files"]["/proc/meminfo"] = "MemTotal:       65536000 kB\nMemAvailable:"
    case("MQ14b MemAvailable ''", fx, ["memory: /proc/meminfo MemAvailable reads '', not a number"])
    fx = clean()
    fx["files"]["/proc/sys/kernel/threads-max"] = ""
    case("MQ14b threads-max ''", fx, ["processes: the kernel threads-max reads '', not a number"])
    fx = clean()
    fx["files"]["/proc/sys/kernel/pid_max"] = ""
    case("MQ14b pid_max ''", fx, ["kernel: /proc/sys/kernel pid_max reads '', not a number"])
    # MQ15: the tools
    fx = clean()
    fx["sshd"] = ""
    case("MQ15 no sshd", fx, ["tools: no sshd found (PATH and /usr/sbin)"])
    fx = clean()
    fx["compilers"] = {}
    case("MQ15 no compiler", fx, ["tools: g++ does not answer --version (the day's Linux build calls g++; a clang++ alone "
                                  "is not it)"])
    fx = clean()
    fx["compilers"] = {"clang++": "Ubuntu clang version 18.1.3 (1ubuntu1)\n"}
    case("MQ15b clang++ alone (Fable's M3)", fx, ["tools: g++ does not answer --version (the day's Linux build calls g++; a clang++ alone "
                                  "is not it)"])
    case("MQ15 the lzma round trip fails", clean(), ["tools: the lzma round trip failed"],
         after=lambda rd: rd["codecs"].__setitem__("lzma", False))
    check("MQ15 the real codecs here", M.codecs(), {"lzma": True, "sha256": True, "zlib": True})
    # MQ19: cgroup v2 at /sys/fs/cgroup
    fx = clean()
    fx["files"]["/proc/self/mountinfo"] = "\n".join(MOUNTS.values()).replace(
        "- cgroup2 cgroup2 rw,nsdelegate,memory_recursiveprot", "- tmpfs tmpfs ro,mode=755")
    case("MQ19 no cgroup2 mount", fx, ["processor: no cgroup2 mount at /sys/fs/cgroup (cgroup v1 or hybrid): this check "
                                       "reads v2 limits only"])
    # MQ20: the fallback envelope is recorded, never a failure
    fb = req_with(volumes=[dict(REQ["volumes"][0], need_bytes_fallback=70 * GB),
                           dict(REQ["volumes"][1], mount_point="/srv/day", path="/srv/day/b",
                                need_bytes_fallback=60 * GB)])
    fx = clean()
    fx["space"] = {"/srv/day/a": {"dev": 66305, "free_bytes": 130 * GB, "free_entries": 10 ** 7},
                   "/srv/day/b": {"dev": 66305, "free_bytes": 130 * GB, "free_entries": 10 ** 7}}
    case("MQ20 normal 125 of 130, fallback 140", fx, [], fb,
         notes={"devices": {"66305": {"fallback_covered": False, "fallback_short_bytes": 10 * GB,
                                      "free_bytes": 130 * GB, "need_bytes": 125 * GB, "volumes": ["A", "B"]}}})
    # MQ21: core dumps off
    fx = clean()
    fx["unit"]["LimitCORESoft"] = "infinity"
    case("MQ21 LimitCORE infinity", fx, ["files: forgeday.service LimitCORESoft reads 'infinity': core dumps must be off "
                                         "(0)"])
    # MQ22: the unit runs as root
    fx = clean()
    fx["unit"]["User"] = "forge"
    case("MQ22 User forge", fx, ["processes: forgeday.service runs as 'forge': this check does not read that user's "
                                 "process count (the kernel does not limit root's)"])
    fx = clean()
    fx["unit"]["User"] = "root"
    case("MQ22 User root", fx, [])
    # MQ23: the unit level, inactive: systemd's default TasksMax binds
    fx = clean()
    fx["unit"]["TasksMax"] = "4915"
    case("MQ23 TasksMax 4915, 5000 needed", fx, ["processes: forgeday.service has 4915 tasks free (4915 - 0) < 5000 "
                                                 "needed"], req_with(extra_tasks=5000))
    # MQ23b (added with the test): an ACTIVE unit's own use is read from its own cgroup folder
    fx = clean()
    fx["unit"].update(ActiveState="active", ControlGroup="/system.slice/forgeday.service", MemoryMax=str(4 * GiB))
    fx["files"].update({"/sys/fs/cgroup/system.slice/forgeday.service/memory.current": str(3 * GiB),
                        "/sys/fs/cgroup/system.slice/forgeday.service/pids.current": "10",
                        "/sys/fs/cgroup/system.slice/forgeday.service/cpu.stat": STAT_S})
    case("MQ23b an active unit uses 3 of its 4 GiB", fx,
         [f"memory: forgeday.service has {GiB} bytes free ({4 * GiB} - {3 * GiB}) < {2 * GiB} needed"])


def calls_main():
    # MQ17: the call writes the record create-only, canonical; the same --out again: exit 2, the file unchanged
    rq = WORK / "request.json"
    rq.write_bytes(canon(REQ))
    out = WORK / "record_clean.json"
    rc = M.main(["--request", str(rq), "--out", str(out)], ops=FakeOps(clean()))
    check("MQ17 exit", rc, 0)
    data = out.read_bytes() if out.exists() else b""
    try:
        rec = parse_canon(data, "the record")
        check("MQ17 the record: canonical, verdict, schema, request",
              (rec["verdict"], rec["failures"], rec["schema"], rec["request"] == REQ), ("QUALIFIED", [], 1, True))
    except ValueError as e:
        check("MQ17 the record is canonical", str(e), "canonical")
    check("MQ17 LF only", (data.endswith(b"\n"), b"\r" in data), (True, False))
    h = hashlib.sha256(data).hexdigest()
    ops = FakeOps(clean())
    rc = M.main(["--request", str(rq), "--out", str(out)], ops=ops)
    check("MQ17 the same --out again: exit 2, unchanged, nothing read",
          (rc, hashlib.sha256(out.read_bytes()).hexdigest() == h, ops.calls), (2, True, []))
    # MQ17 unqualified: exit 1, the record says why
    fx = clean()
    fx["files"]["/proc/sys/kernel/pid_max"] = "32768"
    out = WORK / "record_pidmax.json"
    rc = M.main(["--request", str(rq), "--out", str(out)], ops=FakeOps(fx))
    rec = parse_canon(out.read_bytes(), "the record") if out.exists() else {}
    check("MQ17 unqualified: exit 1 and the record", (rc, rec.get("verdict"), rec.get("failures")),
          (1, "UNQUALIFIED", ["kernel: pid_max 32768 < 4194304 needed"]))
    # MQ24: a request that is not the form, and an --out that exists: exit 2, no file, nothing read
    good = canon(REQ)
    bad = {"a float": good.replace(b'"extra_memory_bytes":2147483648', b'"extra_memory_bytes":2.5'),
           "an unknown key": canon(req_with(extra=1)),
           "a missing key": canon({k: v for k, v in REQ.items() if k != "nofile"}),
           "a negative number": canon(req_with(floor_bytes=-1)),
           "threads 0": canon(req_with(threads=0)),
           "a volume without exec": canon(req_with(volumes=[{k: v for k, v in REQ["volumes"][0].items() if k != "exec"}])),
           "a label twice": canon(req_with(volumes=[REQ["volumes"][0], REQ["volumes"][0]]))}
    check("MQ24 the float stands in the request bytes", b"2.5" in bad["a float"], True)
    for i, (what, data) in enumerate(bad.items()):
        p, o = WORK / f"bad_request_{i}.json", WORK / f"record_bad_{i}.json"
        p.write_bytes(data)
        ops = FakeOps(clean())
        rc = M.main(["--request", str(p), "--out", str(o)], ops=ops)
        check(f"MQ24 {what}: exit 2, no record, nothing read", (rc, o.exists(), ops.calls), (2, False, []))
    o = WORK / "record_exists.json"
    o.write_bytes(b"keep\n")
    ops = FakeOps(clean())
    rc = M.main(["--request", str(rq), "--out", str(o)], ops=ops)
    check("MQ24 an --out that exists: exit 2, unchanged, nothing read", (rc, o.read_bytes(), ops.calls),
          (2, b"keep\n", []))
    # M2 (Fable 25 Nov): a crash inside the check is exit 4 with one line and no record, never UNQUALIFIED's exit 1
    class Boom(FakeOps):
        def run(self, argv):
            raise RuntimeError("planted inside the check")
    import contextlib
    import io
    o, buf = WORK / "record_boom.json", io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = M.main(["--request", str(rq), "--out", str(o)], ops=Boom(clean()))
    check("M2 a crash inside the check: exit 4, no record, one line naming it",
          (rc, o.exists(), "failed inside itself" in buf.getvalue()), (4, False, True))


def real_link_probe():
    # the REAL Ops.link_probe in a folder of this test: ok, and nothing is left behind
    d = WORK / "probe_target"
    d.mkdir()
    res = M.Ops().link_probe(str(d))
    check("real link probe: ok and nothing left", (res, sorted(os.listdir(d))), ("ok", []))
    res = M.Ops().link_probe(str(WORK / "no_such_folder"))
    check("real link probe: a folder that does not exist is not ok", (res.startswith(M.UNREAD), res == "ok"),
          (True, False))


for part in (cases, calls_main, real_link_probe):
    try:
        part()
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        check(f"{part.__name__} ran to its end", "a traceback", "no traceback")
failed = [n for n, ok in RESULTS if not ok]
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)

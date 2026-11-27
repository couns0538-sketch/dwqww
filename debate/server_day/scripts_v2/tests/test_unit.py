"""test_unit.py: the unit file (A3b, part 2, unit/forgeday.service) against known answers written BEFORE it
(tmp/opus_scratch/unit/KNOWN_ANSWERS_by_opus.md on the PC; SETUP_PLAN D6, D15; FORMATS 1.3). No systemd is needed:
the file is read as systemd reads it (sections, `key=value`, a line ending in a backslash continues), and the two
command lines are handed to the programs' OWN main(), with the classes that would run replaced by recorders.

    test_unit.py <unit file> <run folder: bootguard.py, guard.py and what they import> <a NEW folder> [plantN]

U1 sections Unit, Service, Install, each once. U2 ExecStartPre: one line, prefix `+`, /usr/bin/python3 -I -B
<PKG>/run/bootguard.py. U3 ExecStart: one line, no prefix, /usr/bin/python3 -I -B <PKG>/run/guard.py, the same PKG.
U4 --root, --exe, --net, --manifest, --known-startup equal in both lines; --package-list = <PKG>/MANIFEST.sha256.
U4b the guard's --policy = <PKG>/plan.json: the file the boot guard requires in the list (bug hunt 23 Nov 19:30).
U5 bootguard.main() and guard.main() accept their lines (exit 0, the recorded values are the line's); a word they
do not know is refused with exit 2 (the instrument). U6 Restart=on-failure, RestartSec=30, RestartSteps=10,
RestartMaxDelaySec=600, RestartPreventExitStatus=2, StartLimitIntervalSec=0. U7 KillMode=process. U8
TimeoutStartSec >= 1200 and no --sync-wait in the boot guard's line (its default 900 s). U9 WantedBy=multi-user.target,
After=time-sync.target, Type=simple, no User=. U10 (v17, 26 Nov evening, Neon's catch) LimitCORE=0 and
LimitNOFILE=65536: the two limits run/machine.py checks (LimitCORESoft "0", LimitNOFILESoft >= the day's nofile)
stand in the unit, so that no image's default is relied on (systemd 255's default soft open files is 1024).
PLANTS (each must make the test fail): plant1 KillMode=control-group (U7); plant2 TimeoutStartSec=90 (U8); plant3 no
`+` (U2); plant4 the guard's --root another folder (U4); plant5 Restart=no (U6); plant6 `-I` missing in ExecStart
(U3); plant7 a misspelt argument in the boot guard's line (U5); plant8 no WantedBy (U9); plant9 the guard's
--policy outside the package (U4b); plant10 LimitNOFILE=1024 (U10).
"""
import shlex
import sys
from pathlib import Path

if len(sys.argv) < 4:
    print("usage: test_unit.py <unit file> <run folder> <a NEW folder> [plantN]")
    sys.exit(2)
UNIT, RUN, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
PLANT = sys.argv[4] if len(sys.argv) > 4 else None
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
PLANTS = {
    "plant1": ("KillMode=process\n", "KillMode=control-group\n"),
    "plant2": ("TimeoutStartSec=1200\n", "TimeoutStartSec=90\n"),
    "plant3": ("ExecStartPre=+/usr/bin/python3", "ExecStartPre=/usr/bin/python3"),
    "plant4": ("run/guard.py \\\n    --root /srv/forgeday/run --exe", "run/guard.py \\\n    --root /srv/forgeday/run2 --exe"),
    "plant5": ("Restart=on-failure\n", "Restart=no\n"),
    "plant6": ("ExecStart=/usr/bin/python3 -I -B", "ExecStart=/usr/bin/python3 -B"),
    "plant7": ("--package-list /srv/forgeday/package/MANIFEST.sha256", "--package-lst /srv/forgeday/package/MANIFEST.sha256"),
    "plant9": ("--policy /srv/forgeday/package/plan.json", "--policy /srv/forgeday/plan.json"),
    "plant8": ("WantedBy=multi-user.target\n", "#WantedBy=multi-user.target\n"),
    "plant10": ("LimitNOFILE=65536\n", "LimitNOFILE=1024\n"),
}
text = UNIT.read_bytes().decode("ascii")
if PLANT:
    if PLANT not in PLANTS or text.count(PLANTS[PLANT][0]) != 1:
        print(f"STOP: {PLANT}: no such plant, or its text does not stand exactly once")
        sys.exit(2)
    text = text.replace(*PLANTS[PLANT])
    (WORK / "forgeday.service").write_bytes(text.encode("ascii"))
    print(f"PLANT {PLANT} applied to the copy")
sys.path.insert(0, str(RUN))
import bootguard as BG  # noqa: E402
import guard as G  # noqa: E402

RESULTS = []


def check(name, got, want):
    ok = got == want
    RESULTS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {str(got)[:300]}" + ("" if ok else f"; want {str(want)[:300]}"),
          flush=True)
    return ok


def parse(t):
    """{section: {key: [values]}} as systemd reads it; ValueError for anything else."""
    out, sec, buf = {}, None, ""
    for raw in t.split("\n"):
        line = buf + raw
        if line.endswith("\\"):
            buf = line[:-1] + " "
            continue
        buf, s = "", line.strip()
        if not s or s[0] in "#;":
            continue
        if s.startswith("[") and s.endswith("]"):
            if s[1:-1] in out:
                raise ValueError(f"section {s} twice")
            sec = out.setdefault(s[1:-1], {})
            continue
        if sec is None or "=" not in s:
            raise ValueError(f"not key=value inside a section: {s[:60]}")
        k, v = s.split("=", 1)
        sec.setdefault(k.strip(), []).append(v.strip())
    if buf:
        raise ValueError("the file ends inside a continued line")
    return out


def pairs(argv):
    """--name value pairs, in order; None when the list is not of that form."""
    if len(argv) % 2 or any(not x.startswith("--") for x in argv[::2]):
        return None
    return dict(zip(argv[::2], argv[1::2]))


def main_code(module, cls, argv):
    """module.main() on argv with module.<cls> replaced by a recorder: (exit code, the namespace it was given)."""
    seen = {}

    class Recorder:
        def __init__(self, a, *rest):
            seen["a"] = a

        def run(self):
            return 0
    saved, saved_argv = getattr(module, cls), sys.argv
    setattr(module, cls, Recorder)
    sys.argv = ["x"] + argv
    try:
        code = module.main()
    except SystemExit as e:
        code = e.code
    finally:
        setattr(module, cls, saved)
        sys.argv = saved_argv
    return code, seen.get("a")


try:
    u = parse(text)
except ValueError as e:
    u = {}
    print(f"the file does not parse: {e}")
check("U1 sections Unit, Service, Install, each once", sorted(u), ["Install", "Service", "Unit"])
sv, un, ins = u.get("Service", {}), u.get("Unit", {}), u.get("Install", {})
pre, start = sv.get("ExecStartPre", []), sv.get("ExecStart", [])
pa = shlex.split(pre[0][1:]) if len(pre) == 1 and pre[0][:1] == "+" else []
sa = shlex.split(start[0]) if len(start) == 1 and start[0][:1] not in "+-@:!" else []
pkg = pa[3][:-len("/run/bootguard.py")] if len(pa) > 3 and pa[3].endswith("/run/bootguard.py") else None
check("U2 ExecStartPre: one line, prefix +, /usr/bin/python3 -I -B <PKG>/run/bootguard.py",
      (len(pre), pre[0][:1] if pre else None, pa[:3], pkg is not None), (1, "+", ["/usr/bin/python3", "-I", "-B"], True))
check("U3 ExecStart: one line, no prefix, /usr/bin/python3 -I -B <PKG>/run/guard.py",
      (len(start), sa[:4]), (1, ["/usr/bin/python3", "-I", "-B", f"{pkg}/run/guard.py"]))
pp, sp = pairs(pa[4:]) or {}, pairs(sa[4:]) or {}
shared = ("--root", "--exe", "--net", "--manifest", "--known-startup")
check("U4 the five shared arguments equal in both lines, all there",
      [(k, pp.get(k) == sp.get(k) and pp.get(k) is not None) for k in shared], [(k, True) for k in shared])
check("U4 --package-list = <PKG>/MANIFEST.sha256", pp.get("--package-list"), f"{pkg}/MANIFEST.sha256")
check("U4b the guard's --policy = <PKG>/plan.json", sp.get("--policy"), f"{pkg}/plan.json")
code, a = main_code(BG, "BootGuard", pa[4:])
check("U5 bootguard.main() accepts its line: exit 0, the recorded values are the line's",
      (code, None if a is None else (a.root, a.exe, a.net, a.manifest, a.known_startup, a.package_list, a.sync_wait)),
      (0, (pp.get("--root"), pp.get("--exe"), pp.get("--net"), pp.get("--manifest"), pp.get("--known-startup"),
           pp.get("--package-list"), 900.0)))
code, a = main_code(G, "Guard", sa[4:])
check("U5 guard.main() accepts its line: exit 0, the recorded values are the line's",
      (code, None if a is None else (a.root, a.exe, a.net, a.manifest, a.known_startup, a.converter, a.policy,
                                     a.floor_bytes, a.openings)),
      (0, (sp.get("--root"), sp.get("--exe"), sp.get("--net"), sp.get("--manifest"), sp.get("--known-startup"),
           sp.get("--converter"), sp.get("--policy"), int(sp.get("--floor-bytes", "-1")), "")))
check("U5 the instrument: a word neither knows is refused with exit 2",
      (main_code(BG, "BootGuard", pa[4:] + ["--no-such-word", "1"])[0],
       main_code(G, "Guard", sa[4:] + ["--no-such-word", "1"])[0]), (2, 2))
check("U6 restarts: on-failure, from 30 s to at most 600 s apart, never on exit 2, never given up",
      (sv.get("Restart"), sv.get("RestartSec"), sv.get("RestartSteps"), sv.get("RestartMaxDelaySec"),
       sv.get("RestartPreventExitStatus"), un.get("StartLimitIntervalSec")),
      (["on-failure"], ["30"], ["10"], ["600"], ["2"], ["0"]))
check("U7 KillMode=process (workers and packer outlive the guard)", sv.get("KillMode"), ["process"])
tss = sv.get("TimeoutStartSec", ["0"])
check("U8 TimeoutStartSec >= 1200 and the boot guard's default --sync-wait 900",
      (len(tss) == 1 and tss[0].isdigit() and int(tss[0]) >= 1200, "--sync-wait" in pp), (True, False))
check("U9 WantedBy=multi-user.target, After=time-sync.target, Type=simple, no User=",
      (ins.get("WantedBy"), "time-sync.target" in " ".join(un.get("After", [])).split(), sv.get("Type"), "User" in sv),
      (["multi-user.target"], True, ["simple"], False))
check("U10 LimitCORE=0 and LimitNOFILE=65536 (machine.py's two file limits stand in the unit)",
      (sv.get("LimitCORE"), sv.get("LimitNOFILE")), (["0"], ["65536"]))
failed = [n for n, ok in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks pass")
print("ALL PASS" if not failed and RESULTS else f"{len(failed)} failed: {failed}")
sys.exit(0 if not failed and RESULTS else 1)

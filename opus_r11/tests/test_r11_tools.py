"""R11 self-test of the helper tools and the three Code Review flags.

  1 r11_astra.py extract: a correct archive extracts and verifies; a whole-archive checksum failure deletes every
    file the run extracted (CR flag 1); a member that already exists is never overwritten.
  2 r11_common.production_processes fails CLOSED when psutil is missing (CR flag 2).
  3 r11_common.assert_writable_path refuses production / live-data / other agents' folders.
  4 GPL boundary (CR flag 3): the branch changes nothing under src/, include/, tests/ or CMakeLists.txt relative to
    the R10 fix1 base 7f79c349, every file that includes or imports nnue-pytorch lives in tools/nnue_pytorch_amd/,
    and no file in opus_r11/ includes lib/binpack.h or imports the trainer's modules.
Usage: test_r11_tools.py <scratch_dir>   (must not exist). Prints "R11 TOOLS SELFTEST PASS".
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "opus_r11", "pipeline"))
import r11_astra as A  # noqa: E402
import r11_common as C  # noqa: E402

FAILS: list[str] = []


def check(cond: bool, what: str) -> None:
    print(("ok   " if cond else "FAIL ") + what, flush=True)
    if not cond:
        FAILS.append(what)


def make_transport(dl: str, whole_sha_override: str | None = None) -> tuple[tuple[str, int], dict]:
    """A synthetic transport set; returns (pins of the real blob, member sha256s)."""
    os.makedirs(dl)
    buf = io.BytesIO()
    members = {}
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in (("completed/full10m/forge_filtered.pos", os.urandom(300_000)),
                           ("completed/full10m/forge_filtered.hce", os.urandom(50_000)),
                           ("completed/other.txt", b"x" * 1000)):
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
            members[name] = hashlib.sha256(data).hexdigest()
    blob = buf.getvalue()
    pins = (hashlib.sha256(blob).hexdigest(), len(blob))
    half = len(blob) // 2
    parts = []
    for i, (off, chunk) in enumerate(((0, blob[:half]), (half, blob[half:]))):
        name = f"t.tar.gz.part{i:06d}"
        with open(os.path.join(dl, name), "wb") as f:
            f.write(chunk)
        parts.append({"name": name, "offset": off, "size": len(chunk), "sha256": hashlib.sha256(chunk).hexdigest()})
    man = {"format": "forge-transport-v1", "part_bytes": half, "parts": parts,
           "whole": {"name": "t.tar.gz", "size": len(blob), "sha256": whole_sha_override or hashlib.sha256(blob).hexdigest()}}
    with open(os.path.join(dl, A.MANIFEST), "w", encoding="utf-8") as f:
        json.dump(man, f)
    return pins, members


def no_staging(out: str) -> bool:
    return not os.path.isdir(out) or not any(x.startswith(".staging_") for x in os.listdir(out))


def main() -> int:
    scratch = sys.argv[1]
    if os.path.exists(scratch):
        print(f"{scratch} exists; give a new folder")
        return 2
    globs = ["completed/full10m/forge_filtered.pos", "completed/full10m/forge_filtered.hce"]

    # 1a correct archive (pins of the synthetic blob; the CLI uses the real pins)
    dl, out = os.path.join(scratch, "dl_ok"), os.path.join(scratch, "out_ok")
    pins, mem = make_transport(dl)
    check(A.cmd_verify(dl, pins) == 0, "astra: part checksums verify")
    rc = A.cmd_extract(dl, out, globs, os.path.join(scratch, "ok.json"), pins, mem)
    check(rc == 0 and sorted(os.listdir(out)) == ["forge_filtered.hce", "forge_filtered.pos"] and no_staging(out),
          "astra: correct archive -> staged, checked, renamed: exactly the requested members, no staging left")
    # 1b existing target is never overwritten
    rc = A.cmd_extract(dl, out, globs, None, pins, mem)
    check(rc == 2 and sorted(os.listdir(out)) == ["forge_filtered.hce", "forge_filtered.pos"] and no_staging(out),
          "astra: existing targets are not overwritten (earlier files stay, staging cleaned)")
    # 1c whole-archive checksum failure (manifest consistent with itself, data different) -> nothing in place
    dl2, out2 = os.path.join(scratch, "dl_bad"), os.path.join(scratch, "out_bad")
    pins2, mem2 = make_transport(dl2, whole_sha_override="0" * 64)
    rc = A.cmd_extract(dl2, out2, globs, os.path.join(scratch, "bad.json"), ("0" * 64, pins2[1]), mem2)
    left = os.listdir(out2) if os.path.isdir(out2) else []
    check(rc != 0 and left == [], f"astra: checksum failure leaves nothing (staged files deleted; left: {left})")
    # 1d CR fix 3: a manifest that does not match the pins is refused before anything is written
    out3 = os.path.join(scratch, "out_pin")
    rc = A.cmd_extract(dl, out3, globs, None, ("f" * 64, pins[1]), mem)
    check(rc != 0 and (not os.path.isdir(out3) or os.listdir(out3) == []),
          "astra: manifest whole sha256 != pinned value -> refused, nothing written")
    rc = A.cmd_extract(dl, out3, globs, None, (pins[0], pins[1] + 1), mem)
    check(rc != 0 and (not os.path.isdir(out3) or os.listdir(out3) == []),
          "astra: manifest whole size != pinned size -> refused, nothing written")
    # 1e a pinned member with another sha256 -> staged files deleted, nothing renamed
    out4 = os.path.join(scratch, "out_member")
    bad_mem = dict(mem)
    bad_mem["completed/full10m/forge_filtered.pos"] = "e" * 64
    rc = A.cmd_extract(dl, out4, globs, None, pins, bad_mem)
    check(rc != 0 and os.listdir(out4) == [], f"astra: member pin mismatch -> nothing in place ({os.listdir(out4)})")
    # 1f the CLI pins are the release's values, and the real download's manifest matches them
    check(A.PINNED_WHOLE_SHA256 == "148803c5a45a5e291c18f667b918100ec1fa1a8e08d5a74dfe430651b3f1418f"
          and A.PINNED_WHOLE_SIZE == 2_329_781_152, "astra: pinned whole sha256 148803c5... and size 2,329,781,152")
    real = "D:/grok-pc-data/r11_nnue/astra_dl/transport_manifest.json"
    if os.path.isfile(real):
        rm = json.load(open(real, encoding="utf-8"))
        check(rm["whole"]["sha256"] == A.PINNED_WHOLE_SHA256 and rm["whole"]["size"] == A.PINNED_WHOLE_SIZE,
              "astra: the downloaded transport manifest matches the pins")

    # 1g CR fix 8: free disk space is checked before writing, downloading and extracting
    drive = C.winpath(scratch)[:2]
    try:
        C.require_disk(scratch, 1 << 20, "tiny write")
        check(True, "a small write passes the 1 GB small-write floor")
    except C.StageFailed as e:
        check(False, f"a small write was refused: {e}")
    saved_floors = dict(C._FLOORS)
    C._FLOORS[drive] = 1e6
    try:
        C.require_disk(scratch, 100 << 20, "bulk write")
        check(False, "a bulk write must be refused below the drive floor")
    except C.StageFailed as e:
        check("floor" in str(e), f"a bulk write below the drive floor is refused: {str(e)[:90]}")
    dl_refused = os.path.join(scratch, "dl_refused")
    rc = A.cmd_download(dl_refused)
    check(rc == 2 and not os.path.exists(dl_refused), "Astra download refused before anything is written (floor)")
    C._FLOORS.clear()
    C._FLOORS.update(saved_floors)
    saved_small = C.SMALL_WRITE_FLOOR_GB
    C.SMALL_WRITE_FLOOR_GB = 1e6
    out5 = os.path.join(scratch, "out_nospace")
    rc = A.cmd_extract(dl, out5, globs, None, pins, mem)
    C.SMALL_WRITE_FLOOR_GB = saved_small
    check(rc != 0 and os.listdir(out5) == [], "Astra extract refused for lack of space leaves nothing behind")

    # 0 the shipped config loads (a comment key in limits once broke every stage after the fix-8 commit)
    real_cfg = C.read_json(os.path.join(REPO, "opus_r11", "pipeline", "r11_config.json"))
    try:
        lim = C.limits_from(real_cfg)
        check(lim.min_disk_free_gb == 40.0 and lim.disk_floor_gb.get("D:") == 40.0,
              "the shipped r11_config.json loads (limits_from) with the 40 GB D: floor")
    except Exception as e:  # noqa: BLE001
        check(False, f"the shipped r11_config.json does not load: {e}")
    for section in ("data", "engine", "trainer", "check", "train"):
        check(section in real_cfg, f"config section {section!r} present")
    # CR R2 H1: yield is the only GPU policy - no share / duty cycle anywhere
    profs = real_cfg["train"]["profiles"]
    check(all(p.get("gpu_policy") == "yield" and "share_duty" not in p for p in profs.values()),
          f"every training profile yields to production, none shares ({ {k: p.get('gpu_policy') for k, p in profs.items()} })")
    import importlib.util
    spec = importlib.util.spec_from_file_location("r11_train_entry", os.path.join(REPO, "tools", "nnue_pytorch_amd", "r11",
                                                                                   "r11_train_entry.py"))
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)  # defines functions only; nothing of the trainer is imported
    for bad in (["--r11-policy", "share"], ["--r11-share-duty", "0.5"]):
        try:
            entry.parse_own_args(bad + ["--r11-clone", "x", "--r11-run-dir", "y", "--"])
            check(False, f"the entry must refuse {bad[0]}")
        except SystemExit as e:
            check("unknown option" in str(e), f"the entry refuses {bad[0]} (no share policy left)")
    # CR R2 M1: the entry checks for production BEFORE importing torch: with a dummy clone (no train.py, no trainer
    # modules) and a running "production" marker process it must exit 76, never reach an import
    marker = f"R11M1MARKER{os.getpid()}"
    pfile = os.path.join(scratch, "patterns.json")
    with open(pfile, "w", encoding="utf-8") as f:
        json.dump([marker], f)  # from a FILE: on the command line the entry's own launcher would match
    fake_clone = os.path.join(scratch, "fake_clone")
    os.makedirs(fake_clone)

    def run_entry(run_dir: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", "-B", spec.origin, "--r11-clone", fake_clone, "--r11-run-dir", run_dir,
                               "--r11-patterns-file", pfile, "--r11-affinity", "0x700", "--", "dummy.binpack"],
                              capture_output=True, text=True, timeout=300)

    dummy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(12)", marker])
    try:
        time.sleep(1.0)
        run_m1 = os.path.join(scratch, "run_m1")
        r = run_entry(run_m1)
    finally:
        dummy.wait(timeout=60)
    ev = open(os.path.join(run_m1, "r11_events.jsonl"), encoding="utf-8").read() if os.path.isfile(
        os.path.join(run_m1, "r11_events.jsonl")) else ""
    check(r.returncode == 76 and "yield_before_import" in ev and "No module named" not in r.stderr,
          f"production check before import torch: exit {r.returncode}, event yield_before_import "
          f"{'present' if 'yield_before_import' in ev else 'missing'}")
    # negative: no production marker -> the entry gets past the check (it must not match its own launcher) and only
    # then imports the trainer, which fails on the dummy clone
    r2 = run_entry(os.path.join(scratch, "run_m1_neg"))
    check(r2.returncode not in (0, 76) and "No module named 'train'" in r2.stderr,
          f"no production -> the entry does not yield to itself and reaches the trainer import (exit {r2.returncode})")
    import r11_train as TR
    cfg_share = json.loads(json.dumps(real_cfg))
    cfg_share["train"]["profiles"]["smoke"]["gpu_policy"] = "share"
    try:
        TR.run_train(cfg_share, "smoke", C.Log(None, "train"), None)
        check(False, "a share profile must be refused")
    except C.StageFailed as e:
        check("yield is the only GPU policy" in str(e), "the train stage refuses a share profile")

    # 1h CR fix 10: sealed inputs are identified by their full sha256; a change in the middle of a big file (which a
    # first/last-MiB fingerprint misses) is detected
    big = os.path.join(scratch, "sealed_big.bin")
    with open(big, "wb") as f:
        f.write(os.urandom(3 << 20))
    sealed = C.SealedInputs()
    registered = sealed.sha256(big)

    def edges(path: str) -> str:  # the pre-fix-10 fingerprint, only to show what it missed
        hh = hashlib.sha256()
        with open(path, "rb") as fh:
            hh.update(fh.read(1 << 20))
            fh.seek(os.path.getsize(path) - (1 << 20))
            hh.update(fh.read(1 << 20))
        return hh.hexdigest()

    before_edges = edges(big)
    with open(big, "r+b") as f:
        f.seek((3 << 20) // 2)
        b = f.read(1)
        f.seek((3 << 20) // 2)
        f.write(bytes([b[0] ^ 1]))
    check(edges(big) == before_edges, "the old first/last-MiB fingerprint does NOT see a change in the middle")
    try:
        C.SealedInputs().verify(big, registered, "test input")
        check(False, "a changed sealed input must be refused")
    except C.StageFailed as e:
        check("input changed since registration" in str(e), "the full sha256 detects the change in the middle")

    # 1d CR fix 1: no STOP/PAUSE control files anywhere in the pipeline; the hold is the named event
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.windll.kernel32
    k32.CreateEventW.restype = wintypes.HANDLE
    k32.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    k32.ResetEvent.argtypes = [wintypes.HANDLE]
    k32.SetEvent.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    check(not C.hold_requested(), "no hold before the event exists")
    h = k32.CreateEventW(None, True, True, C.HOLD_EVENT)
    check(bool(h) and C.hold_requested(), f"hold active while {C.HOLD_EVENT} is signalled")
    k32.ResetEvent(h)
    check(not C.hold_requested(), "no hold while the event is reset")
    k32.SetEvent(h)
    k32.CloseHandle(h)
    check(not C.hold_requested(), "no hold after the last handle is closed")
    offenders = []
    for d in ("opus_r11/pipeline", "tools/nnue_pytorch_amd/r11"):
        for fn in os.listdir(os.path.join(REPO, d)):
            if fn.endswith(".py"):
                text = open(os.path.join(REPO, d, fn), encoding="utf-8").read()
                for marker in ('"STOP"', '"PAUSE"', "stop_requested", "control/STOP", "control/PAUSE", '"control"'):
                    if marker in text:
                        offenders.append(f"{d}/{fn}: {marker}")
    check(offenders == [], f"no STOP/PAUSE control files in the pipeline code: {offenders}")

    # 1e CR fix 2: Idle priority + background mode on <= 3 cores, inherited by a child process
    probe = os.path.join(scratch, "prio_probe.py")
    with open(probe, "w", encoding="utf-8", newline="\n") as f:
        f.write("import os, sys, json, subprocess, psutil\n"
                f"sys.path.insert(0, {os.path.join(REPO, 'opus_r11', 'pipeline')!r})\n"
                "import r11_common as C\n"
                "info = C.set_idle_background(0x700)\n"
                "me = psutil.Process()\n"
                "child = subprocess.run([sys.executable, '-c', 'import psutil; p = psutil.Process(); "
                "print(int(p.nice()), int(p.ionice()), p.cpu_affinity())'], capture_output=True, text=True).stdout.strip()\n"
                "print(json.dumps({'info': info, 'nice': int(me.nice()), 'io': int(me.ionice()), 'aff': me.cpu_affinity(), "
                "'child': child}))\n")
    r = subprocess.run([sys.executable, "-I", "-B", probe], capture_output=True, text=True)
    try:
        pr = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        pr = {"error": r.stdout[-300:] + r.stderr[-300:]}
    check(pr.get("nice") == 0x40 and pr.get("io") == 0 and pr.get("aff") == [8, 9, 10],
          f"set_idle_background: Idle (0x40), I/O priority very low (background mode), CPUs 8-10: {pr}")
    check(str(pr.get("child", "")).startswith("64 0 [8, 9, 10]"),
          f"a child inherits Idle, the very low I/O priority and the 3-core mask: {pr.get('child')}")
    try:
        C.set_idle_background(0xF)
        check(False, "a 4-CPU mask must be refused")
    except C.StageFailed:
        check(True, "a 4-CPU mask is refused")

    # 2 CR fix 4: the process check FAILS without psutil; an unreadable python command line counts as production
    saved = sys.modules.get("psutil", "absent")
    sys.modules["psutil"] = None  # makes "import psutil" raise ImportError
    try:
        C.production_processes(["anything"])
        failed = False
    except C.StageFailed:
        failed = True
    finally:
        if saved == "absent":
            del sys.modules["psutil"]
        else:
            sys.modules["psutil"] = saved
    check(failed, "process check fails (StageFailed) when psutil is missing")
    res = C.production_processes([r"this-pattern-matches-no-process-\d{40}"])
    check(res == [], "process check with psutil and no match returns []")
    import psutil

    class FakeProc:
        def __init__(self, pid, name, cmdline, ppid=1000):
            self.info = {"pid": pid, "ppid": ppid, "name": name, "cmdline": cmdline}

    real_iter = psutil.process_iter
    psutil.process_iter = lambda attrs=None: iter([FakeProc(999001, "python.exe", None),
                                                   FakeProc(999002, "System", None),
                                                   FakeProc(999003, "notepad.exe", ["notepad.exe", "x.txt"]),
                                                   FakeProc(999004, None, None, ppid=4),
                                                   FakeProc(999005, None, None, ppid=1234)])
    try:
        res = C.production_processes([r"no-such-pattern-\d{30}"])
    finally:
        psutil.process_iter = real_iter
    check([r["pid"] for r in res] == [999001, 999005] and all(r["pattern"] == C.UNREADABLE for r in res),
          "unreadable command line: python and unnamed non-kernel processes count as production (wait); "
          f"System and kernel children (ppid 4) do not: {res}")

    # 3 protected folders
    for p in ("F:/forge_j1_data/x.binpack", "D:/forge_nnue_train/exports/y", "C:/Users/Administrator/grok-pc/z",
              "D:/grok-pc-data/selfplay_out/w", "D:/forge_j1_data_astra/v"):
        try:
            C.assert_writable_path(p)
            check(False, f"protected path accepted: {p}")
        except C.StageFailed:
            check(True, f"protected path refused: {p}")
    try:
        C.assert_writable_path("D:/grok-pc-data/r11_nnue/data/x")
        C.assert_writable_path("D:/grok-pc-data/selfplay_out_other/x")
        check(True, "own output folders accepted")
    except C.StageFailed as e:
        check(False, f"own output folder refused: {e}")

    # 4 GPL boundary
    r = subprocess.run(["git", "-C", REPO, "diff", "--stat", "7f79c349", "--", "src", "include", "tests", "CMakeLists.txt"],
                       capture_output=True, text=True)
    check(r.returncode == 0 and r.stdout.strip() == "", "no change under src/, include/, tests/, CMakeLists.txt vs 7f79c349")
    r = subprocess.run(["git", "-C", REPO, "ls-files"], capture_output=True, text=True)
    files = r.stdout.splitlines()
    gpl_users = []
    for f in files:
        if not f.endswith((".cpp", ".h", ".hpp", ".py")):
            continue
        if f.startswith("opus_r11/tests/"):
            continue  # this test names the markers it searches for
        try:
            text = open(os.path.join(REPO, f), "rb").read().decode("utf-8", "replace")
        except OSError:
            continue
        if '#include "lib/binpack.h"' in text or "import model as M" in text or "from model import" in text:
            gpl_users.append(f)
    bad = [f for f in gpl_users if not f.startswith("tools/nnue_pytorch_amd/") and not f.startswith("opus_r10/tools/")]
    check(bad == [], f"files using nnue-pytorch code live in tools/nnue_pytorch_amd/ only (GPL users: {gpl_users})")
    check(not any(f.startswith(("src/", "include/", "tests/")) for f in gpl_users), "nothing GPL under src/include/tests")

    print(f"\n{len(FAILS)} failed checks")
    print("R11 TOOLS SELFTEST " + ("PASS" if not FAILS else "FAIL"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())

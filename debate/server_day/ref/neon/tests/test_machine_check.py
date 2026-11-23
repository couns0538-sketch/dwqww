"""Neon 2026-11-23, self-test for ref/neon/machine_check.py (SETUP_PLAN.md section 4, D15, row 44).

    python3 -I -B test_machine_check.py <NEW work folder>

Zero system temp folders, zero writes outside <NEW work folder>, standard library only.
Tests every planted failing case of section 4 + live host smoke check.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print(__doc__)
    sys.exit(2)

WORK = Path(sys.argv[1]).resolve()
if WORK.exists():
    print(f"STOP: {WORK} already exists (pass a NEW work folder)")
    sys.exit(2)
WORK.mkdir(parents=True)

SCRIPT = Path(__file__).resolve().parent.parent / "machine_check.py"
results = []

ALL_V4_FLAGS = (
    "fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 "
    "ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon rep_good nopl xtopology "
    "cx16 lahf_lm popcnt pni sse4_1 sse4_2 ssse3 avx avx2 bmi1 bmi2 f16c fma abm movbe xsave "
    "avx512f avx512bw avx512cd avx512dq avx512vl"
)
GOOD_UUID = "11111111-2222-3333-4444-555555555555"


def check(name: str, ok, detail="") -> None:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:260]}" if not ok and detail != "" else ""), flush=True)


def make_env(case_dir: Path, cpu_flags_map: dict, cg_v2_rel="/slice/workload",
             cpu_max="max 100000", mem_total_kb=64 * 1024 * 1024, mem_max="max",
             pids_max="max", pid1="systemd", systemd_dir=True, boot_id=GOOD_UUID,
             v1_mode=False, v1_quota=-1, v1_mem_limit=None, ancestor_mem_max=None):
    proc = case_dir / "proc"
    cg = case_dir / "cgroup"
    rundir = case_dir / "run"
    (proc / "self").mkdir(parents=True)
    (proc / "1").mkdir(parents=True)
    (proc / "sys" / "kernel" / "random").mkdir(parents=True)

    blocks = []
    for cid, fl in sorted(cpu_flags_map.items()):
        if fl is None:
            blocks.append(f"processor\t: {cid}\nmodel name\t: Synthetic\n")
        else:
            blocks.append(f"processor\t: {cid}\nmodel name\t: Synthetic\nflags\t\t: {fl}\n")
    (proc / "cpuinfo").write_text("\n".join(blocks) + "\n", encoding="utf-8")
    (proc / "meminfo").write_text(
        f"MemTotal:       {mem_total_kb} kB\nMemAvailable:   {mem_total_kb // 2} kB\n",
        encoding="utf-8",
    )
    (proc / "sys" / "kernel" / "threads-max").write_text("100000\n", encoding="utf-8")
    if boot_id is not None:
        (proc / "sys" / "kernel" / "random" / "boot_id").write_text(boot_id + "\n", encoding="utf-8")
    (proc / "1" / "comm").write_text(pid1 + "\n", encoding="utf-8")
    if systemd_dir:
        (rundir / "systemd" / "system").mkdir(parents=True)
    else:
        rundir.mkdir(parents=True)

    if not v1_mode:
        (proc / "self" / "cgroup").write_text(f"0::{cg_v2_rel}\n", encoding="utf-8")
        leaf = cg / cg_v2_rel.lstrip("/")
        leaf.mkdir(parents=True)
        (leaf / "cpu.max").write_text(cpu_max + "\n", encoding="utf-8")
        (leaf / "memory.max").write_text(mem_max + "\n", encoding="utf-8")
        (leaf / "pids.max").write_text(pids_max + "\n", encoding="utf-8")
        (leaf / "cpu.stat").write_text("nr_throttled 3\nthrottled_usec 1200\n", encoding="utf-8")
        if ancestor_mem_max is not None:
            (leaf.parent / "memory.max").write_text(str(ancestor_mem_max) + "\n", encoding="utf-8")
    else:
        (proc / "self" / "cgroup").write_text("2:cpu:/grp\n3:memory:/grp\n4:pids:/grp\n", encoding="utf-8")
        (cg / "cpu" / "grp").mkdir(parents=True)
        (cg / "cpu" / "grp" / "cpu.cfs_quota_us").write_text(f"{v1_quota}\n", encoding="utf-8")
        (cg / "cpu" / "grp" / "cpu.cfs_period_us").write_text("100000\n", encoding="utf-8")
        (cg / "memory" / "grp").mkdir(parents=True)
        (cg / "memory" / "grp" / "memory.limit_in_bytes").write_text(
            f"{v1_mem_limit if v1_mem_limit is not None else (1 << 62)}\n", encoding="utf-8"
        )
        (cg / "pids" / "grp").mkdir(parents=True)
        (cg / "pids" / "grp" / "pids.max").write_text(pids_max + "\n", encoding="utf-8")

    return proc, cg, rundir


def invoke(out_dir: Path, extra: list) -> tuple:
    cmd = [sys.executable, "-I", "-B", str(SCRIPT), "--work-dir", str(out_dir)] + extra
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    rep = None
    rf = out_dir / "machine_check.json"
    if rf.is_file():
        rep = json.loads(rf.read_text(encoding="ascii"))
    return p.returncode, p.stdout.strip(), p.stderr.strip(), rep


# M1: Clean synthetic qualified host (all checks pass, canonical JSON has no floats)
c1 = WORK / "c1"
proc, cg, rundir = make_env(c1, {i: ALL_V4_FLAGS for i in range(4)})
rc, out, err, rep = invoke(c1 / "out", [
    "--variant", "v4", "--min-threads", "4", "--min-ram-bytes", str(8 * 1024**3),
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir),
    "--affinity", "0-3", "--require-systemd",
])
check("M1 clean synthetic v4 + systemd passes (rc=0, canonical JSON)",
      rc == 0 and rep is not None and rep["qualified"] is True and rep["cpu"]["nr_throttled"] == 3, (rc, out, err))

# M2: Existing --work-dir refused (rc=2)
rc, out, err, _ = invoke(c1 / "out", ["--variant", "scalar_verify"])
check("M2 existing --work-dir refused with rc=2", rc == 2, (rc, out, err))

# M3: Section 4: 5 visible CPUs under a cgroup v2 quota of 4
c3 = WORK / "c3"
proc, cg, rundir = make_env(c3, {i: ALL_V4_FLAGS for i in range(5)}, cpu_max="400000 100000")
rc5, out5, _, rep5 = invoke(c3 / "out5", [
    "--variant", "avx2_pext", "--min-threads", "5", "--min-ram-bytes", "0",
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "0-4",
])
rc4, out4, _, rep4 = invoke(c3 / "out4", [
    "--variant", "avx2_pext", "--min-threads", "4", "--min-ram-bytes", "0",
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "0-4",
])
check("M3 5 visible CPUs under quota 4: min-threads=5 FAILS, min-threads=4 PASSES",
      rc5 == 1 and rep5["cpu"]["effective_cpus_milli"] == 4000 and rc4 == 0, (rc5, out5, rc4, out4))

# M4: Section 4: enough host RAM (64 GiB) under lower ancestor cgroup memory.max (4 GiB)
c4 = WORK / "c4"
proc, cg, rundir = make_env(c4, {0: ALL_V4_FLAGS}, mem_total_kb=64 * 1024 * 1024, mem_max="max",
                            ancestor_mem_max=4 * 1024**3)
rc, out, _, rep = invoke(c4 / "out", [
    "--variant", "avx2_pext", "--min-threads", "1", "--min-ram-bytes", str(8 * 1024**3),
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "0",
])
check("M4 ancestor cgroup memory.max (4 GiB) overrides 64 GiB MemTotal and FAILS 8 GiB gate",
      rc == 1 and rep["memory"]["effective_ram_bytes"] == 4 * 1024**3 and "memory:" in out, (rc, out))

# M5: CPU 0 outside affinity mask + mixed ISA across affinity CPUs
c5 = WORK / "c5"
no_bmi2 = " ".join(f for f in ALL_V4_FLAGS.split() if f != "bmi2")
proc, cg, rundir = make_env(c5, {0: ALL_V4_FLAGS, 1: ALL_V4_FLAGS, 2: no_bmi2})
rc, out, _, rep = invoke(c5 / "out", [
    "--variant", "avx2_pext", "--min-threads", "2", "--min-ram-bytes", "0",
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "1,2",
])
check("M5 mixed ISA across affinity CPUs (CPU 2 lacks bmi2 while CPU 0 has it) FAILS",
      rc == 1 and rep["cpu"]["missing_flags_by_cpu"] == {"2": ["bmi2"]}, (rc, out, rep["cpu"]))

# M6: Missing flags line in cpuinfo (Neon N1 case) fails loudly with named reason
c6 = WORK / "c6"
proc, cg, rundir = make_env(c6, {0: None})
rc, out, _, rep = invoke(c6 / "out", [
    "--variant", "scalar_verify", "--min-threads", "1", "--min-ram-bytes", "0",
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "0",
])
check("M6 missing flags line in cpuinfo fails loudly (N1)",
      rc == 1 and rep["cpu"]["missing_flag_lines"] == [0] and "missing flags line" in out, (rc, out))

# M7: Cgroup v1 fallback enforces CPU quota and memory.limit_in_bytes
c7 = WORK / "c7"
proc, cg, rundir = make_env(c7, {0: ALL_V4_FLAGS, 1: ALL_V4_FLAGS}, v1_mode=True,
                            v1_quota=150000, v1_mem_limit=2 * 1024**3, pids_max="64")
rc, out, _, rep = invoke(c7 / "out", [
    "--variant", "avx2_pext", "--min-threads", "2", "--min-ram-bytes", str(4 * 1024**3), "--min-pids", "128",
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "0,1",
])
check("M7 cgroup v1 enforces CPU quota, memory limit, and pids.max",
      rc == 1 and rep["cpu"]["cgroup_mode"] == "v1" and rep["cpu"]["effective_cpus_milli"] == 1500
      and rep["memory"]["effective_ram_bytes"] == 2 * 1024**3 and rep["limits"]["effective_pids_max"] == 64,
      (rc, out))

# M8: Shared physical volume (st_dev) deduplication catches two dirs whose sum exceeds free space
c8 = WORK / "c8"
d_a = c8 / "spool"
d_b = c8 / "build"
d_a.mkdir(parents=True)
d_b.mkdir(parents=True)
vfs = os.statvfs(str(d_a))
free_b = vfs.f_bavail * vfs.f_frsize
sixty_pct = (free_b * 6) // 10
proc, cg, rundir = make_env(c8, {0: ALL_V4_FLAGS})
rc, out, _, rep = invoke(c8 / "out", [
    "--variant", "scalar_verify", "--min-threads", "1", "--min-ram-bytes", "0",
    "--volume", f"spool:{d_a}:{sixty_pct}:1:0",
    "--volume", f"build:{d_b}:{sixty_pct}:1:1",
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "0",
])
check("M8 two folders on same st_dev (60% + 60% = 120% free) FAILS combined room check",
      rc == 1 and len(rep["storage"]["by_device"]) == 1
      and rep["storage"]["by_device"][0]["hardlink_atomic_ok"] is True
      and "combined required" in out, (rc, out))

# M9: D15 non-systemd PID 1 (tini / container) fails --require-systemd, passes without it; bad boot_id fails
c9 = WORK / "c9"
proc, cg, rundir = make_env(c9, {0: ALL_V4_FLAGS}, pid1="tini", systemd_dir=False, boot_id="not-a-uuid")
rc, out, _, rep = invoke(c9 / "out", [
    "--variant", "scalar_verify", "--min-threads", "1", "--min-ram-bytes", "0", "--require-systemd",
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "0",
])
check("M9 non-systemd container fails D15 --require-systemd and invalid boot_id fails D5",
      rc == 1 and rep["runtime"]["systemd_live"] is False and rep["runtime"]["boot_id_valid"] is False
      and "systemd:" in out and "boot:" in out, (rc, out))

# M10: Live real Linux host check (walks real /proc/self/cgroup & /sys/fs/cgroup & real os.link probe)
c10 = WORK / "c10"
rc, out, err, rep = invoke(c10 / "out", [
    "--variant", "avx2_pext", "--min-threads", "1", "--min-ram-bytes", str(512 * 1024**2),
])
check("M10 live Linux host check runs clean on real /proc + /sys/fs/cgroup + hardlink probe",
      rc == 0 and rep is not None and rep["runtime"]["boot_id_valid"] is True
      and rep["stage"] == "preflight_hardware" and rep["resources_and_evidence_valid"] is True
      and rep["pilot_rate_qualified"] is None and rep["covers_full_target"] is None
      and rep["runtime"]["codecs_ok"] is True and len(rep["runtime"]["compilers"]) >= 1
      and rep["storage"]["by_device"][0]["hardlink_atomic_ok"] is True, (rc, out, err))

# M11: Free bytes OK but free inodes below required threshold fails cleanly
c11 = WORK / "c11"
d11 = c11 / "vol"
d11.mkdir(parents=True)
vfs11 = os.statvfs(str(d11))
proc, cg, rundir = make_env(c11, {0: ALL_V4_FLAGS})
rc, out, _, rep = invoke(c11 / "out", [
    "--variant", "scalar_verify", "--min-threads", "1", "--min-ram-bytes", "0",
    "--volume", f"spool:{d11}:0:{vfs11.f_favail + 1000}:0",
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "0",
])
check("M11 free bytes OK but insufficient free inodes FAILS",
      rc == 1 and "free inodes" in out, (rc, out))

# M12: Unparseable cgroup memory.max fails closed instead of assuming unlimited
c12 = WORK / "c12"
proc, cg, rundir = make_env(c12, {0: ALL_V4_FLAGS}, mem_max="corrupt_value")
rc, out, _, rep = invoke(c12 / "out", [
    "--variant", "scalar_verify", "--min-threads", "1", "--min-ram-bytes", "0",
    "--proc-root", str(proc), "--sys-cgroup-root", str(cg), "--run-dir", str(rundir), "--affinity", "0",
])
check("M12 corrupt cgroup memory.max fails closed (never treated as unlimited)",
      rc == 1 and "unparseable memory.max" in out, (rc, out))

# M13: D3/D4 shortfall vector (Astra 140827Z; Fable 210950Z s.3):
# 80,000 s left, C4 = 0, target = 2,000,000,000 -> n = 25,000 r/s, floor = 12,500 r/s; tested r = 20,000 r/s
sys.path.insert(0, str(SCRIPT.parent))
import machine_check as mc  # noqa: E402

v_acc = mc.admit_budget_d4(80_000, 0, 2_000_000_000, 20_000_000, owner_shortfall_decision="accept_reduced")
v_stop = mc.admit_budget_d4(80_000, 0, 2_000_000_000, 20_000_000, owner_shortfall_decision="stop")
v_hold = mc.admit_budget_d4(80_000, 0, 2_000_000_000, 20_000_000, owner_shortfall_decision=None)
v_guess = mc.admit_budget_d4(80_000, 0, 2_000_000_000, 20_000_000, owner_shortfall_decision="accept_reduced",
                             rate_is_measured=False)
v_disk = mc.admit_budget_d4(80_000, 0, 2_000_000_000, 20_000_000, owner_shortfall_decision="accept_reduced",
                            disk_room_verified=False)
v_low = mc.admit_budget_d4(80_000, 0, 2_000_000_000, 12_000_000, owner_shortfall_decision="accept_reduced")
v_full = mc.admit_budget_d4(80_000, 0, 2_000_000_000, 25_000_000, owner_shortfall_decision=None)
mc.canonical_json_bytes(v_acc)
check("M13 D4 shortfall vector (Astra 140827Z) separates O1 reduced target from invalid evidence and floor",
      v_acc["verdict"] == "qualified_reduced" and v_acc["dispatch_allowed"] is True
      and v_acc["covers_full_target"] is False and v_acc["resources_and_evidence_valid"] is True
      and v_acc["authorized_target_rows"] == 1_600_000_000
      and v_acc["needed_rate_milli"] == 25_000_000 and v_acc["floor_rate_milli"] == 12_500_000
      and v_stop["verdict"] == "stopped_by_owner" and v_stop["dispatch_allowed"] is False
      and v_hold["verdict"] == "hold_for_owner" and v_hold["dispatch_allowed"] is False
      and v_guess["verdict"] == "unqualified" and v_guess["dispatch_allowed"] is False
      and v_disk["verdict"] == "unqualified" and v_disk["dispatch_allowed"] is False
      and v_low["verdict"] == "unqualified_below_floor" and v_low["dispatch_allowed"] is False
      and v_full["verdict"] == "qualified_full" and v_full["covers_full_target"] is True
      and v_full["authorized_target_rows"] == 2_000_000_000,
      (v_acc, v_stop, v_hold, v_guess, v_disk, v_low, v_full))

# M14: Dual-mode storage admission (Astra 141912Z; Fable 212259Z s.2):
# 180 GB available after floor vs 2,110,150,000 raw rows -> 167.61 GB normal (covered) vs 197.30 GB all-fallback (not covered)
s14 = mc.admit_storage_modes(
    available_after_floor_bytes=180_000_000_000,
    target_raw_rows=2_110_150_000,
    normal_alloc_bytes_per_krow=79_430,     # 75.1 + 4.330 B/raw row
    fallback_alloc_bytes_per_krow=93_500,   # 75.1 + 18.4 B/raw row
    open_slots_final_seal_bytes=0,
    pause_margin_bytes=1_000_000_000,
)
mc.canonical_json_bytes(s14)
check("M14 dual-mode storage admission (Astra 141912Z: 180 GB covers 167.61 GB normal, not 197.30 GB fallback)",
      s14["covers_target_normal"] is True and s14["covers_target_all_fallback"] is False
      and s14["pause_line_required"] is True
      and s14["normal_required_bytes"] == 167_609_214_500
      and s14["fallback_required_bytes"] == 197_299_025_000
      and s14["pause_at_resident_bytes"] == 179_000_000_000, s14)

# M15: FORMATS 2.2 s.1.3 instance identity: genuine same-host passes; cloned spool or null==null unprovable FAILS closed
c15 = WORK / "c15"
etc_a, dmi_a = c15 / "etc_a", c15 / "dmi_a"
etc_b, dmi_b = c15 / "etc_b", c15 / "dmi_b"
etc_c, dmi_c = c15 / "etc_c", c15 / "dmi_c"
for d in (etc_a, dmi_a, etc_b, dmi_b, etc_c, dmi_c):
    d.mkdir(parents=True)
(etc_a / "machine-id").write_text("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n", encoding="ascii")
(dmi_a / "product_uuid").write_text("11111111-2222-3333-4444-555555555555\n", encoding="ascii")
(dmi_a / "board_serial").write_text("BOARD-001\n", encoding="ascii")
(etc_b / "machine-id").write_text("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n", encoding="ascii")
(dmi_b / "product_uuid").write_text("99999999-2222-3333-4444-555555555555\n", encoding="ascii")
(dmi_b / "board_serial").write_text("BOARD-002\n", encoding="ascii")
(etc_c / "machine-id").write_text("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n", encoding="ascii")
(dmi_c / "product_uuid").write_text("Not Specified\n", encoding="ascii")
(dmi_c / "board_serial").write_text("To Be Filled By O.E.M.\n", encoding="ascii")
ia = mc.probe_instance_identity(etc_a, dmi_a)
ib = mc.probe_instance_identity(etc_b, dmi_b)
ic = mc.probe_instance_identity(etc_c, dmi_c)
check("M15 instance identity distinguishes reboot vs cloned spool and fails closed on null==null placeholders",
      ia["instance_provable"] is True and mc.same_provable_instance(ia, ia) is True
      and mc.same_provable_instance(ia, ib) is False
      and ic["instance_provable"] is False and mc.same_provable_instance(ic, ic) is False,
      (ia, ib, ic))

bad = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(bad)} of {len(results)} checks pass")
print("ALL " + str(len(results)) + " CHECKS PASS" if not bad else "FAILED: " + "; ".join(bad))
sys.exit(1 if bad else 0)

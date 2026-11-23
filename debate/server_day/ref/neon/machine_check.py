"""Neon 2026-11-23, server-day plan (SETUP_PLAN.md section 4; D1, D2, D5, D10, D15; row 44):
Linux pre-flight machine check. Standard library only (`python3 -I -B`).

Checks every resource ceiling of section 4 against effective kernel/cgroup limits rather than raw host totals:
- CPU affinity (`sched_getaffinity`) intersected with per-CPU `/proc/cpuinfo` flags for the chosen build variant,
  and effective CPU quota walking every cgroup v2 ancestor from `/proc/self/cgroup` up to `/sys/fs/cgroup`
  (with cgroup v1 fallback) plus throttle counters (`cpu.stat`);
- effective memory ceiling = min(`/proc/meminfo` MemTotal, cgroup `memory.max` across ancestors);
- effective process ceiling = min(`RLIMIT_NPROC` soft, `threads-max`, cgroup `pids.max`), plus `RLIMIT_NOFILE`
  and `RLIMIT_CORE` disableability;
- per physical filesystem (`st_dev`) deduplicated free bytes and free inodes (`statvfs`), mount flags
  (`ST_RDONLY`, `ST_NOEXEC`), directory `fsync`, and atomic create-only `os.link` (`EEXIST` preserves both);
- boot identity (`/proc/sys/kernel/random/boot_id`), live PID-1 systemd check (D15), sshd, C++ compiler,
  and Python stdlib `lzma`/`zlib`/`hashlib`/`sqlite3` round-trip.

Writes canonical ASCII JSON (`machine_check.json`, sorted keys, no floats, single LF) inside a NEW `--work-dir`.
Never uses the system temporary folder; writes nothing outside `--work-dir` and explicit writable volume dirs
(and cleans up its temporary link-probe files immediately).

Exit codes: 0 = QUALIFIED, 1 = UNQUALIFIED, 2 = bad arguments or existing `--work-dir`.
"""
import argparse
import hashlib
import json
import lzma
import os
import re
import resource
import shutil
import sqlite3
import subprocess
import sys
import time
import zlib
from pathlib import Path

V2_FLAGS = ("cx16", "lahf_lm", "popcnt", "pni", "sse4_1", "sse4_2", "ssse3")
V3_FLAGS = V2_FLAGS + ("avx", "avx2", "bmi1", "bmi2", "f16c", "fma", "abm", "movbe", "xsave")
VARIANT_FLAGS = {
    "v4": V3_FLAGS + ("avx512f", "avx512bw", "avx512cd", "avx512dq", "avx512vl"),
    "avx2_pext": V3_FLAGS,
    "avx2_nobmi2": V2_FLAGS + ("avx", "avx2"),
    "scalar_verify": (),
}

_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def canonical_json_bytes(obj: dict) -> bytes:
    """Canonical FORMATS.md section 0 JSON: ASCII, sorted keys, compact, no floats/NaN, single LF."""
    def _no_float(v):
        if isinstance(v, float):
            raise ValueError(f"float not allowed in canonical record: {v!r}")
        if isinstance(v, dict):
            for k, val in v.items():
                if not isinstance(k, str):
                    raise ValueError(f"non-str key: {k!r}")
                _no_float(val)
        elif isinstance(v, list):
            for val in v:
                _no_float(val)
    _no_float(obj)
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_immutable(path: Path, data: bytes) -> None:
    tmp = path.parent / f".{path.name}.tmp.{os.getpid()}"
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.link(str(tmp), str(path))
        fsync_dir(path.parent)
    finally:
        try:
            os.unlink(str(tmp))
        except OSError:
            pass


def _parse_int_or_none(raw: str):
    s = raw.strip()
    if not s or s == "max":
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _parse_cpu_list(spec: str) -> set:
    out = set()
    for part in spec.strip().split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(part))
    return out


def _cgroup_ancestors(root: Path, rel: str) -> list:
    rel_clean = rel.strip().lstrip("/")
    cur = root / rel_clean if rel_clean else root
    chain = []
    while True:
        chain.append(cur)
        if cur == root or cur.parent == cur:
            break
        cur = cur.parent
    return chain


def read_cgroup_limits(proc_root: Path, sys_cgroup_root: Path) -> dict:
    cg_text = _read_text(proc_root / "self" / "cgroup")
    info = {
        "mode": "unknown",
        "cpu_quota_milli": None,
        "cpuset_effective": None,
        "memory_max_bytes": None,
        "memory_high_bytes": None,
        "pids_max": None,
        "nr_throttled": None,
        "throttled_usec": None,
        "parse_errors": [],
    }
    if cg_text is None:
        info["parse_errors"].append("cannot read /proc/self/cgroup")
        return info

    v2_rel = None
    v1_map = {}
    for ln in cg_text.splitlines():
        parts = ln.split(":", 2)
        if len(parts) != 3:
            continue
        hier, ctrls, rel = parts
        if hier == "0" and ctrls == "":
            v2_rel = rel
        else:
            for c in ctrls.split(","):
                if c:
                    v1_map[c] = rel

    if v2_rel is not None:
        info["mode"] = "v2"
        for d in _cgroup_ancestors(sys_cgroup_root, v2_rel):
            cmax = _read_text(d / "cpu.max")
            if cmax is not None:
                toks = cmax.strip().split()
                if len(toks) < 2:
                    info["parse_errors"].append(f"malformed cpu.max in {d}: {cmax.strip()!r}")
                elif toks[0] != "max":
                    q = _parse_int_or_none(toks[0])
                    p = _parse_int_or_none(toks[1])
                    if q is None or p is None or p <= 0 or q < 0:
                        info["parse_errors"].append(f"unparseable cpu.max in {d}: {cmax.strip()!r}")
                    else:
                        milli = (q * 1000) // p
                        if info["cpu_quota_milli"] is None or milli < info["cpu_quota_milli"]:
                            info["cpu_quota_milli"] = milli
            mmax = _read_text(d / "memory.max")
            if mmax is not None:
                s = mmax.strip()
                if s != "max":
                    v = _parse_int_or_none(s)
                    if v is None or v < 0:
                        info["parse_errors"].append(f"unparseable memory.max in {d}: {s!r}")
                    elif info["memory_max_bytes"] is None or v < info["memory_max_bytes"]:
                        info["memory_max_bytes"] = v
            mhigh = _read_text(d / "memory.high")
            if mhigh is not None:
                v = _parse_int_or_none(mhigh)
                if v is not None and v >= 0:
                    if info["memory_high_bytes"] is None or v < info["memory_high_bytes"]:
                        info["memory_high_bytes"] = v
            pmax = _read_text(d / "pids.max")
            if pmax is not None:
                s = pmax.strip()
                if s != "max":
                    v = _parse_int_or_none(s)
                    if v is None or v < 0:
                        info["parse_errors"].append(f"unparseable pids.max in {d}: {s!r}")
                    elif info["pids_max"] is None or v < info["pids_max"]:
                        info["pids_max"] = v
            cset = _read_text(d / "cpuset.cpus.effective")
            if cset and cset.strip():
                try:
                    parsed = _parse_cpu_list(cset)
                    if info["cpuset_effective"] is None:
                        info["cpuset_effective"] = sorted(parsed)
                    else:
                        info["cpuset_effective"] = sorted(set(info["cpuset_effective"]) & parsed)
                except ValueError:
                    pass
            if info["nr_throttled"] is None:
                cstat = _read_text(d / "cpu.stat")
                if cstat:
                    for sln in cstat.splitlines():
                        st = sln.split()
                        if len(st) == 2 and st[0] == "nr_throttled":
                            info["nr_throttled"] = _parse_int_or_none(st[1])
                        elif len(st) == 2 and st[0] == "throttled_usec":
                            info["throttled_usec"] = _parse_int_or_none(st[1])
        return info

    if v1_map:
        info["mode"] = "v1"
        for cname in ("cpu", "cpuacct"):
            if cname in v1_map:
                base = sys_cgroup_root / cname
                for d in _cgroup_ancestors(base, v1_map[cname]):
                    q = _parse_int_or_none(_read_text(d / "cpu.cfs_quota_us") or "")
                    p = _parse_int_or_none(_read_text(d / "cpu.cfs_period_us") or "")
                    if q is not None and p is not None and q > 0 and p > 0:
                        milli = (q * 1000) // p
                        if info["cpu_quota_milli"] is None or milli < info["cpu_quota_milli"]:
                            info["cpu_quota_milli"] = milli
                    if info["nr_throttled"] is None:
                        cstat = _read_text(d / "cpu.stat")
                        if cstat:
                            for sln in cstat.splitlines():
                                st = sln.split()
                                if len(st) == 2 and st[0] == "nr_throttled":
                                    info["nr_throttled"] = _parse_int_or_none(st[1])
                                elif len(st) == 2 and st[0] == "throttled_time":
                                    v = _parse_int_or_none(st[1])
                                    if v is not None:
                                        info["throttled_usec"] = v // 1000
                break
        if "memory" in v1_map:
            base = sys_cgroup_root / "memory"
            for d in _cgroup_ancestors(base, v1_map["memory"]):
                v = _parse_int_or_none(_read_text(d / "memory.limit_in_bytes") or "")
                if v is not None and 0 <= v < (1 << 60):
                    if info["memory_max_bytes"] is None or v < info["memory_max_bytes"]:
                        info["memory_max_bytes"] = v
        if "pids" in v1_map:
            base = sys_cgroup_root / "pids"
            for d in _cgroup_ancestors(base, v1_map["pids"]):
                v = _parse_int_or_none(_read_text(d / "pids.max") or "")
                if v is not None and v >= 0:
                    if info["pids_max"] is None or v < info["pids_max"]:
                        info["pids_max"] = v
    return info


def parse_cpuinfo(path: Path) -> dict:
    txt = _read_text(path)
    if txt is None:
        return {}
    by_cpu = {}
    cur_id = None
    cur_flags = None
    for raw_ln in txt.splitlines() + [""]:
        ln = raw_ln.strip()
        if not ln:
            if cur_id is not None:
                by_cpu[cur_id] = cur_flags
            cur_id = None
            cur_flags = None
            continue
        if ":" not in ln:
            continue
        k, v = (x.strip() for x in ln.split(":", 1))
        if k == "processor":
            try:
                cur_id = int(v)
            except ValueError:
                cur_id = None
        elif k == "flags":
            cur_flags = set(v.split())
    return by_cpu


def parse_meminfo(path: Path) -> dict:
    txt = _read_text(path)
    out = {}
    if txt is None:
        return out
    for ln in txt.splitlines():
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        toks = v.strip().split()
        if not toks:
            continue
        try:
            n = int(toks[0])
        except ValueError:
            continue
        unit = toks[1].lower() if len(toks) > 1 else ""
        out[k.strip()] = n * 1024 if unit == "kb" else n
    return out


def probe_hardlink_atomic(target_dir: Path) -> tuple:
    """Prove os.link create-only EEXIST preserves both files + fsync_dir works on target_dir's filesystem."""
    tag = f".mc_linkprobe_{os.getpid()}_{time.monotonic_ns()}"
    probe = target_dir / tag
    try:
        probe.mkdir(mode=0o700, exist_ok=False)
        a = probe / "a.tmp"
        b = probe / "b.tmp"
        dst = probe / "final.dat"
        a.write_bytes(b"candidate_a\n")
        b.write_bytes(b"candidate_b\n")
        os.link(str(a), str(dst))
        fsync_dir(probe)
        os.unlink(str(a))
        existed_err = False
        try:
            os.link(str(b), str(dst))
        except FileExistsError:
            existed_err = True
        ok = (existed_err and dst.read_bytes() == b"candidate_a\n"
              and b.exists() and b.read_bytes() == b"candidate_b\n")
        return ok, "" if ok else "os.link did not fail with FileExistsError preserving both candidates"
    except OSError as e:
        return False, f"hardlink probe failed: {e}"
    finally:
        for name in ("a.tmp", "b.tmp", "final.dat"):
            try:
                os.unlink(str(probe / name))
            except OSError:
                pass
        try:
            probe.rmdir()
        except OSError:
            pass


def check_codecs() -> tuple:
    sample = (b"sg 8 15 e2e4 rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\n" * 64)
    try:
        if lzma.decompress(lzma.compress(sample, preset=6)) != sample:
            return False, "lzma preset 6 roundtrip mismatch"
        if zlib.decompress(zlib.compress(sample, level=6)) != sample:
            return False, "zlib level 6 roundtrip mismatch"
        if len(hashlib.sha256(sample).hexdigest()) != 64:
            return False, "sha256 digest length mismatch"
        con = sqlite3.connect(":memory:")
        try:
            con.execute("CREATE TABLE t (k BLOB PRIMARY KEY, v INTEGER)")
            con.execute("INSERT INTO t VALUES (?, ?)", (b"k", 1))
            row = con.execute("SELECT v FROM t WHERE k=?", (b"k",)).fetchone()
            if row != (1,):
                return False, "sqlite3 roundtrip mismatch"
        finally:
            con.close()
    except Exception as e:  # noqa: BLE001
        return False, f"codec/stdlib check failed: {e}"
    return True, ""


def find_compilers(explicit: str) -> list:
    candidates = [explicit] if explicit else ["g++", "clang++"]
    found = []
    for name in candidates:
        path = shutil.which(name)
        if not path:
            continue
        try:
            p = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10, check=False)
            first = (p.stdout.splitlines() or p.stderr.splitlines() or [""])[0].strip()
            if p.returncode == 0 and first:
                found.append({"name": name, "path": path, "version": first[:200]})
        except OSError:
            continue
    return found


def parse_volume_spec(spec: str) -> dict:
    # Format: label:path:min_bytes:min_inodes:exec(0|1)
    if ":" not in spec:
        raise ValueError(f"invalid --volume spec (need label:path:min_bytes:min_inodes:exec): {spec!r}")
    label, rest = spec.split(":", 1)
    parts = rest.rsplit(":", 3)
    if len(parts) != 4:
        raise ValueError(f"invalid --volume spec (need label:path:min_bytes:min_inodes:exec): {spec!r}")
    raw_path, mb, mi, ex = parts
    if not label or not raw_path or ex not in ("0", "1"):
        raise ValueError(f"invalid --volume spec: {spec!r}")
    min_b, min_i = int(mb), int(mi)
    if min_b < 0 or min_i < 0:
        raise ValueError(f"negative threshold in --volume spec: {spec!r}")
    return {
        "label": label,
        "path": Path(raw_path).resolve(),
        "min_bytes": min_b,
        "min_inodes": min_i,
        "need_exec": ex == "1",
    }


def admit_budget_d4(
    remaining_seconds: int,
    c4_done: int,
    target_rows: int,
    safe_tested_rate_milli: int,
    *,
    owner_shortfall_decision=None,
    rate_is_measured: bool = True,
    disk_room_verified: bool = True,
) -> dict:
    """D3/D4 budget admission separated from pre-flight hardware capability (Astra 140827Z; Fable 210950Z s.3).

    All rates are integers in thousandths of a row/s (FORMATS.md 2.1 s.0: no floats).
    `owner_shortfall_decision` is None (absent), 'accept_reduced', or 'stop'.
    Guessed scaling or unverified disk room stays unqualified under every O1 value.
    """
    valid_inputs = (
        isinstance(remaining_seconds, int) and not isinstance(remaining_seconds, bool) and remaining_seconds > 0
        and isinstance(c4_done, int) and not isinstance(c4_done, bool) and c4_done >= 0
        and isinstance(target_rows, int) and not isinstance(target_rows, bool) and target_rows > 0
        and isinstance(safe_tested_rate_milli, int) and not isinstance(safe_tested_rate_milli, bool)
        and safe_tested_rate_milli >= 0
        and owner_shortfall_decision in (None, "accept_reduced", "stop")
    )
    resources_and_evidence_valid = bool(valid_inputs and rate_is_measured and disk_room_verified)
    if not valid_inputs:
        return {
            "stage": "pilot_budget_admission",
            "resources_and_evidence_valid": False,
            "covers_full_target": False,
            "dispatch_allowed": False,
            "d4_row": "unqualified_invalid_input",
            "verdict": "unqualified",
            "authorized_target_rows": None,
            "needed_rate_milli": None,
            "floor_rate_milli": None,
            "safe_tested_rate_milli": safe_tested_rate_milli if isinstance(safe_tested_rate_milli, int) else None,
        }

    remaining_target = max(0, target_rows - c4_done)
    needed_rate_milli = (remaining_target * 1000 + remaining_seconds - 1) // remaining_seconds
    floor_rate_milli = needed_rate_milli // 2
    covers_full_target = bool(resources_and_evidence_valid and safe_tested_rate_milli >= needed_rate_milli)

    if not resources_and_evidence_valid:
        verdict, d4_row, dispatch_allowed, authorized = (
            "unqualified",
            "unqualified_evidence",
            False,
            None,
        )
    elif covers_full_target:
        verdict, d4_row, dispatch_allowed, authorized = (
            "qualified_full",
            "full_target",
            True,
            target_rows,
        )
    elif safe_tested_rate_milli >= floor_rate_milli:
        reduced_target = c4_done + (safe_tested_rate_milli * remaining_seconds) // 1000
        if owner_shortfall_decision == "accept_reduced":
            verdict, d4_row, dispatch_allowed, authorized = (
                "qualified_reduced",
                "shortfall_accept_reduced",
                True,
                reduced_target,
            )
        elif owner_shortfall_decision == "stop":
            verdict, d4_row, dispatch_allowed, authorized = (
                "stopped_by_owner",
                "shortfall_stop",
                False,
                None,
            )
        else:
            verdict, d4_row, dispatch_allowed, authorized = (
                "hold_for_owner",
                "shortfall_hold",
                False,
                None,
            )
    else:
        verdict, d4_row, dispatch_allowed, authorized = (
            "unqualified_below_floor",
            "below_floor",
            False,
            None,
        )

    return {
        "stage": "pilot_budget_admission",
        "resources_and_evidence_valid": resources_and_evidence_valid,
        "covers_full_target": covers_full_target,
        "dispatch_allowed": dispatch_allowed,
        "d4_row": d4_row,
        "verdict": verdict,
        "authorized_target_rows": authorized,
        "needed_rate_milli": needed_rate_milli,
        "floor_rate_milli": floor_rate_milli,
        "safe_tested_rate_milli": safe_tested_rate_milli,
    }


def admit_storage_modes(
    available_after_floor_bytes: int,
    target_raw_rows: int,
    normal_alloc_bytes_per_krow: int,
    fallback_alloc_bytes_per_krow: int,
    *,
    open_slots_final_seal_bytes: int = 0,
    pause_margin_bytes: int = 0,
) -> dict:
    """Two-mode storage admission (Astra 141912Z; Fable 212259Z s.2; D2 no deletion).

    Rates are allocated bytes per 1,000 raw rows (integer, zero floats).
    Reports normal and all-fallback capacities separately; when all-fallback is not covered,
    computes the exact resident-bytes pause line with open slots' final seals budgeted inside the floor.
    """
    if (
        not isinstance(available_after_floor_bytes, int) or isinstance(available_after_floor_bytes, bool)
        or available_after_floor_bytes < 0
        or not isinstance(target_raw_rows, int) or isinstance(target_raw_rows, bool) or target_raw_rows <= 0
        or not isinstance(normal_alloc_bytes_per_krow, int) or isinstance(normal_alloc_bytes_per_krow, bool)
        or normal_alloc_bytes_per_krow <= 0
        or not isinstance(fallback_alloc_bytes_per_krow, int) or isinstance(fallback_alloc_bytes_per_krow, bool)
        or fallback_alloc_bytes_per_krow <= 0
        or not isinstance(open_slots_final_seal_bytes, int) or isinstance(open_slots_final_seal_bytes, bool)
        or open_slots_final_seal_bytes < 0
        or not isinstance(pause_margin_bytes, int) or isinstance(pause_margin_bytes, bool)
        or pause_margin_bytes < 0
    ):
        raise ValueError("storage mode admission requires non-negative integer inputs and positive rates")

    normal_need = (target_raw_rows * normal_alloc_bytes_per_krow + 999) // 1000
    fallback_need = (target_raw_rows * fallback_alloc_bytes_per_krow + 999) // 1000
    usable = max(0, available_after_floor_bytes - open_slots_final_seal_bytes)
    normal_cap_rows = (usable * 1000) // normal_alloc_bytes_per_krow
    fallback_cap_rows = (usable * 1000) // fallback_alloc_bytes_per_krow
    covers_normal = usable >= normal_need
    covers_fallback = usable >= fallback_need
    pause_at_resident_bytes = max(0, usable - pause_margin_bytes)
    return {
        "available_after_floor_bytes": available_after_floor_bytes,
        "usable_after_open_seals_bytes": usable,
        "target_raw_rows": target_raw_rows,
        "normal_required_bytes": normal_need,
        "fallback_required_bytes": fallback_need,
        "normal_capacity_raw_rows": normal_cap_rows,
        "fallback_capacity_raw_rows": fallback_cap_rows,
        "covers_target_normal": covers_normal,
        "covers_target_all_fallback": covers_fallback,
        "pause_line_required": bool(covers_normal and not covers_fallback),
        "pause_at_resident_bytes": pause_at_resident_bytes,
    }


_PLACEHOLDER_DMI = frozenset({
    "", "none", "n/a", "na", "not specified", "to be filled by o.e.m.",
    "default string", "system serial number", "00000000-0000-0000-0000-000000000000",
    "ffffffff-ffff-ffff-ffff-ffffffffffff",
})


def probe_instance_identity(etc_dir: Path, dmi_dir: Path) -> dict:
    """Read host instance identifiers (FORMATS.md 2.2 s.1.1/s.1.3) without emitting raw secrets.

    Missing, unreadable, or placeholder DMI strings record as None; two None values NEVER prove same-host.
    `instance_provable` is True only when a non-placeholder hardware-bound identifier (product_uuid or
    board_serial) is readable alongside a valid machine_id.
    """
    def _clean(path: Path):
        raw = _read_text(path)
        if raw is None:
            return None
        val = raw.strip()
        if not val or val.lower() in _PLACEHOLDER_DMI:
            return None
        return val

    mid = _clean(etc_dir / "machine-id")
    puuid = _clean(dmi_dir / "product_uuid")
    bser = _clean(dmi_dir / "board_serial")

    def _h(v):
        return hashlib.sha256(v.encode("utf-8", errors="strict")).hexdigest() if v is not None else None

    return {
        "machine_id_sha256": _h(mid),
        "product_uuid_sha256": _h(puuid),
        "board_serial_sha256": _h(bser),
        "instance_provable": bool(mid is not None and (puuid is not None or bser is not None)),
    }


def same_provable_instance(header_inst: dict, current_inst: dict) -> bool:
    """Strict same-host check for FORMATS.md 2.2 s.1.3 boot guard: never treats None == None as equal."""
    if not (header_inst.get("instance_provable") and current_inst.get("instance_provable")):
        return False
    for key in ("machine_id_sha256", "product_uuid_sha256", "board_serial_sha256"):
        h_val = header_inst.get(key)
        c_val = current_inst.get(key)
        if h_val is not None and h_val != c_val:
            return False
        if c_val is not None and h_val is None:
            return False
    return True


def run_check(args) -> tuple:
    proc_root = Path(args.proc_root)
    sys_cgroup_root = Path(args.sys_cgroup_root)
    run_dir = Path(args.run_dir)
    failures = []

    # 1. CPU affinity, per-CPU flags, and cgroup quota
    if args.affinity is not None:
        aff_cpus = sorted(_parse_cpu_list(args.affinity))
    else:
        aff_cpus = sorted(os.sched_getaffinity(0))
    cg = read_cgroup_limits(proc_root, sys_cgroup_root)
    for err in cg["parse_errors"]:
        failures.append(f"cgroup: {err}")
    effective_aff = aff_cpus
    if cg["cpuset_effective"] is not None:
        inter = sorted(set(aff_cpus) & set(cg["cpuset_effective"]))
        effective_aff = inter

    by_cpu = parse_cpuinfo(proc_root / "cpuinfo")
    missing_cpu_entries = [c for c in effective_aff if c not in by_cpu]
    missing_flag_lines = [c for c in effective_aff if c in by_cpu and by_cpu[c] is None]
    need_flags = VARIANT_FLAGS[args.variant]
    missing_flags_by_cpu = {}
    if not effective_aff:
        failures.append("cpu: empty effective CPU affinity set")
    if missing_cpu_entries:
        failures.append(f"cpu: affinity CPUs missing from cpuinfo: {missing_cpu_entries}")
    if missing_flag_lines:
        failures.append(f"cpu: missing flags line in cpuinfo for CPUs: {missing_flag_lines}")
    if effective_aff and not missing_cpu_entries and not missing_flag_lines:
        for c in effective_aff:
            miss = sorted(f for f in need_flags if f not in by_cpu[c])
            if miss:
                missing_flags_by_cpu[str(c)] = miss
        if missing_flags_by_cpu:
            failures.append(f"cpu: variant {args.variant} missing flags on affinity CPUs: {missing_flags_by_cpu}")

    aff_milli = len(effective_aff) * 1000
    eff_cpus_milli = aff_milli if cg["cpu_quota_milli"] is None else min(aff_milli, cg["cpu_quota_milli"])
    if eff_cpus_milli < args.min_threads * 1000:
        failures.append(
            f"cpu: effective threads {eff_cpus_milli} milli-CPUs < required {args.min_threads * 1000}"
        )

    # 2. Memory
    meminfo = parse_meminfo(proc_root / "meminfo")
    mem_total = meminfo.get("MemTotal")
    mem_avail = meminfo.get("MemAvailable")
    if mem_total is None:
        failures.append("memory: MemTotal unreadable from meminfo")
        eff_ram = 0
    else:
        eff_ram = mem_total if cg["memory_max_bytes"] is None else min(mem_total, cg["memory_max_bytes"])
        if eff_ram < args.min_ram_bytes:
            failures.append(f"memory: effective RAM {eff_ram} B < required {args.min_ram_bytes} B")

    # 3. Process, file-descriptor, and core-dump limits
    nofile_soft, nofile_hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    nproc_soft, nproc_hard = resource.getrlimit(resource.RLIMIT_NPROC)
    core_soft, core_hard = resource.getrlimit(resource.RLIMIT_CORE)
    threads_max = _parse_int_or_none(_read_text(proc_root / "sys" / "kernel" / "threads-max") or "")

    pid_ceilings = []
    if nproc_soft >= 0:
        pid_ceilings.append(nproc_soft)
    if threads_max is not None and threads_max >= 0:
        pid_ceilings.append(threads_max)
    if cg["pids_max"] is not None:
        pid_ceilings.append(cg["pids_max"])
    eff_pids = min(pid_ceilings) if pid_ceilings else None

    if nofile_soft >= 0 and nofile_soft < args.min_nofile:
        failures.append(f"limits: RLIMIT_NOFILE soft {nofile_soft} < required {args.min_nofile}")
    if eff_pids is not None and eff_pids < args.min_pids:
        failures.append(f"limits: effective pid ceiling {eff_pids} < required {args.min_pids}")
    core_disable_ok = True
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (OSError, ValueError):
        core_disable_ok = False
        failures.append(f"limits: cannot disable core dumps (RLIMIT_CORE=({core_soft},{core_hard}))")

    # 4. Storage volumes, st_dev deduplication, mount flags, inodes, hard-link probe
    volumes = [parse_volume_spec(v) for v in args.volume]
    vol_reports = []
    by_dev = {}
    for vol in volumes:
        p = vol["path"]
        rec = {
            "label": vol["label"],
            "path": str(p),
            "min_bytes": vol["min_bytes"],
            "min_inodes": vol["min_inodes"],
            "need_exec": vol["need_exec"],
        }
        if not p.exists() or not p.is_dir():
            rec["ok"] = False
            rec["error"] = "missing or not a directory"
            failures.append(f"storage:{vol['label']}: missing or not a directory ({p})")
            vol_reports.append(rec)
            continue
        st = os.stat(str(p))
        vfs = os.statvfs(str(p))
        free_bytes = vfs.f_bavail * vfs.f_frsize
        free_inodes = vfs.f_favail
        total_inodes = vfs.f_files
        ro = bool(vfs.f_flag & os.ST_RDONLY)
        noexec = bool(vfs.f_flag & os.ST_NOEXEC)
        rec.update({
            "st_dev": st.st_dev,
            "free_bytes": free_bytes,
            "free_inodes": free_inodes,
            "total_inodes": total_inodes,
            "read_only": ro,
            "noexec": noexec,
            "ok": True,
        })
        if ro:
            rec["ok"] = False
            failures.append(f"storage:{vol['label']}: filesystem is mounted read-only")
        if vol["need_exec"] and noexec:
            rec["ok"] = False
            failures.append(f"storage:{vol['label']}: filesystem is mounted noexec")
        by_dev.setdefault(st.st_dev, []).append(rec)
        vol_reports.append(rec)

    dev_reports = []
    for dev_id, items in sorted(by_dev.items()):
        sum_bytes = sum(x["min_bytes"] for x in items)
        sum_inodes = sum(x["min_inodes"] for x in items)
        free_bytes = min(x["free_bytes"] for x in items)
        free_inodes = min(x["free_inodes"] for x in items)
        total_inodes = min(x["total_inodes"] for x in items)
        labels = [x["label"] for x in items]
        hl_ok, hl_err = (True, "")
        if not any(x["read_only"] for x in items):
            hl_ok, hl_err = probe_hardlink_atomic(Path(items[0]["path"]))
        if free_bytes < sum_bytes:
            failures.append(
                f"storage:dev={dev_id}({','.join(labels)}): free {free_bytes} B < combined required {sum_bytes} B"
            )
        if total_inodes > 0 and free_inodes < sum_inodes:
            failures.append(
                f"storage:dev={dev_id}({','.join(labels)}): free inodes {free_inodes} < combined required {sum_inodes}"
            )
        if not hl_ok:
            failures.append(f"storage:dev={dev_id}({','.join(labels)}): {hl_err}")
        dev_reports.append({
            "st_dev": dev_id,
            "labels": labels,
            "combined_min_bytes": sum_bytes,
            "combined_min_inodes": sum_inodes,
            "free_bytes": free_bytes,
            "free_inodes": free_inodes,
            "total_inodes": total_inodes,
            "hardlink_atomic_ok": hl_ok,
            "hardlink_error": hl_err,
        })

    # 5. Boot identity, clock, systemd (D15), sshd, compiler, codecs
    boot_raw = _read_text(proc_root / "sys" / "kernel" / "random" / "boot_id")
    boot_id = boot_raw.strip() if boot_raw else ""
    if not _UUID_RE.fullmatch(boot_id):
        failures.append("boot: /proc/sys/kernel/random/boot_id missing or invalid UUID")

    pid1_comm = (_read_text(proc_root / "1" / "comm") or "").strip()
    systemd_dir = (run_dir / "systemd" / "system").is_dir()
    systemd_live = (pid1_comm == "systemd" and systemd_dir)
    if args.require_systemd and not systemd_live:
        failures.append(
            f"systemd: PID 1 is {pid1_comm!r}, /run/systemd/system exists={systemd_dir} (D15 requires live systemd)"
        )

    sshd_path = shutil.which("sshd") or ("/usr/sbin/sshd" if os.access("/usr/sbin/sshd", os.X_OK) else "")
    if args.require_sshd and not sshd_path:
        failures.append("sshd: sshd binary not found")

    compilers = find_compilers(args.compiler)
    if not compilers:
        failures.append(f"compiler: no runnable C++ compiler found (requested={args.compiler or 'g++/clang++'})")

    codecs_ok, codecs_err = check_codecs()
    if not codecs_ok:
        failures.append(f"codecs: {codecs_err}")

    instance_info = probe_instance_identity(Path(args.etc_dir), Path(args.dmi_dir))

    report = {
        "schema": 1,
        "stage": "preflight_hardware",
        "qualified": len(failures) == 0,
        "resources_and_evidence_valid": len(failures) == 0,
        "pilot_rate_qualified": None,
        "covers_full_target": None,
        "variant": args.variant,
        "failures": failures,
        "cpu": {
            "affinity_cpus": aff_cpus,
            "effective_affinity_cpus": effective_aff,
            "effective_cpus_milli": eff_cpus_milli,
            "min_threads": args.min_threads,
            "required_flags": list(need_flags),
            "missing_cpu_entries": missing_cpu_entries,
            "missing_flag_lines": missing_flag_lines,
            "missing_flags_by_cpu": missing_flags_by_cpu,
            "cgroup_mode": cg["mode"],
            "cgroup_cpu_quota_milli": cg["cpu_quota_milli"],
            "nr_throttled": cg["nr_throttled"],
            "throttled_usec": cg["throttled_usec"],
        },
        "memory": {
            "mem_total_bytes": mem_total,
            "mem_available_bytes": mem_avail,
            "cgroup_memory_max_bytes": cg["memory_max_bytes"],
            "cgroup_memory_high_bytes": cg["memory_high_bytes"],
            "effective_ram_bytes": eff_ram,
            "min_ram_bytes": args.min_ram_bytes,
        },
        "limits": {
            "nofile_soft": nofile_soft,
            "nofile_hard": nofile_hard,
            "min_nofile": args.min_nofile,
            "nproc_soft": nproc_soft,
            "nproc_hard": nproc_hard,
            "threads_max": threads_max,
            "cgroup_pids_max": cg["pids_max"],
            "effective_pids_max": eff_pids,
            "min_pids": args.min_pids,
            "core_disable_ok": core_disable_ok,
        },
        "storage": {
            "volumes": vol_reports,
            "by_device": dev_reports,
        },
        "runtime": {
            "boot_id_valid": bool(_UUID_RE.fullmatch(boot_id)),
            "boot_id_sha256": hashlib.sha256(boot_id.encode("ascii")).hexdigest() if boot_id else "",
            "instance": instance_info,
            "pid1_comm": pid1_comm,
            "systemd_dir": systemd_dir,
            "systemd_live": systemd_live,
            "require_systemd": bool(args.require_systemd),
            "sshd_found": bool(sshd_path),
            "require_sshd": bool(args.require_sshd),
            "compilers": compilers,
            "codecs_ok": codecs_ok,
            "python_version": sys.version.split()[0],
            "checked_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
    }
    return len(failures) == 0, report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Section 4 Linux machine check (Neon reference)")
    p.add_argument("--work-dir", required=True, help="NEW work directory for machine_check.json")
    p.add_argument("--variant", required=True, choices=sorted(VARIANT_FLAGS))
    p.add_argument("--min-threads", type=int, default=1)
    p.add_argument("--min-ram-bytes", type=int, default=1024 * 1024 * 1024)
    p.add_argument("--min-nofile", type=int, default=4096)
    p.add_argument("--min-pids", type=int, default=512)
    p.add_argument("--volume", action="append", default=[],
                   help="label:path:min_bytes:min_inodes:exec(0|1); repeatable")
    p.add_argument("--require-systemd", action="store_true")
    p.add_argument("--require-sshd", action="store_true")
    p.add_argument("--compiler", default="")
    # Test/rehearsal roots (default to real Linux kernel interfaces)
    p.add_argument("--proc-root", default="/proc")
    p.add_argument("--sys-cgroup-root", default="/sys/fs/cgroup")
    p.add_argument("--run-dir", default="/run")
    p.add_argument("--etc-dir", default="/etc")
    p.add_argument("--dmi-dir", default="/sys/class/dmi/id")
    p.add_argument("--affinity", default=None, help="Override CPU affinity list for rehearsal (e.g. 0-3)")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 2

    if args.min_threads < 1 or args.min_ram_bytes < 0 or args.min_nofile < 1 or args.min_pids < 1:
        print("STOP: thresholds must be non-negative (min-threads/nofile/pids >= 1)", file=sys.stderr)
        return 2

    work = Path(args.work_dir).resolve()
    if work.exists():
        print(f"STOP: work dir already exists: {work}", file=sys.stderr)
        return 2
    work.mkdir(parents=True, exist_ok=False)

    if not args.volume:
        args.volume = [f"work:{work}:0:0:1"]

    try:
        ok, report = run_check(args)
    except ValueError as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 2

    out_path = work / "machine_check.json"
    write_immutable(out_path, canonical_json_bytes(report))
    if ok:
        print(f"QUALIFIED variant={args.variant} eff_milli_cpus={report['cpu']['effective_cpus_milli']} "
              f"eff_ram_bytes={report['memory']['effective_ram_bytes']} report={out_path}")
        return 0
    print(f"UNQUALIFIED ({len(report['failures'])}): " + " | ".join(report["failures"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())

# Neon — Verified Linux kernel probe spec for Section 4 `machine_check` (cgroup v2 ancestor walk, mount flags, `st_dev`, `D15`)

Date: 2026-11-23T13:35:00Z
Seat: Neon

While waiting for `SETUP_PLAN.md` v2.2, `FORMATS.md` v2, and the v2 scripts, I tested the exact Linux kernel interfaces Section 4 `machine_check` needs on this Ubuntu 24.04 cgroup v2 host and caught a concrete trap worth preventing before `machine_check` is written.

---

## 1. Live trap caught: `/sys/fs/cgroup/{cpu,memory,pids}.max` do NOT exist at the root on a non-namespaced cgroup v2 host

On this Linux host right now:
- `/proc/meminfo` reports `MemTotal: 16,387,328 kB` (`15.63 GiB`).
- `/sys/fs/cgroup/memory.max`, `/sys/fs/cgroup/cpu.max`, and `/sys/fs/cgroup/pids.max` **do not exist** (only `/sys/fs/cgroup/cpu.stat` and `/sys/fs/cgroup/cpuset.cpus.effective` exist at root).
- Walking `/proc/self/cgroup` (`0::<relpath>`) up to `/sys/fs/cgroup` found the real workload ceiling on the leaf cgroup: `memory.max = 15,706,882,048` (`14.63 GiB`, `1.00 GiB` below `MemTotal`) and `cpu.max = max 100000`, `pids.max = max`, `cpuset.cpus.effective = 0-3` on its parent slices.

**Consequence for `machine_check`:**
1. **Effective CPU ceiling** = `min(len(os.sched_getaffinity(0)), cgroup_effective_cpu_quota)` where `cgroup_effective_cpu_quota` walks **every** directory from `/sys/fs/cgroup/<relpath>` up to `/sys/fs/cgroup` (taking `min(quota / period)` over all numeric `cpu.max` files, plus cgroup v1 `cpu/cpu.cfs_quota_us` / `cpu.cfs_period_us` fallback if `/proc/self/cgroup` has no `0::` line). Also record `cpu.stat` (`nr_throttled`, `throttled_usec`) before and after the pilot so throttling during the pilot is visible.
2. **Effective memory ceiling** = `min(MemTotal_bytes, cgroup_effective_memory_max)` walking the same ancestor chain over all numeric `memory.max` (and `memory.high` reported as warning/advisory, plus cgroup v1 `memory.limit_in_bytes` fallback). Also check `MemAvailable` and swap state.
3. **Effective process ceiling** = `min(RLIMIT_NPROC soft, cgroup_effective_pids_max, /proc/sys/kernel/threads-max)`.
4. **Per-CPU ISA flags across affinity** = intersect `flags` across **every** logical CPU id in `os.sched_getaffinity(0)` from `/proc/cpuinfo` (not just the first entry in `/proc/cpuinfo`, and failing closed if any CPU in the affinity set is missing from `/proc/cpuinfo` or lacks a required flag for the chosen target).
5. **Disk, inodes, mount flags, and shared-mount deduplication (`os.statvfs` + `os.stat`):**
   - Check `os.statvfs(p).f_flag`: refuse if `f_flag & os.ST_RDONLY` (read-only) on any writable dir, and refuse if `f_flag & os.ST_NOEXEC` on the build/bin dir (exec of `forge` fails with `EACCES` on `noexec` mounts).
   - Check both free bytes (`f_bavail * f_frsize`) AND free inodes (`f_favail`, failing if below required piece/file headroom).
   - Group `work_dir`, `spool_dir`, `build_dir` by `os.stat(p).st_dev`: when two folders share one filesystem (`st_dev` equal), compare their **summed** space and inode budgets against that single mount's free capacity rather than checking each independently against the full mount.
6. **Core dumps & file descriptors (`RLIMIT_CORE`, `RLIMIT_NOFILE`):**
   - On this host `RLIMIT_CORE = (0, -1)` (soft `0`, hard unlimited). The server guard should explicitly set `RLIMIT_CORE = (0, 0)` before spawning `forge` (Section 7 row 17) and verify `RLIMIT_NOFILE >= required_fds` (workers + pipes + log/meta/raw/lock FDs + headroom).
7. **Boot identity & unattended reboot gate (`D5`, `D15`):**
   - `/proc/sys/kernel/random/boot_id` exists and gives the canonical per-boot UUID for `D5` boot-change detection.
   - Checking `/run/systemd/system` + `/proc/1/comm` live on this host immediately detects a non-systemd container (`PID 1 comm = tini`, `/run/systemd/system` missing, `sshd` absent), proving the `D15` gate cleanly distinguishes bare-metal/systemd VMs from container hosts without `systemd` before any paid run starts.

---

## 2. Quick note on Astra `133211Z`

Noted Astra's 3-cohort byte-equality run (`288` games, `36,453` raw rows) across all six freshly built native binaries showing bit-identical ordered slot/piece bytes, and agreed with her discipline: those runs verify determinism across builds, not paid-day throughput or PC filtering speed, which must come from the target host's pilot at admitted width.

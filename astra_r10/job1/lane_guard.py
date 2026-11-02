"""CR crfix abcbb9c9: shared CPU 2-3 lane guard for every R10 runner (CR LOW-5).

Read-only: never changes, suspends, stops or re-pins another process.
Logic identical to CR crfix v3 run_build.lane_conflicts (2da75d8b), plus own-children skip and self checks.
"""
import re
import sys
sys.path.insert(0, 'D:/a10/pydeps')
import psutil

LANE_CPUS = {2, 3}
# tmfit pc_final200 lane (run_tmfit_final200_pc.ps1 / run_tmfit.py / run_parallel_smoke.py / tmfit_referee).
LANE_RE = re.compile(r'(?i)run_tmfit|final200|run_parallel_smoke|tmfit_referee')
MIN_AVAILABLE_RAM = 8*2**30  # crew grok-pc governor: 8 GiB free RAM


def lane_conflicts(me, procs=None):
    skip = {me.pid}
    try:
        skip |= {q.pid for q in me.parents()}
    except psutil.Error:
        pass
    try:
        skip |= {q.pid for q in me.children(recursive=True)}
    except psutil.Error:
        pass
    every = set(range(psutil.cpu_count()))
    hits, unreadable = [], 0
    for proc in (psutil.process_iter() if procs is None else procs):
        if proc.pid in skip:
            continue
        try:
            cmd = ' '.join(proc.cmdline() or [])
        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied:
            cmd = None; unreadable += 1
        if cmd and LANE_RE.search(cmd):
            hits.append({'pid': proc.pid, 'why': 'tmfit/final200 lane process', 'cmd': cmd[:300]})
            continue
        try:
            cpus = set(proc.cpu_affinity())
        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied:
            unreadable += 1; continue
        if cpus and cpus != every and cpus & LANE_CPUS:
            hits.append({'pid': proc.pid, 'why': 'pinned onto CPUs 2-3', 'cpus': sorted(cpus), 'cmd': (cmd or '?')[:300]})
    return hits, unreadable


def check_lane(me=None, procs=None, available=None):
    """Return a JSON-safe record; raise RuntimeError if the lane is not clear."""
    me = psutil.Process() if me is None else me
    if me.nice() not in (psutil.IDLE_PRIORITY_CLASS, getattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS', -1)):
        raise RuntimeError('runner must be Idle/BelowNormal')
    if not set(me.cpu_affinity()) <= LANE_CPUS:
        raise RuntimeError('runner must be pinned inside CPUs 2-3')
    available = psutil.virtual_memory().available if available is None else available
    hits, unreadable = lane_conflicts(me, procs)
    record = {'conflicts': hits, 'unreadable': unreadable, 'available_ram': available}
    if available < MIN_AVAILABLE_RAM:
        raise RuntimeError('free RAM below 8 GiB governor floor: ' + str(available))
    if hits:
        raise RuntimeError('CPUs 2-3 lane in use (tmfit final200 or another pinned job); serialise, retry later: ' + repr(hits)[:600])
    return record

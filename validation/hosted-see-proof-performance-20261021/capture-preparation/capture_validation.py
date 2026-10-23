"""Derived only from qualified21 grammar/process validator; explicit per-source node identity. No speed analysis."""
import math,re,hashlib
from pathlib import Path
EXPECTED_NODES=321912
BENCHES_PER_PROCESS=5
BOOTSTRAP_SEED=20261029
BOOTSTRAP_DRAWS=10000
BENCH_LINE=re.compile(rb'info string bench depth ([1-9][0-9]*) nodes ([1-9][0-9]*) time ([1-9][0-9]*) nps ([1-9][0-9]*)(\r?\n)')
def parse_bench(raw,expected_nodes):
    if not isinstance(raw,bytes):raise ValueError('Original benchmark bytes required')
    rows=raw.splitlines(keepends=True)
    if len(rows)!=BENCHES_PER_PROCESS:raise ValueError('Exactly five complete canonical rows required')
    records=[];endings=set()
    for line in rows:
        match=BENCH_LINE.fullmatch(line)
        if not match:raise ValueError('Noncanonical benchmark output')
        depth,nodes,millis,nps=map(int,match.groups()[:4]);endings.add(match[5])
        if depth!=11 or nodes!=expected_nodes or nps!=nodes*1000//millis:raise ValueError('Benchmark work/numeric signature differs')
        records.append({'depth':depth,'nodes':nodes,'time_ms':millis,'nps':nps})
    if len(endings)!=1:raise ValueError('Mixed benchmark line endings')
    return records

def positive(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<=0:raise ValueError('Metric must be finite positive number')
    return value

def validate_sample(facts,out,cpu,expected_nodes):
    if (facts.get('returncode_before_verdict')!=0 or facts.get('returncode')!=0 or facts.get('timed_out') is not False or facts.get('owned_group_empty_before_verdict') is not True or facts.get('owned_group_empty_after_cleanup') is not True or facts.get('measurement_affinity')!=[cpu] or facts.get('wall_stop_reason')!='wait4_leader_observed' or any(k in facts for k in ('error','cleanup_error','affinity_restore_error'))):raise ValueError('Faulted sample process; entire attempt invalid')
    for stream in ('stdout','stderr'):
        digest=hashlib.sha256((out/(stream+'.txt')).read_bytes()).hexdigest()
        if facts.get(stream+'_sha256_before_verdict')!=digest or facts.get(stream+'_sha256')!=digest:raise ValueError('Sample original stream changed')
    if (out/'stderr.txt').read_bytes():raise ValueError('Sample stderr/warning invalidates attempt')
    for metric in ('cpu','wall'):positive(facts[metric+'_seconds_before_verdict'])
    limit=positive(facts['timeout_seconds'])
    if limit>60 or facts['wall_seconds_before_verdict']>limit:raise TimeoutError('Sample whole-process wall exceeded its strict deadline')
    user,system=facts['user_seconds_before_verdict'],facts['system_seconds_before_verdict']
    if any(type(x) not in (float,int) or not math.isfinite(x) or x<0 for x in (user,system)) or user+system!=facts['cpu_seconds_before_verdict']:raise ValueError('Exact-child CPU accounting differs')
    return parse_bench((out/'stdout.txt').read_bytes(),expected_nodes)

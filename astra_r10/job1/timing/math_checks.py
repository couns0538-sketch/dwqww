"""R10 ABBA arithmetic and immutable input validation; no subprocesses."""
import hashlib
import json
import math
import pathlib
import statistics

NODES = 12389307
LOCK = 'fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072'


def sha(path):
    with pathlib.Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def protocol_snapshot(path):
    """Bind the protocol to the actual bytes consumed, detecting a read/hash race."""
    raw = pathlib.Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if sha(path) != digest:
        raise ValueError('protocol changed while taking snapshot')
    return raw, json.loads(raw.decode('utf-8-sig')), digest


def summary(values):
    if not values:
        return None
    if any(not math.isfinite(v) for v in values):
        raise ValueError('nonfinite statistic')
    q1, _, q3 = statistics.quantiles(values, n=4, method='inclusive') if len(values) > 1 else [values[0]] * 3
    return dict(count=len(values), median=statistics.median(values), q1=q1, q3=q3,
                iqr=q3-q1, min=min(values), max=max(values))


def block_ratio(rows):
    if len(rows) != 4 or [r['arm'] for r in rows] != list('ABBA'):
        raise ValueError('one complete A-B-B-A block required')
    rates = []
    for row in rows:
        if row['status'] != 'PASS' or row['nodes'] != NODES:
            raise ValueError('incomplete run or wrong search work')
        wall = row['wall_seconds']
        if not math.isfinite(wall) or wall <= 0:
            raise ValueError('invalid external wall time')
        rates.append(NODES / wall)
    return math.sqrt((rates[1] / rates[0]) * (rates[2] / rates[3]))


def calibration(gains):
    stats = summary(gains)
    passed = (len(gains) == 10 and abs(stats['median']) <= .5 and stats['iqr'] <= 1
              and stats['min'] >= -2 and stats['max'] <= 2)
    return dict(passed=passed, gain_percent=stats,
                criteria={'blocks':10, 'abs_median_max':.5, 'iqr_max':1, 'min':-2, 'max':2})


def validate_binding(p):
    """Reject unregistered parameters and incomplete evidence before any engine starts."""
    expected = {'schema':1, 'required_blocks_per_phase':10, 'attempts_per_phase':80,
                'deadline_seconds':3600, 'threads':1, 'hash_mib':16, 'depth':20,
                'expected_nodes':NODES, 'engine_cpu':2, 'controller_cpu':3,
                'pre_sample_seconds':3, 'pre_busy_max_exclusive':20,
                'cpu_wall_min_inclusive':.95, 'sibling_busy_max_exclusive':30,
                'calibration_abs_median_max':.5, 'calibration_iqr_max':1,
                'calibration_min':-2, 'calibration_max':2, 'advisory_gain_min':1}
    for key, value in expected.items():
        if type(p.get(key)) is not type(value) or p[key] != value:
            raise ValueError('protocol parameter differs: ' + key)
    if p.get('classification') != 'UNPROVEN' or p.get('network_sha256') is None:
        raise ValueError('classification/network binding absent')
    commit = p.get('source_commit', '')
    if len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit.lower()):
        raise ValueError('full source commit required')
    inputs = p.get('inputs', [])
    if len({r['role'] for r in inputs}) != len(inputs):
        raise ValueError('duplicate input role')
    by_role = {r['role']:r for r in inputs}
    required = {'baseline_binary','candidate_binary','source_manifest','network',
                'compiler','original_kit','corpus','adapter','uci_adapter','arithmetic','host_topology'}
    if not required <= by_role.keys():
        raise ValueError('missing immutable input role')
    for role, ref in by_role.items():
        path = pathlib.Path(ref['path'])
        digest = ref['sha256']
        if (not path.is_absolute() or len(digest) != 64 or
                any(c not in '0123456789abcdef' for c in digest.lower()) or sha(path) != digest.lower()):
            raise ValueError('input hash mismatch: ' + role)
    if by_role['baseline_binary']['sha256'].lower() != LOCK:
        raise ValueError('baseline is not FD3A5190')
    if by_role['compiler']['sha256'].lower() != '08c11faa4f15a460af8d90a2fd90f658658938c94051bde8babfbecce3304c6c':
        raise ValueError('compiler identity differs from both native kit builds')
    # The D: compiler is an identity copy, not a relocated runnable toolchain.
    topology_ref = by_role['host_topology']
    topology_bytes = pathlib.Path(topology_ref['path']).read_bytes()
    if hashlib.sha256(topology_bytes).hexdigest() != topology_ref['sha256'].lower():
        raise ValueError('topology changed while reading')
    topology = json.loads(topology_bytes.decode('utf-8-sig'))
    cores = topology.get('physical_cores', [])
    if not any(core.get('group') == 0 and core.get('logical_cpus') == [2,3] for core in cores):
        raise ValueError('CPU2/3 not recorded as one physical core in group0')
    if by_role['network']['sha256'].lower() != p['network_sha256'].lower():
        raise ValueError('network identity differs')
    if by_role['corpus']['sha256'].lower() != 'c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265':
        raise ValueError('wrong fens12k')
    required_proof = {'build_pair','off_on_pins','perft','t1_smoke','asan_ubsan','raw_bit_parity','weight_negative_control'}
    prereqs = p.get('prerequisites', {})
    if set(prereqs) != required_proof:
        raise ValueError('prerequisite set differs')
    candidate_hash = by_role['candidate_binary']['sha256'].lower()
    for name, receipt in prereqs.items():
        if (receipt.get('status') != 'PASS' or receipt.get('evidence_scope') != 'native'
                or receipt.get('candidate_sha256', '').lower() != candidate_hash):
            raise ValueError('native candidate prerequisite missing: ' + name)
        if sha(receipt['path']) != receipt['sha256'].lower():
            raise ValueError('changed prerequisite: ' + name)
    return by_role

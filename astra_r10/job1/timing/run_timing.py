"""Execute the preregistered R10 10 A/A then 10 ABBA experiment.

UNPROVEN: no Elo claim. Run only after native prerequisites and independent review.
"""
import argparse
import datetime
import json
import math
import pathlib
import platform
import re
import sys
import time
sys.path.insert(0, 'D:/a10/pydeps')
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import psutil
from lane_guard import check_lane  # CR crfix abcbb9c9
from math_checks import NODES, block_ratio, calibration, protocol_snapshot, sha, summary, validate_binding
from uci_adapter import Engine


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def append(path, data):
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(data, allow_nan=False) + '\n')
        stream.flush()


def busy_fraction(before, after):
    # Windows system includes interrupt and DPC: do not add them twice.
    total = sum(getattr(after, key)-getattr(before, key) for key in ('user','system','idle'))
    if total <= 0:
        raise RuntimeError('unreadable CPU telemetry interval')
    busy = 100 * (1 - (after.idle-before.idle)/total)
    if not math.isfinite(busy) or not 0 <= busy <= 100:
        raise RuntimeError('invalid CPU telemetry')
    return busy


def remaining(deadline):
    left = deadline-time.monotonic()
    if left <= 0:
        raise TimeoutError('60-minute experiment deadline')
    return min(300, left)


def parse_bench(line):
    match = re.search(r'^info string bench depth 20 nodes (\d+) time (\d+) nps (\d+)', line)
    if match is None:
        # Forge's exact checked output may omit the UCI info prefix.
        match = re.search(r'^bench depth 20 nodes (\d+) time (\d+) nps (\d+)', line)
    if match is None or int(match[1]) != NODES:
        raise ValueError('invalid d20 bench line: ' + line)
    return {'nodes':int(match[1]), 'engine_ms':int(match[2]), 'engine_nps':int(match[3])}


def run_arm(ref, phase, attempt, slot, label, load, out, deadline, protocol_hash, network_hash):
    exe = pathlib.Path(ref['path'])
    on = phase == 'ABBA' and label == 'B'
    row = {'phase':phase, 'attempt':attempt, 'slot':slot, 'arm':label, 'status':'RUNNING',
           'exe':str(exe), 'sha256':ref['sha256'], 'protocol_sha256':protocol_hash,
           'network_sha256':network_hash, 'utc_start':utc(), 'pre_core_busy_percent':load[2:4],
           'options':{'Threads':1,'Hash':16,'OwnBook':False,'NNUEWideOutput':on}}
    e = None
    stem = f'{phase}-{attempt:02d}-{slot}-{label}'
    try:
        if sha(exe) != ref['sha256'].lower():
            raise ValueError('binary changed before arm')
        e = Engine(exe, out/(stem+'.log'), on=on, timeout=min(30, remaining(deadline)))
        proc = psutil.Process(e.p.pid)
        row.update(pid=e.p.pid, actual_affinity=proc.cpu_affinity(),
                   actual_priority=int(proc.nice()), os_thread_count=proc.num_threads(),
                   uci_threads_default_verified=True, requested_search_threads=1)
        e.send('bench 20')
        warm = e.wait(r'bench depth 20 nodes ', remaining(deadline))[-1]
        row['warmup'] = parse_bench(warm)
        cb = proc.cpu_times(); sb = psutil.cpu_times(percpu=True)
        begin = time.perf_counter_ns()
        e.send('bench 20')
        line = e.wait(r'bench depth 20 nodes ', remaining(deadline))[-1]
        end = time.perf_counter_ns()
        ca = proc.cpu_times(); sa = psutil.cpu_times(percpu=True)
        row.update(parse_bench(line))
        wall = (end-begin)/1e9
        ratio = (ca.user+ca.system-cb.user-cb.system)/wall
        sibling = busy_fraction(sb[3], sa[3])
        if not math.isfinite(ratio) or ratio < 0:
            raise RuntimeError('invalid process CPU telemetry')
        row.update(monotonic_start_ns=begin, monotonic_end_ns=end, wall_seconds=wall,
                   wall_nps=NODES/wall, engine_cpu_wall_ratio=ratio,
                   sibling_busy_percent=sibling, after_affinity=proc.cpu_affinity(),
                   after_priority=int(proc.nice()))
        if row['actual_affinity'] != [2] or row['after_affinity'] != [2] or proc.nice() != psutil.IDLE_PRIORITY_CLASS:
            raise RuntimeError('engine scheduling drift')
        row['contamination_reasons'] = []
        if ratio < .95:
            row['contamination_reasons'].append('engine_cpu_wall_below_0.95')
        if sibling >= 30:
            row['contamination_reasons'].append('sibling_busy_at_least_30_percent')
        e.close()
        row['exit_code'] = e.p.returncode
        e = None
        row['sha256_after_exit'] = sha(exe)
        if row['sha256_after_exit'] != ref['sha256'].lower():
            raise ValueError('binary changed during arm')
        row['status'] = 'PASS'
    except BaseException as error:
        row['status'] = 'FAIL'; row['error'] = repr(error)
    finally:
        if e is not None:
            try:
                e.abort()
                row['exit_code'] = e.p.returncode if e.p is not None else None
            except BaseException as error:
                row['cleanup_error'] = repr(error)
        row['utc_end'] = utc()
        transcript = out/(stem+'.log')
        if transcript.exists():
            row['transcript_sha256'] = sha(transcript)
        append(out/'runs.jsonl', row)
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--threads', type=int, choices=[1], required=True)
    ap.add_argument('--protocol', type=pathlib.Path, required=True)
    ap.add_argument('--out', type=pathlib.Path, required=True)
    args = ap.parse_args()
    protocol_bytes, protocol, protocol_hash = protocol_snapshot(args.protocol)
    inputs = validate_binding(protocol)
    if inputs['adapter']['sha256'].lower() != sha(__file__):
        raise ValueError('registered adapter differs from executing file')
    if inputs['uci_adapter']['sha256'].lower() != sha(pathlib.Path(__file__).with_name('uci_adapter.py')):
        raise ValueError('registered UCI adapter differs')
    if inputs['arithmetic']['sha256'].lower() != sha(pathlib.Path(__file__).with_name('math_checks.py')):
        raise ValueError('registered arithmetic differs')
    if inputs['lane_guard']['sha256'].lower() != sha(pathlib.Path(__file__).resolve().parent.parent/'lane_guard.py'):
        raise ValueError('registered lane guard differs')
    me = psutil.Process()
    if me.nice() != psutil.IDLE_PRIORITY_CLASS or not set(me.cpu_affinity()) <= {2,3}:
        raise RuntimeError('launch through reviewed safe manifest at Idle on CPUs2/3')
    me.cpu_affinity([3])
    lane = check_lane(me)  # CR crfix: tmfit lane / foreign CPU2-3 pin / 8 GiB RAM before any engine
    args.out.mkdir(parents=True, exist_ok=False)
    append(args.out/'lane_checks.jsonl', dict(lane, utc=utc(), when='start'))
    (args.out/'PROTOCOL.json').write_bytes(protocol_bytes)
    result = {'classification':'UNPROVEN', 'evidence_scope':'native', 'status':'RUNNING',
              'protocol_sha256':protocol_hash, 'platform':platform.platform(), 'start_utc':utc(),
              'controller_priority':int(me.nice()), 'controller_affinity':me.cpu_affinity(),
              'blocks':[], 'phase_summaries':{}, 'advisory_threshold_met':False}
    deadline = time.monotonic()+3600
    try:
        for phase in ('AA','ABBA'):
            selected = []
            all_complete = []
            for attempt in range(80):
                if len(selected) == 10:
                    break
                while True:
                    remaining(deadline)
                    load = psutil.cpu_percent(interval=min(3, remaining(deadline)), percpu=True)
                    if len(load) < 4 or any(not math.isfinite(x) for x in load[2:4]):
                        raise RuntimeError('pre-core telemetry unavailable')
                    append(args.out/'waits.jsonl', {'utc':utc(),'phase':phase,'attempt':attempt,'load':load[2:4]})
                    append(args.out/'lane_checks.jsonl', dict(check_lane(me), utc=utc(), phase=phase, attempt=attempt))
                    if load[2] < 20 and load[3] < 20:
                        break
                    time.sleep(min(15, remaining(deadline)))
                block = {'phase':phase,'attempt':attempt,'status':'RUNNING','eligible':False,
                         'pre_core_busy_percent':load[2:4], 'rows':[]}
                try:
                    for slot, label in enumerate('ABBA'):
                        remaining(deadline)
                        ref = inputs['baseline_binary'] if phase == 'AA' or label == 'A' else inputs['candidate_binary']
                        row = run_arm(ref, phase, attempt, slot, label, load, args.out, deadline,
                                      protocol_hash, protocol['network_sha256'])
                        block['rows'].append(row)
                        if row['status'] != 'PASS':
                            raise RuntimeError('failed arm retained; stop experiment')
                    block['ratio'] = block_ratio(block['rows'])
                    block['gain_percent'] = 100*(block['ratio']-1)
                    block['eligible'] = all(not row['contamination_reasons'] for row in block['rows'])
                    block['status'] = 'COMPLETE'
                    all_complete.append(block['gain_percent'])
                    if block['eligible']:
                        selected.append(block['gain_percent'])
                except BaseException as error:
                    block['status'] = 'INCOMPLETE'; block['error'] = repr(error)
                    raise
                finally:
                    result['blocks'].append(block)
                    append(args.out/'blocks.jsonl', block)
                print(phase, 'eligible', len(selected), '/10 attempts', attempt+1, flush=True)
            result['phase_summaries'][phase] = {'eligible_gain_percent':summary(selected),
                                               'all_complete_gain_percent':summary(all_complete)}
            if len(selected) != 10:
                raise RuntimeError('insufficient eligible complete blocks within 80 attempts')
            if phase == 'AA':
                result['calibration'] = calibration(selected)
                if not result['calibration']['passed']:
                    result['status'] = 'CALIBRATION_FAIL'
                    break
            else:
                result['advisory_threshold_met'] = summary(selected)['median'] >= 1
                result['status'] = 'ADVISORY_THRESHOLD_MET' if result['advisory_threshold_met'] else 'BELOW_THRESHOLD'
        validate_binding(protocol)
        if sha(args.protocol) != protocol_hash:
            raise ValueError('protocol changed during experiment')
    except BaseException as error:
        result['status'] = 'INCOMPLETE'; result['error'] = repr(error)
        result['advisory_threshold_met'] = False
    finally:
        # Retain useful dispersion and rejection counts even if the deadline or an
        # invalid arm ended a phase before its ten-block collection target.
        for phase in ('AA','ABBA'):
            blocks = [b for b in result['blocks'] if b['phase'] == phase]
            complete = [b for b in blocks if b['status'] == 'COMPLETE']
            result['phase_summaries'][phase] = {
                'attempted_blocks':len(blocks), 'complete_blocks':len(complete),
                'eligible_blocks':sum(b['eligible'] for b in complete),
                'eligible_gain_percent':summary([b['gain_percent'] for b in complete if b['eligible']]),
                'all_complete_gain_percent':summary([b['gain_percent'] for b in complete])}
        result['finish_utc'] = utc()
        (args.out/'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
        print(json.dumps({key:value for key,value in result.items() if key != 'blocks'}, indent=2), flush=True)
    return 0 if result['status'] in ('ADVISORY_THRESHOLD_MET','BELOW_THRESHOLD') else 1


if __name__ == '__main__':
    sys.exit(main())

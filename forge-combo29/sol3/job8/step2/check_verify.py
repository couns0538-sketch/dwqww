import json
from pathlib import Path
import re
import sys

arm, out, driver_exit = sys.argv[1:]
out = Path(out)
engine = json.loads((out / 'observed.engine_status.json').read_text(encoding='ascii'))
stream = (out / 'observed.engine.stdout.txt').read_text(encoding='ascii').splitlines()
raw_failures = [line for line in stream if 'V3 VERIFY FAILED' in line]
active = [line for line in stream if line.startswith('info string NNUE v3 active: ')]
expected_keys = dict(searches=8612, total_nodes=29333343, trace_fnv1a64='5c705841c3ea17b4',
                     terminal=42, final_sum=35918624, at_cap=971, final_fnv1a64='5356dbb3a5f1bee3')
if active != engine['active_net'] or len(active) != 1 or not re.search(
        r'\bhidden 768\b.*\bchecksum 30ab43b4ba5db5f3\b.*\bkernel avx512\b', active[0]):
    raise ValueError(f'{arm}: wrong active evaluator {active!r}')
if raw_failures != [detail['line'] for detail in engine['failures']] or len(raw_failures) != engine['failure_count']:
    raise ValueError(f'{arm}: observer mismatch with raw UCI')
print(f'{arm} driver_exit={driver_exit} engine_exit={engine["engine_exit"]} failure_lines={len(raw_failures)}')
print(active[0])
if arm == 'verify':
    if driver_exit != '0' or engine['engine_exit'] != 0 or raw_failures:
        raise ValueError(f'{arm}: expected zero failures and exit 0')
    for file in ('summary.json', 'readback.json'):
        found = json.loads((out / file).read_text())
        fields = {key: found[key] for key in expected_keys}
        print(file, fields)
        if fields != expected_keys:
            raise ValueError(f'{arm}: known answer changed')
    if json.loads((out / 'first_difference.json').read_text()) is not None:
        raise ValueError('First differing rows are in first_difference.json')
else:
    if driver_exit != '3' or engine['engine_exit'] != 3 or len(raw_failures) != 1:
        raise ValueError(f'{arm}: sensitivity not shown, expected one mismatch and exit 3')
    failed = engine['failures'][0]
    match = re.fullmatch(r'info string V3 VERIFY FAILED at ply (\d+): search path (-?\d+), reference (-?\d+), fen (.+)', failed['line'])
    if not match or match[2] == match[3] or len(match[4].split()) != 6:
        raise ValueError(f'{arm}: invalid mismatch line {failed["line"]!r}')
    if (failed['phase'] not in ('warm-up', 'workload') or
            failed['position'].split()[:3] != ['position', 'startpos', 'moves'] or
            len(failed['position'].split()) - 3 != failed['game_ply']):
        raise ValueError(f'{arm}: missing driver root coordinate {failed!r}')
    if failed['phase'] == 'warm-up' and (failed['game'], failed['game_ply']) != (0, 8):
        raise ValueError(f'{arm}: wrong warm-up coordinates {failed!r}')
    if failed['phase'] == 'workload':
        trace = (out / 'trace.jsonl').read_text().splitlines()
        if trace:
            previous = json.loads(trace[-1])
            if (failed['game'], failed['game_ply']) <= (previous['game'], previous['ply']):
                raise ValueError(f'{arm}: failed root was already recorded as completed')
    print(f'{arm} {failed["phase"]} game={failed["game"]} game_ply={failed["game_ply"]} evaluation_ply={match[1]}')
    print(failed['position'])
    print(failed['line'])

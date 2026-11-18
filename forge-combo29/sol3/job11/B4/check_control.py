import json
from pathlib import Path
import re
import sys

arm, destination, driver_exit = sys.argv[1:]
output = Path(destination)
engine = json.loads((output / 'observed.engine_status.json').read_text(encoding='ascii'))
raw = [line for line in (output / 'observed.engine.stdout.txt').read_text(encoding='ascii').splitlines()
       if 'REP VERIFY FAILED' in line]
if raw != [detail['line'] for detail in engine['failures']] or len(raw) != engine['failure_count']:
    raise ValueError('Observer failure count disagrees with raw output')
if len(engine['active_net']) != 1 or not re.search(r'\bchecksum 30ab43b4ba5db5f3\b.*\bkernel avx512\b',
                                                   engine['active_net'][0]):
    raise ValueError('Wrong active evaluator')
print(f'{arm} driver_exit={driver_exit} engine_exit={engine["engine_exit"]} failure_count={len(raw)}')
if driver_exit == '0' and engine['engine_exit'] == 0 and not raw:
    print('The check did not stop on this path.')
    raise SystemExit(4)
if driver_exit != '3' or engine['engine_exit'] != 3 or len(raw) != 1:
    raise ValueError('Expected exact child exit 3 following one mismatch line')
failure = engine['failures'][0]
details = re.fullmatch(r'info string REP VERIFY FAILED reason=(scan|prefilter) old=([01]) new=([01]) '
                       r'search_ply=(\d+) root_history_index=(\d+) fen=(.+)', failure['line'])
if not details or details[2] == details[3] or len(details[6].split()) != 6:
    raise ValueError(f'Malformed mismatch line: {failure["line"]!r}')
if (failure['phase'] not in ('warm-up', 'workload') or
        failure['position'].split()[:3] != ['position', 'startpos', 'moves'] or
        len(failure['position'].split()) - 3 != failure['game_ply']):
    raise ValueError(f'Missing workload coordinate: {failure!r}')
if failure['phase'] == 'warm-up' and (failure['game'], failure['game_ply']) != (0, 8):
    raise ValueError(f'Invalid opening warm-up coordinate: {failure!r}')
print(f'{arm} {failure["phase"]} game={failure["game"]} game_ply={failure["game_ply"]} '
      f'internal_ply={details[4]} old={details[2]} new={details[3]}')
print(failure['position'])
print(failure['line'])

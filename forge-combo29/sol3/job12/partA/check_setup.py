import json
from pathlib import Path
import re
import sys

out, size = Path(sys.argv[1]), sys.argv[2]
state = json.loads((out / 'observed.engine_status.json').read_text())
expected = f'setoption name Hash value {size}'
commands = state['setup_commands']
given = [item for item in commands if item.startswith('setoption name Hash value ')]
if state['engine_exit'] or state['failure_count'] or given != [expected]:
    raise ValueError(f'Engine exit, warning or requested Hash differs: {state!r}')
if len(state['active_net']) != 1 or not re.search(r'\bchecksum 30ab43b4ba5db5f3\b', state['active_net'][0]):
    raise ValueError(f'Wrong active net: {state["active_net"]!r}')
print(expected)
print(state['active_net'][0])

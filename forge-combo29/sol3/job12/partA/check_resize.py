import json
from pathlib import Path
import sys

p = Path(sys.argv[1])
actual = [json.loads(line) for line in p.read_text().splitlines()]
expected = [{"game": 30, "hash_before": 16, "hash_after": 4,
             "sent": ["setoption name Hash value 4", "isready"], "received": "readyok"}]
if actual != expected:
    raise ValueError(f'Unexpected resize receipt: {actual!r}')
print(json.dumps(actual[0]))

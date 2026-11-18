import json
from pathlib import Path
import sys

p = Path(sys.argv[1])
expected = int(sys.argv[2])
summary = json.loads(p.read_text())
values = tuple(summary[key] for key in ('rows', 'equal_search_labels', 'equal_counter_rows'))
print(*values)
if values != (expected, expected, expected):
    raise ValueError(f'Check {p} for first label or counter mismatch')

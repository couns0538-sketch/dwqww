"""Fault injection: optimized Python must never approve a corrupted outcome codec."""
import json
from pathlib import Path
import sys

HERE = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
sys.path.insert(0, str(HERE))
import chess
import audit
from filter_positions import low_priority

low_priority()
root = Path(sys.argv[1])
root.mkdir()
audit.read_records = lambda *args: iter([
    {'fen': chess.STARTING_FEN.replace(' w ', f' {turn} ')}
    for turn in ('w', 'b') for _ in range(125)
])
# Deliberately lie about every encoded W/D result. The literal oracle must catch it.
audit.encode_result = lambda *args: (1, 0, 1)
try:
    outcome = audit.orientation(root)
except (AssertionError, ValueError, RuntimeError) as error:
    print(json.dumps({'status': 'REJECTED', 'optimize': sys.flags.optimize,
                      'exception': type(error).__name__, 'message': str(error)}))
else:
    print(json.dumps({'status': 'FALSE_PASS', 'optimize': sys.flags.optimize,
                      'outcome': outcome}))

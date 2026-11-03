"""Bounded read-only repro of Python versus lock FEN text admission."""
import json
from pathlib import Path
import subprocess
import sys

HERE = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
sys.path.insert(0, str(HERE))
from filter_positions import low_priority, sha256
from records import record
from native_forge_smoke import ENGINE, LOCK
from resource_policy import storage_guard

low_priority()
root = Path(__file__).parent / 'fen_text_probe'
storage_guard(root, allowance=1024*1024)
root.mkdir()
assert sha256(ENGINE) == LOCK
fen = '8/8/8/8/8/6k1/8/K7 w - - 0 1'
cases = {'space': fen, 'nbsp': fen.replace(' w ', '\u00a0w '),
         'unit_separator': fen.replace(' w ', '\x1fw '),
         'unicode_clock': fen[:-1] + '\u0661'}
observed = {}
for name, text in cases.items():
    try:
        row = record(text, 20, 'cp', 1, 'fixture', 1, 'selfplay')
        accepted = True
    except ValueError:
        accepted = False
    commands = '\n'.join(['uci', 'setoption name Threads value 1',
        'setoption name Hash value 16', 'setoption name OwnBook value false',
        'isready', 'position startpos', 'position fen ' + text,
        'go perft 1', 'quit']) + '\n'
    (root / (name + '.stdin.txt')).write_text(commands, encoding='utf-8')
    reply = subprocess.run([str(ENGINE)], input=commands.encode('utf-8'),
        capture_output=True, cwd=root, timeout=15,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    (root / (name + '.stdout.log')).write_bytes(reply.stdout)
    (root / (name + '.stderr.log')).write_bytes(reply.stderr)
    observed[name] = {'admitted': accepted, 'returncode': reply.returncode,
                      'fen': text, 'tail': reply.stdout.decode('utf-8', errors='replace').splitlines()[-8:]}
assert sha256(ENGINE) == LOCK
(root / 'report.json').write_text(json.dumps(observed, indent=2), encoding='utf-8')
print(json.dumps(observed))

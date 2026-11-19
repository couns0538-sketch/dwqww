"""Feed fixed UCI reply streams into the exact job 20 runner without a chess engine."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
here=Path(__file__).resolve().parent
runner=Path('/workspace/work/j20match/selfplay.py')
spec=importlib.util.spec_from_file_location('driver_under_test',runner)
driver=importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
class Mock:
    pid=1
    def __init__(self, text):
        self.stdin=io.StringIO()
        self.stdout=io.StringIO(text)
cases=json.loads((here/'label-fixtures.json').read_text())
proc=Mock(''.join('\r\n'.join(c['stream'])+'\r\n' for c in cases))
print('Runner SHA-256',hashlib.sha256(runner.read_bytes()).hexdigest())
for case in cases:
    position='position startpos moves c2c4'
    go='go softnodes 2000'
    best,chosen,reply=driver.search(proc,position,go)
    actual=driver.normalize_depth(chosen) if chosen is not None else 'NA'
    assert (best,actual)==(case['bestmove'],case['label']),case
    assert reply==case['stream']
    print(f'PASS {case["name"]}\n  record label {actual}')
assert proc.stdin.getvalue()==(position+'\n'+go+'\n')*len(cases)
print(f'{len(cases)} fixed synthetic streams passed, with three archived raw depth lines. Consecutive calls on one mock process verified per-search state reset. No game or engine process was started.')

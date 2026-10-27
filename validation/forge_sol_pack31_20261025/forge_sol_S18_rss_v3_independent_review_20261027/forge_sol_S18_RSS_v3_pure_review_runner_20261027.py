"""Run only existing pure/dry S18 tests, refusing heavy imports/processes/signals."""
import importlib.abc
import json
from pathlib import Path
import sys
import time
import unittest

if not __debug__:
    raise RuntimeError('Run without -O/PYTHONOPTIMIZE')
sys.dont_write_bytecode=True
ROOT=Path('/tmp/forge_sol_S18_rss_scope_v3_checkpoint_20261027/prep')
OUT=Path(__file__).resolve().parent
attempts=[]
class BlockHeavyImports(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'torch','numpy'}:
            attempts.append(fullname)
            raise RuntimeError('Pure review forbids import: '+fullname)
def audit(event,args):
    if event in {'subprocess.Popen','os.system','os.posix_spawn','os.fork','os.kill','os.killpg'}:
        attempts.append(event)
        raise RuntimeError('Pure review forbids process/signal event: '+event)
sys.meta_path.insert(0,BlockHeavyImports())
sys.addaudithook(audit)
started=time.monotonic()
suite=unittest.TestLoader().discover(str(ROOT),pattern='test_forge_sol_S18*_20261027.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
summary={'status':'PASS' if result.wasSuccessful() and result.testsRun==44 and not attempts else 'FAIL',
         'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
         'elapsed_seconds':time.monotonic()-started,'blocked_attempts':attempts,
         'Torch_imported':'torch' in sys.modules,'NumPy_imported':'numpy' in sys.modules,
         'scope':'Existing44 pure/dry tests only; heavy imports, real subprocesses and kernel signals forbidden.'}
with (OUT/'forge_sol_S18_RSS_v3_independent_pure_result_20261027.json').open('x') as stream:
    json.dump(summary,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps(summary,sort_keys=True))
raise SystemExit(0 if summary['status']=='PASS' else 1)

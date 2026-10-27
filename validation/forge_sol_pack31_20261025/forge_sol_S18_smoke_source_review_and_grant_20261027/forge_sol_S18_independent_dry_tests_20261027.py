"""Existing S18 pure/dry suite with an explicit Torch/NumPy import blocker."""
from pathlib import Path
import hashlib,importlib.abc,json,sys,unittest
ROOT=Path('/tmp/forge_sol_S18_TRAIN_SMOKE_V2_PREP_20261026')
OUT=Path(__file__).resolve().parent
assert 'torch' not in sys.modules and 'numpy' not in sys.modules
attempts=[]
class NoTrainingImports(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in ('torch','numpy'):
            attempts.append(fullname)
            raise RuntimeError('Independent SOURCE ONLY review forbids training import: '+fullname)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={p.name:sha(p) for p in ROOT.iterdir() if p.is_file()}
sys.meta_path.insert(0,NoTrainingImports())
suite=unittest.defaultTestLoader.discover(str(ROOT),pattern='test*.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
after={p.name:sha(p) for p in ROOT.iterdir() if p.is_file()}
record={'status':'PASS_PURE_DRY_INDEPENDENT' if result.wasSuccessful() and before==after and not attempts and 'torch' not in sys.modules and 'numpy' not in sys.modules else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'Torch_NumPy_import_attempts':attempts,'Torch_imported':'torch' in sys.modules,'NumPy_imported':'numpy' in sys.modules,'original_prep_files_unchanged':before==after,'original_prep_SHA256':before,'scope':'Existing pure/dry tests only. Process/kernel calls fully mocked by original contract fixtures; no trainer, checkpoint model, native engine, compiler or Git action.'}
(OUT/'forge_sol_S18_independent_dry_test_result_20261027.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='original_prep_SHA256'},sort_keys=True))
raise SystemExit(0 if record['status'].startswith('PASS') else 1)

"""Run unchanged source/export assertions using the local pinned v3b input.

The original metadata records historical paths. An audit hook forbids reads from
those workspaces, so a successful run proves tests use only the supplied packet
plus Python/NumPy. No Torch, engine or training process is started.
"""
from pathlib import Path
import hashlib,importlib.util,sys,unittest

ROOT=Path(__file__).resolve().parent
LEGACY=ROOT/'forge_sol_S09_original_v3b_dependency_20261026.py'
LEGACY_SHA='5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f'
TEST=ROOT/'forge_sol_S09_tests_20261026.py'
TEST_SHA='f9c6256aef03bd3eb7dd67b4c3143d4f564a362016b844874435c13be90247ed'

def main():
    sys.dont_write_bytecode=True
    if hashlib.sha256(LEGACY.read_bytes()).hexdigest()!=LEGACY_SHA or hashlib.sha256(TEST.read_bytes()).hexdigest()!=TEST_SHA:
        raise ValueError('original legacy input or test assertions changed')
    denied=('/workspace/forge-pack24-20261025/','/workspace/forge-pack24-20261026/S09/')
    def hook(event,args):
        if event=='open' and args and isinstance(args[0],(str,bytes)):
            name=args[0].decode() if isinstance(args[0],bytes) else args[0]
            if any(name.startswith(prefix) for prefix in denied):raise PermissionError('portable test forbids original-workspace input: '+name)
    sys.addaudithook(hook)
    spec=importlib.util.spec_from_file_location('forge_s09_original_assertions',TEST)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.BASE=LEGACY
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    return 0 if result.wasSuccessful() and result.testsRun==15 else 1

if __name__=='__main__':raise SystemExit(main())

"""Use only the retained official pip wheel, without installing global tooling."""
import runpy
import sys
sys.path.insert(0, 'D:/a10/job3/runtime312/bootstrap_packages')
runpy.run_module('pip', run_name='__main__')

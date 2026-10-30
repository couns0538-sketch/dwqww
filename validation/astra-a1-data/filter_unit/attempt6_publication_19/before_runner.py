import importlib.util,sys,unittest
from pathlib import Path
root=Path.cwd()
sys.path.insert(0,str(root/'tools/data'))
spec=importlib.util.spec_from_file_location('filter_positions',root/'validation/astra-a1-data/filter_full10m_v2_protocol/filter_positions.py')
module=importlib.util.module_from_spec(spec);sys.modules['filter_positions']=module;spec.loader.exec_module(module)
spec=importlib.util.spec_from_file_location('filter_regression',root/'tests/data/test_filter_positions.py')
test=importlib.util.module_from_spec(spec);sys.modules['filter_regression']=test;spec.loader.exec_module(test)
suite=unittest.TestSuite([test.IntegrationTests('test_manifest_write_failure_does_not_publish_sealed_summary')])
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())

"""Opus 30-h job: unit check of tune_spsa.disk_low() (the C: / D: floor stop) - real floors, then forced floors."""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('tune_spsa', r'D:\o30\wt\opus_30h\b\tune_spsa.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
real = m.disk_low()
print('floors', m.DISK_FLOORS_GB, '-> real:', repr(real))
m.DISK_FLOORS_GB = {'D:\\': 9999.0, 'Q:\\': 1.0}
forced = m.disk_low()
print('forced D: 9999 + missing Q: ->', repr(forced))
ok = real == '' and forced.startswith('D:\\ ') and 'Q:' not in forced
print('DISK FLOOR CHECK', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)

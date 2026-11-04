"""Opus 30-h job: render make_net_index.py on two fake net folders (with and without offline_rule) in a new temp root."""
import json
import os
import subprocess
import sys
import time

root = r'D:\o30\tmp\idxtest_' + time.strftime('%H%M%S')
base = {'net': r'D:\o30\nets\x\x.nnue2', 'sha256': '0' * 64, 'md5': '0' * 32, 'exe': r'D:\o30\w\e.exe', 'exe_sha256': '1' * 64,
        'gate_option': r'EvalFileV2=D:\o30\nets\x\x.nnue2', 'bench_on': 'd11=1,d13=2,d16=3',
        'info': 'x.nnue2: king buckets 4 output buckets 8 hidden 256 unmirrored residual',
        'parity': ['avx2 -> PASS', 'sse -> PASS', 'scalar -> PASS', 'planted bug caught', 'PARITY PASS'],
        'score_s16': {'mse_b0.6': 0.0142549, 'mse_b1.0': 0.0045432}, 'score_jobA_val': {'mse_b0.6': 0.0133007},
        'pins_off': 'PASS', 'pins_on': 'ON', 'all_checks_passed': True}
for name, rule in (('a_with_rule', {'s16_b06_diff': -5.5e-5, 's16_z': -30.1, 'jobA_b06_diff': 2.9e-5, 'jobA_z': 1.4,
                                    'pass': True}),
                   ('b_no_rule', None), ('c_zero_se', {'s16_b06_diff': 0.0, 's16_z': None, 'jobA_b06_diff': 0.0,
                                                       'jobA_z': None, 'pass': False})):
    d = os.path.join(root, name)
    os.makedirs(d)
    rec = dict(base)
    if rule:
        rec['offline_rule'] = rule
    with open(os.path.join(d, 'RESULT.json'), 'x') as f:
        json.dump(rec, f)
py = sys.executable
rc = subprocess.call([py, '-I', '-B', r'D:\o30\wt\opus_30h\a\make_net_index.py', '--root', root])
text = open(os.path.join(root, 'INDEX.md'), encoding='utf-8').read()
print(text)
ok = rc == 0 and '| a_with_rule | -5.50e-05 (-30.10) | +2.90e-05 (+1.40) | PASS |' in text and 'not recorded' in text \
    and '(n/a)' in text and text.count('## ') == 3
print('INDEX RENDER', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)

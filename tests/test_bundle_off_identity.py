"""A3: fail-closed checks of the actual shell entry point with tiny fake executables."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).with_name('bundle_off_identity.sh')

class OffIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='forge-off-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)

    def engine(self, name, delta=0, mode='ok', advertisement=None):
        if advertisement is None:
            advertisement = ['option name Feature type check default false']
        p = self.root / name
        p.write_text('#!' + sys.executable + '\n' + f'''import re,sys,time
s=sys.stdin.read()
if {mode!r} == 'hang': time.sleep(5)
if {mode!r} == 'nonzero': sys.exit(7)
print('option name Hash type spin default 16 min 1 max 2048')
print('option name Threads type spin default 1 min 1 max 256')
print('option name OwnBook type check default true')
for line in {advertisement!r}: print(line)
print('uciok', flush=True)
if {mode!r} != 'no_ready': print('readyok', flush=True)
if {mode!r} == 'binary': sys.stdout.buffer.write(b'info string raw \\xff\\r\\n'); sys.stdout.flush()
d=int(re.search(r'bench (\\d+)', s)[1])
if {mode!r} != 'missing': print(f'info string bench depth {{d}} nodes {{100+d+{delta}}} time 1 nps 1')
if {mode!r} == 'malformed_extra': print('info string bench depth bogus nodes missing')
if {mode!r} == 'duplicate': print(f'info string bench depth {{d}} nodes {{100+d}} time 1 nps 1')
''')
        p.chmod(0o755)
        return p

    def run_check(self, base, candidate, *extra):
        return subprocess.run(['bash', str(SCRIPT), str(base), str(candidate), '--depths', '1,2',
                               '--output', str(self.root/'evidence'), *extra], text=True,
                              capture_output=True, timeout=10)

    def test_identical_and_explicit_off(self):
        r=self.run_check(self.engine('base'), self.engine('candidate'), '--off', 'Feature=false')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        result=json.loads((self.root/'evidence/summary.json').read_text())
        self.assertEqual(result['status'],'PASS')
        self.assertEqual([row['nodes'] for row in result['runs']],[101,101,102,102])
        self.assertIn('setoption name Feature value false',(self.root/'evidence/candidate-d1.stdin').read_text())

    def test_valid_spin_zero_off(self):
        r=self.run_check(self.engine('base'), self.engine('candidate', advertisement=[
            'option name Feature type spin default 0 min 0 max 5']), '--off', 'Feature=0')
        self.assertEqual(r.returncode, 0, r.stdout+r.stderr)
        self.assertIn('setoption name Feature value 0',
                      (self.root/'evidence/candidate-d1.stdin').read_text())

    def test_invalid_off_type_or_range_rejected(self):
        cases = [
            ('spin_positive_min', 'option name Feature type spin default 1 min 1 max 5', '0'),
            ('spin_negative_max', 'option name Feature type spin default -1 min -5 max -1', '0'),
            ('button', 'option name Feature type button', 'false'),
            ('check_zero', 'option name Feature type check default false', '0'),
            ('spin_false', 'option name Feature type spin default 0 min 0 max 5', 'false'),
            ('string', 'option name Feature type string default false', 'false'),
        ]
        for label, advertisement, value in cases:
            with self.subTest(case=label):
                r=self.run_check(self.engine('base-'+label), self.engine('candidate-'+label,
                    advertisement=[advertisement]), '--off', 'Feature='+value,
                    '--output', str(self.root/label))
                self.assertNotEqual(r.returncode, 0, r.stdout+r.stderr)
                self.assertNotIn('PASS: every OFF', r.stdout)

    def test_malformed_or_duplicate_advertisement_rejected(self):
        cases = [
            ['option name Feature type spin default 0 min 0'],
            ['option name Feature type check default false',
             'option name Feature type check default true'],
        ]
        for index, advertisement in enumerate(cases):
            with self.subTest(advertisement=advertisement):
                r=self.run_check(self.engine('base-'+str(index)),
                    self.engine('candidate-'+str(index), advertisement=advertisement),
                    '--off', 'Feature=false', '--output', str(self.root/('ads-'+str(index))))
                self.assertNotEqual(r.returncode, 0, r.stdout+r.stderr)
                self.assertNotIn('PASS: every OFF', r.stdout)

    def test_controlled_settings_cannot_be_overridden(self):
        for name in ('Hash', 'Threads'):
            with self.subTest(name=name):
                r=self.run_check(self.engine('base-'+name), self.engine('candidate-'+name),
                    '--off', name+'=0', '--output', str(self.root/name))
                self.assertNotEqual(r.returncode, 0, r.stdout+r.stderr)
                self.assertNotIn('PASS: every OFF', r.stdout)

    def test_node_mismatch(self):
        r=self.run_check(self.engine('base'),self.engine('candidate',delta=1))
        self.assertNotEqual(r.returncode,0)
        self.assertIn('node mismatch',r.stdout+r.stderr)

    def test_engine_failure(self):
        r=self.run_check(self.engine('base'),self.engine('candidate',mode='nonzero'))
        self.assertNotEqual(r.returncode,0)
        self.assertIn('exit 7',r.stdout+r.stderr)

    def test_missing_and_duplicate_bench(self):
        for mode in ['missing','duplicate']:
            with self.subTest(mode=mode):
                out=self.root/mode
                r=subprocess.run(['bash',str(SCRIPT),str(self.engine('base-'+mode)),str(self.engine('cand-'+mode,mode=mode)),
                                  '--depths','1','--output',str(out)],capture_output=True,text=True,timeout=10)
                self.assertNotEqual(r.returncode,0)
                self.assertIn('exactly one bench',r.stdout+r.stderr)

    def test_timeout_keeps_evidence(self):
        r=self.run_check(self.engine('base'),self.engine('candidate',mode='hang'),'--timeout','0.2')
        self.assertNotEqual(r.returncode,0)
        self.assertTrue((self.root/'evidence/candidate-d1.stderr').exists())

    def test_existing_output_not_overwritten(self):
        (self.root/'evidence').mkdir(); marker=self.root/'evidence/marker';marker.write_text('retained')
        r=self.run_check(self.engine('base'),self.engine('candidate'))
        self.assertNotEqual(r.returncode,0);self.assertEqual(marker.read_text(),'retained')

    def test_enabling_option_rejected(self):
        r=self.run_check(self.engine('base'),self.engine('candidate'),'--off','Feature=true')
        self.assertNotEqual(r.returncode,0)


    def test_readyok_required(self):
        r=self.run_check(self.engine('base'),self.engine('candidate',mode='no_ready'))
        self.assertNotEqual(r.returncode,0)
        self.assertIn('readyok',r.stdout+r.stderr)

    def test_malformed_extra_result_rejected(self):
        r=self.run_check(self.engine('base'),self.engine('candidate',mode='malformed_extra'))
        self.assertNotEqual(r.returncode,0)
        self.assertIn('exactly one bench',r.stdout+r.stderr)

    def test_original_output_bytes_preserved(self):
        r=self.run_check(self.engine('base'),self.engine('candidate',mode='binary'))
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        raw=(self.root/'evidence/candidate-d1.stdout').read_bytes()
        self.assertIn(b'raw \xff\r\n',raw)

if __name__=='__main__': unittest.main()

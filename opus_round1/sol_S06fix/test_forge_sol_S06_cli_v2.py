"""Synthetic CLI input fixtures; never reconstructed historical gate games."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).with_name('forge_sol_S06_gatelog_miner_v2.py')
RESULT = 'forge_sol_S06_result_v2.json'
CSV = '\ufeff"gate","games","W","D","L","sprt_bounds","llr","conc","status","verdict"\n"G104","698","130","497","71","[0.00, 10.00]","2.95","5","done","H1 accepted"\n'

def pgn():
    records = []
    for white, black, result in [('Candidate','Baseline','1-0'), ('Baseline','Candidate','0-1')]:
        records.append('\n'.join(f'[{k} "{v}"]' for k,v in {
            'Event':'Synthetic S06', 'Round':'1', 'White':white, 'Black':black,
            'Result':result, 'FEN':'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'Termination':'normal', 'Phase':'opening'}.items())+'\n\n1. e4 e5 '+result+'\n')
    return '\n'.join(records)

class CommandLine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root/'new_output'
    def tearDown(self):
        self.tmp.cleanup()
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(CLI), *map(str,args), '--out', str(self.out)], capture_output=True, text=True, timeout=15)
    def result(self):
        return json.loads((self.out/RESULT).read_text())
    def test_known_counts_and_new_sealed_output(self):
        r = self.run_cli('counts', '--penta', 5,121,458,154,12)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = self.result()
        self.assertAlmostEqual(data['statistics']['gaussian_llr']['value'], 2.219838109695718)
        self.assertIsNone(data['statistics']['individual_wdl'])
        self.assertFalse(data['acceptance_authorized'])
        self.assertTrue((self.out/'forge_sol_S06_SHA256SUMS_v2.txt').exists())
    def test_existing_output_never_overwritten(self):
        self.out.mkdir(); sentinel=self.out/'keep'; sentinel.write_bytes(b'preserve')
        r = self.run_cli('counts', '--penta', 1,1,1,1,1)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(sentinel.read_bytes(), b'preserve')
        self.assertNotIn('Traceback',r.stderr)
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), ['keep'])
    def test_bom_csv_and_g104_is_not_invented(self):
        src=self.root/'metadata.csv';src.write_text(CSV,encoding='utf-8')
        before=hashlib.sha256(src.read_bytes()).hexdigest()
        r=self.run_cli('triage','--csv',src)
        self.assertEqual(r.returncode,0,r.stderr)
        row=self.result()['rows'][0]
        self.assertEqual(row['gate'],'G104')
        self.assertEqual(row['wdl'],[130,497,71])
        self.assertEqual(row['reported_llr'],2.95)
        self.assertIsNone(row['pentabins'])
        self.assertFalse(row['acceptance_verified'])
        self.assertAlmostEqual(row['elo_descriptive'],29.43800853666901)
        self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),before)
    def test_duplicate_gate_rows_fail_closed_not_pool(self):
        src=self.root/'metadata.csv';src.write_text(CSV+CSV.splitlines()[1]+'\n',encoding='utf-8')
        r=self.run_cli('triage','--csv',src)
        self.assertEqual(r.returncode,1,r.stderr)
        self.assertEqual(len(self.result()['rows']),2)
        self.assertEqual(self.result()['status'],'BLOCKED')
    def test_malformed_counts_retained_with_errors(self):
        src=self.root/'metadata.csv';src.write_text(CSV.replace('"698"','"697"'),encoding='utf-8')
        r=self.run_cli('triage','--csv',src)
        self.assertEqual(r.returncode,1,r.stderr)
        self.assertEqual(self.result()['rows'][0]['status'],'BLOCKED')
    def test_pgn_synthetic_positive_input_bytes_preserved(self):
        src=self.root/'synthetic.pgn';src.write_text(pgn())
        r=self.run_cli('mine','--pgn',src,'--gate-id','SYNTHETIC','--candidate','Candidate','--baseline','Baseline')
        self.assertEqual(r.returncode,0,r.stderr)
        data=self.result()
        self.assertEqual(data['pgn']['paired']['pentabins'],[0,0,0,0,1])
        self.assertEqual(data['pgn']['raw']['W'],2)
        self.assertFalse(data['acceptance_authorized'])
        raw=self.out/data['inputs'][0]['saved_as']
        self.assertEqual(raw.read_bytes(),src.read_bytes())
    def test_conflicting_pgn_log_is_not_favorable_subset(self):
        pg=self.root/'synthetic.pgn';pg.write_text(pgn())
        log=self.root/'synthetic.log';log.write_text('Results of Candidate vs Baseline (synthetic):\nGames: 2, Wins: 0, Losses: 2, Draws: 0\nPtnml(0-2): [1,0,0,0,0]\n')
        r=self.run_cli('mine','--pgn',pg,'--log',log,'--gate-id','SYNTHETIC','--candidate','Candidate','--baseline','Baseline')
        self.assertEqual(r.returncode,1,r.stderr)
        self.assertEqual(self.result()['status'],'BLOCKED')
        self.assertTrue(self.result()['reconciliation']['issues'])
    def test_faulted_pgn_never_clean_strength(self):
        src=self.root/'faulted.pgn';src.write_text(pgn().replace('"normal"','"time forfeit"',1))
        r=self.run_cli('mine','--pgn',src,'--gate-id','SYNTHETIC','--candidate','Candidate','--baseline','Baseline')
        self.assertEqual(r.returncode,1,r.stderr)
        self.assertEqual(self.result()['pgn']['raw']['games'],2)
        self.assertEqual(self.result()['pgn']['raw']['faults']['time_loss'],1)
        self.assertFalse(self.result()['acceptance_authorized'])
    def test_no_input_clean_error(self):
        r=self.run_cli('mine','--gate-id','empty','--candidate','Candidate','--baseline','Baseline')
        self.assertNotEqual(r.returncode,0)
        self.assertNotIn('Traceback',r.stderr)
        self.assertFalse(self.out.exists())
    def test_invalid_statistical_hypothesis_clean_error(self):
        r=self.run_cli('counts','--penta',1,2,3,4,5,'--e0','nan')
        self.assertNotEqual(r.returncode,0)
        self.assertNotIn('Traceback',r.stderr)
    def test_manifest_covers_every_retained_output(self):
        r=self.run_cli('counts','--penta',1,2,3,4,5)
        self.assertEqual(r.returncode,0,r.stderr)
        manifest=self.out/'forge_sol_S06_SHA256SUMS_v2.txt'
        paths=set()
        for line in manifest.read_text().splitlines():
            digest,name=line.split('  ',1);paths.add(name)
            self.assertEqual(hashlib.sha256((self.out/name).read_bytes()).hexdigest(),digest)
        self.assertEqual(paths,{p.name for p in self.out.iterdir() if p!=manifest})

    def test_unestimable_hypothesis_not_reported_calculated_pass(self):
        r=self.run_cli('counts','--penta',1,2,3,4,5,'--e0','1e307','--e1','1e308')
        self.assertEqual(r.returncode,1,r.stderr)
        self.assertEqual(self.result()['status'],'BLOCKED')
        self.assertIsNone(self.result()['statistics']['gaussian_llr']['value'])

    def test_supplied_unrecognized_log_does_not_pass_reconciliation(self):
        pg=self.root/'synthetic.pgn';pg.write_text(pgn())
        log=self.root/'unknown.log';log.write_text('SYNTHETIC unknown producer dialect\n')
        r=self.run_cli('mine','--pgn',pg,'--log',log,'--gate-id','SYNTHETIC','--candidate','Candidate','--baseline','Baseline')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(self.result()['status'],'UNVERIFIED')
        self.assertEqual(self.result()['log']['status'],'UNVERIFIED')

if __name__=='__main__':
    unittest.main()

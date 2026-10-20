"""Numerical fixtures are synthetic; parser positives derive from actual producerbytes."""
from pathlib import Path
import copy,importlib.util,math,unittest
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];PKG=REPO/'.github/hosted-pawn-span-performance'
PATH=PKG/'analysis.py';LEGACY=not PATH.exists()
spec=importlib.util.spec_from_file_location('perf_analysis_test',REPO/'.github/hosted-nnue-performance/run_hosted.py' if LEGACY else PATH);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def parse(raw):return m.parse_bench(raw.decode('ascii') if LEGACY else raw)
def blocks(phase,n,ratio=1.,wallratio=None,drift=0.):
    wallratio=ratio if wallratio is None else wallratio;result=[]
    for i in range(n):
        order='ABBA' if i%2==0 else 'BAAB';samples=[]
        for j,variant in enumerate(order):
            scale=math.exp(drift*j);samples.append({'sample_id':f'{phase}-{i:02d}-{j}','phase':phase,'block':i,'index':j,'variant':variant,'binary_label':'baseline' if phase=='aa' or variant=='A' else 'candidate','cpu_seconds':scale*(ratio if variant=='A' else 1.),'wall_seconds':scale*(wallratio if variant=='A' else 1.)})
        result.append({'phase':phase,'block':i,'order':order,'samples':samples})
    return result
def aa(rows):return m.calibration(rows) if LEGACY else m.calibrate(rows)
def ab(rows):return m.analyze_blocks(rows)
class CanonicalParser(unittest.TestCase):
    def test_five_rows_derived_from_actual18and19_lf_and_crlf(self):
        for label in ('baseline','candidate'):
            raw=(PKG/'fixtures/historical-18-19'/(label+'-single.stdout.bin')).read_bytes()
            self.assertEqual(raw.count(b'\n'),1)
            for derived in (raw*5,raw.replace(b'\n',b'\r\n')*5):
                with self.subTest(label=label):self.assertEqual(len(parse(derived)),5)
    def test_noncanonical_count_warning_prefix_numeric_and_ending_reject(self):
        line=(PKG/'fixtures/historical-18-19/baseline-single.stdout.bin').read_bytes()
        invalid=[line*4,line*6,line*5+b'warning extra\n',(line*5).replace(b'info string ',b''),(line*5).replace(b'321912',b'321913'),line*4+line.rstrip(b'\n'),line*4+line.replace(b'\n',b'\r\n'),(line*5).replace(b'nps ',b'nps +'),(line*5).replace(b'time ',b'time 0')]
        # The last case may remain positive; forcezero timeusingcanonicalfieldreplacement.
        invalid[-1]=(line*5).replace(b'time '+line.split(b'time ')[1].split(b' ')[0],b'time 0')
        for raw in invalid:
            with self.subTest(raw=raw[:80]),self.assertRaises((ValueError,TypeError)):parse(raw)
class Analysis(unittest.TestCase):
    def test_samebaseline15blocks_pass_bothmetrics(self):self.assertTrue(aa(blocks('aa',15))['passed'])
    def test_one_bad_aa_block_stops_despite_neutralmedian(self):
        rows=blocks('aa',15);rows[7]['samples'][0]['cpu_seconds']=1.13;self.assertFalse(aa(rows)['passed'])
    def test_median_aa_bias_rejects_within_eachblocklimits(self):self.assertFalse(aa(blocks('aa',15,1.02))['passed'])
    def test_31block_twofold_speed_and_shared_bootstrap_reproducible(self):
        result=ab(blocks('ab',31,2.));self.assertEqual(result,ab(blocks('ab',31,2.)));self.assertAlmostEqual(result['cpu']['geomean'],2.);self.assertGreater(result['wall']['ci95_lower'],1.)
    def test_no_arbitrary_threepercent_floor(self):self.assertTrue(ab(blocks('ab',31,1.005))['both_metrics_positive'])
    def test_identity_or_reversedlabels_do_not_prove_gain(self):
        for ratio in (1.,.5):self.assertFalse(ab(blocks('ab',31,ratio))['both_metrics_positive'])
    def test_wall_neutral_rejects_cpu_only_claim(self):self.assertFalse(ab(blocks('ab',31,1.1,1.))['both_metrics_positive'])
    def test_counterbalanced_loglinear_drift_cancels(self):self.assertAlmostEqual(ab(blocks('ab',31,2.,drift=.1))['cpu']['geomean'],2.)
    def test_incomplete_duplicate_wrongorder_wronglabel_warmup_reject(self):
        mutations=[];x=blocks('ab',31);mutations.append(x[:-1]);y=copy.deepcopy(x);y[1]['block']=0;mutations.append(y);y=copy.deepcopy(x);y[1]['samples'].reverse();mutations.append(y);y=copy.deepcopy(x);y[0]['samples'][1]['binary_label']='baseline';mutations.append(y);y=copy.deepcopy(x);y[0]['phase']='warmup';mutations.append(y)
        for rows in mutations:
            with self.subTest(rows=rows[0]['phase']),self.assertRaises(ValueError):ab(rows)
    def test_nonfinite_boolean_zero_metric_reject(self):
        for value in (float('nan'),float('inf'),0.,True,-1.):
            rows=blocks('ab',31);rows[0]['samples'][0]['cpu_seconds']=value
            with self.subTest(value=value),self.assertRaises(ValueError):ab(rows)
if __name__=='__main__':unittest.main(verbosity=2)

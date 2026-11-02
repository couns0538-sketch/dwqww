"""Fixture-only raw-component parser checks; no native qualification."""
import argparse
import hashlib
import json
import pathlib
import tempfile
import unittest
import check_eval_parity as checker

COMPONENTS = [{'name': 'lane0', 'encoding': 'f32-bits'}, {'name': 'combined', 'encoding': 'i32-bits'}]


class ComponentTests(unittest.TestCase):
    def values(self, rows, components=COMPONENTS):
        root = pathlib.Path(tempfile.mkdtemp(prefix='components-fixture-'))
        path = root / 'trace.jsonl'
        header = {'schema': 1, 'kind': 'eval-trace', 'encoding': 'components-v1', 'components': components,'implementation':'scalar'}
        path.write_text('\n'.join(json.dumps(x) for x in [header, *rows]) + '\n', encoding='utf-8')
        return checker.values(path, ['a' * 64], 'components-v1',
                              {'encoding': 'components-v1', 'components': components,'implementation':'scalar'}, checker.digest(path), components)

    def row(self, bits):
        return {'row': 0, 'fen_sha256': 'a' * 64, 'eval_bits': bits,'active_evaluations':0}

    def test_vector_preserves_float_and_signed_integer_bits(self):
        self.assertEqual(self.values([self.row(['3f800000', 'ffffffff'])]), [('3f800000', 'ffffffff')])

    def test_nonfinite_float_component_refused(self):
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            self.values([self.row(['7f800000', '00000000'])])

    def test_missing_component_refused(self):
        with self.assertRaisesRegex(ValueError, 'component'):
            self.values([self.row(['3f800000'])])

    def test_extra_component_refused(self):
        with self.assertRaisesRegex(ValueError, 'component'):
            self.values([self.row(['3f800000', '00000000', '00000000'])])

    def test_signed_zero_remains_distinct(self):
        self.assertNotEqual(self.values([self.row(['80000000', '00000000'])]),
                            self.values([self.row(['00000000', '00000000'])]))

    def test_duplicate_component_names_refused(self):
        components=[{'name':'same','encoding':'f32-bits'}, {'name':'same','encoding':'i32-bits'}]
        with self.assertRaisesRegex(ValueError, 'component'):
            self.values([self.row(['00000000','00000000'])],components)

    def test_component_order_is_part_of_header(self):
        root=pathlib.Path(tempfile.mkdtemp(prefix='components-fixture-'))
        path=root/'trace.jsonl'
        path.write_text(json.dumps({'schema':1,'kind':'eval-trace','encoding':'components-v1','components':list(reversed(COMPONENTS))})+'\n'+json.dumps(self.row(['00000000','00000000']))+'\n')
        with self.assertRaises(checker.Failed):
            checker.values(path,['a'*64],'components-v1',{'components':COMPONENTS},checker.digest(path),COMPONENTS)

    def test_inactive_candidate_row_refused(self):
        row=self.row(['00000000','00000000']);row['active_evaluations']=1
        with self.assertRaisesRegex(ValueError,'activation'):
            self.values([row])


class EmbeddedTests(unittest.TestCase):
    def case(self,storage='embedded',positive_mismatch=False,negative_mismatch=True,bad_binary_header=False,same_binary=False):
        root=pathlib.Path(tempfile.mkdtemp(prefix='embedded-fixture-'))
        def ref(name,data):
            path=root/name;path.write_bytes(data)
            return {'path':name,'sha256':checker.digest(path)}
        fen='8/8/8/8/8/8/4k3/6K1 w - - 0 1'
        fen_sha=hashlib.sha256(fen.encode()).hexdigest()
        record={'schema':1,'encoding':'components-v1','components':COMPONENTS,'network_storage':storage,
                'candidate_path':{'name':'wide','active_evaluations':12000},
                'fens':ref('fens.txt',((fen+'\n')*12000).encode()),
                'scalar_binary':ref('scalar.exe',b'fixture-good'),
                'candidate_binary':ref('candidate.exe',b'fixture-good'),
                'network':ref('network.bin',b'\x00\x00\x01\x00'),
                'scalar_options':ref('off.json',b'{"wide":false}'),
                'candidate_options':ref('on.json',b'{"wide":true}'),
                'native_log':ref('native.log',b'fixture only; no engine executed'),
                'embedded_provenance':ref('source.json',b'{"scope":"fixture"}'),
                'build_provenance':ref('build.json',b'{"scope":"fixture"}')}
        control={'network':ref('negative-network.bin',b'\x00\x00\x02\x00'),'tensor':'W2','offset':2,'width':2}
        if storage=='embedded':control['binary']=ref('negative.exe',b'fixture-good' if same_binary else b'fixture-negative')
        def trace(name,binary,network,options,implementation,mismatch):
            header={'schema':1,'kind':'eval-trace','encoding':'components-v1','components':COMPONENTS,
                    'binary_sha256':binary['sha256'],'network_sha256':network['sha256'],
                    'fens_sha256':record['fens']['sha256'],'options_sha256':options['sha256'],'implementation':implementation}
            path=root/name
            with path.open('w',encoding='utf-8',newline='\n') as f:
                f.write(json.dumps(header)+'\n')
                for i in range(12000):
                    f.write(json.dumps({'row':i,'fen_sha256':fen_sha,
                                        'eval_bits':['40000000' if mismatch and i==0 else '3f800000','00000000'],
                                        'active_evaluations':0 if implementation=='scalar' else 1})+'\n')
            return {'path':name,'sha256':checker.digest(path)}
        record['scalar_trace']=trace('off.jsonl',record['scalar_binary'],record['network'],record['scalar_options'],'scalar',False)
        record['candidate_trace']=trace('on.jsonl',record['candidate_binary'],record['network'],record['candidate_options'],'wide',positive_mismatch)
        negative_binary=control.get('binary',record['candidate_binary'])
        if bad_binary_header:negative_binary=record['candidate_binary']
        control['trace']=trace('negative.jsonl',negative_binary,control['network'],record['candidate_options'],'wide',negative_mismatch)
        record['negative_control']=control
        path=root/'record.json';path.write_text(json.dumps(record),encoding='utf-8')
        return checker.check(path)

    def test_embedded_separate_negative_binary_passes(self):
        result=self.case();self.assertEqual(result['status'],'PASS',result)
        self.assertEqual(result['mismatches'],0);self.assertEqual(result['negative_control_mismatches'],1)

    def test_wrong_negative_binary_header_fails(self):
        self.assertEqual(self.case(bad_binary_header=True)['status'],'FAIL')

    def test_same_embedded_binary_fails(self):
        self.assertEqual(self.case(same_binary=True)['status'],'FAIL')

    def test_positive_component_difference_fails(self):
        result=self.case(positive_mismatch=True)
        self.assertEqual(result['status'],'FAIL');self.assertEqual(result['mismatches'],1)

    def test_negative_must_differ_from_good_off(self):
        self.assertEqual(self.case(negative_mismatch=False)['status'],'FAIL')

    def test_external_network_still_uses_same_candidate_binary(self):
        self.assertEqual(self.case(storage='external')['status'],'PASS')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--threads',type=int,choices=[1],required=True);ap.add_argument('--baseline');args=ap.parse_args()
    if args.baseline:
        import importlib.util
        spec=importlib.util.spec_from_file_location('original_checker',args.baseline)
        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    unittest.main(argv=['test_components'],verbosity=2)

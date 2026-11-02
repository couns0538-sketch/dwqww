"""Synthetic sealer regressions only; no native data/engine qualification."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
import argparse

MODULE = Path('D:/a10/wt/skills/gate-handover-pack/scripts/seal_evidence.py')
spec = importlib.util.spec_from_file_location('seal_evidence', MODULE)
seal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seal)


class SealerTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='pack-fixture-'))
        self.request = self.root / 'request.json'
        self.out = self.root / 'sealed'
        self.artifacts = []
        self.add('log', 'raw.log', b'original fixture log\n')

    def add(self, role, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        entry = {'role': role, 'path': name,
                 'sha256': hashlib.sha256(data).hexdigest()}
        self.artifacts.append(entry)
        return entry

    def manifest(self, blockers=None):
        self.request.write_text(json.dumps({'schema': 1,
            'source_root': str(self.root), 'artifacts': self.artifacts,
            'blockers': ([] if any(x['role']=='audit_report' for x in self.artifacts) else ['Native qualification pending']) if blockers is None else blockers}), encoding='utf-8')

    def run_seal(self, purpose='incomplete-engine'):
        return seal.seal(self.request, self.out, purpose)

    def test_incomplete_seals_original_bytes_and_both_hash_manifests(self):
        self.manifest()
        report = self.run_seal()
        self.assertEqual(report['status'], 'SEALED_INCOMPLETE')
        self.assertEqual(report['strength'], 'UNPROVEN')
        self.assertEqual((self.out/'artifacts/raw.log').read_bytes(), b'original fixture log\n')
        for algorithm, name in [('sha256','SHA256SUMS'),('md5','MD5SUMS')]:
            for line in (self.out/name).read_text().splitlines():
                digest, rel = line.split('  ', 1)
                self.assertEqual(hashlib.new(algorithm,(self.out/rel).read_bytes()).hexdigest(),digest)
        self.assertNotIn('READY_FOR_QA_REVIEW', (self.out/'REPORT.json').read_text())

    def test_output_reuse_refused(self):
        self.manifest(); self.run_seal()
        with self.assertRaisesRegex(ValueError,'already exists'):
            self.run_seal()

    def test_wrong_input_hash_refused_before_output(self):
        self.manifest(); (self.root/'raw.log').write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            self.run_seal()
        self.assertFalse(self.out.exists())

    def test_path_traversal_refused(self):
        self.artifacts[0]['path']='../raw.log'; self.manifest()
        with self.assertRaisesRegex(ValueError,'relative artifact path'):
            self.run_seal()

    def test_case_alias_duplicate_refused(self):
        self.artifacts.append(dict(self.artifacts[0],path='RAW.LOG')); self.manifest()
        with self.assertRaisesRegex(ValueError,'duplicate artifact'):
            self.run_seal()

    def test_incomplete_needs_nonempty_blocker(self):
        self.manifest(blockers=[])
        with self.assertRaisesRegex(ValueError,'blocker'):
            self.run_seal()

    def test_non_r10_output_refused(self):
        self.manifest(); self.out=Path('D:/a10-other/forbidden-output')
        with self.assertRaisesRegex(ValueError,'D:.*a10'):
            self.run_seal()

    def test_reparse_input_refused(self):
        link=self.root/'alias.log'
        os.symlink(self.root/'raw.log',link)
        try:
            self.artifacts[0]['path']='alias.log'; self.manifest()
            with self.assertRaisesRegex(ValueError,'reparse|symlink'):
                self.run_seal()
        finally:
            link.unlink()  # only this owned synthetic symlink

    def data_reports(self):
        evidence = [{'path':'raw.log','sha256':self.artifacts[0]['sha256']}]
        self.add('tool','tool.py',b'# fixture tool\n')
        self.add('sample','sample.pos',b'fixture sample')
        self.add('training_command','training.txt',b'fixture; do not run\n')
        left=self.add('replay_output','baseline.pos',b'fixture output')
        self.audit={'schema':1,'status':'PASS','evidence_scope':'actual-adapter',
            'source_rows':1,'training_rows':1,'position_overlap_rows':0,
            'game_overlap_rows':0,'state_mismatch_rows':0,'unknown_game_id_rows':0,
            'holdouts':{h:{'rows':1,'sha256':'a'*64,'trusted_complete':True} for h in ('013','014')},
            'evidence':evidence}
        self.replay={'schema':1,'status':'PASS','evidence_scope':'actual-adapter',
            'output_roles':['pos'],'evidence':evidence,
            'faults':{}}
        for name in seal.FAULTS:
            right=self.add('replay_output',name+'.pos',b'fixture output')
            output={'role':'pos','uninterrupted':dict(left,md5=hashlib.md5(b'fixture output').hexdigest()),
                    'resumed':dict(right,md5=hashlib.md5(b'fixture output').hexdigest())}
            self.replay['faults'][name]={'status':'PASS','outputs':[output]}
        self.add('audit_report','audit.json',json.dumps(self.audit).encode())
        self.add('replay_report','replay.json',json.dumps(self.replay).encode())

    def test_data_without_actual_reports_blocked(self):
        self.manifest(blockers=[])
        with self.assertRaisesRegex(ValueError,'data-tool requires'):
            self.run_seal('data-tool')
        self.assertFalse(self.out.exists())

    def test_bound_synthetic_data_contract_can_seal_without_gate_ready_status(self):
        self.data_reports(); self.manifest()
        report=self.run_seal('data-tool')
        self.assertEqual(report['status'],'SEALED_DATA_TOOL')
        self.assertEqual(report['strength'],'UNPROVEN')

    def replace_report(self, role, report):
        entry=next(x for x in self.artifacts if x['role']==role)
        data=json.dumps(report).encode(); (self.root/entry['path']).write_bytes(data)
        entry['sha256']=hashlib.sha256(data).hexdigest()

    def test_missing_game_ids_cannot_be_pass(self):
        self.data_reports(); self.audit['unknown_game_id_rows']=1
        self.replace_report('audit_report',self.audit);self.manifest()
        with self.assertRaisesRegex(ValueError,'unknown_game_id_rows'):
            self.run_seal('data-tool')

    def test_fixture_scope_cannot_be_data_proof(self):
        self.data_reports(); self.replay['evidence_scope']='fixture'
        self.replace_report('replay_report',self.replay);self.manifest()
        with self.assertRaisesRegex(ValueError,'actual-adapter'):
            self.run_seal('data-tool')

    def test_missing_fault_point_blocked(self):
        self.data_reports();del self.replay['faults'][seal.FAULTS[0]]
        self.replace_report('replay_report',self.replay);self.manifest()
        with self.assertRaisesRegex(ValueError,'fault points'):
            self.run_seal('data-tool')

    def test_wrong_resume_md5_blocked(self):
        self.data_reports();self.replay['faults'][seal.FAULTS[0]]['outputs'][0]['resumed']['md5']='0'*32
        self.replace_report('replay_report',self.replay);self.manifest()
        with self.assertRaisesRegex(ValueError,'MD5'):
            self.run_seal('data-tool')

    def test_reused_baseline_as_resumed_output_blocked(self):
        self.data_reports();output=self.replay['faults'][seal.FAULTS[0]]['outputs'][0]
        output['resumed']=dict(output['uninterrupted'])
        self.replace_report('replay_report',self.replay);self.manifest()
        with self.assertRaisesRegex(ValueError,'independent'):
            self.run_seal('data-tool')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--threads',type=int,choices=(1,),required=True)
    parser.parse_args()
    unittest.main(argv=[__file__],verbosity=2)

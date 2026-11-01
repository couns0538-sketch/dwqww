"""Gate packs retain immutable evidence and scope snapshot freshness honestly."""
import hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/gate-handover-pack/scripts/make_gate_pack.py'

class GatePackTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'gate helper missing')
        spec=importlib.util.spec_from_file_location('gate_helper', SCRIPT)
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name); self.out=self.root/'pack'
        self.request=self.root/'request.json'
        self.data={'schema':1,'baseline_commit':'a'*40,'candidate_commit':'b'*40,
          'gate':{'name':'fixture','start':1001,'srand':2001,'time_control':'10+0.1','threads':1,'hash_mb':128},
          'build':{'compiler':'fixture GCC','flags':'fixture flags'},
          'variants':{'OFF':{'Option':0},'ON':{'Option':1}},
          'artifacts':[], 'snapshots':[]}
        for role in self.m.REQUIRED_ROLES:
            content=json.dumps(self.data['gate']).encode() if role=='protocol' else b'fixture '+role.encode()
            f=self.root/(role+'.json');f.write_bytes(content)
            self.data['artifacts'].append({'role':role,'path':f.name,'sha256':hashlib.sha256(content).hexdigest()})
        items={a['role']:a for a in self.data['artifacts']}
        proof={'schema':1,'evidence_scope':'native','status':'PASS','baseline_commit':'a'*40,'candidate_commit':'b'*40,
          'contract_sha256':items['lock_contract']['sha256'],
          'tested_options':{'off':self.data['variants']['OFF'],'on':self.data['variants']['ON']},
          'baseline_binary_sha256':items['baseline_binary']['sha256'],'candidate_binary_sha256':items['candidate_binary']['sha256'],'net_sha256':items['net']['sha256'],
          'checks':[{'name':n,'status':'PASS','evidence':[dict(path=items['test_log']['path'],sha256=items['test_log']['sha256'])]} for n in self.m.REQUIRED_CHECKS]}
        p=self.root/items['proof']['path'];p.write_text(json.dumps(proof));items['proof']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        snap=self.root/'gate-copy.json';snap.write_text(json.dumps({'schema':1,'gates':[{'name':'old','start':2,'srand':3}]}))
        self.data['snapshots']=[{'path':snap.name,'sha256':hashlib.sha256(snap.read_bytes()).hexdigest(),
          'mtime_ns':snap.stat().st_mtime_ns,'captured_at_utc':datetime.now(timezone.utc).isoformat(),
          'source_label':'crew normalized copy of complete active and archived gate list','trusted_copy':True}]
        self.save()
    def save(self):self.request.write_text(json.dumps(self.data))
    def update_protocol(self):
        item=next(a for a in self.data['artifacts'] if a['role']=='protocol');p=self.root/item['path'];p.write_text(json.dumps(self.data['gate']));item['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    def make(self):self.save();return self.m.make_pack(self.request,self.out)
    def test_pack_has_matching_md5s_sha256s_and_never_overwrites(self):
        before={p.name:p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        result=self.make();self.assertEqual(result['status'],'READY_FOR_QA_REVIEW')
        for manifest,algorithm in [('MD5SUMS','md5'),('SHA256SUMS','sha256')]:
            for line in (self.out/manifest).read_text().splitlines():
                digest,name=line.split('  ',1)
                self.assertEqual(hashlib.new(algorithm,(self.out/name).read_bytes()).hexdigest(),digest)
        self.assertIn('Snapshot-only',(self.out/'GATE.md').read_text())
        with self.assertRaisesRegex(ValueError,'exists'):self.make()
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir() if p.is_file()})
    def test_reused_start_or_srand_rejected_before_output(self):
        for key,value in [('start',2),('srand',3)]:
            old=self.data['gate'][key];self.data['gate'][key]=value
            self.update_protocol()
            with self.assertRaisesRegex(ValueError,'reused '+key):self.make()
            self.assertFalse(self.out.exists());self.data['gate'][key]=old
    def test_stale_and_future_snapshots_rejected(self):
        for delta in [timedelta(hours=-1),timedelta(minutes=1)]:
            self.data['snapshots'][0]['captured_at_utc']=(datetime.now(timezone.utc)+delta).isoformat()
            with self.assertRaisesRegex(ValueError,'freshness'):self.make()
            self.assertFalse(self.out.exists())
    def test_snapshot_hash_and_mtime_checked(self):
        for field,value in [('sha256','0'*64),('mtime_ns',1)]:
            old=self.data['snapshots'][0][field];self.data['snapshots'][0][field]=value
            with self.assertRaisesRegex(ValueError,'hash|mtime'):self.make()
            self.assertFalse(self.out.exists());self.data['snapshots'][0][field]=old
    def test_missing_role_and_wrong_artifact_bytes_rejected(self):
        item=self.data['artifacts'].pop()
        with self.assertRaisesRegex(ValueError,'roles'):self.make()
        self.data['artifacts'].append(item)
        (self.root/item['path']).write_bytes(b'corrupted')
        with self.assertRaisesRegex(ValueError,'hash'):self.make()
        self.assertFalse(self.out.exists())
    def test_nonpassing_or_unbound_proof_rejected(self):
        proof=next(a for a in self.data['artifacts'] if a['role']=='proof');p=self.root/proof['path']
        for field,value in [('status','UNVERIFIED'),('candidate_commit','c'*40)]:
            obj=json.loads(p.read_text());obj[field]=value;p.write_text(json.dumps(obj));proof['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,'proof'):self.make()
            self.assertFalse(self.out.exists())
    def test_no_live_queue_or_npt_paths(self):
        for name in ['queue.txt','queue_state.json','npt/gates.json']:
            self.data['snapshots'][0]['path']=name
            with self.assertRaisesRegex(ValueError,'protected'):self.make()
            self.assertFalse(self.out.exists())
    def test_duplicate_json_keys_and_bool_seed_rejected(self):
        self.request.write_text('{"schema":1,"schema":1}')
        with self.assertRaisesRegex(ValueError,'duplicate'):self.m.make_pack(self.request,self.out)
        self.data['gate']['srand']=True
        with self.assertRaisesRegex(ValueError,'integer'):self.make()
    def test_bad_gate_snapshot_rows_are_not_silently_skipped(self):
        snap=self.data['snapshots'][0];p=self.root/snap['path'];p.write_text('{"schema":1,"gates":[{"name":"bad","srand":1}]}')
        snap['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();snap['mtime_ns']=p.stat().st_mtime_ns
        with self.assertRaisesRegex(ValueError,'integer'):self.make()
    def test_fixture_proof_and_missing_required_check_block_pack(self):
        item=next(a for a in self.data['artifacts'] if a['role']=='proof');p=self.root/item['path'];original=json.loads(p.read_text())
        for variant in ('fixture','missing-check','missing-evidence'):
            proof=json.loads(json.dumps(original))
            if variant=='fixture':proof['evidence_scope']='fixture'
            if variant=='missing-check':proof['checks'].pop()
            if variant=='missing-evidence':proof['checks'][0]['evidence']=[]
            p.write_text(json.dumps(proof));item['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,'proof'):self.make()
            self.assertFalse(self.out.exists())
    def test_protocol_values_cannot_diverge_from_gate_request(self):
        self.data['gate']['time_control']='1+0.01'
        with self.assertRaisesRegex(ValueError,'protocol'):self.make()
        self.assertFalse(self.out.exists())
    def test_symlink_request_and_parent_are_rejected(self):
        alias=self.root/'request-link.json';alias.symlink_to(self.request)
        with self.assertRaisesRegex(ValueError,'symlink'):self.m.make_pack(alias,self.out)
        link=self.root/'parent-link';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):self.m.make_pack(link/'request.json',self.out)
        self.assertFalse(self.out.exists())
    def test_packaged_binaries_and_net_must_be_proof_subjects(self):
        item=next(a for a in self.data['artifacts'] if a['role']=='proof');p=self.root/item['path'];original=json.loads(p.read_text())
        for field in ('baseline_binary_sha256','candidate_binary_sha256','net_sha256'):
            proof=json.loads(json.dumps(original));proof[field]='d'*64
            p.write_text(json.dumps(proof));item['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,'proof subject'):self.make()
            self.assertFalse(self.out.exists())
    def test_substituted_candidate_with_correct_new_manifest_hash_is_rejected(self):
        item=next(a for a in self.data['artifacts'] if a['role']=='candidate_binary');p=self.root/item['path']
        p.write_bytes(b'valid new bytes but not the tested binary');item['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'proof subject'):self.make()
        self.assertFalse(self.out.exists())
    def test_changed_options_do_not_reuse_old_proof(self):
        self.data['variants']['ON']['Option']=2
        with self.assertRaisesRegex(ValueError,'proof options'):self.make()
        self.assertFalse(self.out.exists())
    def test_cli_has_explicit_failure_code_and_no_output(self):
        self.data['gate']['start']=2;self.update_protocol();self.save()
        r=subprocess.run([sys.executable,str(SCRIPT),str(self.request),'--out',str(self.out)],capture_output=True,text=True)
        self.assertEqual(r.returncode,2,r.stderr);self.assertIn('reused start',r.stdout);self.assertEqual(json.loads(r.stdout)['status'],'BLOCKED');self.assertFalse(self.out.exists())

if __name__=='__main__':unittest.main()

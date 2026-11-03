import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import struct
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from p5_qc import audit_r14, audit_old, DuplicateIndex
from qc_core import fen_info
from run_policy import Inputs

FEN = '4k3/8/8/8/8/8/8/4K3 w - - 0 1'

def put_json(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fixture(root):
    job = root / 'job'
    (job / 'shards' / 'shard_00000').mkdir(parents=True)
    (job / 'final').mkdir()
    source = root / 'source.txt'
    source.write_text(FEN + ' | 5 | 1\n', encoding='utf-8')
    headers = ['row_id','game_id','split','fen','score_stm','old_score_stm','result','depth','nodes']
    values = ['0','s0g0','train',FEN,'30000','5','1','1','10']
    labels = '\t'.join(headers)+'\n'+'\t'.join(values)+'\n'
    shard = job / 'shards' / 'shard_00000'
    (shard / 'labels.tsv').write_text(labels, encoding='utf-8')
    (job / 'final' / 'labels.tsv').write_text(labels, encoding='utf-8')
    (job / 'final' / 'train.txt').write_text(FEN + ' | 30000 | 1\n', encoding='utf-8')
    (job / 'final' / 'val.txt').write_text('', encoding='utf-8')
    (job / 'rows.tsv').write_text('row_id\tgame_id\tsplit\tfen\told_score_stm\tresult\tsource\tsource_row\n0\ts0g0\ttrain\t'+FEN+'\t5\t1\t0\t1\n', encoding='utf-8')
    prepare = dict(run_id='fixture', rows=1, train_rows=1, val_rows=0,
                   inputs=[dict(index=0,path=str(source),sha256=digest(source),kind='selfplay')], rows_tsv_sha256=digest(job/'rows.tsv'))
    put_json(job/'prepare.json', prepare)
    put_json(job/'run_config.json', dict(run_id='fixture',shard_size=1,nodes=10,prepare_json_sha256=digest(job/'prepare.json')))
    put_json(job/'status.json', dict(run_id='fixture',rows_total=1,rows_done=1,shards_total=1,shards_done=1))
    put_json(shard/'summary.json', dict(run_id='fixture',shard=0,first_row=0,rows=1,nodes_total=10))
    put_json(shard/'MANIFEST.json', {name:digest(shard/name) for name in ('labels.tsv','summary.json')})
    final = dict(run_id='fixture',rows=1,train_rows=1,val_rows=0,train_games=1,val_games=0,game_overlap=0,
                 prepare_json_sha256=digest(job/'prepare.json'),shard_labels_sha256=[digest(shard/'labels.tsv')],
                 files={name:dict(sha256=digest(job/'final'/name),md5=hashlib.md5((job/'final'/name).read_bytes()).hexdigest(),bytes=(job/'final'/name).stat().st_size) for name in ('labels.tsv','train.txt','val.txt')})
    put_json(job/'final'/'MANIFEST.json',final)
    return job

def old_fixture(root):
    job=root/'old'
    shard=job/'shards'/'shard_00000'
    shard.mkdir(parents=True)
    stem='relabel_00000'
    (shard/(stem+'.pos')).write_bytes(struct.pack('<4sIQ',b'FPOS',1,1)+fen_info(FEN)['board']+struct.pack('<hB',0,2))
    (shard/(stem+'.hce')).write_bytes(struct.pack('<4sIQ',b'FHCE',1,1)+struct.pack('<h',0))
    (shard/(stem+'.fen')).write_text(FEN+'\n')
    label=dict(input_index=0,output_index=0,score_stm=0,old_score_stm=5,hce_stm=0,depth=1,nodes=1,state_origin='reconstructed_no_castling_no_ep_clock0')
    (shard/'labels.jsonl').write_text(json.dumps(label)+'\n')
    outputs={'.'+ext:digest(shard/(stem+'.'+ext)) for ext in ('pos','hce','fen')}
    summary=dict(status='SEALED',selected=1,exact_label_rows=0,reconstructed_label_rows=1,state_origin=label['state_origin'],
                 config=dict(start=0,count=1,stride=1),outputs=outputs)
    put_json(shard/'summary.json',summary)
    manifest={name:digest(shard/name) for name in ('labels.jsonl','summary.json',stem+'.pos',stem+'.hce',stem+'.fen')}
    put_json(shard/'manifest.json',manifest)
    (job/'shards.tsv').write_text('shard\trows\tdir\tseconds\tpos_sha256\thce_sha256\tfen_sha256\trun_id\n0\t1\tshard_00000\t1.0\t'+outputs['.pos']+'\t'+outputs['.hce']+'\t'+outputs['.fen']+'\tfixture\n')
    put_json(job/'status.json',dict(run_id='fixture',shards_done=1,shards_total=2,rows_done=1,rows_total=2))
    return job


class AuditTests(unittest.TestCase):
    def test_old_publication_totals_are_consistent(self):
        for patch in ({'rows_total':0},{'shards_total':0},{'shards_total':1}):
            with self.subTest(patch=patch),tempfile.TemporaryDirectory() as tmp:
                job=old_fixture(Path(tmp))
                status=json.loads((job/'status.json').read_text())
                status.update(patch)
                put_json(job/'status.json',status)
                with self.assertRaisesRegex(ValueError,'total|completion'):
                    audit_old(job,Inputs(),lambda row:None)

    def test_old_complete_prefix_is_not_complete_source_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            job=old_fixture(Path(tmp))
            rows=[]
            result=audit_old(job,Inputs(),rows.append)
            self.assertTrue(result['cohort_complete'])
            self.assertFalse(result['source_job_complete'])
            self.assertEqual(rows[0]['result'],0.5)

    def test_old_boolean_integer_fields_rejected_even_with_valid_hashes(self):
        for field in ('input_index','output_index','score_stm','hce_stm','depth','nodes'):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                job=old_fixture(Path(tmp))
                shard=job/'shards'/'shard_00000'
                path=shard/'labels.jsonl'
                label=json.loads(path.read_text())
                label[field]=bool(label[field])
                path.write_text(json.dumps(label)+'\n')
                manifest=json.loads((shard/'manifest.json').read_text())
                manifest['labels.jsonl']=digest(path)
                put_json(shard/'manifest.json',manifest)
                with self.assertRaises(ValueError):
                    audit_old(job,Inputs(),lambda row:None)

    def test_complete_fixture_and_retained_part(self):
        with tempfile.TemporaryDirectory() as tmp:
            job=fixture(Path(tmp))
            (job/'shards'/'shard_00000'/'leftover.part').write_text('retained')
            rows=[]
            result=audit_r14(job, Inputs(), rows.append, fixture=True)
            self.assertEqual(result['rows'],1)
            self.assertEqual(rows[0]['score_stm'],30000)
            self.assertEqual(rows[0]['original_label']['score_stm'],'30000')
            self.assertEqual(rows[0]['input_line'],2)
            self.assertEqual(result['authentic_game_overlap'],None)
            self.assertEqual(result['provenance_status'],'UNVERIFIED')

    def test_missing_shard_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            job=fixture(Path(tmp))
            (job/'shards'/'shard_00000'/'labels.tsv').unlink()
            with self.assertRaises((ValueError,FileNotFoundError)):
                audit_r14(job,Inputs(),lambda row:None,fixture=True)

    def test_final_assembly_rehashed_but_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            job=fixture(Path(tmp))
            target=job/'final'/'labels.tsv'
            target.write_text(target.read_text().replace('\t30000\t','\t29999\t'))
            manifest=json.loads((job/'final'/'MANIFEST.json').read_text())
            manifest['files']['labels.tsv'].update(sha256=digest(target),md5=hashlib.md5(target.read_bytes()).hexdigest(),bytes=target.stat().st_size)
            put_json(job/'final'/'MANIFEST.json',manifest)
            with self.assertRaisesRegex(ValueError,'assembly'):
                audit_r14(job,Inputs(),lambda row:None,fixture=True)

    def test_duplicate_index_full_fen_and_split_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            index=DuplicateIndex(Path(tmp)/'index.sqlite')
            index.add('new','train',FEN)
            index.add('new','val',FEN)
            index.add('new','train',FEN.replace('0 1','1 1'))
            result=index.report('new')
            self.assertEqual(result['unique_fens'],2)
            self.assertEqual(result['duplicate_rows'],1)
            self.assertEqual(result['train_val_shared_fens'],1)
            index.close()

    def test_assembly_bytes_not_just_parsed_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            job=fixture(Path(tmp))
            target=job/'final'/'labels.tsv'
            target.write_bytes(target.read_bytes()+b'\n')
            manifest=json.loads((job/'final'/'MANIFEST.json').read_text())
            manifest['files']['labels.tsv'].update(sha256=digest(target),md5=hashlib.md5(target.read_bytes()).hexdigest(),bytes=target.stat().st_size)
            put_json(job/'final'/'MANIFEST.json',manifest)
            with self.assertRaisesRegex(ValueError,'assembly'):
                audit_r14(job,Inputs(),lambda row:None,fixture=True)

    def test_original_source_binding_not_only_row_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            job=fixture(Path(tmp))
            source=Path(tmp)/'source.txt'
            source.write_text(FEN+' | 6 | 1\n')
            prepare=json.loads((job/'prepare.json').read_text())
            prepare['inputs'][0]['sha256']=digest(source)
            put_json(job/'prepare.json',prepare)
            for target in (job/'run_config.json',job/'final'/'MANIFEST.json'):
                value=json.loads(target.read_text())
                value['prepare_json_sha256']=digest(job/'prepare.json')
                put_json(target,value)
            with self.assertRaisesRegex(ValueError,'original source row'):
                audit_r14(job,Inputs(),lambda row:None,fixture=True)

    def test_boolean_publication_count_not_an_integer(self):
        for name,key in (('status.json','rows_done'),('final/MANIFEST.json','rows'),('final/MANIFEST.json','train_games')):
            with self.subTest(name=name,key=key),tempfile.TemporaryDirectory() as tmp:
                job=fixture(Path(tmp))
                path=job/name
                value=json.loads(path.read_text())
                value[key]=True
                put_json(path,value)
                with self.assertRaises(ValueError):
                    audit_r14(job,Inputs(),lambda row:None,fixture=True)

if __name__=='__main__':
    unittest.main()

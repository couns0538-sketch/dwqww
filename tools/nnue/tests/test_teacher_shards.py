"""Manifest, assignment and preservation contracts for process-sharded labeling."""
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import label_teacher_games as labels


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


class ShardTests(unittest.TestCase):
    def setUp(self):
        try:self.tool=importlib.import_module('coordinate_teacher_shards')
        except ModuleNotFoundError:self.tool=None
        self.assertIsNotNone(self.tool,'Process-shard coordinator is not implemented')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.gen=self.root/'generated';(self.gen/'chunks').mkdir(parents=True)
        self.initial=self.root/'initial';(self.initial/'chunks').mkdir(parents=True)
        self.teacher=self.root/'teacher';self.teacher.write_bytes(b'pinned external teacher')
        config={'seed':17};config['config_sha256']=hashlib.sha256(encoded(config)).hexdigest()
        chunks=[]
        for index in range(8):
            path=self.gen/'chunks'/('games-%06d.jsonl.gz'%index)
            with gzip.open(path,'wt') as stream:stream.write(json.dumps({'game_id':'g%d'%index})+'\n')
            chunks.append({'path':str(path.relative_to(self.gen)),'sha256':labels.sha256(path),'games':1,'game_indices':[index]})
        self.generation={'configuration':config,'chunks':chunks,'status':'PASS_COMPLETED_GAMES_OWNED_ENGINES_CLOSED'}
        self.write(self.gen/'manifest.json',self.generation)
        self.config={'depth':3,'workers':4,'teacher_binary':str(self.teacher),'teacher_sha256':labels.sha256(self.teacher),
            'teacher_bytes':self.teacher.stat().st_size,'teacher_network_sha256':'a'*64,'options':labels.OPTIONS,'policy':labels.POLICY,
            'input_dir':str(self.gen),'tool_sha256':labels.sha256(Path(labels.__file__)),'timeout_s':60}
        self.initial_manifest=self.manifest(self.initial,0,self.config)

    def write(self,path,value):path.write_text(json.dumps(value)+'\n')

    def manifest(self,root,index,config):
        name='chunk-games-%06d'%index;folder=root/'chunks'/name;folder.mkdir(parents=True,exist_ok=True)
        data=folder/'labels.jsonl.gz'
        with gzip.open(data,'wt') as stream:stream.write(json.dumps({'game_id':'g%d'%index,'samples':[]})+'\n')
        source=self.gen/'chunks'/('games-%06d.jsonl.gz'%index)
        meta={'path':name+'/labels.jsonl.gz','sha256':labels.sha256(data),'source_path':str(source),
            'source_sha256':labels.sha256(source),'games':1,'accepted':0,'input_positions':1,'game_ids':['g%d'%index],
            'game_indices':[index],'split_games':{'train':1},'teacher_depth':3}
        self.write(folder/'metadata.json',meta)
        (root/'transcript-000').mkdir(exist_ok=True)
        raw=root/'transcript-000'/'uci-000000.jsonl.gz'
        with gzip.open(raw,'wt') as stream:stream.write('{"direction":"out","line":"uciok"}\n')
        result={'schema':'forge-independent-teacher-games-v1','configuration':config,'chunks':[meta],
            'totals':{'games':1,'accepted':0},'status':'complete',
            'teacher_identities':[{'name':'Stockfish 19'}],
            'transcript_sessions':[{'directory':'transcript-000','complete':True,'records':1,
                'segments':[{'path':raw.name,'sha256':labels.sha256(raw),'bytes':raw.stat().st_size,'records':1}]}]}
        self.write(root/'manifest.json',result);return root/'manifest.json'

    def coordinator(self):
        return self.tool.Coordinator(self.gen,self.root/'combined',self.initial_manifest,
            self.teacher,'a'*64,Path(labels.__file__),3,4)

    def test_initial_preserved_and_new_chunks_assigned_by_index_mod4(self):
        original=labels.sha256(self.initial_manifest);coordinator=self.coordinator()
        assigned=coordinator.assign_inputs(max_pending=2)
        self.assertEqual(len(assigned),7)
        self.assertFalse(any(row['index']==0 for row in assigned))
        for row in assigned:
            self.assertEqual(row['worker'],row['index']%4)
            alias=Path(row['alias']);self.assertTrue(alias.is_symlink())
            self.assertEqual(alias.resolve(),Path(row['source_path']))
            self.assertEqual(labels.sha256(alias),row['sha256'])
        combined=coordinator.publish('running')
        self.assertEqual(combined['chunks'][0]['path'],'initial/chunk-games-000000/labels.jsonl.gz')
        self.assertEqual(labels.sha256(self.initial_manifest),original)
        self.assertEqual(combined['configuration']['tool_sha256'],self.config['tool_sha256'])
        self.assertEqual(combined['configuration']['execution_model'],'4_independent_python_processes')
        self.assertEqual(combined['configuration']['workers'],4)
        self.assertEqual(combined['chunks'][0]['source_path'],str(self.gen/'chunks/games-000000.jsonl.gz'))

    def test_changed_generator_chunk_is_rejected_before_symlink(self):
        path=self.gen/'chunks/games-000001.jsonl.gz';path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'hash'):self.coordinator()
        self.assertFalse(list((self.root/'combined/inputs').glob('*/chunks/*.jsonl.gz')))

    def test_changed_initial_transcript_fails_before_children_launch(self):
        raw=self.initial/'transcript-000/uci-000000.jsonl.gz';raw.write_bytes(raw.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'hash'):self.coordinator()

    def test_all_source_paths_bound_and_unassigned_sources_checked_at_closure(self):
        coordinator=self.coordinator()
        expected={str(self.teacher.resolve()),str(Path(labels.__file__).resolve()),
                  str(Path(self.tool.__file__).resolve())}
        self.assertTrue(expected.issubset(coordinator.bindings))
        path=self.gen/'chunks/games-000007.jsonl.gz'
        path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'hash'):coordinator.verify_all_bindings()

    def test_shard_metadata_preserved_and_final_bindings_revalidated(self):
        coordinator=self.coordinator();coordinator.assign_inputs()
        root=coordinator.worker_root(1);config=dict(coordinator.child_configuration(1))
        manifest_path=self.manifest(root,1,config);manifest_hash=labels.sha256(manifest_path)
        combined=coordinator.publish('running')
        self.assertEqual(len(combined['chunks']),2)
        self.assertEqual(combined['totals']['games'],2)
        self.assertEqual(combined['chunks'][1]['path'],'worker1/chunk-games-000001/labels.jsonl.gz')
        self.assertEqual(labels.sha256(manifest_path),manifest_hash)
        self.assertEqual(combined['chunks'][1]['source_path'],str(self.gen/'chunks/games-000001.jsonl.gz'))
        coordinator.verify_all_bindings()
        (self.initial/'chunks/chunk-games-000000/labels.jsonl.gz').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'hash'):coordinator.verify_all_bindings()

if __name__=='__main__':unittest.main(verbosity=2)

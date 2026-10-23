"""A raw segment union must remain valid input to the unchanged coordinator."""
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import label_teacher_games as labeler
from coordinate_teacher_shards import Coordinator


class MergeTests(unittest.TestCase):
    def setUp(self):
        try:self.tool=importlib.import_module('merge_teacher_segments')
        except ModuleNotFoundError:self.tool=None
        self.assertIsNotNone(self.tool,'Closed raw segment merger is not implemented')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.gen=self.root/'gen';(self.gen/'chunks').mkdir(parents=True)
        self.teacher=self.root/'teacher';self.teacher.write_bytes(b'fixed teacher')
        self.cfg={'teacher_binary':str(self.teacher),'teacher_bytes':self.teacher.stat().st_size,
            'teacher_sha256':labeler.sha256(self.teacher),'teacher_network_sha256':'a'*64,
            'teacher_network_identity':'embedded network bound to teacher binary SHA256',
            'depth':3,'workers':1,'options':labeler.OPTIONS,'policy':labeler.POLICY,
            'input_dir':str(self.gen),'tool_sha256':labeler.sha256(Path(labeler.__file__)),'timeout_s':60}
        self.paths=[];records=[]
        for index in range(2):
            source=self.gen/'chunks'/('games-%06d.jsonl.gz'%index)
            with gzip.open(source,'wt') as stream:stream.write(json.dumps({'game_id':'g%d'%index})+'\n')
            records.append({'path':str(source.relative_to(self.gen)),'sha256':labeler.sha256(source)})
            root=self.root/('raw%d'%index);folder=root/'chunks'/('chunk-games-%06d'%index);folder.mkdir(parents=True)
            labels=folder/'labels.jsonl.gz'
            with gzip.open(labels,'wt') as stream:stream.write(json.dumps({'game_id':'g%d'%index,'samples':[]})+'\n')
            metadata={'path':str(labels.relative_to(root/'chunks')),'sha256':labeler.sha256(labels),
                'source_path':str(source),'source_sha256':labeler.sha256(source),'games':1,
                'accepted':0,'input_positions':1,'game_ids':['g%d'%index],'game_indices':[index],
                'split_games':{'train':1},'teacher_depth':3}
            (folder/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
            trace=root/'transcript-000';trace.mkdir();raw=trace/'uci-000000.jsonl.gz'
            with gzip.open(raw,'wt') as stream:stream.write('{"direction":"out","line":"uciok"}\n')
            manifest={'schema':'forge-independent-teacher-games-v1','status':'complete',
                'configuration':dict(self.cfg,workers=4 if index==0 else 1),'chunks':[metadata],
                'totals':{'games':1,'accepted':0,'input_positions':1},'teacher_identities':[{'name':'Stockfish 19'}],
                'transcript_sessions':[{'directory':'transcript-000','complete':True,'records':1,
                    'segments':[{'path':raw.name,'sha256':labeler.sha256(raw),'bytes':raw.stat().st_size,'records':1}]}]}
            path=root/'manifest.json';path.write_text(json.dumps(manifest)+'\n');self.paths.append(path)
        gconfig={'seed':17};gconfig['config_sha256']=hashlib.sha256(json.dumps(gconfig,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        (self.gen/'manifest.json').write_text(json.dumps({'configuration':gconfig,'chunks':records,
            'status':'PASS_COMPLETED_GAMES_OWNED_ENGINES_CLOSED'})+'\n')

    def merge(self):return self.tool.merge_segments(self.paths,self.gen/'manifest.json',self.root/'merged')

    def test_exact_raw_metadata_union_ingests_unchanged_coordinator(self):
        original=[path.read_bytes() for path in self.paths];merged=self.merge()
        self.assertEqual(merged['totals']['games'],2);self.assertEqual(len(merged['chunks']),2)
        self.assertEqual(merged['active_teacher_workers'],0)
        for index,metadata in enumerate(merged['chunks']):
            path=self.root/'merged/chunks'/metadata['path'];raw=path.parent/'metadata.json'
            old=self.paths[index].parent/'chunks'/metadata['path']
            self.assertEqual(raw.read_bytes(),old.parent.joinpath('metadata.json').read_bytes())
            self.assertEqual(metadata,json.loads(raw.read_bytes()))
            self.assertEqual(path.stat().st_ino,old.stat().st_ino)
            self.assertEqual(self.paths[index].read_bytes(),original[index])
        coordinator=Coordinator(self.gen,self.root/'next',self.root/'merged/manifest.json',
            self.teacher,'a'*64,Path(labeler.__file__),3,4)
        self.assertEqual(len(coordinator.completed),2)
        self.assertEqual(coordinator.assign_inputs(),[])

    def test_overlapping_game_ids_fail_without_publishing(self):
        path=self.paths[1];manifest=json.loads(path.read_text());metadata=manifest['chunks'][0]
        metadata['game_ids']=['g0'];raw=path.parent/'chunks'/metadata['path']
        with gzip.open(raw,'wt') as stream:stream.write(json.dumps({'game_id':'g0','samples':[]})+'\n')
        metadata['sha256']=labeler.sha256(raw)
        (raw.parent/'metadata.json').write_text(json.dumps(metadata)+'\n')
        path.write_text(json.dumps(manifest)+'\n')
        with self.assertRaisesRegex(ValueError,'duplicate game'):self.merge()
        self.assertFalse((self.root/'merged/manifest.json').exists())

    def test_incomplete_or_changed_science_is_rejected(self):
        for field,value in [('status','running'),('depth',4)]:
            manifest=json.loads(self.paths[1].read_text())
            if field=='status':manifest[field]=value
            else:manifest['configuration'][field]=value
            self.paths[1].write_text(json.dumps(manifest)+'\n')
            with self.assertRaises(ValueError):self.merge()
            manifest['status']='complete';manifest['configuration']['depth']=3
            self.paths[1].write_text(json.dumps(manifest)+'\n')

    def test_aggregate_wrapped_metadata_is_rejected(self):
        manifest=json.loads(self.paths[1].read_text())
        manifest['chunks'][0]['segment']='worker0'
        self.paths[1].write_text(json.dumps(manifest)+'\n')
        with self.assertRaisesRegex(ValueError,'raw chunk metadata differs'):self.merge()
        self.assertFalse((self.root/'merged/manifest.json').exists())

    def test_failed_generator_committed_prefix_is_snapshotted_without_claiming_completion(self):
        path=self.gen/'manifest.json';generation=json.loads(path.read_text())
        generation['status']='INCOMPLETE_OR_FAILED';path.write_text(json.dumps(generation)+'\n')
        original=path.read_bytes();merged=self.merge()
        self.assertEqual(merged['generation_status_observed'],'INCOMPLETE_OR_FAILED')
        self.assertEqual((self.root/'merged/generation-at-merge.json').read_bytes(),original)
        self.assertNotIn(str(path.resolve()),[r['path'] for r in merged['artifact_bindings']])
        generation['status']='GENERATION_IN_PROGRESS';path.write_text(json.dumps(generation)+'\n')
        for record in merged['artifact_bindings']:
            self.assertEqual(labeler.sha256(Path(record['path'])),record['sha256'])

    def test_changed_raw_transcript_is_rejected(self):
        raw=self.paths[1].parent/'transcript-000/uci-000000.jsonl.gz';raw.write_bytes(raw.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'hash|size'):self.merge()
        self.assertFalse((self.root/'merged/manifest.json').exists())

if __name__=='__main__':unittest.main(verbosity=2)

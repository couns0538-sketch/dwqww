"""Synthetic controls only; these cannot authenticate the private Job3 games."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from build_game_provenance import build_pack, canonical_game_id
from verify_game_provenance import verify_pack


FENS = [
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',
    'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2',
    'rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1',
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class GameProvenanceTests(unittest.TestCase):
    def setUp(self):
        # Parent supplies D-only TMP and never invokes this suite on a live shard.
        self.root = Path(tempfile.mkdtemp(prefix='gameprov-'))
        self.addCleanup(lambda: None)  # Preserve every fixture, including failures.

    def fixture(self, traced=True, same_game=False):
        src = self.root / 'source.txt'
        src.write_text('\n'.join(f + ' | 0 | 0.5' for f in FENS[:2])+'\n', encoding='utf8')
        normalized = [{'fen': f, 'source': 'fixture-source', 'source_row': i+1,
                       'ply': i, 'raw_score': '0', 'score_stm': 0, 'result_white': 0,
                       'source_kind': 'selfplay', 'has_result': True}
                      for i, f in enumerate(FENS[:2])]
        cohort = self.root / 'cohort.jsonl'
        train = self.root / 'train.jsonl'
        for p in (cohort, train):
            p.write_text(''.join(json.dumps(x)+'\n' for x in normalized), encoding='utf8')
        h13 = self.root / 'h13.txt'; h14 = self.root / 'h14.txt'
        h13.write_text(FENS[2]+' | 0 | 0.5\n', encoding='utf8')
        h14.write_text(FENS[3]+' | 0 | 0.5\n', encoding='utf8')
        specs=[]
        for name, role, fmt, path, count in [('s','source','forge',src,2),
               ('c','cohort','jsonl',cohort,2), ('t','train','jsonl',train,2),
               ('h13','holdout013','forge',h13,1), ('h14','holdout014','forge',h14,1)]:
            specs.append(dict(id=name,role=role,format=fmt,path=str(path),sha256=sha(path),rows=count))
        req=dict(schema=1,scope='fixture',inputs=specs,source_labels={'fixture-source':'s'},origins=[],bindings=[])
        self.trust={'origins':set(),'bindings':{}}
        if traced:
            origin = self.root / 'archive.jsonl'
            positions=[dict(game_index=(0 if same_game and i==2 else i),ply=(0,1,2,1)[i],fen=f) for i,f in enumerate(FENS)]
            origin.write_text(''.join(json.dumps(x)+'\n' for x in positions),encoding='utf8')
            digest=sha(origin); self.trust['origins']={digest}
            req['origins']=[dict(path=str(origin),sha256=digest,format='archived-game-rows-v1',rows=len(positions),bytes=origin.stat().st_size)]
            mapping=self.root / 'bindings.jsonl'
            data=[dict(input_id=id,physical_row=row,origin_sha256=digest,game_index=positions[i]['game_index'],ply=positions[i]['ply'])
                  for id,row,i in [('t',1,0),('t',2,1),('h13',1,2),('h14',1,3)]]
            mapping.write_text(''.join(json.dumps(x)+'\n' for x in data),encoding='utf8')
            req['bindings']=[dict(path=str(mapping),sha256=sha(mapping),rows=len(data),bytes=mapping.stat().st_size)]
            self.trust['bindings'][sha(mapping)]={s['id']:s['sha256'] for s in specs if s['role'] in ('train','holdout013','holdout014')}
        request=self.root / 'request.json'
        request.write_text(json.dumps(req),encoding='utf8')
        return request,req

    def approve_fixture_binding(self,req):
        spec=req['bindings'][0];path=Path(spec['path'])
        spec.update(sha256=sha(path),rows=len(path.read_text().splitlines()),bytes=path.stat().st_size)
        self.trust['bindings']={spec['sha256']:{s['id']:s['sha256'] for s in req['inputs'] if s['role'] in ('train','holdout013','holdout014')}}

    def build(self, **kw):
        request,_=self.fixture(**kw)
        out=self.root/'pack'
        build_pack(request,out,fixture_trust=self.trust)
        return out

    def verify(self, out):
        return verify_pack(out,self.root/('verify-'+str(len(list(self.root.glob('verify-*'))))),fixture_trust=self.trust)

    def test_canonical_id_is_exact_and_relocatable(self):
        expected=hashlib.sha256(b'astra-gameprov-v1\0'+b'a'*64+b'\0'+b'12').hexdigest()
        self.assertEqual(canonical_game_id('a'*64,12),expected)

    def test_traced_fixture_passes_and_preserves_fen(self):
        result=self.verify(self.build())
        self.assertEqual(result['status'],'FIXTURE_PASS')
        self.assertEqual(result['counts']['traced'],4)
        self.assertEqual(result['game_overlap'],0)
        self.assertEqual(result['games'],{'train':2,'holdout':2})

    def test_unknown_holdouts_block_not_zero_overlap(self):
        result=self.verify(self.build(traced=False))
        self.assertEqual(result['status'],'BLOCKED')
        self.assertIsNone(result['game_overlap'])
        self.assertEqual(result['counts']['untraceable'],4)
        self.assertEqual(result['counts']['population'],4)

    def test_holdout_game_wins_even_for_different_positions(self):
        result=self.verify(self.build(same_game=True))
        self.assertEqual(result['status'],'FIXTURE_PASS')
        self.assertEqual(result['counts']['moved_to_holdout'],1)
        self.assertEqual(result['games'],{'train':1,'holdout':2})

    def test_arbitrary_origin_is_not_authenticated(self):
        request,req=self.fixture()
        req['scope']='production'
        request.write_text(json.dumps(req),encoding='utf8')
        with self.assertRaisesRegex(ValueError,'trusted|production'):
            build_pack(request,self.root/'pack',fixture_trust=self.trust)

    def test_unreviewed_archive_digest_refused(self):
        request,_=self.fixture()
        with self.assertRaisesRegex(ValueError,'trusted registry'):
            build_pack(request,self.root/'pack')

    def test_fixture_trust_cannot_override_production_registry(self):
        from pack_io import PRODUCTION,validate_request
        req={'schema':1,'scope':'production','inputs':[],
             'source_labels':{'original':'source001'},'origins':[],'bindings':[]}
        for key,(role,fmt,count,digest) in PRODUCTION.items():
            req['inputs'].append(dict(id=key,role=role,format=fmt,rows=count,sha256=digest))
        with self.assertRaisesRegex(ValueError,'fixture trust cannot authorize production'):
            validate_request(req,fixture_trust={'origins':{'a'*64},'bindings':{}})

    def test_missing_one_original_holdout_binding_blocks(self):
        request,req=self.fixture()
        binding=Path(req['bindings'][0]['path'])
        rows=[json.loads(s) for s in binding.read_text().splitlines()]
        binding.write_text(''.join(json.dumps(r)+'\n' for r in rows if r['input_id']!='h14'))
        self.approve_fixture_binding(req);request.write_text(json.dumps(req))
        out=self.root/'pack';build_pack(request,out,fixture_trust=self.trust)
        result=self.verify(out)
        self.assertEqual(result['status'],'BLOCKED')
        self.assertEqual(result['by_role']['holdout014']['untraceable'],1)
        self.assertIsNone(result['game_overlap'])

    def test_ambiguous_duplicate_binding_refused(self):
        request,req=self.fixture()
        binding=Path(req['bindings'][0]['path'])
        first=binding.read_text().splitlines()[0]
        with binding.open('a') as f:f.write(first+'\n')
        self.approve_fixture_binding(req);request.write_text(json.dumps(req))
        with self.assertRaisesRegex(ValueError,'ambiguous duplicate'):
            build_pack(request,self.root/'pack',fixture_trust=self.trust)

    def test_original_state_mismatch_fails(self):
        request,req=self.fixture()
        train=Path(req['inputs'][2]['path'])
        data=[json.loads(s) for s in train.read_text().splitlines()]
        data[0]['fen']=data[0]['fen'].replace(' KQkq ',' - ')
        train.write_text(''.join(json.dumps(x)+'\n' for x in data))
        req['inputs'][2]['sha256']=sha(train)
        self.approve_fixture_binding(req)
        request.write_text(json.dumps(req))
        with self.assertRaisesRegex(ValueError,'state|source|FEN|cohort'):
            build_pack(request,self.root/'pack',fixture_trust=self.trust)

    def test_changed_input_hash_is_refused(self):
        request,req=self.fixture()
        with open(req['inputs'][0]['path'],'ab') as f:f.write(b'\n')
        with self.assertRaisesRegex(ValueError,'hash|SHA256'):
            build_pack(request,self.root/'pack',fixture_trust=self.trust)

    def test_ep_halfmove_and_fullmove_changes_fail(self):
        for suffix,old,new in [('ep',' e3 ',' - '),('half',' 0 1',' 1 1'),('full',' 0 1',' 0 2')]:
            with self.subTest(field=suffix):
                # Isolate each complete fixture and preserve all failed outputs.
                self.root=Path(tempfile.mkdtemp(prefix='gameprov-state-'))
                request,req=self.fixture()
                train=Path(req['inputs'][2]['path'])
                data=[json.loads(s) for s in train.read_text().splitlines()]
                data[1]['fen']=data[1]['fen'].replace(old,new)
                train.write_text(''.join(json.dumps(x)+'\n' for x in data))
                req['inputs'][2]['sha256']=sha(train);request.write_text(json.dumps(req))
                self.approve_fixture_binding(req);request.write_text(json.dumps(req))
                with self.assertRaisesRegex(ValueError,'source|cohort'):
                    build_pack(request,self.root/'pack',fixture_trust=self.trust)

    def test_reintroduced_row_not_in_cohort_is_refused(self):
        request,req=self.fixture(traced=False)
        train=Path(req['inputs'][2]['path'])
        item=json.loads(train.read_text().splitlines()[0]);item['source_row']=3
        with train.open('a') as f:f.write(json.dumps(item)+'\n')
        req['inputs'][2]['rows']=3;req['inputs'][2]['sha256']=sha(train)
        request.write_text(json.dumps(req))
        with self.assertRaisesRegex(ValueError,'frozen cohort'):
            build_pack(request,self.root/'pack')

    def test_semantic_overlap_negative_with_valid_checksums(self):
        out=self.build(same_game=True)
        manifest=json.loads((out/'PACK.json').read_text())
        changed=False
        for name in manifest['row_chunks']:
            p=out/name
            records=[json.loads(s) for s in gzip.decompress(p.read_bytes()).splitlines()]
            for r in records:
                if r['outcome']=='moved_holdout':
                    r['outcome']='train'; changed=True
            with p.open('wb') as raw:
                with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=1) as stream:
                    for r in records:stream.write((json.dumps(r,sort_keys=True,separators=(',',':'))+'\n').encode())
        self.assertTrue(changed)
        from build_game_provenance import seal_hashes
        seal_hashes(out,replace=True)  # The negative is not merely a checksum failure.
        with self.assertRaisesRegex(ValueError,'game overlap'):
            self.verify(out)

    def test_missing_population_chunk_caught_after_reseal(self):
        out=self.build()
        manifest=json.loads((out/'PACK.json').read_text())
        manifest['row_chunks']=[]
        (out/'PACK.json').write_text(json.dumps(manifest))
        from build_game_provenance import seal_hashes
        seal_hashes(out,replace=True)
        with self.assertRaisesRegex(ValueError,'coverage|population|unaccounted'):
            self.verify(out)

    def test_resume_identical_bytes(self):
        request,_=self.fixture()
        left=self.root/'interrupted'; right=self.root/'uninterrupted'
        with self.assertRaisesRegex(RuntimeError,'cooperative interruption'):
            build_pack(request,left,fixture_trust=self.trust,interrupt_after=1)
        build_pack(request,left,fixture_trust=self.trust,resume=True)
        build_pack(request,right,fixture_trust=self.trust)
        a={str(p.relative_to(left)):sha(p) for p in left.rglob('*') if p.is_file()}
        b={str(p.relative_to(right)):sha(p) for p in right.rglob('*') if p.is_file()}
        self.assertEqual(a,b)

    def test_resume_changed_request_refused(self):
        request,req=self.fixture()
        out=self.root/'pack'
        with self.assertRaisesRegex(RuntimeError,'cooperative interruption'):
            build_pack(request,out,fixture_trust=self.trust,interrupt_after=1)
        request.write_text(json.dumps(req,indent=2))
        with self.assertRaisesRegex(ValueError,'resume request changed'):
            build_pack(request,out,fixture_trust=self.trust,resume=True)

    def test_partial_processing_state_refused_and_preserved(self):
        request,_=self.fixture()
        out=self.root/'pack'
        with self.assertRaisesRegex(RuntimeError,'cooperative interruption'):
            build_pack(request,out,fixture_trust=self.trust,interrupt_after=1)
        prior=out.parent/(out.name+'.build.sqlite')
        prior.write_bytes(b'preserved interrupted processing state')
        with self.assertRaisesRegex(ValueError,'existing processing state'):
            build_pack(request,out,fixture_trust=self.trust,resume=True)
        self.assertEqual(prior.read_bytes(),b'preserved interrupted processing state')

    def test_same_fen_same_ply_different_games_cannot_authorize_remapping(self):
        request,req=self.fixture()
        origin=Path(req['origins'][0]['path'])
        archived=[json.loads(s) for s in origin.read_text().splitlines()]
        archived.append(dict(game_index=99,ply=0,fen=FENS[0]))
        origin.write_text(''.join(json.dumps(r)+'\n' for r in archived))
        digest=sha(origin)
        req['origins'][0].update(sha256=digest,rows=len(archived),bytes=origin.stat().st_size)
        self.trust['origins']={digest}
        binding=Path(req['bindings'][0]['path'])
        links=[json.loads(s) for s in binding.read_text().splitlines()]
        for r in links:r['origin_sha256']=digest
        binding.write_text(''.join(json.dumps(r)+'\n' for r in links))
        self.approve_fixture_binding(req)  # Authenticate the original mapping.
        links[0]['game_index']=99  # Both games contain the identical FEN and ply.
        binding.write_text(''.join(json.dumps(r)+'\n' for r in links))
        req['bindings'][0].update(sha256=sha(binding),bytes=binding.stat().st_size)
        request.write_text(json.dumps(req))
        with self.assertRaisesRegex(ValueError,'binding not authenticated'):
            build_pack(request,self.root/'pack',fixture_trust=self.trust)

    def test_binding_cannot_be_reused_for_different_input_identity(self):
        request,req=self.fixture()
        req['inputs'][2]['sha256']='f'*64
        request.write_text(json.dumps(req))
        with self.assertRaisesRegex(ValueError,'binding input source identities changed'):
            build_pack(request,self.root/'pack',fixture_trust=self.trust)

    def test_windows_trailing_aliases_are_refused(self):
        from pack_io import safe_path
        for name in ('evidence.','evidence ','queue_state.json.','net.nnue '):
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'alias'):
                safe_path(self.root/name)

    def test_reparse_ancestor_checked_before_descendant(self):
        from pack_io import safe_path
        parent=self.root/'junction';child=parent/'child.json'
        actual=os.lstat;seen=[]
        def checked(path,*args,**kwargs):
            p=Path(path);seen.append(p)
            if p==parent:return SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=1024)
            if p==child:raise AssertionError('descendant touched before rejecting junction')
            return actual(path,*args,**kwargs)
        with patch('pack_io.os.lstat',side_effect=checked),self.assertRaisesRegex(ValueError,'reparse'):
            safe_path(child)
        self.assertIn(parent,seen);self.assertNotIn(child,seen)

    def test_nested_manifests_are_checksum_covered(self):
        out=self.build()
        nested=out/'extra';nested.mkdir()
        (nested/'MD5SUMS').write_text('must be hashed')
        from build_game_provenance import seal_hashes
        seal_hashes(out,replace=True)
        self.assertIn('extra/MD5SUMS',(out/'SHA256SUMS').read_text())
        (nested/'MD5SUMS').write_text('changed')
        with self.assertRaisesRegex(ValueError,'checksum mismatch'):
            self.verify(out)

    def test_binding_and_index_capacity_is_reserved_before_output(self):
        from pack_io import estimate_budget
        request,req=self.fixture()
        for s in req['inputs']:s['bytes']=Path(s['path']).stat().st_size
        total=estimate_budget(req)
        bare=dict(req,origins=[],bindings=[])
        baseline=estimate_budget(bare)
        self.assertGreater(total,baseline)
        def disk(path):return SimpleNamespace(free=(50*1024**3+baseline) if str(path).startswith('D') else 100*1024**3)
        with patch('pack_io.shutil.disk_usage',side_effect=disk),self.assertRaisesRegex(ValueError,'reservation'):
            build_pack(request,self.root/'pack',fixture_trust=self.trust)
        self.assertFalse((self.root/'pack').exists())

    def test_verifier_reserves_emitted_index_before_output(self):
        from pack_io import estimate_budget
        out=self.build();manifest=json.loads((out/'PACK.json').read_text())
        reservation=estimate_budget(manifest,verification=True)
        audit=self.root/'starved-audit'
        def disk(path):return SimpleNamespace(free=(50*1024**3+reservation-1) if str(path).startswith('D') else 100*1024**3)
        with patch('pack_io.shutil.disk_usage',side_effect=disk),self.assertRaisesRegex(ValueError,'reservation'):
            verify_pack(out,audit,fixture_trust=self.trust)
        self.assertFalse(audit.exists())

    def test_live_floor_checked_during_checksum_scan(self):
        from pack_io import hashes
        path=self.root/'scan.bin';path.write_bytes(b'x'*(2*1024**2))
        calls=0
        def disk(drive):
            nonlocal calls
            if str(drive).startswith('D'):
                calls+=1
                return SimpleNamespace(free=(51 if calls==1 else 49)*1024**3)
            return SimpleNamespace(free=100*1024**3)
        with patch('pack_io.shutil.disk_usage',side_effect=disk),self.assertRaisesRegex(ValueError,'D50GiB'):
            hashes(path)


if __name__=='__main__':unittest.main()

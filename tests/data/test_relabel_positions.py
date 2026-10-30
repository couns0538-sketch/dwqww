#!/usr/bin/env python3
"""Synthetic relabel unit fixtures: no native throughput or label-quality evidence.
IDEA_SOURCE: user exact-label/provenance contract and same-project FPOS/FHCE API.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/data'))
import forge_pos as fmt
import relabel_positions as target

FENS = [
    'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 9 20',
    'r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 10 20',
    '4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 21',
    '4k3/8/8/8/8/8/8/R3K3 b - - 42 22',
    '4k3/8/8/8/8/8/8/R3K3 w - - 43 23',
]

class RelabelTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='forge-relabel-unit-'))
        print('retained synthetic fixture ' + str(self.root), file=sys.stderr)
        self.source = self.root / 'input'; self.source.mkdir()
        self.pos = self.source / 'fixture.pos'; self.sidecar = self.source / 'fixture.txt'
        self.probe = self.root / 'fake-probe'; self.probe.write_text('SYNTHETIC - NOT EXECUTED\n')
        lines=[]
        self.records=[]
        with fmt.PosWriter(self.source, 'fixture', with_hce=False) as writer:
            for i,fen in enumerate(FENS):
                score = 10 - i * 7; result = (0, .5, 1, 0, 1)[i]
                line = f'{fen} | {score} | {result}\n'
                record,_=fmt.text_record(line); self.records.append(record)
                writer.append(record, fen=fen); lines.append(line)
        self.sidecar.write_text(''.join(lines))

    def config(self, out='out', **changes):
        c=target.Config(self.pos,self.sidecar,self.root/out,self.probe,nodes=512,count=5,batch_size=2)
        for k,v in changes.items(): setattr(c,k,v)
        return c

    def fake_pool(self, overrides=None, close_error=None):
        overrides=overrides or {}; calls=[]
        class Pool:
            total_child_cpu_seconds=None
            def __init__(self,*args,**kwargs): pass
            def __enter__(self): return self
            def __exit__(self,kind,*args):
                if kind is None and close_error is not None: raise close_error
            def map(self,requests,op='analyze'):
                calls.append((op,list(requests))); answer=[]
                for ident,fen in requests:
                    i=int(ident)
                    row={'id':ident,'ok':True,'operation':op,'fen':fen,'analyzed':True,
                         'terminal':False,'score':100+i,'hce':-30-i,'nodes':512,
                         'nodes_limit':512,'hash_mb':1,'threads':1,'depth':5,'cpu_ns':10,'bestmove':'e1e2'}
                    row.update(overrides.get(i,{})); answer.append(row)
                return answer
        return Pool,calls

    def test_stride_preserves_board_white_result_and_exact_fen(self):
        pool,calls=self.fake_pool()
        result=target.run(self.config(start=1,count=2,stride=2),pool)
        self.assertEqual(result['selected'],2); self.assertEqual(result['exact_label_rows'],2)
        self.assertEqual(result['reconstructed_label_rows'],0)
        self.assertEqual(result['search_nodes'],1024)
        self.assertEqual(result['depth_histogram'],{'5':2})
        with fmt.PosReader(self.root/'out/relabeled.pos',self.root/'out/relabeled.hce') as reader:
            self.assertEqual(reader.n,2)
            for output_i,input_i in enumerate((1,3)):
                row=reader.row(output_i); original=self.records[input_i]
                self.assertEqual((row.board,row.meta),(original.board,original.meta))
                self.assertEqual((row.score,row.hce),(100+input_i,-30-input_i))
        self.assertEqual((self.root/'out/relabeled.fen').read_text().splitlines(),[FENS[1],FENS[3]])
        labels=[json.loads(s) for s in (self.root/'out/labels.jsonl').read_text().splitlines()]
        self.assertEqual([x['input_index'] for x in labels],[1,3])
        self.assertEqual([x['old_score_stm'] for x in labels],[self.records[1].score,self.records[3].score])
        self.assertEqual(calls,[('analyze',[('1',FENS[1]),('3',FENS[3])])])

    def test_sidecar_score_or_result_mismatch_fails_before_native(self):
        for field,value in ((1,'999'),(2,'1')):
            path=self.source/f'mismatch_{field}.txt'
            lines=self.sidecar.read_text().splitlines(); parts=lines[0].split('|'); parts[field]=value
            lines[0]='|'.join(parts); path.write_text('\n'.join(lines)+'\n')
            pool,calls=self.fake_pool()
            with self.assertRaisesRegex(ValueError,'mismatch'):
                target.run(self.config(out=f'bad_{field}',sidecar=path),pool)
            self.assertEqual(calls,[])
            self.assertEqual(json.loads((self.root/f'bad_{field}/failure.json').read_text())['status'],'FAILED_UNSEALED')
            self.assertFalse((self.root/f'bad_{field}/summary.json').exists())

    def test_sidecar_full_count_is_checked_even_for_one_selected_row(self):
        for kind,content in [('short',''.join(self.sidecar.read_text().splitlines(keepends=True)[:-1])),
                             ('long',self.sidecar.read_text()+self.sidecar.read_text().splitlines()[0]+'\n')]:
            path=self.source/f'{kind}.txt'; path.write_text(content); pool,calls=self.fake_pool()
            with self.assertRaisesRegex(ValueError,'sidecar (shorter|longer)'):
                target.run(self.config(out=kind,sidecar=path,count=1),pool)
            self.assertEqual(calls,[])

    def test_reconstruction_requires_explicit_permission_and_never_counts_exact(self):
        pool,calls=self.fake_pool()
        with self.assertRaisesRegex(ValueError,'sidecar required'):
            target.run(self.config(sidecar=None),pool)
        self.assertFalse((self.root/'out').exists())
        result=target.run(self.config(sidecar=None,allow_reconstructed=True,count=2),pool)
        self.assertEqual(result['exact_label_rows'],0)
        self.assertEqual(result['reconstructed_label_rows'],2)
        self.assertEqual(result['state_origin'],'reconstructed_no_castling_no_ep_clock0')
        for _,rows in calls:
            for _,fen in rows: self.assertEqual(fen.split()[2:],['-','-','0','1'])
        labels=[json.loads(s) for s in (self.root/'out/labels.jsonl').read_text().splitlines()]
        self.assertTrue(all(x['state_origin']==result['state_origin'] for x in labels))

    def test_fen_only_sidecar_requires_explicit_origin(self):
        pool,calls=self.fake_pool()
        with self.assertRaisesRegex(ValueError,'origin|provenance'):
            target.run(self.config(sidecar=self.source/'fixture.fen',count=1),pool)
        self.assertEqual(calls,[])
        pool,_=self.fake_pool()
        result=target.run(self.config('explicit_full',sidecar=self.source/'fixture.fen',
                                    sidecar_origin='original_full_fen',count=1),pool)
        self.assertEqual(result['exact_label_rows'],1)
        self.assertEqual(result['reconstructed_label_rows'],0)

    def test_reconstructed_sidecar_cannot_silently_become_exact_on_relabel(self):
        pool,_=self.fake_pool()
        target.run(self.config('reconstructed_first',sidecar=None,allow_reconstructed=True,count=2),pool)
        original=self.root/'reconstructed_first'
        pool,calls=self.fake_pool()
        with self.assertRaisesRegex(ValueError,'origin|provenance'):
            target.run(self.config('ambiguous',pos=original/'relabeled.pos',
                                   sidecar=original/'relabeled.fen',count=2),pool)
        self.assertEqual(calls,[])
        pool,_=self.fake_pool()
        result=target.run(self.config('reconstructed_second',pos=original/'relabeled.pos',
                                    sidecar=original/'relabeled.fen',count=2,
                                    sidecar_origin='reconstructed'),pool)
        self.assertEqual(result['exact_label_rows'],0)
        self.assertEqual(result['reconstructed_label_rows'],2)
        pool,_=self.fake_pool()
        with self.assertRaisesRegex(ValueError,'origin|provenance|reconstruct'):
            target.run(self.config('contradictory',pos=original/'relabeled.pos',
                                   sidecar=original/'relabeled.fen',count=2,
                                   sidecar_origin='original_full_fen'),pool)

    def test_invalid_native_responses_do_not_seal(self):
        changes=[{'id':'999'}, {'ok':False}, {'terminal':True}, {'depth':0},
                 {'score':32768}, {'hce':-32768}, {'score':True},
                 {'nodes':-1}, {'nodes':513}, {'cpu_ns':-1}, {'analyzed':False},
                 {'fen':FENS[1]}, {'nodes_limit':1024}, {'hash_mb':2}, {'threads':2}]
        for i,change in enumerate(changes):
            with self.subTest(change=change):
                pool,_=self.fake_pool({0:change})
                with self.assertRaises(ValueError): target.run(self.config(out=f'invalid_{i}',count=1),pool)
                self.assertFalse((self.root/f'invalid_{i}/relabeled.pos').exists())
                self.assertFalse((self.root/f'invalid_{i}/summary.json').exists())
                self.assertEqual(json.loads((self.root/f'invalid_{i}/failure.json').read_text())['status'],'FAILED_UNSEALED')

    def test_nonzero_probe_shutdown_leaves_rows_unsealed(self):
        pool,_=self.fake_pool(close_error=RuntimeError('fake child failed on EOF'))
        with self.assertRaisesRegex(RuntimeError,'fake child failed'):
            target.run(self.config(count=1),pool)
        self.assertFalse((self.root/'out/relabeled.pos').exists())
        self.assertFalse((self.root/'out/summary.json').exists())
        self.assertTrue((self.root/'out/labels.jsonl').exists())

    def test_worker_batch_choices_preserve_bytes_and_overwrite_is_rejected(self):
        for name,workers,batch in [('single',1,1),('three',3,4)]:
            pool,_=self.fake_pool(); target.run(self.config(name,workers=workers,batch_size=batch),pool)
        for suffix in ('.pos','.hce','.fen'):
            self.assertEqual((self.root/('single/relabeled'+suffix)).read_bytes(),(self.root/('three/relabeled'+suffix)).read_bytes())
        pool,_=self.fake_pool()
        with self.assertRaises(FileExistsError): target.run(self.config('single'),pool)

    def test_slice_bounds_fail_without_probe_queries(self):
        pool,calls=self.fake_pool()
        with self.assertRaisesRegex(ValueError,'slice extends'):
            target.run(self.config(start=4,count=2),pool)
        self.assertEqual(calls,[])

if __name__=='__main__': unittest.main()

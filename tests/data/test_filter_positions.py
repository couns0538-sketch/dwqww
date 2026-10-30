#!/usr/bin/env python3
"""Synthetic unit fixtures only; not measured native data/engine evidence.
IDEA_SOURCE: user data-integrity contract and the original filter implementation.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/data'))
import filter_positions as target

@dataclass
class R:
    board: bytes
    score: int
    meta: int
    hce: int | None = None


def packed(pieces):
    value = bytearray(32)
    for square, piece in pieces.items(): value[square//2] |= piece << (4*(square%2))
    return bytes(value)


class PolicyTests(unittest.TestCase):
    def test_disagreement_respects_stm_and_white_result(self):
        board = bytes(32)
        # Black won: a positive score for Black agrees, a negative one disagrees.
        self.assertFalse(target.disagreement(R(board, 500, 1), 400, 800))
        self.assertTrue(target.disagreement(R(board, -400, 1), 400, 800))
        self.assertTrue(target.disagreement(R(board, 400, 5), 400, 800))
        self.assertFalse(target.disagreement(R(board, 799, 2), 400, 800))
        self.assertTrue(target.disagreement(R(board, -800, 3), 400, 800))

    def test_exact_identity_excludes_label_but_includes_stm(self):
        a = R(bytes(32), 1, 0); b = R(bytes(32), -200, 4)
        self.assertEqual(target.fingerprint(a), target.fingerprint(b))
        self.assertNotEqual(target.fingerprint(a), target.fingerprint(R(bytes(32), 1, 1)))

    def test_near_uses_kept_only_original_row_window_and_full_policy(self):
        a = R(packed({4:6, 60:12, 1:2, 8:1}), 25, 2)
        b = R(packed({4:6, 60:12, 18:2, 8:1}), 50, 2)
        fen = '4k3/8/8/8/8/8/P7/1N2K3 w - - 0 1'
        near = target.NearIndex(64, 25)
        self.assertFalse(near.contains(1, b, fen))
        near.add(0, a, fen)
        self.assertTrue(near.contains(64, b, fen))
        self.assertFalse(near.contains(65, b, fen))
        self.assertFalse(near.contains(1, R(b.board, 51, 2), fen))
        self.assertFalse(near.contains(1, R(b.board, 50, 4), fen))
        self.assertFalse(near.contains(1, b, fen.replace(' w - -', ' w K -')))
        pawn_changed = R(packed({4:6, 60:12, 1:2, 16:1}), 25, 2)
        self.assertFalse(near.contains(1, pawn_changed, fen))

    def test_exact_index_checks_collisions(self):
        temporary = tempfile.mkdtemp(prefix='forge-filter-index-test-')
        index = target.ExactIndex(Path(temporary)/'index.sqlite')
        key = bytes(33); index.add('kept', key)
        self.assertTrue(index.contains('kept', key))
        index.db.execute('UPDATE kept SET key=?', (bytes([1])+bytes(32),))
        with self.assertRaisesRegex(ValueError, 'collision'): index.contains('kept', key)
        index.close()
        print('retained synthetic fixture '+temporary, file=sys.stderr)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        try:
            import forge_pos
        except ImportError:
            self.skipTest('shared format module not yet materialized')
        self.io = forge_pos
        self.root = Path(tempfile.mkdtemp(prefix='forge-filter-test-'))
        print('retained synthetic fixture '+str(self.root), file=sys.stderr)
        self.source = self.root/'source'; self.source.mkdir()

    def make_input(self, rows):
        # Real record format, synthetic documented fixture positions/scores/results.
        writer = self.io.PosWriter(self.source, 'fixture', with_hce=True)
        lines=[]
        for fen, score, result in rows:
            record, canonical_fen = self.io.text_record(f'{fen} | {score} | {result}')
            writer.append(self.io.Record(record.board, score, record.meta, 7), fen=canonical_fen)
            lines.append(f'{fen} | {score} | {result}\n')
        writer.close()
        sidecar=self.source/'fixture.txt'; sidecar.write_text(''.join(lines))
        return self.source/'fixture.pos',sidecar

    @staticmethod
    def fake_pool(responses):
        class Pool:
            def __init__(self,*args,**kwargs): self.calls=[]
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def map(self,requests,op='filter'):
                output=[]
                for identifier,fen in requests:
                    record={'id':identifier,'ok':True,'in_check':False,'terminal':False,'analyzed':True,
                            'hce':11,'depth':4,'nodes':1024,'cpu_ns':10,'score':18,'bestmove':'a1a2',
                            'capture':False,'promotion':False}
                    record.update(responses.get(int(identifier),{}));output.append(record)
                return output
        return Pool

    def config(self, paths, out='out', **changes):
        probe=self.root/'fake-probe'
        if not probe.exists():probe.write_text('SYNTHETIC UNIT FIXTURE - NEVER EXECUTED\n')
        config=target.Config([paths[0]],[paths[1]],self.root/out,probe,near_window=0)
        for name,value in changes.items(): setattr(config,name,value)
        return config

    def test_batch_duplicates_depend_only_on_previously_kept_rows(self):
        fen='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
        paths=self.make_input([(fen,10,.5),(fen,10,.5),(fen,10,.5)])
        summary=target.run(self.config(paths), self.fake_pool({0:{'capture':True}}))
        self.assertEqual(summary['kept'],1)
        self.assertEqual(summary['rules']['bestmove_capture']['dropped'],1)
        self.assertEqual(summary['rules']['exact_duplicate']['dropped'],1)
        self.assertEqual(summary['speculative_native_queries_not_used'],1)
        self.assertEqual(summary['native_queries'],3)
        with self.io.PosReader(self.root/'out/forge_filtered.pos',self.root/'out/forge_filtered.hce') as reader:
            self.assertEqual(reader.n,1);self.assertEqual(reader.row(0).hce,11)

    def test_count_and_alignment_failure_remains_unsealed(self):
        fen='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
        paths=self.make_input([(fen,10,.5)])
        paths[1].write_text(f'{fen} | 11 | 0.5\n')
        with self.assertRaisesRegex(ValueError,'mismatch'):target.run(self.config(paths),self.fake_pool({}))
        self.assertEqual(json.loads((self.root/'out/failure.json').read_text())['status'],'FAILED_UNSEALED')
        self.assertFalse((self.root/'out/summary.json').exists())

    def test_holdout_and_ordered_rules(self):
        a='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
        b='4k3/8/8/8/8/8/8/1R2K3 w - - 0 1'
        c='4k3/8/8/8/8/8/8/2R1K3 w - - 0 1'
        paths=self.make_input([(a,10,.5),(b,500,0),(c,10,.5)])
        hold=self.root/'holdout.txt';hold.write_text(f'{a} | 10 | 0.5\n')
        summary=target.run(self.config(paths,holdouts=[hold]),self.fake_pool({2:{'in_check':True,'analyzed':False}}))
        self.assertEqual(summary['kept'],0)
        self.assertEqual(summary['rules']['holdout']['dropped'],1)
        self.assertEqual(summary['rules']['disagreement']['dropped'],1)
        self.assertEqual(summary['rules']['in_check']['dropped'],1)
        self.assertEqual(summary['rules']['in_check']['eligible'],1)
        self.assertEqual(summary['supplied_holdout_position_overlap'],0)
        self.assertEqual((self.root/'out/forge_filtered.fen').read_bytes(),b'')
        self.assertEqual(summary['shards'][0]['rules'],summary['rules'])

    def test_worker_count_does_not_change_kept_bytes_and_overwrite_rejected(self):
        a='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
        b='4k3/8/8/8/8/8/8/1R2K3 w - - 0 1'
        paths=self.make_input([(a,10,.5),(b,10,.5)])
        target.run(self.config(paths,'one',workers=1),self.fake_pool({}))
        target.run(self.config(paths,'three',workers=3),self.fake_pool({}))
        for suffix in ('.pos','.hce','.fen'):
            self.assertEqual((self.root/('one/forge_filtered'+suffix)).read_bytes(),(self.root/('three/forge_filtered'+suffix)).read_bytes())
        with self.assertRaises(FileExistsError):target.run(self.config(paths,'one'),self.fake_pool({}))

    def test_promotion_and_terminal_are_separate_drop_reasons(self):
        a='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
        b='4k3/8/8/8/8/8/8/1R2K3 w - - 0 1'
        paths=self.make_input([(a,10,.5),(b,10,.5)])
        summary=target.run(self.config(paths),self.fake_pool({
            0:{'promotion':True,'bestmove':'a7a8q'},1:{'terminal':True,'analyzed':False}}))
        self.assertEqual(summary['kept'],0)
        self.assertEqual(summary['rules']['terminal']['dropped'],1)
        self.assertEqual(summary['rules']['bestmove_promotion']['dropped'],1)
        self.assertEqual(summary['rules']['bestmove_promotion']['eligible'],1)

    def test_prefix_scope_counts_remaining_lines_but_does_not_claim_alignment(self):
        fen='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
        paths=self.make_input([(fen,10,.5),(fen,10,.5)])
        # The unselected second row is deliberately mismatched: this is a prefix check.
        paths[1].write_text(f'{fen} | 10 | 0.5\n{fen} | 11 | 0.5\n')
        summary=target.run(self.config(paths,limit=1),self.fake_pool({}))
        self.assertEqual(summary['input_rows'],1)
        alignment=summary['source_alignment'][0]
        self.assertEqual(alignment['record_matches_verified'],1)
        self.assertEqual(alignment['sidecar_rows'],2)
        self.assertEqual(alignment['scope'],'selected_prefix_only_other_rows_counted_not_decoded')
        paths[1].write_text(paths[1].read_text()+f'{fen} | 10 | 0.5\n')
        with self.assertRaisesRegex(ValueError,'more rows'):
            target.run(self.config(paths,'bad-count',limit=1),self.fake_pool({}))

    def test_incomplete_search_or_invalid_move_aborts(self):
        fen='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
        paths=self.make_input([(fen,10,.5)])
        for index,response in enumerate(({'depth':0},{'bestmove':'0000'})):
            with self.subTest(response=response):
                with self.assertRaisesRegex(ValueError,'teacher iteration|native bestmove'):
                    target.run(self.config(paths,'incomplete-'+str(index)),self.fake_pool({0:response}))
                self.assertFalse((self.root/('incomplete-'+str(index))/'summary.json').exists())

    def test_kept_near_policy_is_batch_size_invariant(self):
        a='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
        b='4k3/8/8/8/8/8/8/1R2K3 w - - 0 1'
        c='4k3/8/8/8/8/8/8/2R1K3 w - - 0 1'
        paths=self.make_input([(a,10,.5),(b,10,.5),(c,10,.5),(b,10,.5)])
        summaries=[]
        for batch in (1,256):
            summaries.append(target.run(self.config(paths,'batch-'+str(batch),batch_size=batch,near_window=2),
                                        self.fake_pool({0:{'capture':True}})))
        self.assertEqual(summaries[0]['rules'],summaries[1]['rules'])
        self.assertEqual(summaries[0]['kept'],1)
        for suffix in ('.pos','.hce','.fen'):
            self.assertEqual((self.root/('batch-1/forge_filtered'+suffix)).read_bytes(),
                             (self.root/('batch-256/forge_filtered'+suffix)).read_bytes())

    def test_native_error_is_not_a_drop_and_retains_failure(self):
        fen='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'
        paths=self.make_input([(fen,10,.5)])
        with self.assertRaisesRegex(ValueError,'native failure'):
            target.run(self.config(paths),self.fake_pool({0:{'ok':False,'error':'invalid native board'}}))
        failure=json.loads((self.root/'out/failure.json').read_text())
        self.assertEqual(failure['status'],'FAILED_UNSEALED')
        self.assertEqual(sum(row['dropped'] for row in failure['rules'].values()),0)

if __name__=='__main__':unittest.main()

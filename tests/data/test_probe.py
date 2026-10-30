#!/usr/bin/env python3
"""Native protocol/legality regressions for the offline Forge probe.
IDEA_SOURCE: user data-label integrity requirements and Forge public API contract.
No match, training, strength or cross-machine speed claims.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import unittest

START='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
KIWI='r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
CONFIG=None
COUNTER=0

def run(lines=(), extra=()):
    global COUNTER
    COUNTER+=1
    stem=CONFIG.evidence/f'case_{COUNTER:03d}'
    command=[str(CONFIG.probe),'--nodes','2048',*extra]
    data=''.join(x+'\n' for x in lines).encode()
    stem.with_suffix('.stdin').write_bytes(data)
    stem.with_suffix('.command.json').write_text(json.dumps(command)+'\n')
    p=subprocess.run(command,input=data,capture_output=True,timeout=30)
    stem.with_suffix('.stdout').write_bytes(p.stdout)
    stem.with_suffix('.stderr').write_bytes(p.stderr)
    stem.with_suffix('.exit').write_text(str(p.returncode)+'\n')
    return p

def query(rows):
    p=run([f'{i}\t{op}\t{fen}' for i,(op,fen) in enumerate(rows)])
    if p.returncode:raise AssertionError((p.returncode,p.stderr))
    result=[json.loads(x) for x in p.stdout.splitlines()]
    if len(result)!=len(rows):raise AssertionError('one JSON response required per row')
    for i,item in enumerate(result):
        if item['id']!=str(i) or item['operation']!=rows[i][0]:raise AssertionError('request association mismatch')
    return result

class ProbeTests(unittest.TestCase):
    def test_inspect_start_and_kiwipete(self):
        a,b=query([('inspect',START),('inspect',KIWI)])
        self.assertTrue(a['ok']);self.assertTrue(b['ok'])
        self.assertEqual(len(a['moves']),20);self.assertEqual(len(b['moves']),48)
        self.assertEqual(a['fen'],START);self.assertFalse(a['analyzed'])
        self.assertEqual(len({x['uci'] for x in a['moves']}),20)
        self.assertIn('e2e4',{x['uci'] for x in a['moves']})
        for move in a['moves']:
            self.assertFalse(move['capture']);self.assertFalse(move['promotion'])
            self.assertEqual(move['fen'].split()[1],'b')
        self.assertIsInstance(a['hce'],int)

    def test_special_move_flags(self):
        ep='7k/8/8/3pP3/8/8/8/K7 w - d6 0 1'
        promotion='7k/P7/6K1/8/8/8/8/8 w - - 0 1'
        a,b=query([('inspect',ep),('inspect',promotion)])
        self.assertTrue(a['ok']);self.assertTrue(b['ok'])
        move=next(x for x in a['moves'] if x['uci']=='e5d6')
        self.assertTrue(move['capture']);self.assertFalse(move['promotion'])
        promoted=[x for x in b['moves'] if x['uci'].startswith('a7a8')]
        self.assertEqual({x['uci'][-1] for x in promoted},set('qrbn'))
        self.assertTrue(all(x['promotion'] and not x['capture'] for x in promoted))

    def test_filter_skips_checked_and_terminal_roots(self):
        check='4k3/8/8/8/8/8/4r3/4K3 w - - 0 1'
        mate='7k/6Q1/5K2/8/8/8/8/8 b - - 0 1'
        stale='7k/5Q2/6K1/8/8/8/8/8 b - - 0 1'
        a,b,c=query([('filter',check),('filter',mate),('analyze',stale)])
        self.assertTrue(a['in_check']);self.assertFalse(a['terminal'])
        self.assertEqual(b['terminal_reason'],'checkmate')
        self.assertEqual(c['terminal_reason'],'stalemate')
        for item in [a,b,c]:
            self.assertTrue(item['ok']);self.assertFalse(item['analyzed'])
            self.assertIsNone(item['bestmove']);self.assertIsNone(item['score'])
            self.assertEqual(item['nodes'],0)

    def test_capture_analysis_and_accounting(self):
        capture='q3k3/8/8/8/8/8/8/R3K3 w Q - 0 1'
        item=query([('analyze',capture)])[0]
        self.assertTrue(item['ok']);self.assertTrue(item['analyzed'])
        self.assertTrue(item['capture']);self.assertFalse(item['promotion'])
        self.assertGreater(item['depth'],0);self.assertGreater(item['nodes'],0)
        self.assertLessEqual(item['nodes'],item['nodes_limit'])
        self.assertGreaterEqual(item['process_cpu_ns'],item['cpu_ns'])
        self.assertGreaterEqual(item['cpu_ns'],0);self.assertGreater(item['elapsed_ns'],0)
        self.assertEqual(item['threads'],1)

    def test_cold_independent_of_input_order(self):
        a,b,c=query([('analyze',START),('analyze',KIWI),('analyze',START)])
        self.assertTrue(all(x['ok'] for x in [a,b,c]))
        fields=['fen','in_check','terminal','hce','bestmove','capture','promotion','score','nodes','depth']
        self.assertEqual({k:a[k] for k in fields},{k:c[k] for k in fields})
        self.assertLessEqual(a['nodes'],2048)

    def test_real_quiescence_root_can_exhaust_budget_before_depth_one(self):
        # Original 10M filter input row 27772. The 1024-node budget is consumed
        # by a legal, non-check root's first iteration, not a malformed position.
        fen='r1bq2k1/pp3r1p/3b1n2/P2p1Np1/5p2/3Q2P1/1BP1PPBP/R4RK1 b - - 8 21'
        p=run(['27772\tfilter\t'+fen,'next\tanalyze\t'+START],extra=('--nodes','1024'))
        self.assertEqual(p.returncode,0)
        a,b=[json.loads(x) for x in p.stdout.splitlines()]
        self.assertTrue(a['ok']);self.assertFalse(a['terminal']);self.assertFalse(a['in_check'])
        self.assertFalse(a['analyzed']);self.assertEqual(a['analysis_status'],'insufficient_budget')
        self.assertEqual(a['depth'],0);self.assertEqual(a['nodes'],1024)
        self.assertIsNone(a['score']);self.assertIsNone(a['bestmove'])
        self.assertTrue(b['ok']);self.assertTrue(b['analyzed'])

    def test_invalid_roots_and_recovery(self):
        invalid=['nonsense','8/8/8/8/8/8/8/Kk6 w - - 0 1',
                 '4k3/8/8/8/8/8/8/4K3 w K - 0 1',
                 START.rsplit(' ',2)[0]+' 65536 1',
                 START+' extra']
        rows=query([('inspect',x) for x in invalid]+[('inspect',START)])
        for item in rows[:-1]:self.assertFalse(item['ok']);self.assertIn('error',item)
        self.assertTrue(rows[-1]['ok'])

    def test_oversized_and_malformed_protocol_recovers(self):
        p=run(['long\tinspect\t'+'x'*5000,'broken','ok\tinspect\t'+START])
        self.assertEqual(p.returncode,0)
        rows=[json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual(len(rows),3);self.assertFalse(rows[0]['ok']);self.assertFalse(rows[1]['ok'])
        self.assertTrue(rows[2]['ok']);self.assertEqual(rows[2]['id'],'ok')
        self.assertIn('4096',rows[0]['error'])

    def test_invalid_config_rejected(self):
        for args in [('--nodes','0'),('--nodes','-1'),('--hash-mb','0'),('--max-depth','65'),('--unknown','1')]:
            with self.subTest(args=args):
                p=run(extra=args);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'')
        p=run(extra=('--version',));self.assertEqual(p.returncode,0)
        self.assertEqual(json.loads(p.stdout)['protocol'],'forge-data-probe-v1')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--probe',type=pathlib.Path,required=True);p.add_argument('--evidence',type=pathlib.Path,required=True)
    CONFIG=p.parse_args();CONFIG.probe=CONFIG.probe.resolve();CONFIG.evidence.mkdir(parents=True,exist_ok=False)
    (CONFIG.evidence/'probe_sha256.txt').write_text(hashlib.sha256(CONFIG.probe.read_bytes()).hexdigest()+'\n')
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ProbeTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (CONFIG.evidence/'summary.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'native':True,'purpose':'protocol, classification and cold-search integrity only'},indent=2)+'\n')
    (CONFIG.evidence/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in sorted(CONFIG.evidence.iterdir()) if f.is_file() and f.name!='SHA256SUMS.txt'))
    raise SystemExit(not result.wasSuccessful())

#!/usr/bin/env python3
"""Real IPC against synthetic Python children; not Forge performance evidence.
IDEA_SOURCE: same-project probe framing and checkpoint-integrity requirements.
"""
from __future__ import annotations
import gzip
import json
import os
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/data'))
from forge_probe import ProbeClient, ProbeError, ProbePool

FEN='4k3/8/8/8/8/8/8/R3K3 w - - 0 1'

@unittest.skipUnless(os.name=='posix','synthetic executable fixtures require POSIX shebang execution')
class ProbeClientTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='forge-probe-client-unit-'))
        print('retained synthetic fixture '+str(self.root),file=sys.stderr)

    def executable(self,mode='normal'):
        script=self.root/(mode+'.py')
        script.write_text('#!'+sys.executable+'\n'+textwrap.dedent('''\
            import json,sys,time
            mode=MODE
            for line in sys.stdin:
                ident,op,fen=line.rstrip('\\n').split('\\t')
                if mode=='timeout': time.sleep(10)
                if mode=='overlong':
                    sys.stdout.write('x'*131073+'\\n');sys.stdout.flush();continue
                if mode=='invalid_json':
                    sys.stdout.write('{no json}\\n');sys.stdout.flush();continue
                if mode=='incomplete':
                    sys.stdout.write('{}');sys.stdout.flush();break
                if mode=='ordered' and int(ident)%3==0:time.sleep(.02)
                result={'id':ident,'operation':op,'ok':True,'cpu_ns':7,'fen':fen}
                if mode=='wrong_id':result['id']='wrong'
                if mode=='wrong_operation':result['operation']='inspect'
                print(json.dumps(result),flush=True)
                if mode=='extra':print(json.dumps(result),flush=True)
            sys.exit(7 if mode=='nonzero' else 0)
            ''').replace('MODE',repr(mode)))
        script.chmod(0o700)
        return script

    def test_roundtrip_retains_original_ipc_and_process_receipt(self):
        directory=self.root/'receipt'
        with ProbeClient(self.executable(),64,workdir=directory) as client:
            a=client.query(FEN,'analyze','row-7')
            self.assertEqual(a['fen'],FEN)
            self.assertEqual(client.count,1);self.assertEqual(client.cpu_ns,7)
        self.assertEqual(gzip.open(directory/'requests.tsv.gz','rt').read(),f'row-7\tanalyze\t{FEN}\n')
        response=json.loads(gzip.open(directory/'responses.jsonl.gz','rt').read())
        self.assertEqual(response['id'],'row-7')
        receipt=json.loads((directory/'process.json').read_text())
        self.assertEqual(receipt['returncode'],0)
        self.assertTrue(receipt['binary_unchanged'])
        self.assertEqual(receipt['successful_requests'],receipt['response_count'])

    def test_id_operation_json_and_frame_corruption_are_rejected(self):
        for mode in ('wrong_id','wrong_operation','invalid_json','overlong','incomplete'):
            with self.subTest(mode=mode):
                client=ProbeClient(self.executable(mode),64,workdir=self.root/mode)
                try:
                    with self.assertRaises(ProbeError):client.query(FEN,'analyze','row-1')
                finally:client.close(raise_on_error=False)
                self.assertTrue((self.root/mode/'process.json').exists())

    def test_nonzero_child_exit_fails_successful_context(self):
        directory=self.root/'nonzero_logs'
        with self.assertRaisesRegex(ProbeError,'shutdown'):
            with ProbeClient(self.executable('nonzero'),64,workdir=directory) as client:
                self.assertTrue(client.query(FEN)['ok'])
        self.assertEqual(json.loads((directory/'process.json').read_text())['returncode'],7)

    def test_changed_executable_is_detected_on_close(self):
        exe=self.executable();directory=self.root/'changed'
        client=ProbeClient(exe,64,workdir=directory)
        client.query(FEN)
        with exe.open('a') as file:file.write('# synthetic mutation for identity test\n')
        with self.assertRaisesRegex(ProbeError,'identity'):client.close()
        self.assertFalse(json.loads((directory/'process.json').read_text())['binary_unchanged'])

    def test_extra_response_fails_even_when_first_query_succeeds(self):
        with self.assertRaisesRegex(ProbeError,'response-count'):
            with ProbeClient(self.executable('extra'),64,workdir=self.root/'extra_logs') as client:
                self.assertTrue(client.query(FEN)['ok'])

    def test_timeout_terminates_only_owned_child_and_retains_receipt(self):
        client=ProbeClient(self.executable('timeout'),64,workdir=self.root/'timeout_logs',timeout=.1)
        try:
            with self.assertRaisesRegex(ProbeError,'owned child'):client.query(FEN)
        finally:client.close(raise_on_error=False)
        self.assertIsNotNone(client.process.poll())
        self.assertTrue((self.root/'timeout_logs/process.json').exists())

    def test_pool_returns_input_order_independent_of_worker_completion(self):
        items=[(str(i),FEN) for i in range(11)]
        with ProbePool(self.executable('ordered'),64,workers=3,workdir=self.root/'pool') as pool:
            self.assertEqual([x['id'] for x in pool.map(items,op='analyze')],[str(i) for i in range(11)])
            self.assertEqual(pool.map([],op='analyze'),[])
        for i in range(3):
            receipt=json.loads((self.root/f'pool/worker-{i}/process.json').read_text())
            self.assertEqual(receipt['successful_requests'],len(items[i::3]))
            self.assertEqual(receipt['returncode'],0)

    def test_invalid_framing_is_rejected_without_sending(self):
        with ProbeClient(self.executable(),64,workdir=self.root/'framing') as client:
            for fen in (FEN+'\n',FEN+'\t','x'*513):
                with self.assertRaises(ValueError):client.query(fen)
            with self.assertRaises(ValueError):client.query(FEN,request_id='space not allowed')
            self.assertEqual(client.count,0)

if __name__=='__main__':unittest.main()

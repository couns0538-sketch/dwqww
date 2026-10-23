"""Independent external-teacher protocol and whole-game publication contracts."""
from __future__ import annotations
import gzip
import importlib
import json
import os
import signal
import shutil
import subprocess
import time
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chess

WHITE = chess.STARTING_FEN
board = chess.Board(); board.push_uci('e2e4'); BLACK = board.fen()


class TeacherLabelTests(unittest.TestCase):
    def setUp(self):
        try:
            self.tool = importlib.import_module('label_teacher_games')
        except ModuleNotFoundError:
            self.tool = None
        self.assertIsNotNone(self.tool, 'Independent-teacher labeler is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def engine(self, response=None):
        response = response or "print('info depth 6 seldepth 8 multipv 1 score cp 31 nodes 123 time 2 pv e2e4'); print('bestmove e2e4')"
        path = self.directory / ('engine-%d.py' % len(list(self.directory.glob('engine*'))))
        path.write_text('import sys,time\nfor line in sys.stdin:\n s=line.strip()\n if s=="uci":\n  print("id name Test teacher"); print("id author Test")\n  for name in ["Threads","Hash","MultiPV","Ponder","Skill Level","UCI_LimitStrength","UCI_Chess960","SyzygyPath","Clear Hash"]: print("option name "+name+" type string default test")\n  print("uciok")\n elif s=="isready": print("readyok")\n elif s.startswith("go "):\n  '+response+'\n elif s=="quit": break\n sys.stdout.flush()\n')
        trace = self.tool.Transcript(self.directory / ('trace-%d' % len(list(self.directory.glob('trace*')))), rotate_bytes=1024)
        engine = self.tool.Teacher([sys.executable, str(path)], trace, worker_id=0, depth=6, timeout=2.0)
        self.addCleanup(trace.close)
        self.addCleanup(engine.close)
        return engine, trace

    def game(self, identity='g1', split='train', fen=WHITE):
        return {'game_id':identity, 'game_index':1, 'split':split, 'result_white':1.0,
                'initial_fen':fen, 'moves':['e7e5' if fen==BLACK else 'e2e4'] if fen in (WHITE,BLACK) else [], 'samples':[{'game_id':identity,'split':split,
                'fen':fen,'ply':0,'bestmove':'e2e4','score_cp_stm':-333}]}

    def test_external_cp_replaces_forge_label_and_stays_in_stm_pov(self):
        engine, trace = self.engine()
        game, counts = self.tool.label_game(self.game(), engine)
        sample = game['samples'][0]
        self.assertEqual(sample['teacher_cp_stm'], 31)
        self.assertEqual(sample['score_cp_stm'], 31)
        self.assertEqual(sample['forge_score_cp_stm'], -333)
        self.assertEqual((sample['teacher_depth'],sample['teacher_nodes'],sample['teacher_time_ms']), (6,123,2))
        self.assertEqual(counts['accepted'], 1)
        engine.close(); trace.close()
        lines = [json.loads(x) for file in sorted(trace.directory.glob('*.gz')) for x in gzip.open(file,'rt')]
        commands = [x['line'] for x in lines if x['direction']=='in']
        self.assertLess(commands.index('ucinewgame'), commands.index('go depth 6'))
        self.assertIn('setoption name Clear Hash', commands)
        self.assertIn('setoption name UCI_LimitStrength value false', commands)

    def test_black_to_move_score_is_not_negated(self):
        engine, _ = self.engine("print('info depth 6 multipv 1 score cp -42 nodes 80 time 1 pv e7e5'); print('bestmove e7e5')")
        game, _ = self.tool.label_game(self.game(fen=BLACK), engine)
        self.assertEqual(game['samples'][0]['teacher_cp_stm'], -42)

    def test_all_mates_and_out_of_cap_are_counted_and_games_retained(self):
        for kind,value,reason in [('mate',3,'mate'),('mate',-4,'mate'),('mate',0,'mate'),('cp',1001,'score_cap'),('cp',-1001,'score_cap')]:
            with self.subTest(kind=kind,value=value):
                engine, _ = self.engine("print('info depth 6 multipv 1 score %s %d nodes 80 time 1 pv e2e4'); print('bestmove e2e4')" % (kind,value))
                game, counts = self.tool.label_game(self.game(), engine)
                self.assertEqual(game['game_id'], 'g1'); self.assertEqual(game['samples'], [])
                self.assertEqual(counts[reason], 1)
                engine.close()

    def test_score_cap_is_inclusive(self):
        for value in [-1000,1000]:
            engine, _ = self.engine("print('info depth 6 multipv 1 score cp %d nodes 80 time 1 pv e2e4'); print('bestmove e2e4')" % value)
            game,_ = self.tool.label_game(self.game(),engine)
            self.assertEqual(game['samples'][0]['teacher_cp_stm'],value); engine.close()

    def test_bound_shallow_stale_missing_illegal_and_duplicate_results_fail_closed(self):
        responses = [
            "print('info depth 6 multipv 1 score cp 31 lowerbound nodes 80 time 1 pv e2e4'); print('bestmove e2e4')",
            "print('info depth 5 multipv 1 score cp 31 nodes 80 time 1 pv e2e4'); print('bestmove e2e4')",
            "print('info depth 6 multipv 1 score cp 31 nodes 80 time 1 pv e2e4'); print('info depth 6 multipv 1 score cp 32 upperbound nodes 81 time 2 pv e2e4'); print('bestmove e2e4')",
            "print('bestmove e2e4')",
            "print('info depth 6 multipv 1 score cp 31 nodes 80 time 1 pv e2e5'); print('bestmove e2e5')",
            "print('info depth 6 multipv 1 score cp 31 nodes 80 time 1 pv d2d4'); print('bestmove e2e4')",
            "print('info depth 6 multipv 1 score cp 31 nodes 80 time 1 pv e2e4'); print('bestmove e2e4'); print('bestmove d2d4')",
            "sys.exit(3)", "time.sleep(5)",
        ]
        for response in responses:
            with self.subTest(response=response):
                engine,_ = self.engine(response)
                with self.assertRaises(self.tool.ProtocolError): self.tool.label_game(self.game(),engine)
                engine.close(); self.assertIsNotNone(engine.process.poll())

    def test_teacher_quiet_filter_checks_capture_promotion_and_check(self):
        cases = [
            ('4k3/8/8/8/8/8/4p3/4K3 w - - 0 1','e1e2','capture'),
            ('4k3/P7/8/8/8/8/8/4K3 w - - 0 1','a7a8n','promotion'),
            ('4k3/8/8/8/8/8/8/4K2R w - - 0 1','h1h8','gives_check')]
        for fen,move,reason in cases:
            with self.subTest(reason=reason):
                engine,_=self.engine("print('info depth 6 multipv 1 score cp 1 nodes 80 time 1 pv %s'); print('bestmove %s')" % (move,move))
                game,counts=self.tool.label_game(self.game(fen=fen),engine)
                self.assertEqual(game['samples'],[]);self.assertEqual(counts[reason],1);engine.close()

    def test_reject_sample_split_mismatch_before_search(self):
        engine,_=self.engine();game=self.game();game['samples'][0]['split']='audit'
        with self.assertRaisesRegex(ValueError,'split'):self.tool.label_game(game,engine)

    def test_atomic_chunk_hashes_counts_disjoint_games_and_failures(self):
        engine,trace=self.engine()
        source=self.directory/'games.jsonl.gz'
        with gzip.open(source,'wt') as handle:
            for identity,split in [('g1','train'),('g2','audit')]:handle.write(json.dumps(self.game(identity,split))+'\n')
        out=self.directory/'chunks'
        meta=self.tool.label_chunk(source,out,engine,seen_games={})
        destination=out/meta['path']
        self.assertTrue(destination.is_file());self.assertEqual(self.tool.sha256(destination),meta['sha256'])
        self.assertEqual(meta['games'],2);self.assertEqual(meta['accepted'],2)
        self.assertEqual(meta['game_ids'],['g1','g2']);self.assertEqual(meta['split_games'],{'train':1,'audit':1})
        duplicate=self.directory/'duplicate.jsonl.gz'; duplicate.write_bytes(source.read_bytes())
        with self.assertRaisesRegex(ValueError,'duplicate'):self.tool.label_chunk(duplicate,out,engine,seen_games={'g1':'train'})
        self.assertEqual(len(list(out.glob('chunk-*'))),1)
        bad,_=self.engine("print('bestmove e2e4')")
        empty=self.directory/'failed'
        with self.assertRaises(self.tool.ProtocolError):self.tool.label_chunk(source,empty,bad,seen_games={})
        self.assertEqual(list(empty.glob('chunk-*')),[])

    def test_completed_game_null_move_is_rejected(self):
        engine,_=self.engine();game=self.game();game['moves']=['0000']
        with self.assertRaisesRegex(ValueError,'illegal completed game move'):
            self.tool.label_game(game,engine)

    def test_resume_rejects_changed_original_transcript(self):
        engine,_=self.engine();script=Path(engine.process.args[1]);engine.close()
        script.write_text('#!'+sys.executable+'\n'+script.read_text());script.chmod(0o700)
        incoming=self.directory/'incoming';incoming.mkdir()
        with gzip.open(incoming/'games.jsonl.gz','wt') as stream:
            stream.write(json.dumps(self.game())+'\n')
        output=self.directory/'output'
        arguments=['--input-dir',str(incoming),'--output-dir',str(output),
                   '--teacher',str(script),'--depth','6','--workers','1']
        self.tool.main(arguments)
        manifest=json.loads((output/'manifest.json').read_text())
        session=manifest['transcript_sessions'][0]
        segment=output/session['directory']/session['segments'][0]['path']
        segment.write_bytes(segment.read_bytes()+b'corruption')
        with self.assertRaisesRegex(ValueError,'transcript'):
            self.tool.main(arguments)

    def test_interrupt_stops_owned_teacher_without_committing_active_game(self):
        marker=self.directory/'teacher.pid'
        response="__import__('pathlib').Path("+repr(str(marker))+").write_text(str(__import__('os').getpid())); time.sleep(60)"
        engine,_=self.engine(response);script=Path(engine.process.args[1]);engine.close()
        script.write_text('#!'+sys.executable+'\n'+script.read_text());script.chmod(0o700)
        incoming=self.directory/'incoming';incoming.mkdir()
        with gzip.open(incoming/'games.jsonl.gz','wt') as stream:stream.write(json.dumps(self.game())+'\n')
        output=self.directory/'output'
        process=subprocess.Popen([sys.executable,str(Path(self.tool.__file__)),
            '--input-dir',str(incoming),'--output-dir',str(output),'--teacher',str(script),
            '--depth','6','--workers','1','--timeout','120'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            deadline=time.monotonic()+10
            while not marker.exists() and time.monotonic()<deadline:time.sleep(0.02)
            self.assertTrue(marker.exists(),'teacher search did not start')
            child=int(marker.read_text());started=time.monotonic();process.terminate()
            process.communicate(timeout=5)
            self.assertLess(time.monotonic()-started,5)
            with self.assertRaises(ProcessLookupError):os.kill(child,0)
            self.assertEqual(list((output/'chunks').glob('chunk-*')),[])
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['status'],'interrupted')
        finally:
            if process.poll() is None:process.kill();process.communicate()
            if marker.exists():
                try:os.kill(int(marker.read_text()),signal.SIGKILL)
                except ProcessLookupError:pass

    def test_stop_file_drains_current_chunk_without_scheduling_next(self):
        marker=self.directory/'teacher.pid';stop=self.directory/'stop'
        response="__import__('pathlib').Path("+repr(str(marker))+").write_text(str(__import__('os').getpid())); time.sleep(0.5); print('info depth 6 multipv 1 score cp 31 nodes 123 time 2 pv e2e4'); print('bestmove e2e4')"
        engine,_=self.engine(response);script=Path(engine.process.args[1]);engine.close()
        script.write_text('#!'+sys.executable+'\n'+script.read_text());script.chmod(0o700)
        incoming=self.directory/'incoming';incoming.mkdir()
        for index,identity in enumerate(('g1','g2')):
            with gzip.open(incoming/('games-%02d.jsonl.gz'%index),'wt') as stream:
                stream.write(json.dumps(self.game(identity))+'\n')
        output=self.directory/'output'
        process=subprocess.Popen([sys.executable,str(Path(self.tool.__file__)),
            '--input-dir',str(incoming),'--output-dir',str(output),'--teacher',str(script),
            '--depth','6','--workers','1','--stop-file',str(stop)],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            deadline=time.monotonic()+5
            while not marker.exists() and process.poll() is None and time.monotonic()<deadline:time.sleep(0.02)
            self.assertTrue(marker.exists(),'teacher must start current chunk before stop request')
            child=int(marker.read_text());stop.touch()
            _,errors=process.communicate(timeout=5)
            self.assertEqual(process.returncode,0,errors.decode())
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['status'],'complete')
            self.assertEqual(manifest['stop_reason'],'stop_file')
            self.assertEqual(manifest['totals']['games'],1)
            self.assertEqual(manifest['chunks'][0]['game_ids'],['g1'])
            self.assertEqual(len(list((output/'chunks').glob('chunk-*'))),1)
            self.assertTrue(all(item['complete'] for item in manifest['transcript_sessions']))
            with self.assertRaises(ProcessLookupError):os.kill(child,0)
        finally:
            if process.poll() is None:process.kill();process.communicate()
            if marker.exists():
                try:os.kill(int(marker.read_text()),signal.SIGKILL)
                except ProcessLookupError:pass

    def test_follower_waits_for_games_and_excludes_process_trace(self):
        engine,_=self.engine();script=Path(engine.process.args[1]);engine.close()
        script.write_text('#!'+sys.executable+'\n'+script.read_text());script.chmod(0o700)
        incoming=self.directory/'incoming';(incoming/'chunks').mkdir(parents=True)
        with gzip.open(incoming/'process-trace.jsonl.gz','wt') as stream:
            stream.write(json.dumps({'event':'process_started','worker':0})+'\n')
        output=self.directory/'output';stop=self.directory/'stop'
        process=subprocess.Popen([sys.executable,str(Path(self.tool.__file__)),
            '--input-dir',str(incoming),'--output-dir',str(output),'--teacher',str(script),
            '--depth','6','--workers','1','--follow','--idle-timeout','300','--stop-file',str(stop)],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            deadline=time.monotonic()+10
            while not (output/'manifest.json').exists() and process.poll() is None and time.monotonic()<deadline:
                time.sleep(0.02)
            self.assertTrue((output/'manifest.json').exists())
            time.sleep(0.3)
            self.assertIsNone(process.poll(),'process trace must not be scheduled as a game')
            temporary=incoming/'chunks'/'games-000000.jsonl.gz.part'
            with gzip.open(temporary,'wt') as stream:stream.write(json.dumps(self.game())+'\n')
            os.replace(temporary,incoming/'chunks'/'games-000000.jsonl.gz')
            deadline=time.monotonic()+10
            while not list((output/'chunks').glob('chunk-*')) and process.poll() is None and time.monotonic()<deadline:
                time.sleep(0.02)
            self.assertTrue(list((output/'chunks').glob('chunk-*')))
            stop.touch();_,errors=process.communicate(timeout=5)
            self.assertEqual(process.returncode,0,errors.decode())
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['chunks'][0]['game_ids'],['g1'])
            self.assertEqual(manifest['status'],'complete')
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.communicate(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.communicate()

    def test_real_generator_chunk_waits_for_atomic_publication_and_ignores_trace(self):
        fixture=os.environ.get('FORGE_TEACHER_REAL_CHUNK')
        binary=os.environ.get('FORGE_TEACHER_BINARY')
        if not fixture or not binary:
            self.skipTest('Set FORGE_TEACHER_REAL_CHUNK and FORGE_TEACHER_BINARY for external integration')
        source=Path(fixture);generator=source.parent.parent
        evidence=os.environ.get('FORGE_TEACHER_EVIDENCE_DIR')
        directory=Path(evidence) if evidence else self.directory
        directory.mkdir(parents=True,exist_ok=True)
        incoming=directory/'incoming';(incoming/'chunks').mkdir(parents=True)
        shutil.copyfile(generator/'process-trace.jsonl.gz',incoming/'process-trace.jsonl.gz')
        output=directory/'output';stop=directory/'stop'
        process=subprocess.Popen([sys.executable,str(Path(self.tool.__file__)),
            '--input-dir',str(incoming),'--output-dir',str(output),'--teacher',binary,
            '--depth','6','--workers','1','--follow','--idle-timeout','300','--stop-file',str(stop)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            deadline=time.monotonic()+15
            while not (output/'manifest.json').exists() and process.poll() is None and time.monotonic()<deadline:
                time.sleep(0.02)
            self.assertTrue((output/'manifest.json').exists(),'labeler must initialize')
            # Let the follower observe the trace while no completed game chunk exists.
            time.sleep(0.5)
            self.assertIsNone(process.poll(),'generator trace was incorrectly treated as a game chunk')
            temporary=incoming/'chunks'/'games-000000.jsonl.gz.part'
            shutil.copyfile(source,temporary)
            os.replace(temporary,incoming/'chunks'/'games-000000.jsonl.gz')
            deadline=time.monotonic()+180
            while not list((output/'chunks').glob('chunk-*')) and process.poll() is None and time.monotonic()<deadline:
                time.sleep(0.05)
            self.assertTrue(list((output/'chunks').glob('chunk-*')),'actual generator chunk did not commit')
            stop.touch();stdout,stderr=process.communicate(timeout=10)
            self.assertEqual(process.returncode,0,stderr.decode())
            manifest=json.loads((output/'manifest.json').read_text())
            with gzip.open(source,'rt') as handle:original=[json.loads(line) for line in handle]
            self.assertEqual(manifest['status'],'complete')
            self.assertEqual(manifest['stop_reason'],'stop_file')
            self.assertEqual(len(manifest['chunks']),1)
            chunk=manifest['chunks'][0]
            self.assertEqual(chunk['source_sha256'],self.tool.sha256(source))
            self.assertEqual(chunk['game_ids'],[game['game_id'] for game in original])
            self.assertEqual(chunk['games'],len(original))
            self.assertGreater(chunk['accepted'],0)
            with gzip.open(output/'chunks'/chunk['path'],'rt') as handle:labelled=[json.loads(line) for line in handle]
            self.assertEqual([game['game_id'] for game in labelled],[game['game_id'] for game in original])
            for game in labelled:
                for sample in game['samples']:
                    self.assertEqual(sample['teacher_depth'],6)
                    self.assertEqual(sample['score_cp_stm'],sample['teacher_cp_stm'])
            summary={'games':chunk['games'],'input_positions':chunk['input_positions'],
                     'accepted':chunk['accepted'],'source_sha256':chunk['source_sha256'],
                     'label_sha256':chunk['sha256'],'elapsed_s':chunk['elapsed_s'],
                     'searched_nodes':chunk['searched_nodes'],'searched_time_ms':chunk['searched_time_ms'],
                     'tool_sha256':self.tool.sha256(Path(self.tool.__file__))}
            if evidence:(directory/'integration-summary.json').write_text(json.dumps(summary,sort_keys=True)+'\n')
            print('REAL_GENERATOR_INTEGRATION '+json.dumps(summary,sort_keys=True),flush=True)
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.communicate(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.communicate()

    def test_transcript_rotates_into_bounded_compressed_streams(self):
        trace=self.tool.Transcript(self.directory/'rotate',rotate_bytes=128)
        for i in range(20):trace.record(0,i,'out','info '+str(i))
        trace.close();files=list(trace.directory.glob('*.gz'))
        self.assertGreater(len(files),1)
        records=[json.loads(x) for file in sorted(files) for x in gzip.open(file,'rt')]
        self.assertEqual([x['search_id'] for x in records],list(range(20)))
        self.assertEqual(sum(x['records'] for x in trace.manifest()),20)
        for row in trace.manifest():self.assertEqual(row['sha256'],self.tool.sha256(trace.directory/row['path']))

if __name__=='__main__':unittest.main(verbosity=2)

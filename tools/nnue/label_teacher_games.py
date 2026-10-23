#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Label completed whole-game JSONL chunks with an external UCI teacher.

No engine implementation is imported. Teacher scores are side-to-move scores.
Games retain their assigned split, including games with no accepted samples.
The teacher is reset between whole games; TT/search history may persist within
one authenticated game and never between games. Raw UCI traffic is streamed to
bounded gzip segments, never one file per position. Requires python-chess.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import gzip
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import selectors
import shutil
import signal
import subprocess
import threading
import time
from typing import Any

import chess

OPTIONS = {'Threads':'1', 'Hash':'16', 'MultiPV':'1', 'Ponder':'false',
           'Skill Level':'20', 'UCI_LimitStrength':'false',
           'UCI_Chess960':'false', 'SyzygyPath':'<empty>'}
POLICY = {'score_pov':'side_to_move', 'score_cap_cp':1000, 'mate_policy':'drop_all',
          'teacher_move':'legal,noncapture,nonpromotion,not_gives_check',
          'reset':'ucinewgame+Clear Hash+isready before every whole game',
          'position_history':'complete authenticated game prefix',
          'within_game_state':'persistent TT and search history',
          'normalization':'raw Stockfish cp; fixed downstream sigmoid(cp*2.25/400); no calibration'}
_GAME_LOCK = threading.Lock()


class ProtocolError(RuntimeError):
    """An incomplete, stale or invalid UCI exchange; never a training label."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json_atomic(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, sort_keys=True, separators=(',',':'))
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


class Transcript:
    """A single ordered stream across workers, rotated by uncompressed bytes."""
    def __init__(self, directory: Path, rotate_bytes: int = 512 << 20):
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        if list(self.directory.glob('*.gz')):
            raise ValueError('transcript directory must be new')
        self.rotate_bytes = rotate_bytes
        self.lock = threading.Lock(); self.stream = None
        self.segment_bytes = 0; self.segment_records = 0; self.segments = []
        self.total_records = 0

    def _finish(self):
        if self.stream is not None:
            self.stream.close()
            path = self.directory / ('uci-%06d.jsonl.gz' % len(self.segments))
            self.segments.append({'path':path.name, 'sha256':sha256(path),
                                  'bytes':path.stat().st_size,
                                  'uncompressed_bytes':self.segment_bytes,
                                  'records':self.segment_records})
            self.stream = None

    def record(self, worker_id: int, search_id: int, direction: str, line: str):
        value = json.dumps({'worker_id':worker_id, 'search_id':search_id,
                            'direction':direction, 'line':line},separators=(',',':'))+'\n'
        encoded_bytes = len(value.encode())
        with self.lock:
            if self.stream is not None and self.segment_bytes + encoded_bytes > self.rotate_bytes:
                self._finish()
            if self.stream is None:
                self.stream = gzip.open(self.directory / ('uci-%06d.jsonl.gz' % len(self.segments)),
                                        'wt', compresslevel=1)
                self.segment_bytes = 0; self.segment_records = 0
            self.stream.write(value); self.segment_bytes += encoded_bytes
            self.segment_records += 1; self.total_records += 1

    def close(self):
        with self.lock:
            self._finish()

    def manifest(self):
        with self.lock:
            return list(self.segments)


class Teacher:
    """One persistent external UCI process, owned by exactly one worker."""
    def __init__(self, command, transcript: Transcript, worker_id: int, depth: int,
                 timeout: float = 60.0):
        if depth < 1: raise ValueError('depth must be positive')
        self.transcript=transcript; self.worker_id=worker_id; self.depth=depth
        self.timeout=timeout; self.search_id=0; self.buffer=b''; self.closed=False
        self.process=subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, bufsize=0, start_new_session=True)
        self.selector=selectors.DefaultSelector()
        self.selector.register(self.process.stdout,selectors.EVENT_READ)
        self.identity={}; self.advertised_options=[]; self.network_messages=set()
        try:
            self.send('uci'); deadline=time.monotonic()+timeout
            while True:
                line=self.read(deadline)
                if line=='uciok': break
                if line.startswith('id '):
                    key,_,value=line[3:].partition(' ');self.identity[key]=value
                elif line.startswith('option name '):self.advertised_options.append(line)
            if not self.identity.get('name'):raise ProtocolError('teacher has no UCI identity')
            names={re.split(r' type ',line[12:],maxsplit=1)[0] for line in self.advertised_options}
            for name,value in OPTIONS.items():
                if name not in names:raise ProtocolError('teacher missing required option '+name)
                self.send('setoption name '+name+' value '+value)
            if 'Clear Hash' not in names:raise ProtocolError('teacher missing Clear Hash option')
            self.ready()
        except BaseException:
            self.close();raise

    def send(self, line: str):
        self.transcript.record(self.worker_id,self.search_id,'in',line)
        try:
            self.process.stdin.write((line+'\n').encode());self.process.stdin.flush()
        except (BrokenPipeError,OSError) as error:raise ProtocolError('teacher input closed') from error

    def read(self, deadline: float) -> str:
        while b'\n' not in self.buffer:
            delay=deadline-time.monotonic()
            if delay<=0 or not self.selector.select(delay):raise ProtocolError('teacher timeout')
            data=os.read(self.process.stdout.fileno(),65536)
            if not data:raise ProtocolError('teacher EOF, exit='+str(self.process.poll()))
            self.buffer+=data
            if len(self.buffer)>4<<20:raise ProtocolError('unbounded teacher output line')
        raw,self.buffer=self.buffer.split(b'\n',1)
        try:line=raw.decode('utf-8').strip()
        except UnicodeDecodeError as error:raise ProtocolError('non UTF-8 teacher output') from error
        self.transcript.record(self.worker_id,self.search_id,'out',line)
        if line.startswith('info string NNUE '):self.network_messages.add(line)
        if line.lower().startswith(('unknown command','error','info string error')):
            raise ProtocolError('teacher reported error: '+line)
        return line

    def ready(self):
        self.send('isready'); deadline=time.monotonic()+self.timeout
        while True:
            line=self.read(deadline)
            if line=='readyok':return
            if line.startswith(('bestmove ','info depth ')):
                raise ProtocolError('delayed or duplicate search output: '+line)

    def begin_game(self, game_id: str):
        self.transcript.record(self.worker_id,self.search_id,'game',game_id)
        self.send('ucinewgame');self.send('setoption name Clear Hash');self.ready()

    def analyse(self, board: chess.Board, position_command: str):
        self.search_id+=1
        # Reset every field locally; no score may survive from an earlier go.
        final=None; started=time.monotonic()
        self.send(position_command);self.send('go depth '+str(self.depth))
        deadline=time.monotonic()+self.timeout
        while True:
            line=self.read(deadline)
            if line.startswith('info ') and ' score ' in line:
                fields=line.split()
                def number(name):
                    try:return int(fields[fields.index(name)+1])
                    except (ValueError,IndexError):raise ProtocolError('malformed '+name+': '+line)
                # Ignore explicit secondary PVs; they cannot replace the primary.
                if 'multipv' in fields and number('multipv')!=1:continue
                try:
                    at=fields.index('score');kind=fields[at+1];score=int(fields[at+2])
                    pv=fields[fields.index('pv')+1] if 'pv' in fields else None
                except (ValueError,IndexError):raise ProtocolError('malformed teacher score: '+line)
                final={'kind':kind,'value':score,'depth':number('depth'),
                       'nodes':number('nodes'),'time_ms':number('time'),
                       'bound':('lowerbound' in fields or 'upperbound' in fields),'pv':pv}
            if line.startswith('bestmove '):
                fields=line.split()
                if len(fields) not in (2,4) or (len(fields)==4 and fields[2]!='ponder'):
                    raise ProtocolError('malformed bestmove: '+line)
                bestmove=fields[1];break
        # Barrier catches duplicate/delayed bestmoves before publishing the label.
        self.ready()
        if final is None:raise ProtocolError('completed search without a fresh score')
        if final['depth']!=self.depth or final['bound']:
            raise ProtocolError('teacher did not complete requested exact depth')
        if final['kind'] not in ('cp','mate') or final['nodes']<0 or final['time_ms']<0:
            raise ProtocolError('invalid teacher score or counters')
        try:move=chess.Move.from_uci(bestmove)
        except ValueError as error:raise ProtocolError('invalid bestmove') from error
        if move not in board.legal_moves:raise ProtocolError('illegal teacher bestmove '+bestmove)
        if final['pv']!=bestmove:raise ProtocolError('teacher PV/bestmove mismatch')
        if self.process.poll() is not None:raise ProtocolError('teacher exited after search')
        final.update(bestmove=bestmove,wall_ms=(time.monotonic()-started)*1000)
        return final

    def terminate(self):
        # Keep stdout/selector open until the reading worker has observed EOF.
        if self.process.poll() is None:
            try:self.send('quit');self.process.wait(timeout=1)
            except (ProtocolError,subprocess.TimeoutExpired,OSError):
                try:os.killpg(self.process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                self.process.wait()

    def close(self):
        if self.closed:return
        self.closed=True
        self.terminate()
        self.selector.close()
        self.process.stdin.close();self.process.stdout.close()


def label_game(game: dict, teacher: Teacher):
    game_id=game.get('game_id');split=game.get('split')
    if not isinstance(game_id,str) or not game_id:raise ValueError('missing game_id')
    if split not in ('train','validation','audit'):raise ValueError('invalid game split')
    if game.get('result_white') not in (0,0.5,1):raise ValueError('invalid completed game result')
    samples=game.get('samples')
    if not isinstance(samples,list):raise ValueError('missing game samples')
    moves=game.get('moves')
    if not isinstance(moves,list):raise ValueError('missing complete game history')
    board=chess.Board(game.get('initial_fen',chess.STARTING_FEN))
    if not board.is_valid():raise ValueError('invalid initial game board')
    prior_ply=0; accepted=[];counts=Counter(input_positions=len(samples),accepted=0)
    mates=Counter();teacher.begin_game(game_id)
    for source_sample_index,sample in enumerate(samples):
        if sample.get('game_id')!=game_id:raise ValueError('sample game_id mismatch')
        if sample.get('split',split)!=split:raise ValueError('sample split mismatch')
        if sample.get('result_white',game['result_white'])!=game['result_white']:
            raise ValueError('sample game result mismatch')
        ply=sample.get('ply')
        if not isinstance(ply,int) or ply<prior_ply or ply>len(moves):raise ValueError('invalid sample ply ordering')
        for token in moves[prior_ply:ply]:
            try:
                move=chess.Move.from_uci(token)
                if move not in board.legal_moves:raise ValueError('illegal or null move')
                board.push(move)
            except ValueError as error:raise ValueError('illegal completed game move') from error
        prior_ply=ply
        try:sample_board=chess.Board(sample['fen'])
        except (KeyError,ValueError) as error:raise ValueError('invalid sample FEN') from error
        if not sample_board.is_valid() or sample_board.fen(en_passant='fen')!=board.fen(en_passant='fen'):
            raise ValueError('sample FEN does not match complete game prefix')
        if board.is_game_over(claim_draw=False):
            counts['terminal']+=1;continue
        initial=game.get('initial_fen')
        command=('position fen '+initial if initial else 'position startpos')
        if ply:command+=' moves '+' '.join(moves[:ply])
        label=teacher.analyse(board,command)
        counts['searched_positions']+=1;counts['searched_nodes']+=label['nodes']
        counts['searched_time_ms']+=label['time_ms']
        counts['searched_wall_ms']+=round(label['wall_ms'],6)
        if label['kind']=='mate':
            counts['mate']+=1;mates[str(label['value'])]+=1;continue
        if abs(label['value'])>1000:counts['score_cap']+=1;continue
        move=chess.Move.from_uci(label['bestmove'])
        if board.is_capture(move):counts['capture']+=1;continue
        if move.promotion:counts['promotion']+=1;continue
        if board.gives_check(move):counts['gives_check']+=1;continue
        labelled=dict(sample)
        labelled.update(source_sample_index=source_sample_index,
                        forge_score_cp_stm=sample.get('score_cp_stm'),
                        score_cp_stm=label['value'],teacher_cp_stm=label['value'],
                        teacher_kind='cp',teacher_depth=label['depth'],
                        teacher_nodes=label['nodes'],teacher_time_ms=label['time_ms'],
                        teacher_wall_ms=round(label['wall_ms'],6),teacher_bestmove=label['bestmove'])
        accepted.append(labelled);counts['accepted']+=1
        counts['accepted_nodes']+=label['nodes'];counts['accepted_time_ms']+=label['time_ms']
    # Validate the unsampled tail too: every committed record is a complete legal game.
    for token in moves[prior_ply:]:
        try:
            move=chess.Move.from_uci(token)
            if move not in board.legal_moves:raise ValueError('illegal or null move')
            board.push(move)
        except ValueError as error:raise ValueError('illegal completed game move') from error
    if 'final_fen' in game and board.fen(en_passant='fen')!=game['final_fen']:
        raise ValueError('completed game final FEN mismatch')
    labelled_game=dict(game);labelled_game['samples']=accepted
    labelled_game['teacher_counts']=dict(counts);labelled_game['teacher_mate_histogram']=dict(mates)
    return labelled_game,dict(counts)


def label_chunk(source: Path, output_dir: Path, teacher: Teacher, seen_games: dict):
    source=Path(source);output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    stem=source.name.removesuffix('.jsonl.gz');name='chunk-'+stem
    destination=output_dir/name;temporary=output_dir/('.'+name+'.pending')
    if destination.exists():raise ValueError('output chunk already exists '+str(destination))
    if temporary.exists():shutil.rmtree(temporary)
    temporary.mkdir();counter=Counter();ids=[];splits=Counter();indices=[]
    source_sha=sha256(source);started=time.monotonic()
    try:
        with gzip.open(source,'rt') as incoming,gzip.open(temporary/'labels.jsonl.gz','wt',compresslevel=1) as outgoing:
            for line in incoming:
                game=json.loads(line);identity=game.get('game_id');split=game.get('split')
                with _GAME_LOCK:
                    if identity in seen_games:raise ValueError('duplicate game_id '+str(identity))
                    seen_games[identity]=split
                result,counts=label_game(game,teacher)
                outgoing.write(json.dumps(result,separators=(',',':'))+'\n')
                ids.append(identity);splits[split]+=1;indices.append(game.get('game_index'))
                counter.update(counts)
        if not ids:raise ValueError('empty completed input chunk')
        labels=temporary/'labels.jsonl.gz'
        with labels.open('rb') as stream:os.fsync(stream.fileno())
        metadata={'path':name+'/labels.jsonl.gz','sha256':sha256(labels),'bytes':labels.stat().st_size,
                  'source_path':str(source.resolve()),'source_sha256':source_sha,
                  'games':len(ids),'game_ids':ids,'game_indices':indices,'split_games':dict(splits),
                  'teacher':teacher.identity,'teacher_depth':teacher.depth,
                  'elapsed_s':time.monotonic()-started,**dict(counter)}
        write_json_atomic(temporary/'metadata.json',metadata)
        os.replace(temporary,destination)
        return metadata
    except BaseException:
        shutil.rmtree(temporary,ignore_errors=True);raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--teacher',type=Path,required=True)
    parser.add_argument('--depth',type=int,required=True)
    parser.add_argument('--teacher-network-sha256',default=None,
                        help='Full SHA256 of externally exported embedded teacher network')
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--timeout',type=float,default=60)
    parser.add_argument('--follow',action='store_true')
    parser.add_argument('--stop-file',type=Path,default=None,
                        help='Stop scheduling new chunks when this file exists; drain active chunks')
    parser.add_argument('--idle-timeout',type=float,default=300)
    parser.add_argument('--target-positions',type=int,default=0)
    parser.add_argument('--transcript-rotate-mib',type=int,default=512)
    args=parser.parse_args(argv)
    if args.workers<1 or args.workers>4:parser.error('workers must be 1..4')
    if args.depth<1:parser.error('depth must be positive')
    if args.teacher_network_sha256 and not re.fullmatch(r'[0-9a-f]{64}',args.teacher_network_sha256):
        parser.error('teacher network SHA256 must be 64 lowercase hex characters')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    chunks_dir=args.output_dir/'chunks';chunks_dir.mkdir(exist_ok=True)
    configuration={'teacher_binary':str(args.teacher.resolve()),'teacher_sha256':sha256(args.teacher),
                   'teacher_bytes':args.teacher.stat().st_size,
                   'teacher_network_sha256':args.teacher_network_sha256,
                   'teacher_network_identity':'embedded network bound to teacher binary SHA256',
                   'options':OPTIONS,'policy':POLICY,
                   'depth':args.depth,'workers':args.workers,'timeout_s':args.timeout,
                   'input_dir':str(args.input_dir.resolve()),'tool_sha256':sha256(Path(__file__))}
    manifest_path=args.output_dir/'manifest.json';chunks=[];seen_games={};processed={}
    previous={}
    if manifest_path.exists():
        previous=json.loads(manifest_path.read_text())
        if previous['configuration']!=configuration:raise ValueError('resume configuration changed')
        chunks=previous['chunks']
        for recorded_session in previous.get('transcript_sessions',[]):
            if not recorded_session.get('complete'):
                raise ValueError('incomplete transcript session requires explicit recovery')
            for segment in recorded_session['segments']:
                segment_path=args.output_dir/recorded_session['directory']/segment['path']
                if not segment_path.is_file() or segment_path.stat().st_size!=segment['bytes'] or sha256(segment_path)!=segment['sha256']:
                    raise ValueError('committed transcript hash/size changed')
        for metadata in chunks:
            label_path=chunks_dir/metadata['path'];source=Path(metadata['source_path'])
            if sha256(label_path)!=metadata['sha256'] or sha256(source)!=metadata['source_sha256']:
                raise ValueError('committed chunk/source hash changed')
            processed[str(source.resolve())]=metadata['source_sha256']
            for identity in metadata['game_ids']:
                if identity in seen_games:raise ValueError('duplicate committed game_id')
                seen_games[identity]='committed'
    # Never adopt orphan directories that were not authenticated by the manifest.
    expected={metadata['path'].split('/')[0] for metadata in chunks}
    orphan=[path for path in chunks_dir.glob('chunk-*') if path.name not in expected]
    if orphan:raise ValueError('unmanifested committed chunk; explicit recovery required: '+str(orphan[0]))
    session=len(previous.get('transcript_sessions',[]))
    transcript=Transcript(args.output_dir/('transcript-%03d'%session),args.transcript_rotate_mib<<20)
    teachers=[];pool=None;futures={};available=queue.Queue();stop=threading.Event()
    interrupted=False;last_input=time.monotonic();failure=None;stop_reason=None
    def halt(signum,frame):
        nonlocal interrupted
        interrupted=True;stop.set()
    old_handlers={number:signal.signal(number,halt) for number in (signal.SIGINT,signal.SIGTERM)}
    def totals():
        value=Counter()
        for chunk in chunks:
            for key in ('games','input_positions','accepted','mate','score_cap','capture','promotion','gives_check','terminal','accepted_nodes','accepted_time_ms','searched_positions','searched_nodes','searched_time_ms','searched_wall_ms'):
                value[key]+=chunk.get(key,0)
        return dict(value)
    def save(status):
        sessions=list(previous.get('transcript_sessions',[]))
        sessions.append({'directory':transcript.directory.name,'segments':transcript.manifest(),
                         'records':transcript.total_records,'complete':transcript.stream is None})
        write_json_atomic(manifest_path,{'schema':'forge-independent-teacher-games-v1',
            'configuration':configuration,'teacher_identities':[teacher.identity for teacher in teachers],
            'teacher_advertised_options':teachers[0].advertised_options if teachers else [],
            'teacher_network_messages':sorted({line for teacher in teachers for line in teacher.network_messages}),
            'chunks':chunks,'totals':totals(),'transcript_sessions':sessions,'status':status,
            'stop_reason':stop_reason})
    def work(source):
        teacher=available.get()
        try:return label_chunk(source,chunks_dir,teacher,seen_games)
        finally:available.put(teacher)
    try:
        for worker_id in range(args.workers):
            teacher=Teacher([str(args.teacher.resolve())],transcript,worker_id,args.depth,args.timeout)
            teachers.append(teacher);available.put(teacher)
        pool=ThreadPoolExecutor(max_workers=args.workers)
        save('running')
        while True:
            if interrupted:break
            if args.stop_file is not None and args.stop_file.exists():
                stop_reason='stop_file';stop.set()
            if not stop.is_set():
                chunk_directory=args.input_dir/'chunks'
                # An empty committed-chunks directory means wait for publication;
                # generator process traces are never game inputs.
                candidates=sorted(chunk_directory.glob('games*.jsonl.gz')) if chunk_directory.is_dir() else sorted(args.input_dir.glob('games*.jsonl.gz'))
                for source in candidates:
                    if args.stop_file is not None and args.stop_file.exists():
                        stop_reason='stop_file';stop.set();break
                    key=str(source.resolve())
                    if key in processed:continue
                    if len(futures)>=args.workers:break
                    processed[key]='pending';futures[pool.submit(work,source)]=source
                    last_input=time.monotonic()
            if futures:
                done,_=wait(futures,timeout=0.2,return_when=FIRST_COMPLETED)
                for future in done:
                    source=futures.pop(future)
                    try:metadata=future.result()
                    except BaseException as error:failure=error;stop.set();continue
                    chunks.append(metadata);save('running')
                    print(json.dumps({'chunk':metadata['path'],'totals':totals()},separators=(',',':')),flush=True)
                if failure:break
                if args.target_positions and totals().get('accepted',0)>=args.target_positions:stop.set()
                continue
            if stop.is_set() or not args.follow:break
            if time.monotonic()-last_input>=args.idle_timeout:break
            stop.wait(0.5)
        if failure:raise failure
    except BaseException as error:
        failure=error;stop.set()
    finally:
        # On failure/interrupt, stop owned processes before waiting for worker joins.
        if failure or interrupted:
            for teacher in teachers:teacher.terminate()
        if pool is not None:
            pool.shutdown(wait=True,cancel_futures=True)
            for future,source in list(futures.items()):
                if future.done() and not future.cancelled():
                    try:metadata=future.result()
                    except BaseException:continue
                    if metadata not in chunks:chunks.append(metadata)
        for teacher in teachers:teacher.close()
        transcript.close();save('failed' if failure else ('interrupted' if interrupted else 'complete'))
        for number,handler in old_handlers.items():signal.signal(number,handler)
    if failure:raise failure
    return 0


if __name__=='__main__':raise SystemExit(main())

#!/usr/bin/env python3
"""One fixed cold/warm causal diagnostic; root resource clearance required."""
from __future__ import annotations
import argparse, base64, collections, datetime, gzip, hashlib, json, os
from pathlib import Path
import queue, re, signal, subprocess, sys, threading, time
import chess
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
INPUT=REPO/'validation/tt-strength-20261020/final-audit/game85-baseline-original-input.txt'
SESSION=REPO/'validation/tt-strength-20261020/final-audit/game85-original-protocol.log.gz'
ORIGINAL=REPO/'validation/tt-strength-20261020/final-audit/forfeit-exchange.json'
EXPECTED_INPUT='cd4b74174c8536dc83e1c5e55c0374e08a889f678958744b395dddc1fec9e41d'
HEAVY={'forge','cmake','ctest','make','ninja','cc1plus','g++','g++-14','clang','clang++'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def clocks():return {'wall_ns':time.monotonic_ns(),'thread_cpu_ns':time.thread_time_ns(),'process_cpu_ns':time.process_time_ns(),'pid':os.getpid(),'tid':threading.get_native_id()}
def processes():
    rows=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            name=(p/'comm').read_text().strip();stat=(p/'stat').read_text();state=stat[stat.rindex(')')+2:].split()[0]
        except (OSError,ValueError):continue
        if state!='Z' and name in HEAVY:rows.append({'pid':int(p.name),'name':name,'state':state})
    return rows
def active_owned_group(pgid):
    """Ignore dead zombies; identify live members even after leader exit."""
    members=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            text=(p/'stat').read_text();fields=text[text.rindex(')')+2:].split()
            if fields[0]!='Z' and int(fields[2])==pgid:members.append(int(p.name))
        except (OSError,ValueError,IndexError):continue
    return members
class Capture:
    def __init__(self,engine:Path,out:Path,poll_target:int,deadline:float):
        self.out,self.deadline=out,deadline;out.mkdir(exist_ok=False)
        self.queue=queue.Queue();self.errors=[];self.record_lock=threading.Lock();self.count_lock=threading.Lock();self.raw_bytes=0
        self.log_fd=os.open(out/'manager-events.jsonl',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_APPEND,0o600)
        env=os.environ.copy();env.update(FORGE_TIME_DIAGNOSTIC_PATH=str(out/'engine-events.jsonl'),FORGE_TIME_DIAGNOSTIC_POLL_SEARCH=str(poll_target))
        self.environment_overrides={k:env[k] for k in ['FORGE_TIME_DIAGNOSTIC_PATH','FORGE_TIME_DIAGNOSTIC_POLL_SEARCH']}
        self.log('manager_spawn_begin',**clocks())
        self.proc=subprocess.Popen([str(engine)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,cwd=engine.parent,start_new_session=True,bufsize=0)
        self.log('manager_spawn_end',engine_pid=self.proc.pid,**clocks())
        self.readers=[threading.Thread(target=self.read,args=('stdout',self.proc.stdout),daemon=True),threading.Thread(target=self.read,args=('stderr',self.proc.stderr),daemon=True)]
        for t in self.readers:t.start()
        self.stdin=(out/'stdin.bin').open('xb');self.responses=[];self.cleanup=[];self.finished=False;self.search_id=0
    def log(self,event,**data):
        blob=(json.dumps({'event':event,**data},separators=(',',':'))+'\n').encode()
        with self.record_lock:
            n=os.write(self.log_fd,blob)
            if n!=len(blob):raise RuntimeError('Incomplete manager event write')
    def read(self,label,pipe):
        carry=b'';offset=0
        try:
            with (self.out/(label+'.bin')).open('xb',buffering=0) as raw:
                while True:
                    b=os.read(pipe.fileno(),16384);observed=clocks()
                    if not b:break
                    with self.count_lock:
                        self.raw_bytes+=len(b)
                        if self.raw_bytes>16*1024*1024:raise RuntimeError('Raw output exceeds16MiB diagnostic cap')
                    raw.write(b)
                    self.log('manager_os_read',stream=label,offset=offset,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),**observed);offset+=len(b)
                    if label=='stdout':
                        carry+=b
                        while b'\n' in carry:
                            line,carry=carry.split(b'\n',1)
                            record={'text':line.rstrip(b'\r').decode('utf-8',errors='strict'),'observed':observed,'line_decoded':clocks()}
                            self.log('manager_line_decoded',stream=label,text=record['text'],read_wall_ns=observed['wall_ns'],**record['line_decoded'])
                            self.queue.put(record)
                if carry:raise RuntimeError('Unterminated stdout line')
            self.log('manager_stream_eof',stream=label,**clocks())
        except Exception as exc:
            self.errors.append(repr(exc));self.queue.put({'error':repr(exc)})
        finally:
            if label=='stdout':self.queue.put({'eof':True})
    def send(self,line):
        blob=(line+'\n').encode();self.stdin.write(blob);self.stdin.flush()
        assert self.proc.stdin is not None
        stamp=clocks()
        n=os.write(self.proc.stdin.fileno(),blob)
        after=clocks()
        if n!=len(blob):raise RuntimeError('Incomplete stdin command write')
        # Persist both timestamps after the measured write, so logging itself
        # does not sit between the prewrite sample and the actual pipe write.
        self.log('manager_write_begin',command=line,search=self.search_id,**stamp)
        self.log('manager_write_end',command=line,search=self.search_id,**after)
        return stamp
    def wait(self,token):
        while True:
            left=self.deadline-time.monotonic()
            if left<=0:raise TimeoutError('Global56s active diagnostic deadline')
            path=self.out/'engine-events.jsonl'
            if path.exists() and path.stat().st_size>32*1024*1024:raise RuntimeError('Telemetry exceeds32MiB cap')
            try:r=self.queue.get(timeout=min(.05,left))
            except queue.Empty:
                if self.errors:raise RuntimeError(self.errors[0])
                continue
            self.log('manager_consumer_receive',token=token,record=r,search=self.search_id,**clocks())
            if 'error' in r:raise RuntimeError(r['error'])
            if r.get('eof'):raise RuntimeError('EOF before '+token)
            text=r['text']
            if text==token or token=='bestmove' and text.startswith('bestmove '):return r
            if text.startswith('bestmove '):raise RuntimeError('Unexpected bestmove before '+token)
    def close(self,success=False):
        if self.finished:return
        cleanup_deadline=min(self.deadline+4,time.monotonic()+3)
        def remaining(cap):return max(0,min(cap,cleanup_deadline-time.monotonic()))
        try:
            if self.proc.poll() is None and success:
                self.proc.wait(timeout=remaining(1))
        except subprocess.TimeoutExpired:pass
        # A reaped leader can leave descendants holding capture pipes. The
        # session/group was created by this Capture; never signal other groups.
        try:os.killpg(self.proc.pid,signal.SIGTERM);self.cleanup.append('SIGTERM owned process group')
        except ProcessLookupError:pass
        term_deadline=min(cleanup_deadline,time.monotonic()+.5)
        while active_owned_group(self.proc.pid) and time.monotonic()<term_deadline:
            time.sleep(min(.01,max(0,term_deadline-time.monotonic())))
        if active_owned_group(self.proc.pid):
            try:os.killpg(self.proc.pid,signal.SIGKILL);self.cleanup.append('SIGKILL owned process group')
            except ProcessLookupError:pass
        if self.proc.poll() is None:
            self.proc.wait(timeout=remaining(1))
        for t in self.readers:t.join(timeout=remaining(.5))
        members=active_owned_group(self.proc.pid)
        joined=all(not t.is_alive() for t in self.readers)
        self.log('manager_capture_complete',exit_code=self.proc.returncode,readers_joined=joined,active_owned_group_members=members,errors=self.errors,cleanup=self.cleanup,**clocks())
        if not joined or members or self.proc.poll() is None:
            raise RuntimeError('Incomplete capture cleanup; owned process/readers remain')
        for stream in (self.proc.stdin,self.proc.stdout,self.proc.stderr,self.stdin):
            if stream is not None and not stream.closed:stream.close()
        os.close(self.log_fd)
        self.log_fd=None
        self.finished=True
        if self.errors:raise RuntimeError('Incomplete capture: '+repr(self.errors))
def parse_position(line):
    words=line.split();assert words[:2]==['position','fen']
    board=chess.Board(' '.join(words[2:8]));assert board.is_valid()
    if len(words)>8:
        assert words[8]=='moves'
        for move in words[9:]:board.push_uci(move)
    return board

def run_case(name,commands,expected,engine,out,deadline):
    target=sum(c.startswith('go ') for c in commands);capture=Capture(engine,out,target,deadline);board=None;searches=[]
    result={'case':name,'original_or_derived_commands':commands,'expected_go_count':target,'environment_overrides':capture.environment_overrides,'status':'RUNNING'}
    save(out/'case.json',result)
    try:
        for line in commands:
            if line.startswith('position '):board=parse_position(line)
            if line.startswith('go '):capture.search_id+=1
            before=capture.send(line)
            if line=='uci':capture.wait('uciok')
            elif line=='isready':capture.wait('readyok')
            elif line.startswith('go '):
                assert board is not None
                response=capture.wait('bestmove');move=response['text'].split()[1]
                legal=chess.Move.from_uci(move) in board.legal_moves
                if not legal:raise RuntimeError('Illegal diagnostic bestmove '+move)
                searches.append({'search':capture.search_id,'position_fen':board.fen(en_passant='fen'),'go_original':line,'manager_go_prewrite':before,'manager_observed_bestmove':response,'bestmove':move,'legal':True,'original_expected_bestmove':expected[capture.search_id-1],'differs_from_original':move!=expected[capture.search_id-1]})
            elif line=='quit':break
        capture.close(success=True)
        if capture.proc.returncode!=0:raise RuntimeError('Engine exited '+str(capture.proc.returncode))
        if (out/'stderr.bin').stat().st_size:raise RuntimeError('Unexpected runtime stderr')
        telemetry=[json.loads(s) for s in (out/'engine-events.jsonl').read_text().splitlines()]
        ids=[r['id'] for r in telemetry]
        assert sorted(ids)==list(range(1,len(ids)+1)), 'Missing/duplicate telemetry event IDs'
        manager=[json.loads(s) for s in (out/'manager-events.jsonl').read_text().splitlines()]
        info_counts=collections.Counter(r['search'] for r in manager if r['event']=='manager_consumer_receive' and r['record'].get('text','').startswith('info depth '))
        raw_info_count=sum(line.startswith(b'info depth ') for line in (out/'stdout.bin').read_bytes().splitlines())
        assert sum(info_counts.values())==raw_info_count,'Missing/duplicate consumed info depth lines'
        phase_counts=[]
        for seq in range(1,target+1):
            rows=[r for r in telemetry if r['search']==seq];names=collections.Counter(r['event'] for r in rows)
            for tag in ['go_receipt','worker_dispatch_begin','facade_enter','worker_search_begin','worker_origin','budget_ready','worker_result','facade_result','uci_search_return','bestmove_pre_lock','bestmove_pre_output','bestmove_post_flush']:
                assert names[tag]==1,(seq,tag,names[tag])
            for tag in ['info_pre_lock','info_pre_output','info_pre_flush','info_post_flush']:
                assert names[tag]==info_counts[seq],(seq,tag,names[tag],info_counts[seq])
            assert names['timer_poll_begin']==names['timer_poll_end'],(seq,'incomplete timer poll')
            if seq!=target:assert names['timer_poll_begin']==0,(seq,'unexpected poll telemetry')
            phase_counts.append({'search':seq,'info_depth_lines':info_counts[seq],'event_counts':dict(names)})
        result.update(status='PASS_DIAGNOSTIC_CAPTURE',go_count=len(searches),searches=searches,telemetry_events=len(telemetry),telemetry_complete_ids=True,telemetry_phase_counts=phase_counts,cleanup=capture.cleanup,exit_code=capture.proc.returncode,readers_joined=True)
    except BaseException as exc:
        result.update(status='FAILED_OR_INCOMPLETE_DIAGNOSTIC',error=repr(exc),searches=searches)
        try:capture.close()
        except Exception as cleanup_error:result['cleanup_error']=repr(cleanup_error)
        raise
    finally:
        result['raw_files']={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.iterdir()) if p.is_file() and p.name!='case.json'}
        save(out/'case.json',result)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--clearance',type=Path,required=True,help='Root-written resource clearance JSON bound to protocol SHA')
    a=parser.parse_args();a.out=a.out.resolve();a.engine=a.engine.resolve()
    assert not a.out.exists(),'Refusing output reuse'
    protocol=HERE/'PROTOCOL.json';clearance=json.loads(a.clearance.read_text())
    assert clearance.get('timing_execution_authorized') is True and clearance.get('protocol_sha256')==sha(protocol),'Root resource clearance missing/mismatched'
    busy=processes();assert not busy,('Known competing heavy processes active',busy)
    assert sha(INPUT)==EXPECTED_INPUT
    original=json.loads(ORIGINAL.read_text());warm=INPUT.read_text().splitlines()
    assert len(warm)==260 and sum(c.startswith('go ') for c in warm)==50
    rawsession=gzip.decompress(SESSION.read_bytes())
    assert hashlib.sha256(rawsession).hexdigest()==original['session_original_sha256']
    expected=re.findall(rb'  Baseline ---> bestmove (\S+)',rawsession)
    expected=[s.decode() for s in expected];assert len(expected)==50
    setup=warm[:7];assert setup[-1]=='isready'
    cold=setup+['position fen '+original['final_search']['current_fen_strict_ep'],'isready',original['final_search']['go_command_original'],'isready','stop','stop','quit']
    build=json.loads((HERE/'BUILD.json').read_text())
    assert build['status']=='PASS_BUILD_ONLY' and build['engine']['path']==str(a.engine) and build['engine']['sha256']==sha(a.engine)
    source=json.loads((HERE/'SOURCE.json').read_text())
    def frozen_inputs():
        result={'engine_sha256':sha(a.engine),'core_library_sha256':sha(build['core_library']['path']),'build_provenance_sha256':sha(HERE/'BUILD.json'),'protocol_sha256':sha(protocol),'original_stdin_sha256':sha(INPUT),'original_session_sha256':sha(SESSION),'original_exchange_sha256':sha(ORIGINAL),'source_inventory_sha256':sha(HERE/'SOURCE.json'),'runner_sha256':sha(Path(__file__))}
        for rel,expected in source['instrumented_sha256'].items():
            actual=sha(Path(source['source_export'])/rel)
            result['source:'+rel]=actual
        return result
    before=frozen_inputs()
    assert before['core_library_sha256']==build['core_library']['sha256']
    assert build['source_manifest_sha256']==before['source_inventory_sha256']
    assert all(before['source:'+rel]==expected for rel,expected in source['instrumented_sha256'].items())
    a.out.mkdir(parents=True,exist_ok=False)
    report={'status':'RUNNING','scope':'Causal diagnostic only; no games, Elo, retry, original internal-state identity or performance claim.','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozen_inputs_before':before,'clearance':clearance,'original_affinity':sorted(os.sched_getaffinity(0)),'preflight_known_heavy_processes':busy,'cases':[]}
    save(a.out/'summary.json',report);saved_affinity=os.sched_getaffinity(0);start=time.monotonic();deadline=start+56
    try:
        cpu=min(saved_affinity);os.sched_setaffinity(0,{cpu});report['selected_cpu']=cpu
        for name,commands,expected_moves in [('cold',cold,[expected[-1]]),('warm',warm,expected)]:
            row=run_case(name,commands,expected_moves,a.engine,a.out/name,deadline);report['cases'].append({k:row[k] for k in ['case','status','go_count','telemetry_events']});save(a.out/'summary.json',report)
        report.update(status='COMPLETE_CAUSAL_DIAGNOSTIC_NO_STRENGTH_CLAIM')
    except BaseException as exc:
        report.update(status='FAILED_OR_INCOMPLETE_DIAGNOSTIC',error=repr(exc));raise
    finally:
        try:
            after=frozen_inputs();report['frozen_inputs_after']=after;report['inputs_unchanged']=before==after
            if before!=after:report.update(status='FAILED_OR_INCOMPLETE_DIAGNOSTIC',final_input_error='Frozen inputs changed')
        except Exception as final_error:
            report.update(status='FAILED_OR_INCOMPLETE_DIAGNOSTIC',inputs_unchanged=False,final_input_error=repr(final_error))
        os.sched_setaffinity(0,saved_affinity);report['elapsed_seconds']=time.monotonic()-start;report['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(a.out/'summary.json',report)
    assert report['inputs_unchanged'],'Frozen input unavailable or changed'
    print(json.dumps({'status':report['status'],'elapsed_seconds':report['elapsed_seconds'],'cases':report['cases']}))
if __name__=='__main__':main()

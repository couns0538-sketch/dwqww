#!/usr/bin/env python3
"""One frozen outside-production pair; requires the explicit root clearance."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, re, selectors, shutil, signal, subprocess, time

ROOT=Path(__file__).resolve().parent
WORK=Path('/workspace/promotion-see-qsearch-causal-20261020')
parser=argparse.ArgumentParser()
parser.add_argument('--clearance',required=True)
args=parser.parse_args()
if args.clearance!='17 QSEARCH TRACE CLEAR':raise SystemExit('Exact root trace clearance required.')
PROTOCOL=json.loads((ROOT/'PROTOCOL.json').read_text())
ATTEMPT=ROOT/'attempt1';ATTEMPT.mkdir(exist_ok=False)
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
record={'status':'RUNNING','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'protocol_sha256':sha(ROOT/'PROTOCOL.json'),'phases':[],'processes':[],
        'engine_seconds':0,'engine_budget_seconds':30,'performance_claim':None,'strength_claim':None}
def save():write(ATTEMPT/'record.json',record)
def build_step(label,command,timeout=90):
    start=time.monotonic()
    try:
        p=subprocess.run([str(x) for x in command],cwd=WORK,env=ENV,capture_output=True,timeout=timeout)
        rc,out,err=p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired as exc:rc,out,err=124,exc.stdout or b'',exc.stderr or b''
    for ext,data in [('stdout',out),('stderr',err)]: (ATTEMPT/(label+'.'+ext)).write_bytes(data)
    record['phases'].append({'label':label,'command':[str(x) for x in command],'timeout_seconds':timeout,
        'exit_code':rc,'elapsed_seconds_operational_only':time.monotonic()-start,
        'stdout_sha256':sha(ATTEMPT/(label+'.stdout')),'stderr_sha256':sha(ATTEMPT/(label+'.stderr'))})
    save();print(label,rc,flush=True)
    if rc:raise RuntimeError(label+' failed; no retry')
    return out

def group_alive(pid):
    try:os.killpg(pid,0);return True
    except ProcessLookupError:return False

def engine_once(label,exe):
    if record['engine_seconds']+11>PROTOCOL['engine_budget_seconds']:
        raise RuntimeError('Insufficient remaining budget for bounded process and cleanup')
    start=time.monotonic();deadline=start+PROTOCOL['per_process_total_response_deadline_seconds']
    p=subprocess.Popen([str(exe)],cwd=WORK,env=ENV,stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0,start_new_session=True)
    sel=selectors.DefaultSelector()
    sel.register(p.stdout,selectors.EVENT_READ,'stdout');sel.register(p.stderr,selectors.EVENT_READ,'stderr')
    data={'stdin':bytearray(),'stdout':bytearray(),'stderr':bytearray()}
    events=[];stage='uci';error=None
    def send(text):
        payload=text.encode();p.stdin.write(payload);p.stdin.flush();data['stdin'].extend(payload)
        events.append({'event':'send','text':text,'elapsed_seconds_operational_only':time.monotonic()-start})
    def pump_until(pattern):
        while not re.search(pattern,data['stdout'].decode(errors='replace'),re.MULTILINE):
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('10s total response guard at '+stage)
            for key,_ in sel.select(min(remaining,0.05)):
                chunk=os.read(key.fileobj.fileno(),65536)
                if chunk:
                    data[key.data].extend(chunk)
                    events.append({'event':'read','stream':key.data,'bytes':len(chunk),
                        'elapsed_seconds_operational_only':time.monotonic()-start})
                else:sel.unregister(key.fileobj)
            if p.poll() is not None and not re.search(pattern,data['stdout'].decode(errors='replace'),re.MULTILINE):
                raise RuntimeError('Engine exited before '+stage)
    try:
        send('uci\n');pump_until(r'^uciok\r?$')
        stage='ready'
        send('setoption name OwnBook value false\nsetoption name Threads value 1\nsetoption name Hash value 16\nucinewgame\nisready\n')
        pump_until(r'^readyok\r?$')
        stage='search'
        send('position fen '+PROTOCOL['parent_fen']+'\ngo depth 1 searchmoves '+PROTOCOL['root_move']+'\n')
        pump_until(r'^bestmove\s+\S+')
        stage='quit';send('quit\n')
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('10s total response guard at quit')
        p.wait(timeout=remaining)
        if p.returncode:raise RuntimeError('Engine exit '+str(p.returncode))
    except BaseException as exc:
        error=repr(exc)
    finally:
        sel.close()
        if group_alive(p.pid):
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        try:p.wait(timeout=1)
        except subprocess.TimeoutExpired:error=error or 'Owned group cleanup did not finish'
        try:
            out,err=p.communicate(timeout=1)
            data['stdout'].extend(out or b'');data['stderr'].extend(err or b'')
        except BaseException as exc:error=error or ('Pipe cleanup '+repr(exc))
        elapsed=time.monotonic()-start
        for stream,payload in data.items():(ATTEMPT/(label+'.'+stream)).write_bytes(payload)
        write(ATTEMPT/(label+'-events.json'),events)
        proc={'label':label,'command':[str(exe)],'pid':p.pid,'process_group':p.pid,
            'exit_code':p.returncode,'stage':stage,'error':error,
            'status':'PASS_CAPTURE' if error is None else 'FAILED_STOP_NO_RETRY',
            'elapsed_seconds_operational_only':elapsed,'response_deadline_seconds':10,
            'owned_group_empty_after_cleanup':not group_alive(p.pid),
            'stdin_sha256':sha(ATTEMPT/(label+'.stdin')),'stdout_sha256':sha(ATTEMPT/(label+'.stdout')),
            'stderr_sha256':sha(ATTEMPT/(label+'.stderr'))}
        record['engine_seconds']+=elapsed;record['processes'].append(proc);save()
    if error:raise RuntimeError(label+' failed at '+stage+': '+error)
    if not proc['owned_group_empty_after_cleanup']:raise RuntimeError('Owned process group remains')
    if record['engine_seconds']>30:raise RuntimeError('Aggregate engine budget exceeded')
    return bytes(data['stdout']).decode(errors='replace'),bytes(data['stderr']).decode(errors='replace')

def parse_trace(stderr):
    rows=[]
    for line in stderr.splitlines():
        if not line.startswith('QSEARCH_TRACE '):continue
        meta,separator,fen=line.partition(' fen=')
        row=dict(token.split('=',1) for token in meta.split()[1:])
        if separator:row['fen']=fen
        rows.append(row)
    return rows

try:
    assert PROTOCOL['engine_budget_seconds']==30
    assert PROTOCOL['per_process_total_response_deadline_seconds']==10
    assert all(sha(ROOT/n)==h for n,h in PROTOCOL['driver_sha256'].items())
    assert all(sha(ROOT/'originals'/n)==h for n,h in PROTOCOL['original_file_sha256'].items())
    assert all(sha(p)==h for p,h in PROTOCOL['original_path_sha256'].items())
    assert sha(ROOT/'search-trace.cpp')==PROTOCOL['search_trace_sha256']
    assert sha(WORK/'source/src/search.cpp')==PROTOCOL['search_trace_sha256']
    assert all(sha(WORK/'source'/n)==h for n,h in PROTOCOL['frozen_builds']['source16']['header_sha256'].items())
    flags={}
    for label in ['source16','source17']:
        flags[label]=next(line.split(' = ',1)[1].split() for line in (ROOT/'originals'/label/'flags.make').read_text().splitlines() if line.startswith('CXX_FLAGS = '))
    assert flags['source16']==flags['source17']
    flags=flags['source16']
    build_step('compile-trace-search',['/usr/bin/c++',*flags,'-I'+str(WORK/'source/include'),'-c',
        WORK/'source/src/search.cpp','-o',ATTEMPT/'search.cpp.o'])
    member_hashes={}
    for label in ['source16','source17']:
        original=ROOT/'originals'/label/'libforge_core.a';core=ATTEMPT/(label+'-trace-core.a')
        shutil.copy2(original,core)
        build_step('replace-search-'+label,['ar','r',core,ATTEMPT/'search.cpp.o'])
        build_step('ranlib-'+label,['ranlib',core])
        members=build_step('members-'+label,['ar','t',original]).decode().splitlines()
        before={m:hashlib.sha256(subprocess.check_output(['ar','p',original,m])).hexdigest() for m in members}
        after={m:hashlib.sha256(subprocess.check_output(['ar','p',core,m])).hexdigest() for m in members}
        assert [m for m in members if before[m]!=after[m]]==['search.cpp.o']
        member_hashes[label]={'original':before,'trace':after}
        build_step('link-'+label,['/usr/bin/c++',*flags,ROOT/'originals'/label/'uci.cpp.o',core,
            '-pthread','-o',ATTEMPT/(label+'-trace')])
    assert [m for m in member_hashes['source16']['original']
            if member_hashes['source16']['original'][m]!=member_hashes['source17']['original'][m]]==['board.cpp.o']
    record['core_member_sha256']=member_hashes;save()
    observed={}
    for label in ['source16','source17']:
        stdout,stderr=engine_once(label,ATTEMPT/(label+'-trace'))
        trace=parse_trace(stderr)
        by_stage={}
        for row in trace:by_stage.setdefault(row['stage'],[]).append(row)
        infos=[line for line in stdout.splitlines() if line.startswith('info depth 1 ')]
        best=[line for line in stdout.splitlines() if line.startswith('bestmove ')]
        observed[label]={'trace':trace,'stages':by_stage,'depth1_info_raw':infos,'bestmove_raw':best}
        write(ATTEMPT/'observed.json',observed)
        assert len(best)==1 and best[0].split()[1]=='g8h8'
        assert len(by_stage.get('ENTER',[]))==1
        assert len(by_stage.get('SEE',[]))==1
        assert not by_stage.get('SKIP_FUTILITY')
        enter=by_stage['ENTER'][0];see=by_stage['SEE'][0]
        assert enter['ply']=='1' and enter['in_check']=='0'
        assert int(enter['beta'])-int(enter['alpha'])>1
        assert see['threshold']=='-40'
        expected=0 if label=='source16' else 1
        assert int(see['passed'])==expected
        assert len(by_stage.get('SKIP_SEE',[]))==1-expected
        assert len(by_stage.get('SEARCH_ENTER',[]))==expected
        assert len(by_stage.get('SEARCH_RETURN',[]))==expected
    assert observed['source16']['stages']['ENTER'][0]==observed['source17']['stages']['ENTER'][0]
    assert all(sha(p)==h for p,h in PROTOCOL['original_path_sha256'].items())
    assert all(sha(ROOT/'originals'/n)==h for n,h in PROTOCOL['original_file_sha256'].items())
    result={'status':'PASS_ACTUAL_QSEARCH_CAUSAL_TRACE','source16_see_pass':False,
        'source17_see_pass':True,'source16_target_searched':False,'source17_target_searched':True,
        'same_pre_gate_state':True,'threshold':-40,'searches':2,
        'engine_seconds_budget_accounting_only':record['engine_seconds'],'engine_budget_seconds':30,
        'all_originals_unchanged':True,'performance_claim':None,'strength_claim':None}
    write(ATTEMPT/'RESULT.json',result)
    record['status']=result['status'];record['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
    print(json.dumps(result))
except BaseException as exc:
    record['status']='INCONCLUSIVE_OR_FAILED_PRESERVE_NO_RETRY'
    record['error']=repr(exc);save();raise

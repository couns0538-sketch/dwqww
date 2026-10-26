"""NEW diagnostic-only S18 t500 observation. No retry, acceptance or training."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import selectors
import signal
import stat
import subprocess
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
PINS=HERE/'forge_sol_S18_diagnostic_pins_20261026.json'
PINS_SHA='3ef3526c67df7e71717f3cd807169344cdf1fbd47554d437bac1ec823f1b7fc3'
READ_LIMIT=4096
STREAM_LIMIT=1048576
TELEMETRY_LIMIT=8388608


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):h.update(block)
    return h.hexdigest()


def load_pins():
    if sha(PINS)!=PINS_SHA:raise ValueError('diagnostic pins changed')
    return json.loads(PINS.read_text())


def parse_stat(text,pid):
    try:
        head,sep,tail=text.rpartition(') ')
        fields=tail.split()
        if not sep or int(head.split(' (',1)[0])!=pid or len(fields)<20:raise ValueError('stat PID/shape mismatch')
        row={'state':fields[0],'ppid':int(fields[1]),'pgrp':int(fields[2]),'utime_ticks':int(fields[11]),
             'stime_ticks':int(fields[12]),'threads':int(fields[17]),'start_ticks':int(fields[19])}
        if any(v<0 for k,v in row.items() if isinstance(v,int)):raise ValueError('negative stat value')
        return row
    except (ValueError,IndexError) as e:raise ValueError('invalid proc stat: '+str(e)) from e


def parse_schedstat(text):
    values=text.split()
    if len(values)!=3:raise ValueError('schedstat must have three fields')
    values=[int(v) for v in values]
    if min(values)<0:raise ValueError('negative schedstat')
    return dict(zip(('runtime_ns','runqueue_ns','timeslices'),values))


def parse_integer_map(text,colon=True):
    result={}
    for line in text.splitlines():
        fields=line.replace(':',' ',1).split() if colon else line.split()
        if len(fields)!=2 or fields[0] in result:raise ValueError('bad/duplicate integer-map row')
        value=int(fields[1])
        if value<0:raise ValueError('negative integer-map value')
        result[fields[0]]=value
    if not result:raise ValueError('empty integer map')
    return result


def parse_pressure(text):
    import math
    result={}
    for line in text.splitlines():
        tokens=line.split()
        if len(tokens)<2 or tokens[0] not in ('some','full') or tokens[0] in result:raise ValueError('bad pressure row')
        row={}
        for token in tokens[1:]:
            k,sep,v=token.partition('=')
            if not sep or k not in ('avg10','avg60','avg300','total') or k in row:raise ValueError('bad pressure field')
            n=int(v) if k=='total' else float(v)
            if n<0 or not math.isfinite(n):raise ValueError('nonfinite/negative pressure')
            row[k]=n
        result[tokens[0]]=row
    if not result:raise ValueError('empty pressure')
    return result


def _read_text(path):
    with Path(path).open('rb') as stream:data=stream.read(READ_LIMIT+1)
    if len(data)>READ_LIMIT:raise ValueError('read limit exceeded')
    return data.decode('utf-8',errors='strict')


def observe_text(path,parser=None,reader=None):
    try:
        text=(reader or _read_text)(path)
        if len(text.encode('utf-8'))>READ_LIMIT:raise ValueError('read limit exceeded')
        result={'available':True,'raw':text}
        if parser is not None:result['value']=parser(text)
        return result
    except (OSError,UnicodeError,ValueError) as e:
        return {'available':False,'error':type(e).__name__+': '+str(e)[:240]}


def sample_child(pid,start_ticks):
    base=Path('/proc')/str(pid)
    status=observe_text(base/'stat',lambda t:parse_stat(t,pid))
    result={'pid':pid,'stat':status,'identity_verified':False}
    if not status['available']:return result
    s=status['value']
    if s['start_ticks']!=start_ticks or s['pgrp']!=pid:
        result['identity_error']='owned PID start/group mismatch; other proc reads suppressed';return result
    result['identity_verified']=True
    result['schedstat']=observe_text(base/'schedstat',parse_schedstat)
    result['wchan']=observe_text(base/'wchan')
    result['io']=observe_text(base/'io',parse_integer_map)
    result['status']=observe_text(base/'status')
    return result


def cgroup_observation():
    """Read only this supervisor's discovered unified cgroup, never change it."""
    membership=observe_text('/proc/self/cgroup')
    result={'scope':'current supervisor cgroup; shared context, not attribution','membership':membership}
    if not membership['available']:return result
    paths=[line[3:] for line in membership['raw'].splitlines() if line.startswith('0::')]
    if len(paths)!=1 or '..' in Path(paths[0]).parts:
        result['available']=False;result['error']='unified cgroup unavailable/invalid';return result
    base=Path('/sys/fs/cgroup')/paths[0].lstrip('/')
    result['path']=str(base)
    for name in ('cpu.stat','cpu.pressure','memory.pressure','io.pressure'):
        result[name]=observe_text(base/name,(lambda t:parse_integer_map(t,colon=False)) if name=='cpu.stat' else parse_pressure)
    return result


class BoundedCapture:
    def __init__(self,stream,limit):
        self.stream=stream;self.limit=limit;self.seen=0;self.written=0;self.truncated=False
    def write(self,data):
        self.seen+=len(data)
        prefix=data[:max(0,self.limit-self.written)]
        if prefix:self.stream.write(prefix);self.stream.flush();self.written+=len(prefix)
        if len(prefix)!=len(data):self.truncated=True
        return len(prefix)
    def summary(self):return {'seen_bytes':self.seen,'written_bytes':self.written,'limit_bytes':self.limit,'truncated':self.truncated}


def emit_json(capture,row):
    capture.write((json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode())
    return not capture.truncated


def tree_sizes(root,max_entries=128,max_depth=3):
    """lstat metadata only in this NEW output; no file bodies or SQLite opens."""
    result={'entries':[],'truncated':False,'errors':[],'visited_entries':0}
    root=Path(root)
    if not root.exists():return result
    todo=[(root,0)]
    while todo:
        current,depth=todo.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if result['visited_entries']>=max_entries:
                        result['truncated']=True;return result
                    result['visited_entries']+=1
                    try:
                        st=entry.stat(follow_symlinks=False)
                        kind='symlink' if stat.S_ISLNK(st.st_mode) else 'directory' if stat.S_ISDIR(st.st_mode) else 'file' if stat.S_ISREG(st.st_mode) else 'other'
                        row={'path':str(Path(entry.path).relative_to(root)),'kind':kind,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
                        result['entries'].append(row)
                        if kind=='directory':
                            if depth<max_depth:todo.append((Path(entry.path),depth+1))
                            else:result['truncated']=True
                    except OSError as e:result['errors'].append(type(e).__name__+': '+str(e)[:120])
        except OSError as e:result['errors'].append(type(e).__name__+': '+str(e)[:120])
    return result


def guard_new_output(path,blocked):
    path=Path(path).absolute()
    if not path.is_relative_to('/tmp') or '..' in path.parts or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('new nonsymlink /tmp directory required')
    if any(x.lower() in ('baseline','locks','.git') or x.lower().startswith('dist-v') for x in path.parts):
        raise ValueError('protected output directory')
    if path.exists():raise ValueError('output already exists; never resume/overwrite')
    if any(path.is_relative_to(Path(p).resolve()) for p in blocked):raise ValueError('output is inside protected source/input/history')
    return path


def child_argv(pins,out,tool):
    sample=Path(pins['sample'])
    return [pins['python'],'-B',str(tool),'--train',*[str(sample/n) for n in pins['train_names']],
            '--holdout-pos',str(sample/pins['holdout']),'--hce-dir',str(sample),'--out',str(out/'sealed'),
            '--work-dir',str(out/'scratch'),'--seed',str(pins['seed']),'--diagnostic-mode','--disagreement-threshold',str(pins['threshold'])]


def diagnostic_result(cause,returncode):
    return {'status':'DIAGNOSTIC_'+{'exited':'PROCESS_EXITED','deadline':'DEADLINE','observer_error':'OBSERVER_ERROR'}.get(cause,cause.upper()),
            'acceptance':False,'returncode':returncode,'previous_failure_status':'FAIL_UNCHANGED',
            'causal_conclusion':'UNDETERMINED; sampled observations do not establish the original failure cause',
            'strength_or_training_claim':False,'data_repeat_validation':'NOT_PERFORMED_BY_THIS_DIAGNOSTIC'}


def _child_setup():
    os.sched_setaffinity(0,{4});os.nice(19-os.getpriority(os.PRIO_PROCESS,0))
    resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824))


def _load_helper(pins):
    path=HERE/pins['cleanup_helper']
    if sha(path)!=pins['cleanup_helper_sha256']:raise ValueError('cleanup helper pin changed')
    spec=importlib.util.spec_from_file_location('s18_owned_cleanup',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def _input_state(pins):
    sample=Path(pins['sample']);result={}
    actual={p.name for p in sample.iterdir() if p.suffix in ('.pos','.hce')}
    if actual!=set(pins['inputs']):raise ValueError('sample inventory changed')
    for name,expected in pins['inputs'].items():
        p=sample/name
        if p.is_symlink() or not p.is_file():raise ValueError('input symlink/nonfile')
        st=p.stat();h=sha(p)
        if st.st_size!=expected['bytes'] or h!=expected['sha256']:raise ValueError('input size/hash changed: '+name)
        result[name]={'sha256':h,'bytes':st.st_size,'mode':stat.S_IMODE(st.st_mode),'mtime_ns':st.st_mtime_ns}
    return result


def execute(pins,out,reference):
    """Single NEW diagnostic. This function is not invoked by pure tests."""
    if sys.platform!='linux':raise ValueError('Linux /proc diagnostic only')
    if sorted(os.sched_getaffinity(0))!=[4] or os.getpriority(os.PRIO_PROCESS,0)!=19:
        raise ValueError('launch with nice -n 19 taskset -c 4')
    if Path(sys.executable).resolve()!=Path(pins['python']).resolve() or sha(pins['python'])!=pins['python_sha256']:
        raise ValueError('original interpreter required')
    for name,h in pins['filter_source'].items():
        if sha(HERE/name)!=h:raise ValueError('filter source pin changed')
    if sha(pins['original_failed_result'])!=pins['original_failed_result_sha256']:raise ValueError('old failed receipt changed')
    helper=_load_helper(pins)
    before=_input_state(pins)
    out.mkdir(exist_ok=False);(out/'scratch').mkdir()
    args=child_argv(pins,out,HERE/'forge_sol_datafilter_v2_20261026.py')
    receipt={'schema':'forge-S18-instrument-diagnostic-v1','scope':'S18 NEW synthetic t500 diagnostic; no acceptance/training',
             'pins_sha256':PINS_SHA,'controller_sha256':sha(__file__),'authorization_reference':reference,'argv':args,
             'original_failed_receipt_sha256':pins['original_failed_result_sha256'],'inputs_before':before,
             'cpu':4,'nice':19,'maximum_supervised_seconds':120,'work_seconds':119,'cleanup_reserve_seconds':1,
             'budget_scope':'Popen through owned cleanup; read-only preflight and final receipt outside interval, recorded separately',
             'child_RLIMIT_AS_bytes':1073741824,'supervisor_soft_RLIMIT_AS_bytes':268435456,
             'aggregate_RAM_hard_limit':'NOT_ENFORCED; per-process AS caps plus sampled child RSS watchdog',
             'rss_watchdog_bytes':536870912,'sample_interval_seconds':1,'training_performed':False,
             'clock_ticks_per_second':os.sysconf('SC_CLK_TCK')}
    process=None;reaped=[];remaining=[];cause='observer_error';start=time.monotonic();deadline=start+120
    previous_limits=resource.getrlimit(resource.RLIMIT_AS)
    capture_paths={'stdout':out/'forge_sol_S18_diagnostic_child_20261026.stdout',
                   'stderr':out/'forge_sol_S18_diagnostic_child_20261026.stderr',
                   'supervisor':out/'forge_sol_S18_diagnostic_supervisor_20261026.stderr',
                   'telemetry':out/'forge_sol_S18_diagnostic_telemetry_20261026.jsonl'}
    files={};captures={};selector=selectors.DefaultSelector()
    try:
        for name,path in capture_paths.items():
            files[name]=path.open('xb');captures[name]=BoundedCapture(files[name],TELEMETRY_LIMIT if name=='telemetry' else STREAM_LIMIT)
        resource.setrlimit(resource.RLIMIT_AS,(268435456,1073741824))
        with helper.SubreaperScope():
            try:
                process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                         start_new_session=True,preexec_fn=_child_setup,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
                receipt.update(pid=process.pid,process_group=process.pid,subreaper_enabled=True)
                initial=observe_text(Path('/proc')/str(process.pid)/'stat',lambda t:parse_stat(t,process.pid))
                if not initial['available']:raise ValueError('cannot establish owned child start identity')
                start_ticks=initial['value']['start_ticks'];receipt['owned_start_ticks']=start_ticks
                for name in ('stdout','stderr'):
                    pipe=getattr(process,name);os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,name)
                next_sample=start
                cause='exited'
                while process.poll() is None or selector.get_map():
                    now=time.monotonic()
                    if now>=deadline-1:
                        cause='deadline';break
                    if now>=next_sample:
                        child=sample_child(process.pid,start_ticks)
                        row={'monotonic_ns':time.monotonic_ns(),'elapsed_seconds':now-start,'owned_child':child,
                             'cgroup':cgroup_observation(),'sealed_sizes':tree_sizes(out/'sealed'),'scratch_sizes':tree_sizes(out/'scratch')}
                        if not emit_json(captures['telemetry'],row):cause='telemetry_limit';break
                        status=child.get('status',{})
                        if status.get('available'):
                            for line in status['raw'].splitlines():
                                if line.startswith('VmRSS:') and int(line.split()[1])*1024>receipt['rss_watchdog_bytes']:
                                    cause='rss_watchdog';break
                        if cause=='rss_watchdog':break
                        next_sample=now+1
                    for key,_ in selector.select(timeout=min(.05,max(0,deadline-1-time.monotonic()))):
                        try:data=os.read(key.fileobj.fileno(),65536)
                        except BlockingIOError:continue
                        if not data:selector.unregister(key.fileobj);key.fileobj.close();continue
                        captures[key.data].write(data)
                        if captures[key.data].truncated:cause='stream_limit';break
                    if cause=='stream_limit':break
            except BaseException as e:
                cause='observer_error';receipt['observer_error']=type(e).__name__+': '+str(e)[:500]
                captures['supervisor'].write(traceback.format_exc(limit=12).encode())
            finally:
                if process is not None:
                    try:
                        reaped,remaining=helper._close_group(process)
                        receipt['leader_reaped']=process.returncode is not None
                    except BaseException as e:
                        cause='cleanup_error';receipt['cleanup_error']=type(e).__name__+': '+str(e)[:500]
                        captures['supervisor'].write(traceback.format_exc(limit=12).encode())
                    receipt['all_owned_group_members_after_close']=helper._all_members(process.pid)
                    receipt['descendant_wait_records']=reaped
                    receipt['remaining_owned_group']=remaining
    except BaseException as e:
        cause='observer_error';receipt['observer_error']=type(e).__name__+': '+str(e)[:500]
        if 'supervisor' in captures:captures['supervisor'].write(traceback.format_exc(limit=12).encode())
    finally:
        streams_fully_drained=not bool(selector.get_map())
        selector.close()
        if process is not None:
            for name in ('stdout','stderr'):
                pipe=getattr(process,name)
                if pipe is not None and not pipe.closed:pipe.close()
        if receipt.get('all_owned_group_members_after_close'):cause='owned_group_remains'
        receipt['child_streams_fully_drained']=streams_fully_drained
        receipt.update(diagnostic_result(cause,None if process is None else process.returncode))
        receipt['supervised_elapsed_seconds']=time.monotonic()-start
        receipt['budget_overrun_seconds']=max(0,receipt['supervised_elapsed_seconds']-120)
        receipt['captures']={n:c.summary() for n,c in captures.items()}
        receipt['peak_children_RSS_KiB']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        for stream in files.values():stream.close()
        # No final SQLite connections, output-body validation, retry, or data acceptance.
        try:
            receipt['inputs_after']=_input_state(pins)
            receipt['inputs_unchanged']=receipt['inputs_after']==before
            receipt['source_pins_unchanged']=all(sha(HERE/n)==h for n,h in pins['filter_source'].items())
            receipt['cleanup_helper_unchanged']=sha(HERE/pins['cleanup_helper'])==pins['cleanup_helper_sha256']
            receipt['controller_unchanged']=sha(__file__)==receipt['controller_sha256']
            receipt['pin_file_unchanged']=sha(PINS)==PINS_SHA
            receipt['original_failed_receipt_unchanged']=sha(pins['original_failed_result'])==pins['original_failed_result_sha256']
            if not all(receipt[k] for k in ('inputs_unchanged','source_pins_unchanged','cleanup_helper_unchanged','controller_unchanged','pin_file_unchanged','original_failed_receipt_unchanged')):
                cause='binding_changed';receipt.update(diagnostic_result(cause,None if process is None else process.returncode))
        except BaseException as e:
            cause='final_readonly_checks_error';receipt['final_readonly_checks_error']=type(e).__name__+': '+str(e)[:500]
            receipt.update(diagnostic_result(cause,None if process is None else process.returncode))
        receipt['total_after_preflight_seconds']=time.monotonic()-start
        receipt['supervisor_capture_scope']='Python exceptions within owned execution only; launch/preflight/tool transport are not captured'
        with (out/'forge_sol_S18_instrument_result_20261026.json').open('x') as stream:json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
        try:resource.setrlimit(resource.RLIMIT_AS,previous_limits)
        except (ValueError,OSError):pass  # Standalone runner; lowering hard limit is irreversible.
    print(json.dumps({'status':receipt['status'],'acceptance':False,'out':str(out)},sort_keys=True))
    return 0 if cause=='exited' and process is not None and process.returncode==0 and receipt.get('leader_reaped') and not receipt.get('all_owned_group_members_after_close') and streams_fully_drained else 1


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--describe',action='store_true');p.add_argument('--execute',action='store_true')
    p.add_argument('--out',type=Path);p.add_argument('--authorization-reference')
    args=p.parse_args(argv);pins=load_pins()
    if args.describe:
        if args.execute:p.error('describe and execute are exclusive')
        print(json.dumps({'scope':'SOURCE PREPARATION ONLY unless --execute after coordinator grant','pins_sha256':PINS_SHA,
                          'threshold':500,'seed':20261025,'work_seconds':119,'cleanup_seconds':1,'acceptance':False},sort_keys=True));return 0
    if not args.execute or args.out is None or not args.authorization_reference:p.error('execution requires --execute, NEW --out and coordinator authorization reference')
    blocked=[HERE,Path(pins['sample']),Path('/tmp/forge_sol_S18_data_20261026'),Path('/tmp/forge_sol_S18_checkpoint_20261026'),Path('/tmp/forge_sol_S16_full_pipeline_20261026')]
    out=guard_new_output(args.out,blocked)
    return execute(pins,out,args.authorization_reference)

if __name__=='__main__':raise SystemExit(main())

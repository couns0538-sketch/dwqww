"""S09 fixed-work qualification, reusing frozen S08 transport and S25 checks.

FIRST is a distinct invocation before any UCI; FULL consumes that closed receipt.
There are no playing-strength, timing, NPS or Windows adoption conclusions here.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sys
import time
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
QUAL=HERE.parent/'S08/forge_sol_S08_v2_qualify_20261026.py'
QUAL_SHA='33c92609f0b4da116625c98cb80d1b9bdd6763cfb5b3d9e3d82f06df87c4a453'
TMP=Path('/tmp/forge_sol_S09_native_20261026')

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

q=load('s09_original_runtime',QUAL)
build_api=load('s09_build_api',HERE/'forge_sol_S09_build_native_20261026.py')
api=build_api.source_api


def verify_build(path):
    data=json.loads(path.read_text());source=Path(data['source']);build=path.parent/'build'
    if data.get('schema')!='forge.S09.build.v1' or data.get('status')!='PASS_BUILD_ONLY' or data.get('source_unchanged') is not True:
        raise ValueError('closed complete S09 build required')
    if not build_api.permitted(build):raise ValueError('build outside dedicated temporary root')
    if data.get('source_before')!=data.get('source_after') or data['source_after']!=api.inventory(source):raise ValueError('source changed since build')
    if data.get('environment',{}).get('PYTHONDONTWRITEBYTECODE')!='1':raise ValueError('bytecode-off build required')
    if not data.get('commands') or any(c.get('returncode')!=0 or type(c.get('returncode')) is not int or c.get('leader_reaped') is not True or c.get('all_group_members_after_reap')!=[] or c.get('stop_reason') or c.get('error') for c in data['commands']):raise ValueError('build commands did not all close')
    artifacts=data.get('target_artifacts',{})
    required=set(build_api.STDLIB_TARGETS)|{'forge_nnue_heads_parity','forge_nnue_bit_snapshot','core_archive'}
    if data['role']=='candidate':required|={'forge_nnue_heads_tests','forge_nnue_heads_contract'}
    if (source/'tests/bad_capture_tie_tests.cpp').exists():required.add('forge_bad_capture_tie_tests')
    if set(artifacts)!=required:raise ValueError('full runtime artifact inventory differs')
    for name,item in artifacts.items():
        expected=build/('libforge_core.a' if name=='core_archive' else name)
        if item.get('path')!=str(expected) or q.shared.sha(expected)!=item.get('sha256'):raise ValueError('build artifact changed: '+name)
    recipe=build_api.audit_recipe(source,build)
    if recipe!=data.get('recipe_after'):raise ValueError('build recipe changed')
    if not all(v['unchanged'] for v in api.verify_all_baselines().values()):raise ValueError('original source baseline changed')
    return data,source,build


def verify_first(data,build_sha,engine_sha):
    if (data.get('schema')!='forge.S09.first_runtime.v1' or data.get('status')!='PASS'
        or data.get('build_receipt_sha256')!=build_sha or data.get('engine_sha256')!=engine_sha
        or data.get('commands_sent')!=['bench 11','quit'] or data.get('no_UCI_before_bench') is not True
        or data.get('bench_nodes')!=308972 or data.get('returncode')!=0
        or data.get('source_unchanged') is not True or data.get('all_artifacts_unchanged') is not True):
        raise ValueError('first bare11 source/build/engine/order receipt differs')


def verify_ctest(text,returncode,names,junit):
    normalized=[re.sub(r'^\d+:\s?','',x) for x in text.splitlines()]
    known=[x for x in normalized if x.startswith('KNOWN_FAILURE:')]
    if returncode!=0 or f'100% tests passed, 0 tests failed out of {len(names)}' not in text or len(known)!=4 or any(x.startswith(('FAIL:','PIN_MISMATCH:')) for x in normalized):raise ValueError('full actual CTest or four known cases failed')
    if any(known.count(line)!=1 for line in q.KNOWN[:2]):raise ValueError('exact WAC known pins changed')
    seen={}
    for line in (x for x in known if x not in q.KNOWN[:2]):
        m=re.fullmatch(r'KNOWN_FAILURE: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion expected (c7c8r|c2c1r) score > 100 at d1 got (c6d7|c3d2) score (-?\d+) at d1'+re.escape(q.SUFFIX),line)
        if m is None or int(m[3])<=100 or {'c7c8r':'c6d7','c2c1r':'c3d2'}[m[1]]!=m[2] or m[1] in seen:raise ValueError('promotion known case violates source-bound rule')
        seen[m[1]]=int(m[3])
    if len(seen)!=2:raise ValueError('two source-known promotion cases required')
    cases=list(ET.parse(junit).getroot().iter('testcase'));observed=[c.attrib.get('name') for c in cases]
    if sorted(observed)!=sorted(names) or any(c.find('failure') is not None or c.find('error') is not None or c.find('skipped') is not None for c in cases):raise ValueError('JUnit does not contain exactly the complete passing inventory')
    return {'registered_tests':len(names),'names':names,'known_findings':known,'promotion_scores_observed':seen,'new_failures':0}


def lifecycle(engine,out,guard):
    p=q.Process(engine,out,'uci_lifecycle',guard);cases=[]
    try:
        p.send('uci');lines=p.until(lambda x:x=='uciok')
        approved=json.loads(q.S25_PATH.with_name('forge_sol_S25_options_20261025.json').read_text())['options']
        check=q.s25.inspect_uci(('\n'.join(lines)+'\n').encode(),b'',0,approved)
        if check['status']!='PASS':raise ValueError('unchanged typed UCI contract failed')
        for threads in (1,2):
            for c in [f'setoption name Threads value {threads}','setoption name Hash value 16','setoption name OwnBook value false','ucinewgame','isready']:p.send(c)
            if p.until(lambda x:x=='readyok')!=['readyok']:raise ValueError('unexpected ready prefix')
            p.send('position startpos');p.send('go nodes 10000')
            block=p.until(lambda x:bool(q.collector.MOVE.fullmatch(x)))
            cases.append({'threads':threads,**q.verify_search(block,False)})
            p.send('isready')
            if p.until(lambda x:x=='readyok')!=['readyok']:raise ValueError('late search output')
        p.close(True);return {'typed_uci':check,'cases':cases,'SMP_nodes_not_pinned':True}
    except BaseException:p.close(False);raise


def main(argv=None):
    os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--authorization-reference',required=True)
    p.add_argument('--mode',choices=('FIRST','FULL'),required=True);p.add_argument('--build-receipt',type=Path,required=True)
    p.add_argument('--first-runtime-receipt',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--max-seconds',type=float,default=600);a=p.parse_args(argv)
    if not a.execute or not 10<=a.max_seconds<=600:p.error('explicit bounded runtime grant required')
    if len(os.sched_getaffinity(0))!=1 or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use one allocated CPU and nice19')
    if not build_api.permitted(a.out) or a.out.exists():p.error('new literal temporary S09 output required')
    if q.shared.sha(QUAL)!=QUAL_SHA or q.shared.sha(q.HERE/'forge_sol_S08_collect_profiles_20261026.py')!=q.COLLECTOR_SHA:p.error('frozen runtime transport changed')
    if shutil.disk_usage(TMP).free<32*1048576:p.error('32MiB temporary runtime start floor')
    data,source,build=verify_build(a.build_receipt);engine=build/'forge';engine_sha=q.shared.sha(engine);receipt_sha=q.shared.sha(a.build_receipt)
    if a.mode=='FULL':
        if data['role']!='candidate' or a.first_runtime_receipt is None:p.error('FULL requires candidate plus original FIRST receipt')
        verify_first(json.loads(a.first_runtime_receipt.read_text()),receipt_sha,engine_sha)
    elif a.first_runtime_receipt is not None:p.error('FIRST does not consume any previous runtime receipt')
    a.out.mkdir();start=time.monotonic();guard=q.Guard(a.out,a.out/'ROOT_STOP',start+a.max_seconds)
    result={'schema':'forge.S09.first_runtime.v1' if a.mode=='FIRST' else 'forge.S09.full_runtime.v1','status':'FAIL','mode':a.mode,'source':str(source),'source_before':api.inventory(source),'build_receipt_sha256':receipt_sha,'engine_sha256':engine_sha,'artifact_inventory':data['target_artifacts'],'controller_sha256':q.shared.sha(__file__),'transport_sha256':QUAL_SHA,'authorization_reference':a.authorization_reference,'cpu':sorted(os.sched_getaffinity(0)),'nice':19,'max_seconds':a.max_seconds,'nps_used':False,'steps':[]}
    old=q.shared.boundary_reason;q.shared.boundary_reason=guard.reason
    def step(name,value):
        result['steps'].append({'name':name,'result':value});q.shared.save_new(a.out/(f'{len(result["steps"]):02d}_'+name+'.json'),value);print(json.dumps({'stage':name,'status':'PASS'}),flush=True)
    def command(argv,label):
        r=q.shared.run_owned(argv,a.out,label,a.out,guard.deadline)
        if r.get('error') or r.get('stop_reason') or r.get('returncode')!=0 or r.get('all_group_members_after_reap'):raise RuntimeError('owned command failed or open: '+label)
        return r
    try:
        if a.mode=='FIRST':
            q.engine_once(engine,a.out,'FIRST_bare11',['bench 11'],lambda x:bool(q.collector.BENCH.fullmatch(x)),guard)
            checked=q.s25.inspect_bench((a.out/'FIRST_bare11.stdout').read_bytes(),(a.out/'FIRST_bare11.stderr').read_bytes(),0)
            if checked['status']!='PASS':raise ValueError('FIRST exact bare11 EOF contract failed')
            result.update(commands_sent=['bench 11','quit'],no_UCI_before_bench=True,bench_nodes=308972,returncode=0,stderr_sha256=q.shared.sha(a.out/'FIRST_bare11.stderr'))
            step('FIRST_bare11',checked)
        else:
            for depth,nodes in q.REFS.items():
                label='bench_'+str(depth);q.engine_once(engine,a.out,label,[f'bench {depth}'],lambda x:bool(q.collector.BENCH.fullmatch(x)),guard)
                checked=q.s25.inspect_bench((a.out/(label+'.stdout')).read_bytes(),(a.out/(label+'.stderr')).read_bytes(),0,depth,nodes)
                if checked['status']!='PASS':raise ValueError('fixed reference/EOF bench failed: '+str(depth))
                step(label,checked)
            for name,position,expected in [('startpos','startpos',4865609),('kiwipete','fen '+q.KIWI,193690690)]:
                label='perft5_'+name;lines=q.engine_once(engine,a.out,label,['position '+position,'go perft 5'],lambda x:bool(re.fullmatch(r'nodes \d+',x)),guard)
                if lines[-1]!='nodes '+str(expected):raise ValueError('perft reference mismatch')
                step(label,{'depth':5,'nodes':expected})
            step('UCI_T1_T2',lifecycle(engine,a.out,guard))
            ctest=q.shared.CMAKE.with_name('ctest');command([str(ctest),'--test-dir',str(build),'--show-only=json-v1'],'CTest_inventory_before')
            inventory=json.loads((a.out/'CTest_inventory_before.stdout').read_text());tests=inventory['tests'];names=[x['name'] for x in tests]
            expected=re.findall(r'add_test\(NAME\s+(\w+)',(source/'CMakeLists.txt').read_text())
            if len(names)!=len(set(names)) or sorted(names)!=sorted(expected):raise ValueError('configured CTest differs from source full inventory')
            for test in tests:
                primary=Path(test['command'][0])
                if test['name'].startswith('forge_') and primary!=build/test['name']:raise ValueError('CTest executable outside closed build')
            step('CTest_inventory',{'names':names,'sha256':q.shared.sha(a.out/'CTest_inventory_before.stdout')})
            r=command([str(ctest),'--test-dir',str(build),'--output-on-failure','-V','-j1','--output-junit',str(a.out/'full_ctest.xml')],'full_CTest')
            step('full_CTest',verify_ctest((a.out/'full_CTest.stdout').read_text(),r['returncode'],names,a.out/'full_ctest.xml'))
            command([str(ctest),'--test-dir',str(build),'--show-only=json-v1'],'CTest_inventory_after')
            if json.loads((a.out/'CTest_inventory_after.stdout').read_text())!=inventory:raise ValueError('CTest definitions changed during runtime')
            for label,path in [('FMA_NNUE_object',build/'CMakeFiles/forge_core.dir/src/nnue.cpp.o'),('FMA_NNUE_scope_ELF',engine)]:
                command([sys.executable,'-B',str(q.FMA),str(path)],label);value=json.loads((a.out/(label+'.stdout')).read_text())
                step(label,value)
            command(['objdump','-d','--no-show-raw-insn',str(engine)],'whole_ELF_assembly')
            if any(re.match(r'^\s*[0-9a-fA-F]+:\s+vf(?:n)?m(?:add|sub)[a-z0-9]*\b',x) for x in (a.out/'whole_ELF_assembly.stdout').read_text().splitlines()):raise ValueError('whole ELF FMA nonzero')
            step('FMA_whole_ELF',{'fma_count':0,'assembly_sha256':q.shared.sha(a.out/'whole_ELF_assembly.stdout')})
        result['status']='PASS'
    except BaseException as e:result['error']=type(e).__name__+': '+str(e)
    finally:
        q.shared.boundary_reason=old
        result['source_after']=api.inventory(source);result['source_unchanged']=result['source_before']==result['source_after']
        try:
            after,_,_=verify_build(a.build_receipt);result['all_artifacts_unchanged']=after['target_artifacts']==data['target_artifacts'] and q.shared.sha(a.build_receipt)==receipt_sha
        except Exception as e:result['all_artifacts_unchanged']=False;result['postflight_error']=type(e).__name__+': '+str(e)
        if not result['source_unchanged'] or not result['all_artifacts_unchanged']:result['status']='FAIL'
        result.update(elapsed_seconds=time.monotonic()-start,minimum_observed_free_bytes=guard.minimum)
        q.shared.save_new(a.out/'forge_sol_S09_runtime_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'mode':a.mode,'error':result.get('error')}));return 0 if result['status']=='PASS' else 1

if __name__=='__main__':
    signal.signal(signal.SIGTERM,q.shared._signal_stop);signal.signal(signal.SIGINT,q.shared._signal_stop)
    raise SystemExit(main())

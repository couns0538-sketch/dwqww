#!/usr/bin/env python3
"""Build isolated net copies and record bounded, hash-bound Forge screens.

Use import-known for documentary tables without executing a compiler or engine.
The native command never edits the input tree, pins, or historical expectations.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse
from collections import Counter
import fcntl
import difflib
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import shlex
import subprocess
import sys
import threading
import time
from types import SimpleNamespace, ModuleType
import xml.etree.ElementTree as ET

DEPTHS = ('11','13','16','20','22')
RAM_FLOOR = 3 * 1024**3
HERE = Path(__file__).resolve().parent
CORE_CTEST_NAMES = frozenset({
    'forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests',
    'forge_pawn_span_tests','forge_nearest_pawn_tests','forge_pv_metadata_tests',
    'forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests',
    'match_tool_tests','windows_validation_tests','uci_regression',
    'ponder_regression','ownbook_regression',
})

def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def read_json(path):
    def unique(pairs):
        result = {}
        for key,value in pairs:
            if key in result: raise ValueError('duplicate JSON key: '+key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(),object_pairs_hook=unique)

def write_json(path, value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def absolute_input(path, directory=False):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path: raise ValueError('input paths must be absolute and have no symlink components: '+str(path))
    if not (path.is_dir() if directory else path.is_file()): raise ValueError('input missing: '+str(path))
    return path

def new_out(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path or os.path.lexists(path): raise ValueError('--out must be a NEW absolute nonsymlink path')
    if not path.parent.is_dir(): raise ValueError('--out parent must exist')
    if any(p=='baseline' or p.startswith('dist-v') for p in path.parts): raise ValueError('protected output directory')
    path.mkdir(); return path

def snapshot(root):
    root = Path(root)
    if root.is_symlink(): raise ValueError('symlink source root')
    result = {}
    for directory,dirs,files in os.walk(root,followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in ('.git','__pycache__'))
        for name in [*dirs,*files]:
            path = Path(directory)/name
            if path.is_symlink(): raise ValueError('source symlink not permitted: '+str(path))
        for name in sorted(files):
            path = Path(directory)/name
            if not path.is_file(): raise ValueError('nonregular source input: '+str(path))
            result[str(path.relative_to(root))] = {'sha256':digest(path),'bytes':path.stat().st_size}
    return result

def copy_source(base, target, expected):
    target.mkdir()
    for relative in expected:
        path = target/relative; path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(base/relative,path)
    if snapshot(target) != expected: raise RuntimeError('private source copy differs from input snapshot')

def validate_bench(bench):
    if not isinstance(bench,dict) or set(bench) != set(DEPTHS): raise ValueError('bench-ref requires exactly d11/d13/d16/d20/d22')
    if any(type(n) is not int or n<=0 for n in bench.values()): raise ValueError('bench-ref nodes must be positive integers')
    return bench

def load_refs(path):
    refs = read_json(path)
    if refs.get('schema') != 'forge-s26-bench-refs-v1' or not isinstance(refs.get('nets'),dict): raise ValueError('invalid bench-ref schema')
    for sha,row in refs['nets'].items():
        if not re.fullmatch('[a-f0-9]{64}',sha): raise ValueError('bench-ref net key is not full SHA256')
        validate_bench(row.get('bench'))
        if row.get('wac1000') is not None and (type(row['wac1000']) is not int or not 0<=row['wac1000']<=300): raise ValueError('invalid WAC reference')
    return refs

def load_dependency(record, name):
    path = absolute_input(record['path'])
    source=path.read_bytes()
    if hashlib.sha256(source).hexdigest() != record['sha256']: raise ValueError('dependency SHA256 mismatch: '+str(path))
    # Execute exactly the checked bytes; never consult or write a sibling .pyc.
    module=ModuleType(name);module.__file__=str(path)
    exec(compile(source,str(path),'exec'),module.__dict__)
    return module

def available_bytes():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'): return int(line.split()[1])*1024
    raise RuntimeError('MemAvailable unavailable; refusing to build/go')

class ResourceStop(RuntimeError): pass

class ResourceGuard:
    def __init__(self, minimum=RAM_FLOOR, reader=available_bytes):
        if minimum<RAM_FLOOR: raise ValueError('minimum available RAM cannot be below 3 GiB')
        self.minimum,self.reader = minimum,reader
    def check(self):
        available = self.reader()
        if available<self.minimum: raise ResourceStop('available RAM below floor: %d < %d; owned work stopped'%(available,self.minimum))
        return available

def terminate_owned(process):
    if process.poll() is None:
        try: os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError: pass
        try: process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            try: os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            process.wait(timeout=2)
    # A process leader can exit while its own descendants survive.
    try: os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError: pass

class Commands:
    """Only argv processes created by this runner are signalled and waited."""
    def __init__(self, out, guard, timeout):
        self.out,self.guard,self.timeout = Path(out),guard,timeout
        self.records=[]
    def run(self, argv, label, accepted=(0,)):
        self.guard.check()
        if not argv or any(not isinstance(a,str) or '\x00' in a for a in argv): raise ValueError('nonempty string argv required')
        prefix=self.out/('%03d_%s'%(len(self.records),label)); stdout=Path(str(prefix)+'.stdout'); stderr=Path(str(prefix)+'.stderr')
        process=None;error=None;started=time.monotonic()
        try:
            with stdout.open('wb') as so,stderr.open('wb') as se:
                process=subprocess.Popen(argv,cwd=self.out,stdout=so,stderr=se,start_new_session=True,
                  env=dict(os.environ,TMPDIR=str(self.out),TMP=str(self.out),TEMP=str(self.out),PYTHONDONTWRITEBYTECODE='1',CMAKE_BUILD_PARALLEL_LEVEL='1',OMP_NUM_THREADS='1'))
                while process.poll() is None:
                    self.guard.check()
                    if time.monotonic()-started>self.timeout: raise TimeoutError('owned command deadline: '+label)
                    if stdout.stat().st_size+stderr.stat().st_size>64*1024*1024: raise RuntimeError('owned command output limit')
                    time.sleep(.025)
                if process.returncode not in accepted: raise RuntimeError('%s exited %d'%(label,process.returncode))
        except BaseException as exc:
            error=type(exc).__name__+': '+str(exc)
            raise
        finally:
            if process is not None: terminate_owned(process)
            row={'argv':argv,'cwd':str(self.out),'label':label,'pid':process.pid if process else None,'returncode':process.returncode if process else None,'child_waited':process is not None and process.returncode is not None,'error':error,'stdout':str(stdout),'stderr':str(stderr),'elapsed_seconds':time.monotonic()-started}
            self.records.append(row);write_json(self.out/'commands.json',self.records)
        return row,stdout.read_text(errors='strict'),stderr.read_text(errors='strict')

def exchange(screen, capture, guard, label, operation, postcheck=None):
    """Reuse S07 protocol/lifecycle; monitor only the children it creates here."""
    guard.check(); real_subprocess=screen.subprocess;children=[];stop=threading.Event();violation=[]
    def launch(*args,**kwargs):
        process=real_subprocess.Popen(*args,**kwargs);children.append(process);return process
    def monitor():
        while not stop.wait(.025):
            try: guard.check()
            except Exception as exc:
                violation.append(str(exc))
                for process in children:
                    if process.poll() is None: terminate_owned(process)
                return
    def guarded(send,until):
        def checked_send(line):
            guard.check(); return send(line)
        def checked_until(*args,**kwargs):
            guard.check();return until(*args,**kwargs)
        return operation(checked_send,checked_until)
    screen.subprocess=SimpleNamespace(Popen=launch,PIPE=real_subprocess.PIPE,TimeoutExpired=real_subprocess.TimeoutExpired)
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    try: value,receipt=capture.exchange(label,guarded,postcheck)
    finally:
        stop.set();thread.join(timeout=3);screen.subprocess=real_subprocess
        for process in children:
            if process.poll() is None: terminate_owned(process)
        for receipt in capture.records:
            for stream in ('stdin','stdout','stderr'):
                receipt[stream]['path']=str((capture.out/receipt[stream]['path']).resolve())
        write_json(capture.out/'processes.json',capture.records)
    if violation: raise ResourceStop(violation[0])
    if receipt['status']!='PASS': raise RuntimeError('engine exchange failed: '+label+': '+str(receipt.get('error')))
    return value

def bench_five(screen, engine, out, guard, timeout):
    out.mkdir();capture=screen.Capture(out,[str(engine)],timeout);result={}
    # The first process is deliberately bare bench11, before any UCI exchange.
    def bare(send,until):
        send('bench 11'); return screen.parse_bench(until(lambda line:bool(screen.BENCH.fullmatch(line))),11)
    first=exchange(screen,capture,guard,'FIRST_BARE_BENCH11',bare,lambda lines:screen.parse_bench(lines,11))
    for depth in DEPTHS:
        def operation(send,until):
            screen.configure(send,until,screen.option_commands({}),[]);send('bench '+depth)
            return screen.parse_bench(until(lambda line:bool(screen.BENCH.fullmatch(line))),int(depth))
        result[depth]=exchange(screen,capture,guard,'bench_d'+depth,operation,lambda lines,d=int(depth):screen.parse_bench(lines,d))
    if first!=result['11']: raise RuntimeError('first bare bench11 differs from configured bench11')
    return result

def wac_screen(screen, engine, positions, proof, out, guard, timeout):
    out.mkdir();capture=screen.Capture(out,[str(engine)],timeout);rows=[]
    def operation(send,until):
        names=screen.configure(send,until,screen.option_commands({}),[])
        if 'Clear Hash' not in names: raise ValueError('Clear Hash not advertised')
        for row in positions:
            send('ucinewgame');send('setoption name Clear Hash');send('isready');until(lambda line:line=='readyok')
            send('position fen '+row['board'].fen());send('go movetime 1000')
            lines=until(lambda line:line.startswith('bestmove '),timeout=timeout+1)
            tokens=lines[-1].split()
            if len(tokens) not in (2,4) or (len(tokens)==4 and tokens[2]!='ponder'): raise ValueError('malformed WAC bestmove')
            rows.append(screen.score_bestmove(row,tokens[1]))
    exchange(screen,capture,guard,'WAC300_1000MS',operation)
    if len(rows)!=300 or any(not row['legal'] for row in rows): raise RuntimeError('WAC incomplete or illegal bestmove')
    result={'status':'PASS','movetime_ms':1000,'evaluated':len(rows),'solved':sum(row['bestmove_allowed'] for row in rows),'suite':proof,'results':rows}
    write_json(out/'result.json',result)
    return {key:value for key,value in result.items() if key!='results'} | {'results_path':str(out/'result.json')}

def observe_pins(screen, pin_helper, engine, out, guard, timeout):
    out.mkdir();capture=screen.Capture(out,[str(engine)],timeout);rows=[]
    for case in pin_helper.CASES:
        label,fen,depth,hashmb,documented_move,documented_score=case
        def operation(send,until):
            commands=screen.option_commands({});commands[1]='setoption name Hash value '+str(hashmb)
            screen.configure(send,until,commands,[]);send('ucinewgame');send('isready');until(lambda line:line=='readyok')
            send('position fen '+fen);send('go depth '+str(depth));lines=until(lambda line:line.startswith('bestmove '))
            best=lines[-1].split()[1];completed=[]
            for line in lines:
                m=re.fullmatch(r'info depth (\d+).*? score (cp|mate) (-?\d+)(?: .*?)? pv (\S+)(?: .*)?',line)
                if m and int(m[1])==depth: completed.append(m)
            if not completed: raise ValueError('pin observation missing completed-depth score/PV')
            m=completed[-1]
            if m[4]!=best: raise ValueError('pin bestmove/PV disagree')
            return {'case':label,'fen':fen,'depth':depth,'Hash':hashmb,'bestmove':best,'score_kind':m[2],'score':int(m[3]),'pv0':m[4],
                    'documented_move':documented_move,'documented_score':documented_score,'documented_pin_matches':best==documented_move and m[2]=='cp' and (int(m[3])==documented_score if documented_score is not None else int(m[3])>100)}
        row=exchange(screen,capture,guard,label,operation)
        row['raw']={stream:pin_helper.raw_record(Path(capture.records[-1][stream]['path']).read_bytes()) for stream in ('stdin','stdout','stderr')}
        rows.append(row)
    result={'status':'OBSERVED_ONLY','pins_edited':False,'cases':rows}
    write_json(out/'result.json',result);return result

def bind_allowlist(allowlist, source_sha256, net_sha256):
    bound=dict(allowlist,rules=[dict(rule) for rule in allowlist.get('rules',[])])
    for profile in allowlist.get('profiles',[]):
        if profile.get('test_source_sha256')==source_sha256 and profile.get('net_sha256')==net_sha256:
            bound['required_groups']=profile['required_groups']
    for proposal in allowlist.get('pins',[]):
        if proposal.get('test_source_sha256')!=source_sha256 or proposal.get('net_sha256')!=net_sha256: continue
        if proposal.get('review_status')!='REVIEWED': raise ValueError('matching pin proposal is not REVIEWED')
        lines=proposal.get('exact_lines')
        if not isinstance(lines,list) or not lines or any(not isinstance(x,str) or any(c in x for c in '\r\n\x00') for x in lines): raise ValueError('reviewed pins require literal diagnostic lines')
        for i,line in enumerate(lines):
            if not reviewable_pin_line(line):raise ValueError('reviewed pins cannot allow unknown failure cases: '+line)
            matching=[rule for rule in bound['rules'] if re.fullmatch(rule['pattern'],line)]
            group=matching[0].get('group','reviewed_'+str(i)) if len(matching)==1 else 'reviewed_'+str(i)
            bound['rules'].append({'pattern':re.escape(line),'max_count':1,'group':group,'exact_reviewed':True})
        if 'required_groups' in proposal:bound['required_groups']=proposal['required_groups']
    return bound

def reviewable_pin_line(line):
    return bool(re.match(r'^(?:PIN_MISMATCH: (?:WAC 001 documented |unrestricted promotion documented )|FAIL: (?:WAC 001 (?:expected |score )|unrestricted search chooses the winning rook underpromotion over stalemating queen promotion$)|KNOWN_FAILURE: (?:WAC 001 (?:expected |score expected )|unrestricted search chooses the winning rook underpromotion over stalemating queen promotion expected ))',line))

def classify_test_output(text, allowlist):
    counts=Counter();groups=Counter();accepted=[]
    for line in text.splitlines():
        if not re.match(r'^(?:FAIL:|KNOWN_FAILURE:|PIN_MISMATCH:)',line): continue
        matches=[i for i,rule in enumerate(allowlist.get('rules',[])) if re.fullmatch(rule['pattern'],line)]
        exact=[i for i in matches if allowlist['rules'][i].get('exact_reviewed')]
        if exact:matches=exact
        if len(matches)!=1: raise ValueError('unallowlisted test diagnostic: '+line)
        index=matches[0];counts[index]+=1
        groups[allowlist['rules'][index].get('group',str(index))]+=1
        if counts[index]>allowlist['rules'][index]['max_count']: raise ValueError('known failure count exceeded: '+line)
        accepted.append(line)
    if sum(not line.startswith('PIN_MISMATCH:') for line in accepted)>allowlist.get('max_total',4): raise ValueError('total known failure count exceeded')
    for group,required in allowlist.get('required_groups',{}).items():
        if groups[group]!=required: raise ValueError('reviewed diagnostic count mismatch: '+group)
    return {'status':'PASS','known_diagnostics':accepted,'counts':dict(counts),'groups':dict(groups)}

def validate_ctest_names(names):
    """The configured inventory may extend, but never omit, the Forge core."""
    if not isinstance(names,(list,tuple,set,frozenset)) or not names:
        raise ValueError('explicit configured CTest names required')
    if any(not isinstance(name,str) or not name or name!=name.strip() or any(c in name for c in '\r\n\x00$\\;') for name in names):
        raise ValueError('invalid configured CTest name')
    if len(set(names))!=len(names):raise ValueError('duplicate configured CTest name')
    if not CORE_CTEST_NAMES.issubset(names):
        raise ValueError('configured CTest inventory omitted canonical core/Python/UCI suites: '+str(sorted(CORE_CTEST_NAMES-set(names))))
    return sorted(names)

def ctest_inventory_binding(source, build):
    """Hash the definitions and generated inventory; do not run CMake/CTest."""
    source=absolute_input(Path(source),True);build=absolute_input(Path(build),True)
    definitions=sorted({source/'CMakeLists.txt',*source.rglob('CMakeLists.txt'),*source.rglob('*.cmake')})
    generated=sorted(build.rglob('CTestTestfile.cmake'))
    if not generated:raise ValueError('configured CTestTestfile.cmake inventory missing')
    names=[]
    for path in generated:
        absolute_input(path)
        for line in path.read_text().splitlines():
            if line.lstrip().startswith('#') or not re.search(r'\badd_test\s*\(',line,re.I):continue
            # CMake-generated static add_test names: bare, quoted, or bracketed.
            # Unknown/dynamic forms fail closed rather than declaring a partial suite.
            match=re.match(r'^\s*add_test\s*\(\s*(?:"([^"\\\r\n]+)"|\[(=*)\[(.*?)\]\2\]|([^\s()]+))(?=\s|\))',line,re.I)
            if not match:raise ValueError('unsupported generated CTest declaration: '+line)
            names.append(match[1] if match[1] is not None else (match[3] if match[3] is not None else match[4]))
    configured=validate_ctest_names(names)
    def hashes(paths,root):
        return {str(path.relative_to(root)):{'sha256':digest(absolute_input(path)),'bytes':path.stat().st_size} for path in paths}
    return {'source_root':str(source),'build_root':str(build),
            'source_definitions':hashes(definitions,source),
            'configured_files':hashes([build/'CMakeCache.txt',*generated],build),
            'configured_names':configured}

def load_ctest_inventory(path, source, build):
    """Require both real discovery metadata and every generated declaration."""
    data=read_json(path)
    if not isinstance(data,dict) or data.get('kind')!='ctestInfo':raise ValueError('invalid CTest discovery object/kind')
    version=data.get('version')
    if not isinstance(version,dict) or type(version.get('major')) is not int or version['major']!=1 or type(version.get('minor')) is not int or version['minor']!=0:
        raise ValueError('unsupported CTest discovery JSON version')
    tests=data.get('tests')
    if not isinstance(tests,list) or not tests:raise ValueError('CTest discovery tests must be a nonempty list')
    names=[];commands={}
    for case in tests:
        if not isinstance(case,dict):raise ValueError('CTest discovery element must be an object')
        name=case.get('name');command=case.get('command')
        if not isinstance(name,str):raise ValueError('CTest discovery name must be a string')
        if not isinstance(command,list) or not command or any(not isinstance(token,str) or not token or '\x00' in token for token in command):
            raise ValueError('CTest discovery command must be a nonempty string argv')
        names.append(name);commands[name]=command
    names=validate_ctest_names(names);binding=ctest_inventory_binding(source,build)
    if names!=binding['configured_names']:raise ValueError('CTest discovery differs from generated configured test set')
    return {'schema':'forge-s26-ctest-inventory-v4','expected_names':names,'commands':commands,
            'discovery':{'path':str(Path(path).resolve()),'sha256':digest(path)},'binding':binding}

def check_ctest(path, returncode, allowlist, expected_names=None):
    expected_names=validate_ctest_names(expected_names)
    root=ET.parse(path).getroot();cases=list(root.iter('testcase'))
    if not cases: raise ValueError('CTest produced no test cases')
    rows=[];failures=0;names=set()
    for case in cases:
        name=case.attrib.get('name','');failed=list(case.findall('failure'))+list(case.findall('error'));failures+=bool(failed)
        if not name or name in names: raise ValueError('empty or duplicate CTest case name')
        names.add(name)
        if case.find('skipped') is not None: raise ValueError('CTest skipped test: '+name)
        text='\n'.join(''.join(item.itertext()) for item in case if item.tag in ('failure','error','system-out','system-err'))
        attributes=' '.join(str(x) for item in [case,*failed] for x in item.attrib.values())
        if re.search(r'Segmentation fault|\bSIG(?:SEGV|ABRT|KILL|TERM|ILL|FPE|BUS)\b|Timeout|timed out|Subprocess aborted|Exception:|AddressSanitizer|runtime error:',text+' '+attributes,re.I): raise ValueError('abnormal CTest termination: '+name)
        if any(item.attrib.get('message','') not in ('','Failed') for item in failed): raise ValueError('unrecognized CTest failure status: '+name)
        selected=allowlist if name==allowlist['allowed_test_failure'] else dict(allowlist,required_groups={})
        proof=classify_test_output(text,selected)
        if proof['known_diagnostics'] and name!=allowlist['allowed_test_failure']: raise ValueError('known diagnostic from unexpected test: '+name)
        if failed and (name!=allowlist['allowed_test_failure'] or not proof['known_diagnostics'] or case.find('error') is not None): raise ValueError('unexpected CTest failure: '+name+': '+text)
        rows.append({'name':name,'failed':bool(failed),**proof})
    if allowlist['allowed_test_failure'] not in names: raise ValueError('CTest omitted required forge_tests')
    if names!=set(expected_names):raise ValueError('CTest cases differ from configured inventory; missing='+str(sorted(set(expected_names)-names))+' unexpected='+str(sorted(names-set(expected_names))))
    if returncode not in (0,8) or (returncode!=0 and not failures) or (returncode==0 and failures): raise ValueError('CTest exit/XML failure status inconsistent')
    return {'status':'PASS','test_cases':rows,'returncode':returncode,'junit':str(Path(path).resolve()),'expected_names':expected_names,'inventory_status':'PASS'}

def record_pin_proposal(source, out, net_sha256, observations):
    """Write an unapplied documented-pin diff; original expectations stay intact."""
    test=Path(source)/'tests/tests.cpp';original=test.read_text();proposed=original
    rows={row['case']:row for row in observations['cases']};unsupported=[]
    wac=rows.get('WAC001')
    if wac and wac.get('score_kind')=='cp' and wac.get('depth')==12 and wac.get('pv0')==wac.get('bestmove') and re.fullmatch('[a-h][1-8][a-h][1-8][qrbn]?',wac['bestmove']):
        for pattern,value in [(r'(constexpr std::string_view documented_wac_move = ")[a-h][1-8][a-h][1-8][qrbn]?(";)',wac['bestmove']),
                              (r'(constexpr int documented_wac_score = )-?\d+(;)',str(wac['score']))]:
            proposed,count=re.subn(pattern,lambda match:match[1]+value+match[2],proposed)
            if count!=1:unsupported.append(pattern)
    else:unsupported.append('WAC observation not suitable for a documented d12 cp/PV pin')
    white,black=rows.get('promotion_white'),rows.get('promotion_black')
    if white and black and all(row.get('score_kind')=='cp' and row.get('score',0)>100 and row.get('depth')==1 and row.get('pv0')==row.get('bestmove') for row in (white,black)):
        pattern=r'(const std::string_view documented_king_text = mirrored \? ")[a-h][1-8][a-h][1-8](" : ")[a-h][1-8][a-h][1-8](";)'
        proposed,count=re.subn(pattern,lambda match:match[1]+black['bestmove']+match[2]+white['bestmove']+match[3],proposed)
        if count!=1:unsupported.append('documented promotion pin source contract not found')
    patch=''.join(difflib.unified_diff(original.splitlines(True),proposed.splitlines(True),fromfile='a/tests/tests.cpp',tofile='b/tests/tests.cpp')) if not unsupported else ''
    target=Path(out)/'documented_pins_ONLY_UNREVIEWED.patch';target.write_text(patch)
    result={'review_status':'UNREVIEWED','applied':False,'net_sha256':net_sha256,'test_source_sha256':digest(test),'original_expectations_changed':False,
            'observations':observations,'unsupported_source_contracts':unsupported,'patch':str(target),'patch_sha256':digest(target),
            'patch_status':'UNSUPPORTED_SOURCE_CONTRACT' if unsupported else ('PROPOSED_DOCUMENTED_PINS_ONLY' if patch else 'NO_DOCUMENTED_PIN_CHANGE'),
            'proposed_allowlist_entry':{'review_status':'UNREVIEWED','net_sha256':net_sha256,'test_source_sha256':digest(test),'exact_lines':[]}}
    write_json(Path(out)/'pin_proposal.json',result);return result

def program(path):
    if not Path(path).is_absolute():
        path=shutil.which(path)
        if path is None: raise ValueError('program missing')
    path=absolute_input(Path(path).resolve(strict=True))
    if not os.access(path,os.X_OK): raise ValueError('program not executable: '+str(path))
    return path

def reference_for(refs, net):
    row=refs['nets'].get(digest(net))
    if row is None: raise ValueError('no frozen bench reference for net SHA256: '+str(net))
    return row

def audit_build_recipe(recipe, source, build, compiler):
    """Check actual CMake commands, including CTest/support translation units."""
    compiler=Path(compiler).resolve(strict=True);cache=build/'CMakeCache.txt';cache_text=cache.read_text()
    cached=Path(recipe.compiler_from_cache(cache_text)).resolve(strict=True)
    if cached!=compiler:raise ValueError('effective recipe compiler/cache identity differs')
    expected={'CMAKE_BUILD_TYPE':'Release','FORGE_NATIVE':'OFF','CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF','CMAKE_EXPORT_COMPILE_COMMANDS':'ON','CMAKE_CXX_FLAGS':recipe.FLAGS}
    for name,value in expected.items():
        matches=re.findall(r'^'+name+r':[^=]+=(.*)$',cache_text,re.M)
        if matches!=[value]:raise ValueError('effective recipe CMake cache mismatch: '+name)
    command_path=build/'compile_commands.json';entries=read_json(command_path)
    if not isinstance(entries,list) or not entries:raise ValueError('effective recipe has no translation units')
    links={target:(build/('CMakeFiles/'+target+'.dir/link.txt')).read_text() for target in ('forge','forge_core')}
    signature=recipe.recipe_signature(entries,source,build,links)
    if signature['status']!='PASS':raise ValueError('effective recipe S27 guard rejected: '+str(signature['errors']))
    strict_bad={'-Ofast','-ffast-math','-funsafe-math-optimizations','-fassociative-math','-freciprocal-math','-ffinite-math-only','-fno-signed-zeros','-fno-trapping-math','-ffp-model=fast','-ffp-model=aggressive'}
    def unsafe(tokens):
        return [token for token in tokens if token in strict_bad or token.startswith(('@','-flto')) or re.match(r'^-f(?:auto-)?profile',token) or (token.startswith('-ffp-contract=') and token!='-ffp-contract=off')]
    units=[];seen=set()
    for entry in entries:
        directory=Path(entry['directory']);file=Path(entry['file']);file=file if file.is_absolute() else directory/file
        file=file.resolve(strict=True)
        if file in seen:raise ValueError('effective recipe duplicate translation unit: '+str(file))
        seen.add(file);tokens=entry.get('arguments') or shlex.split(entry['command'])
        if not tokens or any(not isinstance(token,str) or not token or '\x00' in token for token in tokens):raise ValueError('malformed effective recipe argv')
        if not Path(tokens[0]).is_absolute() or Path(tokens[0]).resolve(strict=True)!=compiler:raise ValueError('effective recipe translation-unit compiler mismatch')
        # Presence alone is insufficient: later options can override these pins.
        machine=[token for token in tokens if token.startswith('-m')]
        if sorted(machine)!=['-march=x86-64-v3','-mtune=znver5']:raise ValueError('effective recipe ISA/tuning mismatch: '+str(file))
        standards=[token for token in tokens if token.startswith('-std=')]
        if len(standards)!=1 or standards[0] not in ('-std=c++20','-std=gnu++20'):raise ValueError('effective recipe C++20 mode mismatch: '+str(file))
        definitions=[]
        for i,token in enumerate(tokens):
            if token in ('-D','-U'):
                if i+1>=len(tokens):raise ValueError('truncated macro flag')
                definitions.append(token+tokens[i+1])
            elif token.startswith(('-D','-U')):definitions.append(token)
        hidden=[token for token in definitions if re.match(r'^-[DU]FORGE_NNUE_HIDDEN(?:=|$)',token)]
        if hidden!=['-DFORGE_NNUE_HIDDEN=256']:raise ValueError('effective recipe H256 macro mismatch: '+str(file))
        if '-fno-fast-math' not in tokens or '-ffp-contract=off' not in tokens or unsafe(tokens):raise ValueError('effective recipe unsafe float/PGO/LTO flags: '+str(file))
        units.append({'source':str(file),'source_sha256':digest(file),'argv_sha256':hashlib.sha256(json.dumps(tokens,separators=(',',':')).encode()).hexdigest()})
    link_hashes={}
    for path in sorted(build.rglob('link.txt')):
        for line in path.read_text().splitlines():
            if unsafe(shlex.split(line)):raise ValueError('effective recipe unsafe linker flags: '+str(path))
        link_hashes[str(path)]=digest(path)
    return {'status':'PASS','canonical_flags':recipe.FLAGS,'compiler':{'path':str(compiler),'sha256':digest(compiler)},
            'cache':{'path':str(cache),'sha256':digest(cache)},'compile_commands':{'path':str(command_path),'sha256':digest(command_path)},
            'translation_units':units,'link_recipes_sha256':link_hashes,'s27_signature':signature}

def one_net(args, deps, positions, suite, guard, source_base, net, job, ref, allow):
    guard.check();job.mkdir();base_before=snapshot(source_base);private=job/'source';copy_source(source_base,private,base_before)
    shutil.copy2(net,private/'src/nnue_weights.inc');private_before=snapshot(private)
    build=job/'build';commands=Commands(job,guard,args.timeout)
    row={'id':ref.get('id',net.stem),'job':str(job),'private_source':str(private),'base':str(source_base),'source_before':base_before,
         'net_path':str(net),'net_md5':digest(net,'md5'),'net_sha256':digest(net),'private_source_sha256_before':private_before,'bench_reference':ref,'status':'FAIL'}
    write_json(job/'progress.json',row)
    try:
        flags=['-DCMAKE_BUILD_TYPE=Release','-DFORGE_NATIVE=OFF','-DCMAKE_CXX_FLAGS='+deps['recipe'].FLAGS,
               '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_CXX_COMPILER='+str(args.cxx)]
        commands.run([str(args.cmake),'-S',str(private),'-B',str(build),*flags],'configure')
        compiler=Path(deps['recipe'].compiler_from_cache((build/'CMakeCache.txt').read_text())).resolve(strict=True)
        if compiler!=args.cxx:raise ValueError('configured compiler differs from pinned compiler')
        receipt,version,version_error=commands.run([str(compiler),'-dumpfullversion','-dumpversion'],'compiler_version')
        if not version.strip() or version_error:raise ValueError('compiler version query failed')
        row['compiler']={'path':str(compiler),'sha256':digest(compiler),'version_stdout':version,'version_command':receipt}
        before=audit_build_recipe(deps['recipe'],private,build,compiler);write_json(job/'recipe_before.json',before)
        row['recipe_before']={'path':str(job/'recipe_before.json'),'sha256':digest(job/'recipe_before.json'),'translation_units':len(before['translation_units']),'status':'PASS','canonical_flags':deps['recipe'].FLAGS}
        commands.run([str(args.cmake),'--build',str(build),'--parallel','1'],'build')
        after=audit_build_recipe(deps['recipe'],private,build,compiler);write_json(job/'recipe_after.json',after)
        row['recipe_after']={'path':str(job/'recipe_after.json'),'sha256':digest(job/'recipe_after.json'),'translation_units':len(after['translation_units']),'status':'PASS','canonical_flags':deps['recipe'].FLAGS}
        if before!=after:raise ValueError('effective recipe or compiler changed during build')
        engine=build/'forge';absolute_input(engine)
        objects=list(build.rglob('nnue.cpp.o'))
        if len(objects)!=1: raise ValueError('expected exactly one NNUE object')
        binaries={str(p):digest(p) for p in (engine,objects[0])};row.update(engine=str(engine),binary_sha256_before=binaries)
        row['bench']=bench_five(deps['screen'],engine,job/'bench',guard,args.timeout)
        if row['bench']!=ref['bench']: raise ValueError('bench differs from frozen reference')
        row['fma']={'status':'PASS','fma_count':0,'artifacts':[]}
        for n,p in enumerate((engine,objects[0])):
            _,assembly,_=commands.run([str(args.objdump),'-d','-C','--no-show-raw-insn',str(p)],'objdump_'+str(n))
            check=deps['fma'].check_assembly(assembly);row['fma']['artifacts'].append({'path':str(p),'sha256':digest(p),**check})
        row['wac']=wac_screen(deps['screen'],engine,positions,suite,job/'wac',guard,args.timeout)
        expected=ref.get('wac1000');row['wac']['reference_status']='UNKNOWN' if expected is None else ('PASS' if abs(row['wac']['solved']-expected)<=3 else 'FAIL')
        row['wac']['reference_solved']=expected
        # A score mismatch is a blocking verdict, not a failed engine exchange.
        # Preserve the remaining cheap correctness evidence in this same attempt.
        wac_reference_failed=row['wac']['reference_status']=='FAIL'
        row['pin_observations']=observe_pins(deps['screen'],deps['pins'],engine,job/'pins',guard,args.timeout)
        if args.record_pins:row['pin_proposal']=record_pin_proposal(private,job,digest(net),row['pin_observations'])
        discovery,_,discovery_error=commands.run([str(args.ctest),'--test-dir',str(build),'--show-only=json-v1'],'ctest_discovery')
        if discovery_error:raise ValueError('CTest discovery wrote stderr; inventory not qualified')
        inventory=load_ctest_inventory(Path(discovery['stdout']),private,build)
        row['ctest_inventory']=inventory;write_json(job/'ctest_inventory.json',inventory)
        junit=job/'ctest.xml';receipt,_,_=commands.run([str(args.ctest),'--test-dir',str(build),'--output-on-failure','--no-tests=error','--output-junit',str(junit)],'ctest',accepted=(0,8))
        if args.record_pins:
            text='\n'.join(''.join(item.itertext()) for item in ET.parse(junit).getroot().iter() if item.tag in ('failure','error','system-out','system-err'))
            diagnostics=list(dict.fromkeys(line for line in text.splitlines() if re.match(r'^(?:FAIL:|KNOWN_FAILURE:|PIN_MISMATCH:)',line)))
            row['pin_proposal']['proposed_allowlist_entry']['exact_lines']=[line for line in diagnostics if reviewable_pin_line(line)]
            row['pin_proposal']['unreviewable_diagnostics']=[line for line in diagnostics if not reviewable_pin_line(line)]
            write_json(job/'pin_proposal.json',row['pin_proposal'])
        try:
            if ctest_inventory_binding(private,build)!=inventory['binding']:raise ValueError('CTest source/build inventory changed during test run')
            row['ctest']=check_ctest(junit,receipt['returncode'],bind_allowlist(allow,digest(private/'tests/tests.cpp'),digest(net)),expected_names=inventory['expected_names'])
        except ValueError as exc:
            row['ctest']={'status':'FAIL','junit':str(junit),'returncode':receipt['returncode'],'failure':type(exc).__name__+': '+str(exc)}
            raise
        row['binary_sha256_after']={str(p):digest(p) for p in (engine,objects[0])}
        if row['binary_sha256_after']!=binaries: raise RuntimeError('binary/object changed during qualification')
        if snapshot(private)!=private_before: raise RuntimeError('private source changed during qualification')
        if wac_reference_failed:raise ValueError('WAC differs from documentary reference by more than3; pin/CTest evidence retained')
        row['status']='PASS'
    finally:
        row['source_after']=snapshot(source_base)
        if 'compiler' in row:
            row['compiler']['sha256_after']=digest(row['compiler']['path'])
            if row['compiler']['sha256_after']!=row['compiler']['sha256']:row['status']='FAIL';row['input_mutation']='compiler changed'
        if 'binary_sha256_before' in row:
            row['binary_sha256_after']={path:digest(path) if Path(path).is_file() else None for path in row['binary_sha256_before']}
            if row['binary_sha256_after']!=row['binary_sha256_before']:row['status']='FAIL';row['input_mutation']='binary/object changed'
        if row['source_after']!=base_before: row['status']='FAIL';row['input_mutation']='base source changed'
        write_json(job/'progress.json',row)
    if row['status']!='PASS': raise RuntimeError(row.get('input_mutation','net job failed'))
    write_json(job/'table.json',row)
    columns=['net','md5','sha256',*('d'+d for d in DEPTHS),'FMA','WAC1000','reference','CTest']
    values=[row['id'],row['net_md5'],row['net_sha256'],*(str(row['bench'][d]) for d in DEPTHS),'0',str(row['wac']['solved']),row['wac']['reference_status'],'PASS']
    (job/'table.md').write_text('| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n| '+' | '.join(values)+' |\n')
    return row

def resource_lease(cpu):
    allowed=os.sched_getaffinity(0)
    if cpu is None: cpu=min(allowed)
    if cpu not in allowed: raise ValueError('requested CPU not in current affinity')
    os.sched_setaffinity(0,{cpu});nice=os.getpriority(os.PRIO_PROCESS,0)
    if nice>19: raise ValueError('unsupported nice priority')
    if nice<19: os.nice(19-nice)
    return {'nice':os.getpriority(os.PRIO_PROCESS,0),'affinity':sorted(os.sched_getaffinity(0)),'scope':'This batch and its owned children only; no host limits changed'}

def manifest(out):
    targets=[p for p in out.rglob('*') if p.is_file() and p!=out/'SHA256SUMS.txt']
    (out/'SHA256SUMS.txt').write_text(''.join(digest(p)+'  '+str(p.relative_to(out))+'\n' for p in sorted(targets)))

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0]=='import-known':
        p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('--bench-ref',required=True);p.add_argument('--out',required=True);a=p.parse_args(argv)
        refs=load_refs(absolute_input(a.bench_ref))
        checked={a.bench_ref:digest(a.bench_ref)}
        for path,expected in refs.get('sources',{}).items():
            absolute_input(path)
            if digest(path)!=expected:raise ValueError('documentary source hash mismatch')
            checked[path]=expected
        for expected,row in refs['nets'].items():
            if row.get('path'):
                absolute_input(row['path'])
                if digest(row['path'])!=expected or digest(row['path'],'md5')!=row['md5']:raise ValueError('documentary net identity mismatch')
                checked[row['path']]=expected
        out=new_out(a.out)
        result={'status':'PASS','evidence_kind':'SUPPLIED_DOCUMENTARY_IMPORT_NO_RERUN','engine_execution':False,'input_sha256':{a.bench_ref:digest(a.bench_ref)},'nets':[dict(row,net_sha256=sha) for sha,row in refs['nets'].items() if row.get('id')!='lock']}
        result['input_sha256']=checked
        for row in result['nets']:
            if not re.fullmatch(r'[A-Za-z0-9_-]+',row['id']):raise ValueError('unsafe documentary net id')
            text='SUPPLIED DOCUMENTARY IMPORT — NO BUILD, ENGINE RUN, OR LOCAL CTEST.\n\n'
            text+='| net | d11 | d13 | d16 | d20 | d22 | WAC1000 documentary | local FMA/CTest |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n'
            text+='| '+row['id']+' | '+' | '.join(str(row['bench'][d]) for d in DEPTHS)+' | '+('UNKNOWN' if row['wac1000'] is None else str(row['wac1000']))+' | UNVERIFIED |\n\n'+row['wac_evidence']+'\n'
            (out/(row['id']+'_DOCUMENTARY.md')).write_text(text)
        write_json(out/'result.json',result);manifest(out);print(json.dumps({'status':'PASS','out':str(out),'engine_execution':False}));return 0
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base','out','bench-ref','allowlist','suite','lock-file'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--net',action='append',required=True,type=Path);p.add_argument('--compare-lock',type=Path)
    p.add_argument('--dependencies',type=Path,default=HERE/'forge_sol_S26_dependencies_20261026.json')
    for name in ('cmake','ctest','objdump'):p.add_argument('--'+name,default=name)
    p.add_argument('--cxx',default='/usr/bin/c++',help='Resolved compiler pinned into CMake and checked against every actual TU')
    p.add_argument('--timeout',type=float,default=1800);p.add_argument('--cpu',type=int)
    p.add_argument('--min-available-bytes',type=int,default=RAM_FLOOR)
    p.add_argument('--evidence-label',choices=('LOCAL_NATIVE','SYNTHETIC'),default='LOCAL_NATIVE')
    p.add_argument('--record-pins',action='store_true',help='Write UNREVIEWED, unapplied documented-pin patch/proposal; never changes tests or allows failures')
    args=p.parse_args(argv)
    def cancelled(signum,frame):raise KeyboardInterrupt('signal '+str(signum)+'; owned work cancelled')
    signal.signal(signal.SIGTERM,cancelled)
    if not math.isfinite(args.timeout) or args.timeout<=0: raise ValueError('timeout must be finite positive')
    args.base=absolute_input(args.base,True)
    if args.compare_lock:args.compare_lock=absolute_input(args.compare_lock,True)
    args.net=[absolute_input(n) for n in args.net]
    for attr in ('bench_ref','allowlist','dependencies','suite','lock_file'):setattr(args,attr,absolute_input(getattr(args,attr)))
    for attr in ('cmake','ctest','objdump','cxx'):setattr(args,attr,program(getattr(args,attr)))
    out_path=Path(args.out)
    for protected in [args.base,*args.net,*([args.compare_lock] if args.compare_lock else [])]:
        if out_path==protected or protected in out_path.parents: raise ValueError('--out cannot be inside an input')
    refs=load_refs(args.bench_ref);allow=read_json(args.allowlist)
    if allow.get('schema')!='forge-s26-allowlist-v1':raise ValueError('invalid allowlist schema')
    # Fail before any build if the supplied source expectations are not reviewed.
    for base in [args.base,*([args.compare_lock] if args.compare_lock else [])]:
        if digest(base/'tests/tests.cpp') not in allow.get('test_source_sha256',[]):raise ValueError('test-source hash not covered by allowlist')
    for net in args.net:reference_for(refs,net)
    if args.compare_lock:reference_for(refs,args.compare_lock/'src/nnue_weights.inc')
    declarations=read_json(args.dependencies)
    deps={name:load_dependency(declarations[name],'s26_'+name) for name in ('screen','fma','pins','recipe')}
    positions,suite=deps['screen'].load_wac(args.suite)
    guard=ResourceGuard(args.min_available_bytes);out=new_out(args.out)
    result={'status':'FAIL','evidence_kind':args.evidence_label,'engine_execution':False,'nets':[],'failed_nets':[],'compare_lock':None,'tool_sha256':digest(__file__),
            'absolute_out':str(out),'dependency_identity':declarations,'input_sha256_before':{str(x):digest(x) for x in [args.bench_ref,args.allowlist,args.dependencies,args.suite,*args.net,*[args.cmake,args.ctest,args.objdump,args.cxx]]}}
    try:
        guard.check()
        with args.lock_file.open('rb') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as exc:raise RuntimeError('shared flock already held; no work started') from exc
            result['resource_lease']=resource_lease(args.cpu);result['resource_lease']['flock']=str(args.lock_file)
            if args.compare_lock:
                net=args.compare_lock/'src/nnue_weights.inc'
                result['compare_lock']=one_net(args,deps,positions,suite,guard,args.compare_lock,net,out/'compare_lock',reference_for(refs,net),allow)
            for index,net in enumerate(args.net):
                job=out/('%02d_%s'%(index,digest(net)[:12]))
                try:row=one_net(args,deps,positions,suite,guard,args.base,net,job,reference_for(refs,net),allow)
                except ResourceStop:raise
                except Exception as exc:
                    row=read_json(job/'progress.json') if (job/'progress.json').is_file() else {'job':str(job),'status':'FAIL'}
                    row.update(status='FAIL',failure=type(exc).__name__+': '+str(exc));write_json(job/'table.json',row)
                    (job/'table.md').write_text('| net | status |\n| --- | --- |\n| '+net.name+' | FAIL; see table.json and raw logs |\n')
                    result['failed_nets'].append(row);write_json(out/'result.json',result)
                    if row.get('input_mutation'):raise RuntimeError('input mutation; stopping remaining nets') from exc
                    continue
                if result['compare_lock']:
                    row['compare_lock_delta']={d:row['bench'][d]-result['compare_lock']['bench'][d] for d in DEPTHS}
                    row['compare_lock_wac_delta']=row['wac']['solved']-result['compare_lock']['wac']['solved']
                result['nets'].append(row);write_json(out/'result.json',result)
            result['status']='FAIL' if result['failed_nets'] else 'PASS'
            if result['failed_nets']:result['failure']='; '.join(row['failure'] for row in result['failed_nets'])
    except (Exception,KeyboardInterrupt) as exc:
        result['failure']=type(exc).__name__+': '+str(exc)
    finally:
        # Receipts represent observed process launches even if compare-lock failed.
        receipts=[path for path in out.rglob('processes.json') if len(path.relative_to(out).parts)==3 and path.relative_to(out).parts[1] in ('bench','wac','pins')]
        result['engine_execution']=any(row.get('pid') for path in receipts for row in read_json(path))
        result['input_sha256_after']={path:digest(path) for path in result['input_sha256_before']}
        if result['input_sha256_before']!=result['input_sha256_after']:result.update(status='FAIL',failure='input file changed during batch')
        write_json(out/'result.json',result);manifest(out)
    print(json.dumps({'status':result['status'],'evidence_kind':args.evidence_label,'out':str(out),'failure':result.get('failure')}))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,RuntimeError,KeyError) as exc:
        print('S26 FAIL: '+str(exc),file=sys.stderr);raise SystemExit(1)

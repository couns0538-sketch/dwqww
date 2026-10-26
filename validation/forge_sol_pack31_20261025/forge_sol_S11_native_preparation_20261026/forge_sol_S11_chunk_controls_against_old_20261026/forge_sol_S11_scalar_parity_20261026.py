"""S11 source-only scalar/AVX2 proof and exact binary-stream transport helpers.

No compiler/engine is launched at import. Callers bind actual build/source/input
receipts and obtain the root's finite native grant before calling capture_arm.
"""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import os
import re
import selectors
import shutil
import struct
import subprocess
import time

ORACLE_SHA='7d3be5616fe9e52382b2deb5b36d76c507a07a66bda07a6311f2e6a5dd557bd1'
OWNED=Path('/workspace/forge-pack24-20261026/S08/forge_sol_S08_build_window_subreaper_20261026.py')
OWNED_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'
SCALAR_FLAGS=('-U__AVX2__','-U__SSE__','-fno-tree-vectorize','-fno-tree-slp-vectorize')
HEADER=struct.Struct('<IIIIQQI')
RECORD_BYTES=2068


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def verify_link_map(text,core_path,scalar_object=None):
    """GNU ld map proof: actual archive selection, not merely mentioned inputs."""
    core=str(Path(core_path))
    if not Path(core).is_absolute():raise ValueError('absolute frozen core archive path required')
    archive=re.compile(re.escape(core)+r'\(([^)]+)\)')
    members=sorted(set(archive.findall(text)))
    if not members:raise ValueError('map has no actual members selected from the pinned core')
    if any(Path(name).name=='search.cpp.o' for name in members):raise ValueError('archive search object pulled despite oracle including actual search.cpp')
    loads=re.findall(r'^\s*LOAD\s+(.+?)\s*$',text,re.M)
    if loads.count(core)!=1:raise ValueError('pinned core LOAD is missing or ambiguous')
    foreign=[path for path in loads if Path(path).name=='libforge_core.a' and path!=core]
    if foreign:raise ValueError('another Forge core archive is loaded')
    nnue=any(Path(name).name=='nnue.cpp.o' for name in members)
    if scalar_object is None:
        if not nnue:raise ValueError('ordinary oracle did not pull its actual archive NNUE object')
        mode='NORMAL_ARCHIVE_NNUE'
    else:
        scalar=str(Path(scalar_object))
        if not Path(scalar).is_absolute() or loads.count(scalar)!=1:raise ValueError('explicit scalar object LOAD missing or ambiguous')
        if nnue:raise ValueError('archive NNUE object pulled alongside explicit scalar object')
        mode='EXPLICIT_SCALAR_NNUE'
    return {'mode':mode,'archive':core,'selected_archive_members':members,'archive_search_pulled':False,'archive_nnue_pulled':nnue,'explicit_scalar_object':None if scalar_object is None else str(scalar_object)}


def verify_oracle_link_argv(argv,core,scalar=None):
    if type(argv) is not list or not all(type(x) is str for x in argv):raise ValueError('actual observed link argv required')
    if any('--whole-archive' in x or '--allow-multiple-definition' in x or 'muldefs' in x for x in argv):raise ValueError('duplicate/whole-archive link policy forbidden')
    if argv.count(str(core))!=1:raise ValueError('exactly one pinned core argument required')
    if any(x in SCALAR_FLAGS for x in argv):raise ValueError('driver must be normally compiled so FP header stays comparable')
    if scalar is not None and (argv.count(str(scalar))!=1 or argv.index(str(scalar))>argv.index(str(core))):raise ValueError('explicit scalar object must precede archive')


def scalar_compile_argv(normal_argv,output):
    argv=list(normal_argv)
    if '-o' not in argv or argv.count('-o')!=1 or '-c' not in argv:raise ValueError('normal one-object compiler argv required')
    if any(x in SCALAR_FLAGS for x in argv):raise ValueError('input compiler recipe already scalar-modified')
    argv[argv.index('-o')+1]=str(output);argv.extend(SCALAR_FLAGS);return argv


def macro_probe_argv(compile_argv):
    argv=list(compile_argv)
    if argv.count('-o')!=1 or argv.count('-c')!=1:raise ValueError('observed one-object compile command required')
    index=argv.index('-o');del argv[index:index+2];argv.remove('-c');argv+=['-dM','-E'];return argv


def verify_macros(text,mode):
    if mode not in {'scalar','avx2'}:raise ValueError('unknown required ISA mode')
    rows=re.findall(r'^#define\s+(\w+)\s*(.*?)\s*$',text,re.M);macros={}
    for name,value in rows:
        if name in macros:raise ValueError('duplicate preprocessor macro')
        macros[name]=value
    if '__FAST_MATH__' in macros or macros.get('FORGE_NNUE_HIDDEN')!='256' or macros.get('FORGE_HAS_NNUE')!='1':raise ValueError('macro proof is not strict H256 loaded NNUE translation unit')
    if mode=='scalar':
        if '__AVX2__' in macros or '__SSE__' in macros or macros.get('FORGE_NNUE_SSE')!='0':raise ValueError('scalar selector still enables AVX2 or SSE fallback')
    elif macros.get('__AVX2__')!='1' or macros.get('__SSE__')!='1':raise ValueError('ordinary NNUE is not AVX2')
    return {'mode':mode,'AVX2_macro':macros.get('__AVX2__'),'SSE_macro':macros.get('__SSE__'),'FORGE_NNUE_SSE':macros.get('FORGE_NNUE_SSE'),'hidden':256}


def verify_disassembly(text,mode):
    if mode not in {'scalar','avx2'}:raise ValueError('unknown required ISA mode')
    symbol=None;scoped=[];evaluate=[]
    for line in text.splitlines():
        match=re.match(r'^\s*[0-9a-fA-F]+\s+<(.+)>:\s*$',line)
        if match:symbol=match[1];continue
        match=re.match(r'^\s*[0-9a-fA-F]+:\s+([a-zA-Z][a-zA-Z0-9_.]*)\s*(.*?)\s*$',line)
        if match and symbol and symbol.startswith('forge::nnue::'):
            row=(symbol,match[1].lower(),match[2]);scoped.append(row)
            if symbol.startswith('forge::nnue::evaluate('):evaluate.append(row)
    if not scoped or not evaluate:raise ValueError('no actual demangled NNUE/evaluate disassembly')
    if any(re.fullmatch(r'vf(?:n)?m(?:add|sub)[a-z0-9]*',op) for _,op,_ in scoped):raise ValueError('NNUE contains FMA')
    if any(re.search(r'%?zmm\d+',args) for _,_,args in scoped):raise ValueError('unsupported AVX512 width')
    if mode=='scalar':
        if any(re.search(r'%?(?:ymm|zmm)\d+',args) for _,_,args in evaluate):raise ValueError('scalar inference uses unsupported packed width')
        for _,op,args in evaluate:
            if (re.fullmatch(r'v?(?:add|sub|mul|div|min|max|sqrt|rcp|rsqrt)(?:ps|pd|sd|ph)',op)
                or re.search(r'%st(?:\(|\b)',args) or re.match(r'f(?:ld|st|add|mul|sub|div|com|ucom|xch|sqrt)',op)):
                raise ValueError('scalar inference contains packed SSE fallback, non-float32 or x87 arithmetic')
        if not any(re.fullmatch(r'v?mulss',op) for _,op,_ in evaluate) or not any(re.fullmatch(r'v?addss',op) for _,op,_ in evaluate):raise ValueError('scalar float32 arithmetic not demonstrated')
    else:
        if not any(op in {'vmulps','vaddps'} and re.search(r'%?ymm\d+',args) for _,op,args in evaluate):raise ValueError('actual AVX2 packed inference not demonstrated')
    return {'mode':mode,'NNUE_instructions':len(scoped),'evaluate_instructions':len(evaluate),'FMA_count':0,'ISA_proven':True}


def parse_header(raw,positions,child_limit):
    if len(raw)!=HEADER.size:raise ValueError('truncated or excessive binary header')
    magic,version,hidden,width,count,children,mxcsr=HEADER.unpack(raw)
    if (magic,version,hidden,width,count,children)!=(0x4b313146,1,256,RECORD_BYTES,positions,child_limit):raise ValueError('binary source/count/format header differs')
    if mxcsr==0xffffffff or mxcsr&~0x0000ffc0:raise ValueError('normally compiled driver FP header missing/invalid')
    return {'magic':magic,'version':version,'hidden':hidden,'record_bytes':width,'positions':count,'child_limit':children,'MXCSR_masked':mxcsr}


def parse_summary(raw,positions,child_limit,table_checks):
    try:value=json.loads(raw.decode('ascii'))
    except Exception as e:raise ValueError('missing/malformed actual oracle summary') from e
    keys={'positions','record_bytes','header_bytes','actual_table_basis_checks','legal_children','nulls','captures','promotions','castles','en_passant','material_key_mismatches','state_mismatches'}
    if type(value) is not dict or set(value)!=keys or any(type(x) is not int or x<0 for x in value.values()):raise ValueError('oracle summary schema/counters invalid')
    for k,want in {'positions':positions,'record_bytes':RECORD_BYTES,'header_bytes':36,'actual_table_basis_checks':table_checks,'material_key_mismatches':0,'state_mismatches':0}.items():
        if value[k]!=want:raise ValueError('oracle actual '+k+' differs')
    if value['nulls']>child_limit or any(value[k]>value['legal_children'] for k in ('captures','promotions','castles','en_passant')):raise ValueError('oracle coverage count inconsistent')
    if child_limit and (value['legal_children']==0 or value['nulls']==0):raise ValueError('make/unmake or null restoration not exercised')
    return value


def compare_gzip(left,right,positions,child_limit):
    expected=36+positions*RECORD_BYTES;offset=0;header=None
    with gzip.open(left,'rb') as a,gzip.open(right,'rb') as b:
        while True:
            x,y=a.read(1048576),b.read(1048576)
            if x!=y:
                first=next((i for i,(u,v) in enumerate(zip(x,y)) if u!=v),min(len(x),len(y)))
                raise ValueError('exact binary stream mismatch at byte '+str(offset+first))
            if not x:break
            if header is None:header=parse_header(x[:36],positions,child_limit)
            offset+=len(x)
            if offset>expected:raise ValueError('excess snapshot bytes')
    if offset!=expected:raise ValueError('truncated or partial-record snapshot stream')
    return {'status':'PASS_EXACT_BYTES','positions':positions,'bytes_compared':offset,'header':header,'comparison':'every decompressed byte, not hash-only'}


def verify_sealed_input(fd,expected_size,expected_sha):
    import fcntl
    # Same Linux UAPI fallback as the preserved S09 sealer; Python may omit names.
    seals=fcntl.fcntl(fd,getattr(fcntl,'F_GET_SEALS',1034))
    required=0x000f  # F_SEAL_SEAL|SHRINK|GROW|WRITE, bits pinned by Linux UAPI.
    if seals&required!=required or os.fstat(fd).st_size!=expected_size:raise ValueError('immutable sealed corpus fd required')
    h=hashlib.sha256();offset=0
    while offset<expected_size:
        chunk=os.pread(fd,min(1048576,expected_size-offset),offset)
        if not chunk:raise ValueError('truncated sealed corpus')
        h.update(chunk);offset+=len(chunk)
    if h.hexdigest()!=expected_sha:raise ValueError('sealed corpus bytes differ from original manifest')
    return {'bytes':offset,'sha256':expected_sha,'seals':seals}


def capture_arm(executable,corpus_fd,*,input_bytes,input_sha256,positions,child_limit,table_checks,out,label,seconds,stop=None,minimum_free_bytes=64*1048576):
    """Run one already-qualified oracle, preserving bounded gzip and original stderr.

    The caller first verifies source/build/link/ISA receipts and has the finite
    native grant. No corpus is generated here. The same sealed fd is rewound for
    each sequential arm. This is correctness work, not a timed speed comparison.
    """
    if not 1<=positions<=1000000 or not 0<=child_limit<=positions or table_checks not in (0,650) or not 1<=seconds<=1800:raise ValueError('invalid finite native arm protocol')
    if not re.fullmatch('[a-zA-Z0-9_]+',label):raise ValueError('unsafe raw label')
    out=Path(out);exe=Path(executable)
    if not out.is_dir() or not exe.is_file():raise ValueError('existing output directory and executable required')
    paths={key:out/(label+suffix) for key,suffix in [('stdout','.stdout.gz'),('stderr','.stderr'),('receipt','.receipt.json')]}
    if any(path.exists() for path in paths.values()):raise FileExistsError('new raw capture paths required')
    if sha(OWNED)!=OWNED_SHA:raise ValueError('owned-process helper changed')
    spec=importlib.util.spec_from_file_location('s11_original_owned',OWNED);owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
    source=verify_sealed_input(corpus_fd,input_bytes,input_sha256);os.lseek(corpus_fd,0,os.SEEK_SET)
    argv=[str(exe),'--positions',str(positions),'--child-limit',str(child_limit)];start=time.monotonic();deadline=start+seconds
    result={'status':'FAIL_CAPTURE','argv':argv,'executable_sha256_before':sha(exe),'sealed_input':source,'positions':positions,'child_limit':child_limit,'expected_table_basis_checks':table_checks,'raw_stdout_bytes':0,'maximum_raw_stdout_bytes':36+positions*RECORD_BYTES,'source_oracle_sha256_required':ORACLE_SHA,'nps_used':False,'leader_reaped':False,'remaining_owned_group':[]}
    proc=None;sel=selectors.DefaultSelector();header=bytearray();digest=hashlib.sha256();stderr=bytearray();error=None
    try:
        with owned.SubreaperScope():
            try:
                with paths['stdout'].open('xb') as file,paths['stderr'].open('xb') as saved_err:
                    with gzip.GzipFile(filename='',mode='wb',fileobj=file,mtime=0,compresslevel=1) as saved:
                        reason=stop() if stop else None
                        if reason or shutil.disk_usage(out).free<minimum_free_bytes:raise RuntimeError('prelaunch root stop/free-disk floor')
                        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
                        proc=subprocess.Popen(argv,stdin=corpus_fd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env=env)
                        result.update(pid=proc.pid,process_group=proc.pid)
                        with (out/'events.jsonl').open('a') as events:events.write(json.dumps({'event':'child_start','label':label,'pid':proc.pid,'utc':owned.utc()})+'\n')
                        sel.register(proc.stdout,selectors.EVENT_READ,'stdout');sel.register(proc.stderr,selectors.EVENT_READ,'stderr')
                        while sel.get_map():
                            reason=stop() if stop else None
                            if reason:raise RuntimeError('root stop: '+str(reason))
                            if time.monotonic()>=deadline-1:raise TimeoutError('owned oracle deadline')
                            if shutil.disk_usage(out).free<minimum_free_bytes:raise RuntimeError('raw evidence free-disk floor')
                            for key,_ in sel.select(.05):
                                chunk=os.read(key.fd,131072)
                                if not chunk:sel.unregister(key.fileobj);continue
                                if key.data=='stderr':
                                    saved_err.write(chunk);stderr.extend(chunk)
                                    if len(stderr)>16384:raise ValueError('oracle stderr exceeded fixed summary bound')
                                else:
                                    saved.write(chunk);digest.update(chunk);result['raw_stdout_bytes']+=len(chunk)
                                    if result['raw_stdout_bytes']>result['maximum_raw_stdout_bytes']:raise ValueError('oracle emitted excess snapshot bytes')
                                    if len(header)<36:
                                        header.extend(chunk[:36-len(header)])
                                        if len(header)==36:result['header']=parse_header(header,positions,child_limit)
                        proc.wait(timeout=max(.01,deadline-time.monotonic()));result['returncode']=proc.returncode;result['leader_reaped']=True
                        if proc.returncode!=0:raise ValueError('oracle did not exit normally with rc0')
                        if result['raw_stdout_bytes']!=result['maximum_raw_stdout_bytes']:raise ValueError('truncated/partial-record oracle stream')
                        result['summary']=parse_summary(bytes(stderr),positions,child_limit,table_checks)
                reaped,remaining=owned._reap_group(proc.pid,timeout=.1);result['reaped_descendants']=reaped;result['remaining_owned_group']=remaining
                if remaining:raise ValueError('oracle owned group not empty after exit')
                result['status']='PASS_CAPTURE'
            finally:
                if proc is not None:
                    if proc.poll() is None or owned._all_members(proc.pid):
                        reaped,remaining=owned._close_group(proc);result['cleanup_reaped']=reaped;result['remaining_owned_group']=remaining
                    result['returncode']=proc.returncode;result['leader_reaped']=proc.poll() is not None
                    for stream in (proc.stdout,proc.stderr):
                        if stream:stream.close()
    except BaseException as exc:error=exc;result['error']=type(exc).__name__+': '+str(exc)
    finally:
        sel.close();result['raw_stdout_sha256']=digest.hexdigest();result['elapsed_seconds']=time.monotonic()-start
        result['executable_sha256_after']=sha(exe);result['executable_unchanged']=result['executable_sha256_before']==result['executable_sha256_after']
        if not result['executable_unchanged'] or result['remaining_owned_group']:result['status']='FAIL_CAPTURE'
        result['captures']={name:{'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)} for name,path in paths.items() if name!='receipt' and path.exists()}
        with paths['receipt'].open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    if result['status']!='PASS_CAPTURE':raise RuntimeError('native arm failed; original receipt '+str(paths['receipt'])) from error
    return result


def verify_oracle_compilation(receipt,role):
    if role not in {'baseline','candidate'} or receipt.get('sha256')!=ORACLE_SHA:raise ValueError('wrong actual oracle source/role')
    source=receipt.get('source');argv=receipt.get('argv')
    if not source or type(argv) is not list or argv.count(source)!=1:raise ValueError('actual oracle source missing from observed compiler argv')
    markers=[x for x in argv if x.startswith('-DS11_REQUIRE_TABLE')]
    if markers!=(['-DS11_REQUIRE_TABLE=1'] if role=='candidate' else []):raise ValueError('wrong candidate-only table oracle marker')
    if any(x in SCALAR_FLAGS for x in argv):raise ValueError('oracle driver must stay normally compiled')
    return {'source_sha256':ORACLE_SHA,'role':role,'expected_table_basis_checks':650 if role=='candidate' else 0,'driver_normally_compiled':True}

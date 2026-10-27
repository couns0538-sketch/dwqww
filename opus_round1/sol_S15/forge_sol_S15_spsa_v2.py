#!/usr/bin/env python3
"""Forge S15 SPSA harness, v2: deterministic SPSA over the tune:: parameters, with a PC driver.

v2 = Sol's prepared v1 (forge_sol_S15_spsa_20261027.py, sha256 5f1f5978...72f6, reviewed with no must-fix)
plus the parts his source-only preparation left out (Opus 5.5, 2026-10-27). v1 logic is kept line for line;
every changed v1 line carries a "v2:" comment. Modes:
  catalog  parse every tune:: parameter (name, default, minimum, maximum) from <source>/src/search.cpp
  demo     N-iteration SPSA on a synthetic objective (no engine; the convergence check)
  plan     one iteration's fastchess command from a captured UCI transcript (no process started)
  observe  read one finished paired PGN through the owned tools/match/pgn_stats.py and make one SPSA update
  run      v2 PC driver: capture the engine's own `uci` reply, prove that both probe settings are applied,
           then per iteration plan -> fastchess -> observe. Children run at Idle (default) or BelowNormal
           priority, one engine thread, concurrency 1, with per-iteration timeout, wall budget and RAM guard.
The tool writes only into a NEW output directory. It never edits engine source and never applies a tune: the
proposed values are reported only. Gains are math controls, not tuned chess values; no strength claim.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,math,random,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
DATE='20261027'
PGN_CHECKER_SHA='a5a6b46e1d5381fc063475fb90f012051653cefbca485c46a01179fafbeec2bf'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()

def encode(value):return (json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def save(out,name,value):
    if Path(name).name!=name:raise ValueError('Output must be a direct child of own output directory')
    with (out/name).open('xb') as stream:stream.write(encode(value))
def pin(path):
    p=Path(path).resolve(strict=True)
    if not p.is_file():raise ValueError('Input is not a regular file')
    return {'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size}
def check_pins(pins):
    for item in pins.values():
        if digest(item['path'])!=item['sha256']:raise ValueError('Pinned input changed: '+item['path'])

def parse_catalog(search,uci):
    if search.count('namespace tune {')!=1 or search.count('} // namespace tune')!=1:raise ValueError('Unsupported tune namespace structure')
    block=search.split('namespace tune {',1)[1].split('} // namespace tune',1)[0]
    block=re.sub(r'/\*.*?\*/|//[^\n]*','',block,flags=re.S)
    declarations={}
    for line in block.splitlines():
        line=line.strip()
        if line.startswith('int '):
            match=re.fullmatch(r'int\s+(\w+)\s*=\s*(-?\d+)\s*;',line)
            if not match:raise ValueError('Nonliteral/unsupported tunable declaration')
            name,value=match.groups()
            if name in declarations:raise ValueError('Duplicate tunable declaration')
            declarations[name]=int(value)
    table=re.search(r'static\s+const\s+std::vector<Parameter>\s+table\s*\{(.*?)\};',block,re.S)
    if not declarations or not table:raise ValueError('Missing explicit parameter declarations/table')
    expression=re.compile(r'\{\s*"(\w+)"\s*,\s*&(\w+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\}')
    rest=expression.sub('',table.group(1))
    if rest.strip(' \t\r\n,'):raise ValueError('Unsupported parameter table expression')
    parameters=[];seen=set()
    for match in expression.finditer(table.group(1)):
        name,pointer,low,high=match.groups();low=int(low);high=int(high)
        if name!=pointer or name in seen or name not in declarations:raise ValueError('Unmatched/duplicate parameter name or pointer')
        value=declarations[name]
        if not low<high or not low<=value<=high:raise ValueError('Invalid source parameter range/default')
        parameters.append({'name':name,'default':value,'minimum':low,'maximum':high});seen.add(name)
    if seen!=set(declarations):raise ValueError('Every tune integer must have exactly one range')
    # No alternate name or range is inferred from idea documents.
    net_present=bool(re.search(r'option name NetScale(?:Pct)? type spin',uci))
    return {'parameters':parameters,'unsupported_requested':[] if 'NetScale' in seen else ['NetScale'],'NetScale_status':'REQUIRES_EXPLICIT_CATALOG_EXTENSION' if net_present else 'ABSENT_ON_EXACT_SOURCE','hidden_tunables':'L accepts table names in setoption; advertisement requires FORGE_EXPOSE_TUNABLES'}

def select(catalog,names):
    available={p['name']:p for p in catalog['parameters']}
    if not names or len(set(names))!=len(names) or set(names)-available.keys():raise ValueError('Empty, duplicate or unsupported parameter selection')
    return {**catalog,'parameters':[available[name] for name in names]}

def initial(catalog):return [(p['default']-p['minimum'])/(p['maximum']-p['minimum']) for p in catalog['parameters']]
def values(catalog,theta):
    if len(theta)!=len(catalog['parameters']) or any(not math.isfinite(x) or not 0<=x<=1 for x in theta):raise ValueError('Invalid normalized state')
    return {p['name']:p['minimum']+int(math.floor(x*(p['maximum']-p['minimum'])+.5)) for p,x in zip(catalog['parameters'],theta)}
def probes(catalog,theta,seed,iteration,c):
    if seed<0 or iteration<0 or not math.isfinite(c) or c<=0:raise ValueError('Invalid seed/iteration/perturbation')
    values(catalog,theta);rng=random.Random(f'ForgeSolS15:{seed}:{iteration}');directions=[1 if rng.getrandbits(1) else -1 for _ in theta]
    delta=[max(c,1/(p['maximum']-p['minimum'])) for p in catalog['parameters']]
    plus=values(catalog,[min(1.,max(0.,x+d*s)) for x,d,s in zip(theta,delta,directions)])
    minus=values(catalog,[min(1.,max(0.,x-d*s)) for x,d,s in zip(theta,delta,directions)])
    effective=[(plus[p['name']]-minus[p['name']])/(p['maximum']-p['minimum']) for p in catalog['parameters']]
    if any(x==0 for x in effective):raise ValueError('Integer perturbation collapsed')
    return {'theta':list(theta),'plus':plus,'minus':minus,'effective':effective,'direction':directions,'iteration':iteration,'seed':seed}
def update(catalog,probe,plus_score,minus_score,gain):
    if any(not math.isfinite(x) for x in (plus_score,minus_score,gain)) or gain<=0:raise ValueError('Invalid objective or gain')
    if len(probe['effective'])!=len(probe['theta']) or any(not math.isfinite(x) or x==0 for x in probe['effective']):raise ValueError('Invalid probe difference')
    difference=plus_score-minus_score
    if not math.isfinite(difference):raise ValueError('Objective difference overflow')
    proposed=[x+gain*difference/step for x,step in zip(probe['theta'],probe['effective'])]
    if any(not math.isfinite(x) for x in proposed):raise ValueError('SPSA update overflow')
    theta=[min(1.,max(0.,x)) for x in proposed]
    return {'theta':theta,'values':values(catalog,theta),'gain':gain,'plus_score':plus_score,'minus_score':minus_score}
def fake_loss(catalog,config):
    return sum(((config[p['name']]-p['minimum'])/(p['maximum']-p['minimum'])-.5)**2 for p in catalog['parameters'])/len(catalog['parameters'])

def verify_profile(catalog,names,text):
    required=select(catalog,names);options={}
    if text.splitlines().count('uciok')!=1:raise ValueError('A completed captured UCI response is required')
    for line in text.splitlines():
        if not line.startswith('option name '):continue
        match=re.fullmatch(r'option name (.+?) type (\S+)(?: (.*))?',line)
        if not match:raise ValueError('Malformed UCI option')
        name,kind,tail=match.groups()
        if name in options:raise ValueError('Duplicate UCI option')
        option={'type':kind,'tail':tail or ''}
        if kind=='spin':
            bounds=re.fullmatch(r'default (-?\d+) min (-?\d+) max (-?\d+)',tail or '')
            if not bounds:raise ValueError('Malformed UCI spin range')
            option['values']=tuple(map(int,bounds.groups()))
        options[name]=option
    for p in required['parameters']:
        if options.get(p['name'],{}).get('values')!=(p['default'],p['minimum'],p['maximum']):raise ValueError('Unsupported, hidden or wrong-range UCI option: '+p['name'])
    return options

def load_pgn_checker(path):
    if digest(path)!=PGN_CHECKER_SHA:raise ValueError('Owned PGN checker differs from the reviewed L tool')
    spec=importlib.util.spec_from_file_location('forge_s15_owned_pgn_checker',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def source_catalog(source):
    source=Path(source).resolve(strict=True);pins={name:pin(source/name) for name in ('src/search.cpp','src/uci.cpp','tools/match/pgn_stats.py')}
    catalog=parse_catalog((source/'src/search.cpp').read_text(encoding='utf-8'),(source/'src/uci.cpp').read_text(encoding='utf-8'));catalog['source_inputs']=pins  # v2: explicit UTF-8 (Windows locale is cp1252)
    return catalog

def seal(out):
    rows=[]
    for p in sorted(out.iterdir()):
        if not p.is_file() or p.is_symlink():raise ValueError('Unexpected output object')
        rows.append(digest(p)+'  '+p.name+'\n')
    with (out/f'forge_sol_S15_SHA256SUMS_{DATE}.txt').open('xb') as stream:stream.write(''.join(rows).encode())  # v2: binary, LF on every OS

def demo(catalog,out,seed,iterations,gain,c):
    if not 1<=iterations<=100000:raise ValueError('Invalid iteration budget')
    theta=initial(catalog);first=fake_loss(catalog,values(catalog,theta));losses=[]
    for i in range(iterations):
        probe=probes(catalog,theta,seed,i,c/((i+1)**(1/6)))
        result=update(catalog,probe,-fake_loss(catalog,probe['plus']),-fake_loss(catalog,probe['minus']),gain/math.sqrt(i+1));theta=result['theta']
        loss=fake_loss(catalog,result['values']);losses.append(loss)
        save(out,f'forge_sol_S15_iteration_{i:06d}_{DATE}.json',{'probe':probe,'update':result,'synthetic_loss_after':loss})
    summary={'iterations':iterations,'seed':seed,'initial_loss':first,'final_loss':losses[-1],'losses':losses,'engine_runs':0,'objective':'SYNTHETIC normalized separable quadratic centered at0.5; maximize negative loss','gain_initial':gain,'perturbation_initial':c,'gain_schedule':'gain/sqrt(iteration+1)','perturbation_schedule':'c/(iteration+1)^(1/6), at least one integer per dimension','convergence':'LOSS_DECREASED' if losses[-1]<first else 'NOT_DEMONSTRATED','strength_claim':None,'scope':'Pure tool demonstration, not chess training/tuning evidence'}
    save(out,f'forge_sol_S15_demo_results_{DATE}.json',summary);return summary

def plan(catalog,args,out):
    names=[p['name'] for p in catalog['parameters']];profile=Path(args.uci_transcript).read_text(encoding='utf-8');options=verify_profile(catalog,names,profile)  # v2: explicit UTF-8
    for name,value in (('Hash',16),('Threads',1)):
        bounds=options.get(name,{}).get('values')
        if not bounds or not bounds[1]<=value<=bounds[2]:raise ValueError('Unsupported common match option: '+name)
    if options.get('OwnBook',{}).get('type')!='check':raise ValueError('OwnBook support is required')
    inputs={name:pin(getattr(args,name)) for name in ('engine','fastchess','openings','uci_transcript')};check_pins(inputs)
    theta=initial(catalog);iteration=0  # v2: state is read before the openings are chosen (their order depends on the iteration)
    if args.state:
        state=json.loads(Path(args.state).read_text(encoding='utf-8'))
        if state['catalog']!=catalog or state['seed']!=args.seed:raise ValueError('Previous state has another catalog/source/seed')
        theta=state['update']['theta'];iteration=state['iteration']+1;inputs['previous_state']=pin(args.state)
    positions=[' '.join(line.split()[:4]) for line in Path(args.openings).read_text(encoding='utf-8').splitlines() if line.strip()]
    if any(len(fen.split())!=4 for fen in positions) or len(set(positions))!=len(positions) or len(positions)<args.pairs:raise ValueError('Need sufficient unique opening records')
    ordered=sorted(positions,key=lambda fen:hashlib.sha256(f'{args.seed}:{iteration}\n{fen}'.encode()).digest())[:args.pairs]  # v2: openings rotate per iteration (v1 replayed the same pairs every iteration)
    selected=out/f'forge_sol_S15_selected_openings_{DATE}.epd'
    with selected.open('xb') as stream:stream.write(('\n'.join(ordered)+'\n').encode())  # v2: binary, LF on every OS
    probe=probes(catalog,theta,args.seed,iteration,args.perturbation/((iteration+1)**(1/6)))
    command=[inputs['fastchess']['path'],'-config','outname=forge_sol_S15_fastchess_state_'+DATE+'.json']
    for label,config in (('Candidate',probe['plus']),('Baseline',probe['minus'])):
        command+=['-engine','cmd='+inputs['engine']['path'],'name='+label]+['option.'+name+'='+str(value) for name,value in config.items()]
    # v2: no '-maxmoves 200'. Fastchess tags a max-moves draw [Termination "adjudication"], which the owned checker
    # rejects, so any game reaching the cap voided the whole iteration (a 252-ply game was seen in the PC probe).
    # Games now end by the rules (mate, stalemate, repetition, fifty moves, material); the runner's timeout bounds them.
    command+=['-each','proto=uci','tc='+args.tc,'option.Threads=1','option.Hash=16','option.OwnBook=false','restart=on','-openings','file='+selected.name,'format=epd','order=sequential','-srand',str(args.seed),'-rounds',str(args.pairs),'-games','2','-concurrency','1','-report','penta=true','-pgnout','file=forge_sol_S15_original_games_'+DATE+'.pgn','append=false','notation=uci','nodes=true','timeleft=true','-log','file=forge_sol_S15_fastchess_'+DATE+'.log','level=warn','append=false','-strict']  # v2: '-report penta=true' for the runner's cross-check
    result={'catalog':catalog,'probe':probe,'iteration':iteration,'gain':args.gain/math.sqrt(iteration+1),'inputs':inputs,'selected_openings_sha256':digest(selected),'command':command,'command_cwd':str(out),'pairs':args.pairs,'seed':args.seed,'engine_runs':0,'support':'Captured exposed UCI ranges match; binding transcript to actual engine execution remains UNVERIFIED','status':'PLAN_ONLY_NO_PROCESS_STARTED','strength_claim':None,'smoke':'Equal-time paired plus-vs-minus bookkeeping, not strength acceptance'}
    save(out,f'forge_sol_S15_match_plan_{DATE}.json',result);return result

def matched_openings(played,planned):
    """v2: fastchess writes an en-passant square that no pawn can capture as '-' (PC probe: EPD 'h6' -> PGN '-'), so a
    played FEN matches a planned EPD when placement, side and castling are equal and the e.p. field is equal or '-'.
    Every played FEN must match exactly one planned opening (otherwise fail closed); returns the matched set."""
    matched=set()
    for fen in played:
        a=fen.split();hits=[e for e in planned if e.split()[:3]==a[:3] and (e.split()[3]==a[3] or a[3]=='-')]
        if len(hits)!=1 or len(a)!=4:raise ValueError('PGN openings differ from plan')
        matched.add(hits[0])
    if len(matched)!=len(played):raise ValueError('PGN openings differ from plan')
    return matched

def observe(args,out):
    pp=Path(args.plan).resolve(strict=True);p=json.loads(pp.read_text(encoding='utf-8'));check_pins(p['inputs']);catalog=p['catalog'];check_pins(catalog['source_inputs'])
    selected=pp.parent/f'forge_sol_S15_selected_openings_{DATE}.epd'
    if digest(selected)!=p['selected_openings_sha256']:raise ValueError('Selected opening file changed')
    raw=Path(args.pgn).read_bytes();text=raw.decode('utf-8').replace('\r\n','\n')  # v2: CRLF-tolerant parse (the checker's tag regex needs LF); original bytes are still copied unchanged
    checker=load_pgn_checker(catalog['source_inputs']['tools/match/pgn_stats.py']['path']);stats=checker.summarize(text)
    if stats['pairs']!=p['pairs']:raise ValueError('Incomplete planned match')
    expected=set(selected.read_text(encoding='utf-8').splitlines());actual={' '.join(tags['FEN'].split()[:4]) for tags,moves in checker.games(text)}
    if matched_openings(actual,expected)!=expected:raise ValueError('PGN openings differ from plan')  # v2: e.p. normalization (see matched_openings)
    score=stats['score_fraction'];result={'catalog':catalog,'iteration':p['iteration'],'seed':p['seed'],'update':update(catalog,p['probe'],score,1-score,p['gain']),'statistics':stats,'plan':pin(pp),'original_pgn':pin(args.pgn),'execution_binding':'UNVERIFIED: PGN provenance/options/binary/legality require separately bound real execution receipt','strength_claim':None,'engine_runs':0}
    with (out/f'forge_sol_S15_original_games_{DATE}.pgn').open('xb') as stream:stream.write(raw)
    save(out,f'forge_sol_S15_observed_state_{DATE}.json',result);return result


# ------------------------------------------------------------------------------------------------------------
# v2 additions: the PC driver. Processes are started only here and only in `run` mode: the engine (to capture
# its own `uci` reply and to prove that a setting is applied) and the planned fastchess command.
# ------------------------------------------------------------------------------------------------------------
import datetime,os,platform,subprocess,time
PRIORITIES=('idle','belownormal')

def engine_argv(engine):
    """The argv that starts the engine for UCI capture (the tests replace it with a Python fake)."""
    return [str(engine)]

def priority_kwargs(priority):
    """Popen keywords that start a child at Idle or BelowNormal priority; never above the caller's own level."""
    if priority not in PRIORITIES:raise ValueError('Unsupported priority: '+str(priority))
    if os.name=='nt':return {'creationflags':subprocess.IDLE_PRIORITY_CLASS if priority=='idle' else subprocess.BELOW_NORMAL_PRIORITY_CLASS}
    level=19 if priority=='idle' else 10
    return {'preexec_fn':lambda:os.setpriority(os.PRIO_PROCESS,0,max(level,os.getpriority(os.PRIO_PROCESS,0)))}

def free_ram_bytes():
    """Available physical memory in bytes, or None where it cannot be read."""
    if os.name=='nt':
        import ctypes
        class Status(ctypes.Structure):
            _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
        status=Status();status.dwLength=ctypes.sizeof(Status)
        return int(status.ullAvailPhys) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)) else None
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
    except OSError:return None
    return None

def run_process(argv,cwd,stdin_bytes,output_path,timeout,priority):
    """Start one owned child, send stdin_bytes, write stdout+stderr to a NEW file, wait at most `timeout` s.
    On timeout only this child is killed (engines started by a killed fastchess see EOF on stdin and exit)."""
    with Path(output_path).open('xb') as sink:
        child=subprocess.Popen([str(a) for a in argv],cwd=cwd,stdin=subprocess.PIPE if stdin_bytes is not None else subprocess.DEVNULL,stdout=sink,stderr=subprocess.STDOUT,env={**os.environ,'NO_COLOR':'1'},**priority_kwargs(priority))
        try:child.communicate(stdin_bytes,timeout=timeout)
        except subprocess.TimeoutExpired:
            child.kill();child.communicate()
            raise ValueError(f'Timeout after {timeout} s: {Path(str(argv[0])).name} (child killed)')
    return child.returncode

def uci_blocks(text):
    """Completed `uci` replies in a transcript, each ending at its uciok line."""
    blocks=[];current=[]
    for line in text.splitlines():
        current.append(line)
        if line=='uciok':blocks.append('\n'.join(current)+'\n');current=[]
    return blocks

def capture_uci(engine,commands,path,timeout,priority,cwd):
    """Run the engine with fixed UCI commands; keep its raw reply in `path` and return it as text."""
    code=run_process(engine_argv(engine),cwd,('\n'.join(commands)+'\n').encode(),path,timeout,priority)
    if code!=0:raise ValueError(f'Engine exited with code {code} during UCI capture')
    return Path(path).read_bytes().decode('utf-8')

def prove_applied(catalog,engine,config,path,timeout,priority,cwd):
    """The exposed build re-advertises each tunable with its current value: `uci`, setoption..., `uci` must show
    the source defaults first and exactly the requested values afterwards (this binary, these settings)."""
    commands=['uci']+[f'setoption name {name} value {value}' for name,value in config.items()]+['uci','quit']
    blocks=uci_blocks(capture_uci(engine,commands,path,timeout,priority,cwd))
    if len(blocks)!=2:raise ValueError('Application proof needs exactly two completed uci replies')
    verify_profile(catalog,list(config),blocks[0])
    applied={**catalog,'parameters':[{**p,'default':config[p['name']]} for p in catalog['parameters'] if p['name'] in config]}
    try:verify_profile(applied,list(config),blocks[1])
    except ValueError as exc:raise ValueError('Engine did not apply the requested setting: '+str(exc)) from None
    return {'transcript':pin(path),'requested':config,'result':'APPLIED'}

def fastchess_pentanomial(console_text):
    """The last Ptnml(0-2) list fastchess printed, or None."""
    found=re.findall(r'Ptnml\(0-2\):\s*\[([^\]]+)\]',re.sub(r'\x1b\[[0-9;]*m','',console_text))
    return [int(n.strip()) for n in found[-1].split(',')] if found else None

def seal_tree(out):
    """SHA256 of every file below `out` (relative POSIX paths, sorted), written to a NEW top-level file."""
    rows=[]
    for p in sorted(out.rglob('*'),key=lambda q:q.relative_to(out).as_posix()):
        if p.is_symlink():raise ValueError('Unexpected symlink in output tree')
        if p.is_file():rows.append(digest(p)+'  '+p.relative_to(out).as_posix()+'\n')
    with (out/f'forge_sol_S15_run_SHA256SUMS_{DATE}.txt').open('xb') as stream:stream.write(''.join(rows).encode())

def run(catalog,args,out):
    """plan -> application proof -> fastchess -> cross-check -> observe, for args.iterations iterations.
    Stops (fail closed) at the first error; finished iterations stay valid. The tune is never applied."""
    started=time.monotonic();engine=Path(args.engine).resolve(strict=True);fastchess=Path(args.fastchess).resolve(strict=True)
    names=[p['name'] for p in catalog['parameters']];run_pins={'engine':pin(engine),'fastchess':pin(fastchess)}
    if args.iterations<1 or args.iteration_timeout<=0 or args.max_wall_seconds<=0 or args.min_free_ram_gib<0:raise ValueError('Invalid run budget')
    summary={'status':'RUNNING','mode':'run','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected':names,'seed':args.seed,'tc':args.tc,'pairs_per_iteration':args.pairs,'iterations_requested':args.iterations,'gain_initial':args.gain,'perturbation_initial':args.perturbation,'priority':args.priority,'engine_threads':1,'concurrency':1,'hash_mb':16,'iteration_timeout_s':args.iteration_timeout,'max_wall_seconds':args.max_wall_seconds,'min_free_ram_gib':args.min_free_ram_gib,'platform':platform.platform(),'python':platform.python_version(),'tool_sha256':digest(__file__),'initial_values':values(catalog,initial(catalog)),'iterations':[],'tune_applied':False,'engine_source_modified':False,'strength_claim':None,'note':'Proposed values are SPSA bookkeeping from a few short games; they are noise, not a tune, and are never applied.'}
    def finish(status,reason=None):
        summary['status']=status;summary['stop_reason']=reason;summary['elapsed_seconds']=round(time.monotonic()-started,3)
        done=summary['iterations'];summary['iterations_completed']=len(done)
        summary['final_values']=done[-1]['values_after'] if done else summary['initial_values']
        save(out,f'forge_sol_S15_run_summary_{DATE}.json',summary);seal_tree(out);return summary
    try:
        uci_path=out/f'forge_sol_S15_initial_uci_{DATE}.txt'
        verify_profile(catalog,names,capture_uci(engine,['uci','quit'],uci_path,60,args.priority,out))
        summary['initial_uci']=pin(uci_path);state=None
        for i in range(args.iterations):
            elapsed=time.monotonic()-started
            if elapsed+args.iteration_timeout>args.max_wall_seconds:return finish('STOPPED_WALL_BUDGET',f'{elapsed:.1f} s used; iteration {i} could need {args.iteration_timeout:g} s more than the {args.max_wall_seconds:g} s budget allows')
            free=free_ram_bytes()
            if free is not None and free<args.min_free_ram_gib*2**30:return finish('STOPPED_LOW_RAM',f'{free/2**30:.2f} GiB free before iteration {i}')
            idir=out/f'iteration_{i:03d}';idir.mkdir();plan_dir=idir/'plan';observed_dir=idir/'observed';t0=time.monotonic()
            argv=['plan','--source',str(args.source),'--out',str(plan_dir),'--select',','.join(names),'--engine',str(engine),'--fastchess',str(fastchess),'--openings',str(args.openings),'--uci-transcript',str(uci_path),'--seed',str(args.seed),'--pairs',str(args.pairs),'--tc',args.tc,'--gain',repr(args.gain),'--perturbation',repr(args.perturbation)]
            if state:argv+=['--state',str(state)]
            execute(argv)
            planned=json.loads((plan_dir/f'forge_sol_S15_match_plan_{DATE}.json').read_text(encoding='utf-8'))
            proofs={label:prove_applied(catalog,engine,planned['probe'][label],idir/f'forge_sol_S15_uci_proof_{label}_{DATE}.txt',60,args.priority,idir) for label in ('plus','minus')}
            console=idir/f'forge_sol_S15_fastchess_console_{DATE}.txt'
            code=run_process(planned['command'],planned['command_cwd'],None,console,args.iteration_timeout,args.priority)
            if code!=0:raise ValueError(f'fastchess exited with code {code} in iteration {i}')
            pgn=plan_dir/f'forge_sol_S15_original_games_{DATE}.pgn'
            execute(['observe','--plan',str(plan_dir/f'forge_sol_S15_match_plan_{DATE}.json'),'--pgn',str(pgn),'--out',str(observed_dir)])
            state=observed_dir/f'forge_sol_S15_observed_state_{DATE}.json';observed=json.loads(state.read_text(encoding='utf-8'))
            reported=fastchess_pentanomial(console.read_bytes().decode('utf-8','replace'))
            if reported!=observed['statistics']['pentanomial_0_half_1_1half_2']:raise ValueError(f'Pentanomial cross-check failed in iteration {i}: fastchess {reported} vs checker {observed["statistics"]["pentanomial_0_half_1_1half_2"]}')
            summary['iterations'].append({'iteration':i,'theta_before':planned['probe']['theta'],'direction':planned['probe']['direction'],'plus':planned['probe']['plus'],'minus':planned['probe']['minus'],'gain':planned['gain'],'selected_openings_sha256':planned['selected_openings_sha256'],'application_proof':proofs,'fastchess_exit_code':code,'statistics':observed['statistics'],'fastchess_pentanomial':reported,'score_plus':observed['update']['plus_score'],'theta_after':observed['update']['theta'],'values_after':observed['update']['values'],'elapsed_seconds':round(time.monotonic()-t0,3),'free_ram_gib_before':None if free is None else round(free/2**30,2)})
        check_pins(run_pins);summary['inputs']=run_pins
        return finish('COMPLETED')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        finish('FAILED',type(exc).__name__+': '+str(exc));raise

def execute(argv):
    """One mode, exceptions propagate (used by main and by `run` for its plan/observe steps)."""
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('catalog','demo','plan','observe','run'));parser.add_argument('--source',type=Path);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--select');parser.add_argument('--seed',type=int,default=20261027);parser.add_argument('--iterations',type=int,default=20);parser.add_argument('--gain',type=float,default=.4);parser.add_argument('--perturbation',type=float,default=.15)
    for name in ('engine','fastchess','openings','uci-transcript','state','plan','pgn'):parser.add_argument('--'+name,type=Path)
    parser.add_argument('--pairs',type=int,default=2);parser.add_argument('--tc',default='0.25+0.01')
    parser.add_argument('--priority',choices=PRIORITIES,default='idle');parser.add_argument('--iteration-timeout',type=float,default=300.);parser.add_argument('--max-wall-seconds',type=float,default=540.);parser.add_argument('--min-free-ram-gib',type=float,default=6.)  # v2: run budgets
    args=parser.parse_args(argv)
    if args.seed<0 or not math.isfinite(args.gain) or args.gain<=0 or not math.isfinite(args.perturbation) or args.perturbation<=0:raise ValueError('Invalid numerical controls')
    if args.mode!='observe' and not args.source:raise ValueError('--source required')
    catalog=source_catalog(args.source) if args.mode!='observe' else None
    if args.select:catalog=select(catalog,args.select.split(','))
    if args.mode=='plan' and (not all(getattr(args,k) for k in ('engine','fastchess','openings','uci_transcript')) or args.pairs<1):raise ValueError('Plan needs engine, fastchess, openings, captured UCI and positive pairs')
    if args.mode=='run' and (not all(getattr(args,k) for k in ('engine','fastchess','openings')) or not args.select or args.pairs<1):raise ValueError('Run needs engine, fastchess, openings, an explicit --select and positive pairs')  # v2
    if args.mode=='observe' and (not args.plan or not args.pgn):raise ValueError('Observe needs plan and original PGN')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    save(out,f'forge_sol_S15_tool_provenance_{DATE}.json',{'tool_name':Path(__file__).name,'tool_sha256':digest(__file__),'Python':sys.version,'engine_runs':0})
    if catalog:save(out,f'forge_sol_S15_parameter_catalog_{DATE}.json',catalog)
    if args.mode=='catalog':result={'parameters':len(catalog['parameters']),'unsupported_requested':catalog['unsupported_requested'],'engine_runs':0}
    elif args.mode=='demo':result=demo(catalog,out,args.seed,args.iterations,args.gain,args.perturbation)
    elif args.mode=='plan':result=plan(catalog,args,out)
    elif args.mode=='observe':result=observe(args,out)
    else:result=run(catalog,args,out)  # v2: run seals its own tree (it has subdirectories)
    if catalog:check_pins(catalog['source_inputs'])
    if args.mode!='run':seal(out)
    if args.mode=='run':return {'mode':'run','status':result['status'],'out':str(out),'iterations_completed':result['iterations_completed'],'final_values':result['final_values'],'tune_applied':False}
    return {'mode':args.mode,'status':'COMPLETED_TOOL_ONLY','out':str(out),'engine_runs':0,'convergence':result.get('convergence')}

def main(argv=None):
    try:
        print(json.dumps(execute(argv),sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())

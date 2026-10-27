#!/usr/bin/env python3
"""Tool-only, deterministic SPSA ask/observe preparation for Forge S15.

No compiler, engine, Fastchess or other subprocess is launched by this tool.
Math-demo gains are not chess constants; no speed/strength acceptance is implied.
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
    catalog=parse_catalog((source/'src/search.cpp').read_text(),(source/'src/uci.cpp').read_text());catalog['source_inputs']=pins
    return catalog

def seal(out):
    rows=[]
    for p in sorted(out.iterdir()):
        if not p.is_file() or p.is_symlink():raise ValueError('Unexpected output object')
        rows.append(digest(p)+'  '+p.name+'\n')
    with (out/f'forge_sol_S15_SHA256SUMS_{DATE}.txt').open('x') as stream:stream.writelines(rows)

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
    names=[p['name'] for p in catalog['parameters']];profile=Path(args.uci_transcript).read_text();options=verify_profile(catalog,names,profile)
    for name,value in (('Hash',16),('Threads',1)):
        bounds=options.get(name,{}).get('values')
        if not bounds or not bounds[1]<=value<=bounds[2]:raise ValueError('Unsupported common match option: '+name)
    if options.get('OwnBook',{}).get('type')!='check':raise ValueError('OwnBook support is required')
    inputs={name:pin(getattr(args,name)) for name in ('engine','fastchess','openings','uci_transcript')};check_pins(inputs)
    positions=[' '.join(line.split()[:4]) for line in Path(args.openings).read_text().splitlines() if line.strip()]
    if any(len(fen.split())!=4 for fen in positions) or len(set(positions))!=len(positions) or len(positions)<args.pairs:raise ValueError('Need sufficient unique opening records')
    ordered=sorted(positions,key=lambda fen:hashlib.sha256(f'{args.seed}\n{fen}'.encode()).digest())[:args.pairs]
    selected=out/f'forge_sol_S15_selected_openings_{DATE}.epd'
    with selected.open('x') as stream:stream.write('\n'.join(ordered)+'\n')
    theta=initial(catalog);iteration=0
    if args.state:
        state=json.loads(Path(args.state).read_text())
        if state['catalog']!=catalog or state['seed']!=args.seed:raise ValueError('Previous state has another catalog/source/seed')
        theta=state['update']['theta'];iteration=state['iteration']+1;inputs['previous_state']=pin(args.state)
    probe=probes(catalog,theta,args.seed,iteration,args.perturbation/((iteration+1)**(1/6)))
    command=[inputs['fastchess']['path'],'-config','outname=forge_sol_S15_fastchess_state_'+DATE+'.json']
    for label,config in (('Candidate',probe['plus']),('Baseline',probe['minus'])):
        command+=['-engine','cmd='+inputs['engine']['path'],'name='+label]+['option.'+name+'='+str(value) for name,value in config.items()]
    command+=['-each','proto=uci','tc='+args.tc,'option.Threads=1','option.Hash=16','option.OwnBook=false','restart=on','-openings','file='+selected.name,'format=epd','order=sequential','-srand',str(args.seed),'-rounds',str(args.pairs),'-games','2','-concurrency','1','-pgnout','file=forge_sol_S15_original_games_'+DATE+'.pgn','append=false','notation=uci','nodes=true','timeleft=true','-log','file=forge_sol_S15_fastchess_'+DATE+'.log','level=warn','append=false','-strict','-maxmoves','200']
    result={'catalog':catalog,'probe':probe,'iteration':iteration,'gain':args.gain/math.sqrt(iteration+1),'inputs':inputs,'selected_openings_sha256':digest(selected),'command':command,'command_cwd':str(out),'pairs':args.pairs,'seed':args.seed,'engine_runs':0,'support':'Captured exposed UCI ranges match; binding transcript to actual engine execution remains UNVERIFIED','status':'PLAN_ONLY_NO_PROCESS_STARTED','strength_claim':None,'smoke':'Equal-time paired plus-vs-minus bookkeeping, not strength acceptance'}
    save(out,f'forge_sol_S15_match_plan_{DATE}.json',result);return result

def observe(args,out):
    pp=Path(args.plan).resolve(strict=True);p=json.loads(pp.read_text());check_pins(p['inputs']);catalog=p['catalog'];check_pins(catalog['source_inputs'])
    selected=pp.parent/f'forge_sol_S15_selected_openings_{DATE}.epd'
    if digest(selected)!=p['selected_openings_sha256']:raise ValueError('Selected opening file changed')
    raw=Path(args.pgn).read_bytes();checker=load_pgn_checker(catalog['source_inputs']['tools/match/pgn_stats.py']['path']);stats=checker.summarize(raw.decode())
    if stats['pairs']!=p['pairs']:raise ValueError('Incomplete planned match')
    expected=set(selected.read_text().splitlines());actual={' '.join(tags['FEN'].split()[:4]) for tags,moves in checker.games(raw.decode())}
    if actual!=expected:raise ValueError('PGN openings differ from plan')
    score=stats['score_fraction'];result={'catalog':catalog,'iteration':p['iteration'],'seed':p['seed'],'update':update(catalog,p['probe'],score,1-score,p['gain']),'statistics':stats,'plan':pin(pp),'original_pgn':pin(args.pgn),'execution_binding':'UNVERIFIED: PGN provenance/options/binary/legality require separately bound real execution receipt','strength_claim':None,'engine_runs':0}
    with (out/f'forge_sol_S15_original_games_{DATE}.pgn').open('xb') as stream:stream.write(raw)
    save(out,f'forge_sol_S15_observed_state_{DATE}.json',result);return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('catalog','demo','plan','observe'));parser.add_argument('--source',type=Path);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--select');parser.add_argument('--seed',type=int,default=20261027);parser.add_argument('--iterations',type=int,default=20);parser.add_argument('--gain',type=float,default=.4);parser.add_argument('--perturbation',type=float,default=.15)
    for name in ('engine','fastchess','openings','uci-transcript','state','plan','pgn'):parser.add_argument('--'+name,type=Path)
    parser.add_argument('--pairs',type=int,default=2);parser.add_argument('--tc',default='0.25+0.01');args=parser.parse_args(argv)
    try:
        if args.seed<0 or not math.isfinite(args.gain) or args.gain<=0 or not math.isfinite(args.perturbation) or args.perturbation<=0:raise ValueError('Invalid numerical controls')
        if args.mode!='observe' and not args.source:raise ValueError('--source required')
        catalog=source_catalog(args.source) if args.mode!='observe' else None
        if args.select:catalog=select(catalog,args.select.split(','))
        if args.mode=='plan' and (not all(getattr(args,k) for k in ('engine','fastchess','openings','uci_transcript')) or args.pairs<1):raise ValueError('Plan needs engine, fastchess, openings, captured UCI and positive pairs')
        if args.mode=='observe' and (not args.plan or not args.pgn):raise ValueError('Observe needs plan and original PGN')
        out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
        save(out,f'forge_sol_S15_tool_provenance_{DATE}.json',{'tool_name':Path(__file__).name,'tool_sha256':digest(__file__),'Python':sys.version,'engine_runs':0})
        if catalog:save(out,f'forge_sol_S15_parameter_catalog_{DATE}.json',catalog)
        if args.mode=='catalog':result={'parameters':len(catalog['parameters']),'unsupported_requested':catalog['unsupported_requested'],'engine_runs':0}
        elif args.mode=='demo':result=demo(catalog,out,args.seed,args.iterations,args.gain,args.perturbation)
        elif args.mode=='plan':result=plan(catalog,args,out)
        else:result=observe(args,out)
        if catalog:check_pins(catalog['source_inputs'])
        seal(out);print(json.dumps({'mode':args.mode,'status':'COMPLETED_TOOL_ONLY','out':str(out),'engine_runs':0,'convergence':result.get('convergence')},sort_keys=True));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())

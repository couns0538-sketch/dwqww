"""Read-only cross-check of c1 correctness evidence; writes one new audit JSON."""
import hashlib,json,pathlib,re,subprocess,sys
sys.path.insert(0,'D:/a9/pydeps')
import psutil,chess
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS);psutil.Process().cpu_affinity([3])
root=pathlib.Path(__file__).parents[1]; work=root.parent; evidence=root/'evidence'
checks={}; hashes={}; selfplay_plies={}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(pathlib.Path(p).read_text())
def require(name,condition):
    checks[name]=bool(condition)
    if not condition:raise RuntimeError(name)
out=pathlib.Path(sys.argv[1]); assert not out.exists()
try:
    expected='775edea1d476a3a18c64af63f53c55d6e29a4571556aad2666e87f18a6ef4284'
    for tag in ['b1','b2']:
        hashes[tag]=sha(f'D:/a9/w/{tag}/src_copy/forge_ltopgo_{tag}.exe')
        require(tag+' executable',hashes[tag]==expected)
    require('build pair record',load(evidence/'build-pair.json')==hashes)
    manifest=load(evidence/'c1-source.json')
    require('worktree source immutable',all(sha(work/name)==h for name,h in manifest.items()))
    require('snapshot source immutable',all(sha(pathlib.Path('D:/a9/c1')/name)==h for name,h in manifest.items()))
    commit=subprocess.check_output(['git','rev-parse','fb58080'],cwd=work,text=True).strip()
    tree=subprocess.check_output(['git','ls-tree','-rz',commit,'--','include','src'],cwd=work)
    for record in tree.split(b'\0'):
        if not record:continue
        meta,name=record.split(b'\t',1); blob=meta.split()[2].decode(); data=(work/name.decode()).read_bytes()
        require('source commit blob '+name.decode(),hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob)
    lock=pathlib.Path('C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean')
    require('embedded network unchanged',sha(lock/'src/nnue_weights.inc')==sha(work/'src/nnue_weights.inc'))
    changed={name.replace('\\','/') for name,h in manifest.items() if sha(lock/name)!=h}
    require('engine change scope',changed=={'include/forge/nnue.hpp','src/nnue.cpp','src/uci.cpp'})
    pins={'d11':312866,'d13':862329,'d16':3024920,'d20':12389307,'d22':34048354}
    perft={'startpos':4865609,'kiwipete':193690690}
    for tag in ['b1','b2']:
        for mode in ['off','opt1']:
            for kind in ['plain','ltopgo']:
                doc=load(evidence/f'kit-{tag}/ident/{mode}.{kind}.json')
                require(f'{tag} {mode} {kind} options',doc['opts']==([] if mode=='off' else ['NNUEWideOutput=true']))
                require(f'{tag} {mode} {kind} exe path',pathlib.Path(doc['exe']).resolve()==pathlib.Path(f'D:/a9/w/{tag}/src_copy/forge_{kind}_{tag}.exe').resolve())
                require(f'{tag} {mode} {kind} pins',doc['bench']==pins and doc['perft']==perft)
        require(tag+' kit PASS',f'RESULT PASS {tag}' in (evidence/f'kit-{tag}/SUMMARY.txt').read_text())
    p=load(evidence/'production-parity-c1/result.json')
    require('parity names order',[r['name'] for r in p['runs']]==['lock','off','on'])
    require('parity binary hashes',[r['sha256'] for r in p['runs']]==['fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072',expected,expected])
    for name in ['lock','off','on']:
        transcript=(evidence/f'production-parity-c1/{name}.uci.log').read_text()
        require('parity '+name+' option activation',('> setoption name NNUEWideOutput value true\n' in transcript)==(name=='on'))
    require('production 12k parity',p['status']=='PASS' and len(p['runs'])==3 and
            all(r['positions']==12000 for r in p['runs']) and len({r['digest'] for r in p['runs']})==1)
    require('corpus identity',p['corpus_sha256']==sha(evidence/'fens_12k.txt'))
    for name in ['eval-lock02.log','eval-wide02.log']:
        text=(evidence/name).read_text()
        require(name,'PASS fens=12000 positions=684200 moves=324100 nulls=12000 digest=3bd3b27ac5a60483' in text)
    require('ON diagnostic execution','wide_output_calls=684200' in (evidence/'eval-wide02.log').read_text())
    san_hash='a56762278935af93344680ba147a9076f63b52504e2495a686d7fe5f28a4a2aa'
    require('sanitizer binary identity',sha('D:/a9/checks/forge_san_c1.exe')==san_hash)
    for mode in ['off','on']:
        d=load(evidence/f'san-c1-{mode}/result.json')
        require(mode+' sanitizer status',d['status']=='PASS' and d['sha256']==san_hash and len(d['checks'])==8)
        require(mode+' sanitizer option',d['on']==(mode=='on'))
        plies=0
        for game in d['checks']:
            b=chess.Board(game['start'])
            for uci in game['moves']:
                m=chess.Move.from_uci(uci);require(f'{mode} game{game["game"]} ply{len(b.move_stack)} legal',m in b.legal_moves)
                b.push(m);plies+=1
        selfplay_plies[mode]=plies
        transcript=(evidence/f'san-c1-{mode}/selfplay.log').read_text()
        require(mode+' sanitizer transcript move count',len(re.findall(r'^bestmove ',transcript,re.MULTILINE))==plies)
        require(mode+' sanitizer zero reports',not re.search(r'ERROR: AddressSanitizer|runtime error:|SUMMARY: (?:AddressSanitizer|UndefinedBehaviorSanitizer)',transcript))
        d=load(evidence/f'smoke-c1-{mode}/result.json')
        require(mode+' smoke identity',d['status']=='PASS' and d['sha256']==expected and len(d['checks'])==24)
        require(mode+' smoke option',d['on']==(mode=='on'))
        require(mode+' T1/T4 smoke',{r['threads'] for r in d['checks']}=={1,4})
        require(mode+' smoke legal',all(chess.Move.from_uci(r['bestmove']) in chess.Board(r['fen']).legal_moves for r in d['checks']))
    require('UBSan positive control','UndefinedBehaviorSanitizer' in (evidence/'ubsan-control.log').read_text())
    require('ASan positive control','ERROR: AddressSanitizer: heap-buffer-overflow' in (evidence/'asan-control.log').read_text())
    result={'correctness_packet':'PASS','checks_passed':len(checks),'candidate_sha256':expected,
            'selfplay_plies':selfplay_plies,'production_source_commit':commit,'speed_acceptance':'NOT ASSESSED BY THIS TOOL'}
except BaseException as exc:
    result={'correctness_packet':'FAIL','error':repr(exc),'checks':checks};raise
finally:
    with out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))

#!/usr/bin/env python3
"""Light source/fixture preparation only. Never compiles, runs engines, or archives."""
from pathlib import Path
import csv, difflib, hashlib, json, shutil

ROOT=Path(__file__).resolve().parent
RESEARCH=ROOT.parent
REPO=ROOT.parents[2]
WORK=Path('/workspace/see-recapture-promotion-prototype-20261020')
SOURCE16=Path('/workspace/.cloud-setup/forge-pin-mask-source')
PRIOR=REPO/'validation/pin-see-filter-cost-20261020'
THRESHOLDS=[-2000,-1000,-900,-800,-600,-500,-300,-1,0,1,99,100,101,299,300,500,899,900,901,1700]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
old_manifest=json.loads((RESEARCH/'archive-manifest.json').read_text())['files']
assert all(sha(RESEARCH/n)==h for n,h in old_manifest.items())
assert sha(RESEARCH/'complete-evidence.zip')=='9f2b0d81d053c433bd3640ad5f6cefb8cbd04e1f3bdf7f02ead244525e7963f3'
WORK.mkdir(exist_ok=False)
reference=WORK/'source-reference'; (reference/'src').mkdir(parents=True)
shutil.copytree(SOURCE16/'include',reference/'include')
shutil.copy2(RESEARCH/'source16-board.cpp',reference/'src/board.cpp')
assert sha(reference/'src/board.cpp')=='239f1475fd48e9dba3babefe2399b22de5962f42e7a90a775271dbe49f6f6f31'
candidate=WORK/'source-candidate';shutil.copytree(reference,candidate)
before=(reference/'src/board.cpp').read_text()
helper=(ROOT/'promotion-helper.inc').read_text()
dispatch=(ROOT/'dispatch.inc').read_text()
anchor='constexpr std::array<int, 7> SeeValue{0, 100, 300, 300, 500, 900, 0};\n'
callsite='    const int captured_square = (move.flags & EnPassant) != 0U ? to - pawn_push_delta(us) : to;\n'
assert before.count(anchor)==before.count(callsite)==1
after=before.replace(anchor,anchor+'\n'+helper,1).replace(callsite,callsite+dispatch,1)
assert after.replace('\n'+helper,'',1).replace(dispatch,'',1)==before
(candidate/'src/board.cpp').write_text(after)
shutil.copy2(reference/'src/board.cpp',ROOT/'source16-board.cpp')
shutil.copy2(candidate/'src/board.cpp',ROOT/'candidate-board.cpp')
(ROOT/'promotion-recapture.patch').write_text(''.join(difflib.unified_diff(
    before.splitlines(True),after.splitlines(True),fromfile='a/src/board.cpp',tofile='b/src/board.cpp')))
reference_headers={str(p.relative_to(reference)):sha(p) for p in sorted((reference/'include').rglob('*')) if p.is_file()}
assert all(sha(candidate/n)==h for n,h in reference_headers.items())

inputs=ROOT/'inputs';inputs.mkdir()
baseline_tsv=(PRIOR/'inputs/all316.tsv').read_text()
new_tsv=(RESEARCH/'cases.tsv').read_text()
(inputs/'baseline316.tsv').write_text(baseline_tsv)
(inputs/'new10.tsv').write_text(new_tsv)
(inputs/'all326.tsv').write_text(baseline_tsv+new_tsv)
oracle_paths=[
    REPO/'validation/pinned-see-prototype-20261020/oracle-corpus.json',
    REPO/'validation/pinned-see-prototype-20261020/supplement-oracle.json',
    REPO/'validation/pin-see-coverage-20261020/oracle-corpus.json',
    RESEARCH/'oracle-corpus.json']
oracles=[]
for i,p in enumerate(oracle_paths):
    shutil.copy2(p,inputs/('original-oracle-'+str(i)+'.json'))
    oracles.extend(json.loads(p.read_text()))
assert len(oracles)==326
ids={c['id'] for c in oracles};assert len(ids)==326
lines=(inputs/'all326.tsv').read_text().splitlines()
assert len(lines)==326
by_id={c['id']:c for c in oracles}
for line in lines:
    name,fen,move=line.split('\t');c=by_id[name]
    assert c['fen']==fen and c['move']==move

def guard(fen,uci):
    placement,turn,_,ep,*_=fen.split()
    squares={}
    for row,rank in enumerate(placement.split('/')):
        file=0
        for token in rank:
            if token.isdigit():file+=int(token)
            else:squares[(7-row)*8+file]=token;file+=1
    origin=(ord(uci[0])-97)+(int(uci[1])-1)*8
    target=(ord(uci[2])-97)+(int(uci[3])-1)*8
    moving=squares[origin]
    if moving.lower()=='k' or target//8 not in [0,7]:return False
    captured=target
    if moving.lower()=='p' and origin%8!=target%8 and target not in squares and ep==uci[2:4]:
        captured=target-(8 if turn=='w' else -8)
    pawn='P' if target//8==7 else 'p'
    rank=6 if pawn=='P' else 1
    return any(squares.get(rank*8+file)==pawn and rank*8+file not in [origin,captured]
               for file in [target%8-1,target%8+1] if 0<=file<8)

expected=[]
new_ids={c['id'] for c in json.loads((RESEARCH/'oracle-corpus.json').read_text())}
for line in lines:
    name,fen,move=line.split('\t');c=by_id[name]
    legal=c.get('initial_legal',True)
    expected.append({'id':name,'fen':fen,'move':move,'initial_legal':legal,
                     'oracle_exchange':c.get('oracle_exchange') if legal else None,
                     'legal_recaptures':sorted(c.get('legal_recaptures',[])),
                     'promotion_guard':guard(fen,move),'new_research_case':name in new_ids})
write(inputs/'expected326.json',expected)
write(inputs/'fixed-thresholds.json',THRESHOLDS)
(inputs/'adjacent-brackets.tsv').write_text(''.join(c['id']+'\t'+
    '\t'.join(str(c['oracle_exchange']+delta) for delta in [-1,0,1])+'\n'
    for c in expected if c['new_research_case']))
golden_old=(PRIOR/'api-mask.stdout').read_text()
golden_new=(RESEARCH/'source16-api.stdout').read_text()
assert golden_old.splitlines()[0]==golden_new.splitlines()[0]
(inputs/'source16-golden326.stdout').write_text(golden_old+'\n'.join(golden_new.splitlines()[1:])+'\n')
golden=list(csv.DictReader((inputs/'source16-golden326.stdout').read_text().splitlines(),delimiter='\t'))
assert len(golden)==326 and {r['id'] for r in golden}==ids
assert all(c['id']==r['id'] for c,r in zip(expected,golden))
assert sum(not c['initial_legal'] for c in expected)==2
source16_wrong=[c['id'] for c,r in zip(expected,golden)
                if c['initial_legal'] and int(r['static_exchange'])!=c['oracle_exchange']]
assert len(source16_wrong)==8
freeze={'status':'FROZEN_SOURCE_AND_ORACLES_NO_RUNTIME',
        'source16_commit':'553caef144ae2e1b696ba35d7a0eb1a50a03fde9',
        'source16_board_sha256':sha(ROOT/'source16-board.cpp'),
        'candidate_board_sha256':sha(ROOT/'candidate-board.cpp'),
        'patch_sha256':sha(ROOT/'promotion-recapture.patch'),
        'header_sha256':reference_headers,'headers_changed':False,
        'ordinary_source16_body_restores_byte_exactly_after_removing_dispatch':True,
        'cases':326,'baseline_cases':316,'new_research_cases':10,'legal_cases':324,
        'initial_illegal_cases':2,'guard_true_cases':[c['id'] for c in expected if c['promotion_guard']],
        'source16_red_exchange_rows':source16_wrong,
        'preexisting_research_manifest_sha256':sha(RESEARCH/'archive-manifest.json'),
        'input_sha256':{str(p.relative_to(inputs)):sha(p) for p in sorted(inputs.iterdir()) if p.is_file()},
        'source_only_file_sha256':{n:sha(ROOT/n) for n in [
            'promotion-helper.inc','dispatch.inc','candidate-board.cpp','source16-board.cpp',
            'api_driver.cpp','compare_results.py','build_and_run.py','prepare_source.py','promotion-recapture.patch']}}
write(ROOT/'SOURCE-FREEZE.json',freeze)
assert all(sha(RESEARCH/n)==h for n,h in old_manifest.items())
print(json.dumps({'status':freeze['status'],'cases':326,'guard_cases':len(freeze['guard_true_cases']),
                  'candidate_board_sha256':freeze['candidate_board_sha256'],'headers_changed':False}))

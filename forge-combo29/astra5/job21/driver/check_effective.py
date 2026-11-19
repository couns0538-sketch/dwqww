"""Check each final fastchess configuration and actual role acknowledgements."""
import json
import sys
from pathlib import Path
from run_match import ROOT,BOOKS,NET,STAGES,EXPECTED_EXE,hash_file

def verify(stage):
    games,seed,ga,gb,na,nb=STAGES[stage]
    result=ROOT/'results'
    cfg=json.loads((result/f'{stage}-config.json').read_text())
    live=(result/f'{stage}-live-options.txt').read_text()
    cutoff=(result/f'{stage}-cutoff.txt').read_text().splitlines()
    if not cutoff[0].startswith(stage+' status '): raise ValueError('missing playing status')
    assert cfg['games']==2 and cfg['rounds']==games//2 and cfg['concurrency']==4 and cfg['seed']==seed
    assert cfg['maxmoves']=={'enabled':True,'move_count':300}
    assert not any(cfg[x]['enabled'] for x in ('draw','resign','tb_adjudication'))
    assert cfg['opening']['file']==str(BOOKS/f'{stage}.epd') and len(cfg['engines'])==2
    assert live.endswith('match_refusal false\n')
    base=dict(s.removeprefix('setoption name ').rsplit(' value ',1) for s in Path('/workspace/work/j7base/pc20.txt').read_text().splitlines())
    text=[cutoff[0]]
    for role,e,guard,nodes in zip(('A','B'),cfg['engines'],(ga,gb),(na,nb)):
        verify_flag='true' if guard==2 else 'false'
        options=dict(base,**{'NullMateGuard':str(guard),'NullThreatVerify':verify_flag,'NNUEArchFile':str(NET),'NNUEArch':'true'})
        assert e['name']==f'{stage}-{role}' and hash_file(Path(e['cmd']))==EXPECTED_EXE
        assert len(e['options'])==len(options) and dict(e['options'])==options
        assert e['limit']['nodes']==nodes and not e['limit']['plies'] and not any(e['limit']['tc'].values())
        for key,val in [('NullMateGuard',guard),('NullThreatVerify',verify_flag)]:
            assert f'{stage}-{role} <--- setoption name {key} value {val}' in live
        for marker in ('loaded','active'):
            assert any(f'{stage}-{role} ---> info string NNUE v3 {marker}:' in l and 'checksum 30ab43b4ba5db5f3' in l for l in live.splitlines())
        text.append(f'{stage}-{role} {nodes} nodes, {len(options)} UCI options correct, NullMateGuard {guard}, NullThreatVerify {verify_flag}, net checksum 30ab43b4ba5db5f3 loaded and active')
    text+=['4 concurrent games; 2 swapped games per opening; no draw or resign adjudication; maxmoves 300','fastchess_config_and_live_exchanges PASS']
    print('\n'.join(text))

if __name__=='__main__': verify(sys.argv[1])

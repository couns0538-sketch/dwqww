"""Check original kit outputs directly, without fabricating generic -Werror witnesses."""
import argparse, hashlib, json, pathlib, shutil
ROOT=pathlib.Path('D:/a10')
PINS=dict(zip(['d11','d13','d16','d20','d22'],[312866,862329,3024920,12389307,34048354]))
PERFT={'startpos':4865609,'kiwipete':193690690}
EXPECTED='775edea1d476a3a18c64af63f53c55d6e29a4571556aad2666e87f18a6ef4284'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--threads',type=int,choices=[1],required=True)
    ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    report={'status':'RUNNING','evidence_scope':'native','Elo':'UNPROVEN','checks':[],
        'source_commit':'f43a26aeed2448379fc2916b25f31ead8707b0ec',
        'recipe':'kit v2.3, original md5 729fe7275c3c01d22c751cb751d5c9d2; only scheduling changed to Idle',
        'limitation':'Generic proof runner requires Werror flags absent from exact kit. This checker validates actual kit fatal profile scan, never invents compiler flags. Overall qualification awaits parity, smoke and sanitizers.'}
    try:
        hashes=[];sources=[]
        for tag in ['pc1-a','pc2-a']:
            b=ROOT/'b'/tag;receipt=ROOT/f'wt/astra_r10/job1/build-{tag}/result.json'
            r=load(receipt);assert r['status']=='PASS' and r['exit_code']==0
            assert not (b/'FAILED').exists()
            assert f'RESULT PASS {tag}' in (b/'SUMMARY.txt').read_text()
            exe=b/f'src_copy/forge_ltopgo_{tag}.exe'
            assert sha(exe)==r['exe_sha256']==EXPECTED
            hashes.append(sha(exe));sources.append(load(receipt.parent/'source.json'))
            assert sources[-1]==load(ROOT/'wt/astra_r9/evidence/c1-source.json')
            for mode in ['off','opt1']:
                for kind in ['plain','ltopgo']:
                    path=b/f'ident/{mode}.{kind}.json';data=load(path)
                    assert data['bench']==PINS,(tag,mode,kind,'pins',data['bench'])
                    assert data['perft']==PERFT,(tag,mode,kind,'perft')
                    assert data['opts']==([] if mode=='off' else ['NNUEWideOutput=true'])
                    log=(b/f'ident/{mode}.{kind}.json.uci.log').read_text()
                    assert 'option name Threads type spin default 1 ' in log
                    # UCI Hash defaults to32, but bench creates its own isolated
                    # Searcher(16), verified in pinned uci.cpp; don't misreport defaults.
                    assert 'forge::Searcher bench_searcher(16);' in (ROOT/'c1/src/uci.cpp').read_text()
                    report['checks'].append({'name':f'{tag}/{mode}/{kind}/pins-perft','status':'PASS','original':str(path),'sha256':sha(path)})
            shutil.copytree(b,a.out/tag)
            shutil.copytree(receipt.parent,a.out/(tag+'-runner'))
        assert hashes[0]==hashes[1] and sources[0]==sources[1]
        report['checks'].append({'name':'reproducible_builds','status':'PASS','sha256':hashes[0]})
        report['bench_contract']='Pinned uci.cpp bench uses isolated Searcher(16), default T1. UCI default Hash32 is unrelated to bench. Explicit T1/Hash16 set for smoke/sanitizer/timing.'
        report['status']='PASS'
    except BaseException as error:
        report['status']='FAIL';report['error']=repr(error);raise
    finally:(a.out/'REPORT.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()

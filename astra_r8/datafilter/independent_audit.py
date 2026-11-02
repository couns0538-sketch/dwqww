"""Independent streaming rule/sign/complete-holdout audit. Does not call filter predicates."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time
import chess
from filter_positions import low_priority, sha256, storage_guard
from records import selfplay_record, dumps

def position_key(fen):
    # Conservative leakage identity: board + turn only, also catches clock/rights variants.
    return ' '.join(fen.split()[:2])

def run(root):
    output = root/'independent_audit'
    storage_guard(output, allowance=200*10**6)
    output.mkdir()
    start = time.perf_counter()
    counts = Counter(); keys = set(); n=sx=sy=sxx=syy=sxy=0
    source_results = Counter()
    sample = open(output/'sample.jsonl','x',encoding='utf-8',newline='\n')
    with open(root/'cohort/million.jsonl', encoding='utf-8') as fh:
        for line in fh:
            r = json.loads(line); b = chess.Board(r['fen']); counts['total'] += 1
            counts['check'] += b.is_check()
            counts['mate'] += r['score_type']=='mate' or abs(r['score_stm'])>=31872
            ply = (int(r['fen'].split()[5])-1)*2 + int(r['fen'].split()[1]=='b')
            assert ply == r['ply']
            counts['ply_gt160'] += ply > 160
            if not b.is_check() and r['score_type']!='mate' and abs(r['score_stm'])<31872:
                counts['default_keep'] += 1
                keys.add(position_key(r['fen']))
                if counts['default_keep'] <= 10000:
                    sample.write(line)
            if r['has_result']:
                y = r['result_white'] if b.turn else -r['result_white']
                assert y == r['result_stm']
                source_results[f"{r['fen'].split()[1]}:{r['result_white']}"] += 1
                x = r['score_stm']; n+=1; sx+=x; sy+=y; sxx+=x*x; syy+=y*y; sxy+=x*y
            else:
                assert r['result_stm'] is None
    sample.close()
    corr = (n*sxy-sx*sy)/math.sqrt((n*sxx-sx*sx)*(n*syy-sy*sy))
    default_report = json.loads((root/'filtered_default/report.json').read_text())
    a = json.loads((root/'filtered_a/report.json').read_text())
    b = json.loads((root/'filtered_b/report.json').read_text())
    assert counts['total'] == default_report['input'] == 1000000
    assert counts['default_keep'] == default_report['kept']
    assert counts['check'] == a['independent']['check'] and counts['mate'] == a['independent']['mate']
    assert counts['ply_gt160'] == a['independent']['ply']
    for name in ('records.jsonl','metadata.jsonl'):
        assert sha256(root/'filtered_a'/name) == sha256(root/'filtered_b'/name) == a['hashes'][name] == b['hashes'][name]
    report = dict(counts=dict(counts), known_result_count=n, result_distribution=dict(source_results),
                  pearson_stm_score_result=corr, sign_status='PASS' if corr>0.1 else 'FAIL',
                  deterministic='PASS', independent_rules='PASS', holdouts=[],
                  key_policy='conservative board+STM; ignores clocks, castling and EP',
                  sample_sha256=sha256(output/'sample.jsonl'), sample_bytes=(output/'sample.jsonl').stat().st_size)
    with open(output/'cohort_audit.json','x') as fh:
        json.dump(report,fh,indent=2)
    # Complete files, not prefixes. Trusted producer MD5 sidecars are pinned below.
    trusted = {'013':'f0739b12b4b32c41094aabf7cac26686', '014':'2900e7985e2cd588dfc02fac26c08ced'}
    with open(output/'validation013.jsonl','x',encoding='utf-8',newline='\n') as validation:
        for shard in ('013','014'):
            storage_guard(allowance=100*10**6)
            path = Path(f'D:/grok-pc-data/selfplay_out/forge_selfplay_{shard}.txt')
            before=path.stat(); md5=hashlib.md5(); digest=hashlib.sha256()
            count=overlap_rows=0; overlapping=set(); val_count=0
            with open(path,'rb') as fh:
                for source_row, raw in enumerate(fh,1):
                    md5.update(raw); digest.update(raw)
                    line=raw.decode('utf-8-sig')
                    if not line.strip() or line.lstrip().startswith('#'): continue
                    r=selfplay_record(line,str(path),source_row)
                    count+=1; key=position_key(r['fen'])
                    if key in keys: overlap_rows+=1; overlapping.add(key)
                    if shard=='013' and val_count<16384:
                        board=chess.Board(r['fen'])
                        if not board.is_check() and abs(r['score_stm'])<31872:
                            validation.write(dumps(r)+'\n'); val_count+=1
            after=path.stat()
            assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
            assert md5.hexdigest()==trusted[shard], 'holdout differs from pinned producer digest'
            receipt=dict(shard=shard,path=str(path),rows=count,bytes=before.st_size,sha256=digest.hexdigest(),
                         trusted_md5=trusted[shard],overlap_rows=overlap_rows,overlap_unique_keys=len(overlapping),
                         validation_rows=val_count,complete_scan=True)
            report['holdouts'].append(receipt)
            with open(output/f'holdout{shard}.json','x') as fh: json.dump(receipt,fh,indent=2)
            print(json.dumps(receipt),flush=True)
    report['elapsed_seconds']=time.perf_counter()-start
    report['holdout_clearance']='PASS' if all(h['overlap_rows']==0 for h in report['holdouts']) else 'FAIL'
    report['training_ready']=report['holdout_clearance']=='PASS' and corr>0.1
    with open(output/'audit.json','x') as fh: json.dump(report,fh,indent=2)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('root',type=Path); a=p.parse_args()
    low_priority(); print(json.dumps(run(a.root),indent=2))

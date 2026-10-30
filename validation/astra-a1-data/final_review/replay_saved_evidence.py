"""Read-only independent record/IPC replay; no native searches or training."""
from pathlib import Path
from collections import Counter
import datetime,gzip,hashlib,json,statistics,subprocess,sys,time
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'tools/data'))
from forge_pos import PosReader
from check_data_bundle import check_bundle
out=Path(__file__).resolve().parent
start=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.monotonic()
results=[];answers={};fens_by_budget={};source_path=Path('/tmp/astra-a1-data-input/extracted/forge_selfplay_003.pos')
with PosReader(source_path) as original:
    for nodes in (1024,4096,16384,65536):
        folder=root/f'validation/astra-a1-data/sealed_bundle_copies/relabel_256_{nodes}'
        verification=check_bundle(folder,full_records=True)
        summary=json.loads((folder/'summary.json').read_text())
        labels=[json.loads(line) for line in (folder/'labels.jsonl').read_text().splitlines()]
        fens=(folder/'relabeled.fen').read_text().splitlines()
        with gzip.open(folder/'probe_logs/worker-0/requests.tsv.gz','rt') as handle:
            requests=[line.rstrip('\n').split('\t') for line in handle]
        with gzip.open(folder/'probe_logs/worker-0/responses.jsonl.gz','rt') as handle:
            responses=[json.loads(line) for line in handle]
        assert len(labels)==len(fens)==len(requests)==len(responses)==256
        with PosReader(folder/'relabeled.pos',folder/'relabeled.hce') as paired:
            for index,(label,fen,request,response) in enumerate(zip(labels,fens,requests,responses)):
                source_index=index*39062
                assert label['output_index']==index and label['input_index']==source_index
                assert request==[str(source_index),'analyze',fen]
                assert response['id']==str(source_index) and response['operation']=='analyze' and response['fen']==fen
                assert response['ok'] is True and response['analyzed'] is True and response['terminal'] is False
                assert response['nodes_limit']==nodes and response['threads']==1 and response['hash_mb']==1
                assert 0<response['nodes']<=nodes and response['depth']>=1
                row=paired.row(index);source=original.row(source_index)
                assert (row.board,row.meta)==(source.board,source.meta)
                assert (row.score,row.hce)==(response['score'],response['hce'])
                assert label['old_score_stm']==source.score
                assert label['nodes_requested']==nodes
                for label_key,response_key in [('score_stm','score'),('hce_stm','hce'),('bestmove','bestmove'),('depth','depth'),('nodes','nodes')]:
                    assert label[label_key]==response[response_key]
        assert sum(r['nodes'] for r in responses)==summary['search_nodes']
        assert sum(r['cpu_ns'] for r in responses)==summary['query_cpu_ns']
        assert dict(Counter(str(r['depth']) for r in responses))==summary['depth_histogram']
        answers[nodes]=responses;fens_by_budget[nodes]=fens
        results.append({'nodes':nodes,'rows':256,'bundle_status':verification['status'],'manifest_sha256':verification['manifest_sha256'],'median_completed_depth':statistics.median(r['depth'] for r in responses),'pipeline_cpu_seconds':summary['pipeline_cpu_seconds'],'positions_per_core_hour_recomputed':256*3600/summary['pipeline_cpu_seconds']})
assert all(fens==fens_by_budget[1024] for fens in fens_by_budget.values())
for result in results:
    current=answers[result['nodes']];reference=answers[65536]
    result['capture_changes_vs_65536']=sum(a['capture']!=b['capture'] for a,b in zip(current,reference))
    result['median_absolute_score_delta_vs_65536']=statistics.median(abs(a['score']-b['score']) for a,b in zip(current,reference))
book=root/'validation/astra-a1-data/openings-unbalanced-25/standard-one/openings.moves'
metadata=[json.loads(line) for line in book.with_name('metadata.jsonl').read_text().splitlines()]
book_lines=book.read_text().splitlines()
assert len(book_lines)==len(metadata)==64
assert len({' '.join(row['fen'].split()[:2]) for row in metadata})==64
for line,row in zip(book_lines,metadata):
    assert line==' '.join(row['moves']) and len(row['moves'])==row['plies']
    assert 25<=abs(row['score_stm_cp'])<=150
    assert all(abs(check['score_stm_cp'])<=150 for check in row['checks'])
    assert len(row['checks'])==row['plies']+1
bench=root/'validation/astra-a1-data/fresh_engine_checks'
for depth,nodes in [(11,312866),(13,862329),(16,3024920),(20,12389307),(22,34048354)]:
    stdout=(bench/f'bench_d{depth}.stdout').read_text()
    assert str(nodes) in stdout and (bench/f'bench_d{depth}.exit').read_text().strip()=='0'
changed=subprocess.check_output(['git','diff','--name-only','e0d76ce8a6450573b503852aeca12b929bf4a17a','--','src','include','CMakeLists.txt','tools/nnue'],cwd=root,text=True)
assert not changed
report={'status':'PASS_READ_ONLY_SAVED_EVIDENCE_REPLAY','started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.monotonic()-clock,'relabel_budgets':results,'native_responses_replayed':1024,'output_rows_replayed':1024,'engine_trainer_diff_from_base':changed,'standard_min25_book':{'rows':64,'sha256':hashlib.sha256(book.read_bytes()).hexdigest(),'mean_abs_cp':statistics.mean(abs(row['score_stm_cp']) for row in metadata),'white_advantage':sum(row['score_white_cp']>0 for row in metadata),'black_advantage':sum(row['score_white_cp']<0 for row in metadata)},'limitations':['Original source hash identity recovered from original receipts; no repeated 10M rehash in this review','No new native search, trainer execution, full10M verification, Windows execution or Elo measurement']}
(out/'saved_evidence_replay.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

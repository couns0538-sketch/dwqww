#!/usr/bin/env python3
"""Read-only replay of the completed S08 profile-ON sanitizer supplement."""
import hashlib, importlib.util, json, pathlib, re
import chess

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/'forge_sol_S08_ASAN_PROFILE_EXTRA_NATIVE_20261026'
API=HERE/'forge_sol_S08_collect_profiles_20261026.py'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert sha(API)=='bf5d18d25bc1fb342c06092a36bfbac2b4717dc8a3f3c8f5cac34add3c3b1143'
    spec=importlib.util.spec_from_file_location('raw_profile_parser',API)
    api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    result_path=OUT/'forge_sol_S08_ASAN_profile_extra_result_20261026.json'
    result=json.loads(result_path.read_text());receipt=json.loads((OUT/'profile_on.receipt.json').read_text())
    assert result['status']=='PASS' and receipt['returncode']==0 and receipt['close_protocol_valid'] is True
    assert receipt['stdout_complete'] and receipt['stderr_complete'] and receipt['reader_queues_cleared']
    for kind,row in receipt['captures'].items():
        p=OUT/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    assert (OUT/'profile_on.stderr').read_bytes()==b''
    packets=[];current=None
    for line in (OUT/'profile_on.stdout').read_text().splitlines():
        if line.startswith('info string prof schema '):
            assert current is None;current=[]
        if current is not None:
            current.append(line)
            if api.BENCH.fullmatch(line) or line.startswith('bestmove '):
                mode='bench' if api.BENCH.fullmatch(line) else 'bestmove'
                packet=api.parse_packet(current,terminal=mode)
                assert not packet['overflow'] and len(packet['counters'])==55
                packets.append((mode,packet,line));current=None
    assert current is None and len(packets)==29
    assert packets[0][0]=='bench' and packets[0][1]==result['bench_prof11']['packet']
    assert packets[0][1]['counters']['nodes']['count']==308972
    stdin=(OUT/'profile_on.stdin').read_text().splitlines();thread=1;fen=None;requests=[];perfts=[]
    for line in stdin:
        if line.startswith('setoption name Threads value '):thread=int(line.rsplit(' ',1)[1])
        elif line.startswith('position fen '):fen=line[len('position fen '):]
        elif line=='go nodes 20000':requests.append((thread,fen))
        elif line=='go perft 4':perfts.append(fen)
    assert len(requests)==28 and len(perfts)==2 and stdin.count('bench_prof 11')==1 and stdin[-1]=='quit'
    for request,row,observed in zip(requests,result['searches'],packets[1:]):
        assert request==(row['threads'],row['fen'])
        assert observed[0]=='bestmove' and observed[1]==row['packet']
        token=observed[2].split()[1];board=chess.Board(row['fen'])
        assert token==row['bestmove'] and token!='0000' and chess.Move.from_uci(token) in board.legal_moves
        if row['threads']==1:assert row['packet']['counters']['nodes']['count']<=20000
    assert sum(t==1 for t,_ in requests)==25 and sum(t==2 for t,_ in requests)==3
    totals=[int(line.split()[1]) for line in (OUT/'profile_on.stdout').read_text().splitlines() if re.fullmatch(r'nodes \d+',line)]
    assert totals==[197281,4085603]
    expected=[(197281,197281),(4085603,4085603)]
    assert [(row['nodes'],row['divide_sum']) for row in result['perfts']]==expected
    before=result['binary_sha256_before'];assert before==result['binary_sha256_after']
    assert sha(HERE/'forge_sol_S08_ASAN_v2_window1_20261026/build/forge')==before
    audit={'status':'PASS_RAW_REPLAY_NO_ENGINE','result_sha256':sha(result_path),'raw_receipt_sha256':sha(OUT/'profile_on.receipt.json'),'profile_packets':29,'counters_per_packet':55,'bench11_nodes':308972,'T1_searches':25,'T2_searches':3,'legal_bestmoves':28,'perft4':totals,'actual_T2_node_counts':[row['packet']['counters']['nodes']['count'] for row in result['searches'] if row['threads']==2],'source_unchanged_recorded':result['source_unchanged'],'sanitizer_stderr_bytes':0,'raw_captures_rehashed':True,'no_speed_or_strength_claim':True}
    print(json.dumps(audit,indent=2,sort_keys=True))

if __name__=='__main__':main()

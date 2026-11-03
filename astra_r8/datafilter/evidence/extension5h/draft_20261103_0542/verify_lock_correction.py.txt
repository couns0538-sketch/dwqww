"""Bounded read-only verification of Couns's corrected lock/data contract."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE))
from filter_positions import low_priority, sha256
from profile_corpus import stat_key
from resource_policy import storage_guard

ENGINE = Path('C:/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe')
LOCK = 'fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072'
PINS = [(11,312866),(13,862329),(16,3024920),(20,12389307),(22,34048354)]
PERFT = [4865609,193690690]
KIWIPETE = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
V7 = Path('C:/astra8_data/extension3h_20261103/handoff_v7')
V7_SHA = '52f39e0ceeb6fc6c63422514296b928b308ede862754e8d69addde1aa44fc720'
CLEARED = Path('D:/grok-pc-data/dwqww/astra8_data/holdout_cleared')
CLEARED_SHA = '0e73a87c2e1af035aed34f51fdd74daefc05833ce133f254845f09f23aeb5dce'


def fingerprint_tree(root):
    return {path.relative_to(root).as_posix():sha256(path)
            for path in sorted(root.rglob('*')) if path.is_file()}


def compare_streams(first, second):
    before = [stat_key(first), stat_key(second)]
    hashes = [(hashlib.sha256(),hashlib.md5()) for _ in range(2)]
    sizes, rows = [0,0], [0,0]
    with first.open('rb') as left, second.open('rb') as right:
        while True:
            blocks = [left.read(1024*1024),right.read(1024*1024)]
            if blocks[0] != blocks[1]:
                raise ValueError('cleared record and metadata streams differ')
            if not blocks[0]:
                break
            for index, block in enumerate(blocks):
                sizes[index] += len(block)
                rows[index] += block.count(b'\n')
                for digest in hashes[index]:
                    digest.update(block)
    if before != [stat_key(first), stat_key(second)]:
        raise ValueError('cleared stream changed during comparison')
    result = [dict(path=str(path), bytes=sizes[index], newline_rows=rows[index],
                   sha256=hashes[index][0].hexdigest(), md5=hashes[index][1].hexdigest(),
                   source_identity=before[index]) for index,path in enumerate((first,second))]
    if any(row['bytes']!=315036094 or row['newline_rows']!=999953 or row['sha256']!=CLEARED_SHA for row in result):
        raise ValueError('cleared streams differ from the approved cohort')
    return result


def check_reply(stdout, returncode):
    perft = [int(value) for value in re.findall(r'^nodes (\d+)\s*$',stdout,re.M)]
    bench = [(int(depth),int(nodes)) for depth,nodes in re.findall(r'bench depth (\d+) nodes (\d+)',stdout)]
    if returncode != 0 or perft != PERFT or bench != PINS:
        raise ValueError('corrected lock pins did not match native output')
    if not re.search(r'^uciok\s*$',stdout,re.M) or not re.search(r'^readyok\s*$',stdout,re.M):
        raise ValueError('UCI handshake missing')
    return dict(perft5_actual=perft, bench_actual=bench)


def write(path, value):
    with path.open('x',encoding='utf-8') as output:
        json.dump(value,output,indent=2)


def run(output):
    low_priority()
    output=Path(output)
    storage_guard(output,allowance=4_000_000)
    output.mkdir()  # Exclusive, new evidence only; no existing artifact is touched.
    started=time.perf_counter()
    source_sha=sha256(__file__)
    record=dict(status='FAIL',strength='UNPROVEN',started_utc=datetime.now(timezone.utc).isoformat(),
                driver_sha256=source_sha,engine=str(ENGINE),expected_engine_sha256=LOCK,
                threads=1,hash_mb=16,priority='BelowNormal',bench_expected=PINS,perft5_expected=PERFT)
    try:
        if sha256(ENGINE)!=LOCK or sha256(V7/'manifest.json')!=V7_SHA:
            raise ValueError('wrong engine or changed protected v7 manifest')
        protected=fingerprint_tree(V7)
        if protected.get('manifest.json')!=V7_SHA:
            raise ValueError('protected v7 snapshot differs from pinned manifest')
        streams=compare_streams(CLEARED/'records.jsonl',CLEARED/'metadata.jsonl')
        commands=['uci','setoption name Threads value 1','setoption name Hash value 16',
                  'setoption name OwnBook value false','setoption name UseNNUE value true','isready',
                  'position startpos','go perft 5','position fen '+KIWIPETE,'go perft 5',
                  *['bench '+str(depth) for depth,_ in PINS],'quit']
        request='\n'.join(commands)+'\n'
        (output/'stdin.txt').write_text(request,encoding='utf-8')
        engine_started=time.perf_counter()
        try:
            result=subprocess.run([str(ENGINE)],input=request,text=True,capture_output=True,cwd=output,
                                  timeout=120,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        except subprocess.TimeoutExpired as error:
            for name,value in [('stdout.log',error.stdout),('stderr.log',error.stderr)]:
                (output/name).write_text(value.decode('utf-8',errors='replace') if isinstance(value,bytes) else value or '',encoding='utf-8')
            raise
        record['engine_seconds']=time.perf_counter()-engine_started
        (output/'stdout.log').write_text(result.stdout,encoding='utf-8')
        (output/'stderr.log').write_text(result.stderr,encoding='utf-8')
        record['engine_exit_code']=result.returncode
        record.update(check_reply(result.stdout,result.returncode))
        if sha256(ENGINE)!=LOCK or fingerprint_tree(V7)!=protected or sha256(__file__)!=source_sha:
            raise ValueError('engine, protected v7 artifact or harness changed')
        if any(stat_key(row['path'])!=row['source_identity'] for row in streams):
            raise ValueError('cleared data changed before closure')
        storage_guard(output,allowance=0)
        record.update(status='PASS',engine_sha256=LOCK,protected_v7=protected,
                      byte_identical_streams=True,streams=streams,
                      note='OFF uses the crew-recorded default UseNNUE=true; these checks establish no strength or speed claim.')
    except Exception as error:
        record['error']=str(error)
        raise
    finally:
        record['elapsed_seconds']=time.perf_counter()-started
        record['finished_utc']=datetime.now(timezone.utc).isoformat()
        record['evidence_sha256']={path.name:sha256(path) for path in output.iterdir() if path.is_file()}
        write(output/'REPORT.json',record)
    return record


if __name__=='__main__':
    print(json.dumps(run(sys.argv[1]),indent=2))

#!/usr/bin/env python3
"""Real, bounded CPU trainer compatibility smoke; not a training-gain experiment.
IDEA_SOURCE: Forge FPOS/FHCE contract, unchanged trainer CLI, user holdout rules.
Writes exclusively new directories; leaves failed artifacts for investigation.
"""
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import sqlite3
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tools/data'))
from forge_pos import Record, PosReader, PosWriter, aligned_records, text_record, file_hash
from forge_probe import ProbeClient

EVIDENCE = Path(__file__).resolve().parent
DATA = Path('/tmp/astra-a1-cpu-smoke-data')
RUN = Path('/tmp/astra-a1-cpu-smoke-run')
PILOT = Path('/tmp/astra-a1-filter-pilot-10000')
INDEX = Path('/tmp/astra-a1-filter-full-10m/position_index.sqlite')
HOLD = Path('/workspace/forge-nnue-handoff-20261023/selfplay-input/payload/forge_selfplay_013_head.txt')
PROBE = Path('/tmp/astra-a1-native-build/budget-status/forge_data_probe')
TRAINER = REPO / 'tools/nnue/train_resid_v3b.py'
PYTHON = '/tmp/astra-a1-torch-cpu-env/bin/python'


def record_json(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, indent=2); f.write('\n')


def identity(row):
    return row.board + bytes([row.meta & 1])


def metadata(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': file_hash(path)}


def run_logged(name, argv, timeout=180):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    code = None
    try:
        with (EVIDENCE/(name+'.stdout')).open('xb') as out, (EVIDENCE/(name+'.stderr')).open('xb') as err:
            result = subprocess.run(argv, stdout=out, stderr=err, timeout=timeout,
                                    cwd=REPO, env={**os.environ, 'OMP_NUM_THREADS':'1',
                                    'MKL_NUM_THREADS':'1', 'OPENBLAS_NUM_THREADS':'1',
                                    'PYTHONDONTWRITEBYTECODE':'1', 'TMPDIR':'/tmp'})
            code = result.returncode
    except subprocess.TimeoutExpired:
        code = 124
    finally:
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        record_json(EVIDENCE/(name+'.command.json'), {
            'argv':argv, 'cwd':str(REPO), 'returncode':code,
            'elapsed_seconds':time.monotonic()-started,
            'actual_child_os_cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
            'math_threads':1, 'device':'cpu', 'timeout_seconds':timeout})
    if code != 0:
        raise RuntimeError(f'{name} exited {code}; original logs retained')


def main():
    if DATA.exists() or RUN.exists():
        raise FileExistsError('Smoke requires new data and run directories')
    DATA.mkdir(); RUN.mkdir()
    pilot_meta = json.loads((PILOT/'summary.json').read_text())
    failed_meta = json.loads((INDEX.parent/'failure.json').read_text())
    paths = [PILOT/f'forge_filtered{suffix}' for suffix in ('.pos','.hce','.fen')]
    paths += [PILOT/'decisions.tsv.gz', PILOT/'summary.json', HOLD, INDEX,
              INDEX.parent/'failure.json', PROBE, TRAINER,
              REPO/'tools/data/forge_pos.py', REPO/'tools/data/forge_probe.py', Path(__file__)]
    before = [metadata(p) for p in paths]
    known_hold = failed_meta['holdouts'][0]
    actual_hold = next(x for x in before if x['path']==str(HOLD))
    if known_hold['sha256'] != actual_hold['sha256'] or known_hold['rows'] != 1500000:
        raise ValueError('Known 013 evidence does not match input')
    original_ids = []
    with gzip.open(PILOT/'decisions.tsv.gz','rt') as f:
        if next(f).rstrip('\n') != 'input_index\tdecision\tbestmove\tteacher_score\tnodes':
            raise ValueError('Unexpected original decision schema')
        for line in f:
            fields = line.rstrip('\n').split('\t')
            if fields[1] == 'kept': original_ids.append(int(fields[0]))
    db = sqlite3.connect(INDEX.as_uri()+'?mode=ro&immutable=1', uri=True)
    db.execute('PRAGMA query_only=ON')
    count = db.execute('SELECT count(*) FROM holdout').fetchone()[0]
    if count != 1499915: raise ValueError('Unexpected 013 index unique count')
    def in_hold(key):
        found = db.execute('SELECT key FROM holdout WHERE digest=?', (hashlib.sha256(key).digest(),)).fetchone()
        if found and found[0] != key: raise ValueError('Position digest collision')
        return found is not None
    training = []; train_keys = set(); exclusion_counts = {'known_013':0, 'duplicate':0}
    with PosReader(paths[0], paths[1]) as reader:
        if reader.n != len(original_ids): raise ValueError('Decision/output row count mismatch')
        # Exhaust the iterator even after selecting 512 to verify the entire pilot sidecar.
        for index, (row, fen) in enumerate(aligned_records(reader,paths[2],sidecar_format='fen')):
            if len(training) == 512: continue
            key = identity(row)
            if in_hold(key): exclusion_counts['known_013'] += 1; continue
            if key in train_keys: exclusion_counts['duplicate'] += 1; continue
            train_keys.add(key); training.append((index, original_ids[index], row, fen))
    if len(training) != 512: raise ValueError('Not enough disjoint train rows')
    if any(in_hold(key) for key in train_keys): raise ValueError('Train/013 overlap')
    holdout = []; hold_keys = set(); hold_skips = {'duplicate':0, 'train_overlap':0}
    with HOLD.open() as f, ProbeClient(PROBE,1024,hash_mb=1,workdir=EVIDENCE/'holdout_native') as probe:
        for index, line in enumerate(f):
            row, fen = text_record(line); key = identity(row)
            if key in train_keys: hold_skips['train_overlap'] += 1; continue
            if key in hold_keys: hold_skips['duplicate'] += 1; continue
            if not in_hold(key): raise ValueError('Original 013 row missing from index')
            response = probe.query(fen,op='inspect',request_id=f'hold013:{index}')
            hce = response.get('hce')
            if response.get('fen') != fen or type(hce) is not int or not -32767 <= hce <= 32767:
                raise ValueError('Native HCE/state mismatch')
            hold_keys.add(key); holdout.append((index, Record(row.board,row.score,row.meta,hce), fen))
            if len(holdout) == 512: break
    if len(holdout) != 512 or train_keys & hold_keys: raise ValueError('Invalid holdout selection')
    db.close()
    for stem, values in [('smoke_train',[(r,f) for _,_,r,f in training]),
                         ('smoke_holdout013',[(r,f) for _,r,f in holdout])]:
        with PosWriter(DATA,stem,with_hce=True,with_fen=True) as writer:
            for row,fen in values: writer.append(row,fen=fen)
    record_json(EVIDENCE/'selection.json',{
        'train_rows':512,'holdout_rows':512,'train_vs_smoke_holdout_position_overlap':0,
        'train_vs_supplied_013_index_position_overlap':0,'supplied_013_rows':1500000,
        'supplied_013_unique_positions':count,'train_exclusions':exclusion_counts,
        'holdout_skips':hold_skips,'train_row_ids':[{'pilot_output_row':i,'original_003_row':j} for i,j,_,_ in training],
        'holdout_original_013_rows':[i for i,_,_ in holdout],
        'original_003_inputs_previously_verified_by_pilot':pilot_meta['inputs'],
        'state_origin':'Original full FEN sidecars; no reconstruction',
        'hce_origin':{'train':pilot_meta['probe'],'holdout':metadata(PROBE)},
        'limits':['013 is a 1.5M-row prefix, not necessarily the full holdout shard.',
                  '014 and authoritative game IDs unavailable; no complete holdout/game-exclusion claim.',
                  'Smoke only: 4 updates on 256 presented rows; no training gain or Elo claim.'],
        'inputs_before':before,'outputs':[metadata(DATA/(stem+suffix)) for stem in ['smoke_train','smoke_holdout013'] for suffix in ['.pos','.hce','.fen']]})
    run_logged('trainer_help',[PYTHON,'-B',str(TRAINER),'--help'],timeout=30)
    argv = [PYTHON,'-B',str(TRAINER),'--train',str(DATA/'smoke_train.pos'),
            '--holdout',str(DATA/'smoke_holdout013.pos'),'--hce-dir',str(DATA),
            '--device','cpu','--adam-impl','torch','--dev-scalars','0','--shape','256',
            '--residual','--epochs','1','--batch-size','64','--steps-per-epoch','4',
            '--val-positions','512','--lr','0.001','--warmup-steps','1','--min-lr-frac','0.01',
            '--blend-start','1','--blend-end','0.8','--sigmoid-k','2.25','--seed','17',
            '--mmap-data','--order-buffers','1','--init-check','--loss-sync-every','1',
            '--run-dir',str(RUN)]
    run_logged('trainer',argv)
    stdout=(EVIDENCE/'trainer.stdout').read_text()
    epoch = re.search(r'EPOCH 1/1.*train_mse=([0-9.eE+-]+).*HOLDOUT n=512.*mse_teacher=([0-9.eE+-]+)',stdout)
    if not epoch or not all(math.isfinite(float(x)) for x in epoch.groups()):
        raise ValueError('Missing/nonfinite final losses')
    output_files=sorted(p for p in RUN.iterdir() if p.is_file())
    checkpoint=RUN/'epoch001-step000000004.pt'
    if not checkpoint.exists() or 'Finished: 256 positions' not in stdout:
        raise ValueError('Expected four-step checkpoint or presented count missing')
    for expected in before:
        if metadata(Path(expected['path'])) != expected: raise ValueError('Input/source changed: '+expected['path'])
    record_json(EVIDENCE/'result.json',{'status':'PASS_CPU_TRAINER_COMPATIBILITY_SMOKE',
        'train_mse_printed':float(epoch[1]),'holdout_teacher_mse_printed':float(epoch[2]),
        'trained_updates':4,'presented_training_rows':256,'train_rows_loaded':512,'holdout_rows_loaded':512,
        'unchanged_input_and_source_hashes_verified':True,'trainer_sha256':file_hash(TRAINER),
        'outputs':[metadata(p) for p in output_files],
        'scope':'Compatibility/finite-loss smoke only; no network adoption, training-gain or Elo claim.'})
    print((EVIDENCE/'result.json').read_text())


if __name__ == '__main__':
    try: main()
    except BaseException as exc:
        record_json(EVIDENCE/'failure.json',{'status':'FAILED_RETAINED','error':repr(exc)})
        raise

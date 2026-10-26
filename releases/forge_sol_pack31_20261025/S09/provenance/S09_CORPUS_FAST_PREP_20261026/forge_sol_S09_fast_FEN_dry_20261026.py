"""Authorized1024-position native corpus dry run only; no million-position run."""
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import sys
import time

HERE=Path(__file__).resolve().parent
OWNED=HERE.parent/'S08/forge_sol_S08_build_window_subreaper_20261026.py'
SOURCE=HERE/'forge_sol_S09_fast_FEN_generator_20261026.cpp'
LAUNCHER=HERE/'forge_sol_S09_fast_FEN_memory_exec_20261026.py'
PROTOCOL=HERE/'forge_sol_S09_fast_FEN_dry_protocol_20261026.json'
OUT=Path('/tmp/forge_sol_S09_native_20261026/fast_FEN_dry_once_20261026')
INPUTS=HERE.parent/'S09_NATIVE_PREP_20261026/forge_sol_S09_prepare_source_view_20261026.py'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
shared=load('s09_fast_owned',OWNED);inputs=load('s09_fast_source',INPUTS)


def main():
    if sys.argv[1:]!=['--execute-dry-only']:raise ValueError('explicit bounded dry grant required')
    if sorted(os.sched_getaffinity(0))!=[3] or os.getpriority(os.PRIO_PROCESS,0)!=19:raise ValueError('CPU3nice19 required')
    protocol=json.loads(PROTOCOL.read_text());core=Path(protocol['closed_reference_core']['path'])
    if shared.sha(OWNED)!='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0' or shared.sha(shared.CXX)!=shared.CXX_SHA or shared.sha(core)!=protocol['closed_reference_core']['sha256']:raise ValueError('frozen compiler/core/owned helper changed')
    if not all(v['unchanged'] for v in inputs.verify_all_baselines().values()):raise ValueError('original baseline changed')
    if shutil.disk_usage(OUT.parent).free<32*1048576:raise ValueError('dry temporary disk start floor32MiB')
    OUT.mkdir(exist_ok=False);start=time.monotonic();deadline=start+120
    before=inputs.inventory(inputs.BASES['L']);original=shared.boundary_reason
    def guard(_unused,limit):
        if time.monotonic()>=limit:return 'OWNED_DEADLINE'
        if shared._STOP_REQUESTED:return 'EXTERNAL_STOP'
        if shutil.disk_usage(OUT).free<16*1048576:return 'TEMP_DISK_FLOOR'
    shared.boundary_reason=guard;commands=[]
    record={'status':'FAIL_DRY','protocol_sha256':shared.sha(PROTOCOL),'source_sha256':shared.sha(SOURCE),'launcher_sha256':shared.sha(LAUNCHER),'controller_sha256':shared.sha(__file__),'core_sha256_before':shared.sha(core),'commands':commands,'native_fullmillion_runs':0,'nps_claim':False,'cpu':[3],'nice':19,'scope':'1024unique positions twice; compilation and rawlegal-FEN validation only'}
    def run(argv,label):
        r=shared.run_owned([sys.executable,'-B',str(LAUNCHER),*map(str,argv)],OUT,label,OUT,deadline);commands.append(r)
        if r.get('error') or r.get('stop_reason') or r.get('returncode')!=0 or not r.get('leader_reaped') or r.get('all_group_members_after_reap'):raise RuntimeError('owned dry command failed/open: '+label)
    try:
        exe=OUT/'forge_sol_S09_fast_FEN_generator_20261026'
        run([str(shared.CXX),'-std=c++20','-O3','-DNDEBUG',*shared.FLAGS.split(),'-I'+str(inputs.BASES['L']/'include'),str(SOURCE),str(core),'-pthread','-o',str(exe)],'00_compile')
        record['generator_sha256']=shared.sha(exe)
        for arm in ('01_dry1024','02_dry1024'):run([exe,'--positions','1024','--max-attempts','16384'],arm)
        import chess
        captures=[]
        for arm in ('01_dry1024','02_dry1024'):
            path=OUT/(arm+'.stdout');raw=path.read_bytes();rows=raw.decode('ascii').splitlines();keys=set()
            if len(rows)!=1024 or not raw.endswith(b'\n'):raise ValueError('dry count/EOF differs')
            for fen in rows:
                board=chess.Board(fen)
                if not board.is_valid() or board.fen(en_passant='fen')!=fen:raise ValueError('independent legal-FEN validation or canonical roundtrip failed')
                fields=fen.split()
                if len(fields)!=6:raise ValueError('full six-field FEN required')
                key=' '.join(fields[:4])
                if key in keys:raise ValueError('duplicate four-field FEN key')
                keys.add(key)
            captures.append({'arm':arm,'sha256':shared.sha(path),'bytes':len(raw),'independently_validated_positions':len(rows),'unique_FEN4':len(keys),'stderr_sha256':shared.sha(OUT/(arm+'.stderr'))})
            path.chmod(0o444)
        if (OUT/'01_dry1024.stdout').read_bytes()!=(OUT/'02_dry1024.stdout').read_bytes():raise ValueError('full deterministic FEN outputs differ')
        record.update(captures=captures,python_chess_version=chess.__version__,status='PASS_DRY',full_output_byteidentity=True)
    except BaseException as e:record['error']=type(e).__name__+': '+str(e)
    finally:
        shared.boundary_reason=original;record['baseline_source_unchanged']=before==inputs.inventory(inputs.BASES['L']);record['core_sha256_after']=shared.sha(core)
        record['child_peak_rss_kib']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss;record['elapsed_seconds']=time.monotonic()-start
        if not record['baseline_source_unchanged'] or record['core_sha256_after']!=record['core_sha256_before'] or record['child_peak_rss_kib']>4*1024**2:record.update(status='FAIL_DRY',postflight_error='source/core changed or child peakRSS exceeded4GiB')
        shared.save_new(OUT/'forge_sol_S09_fast_FEN_dry_result_20261026.json',record)
    print(json.dumps({'status':record['status'],'elapsed_seconds':record['elapsed_seconds'],'error':record.get('error')}));return 0 if record['status']=='PASS_DRY' else 1

if __name__=='__main__':
    signal.signal(signal.SIGTERM,shared._signal_stop);signal.signal(signal.SIGINT,shared._signal_stop)
    raise SystemExit(main())

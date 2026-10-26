"""Run the preregistered million unique legal-position corpus once; no engine."""
import importlib.util,json,os,resource,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s09_build_helpers',HERE/'forge_sol_S09_build_native_20261026.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def main():
    assert sorted(os.sched_getaffinity(0))==[1] and os.getpriority(os.PRIO_PROCESS,0)==19
    prereg=HERE/'forge_sol_S09_native_preregister_20261026.json'
    assert b.owned.sha(prereg)=='d92618f6dde3ce3f06ccd7209f3d71689239eedf339a8abeeeafef2f58c75486'
    p=json.loads(prereg.read_text());g=Path(p['corpus']['generator'])
    assert b.owned.sha(g)==p['corpus']['generator_sha256']
    out=b.TMP/'corpus_controller_once_20261026';out.mkdir(exist_ok=False)
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
    os.environ['PYTHONPATH']='/workspace/.cloud-setup/venv/lib/python3.12/site-packages'
    start=time.monotonic();deadline=start+900;maximum=0
    def guard(_job,end):
        nonlocal maximum
        if time.monotonic()>=end:return 'OWNED_DEADLINE'
        if b.shutil.disk_usage(b.TMP).free<32*1048576:return 'FREE_DISK_FLOOR'
        pids={os.getpid()};ev=out/'events.jsonl'
        if ev.exists():
            lines=ev.read_text().splitlines()
            if lines:pids.update(x['pid'] for x in b.owned._all_members(json.loads(lines[-1])['pid']))
        rss=0
        for pid in pids:
            try:
                for line in Path('/proc',str(pid),'status').read_text().splitlines():
                    if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
            except (OSError,ValueError):pass
        maximum=max(maximum,rss)
        if rss>4*1024**3:return 'OWNED_RSS_LIMIT'
    b.owned.boundary_reason=guard
    result={'status':'FAIL','preregister_sha256':b.owned.sha(prereg),'controller_sha256':b.owned.sha(__file__),
        'generator_sha256':b.owned.sha(g),'CPU':[1],'nice':19,'engine_executions':0}
    command=[b.os.sys.executable,'-B',str(g),'--count','1000000','--seed','20261026','--out',str(b.TMP/'million_unique_corpus_once_20261026')]
    try:
        r=b.owned.run_owned(command,out,'generate_million',out,deadline);result['command']=r
        assert r['returncode']==0 and not r['stop_reason'] and not r.get('error') and not r['all_group_members_after_reap']
        result['manifest']=json.loads((b.TMP/'million_unique_corpus_once_20261026/manifest.json').read_text())
        assert result['manifest']['count']==1000000 and result['manifest']['unique_position_fields']==1000000
        result['status']='PASS_LEGAL_CORPUS'
    except BaseException as exc:result['error']=type(exc).__name__+': '+str(exc)
    finally:
        result['maximum_observed_owned_RSS_bytes']=maximum;result['elapsed_seconds']=time.monotonic()-start
        b.owned.save_new(out/'forge_sol_S09_million_corpus_controller_result_20261026.json',result)
    print(json.dumps({'status':result['status'],'error':result.get('error'),'elapsed_seconds':result['elapsed_seconds']}))
    return 0 if result['status']=='PASS_LEGAL_CORPUS' else 1

if __name__=='__main__':raise SystemExit(main())

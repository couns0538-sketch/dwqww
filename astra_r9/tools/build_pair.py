"""Run the unchanged v2.3 kit twice; constrain only our process descendants."""
import datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time
sys.path.insert(0,'D:/a9/pydeps')
import psutil
root=pathlib.Path('D:/a9'); source=root/'c1'; repo=root/'src'
assert shutil.disk_usage('C:/').free>=30*2**30
assert shutil.disk_usage('D:/').free>=50*2**30
if not source.exists():
    source.mkdir()
    for folder in ['include','src']: shutil.copytree(repo/folder,source/folder)
manifest={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.rglob('*')) if p.is_file()}
manifest_path=repo/'astra_r9/evidence/c1-source.json'
if manifest_path.exists(): assert json.loads(manifest_path.read_text())==manifest
else: manifest_path.write_text(json.dumps(manifest,indent=2))
assert all(hashlib.sha256((repo/name).read_bytes()).hexdigest()==sha for name,sha in manifest.items())
kit=pathlib.Path('C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/kit_v23')
assert hashlib.md5((kit/'build_ltopgo.ps1').read_bytes()).hexdigest()=='729fe7275c3c01d22c751cb751d5c9d2'
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS); psutil.Process().cpu_affinity([2,3])
env=os.environ.copy(); env.update(TEMP='D:/a9/tmp',TMP='D:/a9/tmp',PYTHONDONTWRITEBYTECODE='1')
for tag in ['b1','b2']:
    # Wait without changing other workloads. Never monopolize a busy chosen CPU.
    while True:
        load=psutil.cpu_percent(interval=2,percpu=True)
        if load[2]<40 and load[3]<40: break
        print('WAIT cores2/3 busy',load[2:4],flush=True)
        if time.time()>datetime.datetime.fromisoformat('2026-11-01T19:57:00-08:00').timestamp():
            raise RuntimeError('resource deadline exceeded')
        time.sleep(15)
    cmd=['pwsh','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(kit/'build_ltopgo.ps1'),
         '-SrcDir',str(source),'-Tag',tag,'-Work','D:/a9/w','-Kit',str(kit),'-Affinity','12','-Expose',
         '-CheckOpt','NNUEWideOutput=true','-Pins','d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354',
         '-PerftPins','startpos=4865609,kiwipete=193690690']
    log=repo/f'astra_r9/evidence/{tag}-kit-console.log'
    with log.open('x') as f:
        f.write(json.dumps(cmd)+'\n'); f.flush()
        p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.IDLE_PRIORITY_CLASS)
        owner=psutil.Process(p.pid)
        while p.poll() is None:
            try: children=[owner]+owner.children(recursive=True)
            except psutil.NoSuchProcess: children=[]
            for child in children:
                try: child.nice(psutil.IDLE_PRIORITY_CLASS); child.cpu_affinity([2,3])
                except (psutil.NoSuchProcess,psutil.AccessDenied): pass
            time.sleep(.2)
        if p.returncode: raise RuntimeError(f'kit {tag} failed {p.returncode}; see {log}')
    longest=max(len(str(p)) for p in (root/'w'/tag).rglob('*.gcda'))
    assert longest<250,longest
    print(tag,'PASS gcda longest',longest,flush=True)
hashes={tag:hashlib.sha256((root/f'w/{tag}/src_copy/forge_ltopgo_{tag}.exe').read_bytes()).hexdigest() for tag in ['b1','b2']}
(repo/'astra_r9/evidence/build-pair.json').write_text(json.dumps(hashes,indent=2))
assert hashes['b1']==hashes['b2'],hashes
print('REPRODUCIBLE',hashes,flush=True)

"""R10 bounded kit invocation. Only scheduling changes; production flags untouched."""
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time
sys.path.insert(0, 'D:/a10/pydeps')
import psutil

ROOT = pathlib.Path('D:/a10')
KIT_MD5 = '729fe7275c3c01d22c751cb751d5c9d2'
def sha(p):
    with open(p, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--threads', type=int, choices=[1, 2], required=True)
    ap.add_argument('--tag', required=True)
    a = ap.parse_args()
    if not re.fullmatch(r'pc[12](?:-[a-z0-9]+)?', a.tag):
        ap.error('tag must be pc1/pc2 with optional new lowercase attempt suffix')
    evidence = ROOT/f'wt/astra_r10/job1/build-{a.tag}'
    evidence.mkdir(exist_ok=False)
    # Every preflight or native failure retains a machine-readable receipt.
    try:
        return execute(a, evidence)
    except BaseException as error:
        with (evidence/'exception.json').open('x') as stream:
            json.dump({'status':'FAIL','error':repr(error)}, stream, indent=2)
        raise

def execute(a, evidence):
    me = psutil.Process()
    assert me.nice() == psutil.IDLE_PRIORITY_CLASS
    assert set(me.cpu_affinity()) <= {2, 3}
    assert shutil.disk_usage('C:/').free >= 30*2**30
    assert shutil.disk_usage('D:/').free >= 51*2**30
    used = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
    assert used + 1_000_000_000 <= 15_000_000_000, used
    load = psutil.cpu_percent(interval=3, percpu=True)
    assert max(load[2:4]) < 50, ('spare core busy; retry only after quiet', load)
    original = ROOT/'kit/build_ltopgo.ps1'
    raw = original.read_bytes()
    assert hashlib.md5(raw).hexdigest() == KIT_MD5
    needle = b"$me.PriorityClass = 'BelowNormal'"
    assert raw.count(needle) == 1
    adapted = ROOT/f'kit/build_idle_{a.tag}.ps1'
    with adapted.open('xb') as stream:
        stream.write(raw.replace(needle, b"$me.PriorityClass = 'Idle'"))
    source = ROOT/'c1'
    manifest = {str(p.relative_to(source)):sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
    pinned_manifest = ROOT/'wt/astra_r9/evidence/c1-source.json'
    assert manifest == json.loads(pinned_manifest.read_text()), 'frozen R9 source drift'
    (evidence/'source.json').write_text(json.dumps(manifest, indent=2))
    cmd = ['C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-NonInteractive',
           '-File', str(adapted), '-SrcDir', str(source), '-Work', str(ROOT/'b'), '-Tag', a.tag,
           '-Kit', str(ROOT/'kit'), '-Affinity', '12', '-Flto', '-flto=1', '-Expose',
           '-Python', str(ROOT/'python/python.exe'), '-CheckOpt', 'NNUEWideOutput=true',
           '-Pins', 'd11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354',
           '-PerftPins', 'startpos=4865609,kiwipete=193690690']
    record = {'argv':cmd, 'original_kit_md5':KIT_MD5, 'adapted_sha256':sha(adapted),
              'only_change':"$me.PriorityClass BelowNormal -> Idle", 'load_before':load,
              'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status':'RUNNING'}
    record['tools_sha256'] = {str(p):sha(p) for p in [
        pathlib.Path(cmd[0]), ROOT/'python/python.exe', pinned_manifest,
        pathlib.Path('C:/msys64/ucrt64/bin/g++.exe'), pathlib.Path('C:/msys64/ucrt64/bin/objdump.exe'),
        ROOT/'kit/tools/lp_check.py', ROOT/'kit/tools/gcda_arcs_digest.py',
        ROOT/'kit/workload/frozen_train_cmds.txt', ROOT/'kit/workload/bench_fens.txt']}
    (evidence/'command.json').write_text(json.dumps(record, indent=2))
    env = os.environ.copy()
    env.update(TEMP='D:/a10/tmp', TMP='D:/a10/tmp', PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               PSModulePath='C:/Windows/System32/WindowsPowerShell/v1.0/Modules;C:/Program Files/WindowsPowerShell/Modules')
    with (evidence/'console.log').open('xb') as log:
        p = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                             creationflags=subprocess.IDLE_PRIORITY_CLASS)
        record['owned_pid'] = p.pid
        (evidence/'command.json').write_text(json.dumps(record, indent=2))
        owner = psutil.Process(p.pid)
        tracked = {p.pid:owner.create_time()}
        cleanup = []
        try:
            deadline = time.monotonic() + 7200
            while p.poll() is None:
                try: descendants = owner.children(recursive=True)
                except psutil.NoSuchProcess: descendants = []
                for child in descendants:
                    try: tracked[child.pid] = child.create_time()
                    except psutil.NoSuchProcess: pass
                if time.monotonic() > deadline:
                    raise TimeoutError('bounded kit deadline; inspect retained outputs')
                time.sleep(.2)
            code = p.returncode
        finally:
            # Only observed descendants with unchanged creation identities are ours.
            # A timeout remains failed and requires a residual-process audit.
            try:
                for pid, created in reversed(list(tracked.items())):
                    try:
                        child = psutil.Process(pid)
                        if child.create_time() == created and child.is_running():
                            child.kill(); child.wait(timeout=15)
                            cleanup.append({'pid':pid,'created':created,'action':'terminated owned residual'})
                    except psutil.NoSuchProcess: pass
                p.wait(timeout=15)
            finally:
                (evidence/'ownership.json').write_text(json.dumps({'observed':tracked,'cleanup':cleanup}, indent=2))
        if cleanup and code == 0:
            raise RuntimeError('successful kit left residual children; invalid build')
    record['exit_code'] = code
    record['status'] = 'PASS' if code == 0 else 'FAIL'
    record['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if code == 0:
        exe = ROOT/f'b/{a.tag}/src_copy/forge_ltopgo_{a.tag}.exe'
        record['exe'] = str(exe); record['exe_sha256'] = sha(exe)
        assert {str(p.relative_to(source)):sha(p) for p in sorted(source.rglob('*')) if p.is_file()} == manifest
        assert all(sha(p) == h for p,h in record['tools_sha256'].items()), 'tool drift'
    (evidence/'result.json').write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2), flush=True)
    return code

if __name__ == '__main__':
    sys.exit(main())

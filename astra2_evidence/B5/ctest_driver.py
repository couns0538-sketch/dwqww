import pathlib,subprocess,sys,json,hashlib,datetime
build=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=False)
cmd=['/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest','--test-dir',str(build),'--output-on-failure','--timeout','300','-j1']
(out/'command.json').write_text(json.dumps({'argv':cmd,'utc_start':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
with (out/'ctest.log').open('wb') as f: r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
(out/'exit.txt').write_text(str(r.returncode)+'\n')
for name in ['LastTest.log','LastTestsFailed.log']:
 p=build/'Testing'/'Temporary'/name
 if p.exists():(out/name).write_bytes(p.read_bytes())
print('ctest exit',r.returncode,flush=True)
sys.exit(r.returncode)

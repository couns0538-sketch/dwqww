"""Planted-bug check for forge_sol_S16_overlap_scan.py: every mutant must make test_forge_sol_S16_overlap_scan.py FAIL
and the unmutated copy must PASS. Usage: <python with numpy> -I -B mutation_check_scan.py <NEW scratch dir>"""
import os,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent;TOOL=HERE/'forge_sol_S16_overlap_scan.py';TESTS=HERE/'test_forge_sol_S16_overlap_scan.py'
MUTANTS=[
 ('exact 33-byte check removed','same=(exact_keys(bd[cand],mt[cand])==H.exact(g)).all(axis=1)','same=np.ones(len(cand),bool)'),
 ('side to move dropped from the 64-bit key','return mix64(h^((metas&1).astype(U64)+U64(0x632be59bd9b4e019)))','return mix64(h^U64(0x632be59bd9b4e019))'),
 ('label conflict ignores the score','conf=(sc[cand].astype(np.int32)!=hs)|((mt[cand]>>1)!=hr)','conf=((mt[cand]>>1)!=hr)'),
 ('game boundary ignores a result change','return (fm[1:]<fm[:-1])|(pc[1:]>pc[:-1])|(res[1:]!=res[:-1])','return (fm[1:]<fm[:-1])|(pc[1:]>pc[:-1])'),
 ('interleaving tripwire limit raised','TRIPWIRE_WINDOW,TRIPWIRE_LIMIT=100,20','TRIPWIRE_WINDOW,TRIPWIRE_LIMIT=100,200'),
 ('every junction treated as a new game',"new_game=first[0]<last[0] or first[1]>last[1] or first[2]!=last[2]","new_game=True"),
 ('output directory next to the data allowed',"if out==d or d in out.parents:raise ValueError","if False:raise ValueError"),
 ('free-RAM guard disabled',"if free is not None and free<(args.min_free_ram_gib+extra)*2**30:raise","if False:raise"),
 ('text/POS field check removed',"if max(f_fm)>32767 or not (","if False and not ("),
 ('holdout duplicates not propagated (representative row only)',"hit_rows=np.empty(H.n,bool);hit_rows[H.order]=hit_run[H.run_id]","hit_rows=np.zeros(H.n,bool);hit_rows[H.order[np.flatnonzero(np.r_[True,H.run_id[1:]!=H.run_id[:-1]])]]=hit_run"),
 ('gzip timestamp not fixed',"fileobj=raw,mtime=0,compresslevel=6","fileobj=raw,mtime=None,compresslevel=6"),
 ('whole-file duplicate report dropped',"summary['whole_file_duplicates']=[v for v in md5s.values() if len(v)>1]","summary['whole_file_duplicates']=[]"),
 ('holdout-internal collision accepted',"if not np.array_equal(self.exact(self.order[d]),self.exact(self.order[d-1])):raise ValueError","if False:raise ValueError"),
 ('training file that is a holdout file accepted',"if any(os.path.samefile(t,h) for h in holdout_paths):raise","if False:raise"),
]
def suite(tool,work):
    env={**os.environ,'FORGE_S16_SCAN_TOOL':str(tool),'FORGE_S16_TEST_ROOT':str(work)}
    t=time.monotonic();r=subprocess.run([sys.executable,'-I','-B',str(TESTS)],env=env,capture_output=True,text=True,timeout=600)
    tail=[l for l in r.stderr.splitlines() if l.startswith(('Ran ','OK','FAILED'))];return r.returncode,' / '.join(tail),time.monotonic()-t
def main():
    root=pathlib.Path(sys.argv[1]).resolve();root.mkdir(parents=True,exist_ok=False);src=TOOL.read_text(encoding='utf-8');ok=True
    (root/'clean').mkdir();(root/'clean'/TOOL.name).write_bytes(src.encode())
    code,tail,secs=suite(root/'clean'/TOOL.name,root/'clean'/'work');print(f'clean copy: rc={code} {tail} ({secs:.1f} s) -> {"PASS" if code==0 else "FAIL"}');ok&=code==0
    for n,(name,old,new) in enumerate(MUTANTS,1):
        if src.count(old)!=1:print(f'm{n:02d} {name}: pattern found {src.count(old)} times -> FAIL (stale mutant)');ok=False;continue
        d=root/f'm{n:02d}';d.mkdir();(d/TOOL.name).write_bytes(src.replace(old,new).encode())
        code,tail,secs=suite(d/TOOL.name,d/'work');caught=code!=0;ok&=caught
        print(f'm{n:02d} {name}: rc={code} {tail} ({secs:.1f} s) -> {"caught" if caught else "SURVIVED"}')
    print(f'mutation check: {"PASS" if ok else "FAIL"} ({len(MUTANTS)} mutants)');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())

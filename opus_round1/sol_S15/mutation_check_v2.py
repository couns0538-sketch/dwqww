"""Planted-bug check for forge_sol_S15_spsa_v2.py: each mutant must make test_forge_sol_S15_spsa_v2.py FAIL, and the
unmutated copy must PASS. Usage: python -I -B mutation_check_v2.py <NEW scratch dir>   (writes only below that dir)"""
import os,pathlib,subprocess,sys,time
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
TOOL=HERE/'forge_sol_S15_spsa_v2.py';TESTS=HERE/'test_forge_sol_S15_spsa_v2.py'
MUTANTS=[
 ('gradient sign flipped','proposed=[x+gain*difference/step','proposed=[x-gain*difference/step'),
 ('probe RNG ignores the iteration',"rng=random.Random(f'ForgeSolS15:{seed}:{iteration}')","rng=random.Random(f'ForgeSolS15:{seed}')"),
 ('duplicate declaration accepted',"if name in declarations:raise ValueError('Duplicate tunable declaration')","if False:raise ValueError('Duplicate tunable declaration')"),
 ('adjudication cap re-added',"'level=warn','append=false','-strict']","'level=warn','append=false','-strict','-maxmoves','200']"),
 ('application proof skipped',"proofs={label:prove_applied(catalog,engine,planned['probe'][label],idir/f'forge_sol_S15_uci_proof_{label}_{DATE}.txt',60,args.priority,idir) for label in ('plus','minus')}","proofs={label:{'result':'APPLIED'} for label in ('plus','minus')}"),
 ('pentanomial cross-check skipped',"if reported!=observed['statistics']['pentanomial_0_half_1_1half_2']:raise","if False:raise"),
 ('state not chained between iterations',"if state:argv+=['--state',str(state)]","pass"),
 ('SHA256SUMS written in text mode (CRLF on Windows)',"with (out/f'forge_sol_S15_SHA256SUMS_{DATE}.txt').open('xb') as stream:stream.write(''.join(rows).encode())","with (out/f'forge_sol_S15_SHA256SUMS_{DATE}.txt').open('x') as stream:stream.write(''.join(rows))"),
 ('CRLF PGN not normalized for the checker',"text=raw.decode('utf-8').replace('\\r\\n','\\n')","text=raw.decode('utf-8')"),
 ('child priority not set',"return {'creationflags':subprocess.IDLE_PRIORITY_CLASS if priority=='idle' else subprocess.BELOW_NORMAL_PRIORITY_CLASS}","return {'creationflags':0}"),
 ('free-RAM guard disabled',"if free is not None and free<args.min_free_ram_gib*2**30:return finish(","if False:return finish("),
 ('fastchess exit code ignored',"if code!=0:raise ValueError(f'fastchess exited with code {code} in iteration {i}')","if False:raise ValueError(f'fastchess exited with code {code} in iteration {i}')"),
 ('e.p. normalization removed (exact FEN match only)',"(e.split()[3]==a[3] or a[3]=='-')","(e.split()[3]==a[3])"),
 ('child timeout not enforced','try:child.communicate(stdin_bytes,timeout=timeout)','try:child.communicate(stdin_bytes,timeout=None)'),
 ('wall budget ignored',"if elapsed+args.iteration_timeout>args.max_wall_seconds:return finish(","if False:return finish("),
 ('openings no longer rotate per iteration',"f'{args.seed}:{iteration}\\n{fen}'","f'{args.seed}\\n{fen}'"),
]
def suite(tool,work):
 env={**os.environ,'FORGE_S15_TOOL':str(tool),'FORGE_S15_TEST_ROOT':str(work)}
 t=time.monotonic();r=subprocess.run([sys.executable,'-I','-B',str(TESTS)],env=env,capture_output=True,text=True,timeout=600)
 tail=[l for l in r.stderr.splitlines() if l.startswith(('Ran ','OK','FAILED'))]
 return r.returncode,' / '.join(tail),time.monotonic()-t
def main():
 if len(sys.argv)!=2:raise SystemExit(__doc__)
 root=pathlib.Path(sys.argv[1]).resolve();root.mkdir(parents=True,exist_ok=False);source=TOOL.read_text(encoding='utf-8');ok=True
 clean=root/'clean';clean.mkdir();(clean/TOOL.name).write_bytes(source.encode())
 code,tail,secs=suite(clean/TOOL.name,clean/'work');print(f'clean copy: rc={code} {tail} ({secs:.1f} s) -> {"PASS" if code==0 else "FAIL"}');ok&=code==0
 for n,(name,old,new) in enumerate(MUTANTS,1):
  if source.count(old)!=1:print(f'm{n:02d} {name}: pattern found {source.count(old)} times -> FAIL (stale mutant)');ok=False;continue
  d=root/f'm{n:02d}';d.mkdir();(d/TOOL.name).write_bytes(source.replace(old,new).encode())
  code,tail,secs=suite(d/TOOL.name,d/'work');caught=code!=0;ok&=caught
  print(f'm{n:02d} {name}: rc={code} {tail} ({secs:.1f} s) -> {"caught" if caught else "SURVIVED"}')
 print(f'mutation check: {"PASS" if ok else "FAIL"} ({len(MUTANTS)} mutants)');return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())

"""Record auxiliary build commands from execution history and scan production FMA."""
import hashlib,json,os,pathlib,re,subprocess,sys
sys.path.insert(0,'D:/a9/pydeps')
import psutil
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS);psutil.Process().cpu_affinity([3])
root=pathlib.Path(__file__).parents[1];repo=root.parent
gcc='C:/msys64/ucrt64/bin/g++.exe';clang='D:/a9/toolchain/llvm-mingw-20261020-ucrt-x86_64/bin/clang++.exe'
env=os.environ.copy();env['PATH']=str(pathlib.Path(gcc).parent)+';'+env['PATH']
lock='C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean'
baseflags=['-std=c++20','-O3','-DFORGE_NNUE_HIDDEN=256','-ffp-contract=off','-fno-fast-math','-march=znver5','-static','-pthread']
test='astra_r9/tools/eval_exact.cpp';units=['bitboard','board','eval','eval_params','nnue']
wide=[gcc]+baseflags[:3]+['-DR9_TEST_WIDE','-DFORGE_NNUE_DIAGNOSTICS']+baseflags[3:]+['-Iinclude',test]+['src/'+u+'.cpp' for u in units]+['-o','D:/a9/checks/eval_wide02.exe']
reference=[gcc]+baseflags+['-I'+lock+'/include',test]+[lock+'/src/'+u+'.cpp' for u in units]+['-o','D:/a9/checks/eval_lock02.exe']
san=[clang,'-std=c++20','-O1','-g','-DFORGE_NNUE_HIDDEN=256','-DFORGE_EXPOSE_TUNABLES=1','-march=znver5',
     '-ffp-contract=off','-fno-fast-math','-fsanitize=address,undefined','-fno-sanitize-recover=all',
     '-fno-omit-frame-pointer','-pthread','-ID:/a9/c1/include']+[str(p) for p in sorted(pathlib.Path('D:/a9/c1/src').glob('*.cpp'))]+['-o','D:/a9/checks/forge_san_c1.exe']
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
record={'note':'Auxiliary commands transcribed from executed tool history after review; not claimed to be contemporaneous command logs. Original stdout logs retained, empty on success.',
        'cwd':str(repo),'environment':{'TEMP':'D:/a9/tmp','TMP':'D:/a9/tmp'},
        'source_commit':subprocess.check_output(['git','rev-parse','fb58080'],cwd=repo,text=True).strip(),
        'harness_sha256':sha(repo/test),'candidate_source_manifest_sha256':sha(root/'evidence/c1-source.json'),
        'compilers':{},'builds':[],'sanitizer_run_environment':{'ASAN_OPTIONS':'halt_on_error=1:detect_leaks=0','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1'}}
for name,path in [('gcc',gcc),('clang',clang)]:
    record['compilers'][name]={'path':path,'sha256':sha(path),'version':subprocess.check_output([path,'--version'],env=env,text=True)}
for name,cmd in [('reference',reference),('wide',wide),('sanitizer',san)]:
    record['builds'].append({'name':name,'argv':cmd,'exe_sha256':sha(cmd[-1])})
with (root/'evidence/auxiliary-build-provenance.json').open('x') as f:json.dump(record,f,indent=2)
exe='D:/a9/w/b1/src_copy/forge_ltopgo_b1.exe';tool='C:/msys64/ucrt64/bin/objdump.exe'
disasm=subprocess.check_output([tool,'-d','-C',exe],env=env)
# Cover scalar/packed and positive/negated add/subtract/interleaved FMA spellings.
pattern=rb'\b(?:vfmadd|vfmsub|vfnmadd|vfnmsub|vfmaddsub|vfmsubadd)[a-z0-9]*\b'
hits=sorted(set(m.group().decode() for m in re.finditer(pattern,disasm)))
scan={'exe':exe,'exe_sha256':sha(exe),'argv':[tool,'-d','-C',exe],'objdump_sha256':sha(tool),
      'disassembly_sha256':hashlib.sha256(disasm).hexdigest(),'pattern':pattern.decode(),'mnemonics':hits,'status':'PASS' if not hits else 'FAIL'}
with (root/'evidence/fma-family-scan.json').open('x') as f:json.dump(scan,f,indent=2)
assert not hits,hits
print('Auxiliary provenance recorded; all-family FMA scan PASS')

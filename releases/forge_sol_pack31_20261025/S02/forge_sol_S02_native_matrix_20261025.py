from pathlib import Path
import base64,hashlib,json,re,subprocess,collections,shutil
H=Path('/workspace/forge-pack24-20261025');S=H/'S02';CM='/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake';CT='/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest';P=H/'forge_sol_jobpack_24jobs_20261025/files';out=S/'forge_sol_S02_native_20261025';out.mkdir(exist_ok=False)
REF={11:308972,13:745494,16:2460422,20:11901452,22:31111774};KNOWN=collections.Counter([b'FAIL: WAC 001 expected g3g6 got f6h5',b'FAIL: WAC 001 score 661 below 31997',b'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion',b'FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion'])
RESULT={'status':'INCOMPLETE','profiles':[],'commands':[]}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(label,argv,folder=None,data=None,cwd=None):
 p=subprocess.run([str(x) for x in argv],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=cwd);record={'argv':[str(x) for x in argv],'actual_exit':p.returncode,'stdout_base64':base64.b64encode(p.stdout).decode(),'stderr_base64':base64.b64encode(p.stderr).decode(),'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()};f=(folder or out)/(label+'.json');f.write_text(json.dumps(record,indent=2)+'\n');RESULT['commands'].append({'record':str(f.relative_to(out)),'actual_exit':p.returncode});return p
try:
 for tag in ['L','B']:
  src=S/f'forge_sol_S02_final_{tag}_20261025'
  for kind in ['release_off','release_on','asan_on']:
   asan=kind.startswith('asan');on=kind.endswith('_on');profile='asan' if asan else 'release';common=H/f'forge_sol_S00_{tag}_{profile}_20261025';root=out/f'forge_sol_S02_{tag}_{kind}_20261025';root.mkdir();config=root/'configure';baseflags=['-march=x86-64-v3','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-DFORGE_NNUE_HIDDEN=256'];opt=['-O1','-g1','-DNDEBUG'] if asan else ['-O3','-DNDEBUG'];san=['-fsanitize=address,undefined','-fno-omit-frame-pointer'] if asan else []
   cfg=[CM,'-S',src,'-B',config,'-DCMAKE_BUILD_TYPE=Release','-DFORGE_WARN_UNKNOWN_OPTIONS='+('ON' if on else 'OFF'),'-DCMAKE_CXX_FLAGS='+' '.join(baseflags),'-DFORGE_ENABLE_SANITIZERS='+('ON' if asan else 'OFF')]
   if asan:cfg+=['-DCMAKE_CXX_FLAGS_RELEASE=-O1 -g1 -DNDEBUG']
   if run('forge_sol_S02_configure_20261025',cfg,root).returncode:raise RuntimeError('configure failed')
   count=15 if tag=='B' else 14
   n=run('forge_sol_S02_ctest_listing_20261025',[CT,'--test-dir',config,'-N'],root);expected=count+(1 if on else 0);assert n.returncode==0 and re.search(rb'Total Tests: '+str(expected).encode()+rb'\b',n.stdout)
   assert (b'forge_unknown_option_regression' in n.stdout)==on
   obj=root/'forge_sol_S02_uci_20261025.o';exe=root/'forge_sol_S02_engine_20261025.elf';defines=['-DFORGE_WARN_UNKNOWN_OPTIONS=1'] if on else []
   build=['/usr/bin/c++',*baseflags,*opt,'-std=gnu++20','-ffp-contract=off',*san,*defines,'-I'+str(src/'include'),'-c',src/'src/uci.cpp','-o',obj];assert run('forge_sol_S02_compile_20261025',build,root).returncode==0
   lib=common/'build/libforge_core.a';link=['/usr/bin/c++',*baseflags,*opt,*san,obj,lib,'-o',exe];assert run('forge_sol_S02_link_20261025',link,root).returncode==0
   # No earlier engine invocation for this new executable.
   first=run('forge_sol_S02_first_bare_d11_20261025',[exe],root,b'bench 11\nquit\n');assert first.returncode==0 and not first.stderr and re.search(rb'bench depth 11 nodes 308972\b',first.stdout)
   engine_sha=digest(exe);old_sha=digest(common/'build/forge');row={'base':tag,'profile':kind,'engine_sha256':engine_sha,'original_engine_sha256':old_sha,'original_core_archive_sha256':digest(lib),'unchanged_core_reused':True,'uci_source_sha256':digest(src/'src/uci.cpp'),'first_invocation_bare_d11':True,'cmake_registered_tests':expected,'new_ctest_registered':on}
   if kind=='release_off':
    assert engine_sha==old_sha,'default build binary differs';previous=json.loads((common/'forge_sol_S00_native_receipt_20261025.json').read_text());assert previous['status'].startswith('PASS_');row['default_engine_byte_identical']=True;row['fixed_reference_perft_FMA_receipt_reused_by_identical_binary_sha256']=str(common/'forge_sol_S00_native_receipt_20261025.json')
   if kind=='release_on':
    counts={11:308972}
    for depth,expected_nodes in list(REF.items())[1:]:
     b=run(f'forge_sol_S02_bench_d{depth}_20261025',[exe],root,f'bench {depth}\nquit\n'.encode());assert b.returncode==0 and not b.stderr and re.search(fr'bench depth {depth} nodes {expected_nodes}\b'.encode(),b.stdout);counts[depth]=expected_nodes
    for name,position,expected_nodes in [('start','startpos',4865609),('kiwi','fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',193690690)]:
     b=run(f'forge_sol_S02_perft_{name}_20261025',[exe],root,f'position {position}\ngo perft 5\nquit\n'.encode());assert b.returncode==0 and not b.stderr and re.search(fr'(?m)^nodes {expected_nodes}\s*$'.encode(),b.stdout)
    checker=P/'04_refs/check_nnue_simd_v2_fma_checker.py';assert run('forge_sol_S02_fma_v2_20261025',['python3','-B',checker,exe],root).returncode==0;row['fixed_nodes']=counts;row['perft']=[4865609,193690690];row['fma']=0
   test=run('forge_sol_S02_warning_regression_20261025',['python3','-B',S/'forge_sol_S02_unknownopt_test_20261025.py','--engine',exe,'--expect-warning','on' if on else 'off','--reference-engine',common/'build/forge'],root);assert test.returncode==0 and not test.stderr;assert json.loads(test.stdout)['status']=='PASS';row['warning_and_uci_regression']='PASS'
   # Reuse immutable original suite binaries. All frontend-driven tests use S02.
   template=(config/'CTestTestfile.cmake').read_text();harness=root/'harness';harness.mkdir();oldbuild=common/'build';changed=template.replace(str(config),str(oldbuild));saved=H/f'forge_sol_S01_full_matrix_20261025/forge_sol_S01_saved_{tag}_{profile}_20261025/forge_sol_S01_original_tests_20261025.elf'
   changed=changed.replace('"'+str(oldbuild/'forge_tests')+'"','"'+str(saved)+'"');changed=changed.replace('"'+str(oldbuild/'forge')+'"','"'+str(exe)+'"');changed=changed.replace(str(oldbuild/'uci-regression.log'),str(harness/'forge_sol_S02_uci_regression_20261025.log'));changed=changed.replace(str(oldbuild/'ownbook-regression.json'),str(harness/'forge_sol_S02_ownbook_regression_20261025.json'))
   (harness/'CTestTestfile.cmake').write_text(changed);(root/'forge_sol_S02_harness_changes_20261025.json').write_text(json.dumps({'original_template_sha256':hashlib.sha256(template.encode()).hexdigest(),'used_template_sha256':hashlib.sha256(changed.encode()).hexdigest(),'substitutions':['unbuilt helper targets -> existing original suite binaries','forge_tests -> saved original four-failure binary','frontend -> fresh S02 engine','log outputs -> own harness directory'],'original_tests_sha256':digest(saved)},indent=2)+'\n')
   ct=run('forge_sol_S02_full_ctest_20261025',[CT,'--test-dir',harness,'--output-on-failure','-j','1'],root);lines=collections.Counter(x.strip() for x in ct.stdout.splitlines() if x.startswith(b'FAIL:'));assert ct.returncode==8 and lines==KNOWN,(tag,kind,ct.returncode,lines)
   assert b'1 tests failed out of '+str(count+(1 if on else 0)).encode() in ct.stdout
   assert b'ERROR: AddressSanitizer' not in ct.stdout+ct.stderr and b'runtime error:' not in ct.stdout+ct.stderr
   row['ctest_actual_exit']=ct.returncode;row['only_known_fail_lines']=4;row['only_failing_ctest_target']='forge_tests';RESULT['profiles'].append(row);(out/'forge_sol_S02_native_partial_20261025.json').write_text(json.dumps(RESULT,indent=2)+'\n')
 RESULT['status']='PASS_SIX_NATIVE_PROFILES_DEFAULT_IDENTITY_AND_WARNING'
finally:(out/'forge_sol_S02_native_receipt_20261025.json').write_text(json.dumps(RESULT,indent=2)+'\n')
print(json.dumps({k:v for k,v in RESULT.items() if k!='commands'},indent=2))

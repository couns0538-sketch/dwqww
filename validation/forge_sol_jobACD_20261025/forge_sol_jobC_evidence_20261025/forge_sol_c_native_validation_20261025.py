#!/usr/bin/env python3
"""Actual C-only suite and negative controls, linked to frozen original-lock PGO objects."""
from pathlib import Path
import hashlib,json,subprocess
h=Path('/workspace/forge-jobACD-C-20261025'); lock=Path('/workspace/forge-jobACD-20261025/forge_sol_jobACD_pack_20261025/01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src'); obj=Path('/workspace/forge-sol-20261025-pgo/forge_sol_pgo_linux_proof_20261025/work/obj')
objects=[obj/(n+'.o') for n in ['bitboard','board','book','eval','eval_params','nnue','search']]
flags=['-std=c++20','-O3','-DNDEBUG','-DFORGE_NNUE_HIDDEN=256','-ffp-contract=off','-fno-fast-math','-march=znver5','-static','-pthread','-I'+str(lock/'include')]
results={'source_core':'Exact unchanged lock engine, compiler-only final Linux PGO objects reused; not JobA macro1 core','objects':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in objects},'compiler':subprocess.check_output(['g++','--version'],text=True),'cases':[]}
(h/'forge_sol_c_native_provenance_20261025.json').write_text(json.dumps(results,indent=2)+'\n')
source=(h/'source/tests/tests.cpp').read_text()
mutations=[('candidate',None,None),('unrelated_mate_expectation','3, "e1e8", forge::MateValue - 1','3, "e1e7", forge::MateValue - 1'),('wac_known_move','best == "f6h5" && result.score == 661','best == "g3h4" && result.score == 661'),('wac_known_score','result.score == 661 && result.depth == 12','result.score == 660 && result.depth == 12'),('white_king_alternative','mirrored ? "c3d2" : "c6d7"','mirrored ? "c3d2" : "c6b6"'),('black_king_alternative','mirrored ? "c3d2" : "c6d7"','mirrored ? "c3d3" : "c6d7"'),('promotion_PV_guard','result.pv.front() == *documented_king && result.score > 100','result.pv.front() != *documented_king && result.score > 100'),('promotion_depth_guard','result.score > 100 && result.depth == 1;\n        if (documented_promotion_horizon)','result.score > 100 && result.depth == 2;\n        if (documented_promotion_horizon)'),('null_pruning_guard','forge::SearcherTestProbe::null_tries(searcher) > 0 && forge::SearcherTestProbe::null_cutoffs(searcher) > 0','forge::SearcherTestProbe::null_tries(searcher) == 0 && forge::SearcherTestProbe::null_cutoffs(searcher) == 0')]
for name,old,new in mutations:
 case=h/('forge_sol_c_'+name+'_20261025');case.mkdir(exist_ok=False)
 text=source
 if old:
  assert source.count(old)==1,(name,source.count(old));text=source.replace(old,new,1)
 src=case/'forge_sol_c_tests_20261025.cpp';src.write_text(text);binary=case/'forge_sol_c_tests_20261025'
 argv=['g++',*flags,str(src),*[str(p) for p in objects],'-o',str(binary)]
 (case/'forge_sol_build_command_20261025.json').write_text(json.dumps(argv,indent=2)+'\n')
 proc=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (case/'forge_sol_build_20261025.stdout').write_bytes(proc.stdout);(case/'forge_sol_build_20261025.stderr').write_bytes(proc.stderr)
 assert proc.returncode==0,(name,proc.returncode,proc.stderr.decode())
 proc=subprocess.run([str(binary)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (case/'forge_sol_run_20261025.stdout').write_bytes(proc.stdout);(case/'forge_sol_run_20261025.stderr').write_bytes(proc.stderr)
 lines=(proc.stdout+b'\n'+proc.stderr).decode().splitlines();known=[s for s in lines if s.startswith('KNOWN_FAILURE:')];fail=[s for s in lines if s.startswith('FAIL:')]
 expected=(proc.returncode==0 and len(known)==4 and not fail) if name=='candidate' else(proc.returncode==1 and len(fail)>0)
 row={'case':name,'status':'PASS' if expected else 'FAIL','build_exit':0,'actual_suite_exit':proc.returncode,'known_lines':known,'fail_lines':fail,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'test_source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
 results['cases'].append(row);(h/'forge_sol_c_native_results_20261025.json').write_text(json.dumps(results,indent=2)+'\n');print(name,row['status'],proc.returncode,len(known),len(fail),flush=True)
 assert expected,row
print('ALL_C_NATIVE_CASES_PASS')

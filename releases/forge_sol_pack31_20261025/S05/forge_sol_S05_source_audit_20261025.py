from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parent;p=r.parent/'forge_sol_jobpack_24jobs_20261025/files'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
rows=[]
for base,rel in [('L','01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src'),('B','01b_base_h256_e12_buffix/forge_h256_e12_buffix_src')]:
 original=p/rel;working=r/f'forge_sol_S05_{base}_final_applyproof_20261025';core=[]
 for folder in ('src','include'):
  for f in sorted((original/folder).rglob('*')):
   if f.is_file():
    q=working/f.relative_to(original);assert sha(f)==sha(q);core.append({'file':str(f.relative_to(original)),'sha256':sha(q)})
 assert (working/'tests/tests.cpp').read_bytes()==(original/'tests/tests.cpp').read_bytes()
 old=(original/'IDEA_SOURCE.md').read_text();new=(working/'IDEA_SOURCE.md').read_text();start=new.index('## S05 optional NNUE validation, 2026-10-25');end=new.index('## Provenance note',start)
 assert (new[:start]+new[end:])==old
 profiles=[]
 for profile,feature in [('release','OFF'),('release','ON'),('asan','ON')]:
  build=r/f'forge_sol_S05_{base}_{profile}_{feature}_final_20261025';data=build/'CMakeFiles/forge_core.dir/flags.make';flags=data.read_text()
  for flag in ('-fno-fast-math','-ffp-contract=off','-DFORGE_NNUE_HIDDEN=256','-march=x86-64-v3','-mtune=znver5'):assert flag in flags
  assert 'FORGE_BUILD_NNUE_VALIDATION' not in flags
  profiles.append({'profile':profile,'feature':feature,'engine_sha256':sha(build/'forge'),'core_flags_sha256':sha(data),'no_validation_macro_on_engine':True})
 rows.append({'base':base,'status':'PASS','unchanged_core_files':core,'tests_cpp_sha256':sha(working/'tests/tests.cpp'),'original_IDEA_notes_exact_after_removing_new_section':True,'selected_net_sha256':sha(working/'src/nnue_weights.inc'),'profiles':profiles})
patch=r/'forge_sol_S05_ctestwire_20261025.patch';allowed=['CMakeLists.txt','IDEA_SOURCE.md','tests/forge_sol_S05_float_parity_20261025.cpp','tests/forge_sol_S05_float_threads_20261025.cpp','tools/forge_sol_S05_float_uci_20261025.py','tools/forge_sol_S05_fmacheck_v3_20261025.py','tools/forge_sol_S05_fmacheck_tests_20261025.py']
assert sorted(re.findall(r'^\+\+\+ b/(.+)$',patch.read_text(),re.M))==sorted(allowed)
header=(p/'01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src/include/forge/nnue.hpp').read_text();missing=[x for x in ('set_exact_int32','exact_int32_available','exact_values','exact_int32') if x not in header]
assert len(missing)==4
(r/'forge_sol_S05_source_identity_20261025.json').write_text(json.dumps({'status':'PASS','rows':rows,'patch_sha256':sha(patch),'only_patch_files':allowed,'historical_A_missing_APIs':missing,'historical_A_scope':'BLOCKED by current float-only API; no backend/stub applied','old_checker_sha256':sha(p/'04_refs/check_nnue_simd_v2_fma_checker.py'),'packer_unchanged_sha256':{name:sha(p/'13_coder/packer_snap_a07f1972'/name) for name in ('pack_candidate.sh','pack_candidate_lib.py')}},indent=2)+'\n')
print('PASS two-base engine/source identity, six profiles, explicit missing historical APIs')

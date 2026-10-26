#!/usr/bin/env python3
"""Finish the preserved OFF proofs; no repetition of sixteen TU comparisons."""
import hashlib,importlib.util,json,pathlib,subprocess
HERE=pathlib.Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    helper=load(HERE/'forge_sol_S08_OFF_preprocess_reuse_20261026.py','off_source_guard');shared=helper.load_shared()
    lexer=load(HERE/'forge_sol_S08_libclang_token_hash_20261026.py','off_final_lexer')
    original=HERE/'forge_sol_S08_OFF_PREPROCESS_NATIVE_20261026/forge_sol_S08_OFF_preprocess_result_20261026.json'
    proof=HERE/'forge_sol_S08_OFF_TOKEN_NATIVE_v2_20261026/forge_sol_S08_OFF_token_reuse_v2_result_20261026.json'
    x=json.loads(proof.read_text());assert x['status']=='FAIL' and x['failure']=='ValueError: OFF profile.cpp is not empty'
    assert len(x['pairs'])==16 and {(r['base'],r['tu']) for r in x['pairs']}=={(name,tu) for name in ('Lprime','B') for tu in helper.TUS}
    mismatches=[]
    for row in x['pairs']:
        if row['raw_byte_identical']:assert row['preprocessing_token_identity']=='PASS_BY_RAW_BYTE_IDENTITY'
        else:
            left,right=row['native_lexer']['baseline'],row['native_lexer']['candidate']
            assert row['preprocessing_token_identity']=='PASS' and (left['sha256'],left['tokens'])==(right['sha256'],right['tokens'])
            assert left['input_bytes']-left['last_token_end_offset']==right['input_bytes']-right['last_token_end_offset']==1
            mismatches.append({'base':row['base'],'tu':row['tu'],'token_sha256':left['sha256'],'tokens':left['tokens'],'nonfatal_parse_diagnostics_each':left['nonfatal_parse_diagnostics']})
    assert len(mismatches)==2
    for name,base in [('Lprime',helper.LP),('B',helper.B)]:assert shared.snapshot(base)==x['source_before'][name]
    freeze=json.loads(helper.FREEZE.read_text());assert shared.snapshot(helper.V2)==freeze['source_sha256']
    flags=helper.production_flags()['src/uci.cpp']
    cmd=[str(shared.CXX),*flags,'-I',str(helper.V2/'include'),'-E','-P',str(helper.V2/'src/profile.cpp')]
    empty=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True)
    assert not empty.stderr and empty.stdout==b'       \n'
    zero=lexer.token_hash(empty.stdout);assert zero['tokens']==0
    binaries={
      'Lprime':(HERE/'forge_sol_S08_OFF_build_window1_20261026/build/forge','e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b'),
      'B':(HERE.parent/'S26/forge_sol_S26_NATIVE_B_lock_control_20261026/00_74c4009d86b7/build/forge','55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406')}
    symbols={}
    for name,(path,digest) in binaries.items():
        assert sha(path)==digest
        nm=subprocess.run(['nm','--defined-only','--demangle',str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True)
        assert not nm.stderr and len(nm.stdout.splitlines())>100
        forbidden=[line.decode() for line in nm.stdout.splitlines() if b'forge::prof::' in line or any(token in line for token in (b'set_profiling(',b'profiling_active(',b'profile_snapshot('))]
        assert not forbidden
        symbols[name]={'binary_path':str(path),'sha256':digest,'nm_stdout_sha256':hashlib.sha256(nm.stdout).hexdigest(),'defined_symbol_lines':len(nm.stdout.splitlines()),'profile_symbols':forbidden}
    cmake={}
    for name,base,candidate in [('Lprime',helper.LP,helper.V2),('B',helper.B,original.parent/'B_preprocess_overlay')]:
        assert helper.cmake_off_residue(candidate/'CMakeLists.txt')==(base/'CMakeLists.txt').read_text()
        cmake[name]={'default_OFF':True,'profile_cpp_and_prof_tests_ONLY_in_ON_blocks':True,'unguarded_residue_byte_identical':True}
    result={'status':'PASS_PREPROCESSED_TOKEN_IDENTITY_AND_OFF_REUSE_SUPPORT','original_raw_FAIL_receipt_sha256':sha(original),'sixteen_pair_receipt_still_FAIL_sha256':sha(proof),'reason_sixteen_pair_overall_failed':'extra zero-BYTES assumption; actual guarded profile.cpp emits seven spaces and newline, zero lexical tokens','raw_byte_identical_pairs':14,'raw_byte_mismatch_lexically_identical_pairs':mismatches,'profile_cpp_OFF_raw_bytes':len(empty.stdout),'profile_cpp_OFF_raw_sha256':hashlib.sha256(empty.stdout).hexdigest(),'profile_cpp_OFF_lexical_tokens':zero['tokens'],'libclang_version':zero['libclang_version'],'libclang_sha256':zero['libclang_sha256'],'diagnostics_scope':'Clang parsing GCC-preprocessed standard-library tokens reports56nonfatal diagnostics per UCI input; this is NOT a Clang compile pass. Complete token range reaches final nonwhitespace byte; kind+complete-spelling hash agrees.','original_Lprime_B_unchanged':True,'v2_source_unchanged':True,'cmake':cmake,'canonical_OFF_symbol_checks':symbols,'new_v2_OFF_binary_built':False,'B_ON_native_qualified':False,'no_speed_or_strength_claim':True}
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()

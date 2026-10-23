#!/usr/bin/env python3
"""Audit only: independently read sealed corrected Linux qualification evidence."""
from pathlib import Path
import datetime, hashlib, json, os, re, shutil, stat, subprocess, xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
REPO=Path('/workspace/dwqww')
BASE=Path('/workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-repaired-harness-attempt1')
EVIDENCE=BASE/'evidence'
OWNER=Path('/workspace/forge-nnue-handoff-20261023/linux-final-net-repaired-harness-run-attempt1')
OLD=Path('/workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-attempt1')
CLEAN='6e9622fd5be18e0155fc3ed5fcf6c4586705cca6'
TEST='f4a1ed6be3921a024e0d876cac2433153a96c66c'
BASELINE='1ab50b2dd64d9b2f752f7f1285f6968cad2fd792'
NET='a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7'
TEST_SHA='6dec8511d6107511cae182dc6169122b48b41e00c5033738f8b04ab027441dce'
MARKER='Controlled null cutoff: prepared 1 tries 1 cutoffs 1 nodes 2 score 0 restored 1'


def sha(data):return hashlib.sha256(data).hexdigest()
def load(path):return json.loads(path.read_text())
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def record(path):
    s=path.lstat();assert stat.S_ISREG(s.st_mode),str(path)
    data=path.read_bytes()
    return {'sha256':sha(data),'bytes':len(data),'mode':stat.S_IMODE(s.st_mode)}
def verify_record(rec):
    got=record(Path(rec['path']))
    assert all(got[k]==rec[k] for k in ('sha256','bytes','mode')),rec['path']
    return got

def inventory():
    roots={'owner':OWNER,'evidence':EVIDENCE,'source':BASE/'source','release-build':BASE/'build-release','asan-build':BASE/'build-asan-ubsan'}
    result={}
    for label,root in roots.items():
        for parent,dirs,files in os.walk(root,followlinks=False):
            assert all(not (Path(parent)/n).is_symlink() for n in dirs)
            for name in files:
                p=Path(parent)/name
                result[label+'/'+p.relative_to(root).as_posix()]=record(p)
    return result

def gitblob(commit,path):
    return subprocess.check_output(['git','cat-file','blob',commit+':'+path],cwd=REPO)

def main():
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert sha((OWNER/'FINAL-CLOSED.json').read_bytes())=='f95f3e631afe121c407bd04e906c119747c45e5528e013ce4834858ac551f55e'
    owner=load(OWNER/'FINAL-CLOSED.json')
    assert owner['actual_tool_session_id']==10660 and owner['actual_tool_exit_code']==0
    verify_record(owner['actual_tool_receipt'])
    actual=load(Path(owner['actual_tool_receipt']['path']))
    assert actual['captured_after_actual_completion'] and actual['tool_result']['exit_code']==0
    assert actual['tool_result']['output']=='CORRECTED_LINUX_RUNNER_RC 0\n'
    before=inventory();save('INPUT-INVENTORY-BEFORE.json',before)
    for key in ('source_comparison','source_freeze_manifest','runner_result','first_bench_freeze'):
        verify_record(owner[key])
    wrapper_result=load(OWNER/'runner.result.json')
    assert wrapper_result['returncode']==0
    assert (OWNER/'runner.stderr').stat().st_size==0
    bound=load(OWNER/'BOUND-INVOCATION.json')
    for rec in bound['identities']:
        assert record(Path(rec['path']))['sha256']==rec['sha256'],rec['path']
    assert sha((OWNER/'run_bound_trial.py').read_bytes())==bound['wrapper_sha256']
    expected_source=load(OWNER/'EXPECTED-SOURCE.json')
    assert sha((OWNER/'EXPECTED-SOURCE.json').read_bytes())==bound['expected_source_manifest_sha256']
    freeze=load(EVIDENCE/'source-freeze.json')
    assert freeze['clean_engine_source_commit']==CLEAN and freeze['test_harness_commit']==TEST
    assert freeze['test_harness_sha256']==TEST_SHA and freeze['chosen_include_sha256']==NET
    assert freeze['hidden']==128 and freeze['residual'] is True
    source=Path(freeze['source'])
    source_paths={p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
    assert len(source_paths)==74 and source_paths==set(freeze['source_sha256'])
    assert set(source_paths)==set(freeze['baseline_sha256'])
    source_report={}
    baseline_changes=[];clean_changes=[]
    for name in sorted(source_paths):
        actual_bytes=(source/name).read_bytes()
        baseline=gitblob(BASELINE,name)
        clean=gitblob(CLEAN,name)
        chosen=gitblob(TEST,name) if name=='tests/tests.cpp' else clean
        assert actual_bytes==chosen,name
        assert sha(actual_bytes)==freeze['source_sha256'][name],name
        assert sha(baseline)==freeze['baseline_sha256'][name],name
        if actual_bytes!=baseline:baseline_changes.append(name)
        if actual_bytes!=clean:clean_changes.append(name)
        source_report[name]={'sha256':sha(actual_bytes),'matched_commit':TEST if name=='tests/tests.cpp' else CLEAN,'baseline_sha256':sha(baseline),'clean_sha256':sha(clean)}
    assert clean_changes==['tests/tests.cpp']
    assert baseline_changes==['src/nnue_weights.inc','tests/tests.cpp']
    assert sha((source/'src/nnue_weights.inc').read_bytes())==NET
    assert sha((source/'tests/tests.cpp').read_bytes())==TEST_SHA
    save('EXACT-GIT-SOURCE-PROOF.json',source_report)
    # Raw command/result receipts are actual completed subcommands, not planned commands.
    receipts={}
    for path in sorted(EVIDENCE.glob('*.result.json')):
        rec=load(path)
        assert rec['returncode']==0,path.name
        assert rec['owned_process_reaped'] and not rec['owned_group_killed_on_exception']
        assert rec['exception'] is None
        receipts[path.name]=rec
    save('ACTUAL-SUBCOMMAND-RECEIPTS.json',receipts)
    profiles={};diagnostics=[]
    for name in ('release','asan-ubsan'):
        build=BASE/('build-'+name)
        build_manifest=load(EVIDENCE/(name+'-build-files.json'))
        for rec in build_manifest.values():verify_record(rec)
        command=load(EVIDENCE/(name+'-ctest.command.json'))
        assert '--parallel' in command['argv'] and command['argv'][command['argv'].index('--parallel')+1]=='1'
        assert command['environment_overrides']['ASAN_OPTIONS']=='detect_leaks=1:halt_on_error=1:abort_on_error=1'
        assert command['environment_overrides']['UBSAN_OPTIONS']=='halt_on_error=1:print_stacktrace=1'
        root=ET.parse(build/'ctest-junit.xml').getroot()
        assert root.tag=='testsuite' and root.attrib['tests']=='14'
        assert all(root.attrib[k]=='0' for k in ('failures','disabled','skipped'))
        cases=root.findall('testcase');assert len(cases)==14
        names=[case.attrib['name'] for case in cases];assert len(set(names))==14
        for case in cases:
            assert case.attrib['status']=='run' and not case.findall('failure') and not case.findall('error') and not case.findall('skipped')
        discovery=load(EVIDENCE/(name+'-ctest-discovery.stdout'))
        assert [t['name'] for t in discovery['tests']]==names
        text=(build/'Testing/Temporary/LastTest.log').read_text()
        last_names=re.findall(r'^\d+/14 Testing: (.+)$',text,re.M)
        assert last_names==names and text.count('Test Passed.')==14 and 'Test Failed.' not in text
        assert MARKER in text
        stdout=(EVIDENCE/(name+'-ctest.stdout')).read_text()
        assert '100% tests passed, 0 tests failed out of 14' in stdout
        assert len(re.findall(r'^\s*\d+/14 Test.*Passed',stdout,re.M))==14
        assert (EVIDENCE/(name+'-ctest.stderr')).stat().st_size==0
        flags=(build/'CMakeFiles/forge_core.dir/flags.make').read_text()
        link=(build/'CMakeFiles/forge.dir/link.txt').read_text()
        for flag in ['-march=x86-64-v3','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-fno-lto','-std=gnu++20']:
            assert flag in flags,(name,flag)
        assert '/usr/bin/g++-14' in flags and '-ffast-math' not in flags
        if name=='asan-ubsan':
            assert '-fsanitize=address,undefined' in flags and '-fsanitize=address,undefined' in link
        profiles[name]={'tests':names,'ctests_passed':14,'build_manifest_records_verified':len(build_manifest),'junit':record(build/'ctest-junit.xml'),'last_test_log':record(build/'Testing/Temporary/LastTest.log'),'engine':record(build/'forge'),'core':record(build/'libforge_core.a'),'controlled_fixture_marker':MARKER,'sanitizer_compile_and_link_verified':name=='asan-ubsan'}
        for key in ('engine','core','junit','last_test_log'):
            assert profiles[name][key]==verify_record(owner['profiles'][name][key])
        copied=OUT/'raw-profile-logs'/name;copied.mkdir(parents=True)
        for path in [build/'ctest-junit.xml',build/'Testing/Temporary/LastTest.log']:
            shutil.copyfile(path,copied/path.name)
    # Scan all raw stdout/stderr plus untruncated LastTest logs, avoiding compiler-source artifacts.
    pattern=re.compile(r'ERROR:\s*(?:AddressSanitizer|LeakSanitizer)|AddressSanitizer:DEADLYSIGNAL|(?:UndefinedBehaviorSanitizer|LeakSanitizer):|runtime error:|SUMMARY:\s*(?:AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer)',re.I)
    scanned=list(EVIDENCE.glob('*.stdout'))+list(EVIDENCE.glob('*.stderr'))+[BASE/('build-'+p)/'Testing/Temporary/LastTest.log' for p in ('release','asan-ubsan')]
    for path in scanned:
        for n,line in enumerate(path.read_text(errors='replace').splitlines(),1):
            if pattern.search(line):diagnostics.append({'path':str(path),'line':n,'text':line})
    assert not diagnostics,diagnostics
    old_hashes={}
    for name in ('forge','libforge_core.a'):
        new_bytes=(BASE/'build-release'/name).read_bytes();old_bytes=(OLD/'build-release'/name).read_bytes()
        assert new_bytes==old_bytes,name
        old_hashes[name]={'sha256':sha(new_bytes),'bytes':len(new_bytes),'bit_identical':True,'original_profile_path':str(OLD/'build-release'/name)}
    assert load(OLD/'evidence/release-ctest.result.json')['returncode']==8
    old_failed=(OLD/'evidence/release-ctest.stdout').read_text()
    assert 'FAIL: null pruning is active with non-pawn material' in old_failed
    assert '93% tests passed, 1 tests failed out of 14' in old_failed
    first=load(EVIDENCE/'FIRST-BENCH11.json')
    verify_record(first['engine']);verify_record(first['stdout'])
    assert first['nodes']==348974 and first['chosen_include_sha256']==NET
    assert first['source_manifest_sha256']==sha((EVIDENCE/'source-freeze.json').read_bytes())
    benches=[]
    for number in (1,2):
        label='release-bench11-'+str(number)
        cmd=load(EVIDENCE/(label+'.command.json'))
        assert cmd['argv']==[str(BASE/'build-release/forge')]
        verify_record(cmd['stdin'])
        assert (EVIDENCE/(label+'.stdin')).read_bytes()==b'bench 11\nquit\n'
        raw=(EVIDENCE/(label+'.stdout')).read_text()
        m=re.fullmatch(r'info string bench depth 11 nodes (\d+) time (\d+) nps (\d+)\n',raw)
        assert m and int(m[1])==348974
        assert (EVIDENCE/(label+'.stderr')).stat().st_size==0
        benches.append({'nodes':int(m[1]),'raw_time_ms_observed_not_performance_claim':int(m[2]),'raw_nps_observed_not_performance_claim':int(m[3]),'stdout':record(EVIDENCE/(label+'.stdout'))})
    assert record(BASE/'build-release/forge')['sha256']==first['engine']['sha256']
    # Retain exact original evidence metadata/raw receipts; no duplicate binaries or object files.
    for label,root in [('owner',OWNER),('evidence',EVIDENCE)]:
        destination=OUT/'raw-evidence'/label
        destination.mkdir(parents=True)
        for path in root.iterdir():
            if path.is_file():shutil.copyfile(path,destination/path.name)
    after=inventory();save('INPUT-INVENTORY-AFTER.json',after)
    assert before==after,'sealed producer inputs changed during review'
    result={'status':'PASS','started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'producer_actual_session':10660,'producer_actual_exit_code':0,'clean_source_commit':CLEAN,'authorized_test_commit':TEST,'test_sha256':TEST_SHA,'network_sha256':NET,'source_files_verified':74,'source_changes_from_clean_net_only':clean_changes,'source_changes_from_baseline':baseline_changes,'profiles':profiles,'actual_subcommand_receipts_verified':len(receipts),'release_engine_core_identity_to_failed_original_profile':old_hashes,'original_release_13_of_14_failure_preserved':True,'benchmarks':benches,'sanitizer_diagnostic_hits':diagnostics,'diagnostic_files_scanned':len(scanned),'producer_input_files_unchanged':len(before),'speed_conclusion':None,'elo_conclusion':None,'scope':'Independent read-only exact-source/identity and closed actual-result audit. No builds, tests, searches, model evaluation or Git writes.'}
    save('RESULT.json',result)
    print(json.dumps({'status':'PASS','source_files':74,'release_tests':14,'asan_ubsan_tests':14,'bench_nodes':[b['nodes'] for b in benches],'actual_subcommands':len(receipts),'sanitizer_diagnostics':len(diagnostics),'producer_input_files_unchanged':len(before)},indent=2))

if __name__=='__main__':main()

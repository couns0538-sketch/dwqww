"""Offline guard tests: actual native formats plus clearly derived inert records.

Nothing here builds/runs an engine. Source archives/CTest/LastTest are actual
fc51/61f5 captures. Future generic flags/cache and process records are DERIVED
unit data in the collector's schema; artifact bytes are inert, not executables.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
FIX=ROOT/'build-fixtures/actual'
PACKAGE=REPO/'.github/hosted-runtime-psqt-performance'
TARGET=Path(os.environ.get('BUILD_EVIDENCE_TEST_MODULE',str(PACKAGE/'build_evidence.py')))
spec=importlib.util.spec_from_file_location('psqt_build_evidence_under_test',TARGET)
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
BASE='fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b'
CANDIDATE='61f598056572dfade6994af8ad2e38817cd28aa3'
EXPECTED_BASE=('forge_tests','forge_correction_history_tests','forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests','match_tool_tests','windows_validation_tests','uci_regression','ponder_regression','ownbook_regression')
EXPECTED_CAND=(*EXPECTED_BASE[:2],'forge_runtime_psqt_tests',*EXPECTED_BASE[2:])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def manifest(root):dump(root/'build-evidence-SHA256.json',{p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='build-evidence-SHA256.json'})
def stage(root,name,command,stdout=None):
    out=root/(name+'.stdout');err=root/(name+'.stderr')
    if stdout is not None:out.write_bytes(stdout)
    if not out.exists():out.write_bytes(b'DERIVED INERT successful stage fixture only\n')
    err.write_bytes(b'')
    dump(root/(name+'-command.json'),{'label':name,'command':command,'cwd':'/DERIVED-INERT-UNIT-FIXTURE','timeout_seconds':1,'status':'passed','exit_code':0,'returncode_before_verdict':0,'cleanup_attempted':False,'owned_group_empty_before_verdict':True,'owned_group_empty_after_cleanup':True,'stdout_sha256_before_verdict':sha(out),'stderr_sha256_before_verdict':sha(err),'stdout_sha256':sha(out),'stderr_sha256':sha(err),'elapsed_seconds':0})
def restage_hash(root,name):
    p=root/(name+'-command.json');d=json.loads(p.read_text())
    for stream in ('stdout','stderr'):d[stream+'_sha256']=sha(root/(name+'.'+stream));d[stream+'_sha256_before_verdict']=d[stream+'_sha256']
    dump(p,d)
def create_fixture(root):
    (root/'source').mkdir();(root/'artifacts').mkdir()
    (root/'collector.stdout').write_bytes(b'');(root/'collector.stderr').write_bytes(b'');(root/'collector-exit-code.txt').write_text('0\n')
    cfg={'baseline_sha':BASE,'candidate_sha':CANDIDATE}
    for label in ('baseline','candidate'):
        actual=FIX/label;archive=root/'source'/(label+'.tar');shutil.copy2(actual/'source.tar',archive)
        for source,target in [('ctest.stdout',label+'-ctest.stdout'),('LastTest.log',label+'-LastTest.log')]:shutil.copy2(actual/source,root/target)
        cache=(actual/'CMakeCache.txt').read_text().splitlines();wanted={'CMAKE_BUILD_TYPE':'Release','CMAKE_CXX_FLAGS':'','CMAKE_CXX_FLAGS_RELEASE':guard.RELEASE_FLAGS,'CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF','FORGE_NATIVE':'OFF','CMAKE_CXX_COMPILER':'/usr/bin/g++-14'};seen=set();lines=[]
        for line in cache:
            key=line.split(':',1)[0]
            if key in wanted and ':' in line and '=' in line:line=line.split('=',1)[0]+'='+wanted[key];seen.add(key)
            lines.append(line)
        for key in wanted.keys()-seen:lines.append(key+':STRING='+wanted[key])
        (root/(label+'-CMakeCache.txt')).write_text('\n'.join(lines)+'\n')
        commands=json.loads((actual/'compile_commands.json').read_text())
        for row in commands:row['command']=row['command'].replace('-mtune=znver5','-mtune=generic')
        dump(root/(label+'-compile-commands.json'),commands)
        artifacts=root/'artifacts'/label;artifacts.mkdir();(artifacts/'forge').write_bytes((label+' INERT UNIT ARTIFACT NOT A PROGRAM\n').encode());(artifacts/'forge').chmod(0o755);(artifacts/'libforge_core.a').write_bytes((label+' INERT UNIT CORE\n').encode())
        inventory=guard.source_inventory(archive,cfg[label+'_sha'])
        dump(root/(label+'-build-provenance.json'),{'source_commit':cfg[label+'_sha'],'exported_source_sha256':inventory,'built_artifacts_sha256':{name:sha(artifacts/name) for name in ('forge','libforge_core.a')},'last_test_log_sha256':sha(root/(label+'-LastTest.log')),'source_tar_sha256':sha(archive)})
        source_name='source-'+label;(root/(source_name+'.stderr')).write_bytes(b'')
        dump(root/(source_name+'-command.json'),{'label':source_name,'command':['git','archive',cfg[label+'_sha'],'CMakeLists.txt','LICENSE','src','include','tests','bench','tools'],'cwd':'/DERIVED-INERT-UNIT-FIXTURE','timeout_seconds':1,'status':'passed','exit_code':0,'returncode_before_verdict':0,'cleanup_attempted':False,'owned_group_empty_before_verdict':True,'owned_group_empty_after_cleanup':True,'stdout_sha256_before_verdict':sha(archive),'stderr_sha256_before_verdict':sha(root/(source_name+'.stderr')),'stdout_sha256':sha(archive),'stderr_sha256':sha(root/(source_name+'.stderr')),'elapsed_seconds':0})
        for name in ('configure','build','ctest','core-sections'):
            stdout=None if name!='core-sections' else b'\nDERIVED INERT UNIT SECTION FIXTURE\nfile format elf64-x86-64\nSections:\nIdx Name Size\n  0 .text 00000010\n'
            stage(root,label+'-'+name,['INERT-unit-fixture-not-executed',name],stdout)
    shutil.copy2(FIX/'compiler.stdout',root/'compiler.stdout');stage(root,'compiler',['g++-14','--version'])
    dump(root/'artifacts-SHA256.json',{p.relative_to(root/'artifacts').as_posix():sha(p) for p in (root/'artifacts').rglob('*') if p.is_file()});manifest(root)
    return cfg

class BuildEvidenceOffline(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'build-fixtures',prefix='inert-case-');self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.cfg=create_fixture(self.root)
    def verify(self):
        with patch.object(subprocess,'Popen',side_effect=AssertionError('Guard must not create samples/processes')):
            return guard.verify_build_evidence(self.root,self.cfg,self.root/'artifacts/baseline/forge',self.root/'artifacts/candidate/forge')
    def test_actual_formats_require_exact_ten_and_eleven_named_suites(self):
        self.assertEqual(guard.BASELINE_TESTS,EXPECTED_BASE);self.assertEqual(guard.CANDIDATE_TESTS,EXPECTED_CAND)
        result=self.verify()
        for name in ('source/baseline.tar','source/candidate.tar','baseline-ctest.stdout','candidate-ctest.stdout','candidate-core-sections.stdout','build-evidence-SHA256.json'):self.assertIn(self.root/name,result)
    def test_missing_required_paths_fail_before_any_process(self):
        for name in ('source/candidate.tar','candidate-CMakeCache.txt','candidate-compile-commands.json','candidate-core-sections.stdout','source-candidate-command.json','collector-exit-code.txt','build-evidence-SHA256.json'):
            p=self.root/name;raw=p.read_bytes();p.unlink()
            with self.subTest(path=name),self.assertRaises((ValueError,OSError)):self.verify()
            p.write_bytes(raw)
    def test_wrong_source_pin_cannot_relabel_genuine_archive(self):
        self.cfg['candidate_sha']='0'*40
        with self.assertRaisesRegex(ValueError,'commit identity'):self.verify()
    def test_swapped_core_rejects_even_with_new_artifact_manifest(self):
        p=self.root/'artifacts/candidate/libforge_core.a';p.write_bytes((self.root/'artifacts/baseline/libforge_core.a').read_bytes());art=json.loads((self.root/'artifacts-SHA256.json').read_text());art['candidate/libforge_core.a']=sha(p);dump(self.root/'artifacts-SHA256.json',art);manifest(self.root)
        with self.assertRaisesRegex(ValueError,'Executable/core provenance'):self.verify()
    def test_forbidden_compile_flags_fail_before_any_process(self):
        p=self.root/'candidate-compile-commands.json';original=p.read_bytes()
        for flag in ('-flto','-ffast-math','-march=native','-mtune=znver5'):
            d=json.loads(original);d[0]['command']+=' '+flag;dump(p,d);manifest(self.root)
            with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,'compile command flags'):self.verify()
        p.write_bytes(original)
    def test_candidate_ten_cannot_stand_for_eleven(self):
        (self.root/'candidate-ctest.stdout').write_bytes((self.root/'baseline-ctest.stdout').read_bytes());restage_hash(self.root,'candidate-ctest');manifest(self.root)
        with self.assertRaisesRegex(ValueError,'CTest suite'):self.verify()
    def test_replaced_named_test_is_not_equivalent_count(self):
        p=self.root/'candidate-ctest.stdout';p.write_text(p.read_text().replace('forge_runtime_psqt_tests','an_unexecuted_test'));restage_hash(self.root,'candidate-ctest');manifest(self.root)
        with self.assertRaisesRegex(ValueError,'CTest suite'):self.verify()
    def test_actual_core_lto_sections_reject_even_when_published_hashes_match(self):
        p=self.root/'candidate-core-sections.stdout';p.write_bytes(p.read_bytes()+b' 12 .gnu.lto_runtime_psqt.1234 00000400\n');restage_hash(self.root,'candidate-core-sections');manifest(self.root)
        with self.assertRaisesRegex(ValueError,'LTO|lto'):self.verify()
    def test_failed_or_orphaned_stage_facts_reject_despite_exit_zero(self):
        for record in ('candidate-build-command.json','source-candidate-command.json'):
            p=self.root/record;original=p.read_bytes()
            for key,value in [('status','failed'),('returncode_before_verdict',None),('owned_group_empty_before_verdict',False),('owned_group_empty_after_cleanup',False),('error','DERIVED UNIT failure'),('cleanup_error','DERIVED UNIT cleanup failure')]:
                d=json.loads(original);d[key]=value;dump(p,d);manifest(self.root)
                with self.subTest(record=record,field=key),self.assertRaises(ValueError):self.verify()
            p.write_bytes(original)
    def test_published_evidence_hash_change_fails(self):
        p=self.root/'candidate-CMakeCache.txt';p.write_text(p.read_text()+'# changed after publication\n')
        with self.assertRaisesRegex(ValueError,'Published build evidence hash'):self.verify()

if __name__=='__main__':unittest.main(verbosity=2)

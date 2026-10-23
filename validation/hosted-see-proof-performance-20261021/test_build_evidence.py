"""Offline build-schema guard tests derived from the qualified21 twelve-test suite.

Baseline TAR is the authentic frozen23 source1d3ed25. The dummy24 candidate PAX
reuses exactly those SAME77 source-file bytes; it is DERIVED UNIT SCHEMA, never
actual24 source or qualification. Both fourteen-test CTest/LastTest records,
future generic flags/cache, process facts and inert artifact bytes are DERIVED
unit fixtures. Original23 Release cache/compile records and the historical
GCC14 version fixture are read only. Nothing builds or runs an engine here.
"""
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
FIX=REPO/'validation/hosted-runtime-psqt-performance-20261020/build-fixtures/actual'
PACKAGE=REPO/'.github/hosted-see-proof-performance'
TARGET=Path(os.environ.get('BUILD_EVIDENCE_TEST_MODULE',str(PACKAGE/'build_evidence.py')))
spec=importlib.util.spec_from_file_location('see_proof_build_evidence_under_test',TARGET)
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
ACTUAL23=REPO/'validation/tt-refresh-native-20261021'
BASE='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
CANDIDATE='0000000000000000000000000000000000000024'
EXPECTED_BASE=('forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests','forge_pawn_span_tests','forge_nearest_pawn_tests','forge_pv_metadata_tests','forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests','match_tool_tests','windows_validation_tests','uci_regression','ponder_regression','ownbook_regression')
EXPECTED_CAND=EXPECTED_BASE
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
        actual=ACTUAL23/'frozen-release-attempt1';source_tar=ACTUAL23/'frozen-source-1d3ed25.tar';archive=root/'source'/(label+'.tar');shutil.copy2(source_tar,archive)
        if label=='candidate':
            # DERIVED schema only: same authentic23 file bytes, dummy24 PAX; never actual24.
            with tarfile.open(source_tar) as original,tarfile.open(archive,'w',format=tarfile.PAX_FORMAT,pax_headers={'comment':CANDIDATE}) as derived:
                for member in original:derived.addfile(member,original.extractfile(member) if member.isfile() else None)
        names=EXPECTED_BASE if label=='baseline' else EXPECTED_CAND
        (root/(label+'-ctest.stdout')).write_text('DERIVED UNIT named-CTest schema, never actual24 execution\n'+''.join(f'{i}/{len(names)} Test #{i}: {name} .... Passed 0.01 sec\n' for i,name in enumerate(names,1))+f'100% tests passed, 0 tests failed out of {len(names)}\n')
        (root/(label+'-LastTest.log')).write_text('DERIVED UNIT LastTest schema, never actual24 execution\n'+''.join('Testing: '+name+'\nTest Passed.\n' for name in names))
        cache=(actual/'original-CMakeCache.txt').read_text().splitlines();wanted={'CMAKE_BUILD_TYPE':'Release','CMAKE_CXX_FLAGS':'','CMAKE_CXX_FLAGS_RELEASE':guard.RELEASE_FLAGS,'CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF','FORGE_NATIVE':'OFF','CMAKE_CXX_COMPILER':'/usr/bin/g++-14'};seen=set();lines=[]
        for line in cache:
            key=line.split(':',1)[0]
            if key in wanted and ':' in line and '=' in line:line=line.split('=',1)[0]+'='+wanted[key];seen.add(key)
            lines.append(line)
        for key in wanted.keys()-seen:lines.append(key+':STRING='+wanted[key])
        (root/(label+'-CMakeCache.txt')).write_text('\n'.join(lines)+'\n')
        commands=json.loads((actual/'original-compile_commands.json').read_text())
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
        self.temp=tempfile.TemporaryDirectory(dir=ROOT,prefix='inert-case-');self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.cfg=create_fixture(self.root)
    def verify(self):
        with patch.object(subprocess,'Popen',side_effect=AssertionError('Guard must not create samples/processes')):
            return guard.verify_build_evidence(self.root,self.cfg,self.root/'artifacts/baseline/forge',self.root/'artifacts/candidate/forge')
    def test_derived_formats_require_exact_fourteen_named_suites_both_roles(self):
        self.assertEqual(guard.BASELINE_TESTS,EXPECTED_BASE);self.assertEqual(guard.CANDIDATE_TESTS,EXPECTED_CAND)
        self.assertEqual(guard.SOURCE_FILE_COUNTS,{'baseline':77,'candidate':77});self.assertEqual(EXPECTED_BASE[5],'forge_pv_metadata_tests')
        result=self.verify()
        for name in ('source/baseline.tar','source/candidate.tar','baseline-ctest.stdout','candidate-ctest.stdout','candidate-core-sections.stdout','build-evidence-SHA256.json'):self.assertIn(self.root/name,result)
    def test_extra_source_file_rejected_despite_consistent_provenance(self):
        archive=self.root/'source/candidate.tar'
        original=archive.read_bytes()
        with tarfile.open(fileobj=io.BytesIO(original)) as before,tarfile.open(archive,'w',format=tarfile.PAX_FORMAT,pax_headers={'comment':CANDIDATE}) as after:
            for member in before:after.addfile(member,before.extractfile(member) if member.isfile() else None)
            data=b'DERIVED extra';extra=tarfile.TarInfo('tests/extra-unit-only.cpp');extra.size=len(data);after.addfile(extra,io.BytesIO(data))
        prov=self.root/'candidate-build-provenance.json';d=json.loads(prov.read_text());d['source_tar_sha256']=sha(archive);d['exported_source_sha256']=guard.source_inventory(archive,CANDIDATE);dump(prov,d)
        record=self.root/'source-candidate-command.json';d=json.loads(record.read_text());d['stdout_sha256']=d['stdout_sha256_before_verdict']=sha(archive);dump(record,d);manifest(self.root)
        with self.assertRaisesRegex(ValueError,'source file count'):self.verify()
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
    def test_candidate_thirteen_cannot_stand_for_fourteen(self):
        names=tuple(name for name in EXPECTED_CAND if name!='forge_pv_metadata_tests')
        self.assertEqual(len(names),13)
        (self.root/'candidate-ctest.stdout').write_text('DERIVED UNIT missing-PV thirteen-test schema, never actual24 execution\n'+''.join(f'{i}/{len(names)} Test #{i}: {name} .... Passed 0.01 sec\n' for i,name in enumerate(names,1))+f'100% tests passed, 0 tests failed out of {len(names)}\n')
        restage_hash(self.root,'candidate-ctest');manifest(self.root)
        with self.assertRaisesRegex(ValueError,'CTest suite'):self.verify()
    def test_replaced_named_test_is_not_equivalent_count(self):
        p=self.root/'candidate-ctest.stdout';p.write_text(p.read_text().replace('forge_nearest_pawn_tests','an_unexecuted_test'));restage_hash(self.root,'candidate-ctest');manifest(self.root)
        with self.assertRaisesRegex(ValueError,'CTest suite'):self.verify()
    def test_nearest_fifth_cannot_move_to_another_position(self):
        p=self.root/'candidate-ctest.stdout';text=p.read_text()
        # Swap names without changing the count or original ordinal positions.
        text=text.replace('forge_nearest_pawn_tests','TEMP_NEAREST').replace('forge_tt_tests','forge_nearest_pawn_tests').replace('TEMP_NEAREST','forge_tt_tests')
        p.write_text(text);restage_hash(self.root,'candidate-ctest');manifest(self.root)
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

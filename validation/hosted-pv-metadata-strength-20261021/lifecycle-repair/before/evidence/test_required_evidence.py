"""Preflight integration tests using actual archive/log schemas; never execute engines."""
import copy
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
PACKAGE=REPO/'.github/hosted-pv-metadata-strength'
spec=importlib.util.spec_from_file_location('required_evidence_runner',PACKAGE/'run_hosted.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
ACTUAL=ROOT/'provenance-fixtures/actual17'
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')

def create_fixture(repo):
    """Source archives/CTest/LastTest/cache/command records have real observed formats.

    Artifact payloads and successful stage commands are explicit inert unit data.
    Candidate command paths/flags are derived for the future hosted configuration;
    no fixture claims those command records came from a completed hosted22 build.
    """
    package=repo/'.github/hosted-pv-metadata-strength';package.mkdir(parents=True)
    (package/'match').mkdir();shutil.copyfile(PACKAGE/'match/pgn_stats.py',package/'match/pgn_stats.py')
    if (PACKAGE/'build_evidence.py').exists():shutil.copyfile(PACKAGE/'build_evidence.py',package/'build_evidence.py')
    (repo/'tools/match').mkdir(parents=True);shutil.copyfile(REPO/'tools/match/windows_validate.py',repo/'tools/match/windows_validate.py')
    (repo/'.github/workflows').mkdir();workflow=repo/'.github/workflows/forge-hosted-pv-metadata-strength.yml';workflow.write_text('on: []\n# INERT UNIT FIXTURE\n')
    results=repo/'hosted-results';results.mkdir();(results/'source').mkdir();(results/'artifacts/runner').mkdir(parents=True)
    (results/'collector.stdout').write_bytes(b'');(results/'collector.stderr').write_bytes(b'');(results/'collector-exit-code.txt').write_text('0\n')
    cfg=json.loads((PACKAGE/'protocol.json').read_text());cfg.update(baseline_sha='2e151d019bc58dff2ab4e76e99ef99516af8d222',candidate_sha='0000000000000000000000000000000000000022',correctness_evidence_sha256={'proof.json':hashlib.sha256(b'actual unit proof bytes\n').hexdigest()},workflow_sha256=digest(workflow));(repo/'proof.json').write_bytes(b'actual unit proof bytes\n');dump(package/'protocol.json',cfg)
    for label,source,ctest,last in [
        ('baseline',ROOT/'provenance-fixtures/derived21-22/baseline.tar',ROOT/'provenance-fixtures/derived21-22/baseline-ctest.stdout',ROOT/'provenance-fixtures/derived21-22/baseline-LastTest.log'),
        ('candidate',ROOT/'provenance-fixtures/derived21-22/candidate.tar',ROOT/'provenance-fixtures/derived21-22/candidate-ctest.stdout',ROOT/'provenance-fixtures/derived21-22/candidate-LastTest.log')]:
        shutil.copyfile(source,results/f'source/{label}.tar');shutil.copyfile(ctest,results/f'{label}-ctest.stdout');(results/f'{label}-ctest.stderr').write_bytes(b'');shutil.copyfile(last,results/f'{label}-LastTest.log')
        shutil.copyfile(ACTUAL/'candidate-CMakeCache.txt',results/f'{label}-CMakeCache.txt');shutil.copyfile(ACTUAL/'candidate-compile-commands.json',results/f'{label}-compile-commands.json')
        artifacts=results/'artifacts'/label;artifacts.mkdir();(artifacts/'forge').write_bytes((label+' INERT NOT A PROGRAM\n').encode());(artifacts/'libforge_core.a').write_bytes((label+' INERT CORE\n').encode())
        with tarfile.open(source) as archive:inventory={m.name:hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in archive if m.isfile()}
        observed_keys=set(json.loads((ACTUAL/'candidate-build-provenance.json').read_text()))
        provenance={'source_commit':cfg[label+'_sha'],'exported_source_sha256':inventory,'built_artifacts_sha256':{name:digest(artifacts/name) for name in ('forge','libforge_core.a')},'last_test_log_sha256':digest(results/f'{label}-LastTest.log'),'source_tar_sha256':digest(results/f'source/{label}.tar')};assert set(provenance)==observed_keys, 'Fixture sourceprovenancekeys must matchactual17collector'
        dump(results/f'{label}-build-provenance.json',provenance)
        for stage in ('configure','build','ctest'):
            if stage!='ctest':(results/f'{label}-{stage}.stdout').write_text('Explicit synthetic successful stage output; unit fixture only\n');(results/f'{label}-{stage}.stderr').write_bytes(b'')
            dump(results/f'{label}-{stage}-command.json',{'label':stage,'command':['unit-fixture-only',stage],'cwd':'unit fixture','timeout_seconds':1,'exit_code':0,'elapsed_seconds':0,'stdout_sha256':digest(results/f'{label}-{stage}.stdout'),'stderr_sha256':digest(results/f'{label}-{stage}.stderr')})
    shutil.copyfile(ACTUAL/'source/fastchess.tar',results/'source/fastchess.tar');(results/'artifacts/runner/fastchess').write_bytes(b'INERT FASTCHESS NOT A PROGRAM\n')
    dump(results/'fastchess-build-provenance.json',{'source_commit':cfg['fastchess_sha'],'source_tar_sha256':digest(results/'source/fastchess.tar'),'built_artifacts_sha256':{'fastchess':digest(results/'artifacts/runner/fastchess')}})
    shutil.copyfile(ACTUAL/'compiler.stdout',results/'compiler.stdout');(results/'compiler.stderr').write_bytes(b'')
    for prefix in ('compiler','fastchess-build'):
        if prefix!='compiler':(results/(prefix+'.stdout')).write_text('Explicit synthetic successful build; unit fixture only\n');(results/(prefix+'.stderr')).write_bytes(b'')
        dump(results/(prefix+'-command.json'),{'command':['unit-fixture-only',prefix],'exit_code':0,'stdout_sha256':digest(results/(prefix+'.stdout')),'stderr_sha256':digest(results/(prefix+'.stderr'))})
    # Execute bits model hosted artifact permissions; these inert bytes are never run.
    for executable in ('baseline/forge','candidate/forge','runner/fastchess'):(results/'artifacts'/executable).chmod(0o755)
    dump(results/'artifacts-SHA256.json',{p.relative_to(results/'artifacts').as_posix():digest(p) for p in (results/'artifacts').rglob('*') if p.is_file()});refresh_manifest(results)
    return cfg,results,package

def refresh_manifest(results):
    dump(results/'build-evidence-SHA256.json',{p.relative_to(results).as_posix():digest(p) for p in sorted(results.rglob('*')) if p.is_file() and p.name!='build-evidence-SHA256.json' and 'strength' not in p.parts})

class ObservedFreeze(BaseException):
    def __init__(self,report):self.report=copy.deepcopy(report)

class RequiredEvidenceBeforeProcesses(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT,prefix='required-evidence-unit-');self.addCleanup(self.temp.cleanup);self.repo=Path(self.temp.name);self.cfg,self.results,self.package=create_fixture(self.repo)

    def freeze(self):
        out=self.results/'strength';shutil.rmtree(out,ignore_errors=True)
        args=['runner','--repo',str(self.repo),'--package',str(self.package),'--baseline',str(self.results/'artifacts/baseline/forge'),'--candidate',str(self.results/'artifacts/candidate/forge'),'--fastchess',str(self.results/'artifacts/runner/fastchess'),'--out',str(out)]
        real_save=runner.save
        def observe(path,value):
            real_save(path,value)
            if path.name=='summary.json':raise ObservedFreeze(value)
        with patch.object(sys,'argv',args),patch.object(runner,'require_launch_protocol'),patch.object(runner,'verify_package_inventory'),patch.object(runner.os,'sched_getaffinity',return_value={0}),patch.object(runner.os,'sched_setaffinity'),patch.object(runner,'host_context',return_value={}),patch.object(runner,'save',side_effect=observe),patch.object(runner.subprocess,'Popen') as popen,patch.object(runner.subprocess,'run') as run:
            try:runner.main()
            except ObservedFreeze as observed:return observed.report
            finally:popen.assert_not_called();run.assert_not_called()
        self.fail('Preflight neither rejected nor reached freeze observation')

    def test_actual_format_positive_binds_all_build_and_proof_bytes(self):
        frozen=self.freeze()['frozen_inputs']
        for path in (self.repo/'proof.json',self.results/'candidate-ctest.stdout',self.results/'candidate-build-command.json',self.results/'build-evidence-SHA256.json'):
            self.assertIn(str(path),frozen)

    def test_nonexecutable_runtime_artifact_rejects_before_processes(self):
        for name in ("baseline/forge","candidate/forge","runner/fastchess"):
            path=self.results/"artifacts"/name;path.chmod(0o644)
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,"executable"):self.freeze()
            path.chmod(0o755)

    def test_missing_initial_proof_rejects_before_processes(self):
        (self.repo/'proof.json').unlink()
        with self.assertRaises((ValueError,OSError)):self.freeze()

    def test_mutated_proof_invalidates_final_acceptance(self):
        frozen=self.freeze()['frozen_inputs'];(self.repo/'proof.json').write_text('changed')
        report={'status':'passed'};runner.ensure_final_inputs(report,frozen)
        self.assertEqual(report['status'],'failed_or_inconclusive_no_acceptance')
        self.assertIn(str(self.repo/'proof.json'),report['final_input_rehash']['mismatches'])

    def test_deleted_proof_invalidates_final_acceptance(self):
        frozen=self.freeze()['frozen_inputs'];(self.repo/'proof.json').unlink();report={'status':'passed'};runner.ensure_final_inputs(report,frozen)
        self.assertEqual(report['status'],'failed_or_inconclusive_no_acceptance')

    def test_missing_required_build_files_do_not_silently_match_empty_glob(self):
        for name in ('source/candidate.tar','candidate-compile-commands.json','candidate-CMakeCache.txt','candidate-ctest.stdout','candidate-build-provenance.json','build-evidence-SHA256.json'):
            path=self.results/name;raw=path.read_bytes();path.unlink()
            with self.subTest(name=name),self.assertRaises((ValueError,OSError)):self.freeze()
            path.write_bytes(raw)

    def test_wrong_source_commit_rejects_even_after_manifest_refresh(self):
        path=self.results/'candidate-build-provenance.json';d=json.loads(path.read_text());d['source_commit']='0'*40;dump(path,d);refresh_manifest(self.results)
        with self.assertRaises(ValueError):self.freeze()

    def test_exported_source_inventory_mismatch_rejects(self):
        path=self.results/'candidate-build-provenance.json';d=json.loads(path.read_text());d['exported_source_sha256']['src/search.cpp']='0'*64;dump(path,d);refresh_manifest(self.results)
        with self.assertRaises(ValueError):self.freeze()

    def test_compiler_flag_change_rejects(self):
        path=self.results/'candidate-compile-commands.json';d=json.loads(path.read_text());d[0]['command']+=' -ffast-math';dump(path,d);refresh_manifest(self.results)
        with self.assertRaises(ValueError):self.freeze()

    def test_cache_native_flag_change_rejects(self):
        path=self.results/'candidate-CMakeCache.txt';path.write_text(path.read_text().replace('FORGE_NATIVE:BOOL=OFF','FORGE_NATIVE:BOOL=ON'));refresh_manifest(self.results)
        with self.assertRaises(ValueError):self.freeze()

    def test_artifact_core_swap_rejects(self):
        (self.results/'artifacts/candidate/libforge_core.a').write_bytes((self.results/'artifacts/baseline/libforge_core.a').read_bytes());refresh_manifest(self.results)
        with self.assertRaises(ValueError):self.freeze()

    def test_candidate_thirteen_test_output_cannot_stand_for_fourteen(self):
        path=self.results/'candidate-ctest.stdout';path.write_bytes((self.results/'baseline-ctest.stdout').read_bytes());d=json.loads((self.results/'candidate-ctest-command.json').read_text());d['stdout_sha256']=digest(path);dump(self.results/'candidate-ctest-command.json',d);refresh_manifest(self.results)
        with self.assertRaises(ValueError):self.freeze()

    def test_named_test_cannot_be_replaced(self):
        path=self.results/'candidate-ctest.stdout';path.write_text(path.read_text().replace('forge_pv_metadata_tests','different_unrun_test'));d=json.loads((self.results/'candidate-ctest-command.json').read_text());d['stdout_sha256']=digest(path);dump(self.results/'candidate-ctest-command.json',d);refresh_manifest(self.results)
        with self.assertRaises(ValueError):self.freeze()

    def test_consistently_rehashed_extra_source_rejected(self):
        archive=self.results/'source/candidate.tar';raw=archive.read_bytes()
        with tarfile.open(fileobj=io.BytesIO(raw)) as source,tarfile.open(archive,'w',format=tarfile.PAX_FORMAT,pax_headers={'comment':self.cfg['candidate_sha']}) as output:
            for member in source:output.addfile(member,source.extractfile(member) if member.isfile() else None)
            data=b'EXTRA INERT UNIT SOURCE';extra=tarfile.TarInfo('tests/unexpected.cpp');extra.size=len(data);output.addfile(extra,io.BytesIO(data))
        path=self.results/'candidate-build-provenance.json';d=json.loads(path.read_text());d['source_tar_sha256']=digest(archive);d['exported_source_sha256']['tests/unexpected.cpp']=hashlib.sha256(data).hexdigest();dump(path,d);refresh_manifest(self.results)
        with self.assertRaisesRegex(ValueError,'source file count'):self.freeze()

    def test_nonzero_ctest_exit_cannot_pass_with_successful_text(self):
        path=self.results/'candidate-ctest-command.json';d=json.loads(path.read_text());d['exit_code']=8;dump(path,d);refresh_manifest(self.results)
        with self.assertRaises(ValueError):self.freeze()

    def test_genuine21_tar_is_not_relabeled_as_frozen20(self):
        cfg=json.loads((self.package/'protocol.json').read_text());cfg['baseline_sha']='fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e';dump(self.package/'protocol.json',cfg)
        path=self.results/'baseline-build-provenance.json';d=json.loads(path.read_text());d['source_commit']=cfg['baseline_sha'];dump(path,d);refresh_manifest(self.results)
        with self.assertRaises(ValueError):self.freeze()

if __name__=='__main__':unittest.main(verbosity=2)

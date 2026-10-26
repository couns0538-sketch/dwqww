import gzip,importlib.util,os,sys,tempfile
from pathlib import Path
import unittest
from unittest import mock
import json,types
spec=importlib.util.spec_from_file_location('pair',Path(__file__).with_name('forge_sol_S09_native_pair_20261026.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PairTests(unittest.TestCase):
    def test_same_path_and_hardlink_arm_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);a=p/'a';a.write_text('exe');b=p/'b';os.link(a,b);c=p/'c';c.write_text('exe')
            for other in (a,b):
                with self.assertRaisesRegex(ValueError,'self-comparison'):m.require_distinct(a,other)
            m.require_distinct(a,c)

    def test_arm_binding_pins_role_artifacts_source_and_closed_build(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);src=p/'source';(src/'src').mkdir(parents=True);(src/'core.cpp').write_text('unit fixture source');weights=src/'src/nnue_weights.inc';weights.write_text('unit fixture weights')
            exe=p/'exe';exe.write_text('unit fixture executable');core=p/'core.a';core.write_text('unit fixture archive')
            source_receipt=p/'source.json';source_receipt.write_text('{"unit_fixture":true}')
            inventory=lambda root:{q.relative_to(root).as_posix():m.sha(q) for q in Path(root).rglob('*') if q.is_file()}
            api=types.SimpleNamespace(BASES={'L':src},BASELINE_SHA=m.sha(source_receipt),inventory=inventory,frozen_baselines=lambda:{'L':{'files':{'src/nnue_weights.inc':m.sha(weights)}}})
            build={'status':'PASS_BUILD_ONLY','source':str(src),'source_unchanged':True,'source_before':inventory(src),'source_after':inventory(src),'weights_file':str(weights),'weights_sha256':m.sha(weights),'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'commands':[{'returncode':0,'leader_reaped':True,'running_group_members_after_close':[],'argv':[]}],'target_artifacts':{'helper':{'path':str(exe),'sha256':m.sha(exe)},'core_archive':{'path':str(core),'sha256':m.sha(core)}}}
            br=p/'build.json';br.write_text(json.dumps(build));harness=Path(__file__).parent/'overlay/tools/nnue/heads_parity.cpp'
            binding={'schema':'forge.S09.native_arm.v1','role':'reference','executable':str(exe),'executable_sha256':m.sha(exe),'source_root':str(src),'artifact_key':'helper','expected_stored_heads':1}
            for key,path in [('core_archive',core),('source_receipt',source_receipt),('build_receipt',br),('harness_source',harness),('weights',weights)]:binding[key]=str(path);binding[key+'_sha256']=m.sha(path)
            build['commands'][0]['argv']=['c++','-c',str(harness),'-o','fixture.o'];build['harness_compilation']={'source':str(harness),'sha256':m.sha(harness),'argv':build['commands'][0]['argv'],'command_index':0};br.write_text(json.dumps(build));binding['build_receipt_sha256']=m.sha(br)
            bp=p/'binding.json';bp.write_text(json.dumps(binding));self.assertEqual(m.verify_arm(exe,bp,'reference',api)['role'],'reference')
            with self.assertRaisesRegex(ValueError,'schema/role'):m.verify_arm(exe,bp,'candidate',api)
            import copy
            pristine=copy.deepcopy(build)
            def set_build(value):
                br.write_text(json.dumps(value));binding['build_receipt_sha256']=m.sha(br);bp.write_text(json.dumps(binding))
            mutations=[
                ('core archive',lambda x:x['target_artifacts'].pop('core_archive')),
                ('core archive',lambda x:x['target_artifacts']['core_archive'].update(path=str(exe))),
                ('core archive',lambda x:x['target_artifacts']['core_archive'].update(sha256='0'*64)),
                ('executable',lambda x:x['target_artifacts']['helper'].update(path=str(core))),
                ('harness compilation',lambda x:x.pop('harness_compilation')),
                ('harness compilation',lambda x:x['harness_compilation'].update(source=str(exe))),
                ('harness compilation',lambda x:x['harness_compilation'].update(sha256='0'*64)),
                ('harness compilation',lambda x:x['harness_compilation'].update(command_index=True)),
                ('harness compilation',lambda x:x['harness_compilation'].update(command_index=1)),
                ('harness compilation',lambda x:x['harness_compilation'].update(argv=['c++','different.cpp'])),
                ('harness compilation',lambda x:(x['harness_compilation'].update(argv=['c++',str(harness)+'.other']),x['commands'][0].update(argv=['c++',str(harness)+'.other']))),
            ]
            for message,mutate in mutations:
                with self.subTest(mutation=message,mutator=repr(mutate)):
                    changed=copy.deepcopy(pristine);mutate(changed);set_build(changed)
                    with self.assertRaisesRegex(ValueError,message):m.verify_arm(exe,bp,'reference',api)
            set_build(pristine)
            core.write_text('changed')
            with self.assertRaisesRegex(ValueError,'core_archive hash'):m.verify_arm(exe,bp,'reference',api)
            core.write_text('unit fixture archive');build['commands'][0]['returncode']=False;br.write_text(json.dumps(build));binding['build_receipt_sha256']=m.sha(br);bp.write_text(json.dumps(binding))
            with self.assertRaisesRegex(ValueError,'command failed'):m.verify_arm(exe,bp,'reference',api)
    def test_native_integer_schema_and_failures(self):
        first=m.row(b'0 0 32 7 42 43 1\n',None,8)
        self.assertEqual(m.row(b'0 1 31 7 40 41 1\n',first,8)[:2],(0,1))
        for raw in (b'0 BAD\n',b'0 ILLEGAL\n',b'0 0 32 7 42 43 1',b'0 0 32 6 42 43 1\n',b'0 0 32 7 42 43 0\n',b'2 0 32 7 42 43 1\n'):
            with self.assertRaises(ValueError):m.row(raw,None,8)
        with self.assertRaises(ValueError):m.row(b'0 0 32 7 42 43 1\n',first,8)
        self.assertEqual(m.row(b'1 0 2 0 42 43 1\n',first,8)[:2],(1,0))

    def test_real_child_inherits_input_fd_and_saved_gzip_roundtrips(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);exe=p/'fixture';exe.write_text('#!'+sys.executable+'\nimport sys,os\nassert os.environ["PYTHONDONTWRITEBYTECODE"]=="1"\nassert open(sys.argv[1]).read()=="fixture\\n"\nprint("0 0 32 7 42 43 1")\nprint("lines 1 available=1 residual=1 hidden=256 acc_mismatch=0",file=sys.stderr)\n');exe.chmod(0o700)
            fd=os.memfd_create('unit_fixture',os.MFD_CLOEXEC)
            try:
                os.write(fd,b'fixture\n')
                with mock.patch.dict(os.environ,{'PYTHONDONTWRITEBYTECODE':'0'}):r=m.capture(exe,fd,0,p/'captured',5,1)
                self.assertEqual(r['rows'],1);self.assertEqual(r['roots'],1)
                self.assertEqual(gzip.open(p/'captured.stdout.gz','rb').read(),b'0 0 32 7 42 43 1\n')
            finally:os.close(fd)

    def test_excess_root_stops_immediately_and_owned_child_is_reaped(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);pid=p/'pid';exe=p/'fixture'
            exe.write_text('#!'+sys.executable+'\nimport os,time\nopen('+repr(str(pid))+',"w").write(str(os.getpid()))\nprint("0 0 32 7 42 43 1",flush=True)\nprint("1 0 32 7 42 43 1",flush=True)\ntime.sleep(10)\n');exe.chmod(0o700);fd=os.memfd_create('unit_fixture',os.MFD_CLOEXEC)
            try:
                with self.assertRaisesRegex(ValueError,'more native roots than corpus'):m.capture(exe,fd,0,p/'captured',2,1)
                with self.assertRaises(ProcessLookupError):os.kill(int(pid.read_text()),0)
            finally:os.close(fd)

if __name__=='__main__':unittest.main(verbosity=2)

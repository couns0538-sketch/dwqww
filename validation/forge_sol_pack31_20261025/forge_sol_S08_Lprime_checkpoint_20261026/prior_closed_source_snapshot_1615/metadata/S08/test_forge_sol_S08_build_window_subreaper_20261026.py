"""Contained Python grandchild regression; never touch existing PID1 children."""
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

MODULE=Path(__file__).with_name('forge_sol_S08_build_window_subreaper_20261026.py')


def subreaper(value=None):
    libc=ctypes.CDLL(None,use_errno=True)
    libc.prctl.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong]
    if value is not None:
        if libc.prctl(36,int(value),0,0,0)!=0:raise OSError(ctypes.get_errno(),'SET_CHILD_SUBREAPER')
    result=ctypes.c_int()
    if libc.prctl(37,ctypes.addressof(result),0,0,0)!=0:raise OSError(ctypes.get_errno(),'GET_CHILD_SUBREAPER')
    return result.value


class SubreaperTests(unittest.TestCase):
    def test_cleanup_failure_cannot_be_reported_as_resumable_pause(self):
        spec=importlib.util.spec_from_file_location('s08cleanup',MODULE)
        api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);job=root/'SYNTHETIC_BUILD';job.mkdir();(job/'build').mkdir();(job/'progress.json').write_text('{}')
            source=root/'source';source.mkdir();(source/'fixture').write_text('SYNTHETIC')
            compiler=root/'identity_only';compiler.write_text('NOT A COMPILER')
            freeze=root/'freeze.json';freeze.write_text(json.dumps({'source':str(source),'source_sha256':api.snapshot(source),'compiler_sha256':api.sha(compiler)}))
            window=root/'window'
            failed={'stop_reason':'OWNED_DEADLINE','returncode':-15,'error':'SYNTHETIC unreaped owned child'}
            with mock.patch.object(api,'CXX',compiler),mock.patch.object(api,'CXX_SHA',api.sha(compiler)), \
                 mock.patch.object(api,'run_owned',return_value=failed), \
                 mock.patch.object(api.os,'sched_getaffinity',return_value={0}),mock.patch.object(api.os,'getpriority',return_value=19):
                rc=api.main(['--execute','--s26-job',str(job),'--window-dir',str(window),'--build-dir',str(window/'build'),
                    '--source-freeze',str(freeze),'--authorization-reference','SYNTHETIC only'])
            stored=json.loads((window/'forge_sol_S08_ON_build_result_20261026.json').read_text())
            self.assertEqual(stored['status'],'FAIL_BUILD_ONLY')
            self.assertEqual(rc,1)

    def test_scope_changes_only_current_process_and_restores_prior_flag(self):
        spec=importlib.util.spec_from_file_location('s08subreaper',MODULE)
        api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
        self.assertTrue(hasattr(api,'SubreaperScope'),'current-process subreaper scope is missing')
        before=subreaper()
        with api.SubreaperScope():self.assertEqual(subreaper(),1)
        self.assertEqual(subreaper(),before)

    def test_interrupted_grandchild_is_reaped_by_owning_supervisor(self):
        # Outer containment adopts any old/unfixed orphan, so RED adds no PID1 zombie.
        before=subreaper();subreaper(1);grandchild=None
        try:
            with tempfile.TemporaryDirectory() as root:
                root=Path(root);job=root/'SYNTHETIC_S26_BUILD';job.mkdir();(job/'build').mkdir();(job/'progress.json').write_text('{}\n')
                out=root/'raw';out.mkdir()
                spawner=root/'SYNTHETIC_grandchild.py'
                spawner.write_text('import subprocess,sys,time\np=subprocess.Popen([sys.executable,"-c","import time; time.sleep(20)"])\nprint(p.pid,flush=True)\ntime.sleep(20)\n')
                wrapper=root/'SYNTHETIC_supervisor.py'
                wrapper.write_text('import importlib.util,sys,time\nfrom pathlib import Path\ns=importlib.util.spec_from_file_location("window",sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nm.run_owned([sys.executable,"-u",sys.argv[4]],Path(sys.argv[3]),"owned",Path(sys.argv[2]),time.monotonic()+2.5)\n')
                process=subprocess.run([sys.executable,'-B',str(wrapper),str(MODULE),str(job),str(out),str(spawner)],capture_output=True,text=True,timeout=8)
                self.assertEqual(process.returncode,0,process.stderr)
                grandchild=int((out/'owned.stdout').read_text().strip())
                receipt=json.loads((out/'owned.receipt.json').read_text())
                self.assertEqual(receipt['stop_reason'],'OWNED_DEADLINE')
                self.assertFalse((Path('/proc')/str(grandchild)).exists(),'unfixed supervisor left its grandchild as an adopted zombie')
                self.assertIn(grandchild,receipt['reaped_descendant_pids'])
                self.assertEqual(receipt['all_group_members_after_reap'],[])
                self.assertTrue(receipt['leader_reaped'])
        finally:
            # Only this fixture's known descendant may be waited on by containment.
            if grandchild is not None:
                try:
                    result=os.waitpid(grandchild,os.WNOHANG)
                    if result[0]==0:
                        os.kill(grandchild,signal.SIGKILL)
                        os.waitpid(grandchild,0)
                except (ChildProcessError,ProcessLookupError):pass
            subreaper(before)


if __name__=='__main__':unittest.main(verbosity=2)

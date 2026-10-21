"""Collector failure preservation using mocked processes; no child is launched."""
import importlib.util,json,subprocess,tempfile,time,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parent;PKG=ROOT.parents[1]/'.github/hosted-nearest-pawn-performance'
spec=importlib.util.spec_from_file_location('collector_under_test',PKG/'prepare_hosted.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Collector(unittest.TestCase):
    def failed_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);child=mock.Mock();child.pid=12345;child.returncode=None;child.wait.side_effect=subprocess.TimeoutExpired(['inert'],1)
            writes=[];save=m.runner.save;empty=[False]
            def persistence(path,record):
                writes.append(dict(record))
                if len(writes)==2:raise OSError('injected pre-verdict persistence failure')
                save(path,record)
            def cleanup(process):child.returncode=-9;empty[0]=True
            with mock.patch.object(m.subprocess,'Popen',return_value=child) as spawn,mock.patch.object(m.runner,'save',side_effect=persistence),mock.patch.object(m.runner,'_owned_group_empty',side_effect=lambda process:empty[0]),mock.patch.object(m.runner,'stop_group',side_effect=cleanup) as stop:
                with self.assertRaises(OSError):m.stage(out,'inert-stage',['never-executed'],out,1,time.monotonic()+10)
                self.assertEqual(spawn.call_count,1);self.assertEqual(stop.call_count,1)
            return json.loads((out/'inert-stage-command.json').read_text())
    def test_persistence_failure_cannot_skip_collector_cleanup(self):
        facts=self.failed_persistence();self.assertTrue(facts['cleanup_attempted']);self.assertTrue(facts['owned_group_empty_after_cleanup']);self.assertEqual(facts['exit_code'],-9)
    def test_original_wait_failure_retained_when_observation_save_fails(self):
        facts=self.failed_persistence();self.assertIn('TimeoutExpired',facts['wait_error']);self.assertTrue(facts['timed_out']);self.assertIn('injected',facts['error'])
    def test_deadline_failure_before_process(self):
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(m.subprocess,'Popen') as spawn:
            with self.assertRaises(TimeoutError):m.stage(Path(tmp),'no-launch',['inert'],Path(tmp),1,time.monotonic()-1)
            spawn.assert_not_called()
    def test_collection_preserves_inert_executable_mode_and_failure_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'out';out.mkdir();build=root/'build';build.mkdir();source=root/'source';source.mkdir()
            (build/'forge').write_bytes(b'inert never execute');(build/'forge').chmod(0o755);(build/'libforge_core.a').write_bytes(b'inert archive');(build/'CMakeCache.txt').write_text('partial config')
            m.collect_label(out,'candidate','pin',source,build)
            self.assertEqual((out/'artifacts/candidate/forge').stat().st_mode&0o777,0o755);self.assertEqual((out/'candidate-CMakeCache.txt').read_text(),'partial config')
if __name__=='__main__':unittest.main(verbosity=2)

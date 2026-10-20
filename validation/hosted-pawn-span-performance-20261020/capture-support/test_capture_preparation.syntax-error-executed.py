"""Read-only actual inputs and blocked-execution controls; no capture/child launch."""
import importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('capture_driver_preparation_test',ROOT/'capture_actual_five.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CapturePreparation(unittest.TestCase):
 def test_actual_source_and_release_inputs_have_exact19_20_identities(self):
  for label,plan in m.PLANS.items():
   row=m.inspect_plan(label,plan)
   self.assertEqual(row['source_commit'],plan['source_sha'])
   self.assertEqual(len(row['source_sha256_before']),74 if label=='baseline' else75)
 def test_frozen_helper_is_exact_finalized461a(self):
  self.assertEqual(m.digest(m.HELPER),m.EXPECTED_HELPER)
  self.assertEqual(m.HELPER.read_bytes(),(m.PACKAGE/'owned_process.py').read_bytes())
 def test_missing_authorization_fails_before_helper_load_or_child(self):
  with tempfile.TemporaryDirectory(dir=ROOT) as tmp,patch.object(m,'load',side_effect=AssertionError('No process helper may be loaded')),patch.object(subprocess,'Popen',side_effect=AssertionError('No child may be launched')):
   with self.assertRaisesRegex(ValueError,'Missing/unsafe proof'):m.capture(Path(tmp)/'missing.json')
 def test_example_authorization_cannot_launch(self):
  with patch.object(m,'load',side_effect=AssertionError('No process helper may be loaded')),patch.object(subprocess,'Popen',side_effect=AssertionError('No child may be launched')):
   with self.assertRaisesRegex(ValueError,'authorization required'):m.capture(ROOT/'ROOT-CAPTURE-AUTHORIZATION.example.json')
 def test_wrong_driver_pin_cannot_authorize_capture(self):
  auth=json.loads((ROOT/'ROOT-CAPTURE-AUTHORIZATION.example.json').read_text());auth.update(authorized=True,status=m.AUTH_STATUS,driver_sha256='0'*64)
  with tempfile.TemporaryDirectory(dir=ROOT) as tmp,patch.object(m,'load',side_effect=AssertionError('No process helper may be loaded')),patch.object(subprocess,'Popen',side_effect=AssertionError('No child may be launched')):
   p=Path(tmp)/'authorization.json';p.write_text(json.dumps(auth))
   with self.assertRaisesRegex(ValueError,'driver/helper authorization pin'):m.capture(p)
 def test_source_inventory_cannot_hide_missing_or_extra_inputs(self):
  with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
   source=Path(tmp);(source/'one').write_bytes(b'one');expected={'one':m.digest(source/'one')}
   self.assertEqual(m.source_map({'source':source},expected),expected)
   (source/'extra').write_bytes(b'extra')
   with self.assertRaisesRegex(ValueError,'Complete source inventory'):m.source_map({'source':source},expected)
if __name__=='__main__':unittest.main(verbosity=2)

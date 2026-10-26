import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('activity',ROOT/'forge_sol_S10_activation_20261026.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OPTION='ImprovingRazorGuard'
UCI='option name '+OPTION+' type check default false\nuciok\n'
OFF='info string bench depth 11 nodes 308972 time 1 nps 308972000\n'
ON='info string '+OPTION+' active\ninfo string bench depth 11 nodes 309000 time 1 nps 309000000\n'
class Activation(unittest.TestCase):
 def test_changed_nodes_and_announced_option(self):self.assertEqual(m.validate_activity(UCI,OFF,ON,OPTION)['on_nodes'],309000)
 def test_unknown_option_cannot_pass(self):
  with self.assertRaises(ValueError):m.validate_activity('uciok\n',OFF,ON,OPTION)
 def test_silently_ignored_option_cannot_pass(self):
  with self.assertRaises(ValueError):m.validate_activity(UCI,OFF,'info string '+OPTION+' active\n'+OFF,OPTION)
 def test_wrong_default_cannot_pass(self):
  with self.assertRaises(ValueError):m.validate_activity(UCI.replace('false','true'),OFF,ON,OPTION)
 def test_wrong_type_cannot_pass(self):
  with self.assertRaises(ValueError):m.validate_activity(UCI.replace('type check','type string'),OFF,ON,OPTION)
 def test_absent_actual_activation_rejected(self):
  with self.assertRaises(ValueError):m.validate_activity(UCI,OFF,ON.split('\n',1)[1],OPTION)
 def test_duplicate_record_rejected(self):
  with self.assertRaises(ValueError):m.validate_activity(UCI,OFF,ON+ON,OPTION)
 def test_wrong_off_reference_rejected(self):
  with self.assertRaises(ValueError):m.validate_activity(UCI,OFF.replace('308972','308971'),ON,OPTION)
 def test_active_off_rejected(self):
  with self.assertRaises(ValueError):m.validate_activity(UCI,'info string '+OPTION+' active\n'+OFF,ON,OPTION)
if __name__=='__main__':unittest.main()

from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'astra_r8'/'datafilter'))
import resource_policy as policy

class RuntimePolicyTests(unittest.TestCase):
    def test_owned_root_only(self):
        self.assertEqual(policy.ARTIFACT_ROOT,Path('D:/a13'))
        self.assertTrue(all(p.is_relative_to(Path('D:/a13')) for p in policy.BUDGET_ROOTS))

    def test_exact_gib_floor_and_no_other_drive_scan(self):
        calls=[]
        def usage(drive):
            calls.append(str(drive))
            return SimpleNamespace(free=50*1024**3+100)
        with patch.object(policy.shutil,'disk_usage',side_effect=usage), patch.object(policy,'tree_bytes',return_value=0):
            policy.storage_guard(allowance=100)
            self.assertEqual(calls,['D:/'])
            with self.assertRaises(OSError):
                policy.storage_guard(allowance=101)

if __name__=='__main__':
    unittest.main()

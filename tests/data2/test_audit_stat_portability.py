"""Original tests for Windows 3.12 stat/fstat ctime differences."""
import hashlib,pathlib,sys,tempfile,types,unittest
from unittest import mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'tools/data2'))
import audit_holdout_clearance as a
FIELDS=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
def snapshot(value,**changes):
 result={name:getattr(value,name) for name in FIELDS};result.update(changes);return types.SimpleNamespace(**result)
class StatPortability(unittest.TestCase):
 def setUp(self):self.value=types.SimpleNamespace(st_dev=1,st_ino=2,st_size=3,st_mtime_ns=4,st_ctime_ns=5)
 def test_nonposix_ctime_ignored_required_identity_fields_preserved(self):
  with mock.patch.object(a,'os',types.SimpleNamespace(name='nt')):
   expected=a.stat_identity(self.value)
   self.assertEqual(expected,a.stat_identity(snapshot(self.value,st_ctime_ns=999)))
   self.assertEqual(set(expected),{'device','inode','size','mtime_ns'})
   for field in FIELDS[:-1]:self.assertNotEqual(expected,a.stat_identity(snapshot(self.value,**{field:999})))
 def test_posix_keeps_ctime_change_detection(self):
  with mock.patch.object(a,'os',types.SimpleNamespace(name='posix')):
   self.assertNotEqual(a.stat_identity(self.value),a.stat_identity(snapshot(self.value,st_ctime_ns=999)))
 def test_fingerprint_accepts_windows_handle_path_ctime_difference(self):
  with tempfile.TemporaryDirectory() as folder:
   p=pathlib.Path(folder)/'data';p.write_bytes(b'exact bytes')
   real_fstat=a.os.fstat
   proxy=types.SimpleNamespace(name='nt',fstat=lambda fd:snapshot(real_fstat(fd),st_ctime_ns=1))
   with mock.patch.object(a,'os',proxy):result=a.fingerprint(p,lambda:None)
   self.assertEqual(result['sha256'],hashlib.sha256(b'exact bytes').hexdigest())
   self.assertNotIn('ctime_ns',result['stat'])
if __name__=='__main__':unittest.main()

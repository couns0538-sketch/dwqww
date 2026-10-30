"""Original descriptor-access regression for Windows CRT fsync semantics."""
import contextlib,io,os,pathlib,stat,sys,tempfile,unittest
from unittest import mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'tools/data2'))
import convert_dataset as c
FEN='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 61 | 0.0\n'
class WritableFsync(unittest.TestCase):
 def test_sealed_regular_files_have_writable_descriptors_for_fsync(self):
  with tempfile.TemporaryDirectory() as folder:
   root=pathlib.Path(folder);source=root/'input.txt';source.write_text(FEN)
   args=c.parser().parse_args(['convert','--input',str(source),'--out',str(root/'out'),'--no-filters','--min-free-mb','0'])
   original=os.fsync;checked=[]
   def windows_like_fsync(fd):
    if stat.S_ISREG(os.fstat(fd).st_mode):
     if os.name=='posix':
      import fcntl
      if fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE==os.O_RDONLY:raise OSError(9,'Windows CRT fsync requires writable file descriptor')
     checked.append(fd)
    return original(fd)
   with mock.patch.object(c.os,'fsync',side_effect=windows_like_fsync),contextlib.redirect_stdout(io.StringIO()):result=c.run(args)
   self.assertEqual(result['counts']['kept'],1);self.assertGreaterEqual(len(checked),6)
   self.assertEqual(source.read_text(),FEN)
   self.assertEqual(c.verify(root/'out')['rows'],1)
if __name__=='__main__':unittest.main()

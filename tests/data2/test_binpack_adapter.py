"""Original adapter regression tests. Set FORGE_BINPACK_ADAPTER to the built tool."""
import hashlib,json,os,pathlib,struct,subprocess,tempfile,unittest
EXE=os.environ.get('FORGE_BINPACK_ADAPTER')
START='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
EP='rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'

@unittest.skipUnless(EXE, 'external GPL-3.0 adapter is opt-in via FORGE_BINPACK_ADAPTER')
class Adapter(unittest.TestCase):
    def setUp(self):
        self.root=pathlib.Path(tempfile.mkdtemp(prefix='astra-binpack-case-',dir='/tmp'))
    def run_tool(self,*args):
        return subprocess.run([EXE,*map(str,args)],capture_output=True,text=True)
    def encode(self,text,allow=True):
        p=self.root/'input.txt';p.write_text(text);out=self.root/'data.binpack'
        r=self.run_tool('encode',p,out,*(['--allow-transport-move'] if allow else []))
        return r,out
    def test_exact_fen_score_result_inert_ep_and_rights(self):
        text=f'{START} | 300 | 0.5\n{EP} | -321 | 1.0\n'
        r,out=self.encode(text);self.assertEqual(r.returncode,0,r.stderr)
        d=self.run_tool('decode',out);self.assertEqual(d.returncode,0,d.stderr);self.assertEqual(d.stdout,text)
    def test_requires_explicit_fallback(self):
        r,_=self.encode(f'{START} | 1 | 1.0\n',False);self.assertNotEqual(r.returncode,0);self.assertIn('explicitly required',r.stderr)
    def test_supplied_move(self):
        r,out=self.encode(f'{START} | -9 | 0.0 | e2e4\n',False);self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stderr)['transport_move_fallbacks'],0)
        self.assertEqual(self.run_tool('decode',out).stdout,f'{START} | -9 | 0.0\n')
    def test_illegal_supplied_move(self):
        r,_=self.encode(f'{START} | 1 | 0.5 | e2e5\n',False);self.assertNotEqual(r.returncode,0)
    def test_no_overwrite(self):
        r,out=self.encode(f'{START} | 1 | 0.5\n');self.assertEqual(r.returncode,0,r.stderr)
        before=out.read_bytes();r=self.run_tool('encode',self.root/'input.txt',out,'--allow-transport-move')
        self.assertNotEqual(r.returncode,0);self.assertEqual(out.read_bytes(),before)
    def test_halfmove_overflow_rejected(self):
        r,_=self.encode(f'{START.replace(" 0 1"," 256 1")} | 1 | 0.5\n');self.assertNotEqual(r.returncode,0)
    def test_ply_overflow_rejected(self):
        r,_=self.encode(f'{START.replace(" 0 1"," 0 8193")} | 1 | 0.5\n');self.assertNotEqual(r.returncode,0)
    def test_missing_king_rejected_without_crash(self):
        r,_=self.encode('8/8/8/8/8/8/8/8 w - - 0 1 | 0 | 0.5\n');self.assertEqual(r.returncode,1)
    def test_bad_score_rejected(self):
        r,_=self.encode(f'{START} | 32768 | 0.5\n');self.assertEqual(r.returncode,1)
    def test_empty(self):
        r,out=self.encode('');self.assertEqual(r.returncode,0,r.stderr);d=self.run_tool('decode',out);self.assertEqual(d.returncode,0,d.stderr);self.assertEqual(d.stdout,'')
    def test_corrupt_chunk_rejected(self):
        p=self.root/'corrupt.binpack';p.write_bytes(b'BINP'+struct.pack('<I',100)+b'x')
        self.assertEqual(self.run_tool('decode',p).returncode,1)
    def test_corrupt_occupancy_rejected(self):
        r,out=self.encode(f'{START} | 0 | 0.5\n');self.assertEqual(r.returncode,0,r.stderr)
        b=bytearray(out.read_bytes());b[8:16]=b'\xff'*8;p=self.root/'corrupt.binpack';p.write_bytes(b)
        self.assertEqual(self.run_tool('decode',p).returncode,1)
    def test_deterministic(self):
        r,out=self.encode(f'{START} | 0 | 0.5\n');self.assertEqual(r.returncode,0,r.stderr)
        p=self.root/'again.binpack';r=self.run_tool('encode',self.root/'input.txt',p,'--allow-transport-move');self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(out.read_bytes(),p.read_bytes())

if __name__=='__main__':unittest.main()

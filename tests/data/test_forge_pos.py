"""Format/provenance regressions; fixtures are legal tiny positions, not training evidence."""
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/data'))
from forge_pos import (HEADER, RECONSTRUCTION_POLICY, Record, PosReader, PosWriter,
                       aligned_records, board_to_fen, fen_record, file_hash,
                       match_fen, match_text_record, text_record, validate_record, write_manifest)

START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
AFTER_E4 = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'
KRK = '4R3/8/8/k2K4/8/8/8/8 w - - 0 1'


class PosFormatTests(unittest.TestCase):
    def setUp(self):
        parent = os.environ.get('FORGE_POS_TEST_ROOT')
        if parent:
            Path(parent).mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='forge-pos-test-', dir=parent))
        # Intentionally retained: no test removes any file or directory.

    def record(self, fen=START, score=42, result=1, hce=7):
        row = fen_record(fen, score, result)
        return Record(row.board, row.score, row.meta, hce)

    def write_pair(self, rows, fens=None, stem='data'):
        writer = PosWriter(self.root, stem, with_hce=True)
        for i, row in enumerate(rows):
            writer.append(row, fen=None if fens is None else fens[i])
        return writer.close()

    def test_columnar_roundtrip_and_known_nibbles(self):
        a = self.record(); b = self.record(AFTER_E4, -123, 0.5, -17)
        receipt = self.write_pair([a, b], [START, AFTER_E4])
        data = (self.root/'data.pos').read_bytes()
        self.assertEqual(data, HEADER.pack(b'FPOS', 1, 2)+a.board+b.board+struct.pack('<hh', 42, -123)+bytes([4,3]))
        self.assertEqual(a.board[0], 0x24)
        self.assertEqual(a.board[28], 0x8A)
        self.assertEqual((self.root/'data.hce').read_bytes(), HEADER.pack(b'FHCE',1,2)+struct.pack('<hh',7,-17))
        self.assertEqual(receipt['count'],2)
        with PosReader(self.root/'data.pos',self.root/'data.hce') as reader:
            self.assertEqual(list(reader),[a,b]);self.assertEqual(reader.n,2)
            self.assertEqual(list(aligned_records(reader,self.root/'data.fen',sidecar_format='fen')),[(a,START),(b,AFTER_E4)])
        self.assertTrue((self.root/'data.pos.part').exists())
        self.assertTrue((self.root/'data.boards.part').exists())

    def test_stm_and_result_orientation_are_not_flipped(self):
        for fen,stm in [(START,0),(AFTER_E4,1)]:
            for result,code in [(0,0),(0.5,1),(1,2)]:
                row,full = text_record(f'{fen} | -91 | {result}')
                self.assertEqual(row.meta,stm|(code<<1));self.assertEqual(row.score,-91)
                self.assertEqual(full,fen)

    def test_full_text_matches_score_and_result(self):
        row=self.record()
        self.assertEqual(match_text_record(row,f'{START} | 42 | 1.0'),START)
        for line in [f'{START} | 43 | 1.0',f'{START} | 42 | 0.0',f'{AFTER_E4} | 42 | 1.0']:
            with self.assertRaises(ValueError):match_text_record(row,line)

    def test_fen_sidecar_only_requires_board_stm(self):
        row=self.record()
        self.assertEqual(match_fen(row,START.replace('KQkq - 0 1','- - 19 27')),START.replace('KQkq - 0 1','- - 19 27'))
        with self.assertRaises(ValueError):match_fen(row,START.replace(' w ',' b '))

    def test_alignment_rejects_short_extra_and_mismatch(self):
        self.write_pair([self.record()])
        for i,content in enumerate(['',f'{START} | 42 | 1\n{START} | 42 | 1\n',f'{START} | 43 | 1\n']):
            path=self.root/f'side{i}.txt';path.write_text(content)
            with PosReader(self.root/'data.pos') as reader:
                with self.assertRaises(ValueError):list(aligned_records(reader,path))

    def test_header_size_count_version_and_hce_mismatch(self):
        self.write_pair([self.record()])
        valid=(self.root/'data.pos').read_bytes()
        candidates=[valid[:8],b'FAIL'+valid[4:],valid[:4]+struct.pack('<I',2)+valid[8:],valid[:-1],valid+b'x',HEADER.pack(b'FPOS',1,2)+valid[16:]]
        for i,data in enumerate(candidates):
            path=self.root/f'bad{i}.pos';path.write_bytes(data)
            with self.assertRaises(ValueError):PosReader(path)
        h=self.root/'wrong.hce';h.write_bytes(HEADER.pack(b'FHCE',1,0))
        with self.assertRaises(ValueError):PosReader(self.root/'data.pos',h)

    def test_row_validation_rejects_invalid_codes_meta_scores(self):
        row=self.record()
        bad=[Record(bytes([15])+row.board[1:],42,4,7),Record(row.board,42,6,7),Record(row.board,-32768,4,7),Record(row.board,42,4,-32768)]
        for value in bad:
            with self.assertRaises(ValueError):validate_record(value)
        # Malformed on-disk fields are rejected by row(), not merely by writer.
        for i,kind in enumerate(['piece','meta','score','hce']):
            b=bytearray(row.board);score=42;meta=4;hce=7
            if kind=='piece':b[0]=15
            if kind=='meta':meta=255
            if kind=='score':score=-32768
            if kind=='hce':hce=-32768
            pos=self.root/f'badrow{i}.pos';hp=self.root/f'badrow{i}.hce'
            pos.write_bytes(HEADER.pack(b'FPOS',1,1)+b+struct.pack('<hB',score,meta))
            hp.write_bytes(HEADER.pack(b'FHCE',1,1)+struct.pack('<h',hce))
            with PosReader(pos,hp) as reader:
                with self.assertRaises(ValueError):reader.row(0)

    def test_no_overwrite_and_stale_claim(self):
        self.write_pair([self.record()]);before=(self.root/'data.pos').read_bytes()
        with self.assertRaises(FileExistsError):PosWriter(self.root,'data',True)
        self.assertEqual((self.root/'data.pos').read_bytes(),before)
        (self.root/'stale.claim.part').write_bytes(b'owned')
        with self.assertRaises(FileExistsError):PosWriter(self.root,'stale',False)

    def test_bad_append_aborts_and_retains_parts(self):
        writer=PosWriter(self.root,'broken',True)
        writer.append(self.record(),fen=START)
        with self.assertRaises(ValueError):writer.append(self.record(),fen=AFTER_E4)
        with self.assertRaises(ValueError):writer.close()
        self.assertFalse((self.root/'broken.pos').exists())
        self.assertTrue((self.root/'broken.boards.part').exists())
        self.assertEqual((self.root/'broken.boards.part').stat().st_size,32)

    def test_cannot_mix_sidecar_coverage(self):
        writer=PosWriter(self.root,'mixed',False)
        writer.append(self.record())
        with self.assertRaises(ValueError):writer.append(self.record(),fen=START)
        self.assertFalse((self.root/'mixed.pos').exists())

    def test_explicit_lossy_reconstruction_only(self):
        row=self.record(AFTER_E4)
        with self.assertRaises(ValueError):board_to_fen(row)
        reconstructed=board_to_fen(row,policy=RECONSTRUCTION_POLICY)
        self.assertEqual(reconstructed,AFTER_E4.replace('KQkq e3 0 1','- - 0 1'))
        self.assertEqual(fen_record(reconstructed,row.score,1).board,row.board)

    def test_empty_no_hce_and_idempotent_close(self):
        writer=PosWriter(self.root,'empty',False);first=writer.close()
        self.assertEqual(writer.close(),first)
        with PosReader(self.root/'empty.pos') as reader:
            self.assertEqual(reader.n,0);self.assertEqual(list(reader),[])
            with self.assertRaises(IndexError):reader.row(0)
        self.assertFalse((self.root/'empty.hce').exists())

    def test_explicit_empty_sidecar_is_preserved(self):
        writer=PosWriter(self.root,'empty_sidecar',False,with_fen=True)
        writer.close()
        self.assertEqual((self.root/'empty_sidecar.fen').read_bytes(),b'')
        with PosReader(self.root/'empty_sidecar.pos') as reader:
            self.assertEqual(list(aligned_records(reader,self.root/'empty_sidecar.fen',sidecar_format='fen')),[])

    def test_manifest_hashes_and_overwrite_protection(self):
        self.write_pair([self.record()]);p=self.root/'manifest.json'
        result=write_manifest(p,[self.root/'data.pos',self.root/'data.hce'],metadata={'kind':'synthetic tiny format fixture'})
        self.assertEqual(json.loads(p.read_text()),result)
        self.assertEqual(result['files'][0]['sha256'],hashlib.sha256((self.root/'data.pos').read_bytes()).hexdigest())
        self.assertEqual(file_hash(self.root/'data.hce','md5'),result['files'][1]['md5'])
        with self.assertRaises(FileExistsError):write_manifest(p,[])

    def test_invalid_manifest_metadata_never_publishes(self):
        self.write_pair([self.record()]);target=self.root/'invalid_manifest.json'
        with self.assertRaises(TypeError):write_manifest(target,[self.root/'data.pos'],metadata={'bad':object()})
        self.assertFalse(target.exists())

    def test_bad_fen_and_result_rejected(self):
        for fen in [START.rsplit(' ',1)[0],START.replace('KQkq','KK'),START.replace(' - 0 1',' e4 0 1'),START.replace('0 1','-1 1')]:
            with self.assertRaises(ValueError):fen_record(fen,1,0.5)
        for result in ['nan','sNaN','Infinity',0.25,True]:
            with self.assertRaises(ValueError):fen_record(START,1,result)


if __name__=='__main__':unittest.main()

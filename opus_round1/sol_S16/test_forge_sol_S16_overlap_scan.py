"""Tests for forge_sol_S16_overlap_scan.py on synthetic FPOS shards with aligned text (planted overlaps, an STM flip,
a label conflict, a holdout-internal duplicate, a straddling game, a whole-file copy, interleaved text, a forced
64-bit key collision, output-directory, RAM and mismatch guards, determinism, read-only inputs).
Run: FORGE_S16_TEST_ROOT=<new dir> python -I -B test_forge_sol_S16_overlap_scan.py -v   (needs numpy)
FORGE_S16_SCAN_TOOL selects the tool under test (the mutation check points it at mutants)."""
import gzip,hashlib,importlib.util,json,os,pathlib,shutil,sys,tempfile,unittest
sys.dont_write_bytecode=True
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent
TOOL=pathlib.Path(os.environ.get('FORGE_S16_SCAN_TOOL',str(HERE/'forge_sol_S16_overlap_scan.py'))).resolve()
_root=os.environ.get('FORGE_S16_TEST_ROOT')
WORK=pathlib.Path(_root).resolve() if _root else pathlib.Path(tempfile.mkdtemp(prefix='forge_s16_scan_tests_'))
WORK.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('s16scan',TOOL);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
RES=['0.0','0.5','1.0']

def placement(pawn,extra=None,kings=('K',0,'k',63)):
    """FEN placement with kings on fixed squares, a white pawn on `pawn` and optionally a black pawn on `extra`."""
    sq=[None]*64;sq[kings[1]]=kings[0];sq[kings[3]]=kings[2];sq[pawn]='P'
    if extra is not None:sq[extra]='p'
    ranks=[]
    for r in range(7,-1,-1):
        s='';e=0
        for f in range(8):
            c=sq[r*8+f]
            if c is None:e+=1
            else:
                if e:s+=str(e);e=0
                s+=c
        ranks.append(s+(str(e) if e else ''))
    return '/'.join(ranks)

def row(pl,stm,fm,score,result):
    return (M.pack_placement(pl),score,(stm=='b')|(result<<1),f'{pl} {stm} - - 0 {fm} | {score} | {RES[result]}\n')

def write(d,stem,rows,text=True):
    d.mkdir(parents=True,exist_ok=True);n=len(rows)
    with open(d/f'{stem}.pos','wb') as f:
        f.write(b'FPOS'+(1).to_bytes(4,'little')+n.to_bytes(8,'little'));f.write(b''.join(r[0] for r in rows))
        f.write(b''.join(int(r[1]).to_bytes(2,'little',signed=True) for r in rows));f.write(bytes(r[2] for r in rows))
    if text:(d/f'{stem}.txt').write_bytes(''.join(r[3] for r in rows).encode())
    return d/f'{stem}.pos'

def game(pawns,stm0,fm0,result,score=10,extra=None):
    out=[]
    for k,p in enumerate(pawns):
        stm='w' if (k%2==0)==(stm0=='w') else 'b';out.append(row(placement(p,extra),stm,fm0+(k+(stm0=='b'))//2,score+k,result))
    return out

class ScanTests(unittest.TestCase):
    def fixture(self,name,**kw):
        root=WORK/name;data=root/'data';data.mkdir(parents=True)
        # holdout: 013 = game A (5 rows) + start of game B (3); 014 = end of game B (2, continues across 013->014) + game C (2)
        A=game([8,9,10,11,12],'w',5,2);B1=game([16,17,18],'w',5,0);B2=game([19,20],'b',6,0);C=game([24,25],'w',5,1)
        h13=write(data,'forge_selfplay_013',A+B1);h14=write(data,'forge_selfplay_014',B2+C)
        early=game([32,33,34,35],'w',30,2)
        conflict=row(placement(17),'b',5,B1[1][1]+5,0)  # B1[1]'s position (013 row 6) with another score: a label conflict
        # 012: rows 2 and 4 = A[1] (013 row 1), row 3 = the conflict; it ends at fullmove 31, so 013 starts a new game
        t12=[early[0],early[1],A[1],conflict,A[1],early[2]]
        # 015: rows 0-1 continue game C of 014 (fullmove 6,7 rising, same result, same pieces) = a straddling game;
        # the last row has A[3]'s board with the other side to move, which is NOT the same position
        t15=[row(placement(26),'b',6,13,1),row(placement(27),'w',7,14,1)]+game([40,41,42],'w',5,0)+[row(placement(11),'w',9,13,2)]
        t12p=write(data,'forge_selfplay_012',t12);t15p=write(data,'forge_selfplay_015',t15)
        return root,data,[h13,h14],[t12p,t15p]
    def run_scan(self,root,data,hold,train,extra=(),name='out'):
        argv=['--holdout']+[str(p) for p in hold]+['--train']+[str(p) for p in train]+['--text-dir',str(data),'--out',str(root/name),'--min-free-ram-gib','0','--chunk-rows','3']+list(extra)
        code=M.main(argv);return code,json.loads((root/name/'forge_sol_S16_overlap_summary_20261027.json').read_text(encoding='utf-8'))
    def removal(self,root,name='out'):
        with gzip.open(root/name/'forge_sol_S16_removal_list_20261027.csv.gz','rt',encoding='utf-8') as f:return f.read().splitlines()

    def test_planted_overlaps_labels_stm_and_removal_list(self):
        root,data,hold,train=self.fixture('basic');code,s=self.run_scan(root,data,hold,train)
        self.assertEqual((code,s['status']),(0,'COMPLETED'))
        t={x['stem']:x for x in s['train']}
        self.assertEqual((t['forge_selfplay_012']['overlap_rows'],t['forge_selfplay_012']['distinct_holdout_positions_hit'],t['forge_selfplay_012']['label_conflicts']),(3,2,1))
        self.assertEqual((t['forge_selfplay_015']['overlap_rows'],t['forge_selfplay_015']['key_collisions_rejected']),(0,0))  # the STM-flipped board is not an overlap
        self.assertEqual(s['train_totals']['overlap_rows'],3);self.assertEqual(s['holdout']['positions_also_in_training'],2)
        rows=self.removal(root);self.assertEqual(rows[0],'stem,row,reason,holdout_stem,holdout_row,label_conflict')
        self.assertEqual(set(rows[1:]),{'forge_selfplay_012,2,holdout_position,forge_selfplay_013,1,0','forge_selfplay_012,3,holdout_position,forge_selfplay_013,6,1','forge_selfplay_012,4,holdout_position,forge_selfplay_013,1,0','forge_selfplay_015,0,holdout_game_group,,,0','forge_selfplay_015,1,holdout_game_group,,,0'})
        self.assertEqual(len(rows),6)
    def test_game_groups_straddle_and_fullmove_buckets(self):
        root,data,hold,train=self.fixture('games');code,s=self.run_scan(root,data,hold,train);g=s['games']
        self.assertEqual(g['status'],'COMPLETED');self.assertEqual(g['groups'],3);self.assertEqual(g['groups_with_any_training_position'],2);self.assertEqual(g['groups_fully_in_training'],0)
        j={(x['before'],x['after']):x for x in g['junctions']}
        self.assertTrue(j[('forge_selfplay_012','forge_selfplay_013')]['new_game_at_junction']);self.assertEqual(j[('forge_selfplay_012','forge_selfplay_013')]['straddling_training_rows'],0)
        self.assertFalse(j[('forge_selfplay_014','forge_selfplay_015')]['new_game_at_junction']);self.assertEqual(j[('forge_selfplay_014','forge_selfplay_015')]['straddling_training_rows'],2)
        self.assertEqual(g['straddling_training_rows_total'],2);self.assertEqual(sum(b['rows'] for b in g['holdout_rows_by_fullmove']),s['holdout']['rows'])
        self.assertEqual(g['tripwire']['result'],'PASS')
    def test_holdout_internal_duplicate_rows_are_all_marked(self):
        root=WORK/'dup';data=root/'data';A=game([8,9,10],'w',5,2);B=game([16,17],'w',5,0)
        h=write(data,'forge_selfplay_013',A+B+[A[1]],text=False)  # A[1] twice inside the holdout
        t=write(data,'forge_selfplay_012',[A[1]],text=False)
        argv=['--holdout',str(h),'--train',str(t),'--out',str(root/'out'),'--min-free-ram-gib','0']
        self.assertEqual(M.main(argv),0);s=json.loads((root/'out/forge_sol_S16_overlap_summary_20261027.json').read_text())
        self.assertEqual((s['holdout']['rows'],s['holdout']['unique_positions'],s['holdout']['duplicate_rows_within_holdout']),(6,5,1))
        self.assertEqual((s['holdout']['positions_also_in_training'],s['holdout']['rows_whose_position_is_in_training']),(1,2));self.assertEqual(s['games'],{'status':'UNVERIFIED_NO_TEXT'})
    def test_whole_file_copy_is_reported_and_fully_overlapping(self):
        root,data,hold,train=self.fixture('copy');copy=data/'forge_selfplay_016.pos';shutil.copyfile(hold[1],copy)
        code,s=self.run_scan(root,data,hold,train+[copy]);self.assertEqual(code,0)
        self.assertIn(['forge_selfplay_014','forge_selfplay_016'],s['whole_file_duplicates'])
        t={x['stem']:x for x in s['train']};self.assertEqual(t['forge_selfplay_016']['overlap_rows'],t['forge_selfplay_016']['rows'])
    def test_interleaved_text_fails_the_game_analysis_closed(self):
        root=WORK/'interleave';data=root/'data';rows=[]
        for k in range(120):rows.append(row(placement(8+k%40,48+k//40),'w',5+(k%2)*25+k//2,10,2))  # alternating games
        h=write(data,'forge_selfplay_013',rows);t=write(data,'forge_selfplay_012',game([60,61],'w',5,2))
        code,s=self.run_scan(root,data,[h],[t]);self.assertEqual(code,0)
        self.assertEqual(s['games']['status'],'FAILED_CLOSED_INTERLEAVED_TEXT');self.assertGreater(s['games']['tripwire']['largest_boundaries_in_window'],20);self.assertIsNone(s['games']['groups'])
        self.assertEqual(s['games']['tripwire']['result'],'FAIL_SUSPECTED_INTERLEAVING')
    def test_tripwire_threshold_is_exactly_twenty_boundaries_per_100_rows(self):
        f=np.zeros(150,bool);f[np.arange(20)*4]=True;self.assertEqual(M.tripwire(f,100,20),20)
        f[1]=True;self.assertEqual(M.tripwire(f,100,20),21);self.assertEqual((M.TRIPWIRE_WINDOW,M.TRIPWIRE_LIMIT),(100,20))
    def test_result_change_alone_starts_a_new_game(self):
        root=WORK/'result_only';data=root/'data'
        h=write(data,'forge_selfplay_013',game([8,9,10],'w',5,2)+game([16,17,18],'w',9,0))  # 2nd game: higher fullmove, other result
        t=write(data,'forge_selfplay_012',game([40,41],'w',40,1))
        code,s=self.run_scan(root,data,[h],[t]);self.assertEqual((code,s['games']['groups']),(0,2))
    def test_forced_64bit_collision_is_rejected_by_the_exact_check(self):
        root=WORK/'collision';data=root/'data'
        hold=[row(placement(8+k,40),'w',5+k,10,2) for k in range(4)]  # distinct first 8 bytes (rank-2 pawn), extra black pawn
        h=write(data,'forge_selfplay_013',hold,text=False);t=write(data,'forge_selfplay_012',[row(placement(9),'w',5,10,2),hold[2]],text=False)
        saved=M.keys64;M.keys64=lambda boards,metas:np.ascontiguousarray(boards)[:,:8].copy().view('<u8').reshape(-1)^(np.asarray(metas)&1).astype(np.uint64);self.addCleanup(setattr,M,'keys64',saved)
        self.assertEqual(M.main(['--holdout',str(h),'--train',str(t),'--out',str(root/'out'),'--min-free-ram-gib','0']),0)
        s=json.loads((root/'out/forge_sol_S16_overlap_summary_20261027.json').read_text());x=s['train'][0]
        self.assertEqual((x['overlap_rows'],x['key_collisions_rejected']),(1,1))
        M.keys64=lambda boards,metas:np.zeros(len(boards),np.uint64)
        with self.assertRaises(ValueError):M.main(['--holdout',str(h),'--train',str(t),'--out',str(root/'out2'),'--min-free-ram-gib','0'])
    def test_text_pos_mismatch_fails_closed(self):
        root,data,hold,train=self.fixture('mismatch');p=data/'forge_selfplay_013.txt';p.write_text(p.read_text().replace('| 10 |','| 99 |',1))
        with self.assertRaises(ValueError) as c:self.run_scan(root,data,hold,train)
        self.assertIn('text/POS',str(c.exception));s=json.loads((root/'out/forge_sol_S16_overlap_summary_20261027.json').read_text());self.assertEqual(s['status'],'FAILED')
    def test_output_inside_input_directory_or_existing_is_refused(self):
        root,data,hold,train=self.fixture('outdir');before=sorted(p.name for p in data.iterdir())
        with self.assertRaises(ValueError):M.main(['--holdout',str(hold[0]),'--train',str(train[0]),'--out',str(data/'new_out'),'--min-free-ram-gib','0'])
        (root/'exists').mkdir()
        with self.assertRaises(FileExistsError):M.main(['--holdout',str(hold[0]),'--train',str(train[0]),'--out',str(root/'exists'),'--min-free-ram-gib','0'])
        self.assertEqual(sorted(p.name for p in data.iterdir()),before)
    def test_low_free_ram_stops_before_reading(self):
        root,data,hold,train=self.fixture('ram');saved=M.free_ram_bytes;M.free_ram_bytes=lambda:2**30;self.addCleanup(setattr,M,'free_ram_bytes',saved)
        argv=['--holdout']+[str(p) for p in hold]+['--train']+[str(p) for p in train]+['--out',str(root/'out'),'--min-free-ram-gib','6']
        self.assertEqual(M.main(argv),3);s=json.loads((root/'out/forge_sol_S16_overlap_summary_20261027.json').read_text())
        self.assertEqual(s['status'],'STOPPED_LOW_RAM');self.assertNotIn('train',s)
    def test_deterministic_and_inputs_unchanged(self):
        root,data,hold,train=self.fixture('determinism');digest=lambda:{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.iterdir())}
        before=digest();self.run_scan(root,data,hold,train,name='a');self.run_scan(root,data,hold,train,name='b');self.assertEqual(digest(),before)
        self.assertEqual((root/'a/forge_sol_S16_removal_list_20261027.csv.gz').read_bytes(),(root/'b/forge_sol_S16_removal_list_20261027.csv.gz').read_bytes())
        self.assertEqual((root/'a/forge_sol_S16_removal_list_20261027.csv.gz').read_bytes()[4:8],b'\0\0\0\0')  # gzip header mtime fixed at 0
        def stable(o):
            if isinstance(o,dict):return {k:stable(v) for k,v in o.items() if k not in ('created_utc','elapsed_seconds','seconds','index_seconds','free_ram_gib_start','free_ram_gib_before')}
            return [stable(v) for v in o] if isinstance(o,list) else o
        a,b=(json.loads((root/n/'forge_sol_S16_overlap_summary_20261027.json').read_text()) for n in 'ab');self.assertEqual(stable(a),stable(b))
        sums=(root/'a/SHA256SUMS').read_text().splitlines();self.assertEqual(len(sums),3)
        bm='forge_sol_S16_holdout_rows_in_training_bitmap_20261027.npy';self.assertEqual((root/'a'/bm).read_bytes(),(root/'b'/bm).read_bytes())
        self.assertEqual(int(np.unpackbits(np.load(root/'a'/bm),bitorder='little')[:a['holdout']['rows']].sum()),a['holdout']['rows_whose_position_is_in_training'])
    def test_training_input_that_is_a_holdout_file_is_refused(self):
        root,data,hold,train=self.fixture('alias')
        with self.assertRaises(ValueError):M.main(['--holdout',str(hold[0]),'--train',str(hold[0]),'--out',str(root/'out'),'--min-free-ram-gib','0'])
        link=root/'alias_dir';link.mkdir();os.link(hold[0],link/'renamed_shard.pos')  # same file, other stem
        with self.assertRaises(ValueError) as c:M.main(['--holdout',str(hold[0]),'--train',str(link/'renamed_shard.pos'),'--out',str(root/'out2'),'--min-free-ram-gib','0'])
        self.assertIn('is a holdout file',str(c.exception))

if __name__=='__main__':unittest.main()

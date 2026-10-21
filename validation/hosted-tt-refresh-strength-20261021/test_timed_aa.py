"""Actual nested match wrapper with synthetic PGNs; no engine or Fastchess process."""
import ast,hashlib,importlib.util,json,os,re,sys,tempfile,types,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];PKG=REPO/'.github/hosted-tt-refresh-strength'
SOURCE=Path(os.environ.get('PV_MATCH_SOURCE',str(PKG/'run_hosted.py')))
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
runner=load('pv_aa_runner',PKG/'run_hosted.py');stats=load('pv_aa_stats',PKG/'match/pgn_stats.py');validator=load('pv_aa_validator',REPO/'tools/match/windows_validate.py')
main=next(n for n in ast.parse(SOURCE.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
function=next(n for n in ast.walk(main) if isinstance(n,ast.FunctionDef) and n.name=='match')
class TimedAAGate(unittest.TestCase):
 def run_fixture(self,termination='normal'):
  with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
   root=Path(tmp);cfg=json.loads((PKG/'protocol.json').read_text());a=types.SimpleNamespace(out=root,baseline=Path('/INERT/baseline22'),candidate=Path('/INERT/candidate23'),fastchess=Path('/INERT/fastchess'),package=PKG)
   commands=[]
   def fake_run(command,path,scanner,seconds):
    commands.append(command);self.assertEqual(seconds,90);self.assertEqual(command[command.index('--tc')+1],'1+0.01');self.assertEqual(command[command.index('--pairs')+1],'4');self.assertEqual(command[command.index('--candidate')+1],str(a.baseline));self.assertNotIn('--aa',command);self.assertNotIn('--nodes',command)
    for key,value in [('--hash-mb','32'),('--overhead-ms','10'),('--mode','smoke')]:self.assertEqual(command[command.index(key)+1],value)
    self.assertIn('--disable-book',command);out=root/'aa';out.mkdir();runtime=json.loads((PKG/'provenance/runtime-order.json').read_text())['aa'];fens=runtime['ordered_fens'];blocks=[]
    for number,fen in enumerate(fens,1):
     for reverse in (False,True):
      white,black=('Baseline','Candidate') if reverse else ('Candidate','Baseline');moves='a2a3' if reverse else 'h2h3'
      blocks.append(f'[Event "INERT synthetic unit PGN"]\n[Round "{number}"]\n[White "{white}"]\n[Black "{black}"]\n[FEN "{fen} 0 1"]\n[Result "1/2-1/2"]\n[Termination "{termination}"]\n\n1. {moves} 1/2-1/2\n')
    (out/'games.pgn').write_text('\n'.join(blocks));(out/'console.txt').write_text('Ptnml(0-2): [0, 0, 4, 0, 0]\n');(out/'fastchess.log').write_text('');(out/'selected.epd').write_text('\n'.join(fens)+'\n');(out/'manifest.json').write_text(json.dumps({'selected_sha256':runner.sha(out/'selected.epd')}));return 0
   namespace={'a':a,'cfg':cfg,'cpu':0,'tools':PKG/'match','sys':sys,'re':re,'json':json,'save':runner.save,'sha':runner.sha,'FaultScanner':runner.FaultScanner,'run_owned':fake_run,'stats_module':stats,'validator':validator,'checked_inputs':lambda:None,'audit_likelihood':runner.audit_likelihood}
   exec(compile(ast.Module(body=[function],type_ignores=[]),str(SOURCE),'exec'),namespace)
   result=namespace['match']('aa',90);self.assertEqual(len(commands),1);return result
 def test_timed_aa_accepts_normal_nonidentical_moves_without_strength_decision(self):
  result=self.run_fixture();self.assertEqual(result['statistics']['pairs'],4);self.assertEqual(result['decision'],'aa_operational_readiness_only');self.assertIsNone(result['likelihood_audit'])
 def test_timed_aa_still_rejects_any_nonnormal_termination(self):
  with self.assertRaisesRegex(ValueError,'non-normal termination'):self.run_fixture('time forfeit')
if __name__=='__main__':unittest.main(verbosity=2)

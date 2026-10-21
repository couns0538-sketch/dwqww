"""Static skill checks adapted from existing cleanup harness; pure PGN contract tests."""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,sys,difflib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;S=R/'.agents/skills/validating-chess-strength';checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,ok):
 checks.append({'name':name,'pass':bool(ok)})
 if not ok:raise AssertionError(name)
text=(S/'SKILL.md').read_text();front=text.split('---\n',2)[1];metadata=dict(line.split(': ',1) for line in front.strip().splitlines());check('frontmatter_valid_two_simple_YAML_scalars',len(front)<1024 and set(metadata)=={'name','description'} and re.fullmatch('[a-z0-9-]+',metadata['name']) and metadata['description'].startswith('Use when '))
links=[]
for n in ['SKILL.md','scenarios.md']:
 for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',(S/n).read_text()):
  if '://' not in target and not target.startswith('#'):
   okay=(S/target.split('#')[0]).resolve().is_file();links.append({'from':n,'target':target,'exists':okay});check('relative_link:'+target,okay)
prior=json.loads((D/'PRIOR-PROOF-HASHES.json').read_text());check('all_available_prior_proofs_unchanged',all((R/p).is_file() and h(R/p)==v for p,v in prior.items()))
check('prior_scenarios_preserved_verbatim_prefix',(S/'scenarios.md').read_text().startswith((D/'before-scenarios.md').read_text()))
check('old_universal_fixednode_wording_removed','Run A/A first with the same binary, node budget' not in text)
for phrase in ['deterministic fixed-node A/A with unlimited clocks','timed operational A/A','Different timed moves/results alone are not a harness fault','Do not retrospectively relax a frozen deterministic gate']:
 check('required_distinction:'+phrase,phrase in text)
protocol=R/'.github/hosted-pv-metadata-strength/protocol.json';producer=R/'.github/hosted-pv-metadata-strength/run_hosted.py';cfg=json.loads(protocol.read_text());check('actual22_AA_mode',cfg['aa_settings']=={'pairs':4,'tc':'1+0.01','nodes':0,'identical_moves_required':False,'binary':'baseline'})
source=producer.read_text();tree=ast.parse(source);calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='summarize'];check('actual22_checker_identity_off',any(any(k.arg=='require_identical_pairs' and isinstance(k.value,ast.Constant) and k.value.value is False for k in n.keywords) for n in calls));check('actual22_operational_decision_only',"'aa_operational_readiness_only'" in source)
ps=R/'tools/match/pgn_stats.py';spec=importlib.util.spec_from_file_location('actual_pgn_stats',ps);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
capture=Path('/workspace/.cloud-setup/hosted-results-39325939081-1/hosted-results/pilot/aa/games.pgn');original=capture.read_text();(D/'original-deterministic-AA.pgn').write_bytes(capture.read_bytes());check('actual_original_capture8identity_pass',mod.summarize(original,require_identical_pairs=True)['games']==8)
blocks=[b for b in re.split(r'(?=^\[Event )',original,flags=re.M) if b.strip()];tags,moves=mod.games(blocks[0])[0]
# DERIVED, not an actual new game: preserve actual producer header dialect/result,
# replace only first record body by one different legal root move plus result.
import chess
b=chess.Board(tags['FEN']);alternative=next(m.uci() for m in b.legal_moves if m.uci()!=moves.split()[0]);check('derived_prefix_alternative_legal',chess.Move.from_uci(alternative) in b.legal_moves)
headers='\n'.join(line for line in blocks[0].splitlines() if line.startswith('['));derived=headers+'\n\n1. '+alternative+' '+tags['Result']+'\n\n'+''.join(blocks[1:]);(D/'DERIVED-bookkeeping-move-difference.pgn').write_text(derived)
check('identity_off_accepts_derived_bookkeeping8',mod.summarize(derived,require_identical_pairs=False)['games']==8)
def rejected(text,identity):
 try:mod.summarize(text,require_identical_pairs=identity)
 except ValueError:return True
 return False
check('deterministic_identity_rejects_move_difference',rejected(derived,True));check('timed_identity_off_still_rejects_nonnormal',rejected(derived.replace('[Termination "normal"]','[Termination "time forfeit"]',1),False));check('timed_identity_off_still_rejects_orphan',rejected(''.join(blocks[1:]),False))
for n in ['SKILL.md','scenarios.md']:(D/(n+'.diff')).write_text(''.join(difflib.unified_diff((D/('before-'+n)).read_text().splitlines(True),(S/n).read_text().splitlines(True),fromfile='before/'+n,tofile='after/'+n)))
report={'status':'PASS_STATIC_AND_PURE_DATA_AA_CONTRACT','checks':checks,'check_count':len(checks),'relative_links':links,'prior_proofs_unchanged':len(prior),'existing_validator_reused_as_source':str(R/'validation/strength-skill-cleanup-20261020/validate_skill.py'),'existing_validator_sha256':h(R/'validation/strength-skill-cleanup-20261020/validate_skill.py'),'input_sha256':{str(p):h(p) for p in [S/'SKILL.md',S/'scenarios.md',protocol,producer,ps,capture]},'derived_fixture':'Single different legal root move replaces captured first game body; synthetic bookkeeping control, not a new runtime game/readiness result. Full legality/fault/input gates remain external.','engine_compiler_match_network_git_executions':0,'global_installation':False,'scope':'Repository-local wording/static/data tests only; no causal skill-effectiveness, speed, Elo or full22 readiness claim.'};(D/'APPLICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':len(checks),'links':len(links),'prior_proofs':len(prior)}))

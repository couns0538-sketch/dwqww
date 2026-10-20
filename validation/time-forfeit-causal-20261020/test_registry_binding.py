#!/usr/bin/env python3
"""Exercise real main preflight with data fixtures; Capture is replaced before any executable can run."""
import argparse, importlib.util, json, pathlib, shutil, sys, tempfile, unittest
from unittest import mock
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--runner',required=True,type=pathlib.Path);parser.add_argument('--out',required=True,type=pathlib.Path);args=parser.parse_args()
args.runner=args.runner.resolve();args.out=args.out.resolve();args.out.mkdir(exist_ok=False)
def sha(p):
 import hashlib
 return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
class Registry(unittest.TestCase):
 def check_case(self,mutate):
  with tempfile.TemporaryDirectory(prefix='forge-time-registry-',dir='/tmp') as temp:
   p=pathlib.Path(temp);h=p/'metadata';h.mkdir();source=p/'source';source.mkdir()
   spec=importlib.util.spec_from_file_location('registry_runner',args.runner);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
   orig=REPO/'validation/tt-strength-20261020/final-audit'
   for name in ['game85-baseline-original-input.txt','game85-original-protocol.log.gz','forfeit-exchange.json']:shutil.copyfile(orig/name,p/name)
   engine=p/'engine-not-executable';engine.write_bytes(b'data-only-engine-fixture')
   core=p/'core';core.write_bytes(b'data-only-core-fixture')
   source_record={'baseline_sha':'c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e','source_export':str(source),'instrumented_sha256':{}}
   save(h/'SOURCE.json',source_record)
   build={'status':'PASS_BUILD_ONLY','source_manifest_sha256':sha(h/'SOURCE.json'),'engine':{'path':str(engine),'sha256':sha(engine)},'core_library':{'path':str(core),'sha256':sha(core)}}
   save(h/'BUILD.json',build)
   protocol={'status':'PREPARED_COMPILED_PENDING_ROOT_RESOURCE_CLEARANCE','baseline_sha':source_record['baseline_sha'],'source_manifest_sha256':sha(h/'SOURCE.json'),'source_export':str(source),'build_provenance_sha256':sha(h/'BUILD.json'),'runner_sha256':sha(args.runner),'engine':build['engine'],'core_library':build['core_library'],'original_inputs':{n:{'path':str(p/n),'sha256':sha(p/n)} for n in ['game85-baseline-original-input.txt','game85-original-protocol.log.gz','forfeit-exchange.json']}}
   save(h/'PROTOCOL.json',protocol);clearance=p/'fixture-clearance.json';save(clearance,{'timing_execution_authorized':True,'protocol_sha256':sha(h/'PROTOCOL.json'),'scope':'Unit fixture only; Capture prohibited, no engine authorized.'})
   if mutate:
    with (p/'forfeit-exchange.json').open('a') as f:f.write('\n')
   m.HERE=h;m.INPUT=p/'game85-baseline-original-input.txt';m.SESSION=p/'game85-original-protocol.log.gz';m.ORIGINAL=p/'forfeit-exchange.json';m.processes=lambda:[]
   called=[]
   def blocked_capture(*a,**k):called.append(True);raise RuntimeError('CAPTURE_BLOCKED_BY_DATA_ONLY_TEST')
   m.Capture=blocked_capture
   exc=None
   with mock.patch.object(sys,'argv',[str(args.runner),'--engine',str(engine),'--out',str(p/'output'),'--clearance',str(clearance)]), mock.patch.object(m.os,'sched_setaffinity',lambda *a:None):
    try:m.main()
    except BaseException as e:exc=repr(e)
   result={'mutation':mutate,'capture_reached':bool(called),'exception':exc,'engine_executed':False}
   save(args.out/('mutated.json' if mutate else 'valid.json'),result)
   if mutate:self.assertFalse(called,'Changed preregistered exchange bytes reached Capture instead of preflight rejection')
   else:self.assertTrue(called,'Unchanged input fixture must pass preflight to the blocked Capture control')
 def test_changed_original_exchange_rejected_before_capture(self):self.check_case(True)
 def test_unchanged_input_passes_preflight_to_blocked_capture(self):self.check_case(False)
unittest.main(argv=[sys.argv[0]],verbosity=2)

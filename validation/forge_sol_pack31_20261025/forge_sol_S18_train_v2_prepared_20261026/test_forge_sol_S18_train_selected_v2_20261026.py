import importlib.util
import ast
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

PATH=Path(__file__).with_name('forge_sol_S18_train_selected_v2_20261026.py')
tool=None
if PATH.exists():
    spec=importlib.util.spec_from_file_location('s18_dry_test',PATH)
    tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)

class DryPreparation(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(tool,'S18 source-prepared runner missing')
    def test_import_is_torch_free(self):
        self.assertNotIn('torch',sys.modules)
        self.assertNotIn('numpy',sys.modules)
    def test_five_arms_are_exact(self):
        self.assertEqual(tool.ARMS,{'none':None,'t200':200,'t300':300,'t400':400,'t500':500})
    def test_original_argparse_is_extracted_without_import(self):
        parser=tool.original_parser()
        a=parser.parse_args(['--holdout','h000.pos','--hce-dir','data'])
        self.assertEqual((a.adam_impl,a.dev_scalars,a.order_buffers,a.loss_sync_every),('dml',1,1,128))
        self.assertEqual((a.val_positions,a.min_lr_frac,a.blend_start,a.mmap_data),(4000000,.01,1.,False))
        self.assertNotIn('torch',sys.modules)
    def test_observed_recipe_and_epoch_exception(self):
        plan=tool.source_plan()
        self.assertEqual(plan['observed_f006']['epochs'],48)
        self.assertEqual(plan['effective']['epochs'],2)
        self.assertEqual(plan['effective']['batch_size'],8192)
        self.assertEqual(plan['effective']['lr'],.000707)
        self.assertTrue(plan['effective']['final_full_val'])
        self.assertEqual(plan['effective']['warmup_steps'],300)
    def test_every_arm_uses_identical_seed_and_no_resume(self):
        for name in tool.ARMS:
            args=tool.trainer_argv(Path('/tmp/view')/name,[Path('/tmp/view')/name/'t.pos'],Path('/tmp/newrun')/name)
            parsed=tool.original_parser().parse_args(args)
            self.assertEqual((parsed.seed,parsed.shape,parsed.device,parsed.epochs),(25,256,'cpu',2))
            self.assertTrue(parsed.residual);self.assertIsNone(parsed.resume)
            self.assertFalse(parsed.no_qat);self.assertEqual(parsed.adam_impl,'dml')
    def test_full_label_reports_native_tail(self):
        p=tool.source_plan()
        self.assertEqual(p['native_final_validation'],{'supplied_rows':50000,'evaluated_rows':49152,'dropped_tail_rows':848,'batch_size':8192})
    def test_separate_postscore_covers_every_row_including_tail(self):
        self.assertTrue(callable(getattr(tool,'postscore_ranges',None)),'separate full50000 postscore ranges missing')
        spans=tool.postscore_ranges()
        self.assertEqual([end-begin for begin,end in spans],[8192]*6+[848])
        self.assertEqual([i for begin,end in spans for i in range(begin,end)],list(range(50000)))
        plan=tool.source_plan()['separate_post_training_validation']
        self.assertEqual((plan['rows'],plan['dropped_tail_rows']),(50000,0))
        self.assertEqual(plan['checkpoint_selection'],'FINAL_EPOCH2_PRESELECTED')
    def test_postscore_uses_original_math_and_has_no_weight_update_calls(self):
        self.assertTrue(callable(getattr(tool,'postscore_final_checkpoint',None)),'postscore implementation missing')
        tree=ast.parse(PATH.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='postscore_final_checkpoint')
        calls={n.func.attr for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertTrue({'load_set','make_batch','targets','no_grad'}.issubset(calls))
        self.assertFalse({'step','backward','zero_grad','project_weights','export_forge'}&calls)
    def test_final_epoch_checkpoint_preselected(self):
        self.assertTrue(callable(getattr(tool,'final_checkpoint',None)),'checkpoint preselection missing')
        self.assertEqual(tool.final_checkpoint(Path('/tmp/run'),157666).name,'epoch002-step000000038.pt')
    def test_missing_real_certificate_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'certificate'):
            tool.require_scope('real',{'sample_is_synthetic':False,'arms':{}},None)
    def test_synthetic_cannot_be_labeled_real(self):
        with self.assertRaisesRegex(ValueError,'synthetic'):
            tool.require_scope('real',{'sample_is_synthetic':True,'arms':{}},None)
        self.assertEqual(tool.require_scope('synthetic_pipeline_only',{'sample_is_synthetic':True},None),'PIPELINE_ONLY_SYNTHETIC')
    def test_missing_grant_fails_before_runtime_import(self):
        with self.assertRaisesRegex(ValueError,'root grant'):
            tool.validate_grant(None,Path('/tmp/no-index'),4)
        self.assertNotIn('torch',sys.modules)
    def test_child_output_outside_granted_tmp_tree_rejected(self):
        self.assertTrue(callable(getattr(tool,'validate_paths',None)),'child output grant/path validation missing')
        args=SimpleNamespace(child=True,out=Path('/workspace/input'),arm='none',views=Path('/tmp/x'),scope='synthetic_pipeline_only')
        grant={'out':'/tmp/forge_sol_S18_TRAIN_RUN_20261026/new','scope':args.scope}
        with self.assertRaisesRegex(ValueError,'path|output|grant'):
            tool.validate_paths(args,grant)
    def test_real_copies_preserve_writable_hardlinked_sources(self):
        self.assertTrue(callable(getattr(tool,'validate_copied_view',None)),'copied views must bind exact source inventory')
        root=Path(tempfile.mkdtemp(prefix='S18_dry_fixture_',dir=PATH.parent))
        try:
            original=root/'original';original.mkdir();out=root/'new';out.mkdir()
            for name in ('t.pos','t.hce','h000.pos','h000.hce'):(original/name).write_bytes(('fixture-'+name).encode())
            os.link(original/'h000.pos',original/'hardlink_alias')
            inputs={str(p):tool.fingerprint(p) for p in original.iterdir() if p.name!='hardlink_alias'}
            plans={'none':{'files':[original/'t.pos',original/'t.hce']}}
            with patch.object(tool,'HOLDOUT',original):views=tool.stage_views(out,plans,inputs)
            for source in (original/'t.pos',original/'t.hce',original/'h000.pos',original/'h000.hce'):
                copied=out/'none'/'data'/source.name
                self.assertEqual(copied.read_bytes(),source.read_bytes())
                self.assertFalse(os.path.samefile(copied,source))
                self.assertEqual(copied.stat().st_mode&0o777,0o444)
                self.assertEqual(tool.fingerprint(source),inputs[str(source)])
            with patch.object(tool,'HOLDOUT',original):
                tool.validate_copied_view(views['none'],out/'none',plans['none'],inputs)
                views['none']['train']=[str(out/'none'/'data'/'h000.pos')]
                with self.assertRaisesRegex(ValueError,'train|inventory|copied'):
                    tool.validate_copied_view(views['none'],out/'none',plans['none'],inputs)
        finally:shutil.rmtree(root)

class SelectedControls(unittest.TestCase):
    def test_selected_grant_arms_are_canonical_nonempty(self):
        self.assertTrue(callable(getattr(tool,'selected_arms',None)),'selected grant-arm validation missing')
        self.assertEqual(tool.selected_arms(['none']),['none'])
        self.assertEqual(tool.selected_arms(['t200','t300','t400','t500']),['t200','t300','t400','t500'])
        for bad in [[],['none','none'],['t500','none'],['unknown']]:
            with self.assertRaises(ValueError):tool.selected_arms(bad)
    def test_child_must_be_in_selected_grant(self):
        args=SimpleNamespace(child=True,out=Path('/tmp/forge_sol_S18_TRAIN_RUN_20261026/new/t500'),arm='t500',views=Path('/tmp/forge_sol_S18_TRAIN_RUN_20261026/new/copied_views.json'),scope='synthetic_pipeline_only')
        with self.assertRaises(ValueError):tool.validate_paths(args,{'out':'/tmp/forge_sol_S18_TRAIN_RUN_20261026/new','scope':args.scope,'arms':['none']})
    def test_child_cwd_and_cache_are_new_per_arm(self):
        self.assertTrue(callable(getattr(tool,'child_paths',None)),'per-arm CWD/cache/tmp map missing')
        v=tool.child_paths(Path('/tmp/forge_sol_S18_TRAIN_RUN_20261026/new/none'))
        self.assertEqual(v['cwd'],Path('/tmp/forge_sol_S18_TRAIN_RUN_20261026/new/none/cwd'))
        self.assertEqual(v['env']['TMPDIR'],str(Path('/tmp/forge_sol_S18_TRAIN_RUN_20261026/new/none/tmp')))
        self.assertNotIn('HOME',v['env'])
        self.assertTrue(all(Path(q).is_relative_to('/tmp/forge_sol_S18_TRAIN_RUN_20261026/new/none') for q in v['env'].values()))
    def test_no_trainer_or_optimizer_math_changed(self):
        old=ast.parse(Path('/tmp/forge_sol_S18_TRAIN_PREP_20261026/forge_sol_S18_train_20261026.py').read_text());new=ast.parse(PATH.read_text())
        for name in ['trainer_argv','postscore_ranges','final_checkpoint']:
            a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name)
            b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
    def test_RSS_guard_stops_only_its_new_owned_process(self):
        self.assertTrue(callable(getattr(tool,'RSSGuard',None)),'RSS guard missing')
        class Process:
            pid=123456;returncode=None
            def poll(self):return None
        with patch.object(tool,'read_rss_bytes',return_value=200),patch.object(tool.os,'killpg') as kill:
            p=tool.RSSGuard(Process(),100);p.poll()
        self.assertEqual(p.stop_reason,'RSS_LIMIT');self.assertEqual(p.max_sampled_rss_bytes,200)
        self.assertEqual(kill.call_args.args[0],123456)
    def test_RSS_unavailable_fails_closed(self):
        self.assertTrue(callable(getattr(tool,'RSSGuard',None)),'RSS guard missing')
        class Process:
            pid=123456;returncode=None
            def poll(self):return None
        with patch.object(tool,'read_rss_bytes',side_effect=PermissionError('fixture')),patch.object(tool.os,'killpg'):
            p=tool.RSSGuard(Process(),100);p.poll()
        self.assertEqual(p.stop_reason,'RSS_UNAVAILABLE');self.assertIsNone(p.max_sampled_rss_bytes)
    def test_native_metric_keeps49152_separate(self):
        self.assertTrue(callable(getattr(tool,'native_final_metric',None)))
        line='FINAL FULL HOLDOUT n=49,152: net mse_teacher=0.100000 mse_b0.6=0.200000 mse_b0.8=0.300000 | HCE 0.400000/0.500000/b0.8 0.600000'
        value=tool.native_final_metric(line)
        self.assertEqual((value['evaluated_rows'],value['dropped_tail_rows']),(49152,848))
        self.assertEqual(value['net_MSE']['1.0'],.1)
        for text in [line.replace('49,152','50,000'),line+'\n'+line,'',line.replace('0.100000','nan')]:
            with self.assertRaises(ValueError):tool.native_final_metric(text)
    def test_disk_reserve_refusal_is_before_staging(self):
        self.assertTrue(callable(getattr(tool,'require_disk_reserve',None)))
        with patch.object(tool,'free_disk_bytes',return_value=100):
            with self.assertRaises(ValueError):tool.require_disk_reserve({'minimum_free_disk_bytes':101})
    def test_disk_guard_signals_only_owned_group(self):
        class Process:
            pid=123456;returncode=None
            def poll(self):return None
        with patch.object(tool,'read_rss_bytes',return_value=10),patch.object(tool,'free_disk_bytes',return_value=99),patch.object(tool.os,'killpg') as kill:
            proc=tool.RSSGuard(Process(),100,disk_floor=100);proc.poll()
        self.assertEqual(proc.stop_reason,'DISK_RESERVE');self.assertEqual(kill.call_args.args[0],123456)
    def test_grant_resource_limits_and_single_arm_are_exact(self):
        with tempfile.TemporaryDirectory(prefix='S18_selected_grant_') as temp:
            index=Path(temp)/'fixture_index.json';index.write_text('{}')
            grant={'status':'AUTHORIZED_S18_TRAINING','controller_sha256':tool.sha(PATH),'data_index_sha256':tool.sha(index),
                   'arms':['none'],'cpu':[4],'nice':19,'work_seconds_per_arm':300,'hard_seconds_per_arm':360,
                   'address_space_bytes':4294967296,'rss_limit_bytes':3221225472,'minimum_free_disk_bytes':6979321856,
                   'authorization_reference':'PURE_FIXTURE_NO_RUNTIME'}
            file=Path(temp)/'fixture_grant.json';file.write_text(json.dumps(grant))
            self.assertEqual(tool.validate_grant(file,index,4)['arms'],['none'])
            for key,value in [('rss_limit_bytes',3221225473),('minimum_free_disk_bytes',6979321855),('hard_seconds_per_arm',359),('arms',[])]:
                bad=dict(grant,**{key:value});file.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):tool.validate_grant(file,index,4)
            self.assertNotIn('torch',sys.modules);self.assertNotIn('numpy',sys.modules)
    def test_RSS_exited_process_never_signalled(self):
        self.assertTrue(callable(getattr(tool,'RSSGuard',None)),'RSS guard missing')
        class Process:
            pid=123456;returncode=0
            def poll(self):return 0
        with patch.object(tool,'read_rss_bytes',side_effect=AssertionError('no read after exit')),patch.object(tool.os,'killpg') as kill:
            p=tool.RSSGuard(Process(),100);self.assertEqual(p.poll(),0)
        kill.assert_not_called()

if __name__=='__main__':unittest.main()

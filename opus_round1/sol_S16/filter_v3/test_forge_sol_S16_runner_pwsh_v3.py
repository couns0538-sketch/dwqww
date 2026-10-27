"""Windows runner test (Opus 5.5, 2026-10-27): Sol's one-command fixture from
test_linux_one_command_config_includes_D_and_every_sealed_shard, run through the PowerShell runner
(pwsh -NoProfile -File forge_sol_S16_overlap_runner_v3_20261027.ps1 <config> -Python <this interpreter>).
Sol's report lists the PowerShell/Windows runner as UNVERIFIED; this closes it on the PC. Skipped where pwsh is absent.
Run from this directory: python -I -B -m unittest test_forge_sol_S16_runner_pwsh_v3 -v"""
import json,shutil,subprocess,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import forge_sol_S16_tests_v3_20261027 as sol  # Sol's helpers (setUp, text_shard) via the v3 test file

PWSH=shutil.which('pwsh')

@unittest.skipUnless(PWSH,'pwsh not installed')
class PwshRunnerTest(sol.NewFilterTests):
    def test_windows_pwsh_one_command_config_includes_D_and_every_sealed_shard(self):
        paths={};texts={};ids={}
        for i,stem in enumerate(['D_output','sealed_a','sealed_b','forge_selfplay_013','forge_selfplay_014']):
            line='7k/8/8/8/8/8/{}P{}/K7 w - - 0 1 | 10 | 1'.format(str(i) if i else '',str(7-i) if i<7 else '')
            paths[stem],texts[stem],ids[stem]=self.text_shard(stem,[line],['game-'+str(i)])
        sealed=self.root/'sealed';sealed.mkdir()
        for stem in ('sealed_a','sealed_b'):
            p=sealed/(stem+'.pos');shutil.move(paths[stem],p);p.chmod(0o444);paths[stem]=p
        tm=self.data/'text_map.json';tm.write_text(json.dumps({k:v.name for k,v in texts.items()}))
        gm=self.data/'id_map.json';gm.write_text(json.dumps({k:v.name for k,v in ids.items()}))
        config=self.root/'config.json'
        config.write_text(json.dumps({'d_output_pos':[str(paths['D_output'])],'sealed_pos_dirs':[str(sealed)],
            'holdout_pos':[str(paths['forge_selfplay_013']),str(paths['forge_selfplay_014'])],'hce_dir':str(self.data),
            'out':str(self.root/'runner_out'),'work_dir':str(self.scratch),'text_map':str(tm),'game_id_map':str(gm),
            'ordered_stems':list(paths),'game_id_provenance':'Synthetic authoritative fixture IDs'}))
        command=[PWSH,'-NoProfile','-File',str(sol.ROOT/'forge_sol_S16_overlap_runner_v3_20261027.ps1'),str(config),'-Python',sys.executable]
        result=subprocess.run(command,text=True,capture_output=True,check=False)
        self.assertEqual(result.returncode,0,result.stderr)
        summary=json.loads(result.stdout)
        self.assertEqual(summary['totals'],{'input':3,'kept':3,'dropped':0})
        self.assertEqual({r['stem'] for r in summary['shards']},{'D_output','sealed_a','sealed_b'})
        self.assertTrue(summary['production_eligible'])

def load_tests(loader,tests,pattern):
    return loader.loadTestsFromName('test_windows_pwsh_one_command_config_includes_D_and_every_sealed_shard',PwshRunnerTest) if PWSH else unittest.TestSuite()

if __name__=='__main__':unittest.main()

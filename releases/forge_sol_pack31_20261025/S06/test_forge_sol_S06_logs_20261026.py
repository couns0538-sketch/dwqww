"""Synthetic dialect fixtures, not reconstructed Forge gate logs."""
import unittest
import forge_sol_S06_logs_20261026 as logs

SYNTHETIC = '''Results of Candidate vs Baseline (10+0.1, 1t, 16MB, synthetic.epd):
Games: 4, Wins: 1, Losses: 1, Draws: 2, Points: 2.0 (50.0 %)
Ptnml(0-2): [0, 0, 2, 0, 0], WL/DD Ratio: 1.0
LLR: -0.25 (8.5%) (-2.94, 2.94) [0.00, 10.00]
Finished match
'''

class LogReader(unittest.TestCase):
    def test_explicit_supported_summary(self):
        r = logs.mine_log(SYNTHETIC, 'Candidate', 'Baseline')
        self.assertEqual(r.get('status'), 'PARSED')
        self.assertEqual(r['reported']['wdl'], [1, 2, 1])
        self.assertEqual(r['reported']['pentabins'], [0, 0, 2, 0, 0])
        self.assertEqual(r['reported']['llr']['value'], -0.25)
        self.assertFalse(r['acceptance_authorized'])

    def test_nonfinite_final_llr_never_uses_earlier_finite(self):
        for token in ('nan', '-nan', 'inf', '-inf', 'garbage'):
            r = logs.mine_log(SYNTHETIC + 'LLR: '+token+'\n', 'Candidate', 'Baseline')
            self.assertIsNone(r['reported']['llr']['value'])
            self.assertEqual(r['status'], 'BLOCKED')
            self.assertEqual(r['reported']['llr']['token'], token)

    def test_duplicate_acceptance_is_not_silently_collapsed(self):
        r = logs.mine_log(SYNTHETIC + 'SPRT completed - H1 was accepted\n'*2, 'Candidate', 'Baseline')
        self.assertEqual(len(r['reported']['acceptances']), 2)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_native_decision_not_replaced_by_gaussian(self):
        r = logs.mine_log(SYNTHETIC + 'SPRT completed - H0 was accepted\n', 'Candidate', 'Baseline')
        self.assertEqual(r['reported']['acceptances'][0]['hypothesis'], 'H0')
        self.assertFalse(r['acceptance_authorized'])

    def test_counts_and_pair_totals_must_reconcile(self):
        for bad in (SYNTHETIC.replace('Games: 4', 'Games: 6'),
                    SYNTHETIC.replace('[0, 0, 2, 0, 0]', '[0, 0, 1, 0, 0]')):
            r = logs.mine_log(bad, 'Candidate', 'Baseline')
            self.assertEqual(r['status'], 'BLOCKED')

    def test_cumulative_snapshots_not_summed(self):
        r = logs.mine_log(SYNTHETIC.replace('Finished match\n','') + SYNTHETIC.replace('Games: 4, Wins: 1, Losses: 1, Draws: 2', 'Games: 8, Wins: 2, Losses: 2, Draws: 4').replace('[0, 0, 2, 0, 0]', '[0, 0, 4, 0, 0]'), 'Candidate', 'Baseline')
        self.assertEqual(r['reported']['wdl'], [2, 4, 2])
        self.assertEqual(len(r['snapshots']), 2)
        self.assertEqual(r['status'],'PARSED')

    def test_mixed_match_or_reversed_header_blocked(self):
        for header in ('Results of Other vs Baseline (tc):', 'Results of Baseline vs Candidate (tc):'):
            r = logs.mine_log(SYNTHETIC + header + '\n', 'Candidate', 'Baseline')
            self.assertEqual(r['status'], 'BLOCKED')

    def test_events_and_final_fault_totals_are_separate(self):
        t = '[WARN] fastchess --- Engine Candidate loses on time by 22ms\n[INFO] fastchess --- Player: Candidate\n[INFO] fastchess ---   Timeouts: 1\n[INFO] fastchess ---   Crashed: 0\n'
        r = logs.mine_log(t, 'Candidate', 'Baseline')
        self.assertEqual(r['faults']['reported_player_totals']['Candidate'], {'time_loss': 1, 'crash': 0})
        self.assertEqual(len(r['faults']['events']), 1)
        self.assertIsNone(r['faults']['verified_unique_total'])
        self.assertFalse(r['faults']['clean_proven'])

    def test_normal_process_exit_is_not_a_crash(self):
        r = logs.mine_log('Process exited normally with status 0\n', 'Candidate', 'Baseline')
        self.assertEqual(r['faults']['events'], [])
        self.assertEqual(r['status'], 'UNVERIFIED')

    def test_finished_results_duplicates_and_unknowns(self):
        t = 'Finished game 1 (Candidate vs Baseline): 1-0 {White mates}\nFinished game 2 (Baseline vs Candidate): 1-0 {White mates}\n'
        r = logs.mine_log(t, 'Candidate', 'Baseline')
        self.assertEqual(r['finished']['wdl'], [1, 0, 1])
        self.assertEqual(r['finished']['games'], 2)
        r = logs.mine_log(t+t.splitlines()[0]+'\n', 'Candidate', 'Baseline')
        self.assertEqual(r['finished']['duplicates'], ['1'])
        self.assertEqual(r['status'], 'BLOCKED')

    def test_penta_unrealizable_for_wdl_is_not_accepted(self):
        r = logs.mine_log(SYNTHETIC.replace('[0, 0, 2, 0, 0]', '[0, 0, 0, 0, 2]'), 'Candidate', 'Baseline')
        self.assertEqual(r['status'], 'BLOCKED')

    def test_incomplete_later_summary_does_not_reuse_old_counts(self):
        r = logs.mine_log(SYNTHETIC + 'Results of Candidate vs Baseline (tc):\nGames: 6, Wins: 2, Losses: 1, Draws: 3\n', 'Candidate', 'Baseline')
        self.assertIsNone(r['reported']['pentabins'])
        self.assertEqual(r['reported']['games'], 6)

    def test_decreasing_snapshots_cannot_select_favorable_restart(self):
        later = SYNTHETIC.replace('Games: 4, Wins: 1, Losses: 1, Draws: 2', 'Games: 2, Wins: 2, Losses: 0, Draws: 0').replace('[0, 0, 2, 0, 0]', '[0, 0, 0, 0, 1]')
        r = logs.mine_log(SYNTHETIC.replace('Finished match\n','')+later, 'Candidate','Baseline')
        self.assertEqual(r['status'],'BLOCKED')
        self.assertTrue(any('decreas' in x for x in r['issues']))

    def test_malformed_finished_prefix_cannot_drop_game(self):
        r = logs.mine_log('Finished game 1 (Candidate vs Baseline): 1-0\nFinished game 2 (Baseline vs Candidate): 0-2\n','Candidate','Baseline')
        self.assertEqual(r['status'],'BLOCKED')
        self.assertEqual(len(r['unparsed_records']),1)

    def test_malformed_or_unbound_fault_totals_blocked(self):
        for t in ('Player: Candidate\nTimeouts: NaN\nCrashed: -1\n', 'Timeouts: 1\n', 'Player: Stranger\nCrashed: 1\n'):
            r=logs.mine_log(t,'Candidate','Baseline')
            self.assertEqual(r['status'],'BLOCKED')

    def test_changed_resource_description_not_single_pool(self):
        r=logs.mine_log(SYNTHETIC.replace('Finished match\n','')+SYNTHETIC.replace('1t, 16MB','4t, 256MB'),'Candidate','Baseline')
        self.assertEqual(r['status'],'BLOCKED')

    def test_two_terminal_matches_not_one_experiment(self):
        r=logs.mine_log(SYNTHETIC+SYNTHETIC,'Candidate','Baseline')
        self.assertEqual(r['status'],'BLOCKED')

    def test_player_fault_totals_must_be_cumulative(self):
        r=logs.mine_log('Player: Candidate\nTimeouts: 1\nPlayer: Candidate\nTimeouts: 0\n','Candidate','Baseline')
        self.assertEqual(r['status'],'BLOCKED')

    def test_wins_on_time_fault_dialect_is_retained(self):
        r=logs.mine_log('Finished game 1 (Candidate vs Baseline): 0-1 {Black wins on time}\n','Candidate','Baseline')
        self.assertEqual(r['status'],'BLOCKED')
        self.assertEqual(r['faults']['events'][0]['kind'],'time_loss')

    def test_empty_snapshot_cannot_hide_regression(self):
        old=SYNTHETIC.replace('Finished match\n','')
        later=old.replace('Games: 4, Wins: 1, Losses: 1, Draws: 2','Games: 2, Wins: 2, Losses: 0, Draws: 0').replace('[0, 0, 2, 0, 0]','[0, 0, 0, 0, 1]')
        r=logs.mine_log(old+old.splitlines()[0]+'\n'+later,'Candidate','Baseline')
        self.assertEqual(r['status'],'BLOCKED')

    def test_duplicate_count_fields_never_overwrite_silently(self):
        r=logs.mine_log(SYNTHETIC.replace('Finished match\n','')+'Games: 2, Wins: 2, Losses: 0, Draws: 0\nPtnml(0-2): [0,0,0,0,1]\n','Candidate','Baseline')
        self.assertEqual(r['status'],'BLOCKED')
        self.assertTrue(r['unparsed_records'])

    def test_malformed_player_header_resets_fault_binding(self):
        r=logs.mine_log('Player: Candidate\nTimeouts:0\nPlayer:\nCrashed:0\n','Candidate','Baseline')
        self.assertEqual(r['status'],'BLOCKED')
        self.assertNotIn('crash',r['faults']['reported_player_totals']['Candidate'])

if __name__ == '__main__':
    unittest.main()

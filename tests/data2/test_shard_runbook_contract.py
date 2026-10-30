"""Portable checks for the crew's retained-index runbook contract."""
import os
from pathlib import Path
import re
import unittest


RUNBOOK = Path(os.environ.get('ASTRA_RUNBOOK_PATH',
    str(Path(__file__).resolve().parents[2] / 'docs/ASTRA_CONVERTER_20261030.md')))


class ShardRunbookContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = RUNBOOK.read_text(encoding='utf-8')

    def test_every_retained_index_includes_holdouts_prior_and_current_rows(self):
        self.assertIn('64 * (holdout_rows + prior_retained_rows + current_input_rows) + 1 MiB', self.text)
        self.assertIn('Every retained index remains allocated', self.text)

    def test_completion_records_paths_actual_index_bytes_and_retained_rows(self):
        for field in ('index_path', 'actual_index_bytes', 'actual_output_bytes', 'actual_retained_rows'):
            with self.subTest(field=field):
                self.assertIn('`' + field + '`', self.text)
        self.assertIn('including indexes from earlier attempts', self.text)

    def test_fresh_measurement_and_next_shard_budget_are_explicit(self):
        self.assertIn('Before **each** shard, measure free space again', self.text)
        self.assertIn('fresh_free_bytes >= 32 GiB + next_index_bytes + next_output_bytes', self.text)
        self.assertIn('If that inequality fails, stop before launching the next shard', self.text)

    def test_runbook_has_no_prune_command_and_production_reserve_is_32768(self):
        commands = '\n'.join(re.findall(r'```[^\n]*\n(.*?)```', self.text, flags=re.S))
        self.assertNotIn('--prune-indexes', commands)
        reserves = re.findall(r"--min-free-mb['\"]?(?:,)?\s+['\"]?(\d+)", commands)
        self.assertTrue(reserves, 'production commands must declare the reserve')
        self.assertEqual(set(reserves), {'32768'})
        self.assertIn('separate crew vote', self.text)

    def test_standalone_binpack_roundtrip_explicitly_accepts_gpl3(self):
        commands = re.findall(r'```[^\n]*\n(.*?)```', self.text, flags=re.S)
        roundtrip = [command for command in commands if 'run_1m_roundtrip.py' in command]
        self.assertTrue(roundtrip, 'standalone roundtrip command must remain documented')
        for command in roundtrip:
            self.assertIn('--accept-gpl3', command)


if __name__ == '__main__':
    unittest.main()

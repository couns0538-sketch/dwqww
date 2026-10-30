"""QA Final2 7C: measured probe-log allowance, with live disk guards retained."""
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'tools/data2'))
import convert_dataset as c

class ProbeBudget(unittest.TestCase):
    def test_filtered_rows_charge_128_bytes_and_unfiltered_charge_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp); source=p/'in.txt'
            source.write_text('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 1 | 0.5\n'*20)
            args=c.parser().parse_args(['convert','--input',str(source),'--out',str(p/'out')])
            filtered=c.disk_budget(args, [])
            self.assertEqual(filtered['probe_log_bytes_estimate'], 20*128)
            args.no_filters=True
            unfiltered=c.disk_budget(args, [])
            self.assertEqual(unfiltered['probe_log_bytes_estimate'],0)
            self.assertEqual(filtered['output_bytes_estimate']-unfiltered['output_bytes_estimate'],20*128)

if __name__=='__main__':unittest.main()

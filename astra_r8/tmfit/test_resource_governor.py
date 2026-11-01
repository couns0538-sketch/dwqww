import io
import json
from pathlib import Path
import tempfile
import unittest
import resource_governor as gov


class FakeSamples:
    def __init__(self, values):
        self.values = iter(values)
    def read(self):
        return next(self.values)
    def close(self):
        pass


class GovernorTests(unittest.TestCase):
    def make(self, cpus, free=None):
        samples = [(value, value, 10.0) for value in cpus]
        waits=[]
        controller=gov.Governor(FakeSamples(samples),lambda: gov.MIN_FREE if free is None else free,
                                clock=lambda:10.0,sleep=waits.append,output=io.StringIO())
        return controller,waits

    def test_startup_79_admits_80_waits(self):
        controller,waits=self.make([79])
        controller.checkpoint(start=True)
        self.assertEqual(waits,[])
        controller,waits=self.make([80,79])
        controller.checkpoint(start=True)
        self.assertEqual(waits,[60])

    def test_ongoing_89_admits_90_waits(self):
        controller,waits=self.make([89])
        controller.checkpoint(start=False)
        self.assertEqual(waits,[])
        controller,waits=self.make([90,89])
        controller.checkpoint(start=False)
        self.assertEqual(waits,[60])

    def test_ram_exact_threshold_and_recovery(self):
        controller,waits=self.make([40,40])
        available=iter([gov.MIN_FREE-1,gov.MIN_FREE])
        controller.free_ram=lambda:next(available)
        controller.checkpoint(start=True)
        self.assertEqual(waits,[60])

    def test_missing_stale_metrics_fail_closed(self):
        for cpu,free,stamp in [(None,gov.MIN_FREE,10),(float('nan'),gov.MIN_FREE,10),
                               (30,None,10),(30,gov.MIN_FREE,8)]:
            controller=gov.Governor(FakeSamples([(cpu,cpu,stamp)]),lambda:free,
                                    clock=lambda:10,sleep=lambda _:self.fail('must fail closed'),output=io.StringIO())
            with self.subTest(cpu=cpu,free=free,stamp=stamp):
                with self.assertRaises(RuntimeError):controller.checkpoint()

    def test_peak_since_previous_boundary_is_not_lost(self):
        controller=gov.Governor(FakeSamples([(50,95,10),(50,50,10)]),lambda:gov.MIN_FREE,
                                clock=lambda:10,sleep=lambda seconds:self.assertEqual(seconds,60),output=io.StringIO())
        controller.checkpoint(start=False)
        self.assertEqual(controller.snapshot()['waits'],1)

    def test_logs_are_append_only_and_new_path_required(self):
        with tempfile.TemporaryDirectory() as temp:
            controller,waits=self.make([79,90,89])
            controller.checkpoint(start=True)
            controller.attach(Path(temp))
            first=(Path(temp)/'governor.jsonl').read_bytes()
            controller.checkpoint(start=False)
            self.assertTrue((Path(temp)/'governor.jsonl').read_bytes().startswith(first))
            controller.close()
            other,_=self.make([1])
            with self.assertRaises(FileExistsError):other.attach(Path(temp))
            rows=[json.loads(line) for line in (Path(temp)/'governor.jsonl').read_text().splitlines()]
            self.assertEqual([row['action'] for row in rows],['admit','wait','admit'])

    def test_cpu_formula_excludes_idle_already_in_kernel(self):
        self.assertEqual(gov.percent_from_times((100,200),(120,300)),80)
        with self.assertRaises(RuntimeError):gov.percent_from_times((100,200),(100,200))


if __name__=='__main__':unittest.main()

"""Read-only two-sample CPU3 admission observation; never starts another job."""
import argparse
import datetime
import json
import sys

sys.path.insert(0, 'D:/a10/pydeps')
import psutil

parser = argparse.ArgumentParser()
parser.add_argument('--threads', type=int, choices=[1], required=True)
parser.parse_args()
proc = psutil.Process()
if proc.nice() != psutil.IDLE_PRIORITY_CLASS or proc.cpu_affinity() != [3]:
    raise RuntimeError('Idle CPU3-only sampler required')
samples = []
for index in range(2):
    per_cpu = psutil.cpu_percent(interval=3, percpu=True)
    samples.append({'sample': index + 1, 'seconds': 3, 'cpu3': per_cpu[3],
                    'host_mean': sum(per_cpu) / len(per_cpu),
                    'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({'status': 'PASS' if all(s['cpu3'] < 30 and s['host_mean'] < 95 for s in samples) else 'WAIT',
                  'policy': 'CPU3<30%, host mean<95% in both separate3s observations; caller must inspect before launching',
                  'samples': samples}, indent=2))

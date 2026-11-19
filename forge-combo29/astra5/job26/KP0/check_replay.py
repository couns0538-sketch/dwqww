"""Replay the committed Job 23 K23-1 arm with nc, retaining its original S driver and records."""
import argparse
from hashlib import sha256
import importlib.util
import os
from pathlib import Path

ENGINE_SHA = '9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3'
DRIVER_SHA = '92e54810e5a8c6516b8be79df58bd61877e415ec2af7174924e3f8c60b87adb1'
ARCHIVE_SHA = 'b85eb5f01afbbb12771b1a8cf5c579f3c6db3873fa0779f9fce94ca0c5b25a76'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('job23', 'nc', 'net', 'pc20', 'out'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--claim', required=True, help='ISO-8601 time for the measurement deadline')
    args = parser.parse_args()
    script = args.job23 / 'driver/selfplay.py'
    if sha256(script.read_bytes()).hexdigest() != DRIVER_SHA:
        raise ValueError('Job 23 driver differs from checked-in copy')
    archives = [(args.job23 / a / 'records.txt').read_bytes() for a in ('K23-1', 'K23-2')]
    if archives[0] != archives[1] or sha256(archives[0]).hexdigest() != ARCHIVE_SHA:
        raise ValueError('archived Job 23 repeats failed equality/identity check')
    os.environ.update(JOB23_NET=str(args.net.resolve()), JOB23_PC20=str(args.pc20.resolve()), JOB23_CLAIM=args.claim)
    spec = importlib.util.spec_from_file_location('job23_driver', script)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    driver.ROOT = args.out.resolve()
    driver.RESULTS = driver.ROOT / 'results'
    driver.BUILDS['r15d'] = (args.nc.resolve(), ENGINE_SHA)
    driver.ROOT.mkdir(parents=True, exist_ok=False)
    if driver.run('K23-1') != 0:
        raise RuntimeError('driver failed')
    actual = (driver.RESULTS / 'K23-1/records.txt').read_bytes()
    rows = [line.split() for line in actual.splitlines()]
    na = sum(row[3] == b'NA' for row in rows)
    nodes = sum(int(row[3]) for row in rows if row[3] != b'NA')
    games = len(set(row[0] for row in rows))
    passed = actual == archives[0] and (games,len(rows),na,nodes) == (10,1183,0,4863663)
    summary = (f"Job 23 driver sha256 {DRIVER_SHA}\n"
               f"actual sha256 {sha256(actual).hexdigest()}\narchived K23-1 and K23-2 sha256 {ARCHIVE_SHA}\n"
               f"games {games}\nrecords {len(rows)}\nNA {na}\nnodes {nodes}\n"
               f"actual equals archived K23-1 and K23-2 byte for byte {actual == archives[0]}\n"
               f"{'PASS' if passed else 'FAIL'}\n")
    (driver.ROOT/'comparison.txt').write_text(summary)
    print(summary, end='')
    if not passed:
        raise ValueError('KP0(c) did not reproduce archived K23')
if __name__ == '__main__':
    main()

"""Run the complete datafilter and R13 suites with retained collection receipts."""
import json
import os
from pathlib import Path
import sys
from run_policy import free_guard, write_json

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ['TEMP']).parent
free_guard(256*1024*1024)
import pytest

class Evidence:
    def __init__(self):
        self.results=[]

    def pytest_collection_finish(self,session):
        write_json(OUT/'collection.json',dict(count=len(session.items),nodeids=[item.nodeid for item in session.items]))

    def pytest_runtest_logreport(self,report):
        if report.when=='call' or report.failed or report.skipped:
            self.results.append(dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,duration=report.duration,
                                     kind='subtest' if hasattr(report,'context') else 'test'))

    def pytest_sessionfinish(self,session,exitstatus):
        write_json(OUT/'test_results.json',dict(exitstatus=int(exitstatus),collected=session.testscollected,failed=session.testsfailed,results=self.results))

arguments=[str(ROOT/'astra_r8'/'datafilter'/'tests'),str(ROOT/'tests'),'-q','-p','no:cacheprovider',
           '--basetemp',str(OUT/'pytest'),'--log-file',str(OUT/'pytest-logging.log')]
print(json.dumps(dict(command=[sys.executable,'-m','pytest',*arguments],cpu=os.environ.get('ASTRA_R13_CPU'),threads=1)),flush=True)
exit_code=pytest.main(arguments,plugins=[Evidence()])
free_guard()
raise SystemExit(exit_code)

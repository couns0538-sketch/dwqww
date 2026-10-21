"""Preserve public GitHub observations; never infer game counts from step status."""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
BASE = 'https://github.com/couns0538-sketch/dwqww'

class Steps(HTMLParser):
    def __init__(self):
        super().__init__()
        self.steps = []
    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if 'data-name' in attributes and 'data-number' in attributes:
            self.steps.append({k:v for k,v in attributes.items() if k.startswith('data-')})

def main():
    launch = json.loads((ROOT/'publication-attempt1/LAUNCH.json').read_text())
    now = datetime.now(timezone.utc)
    out = ROOT/'live-monitor'/now.strftime('%Y%m%d-%H%M%S')
    out.mkdir(parents=True, exist_ok=False)
    observation = {'utc':now.isoformat(), 'payload':launch['payload_commit'],
        'branch':launch['target_branch'], 'authentication':'none', 'requests':[],
        'games_observed':None, 'elo_estimate':None,
        'scope':'Public workflow metadata only; a running combined step does not establish any readiness pass or played game.'}
    def fetch(name, url):
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Forge-validation'}),timeout=30) as response:
            data = response.read()
            observation['requests'].append({'url':url,'status':response.status,'bytes':len(data),
                'sha256':hashlib.sha256(data).hexdigest()})
        (out/name).write_bytes(data)
        return data.decode('utf-8')
    actions = fetch('actions.html',BASE+'/actions?'+urllib.parse.urlencode({'query':'branch:'+launch['target_branch']}))
    run_ids = list(dict.fromkeys(re.findall(r'/couns0538-sketch/dwqww/actions/runs/(\d+)',actions)))
    observation['listed_run_ids'] = run_ids
    for run_id in run_ids[:3]:
        run = fetch('run-'+run_id+'.html',BASE+'/actions/runs/'+run_id)
        commits = sorted(set(re.findall(r'/couns0538-sketch/dwqww/commit/([0-9a-f]{40})',run)))
        if launch['payload_commit'] not in commits:
            continue
        observation.update(run_id=run_id, run_url=BASE+'/actions/runs/'+run_id,
            payload_link_verified=True, linked_commits=commits)
        jobs = list(dict.fromkeys(re.findall(r'/actions/runs/'+run_id+r'/job/(\d+)',run)))
        observation['job_ids'] = jobs
        if jobs:
            job = fetch('job-'+jobs[0]+'.html',BASE+'/actions/runs/'+run_id+'/job/'+jobs[0])
            parser=Steps();parser.feed(job)
            observation['steps'] = parser.steps
        break
    (out/'OBSERVATION.json').write_text(json.dumps(observation,indent=2)+'\n')
    (ROOT/'live-monitor/LATEST-OBSERVATION.json').write_text(json.dumps({
        'path':out.relative_to(ROOT).as_posix(),'record':observation},indent=2)+'\n')
    print(json.dumps(observation,indent=2))

if __name__ == '__main__':
    main()

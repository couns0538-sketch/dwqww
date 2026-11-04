import json,subprocess,sys
from pathlib import Path
child=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(6)'],stdout=sys.stdout,stderr=sys.stderr)
Path('D:\\a14\\evidence\\test_logs\\r14\\qc\\launcher-cap-green02\\pytest\\test_exited_child_cannot_leave0\\descendant.json').write_text(json.dumps(dict(pid=child.pid)))

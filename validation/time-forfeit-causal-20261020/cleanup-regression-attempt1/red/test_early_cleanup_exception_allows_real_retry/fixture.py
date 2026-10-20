#!/workspace/.cloud-setup/venv/bin/python

import os, signal
signal.signal(signal.SIGTERM, signal.SIG_IGN)

os.write(1, b'fixture-ready\n')
while True:
    signal.pause()

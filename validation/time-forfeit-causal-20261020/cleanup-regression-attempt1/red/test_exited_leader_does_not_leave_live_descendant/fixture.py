#!/workspace/.cloud-setup/venv/bin/python

import os, signal
signal.signal(signal.SIGTERM, signal.SIG_IGN)

read_fd, write_fd = os.pipe()
child = os.fork()
if child:
    os.close(write_fd)
    os.read(read_fd, 1)
    os.close(read_fd)
    os._exit(0)
os.close(read_fd)
os.write(write_fd, b'R')
os.close(write_fd)

os.write(1, b'fixture-ready\n')
while True:
    signal.pause()

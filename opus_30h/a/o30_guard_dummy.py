"""o30_guard_dummy.py <seconds> <beats file> - test child for the guard (CR item 9): spins on one CPU and writes one
heartbeat line per second (wall time) until <seconds> of wall time have passed, then exits by itself."""
import sys
import time

end = time.time() + float(sys.argv[1])
last = 0.0
with open(sys.argv[2], 'a', encoding='utf-8', newline='\n') as f:
    while time.time() < end:
        if time.time() - last >= 1.0:
            last = time.time()
            f.write(time.strftime('%H:%M:%S') + '\n')
            f.flush()
print('dummy done')

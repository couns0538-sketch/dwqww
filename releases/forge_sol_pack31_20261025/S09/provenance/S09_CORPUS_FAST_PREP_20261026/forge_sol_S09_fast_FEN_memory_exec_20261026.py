"""Set a 4GiB address-space limit, then exec only the supplied owned command."""
import os
import resource
import sys
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
os.execv(sys.argv[1],sys.argv[1:])

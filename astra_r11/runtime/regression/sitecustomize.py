"""Audit guard for normal Python test children via the explicit PYTHONPATH.

Native compiler children and Python -I/-S bypass this hook; neither is a
sandbox. Reviewed regression Python child commands use neither flag.
"""
import os
import sys
from path_guard import audit_open as child_io_guard


sys.addaudithook(child_io_guard)
os.environ['ASTRA_R11_CHILD_IO_GUARD'] = '1'

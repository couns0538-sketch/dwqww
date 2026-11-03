"""Inherited R13 Python child policy; actual native dependencies stay read-only."""
import os
import sys
sys.dont_write_bytecode=True
if os.environ.get('ASTRA_R13_CPU') is not None:
    from run_policy import install_audit_fence
    install_audit_fence()

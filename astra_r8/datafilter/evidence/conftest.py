"""Archived execution scripts are evidence, not importable pytest test modules.

The runnable correctness suite lives in ../tests. Keep original archived bytes
unchanged and exclude Python snapshots throughout this evidence directory.
"""

collect_ignore_glob = ['*.py', '**/*.py']

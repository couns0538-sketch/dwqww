#!/usr/bin/env python3
"""test_runner_vacuous.py -- takes deepseek6 long56's fuzzuci56.py VERBATIM except the
sequence file path, and runs it against the PLANTED fake engine whose every bestmove is
illegal for the position. If its "illegal bestmoves" counter stays 0, the classifier in
that runner is vacuous.

Usage: test_runner_vacuous.py EXE OUTDIR SEQSFILE
"""
import sys
# read the original runner source and substitute only the sequence path
src = open(sys.argv[1].replace('x','x') if False else '/tmp/ds6/long56/fuzzuci56.py').read()
src = src.replace('/tmp/uci56_seqs.txt', sys.argv[3])
exe = sys.argv[1]
outdir = sys.argv[2]
sys.argv = [sys.argv[0], exe, outdir]
exec(compile(src, '<fuzzuci56>', 'exec'), {'__name__': '__main__'})

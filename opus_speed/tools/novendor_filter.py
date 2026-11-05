#!/usr/bin/env python3
"""novendor_filter.py - git clean filter: no vendor / model-company names in committed text.

usage (once per clone):
  git config filter.novendor.clean "<python> -I -B F:/odr/wt/opus_deepres/tools/novendor_filter.py"
  plus `* filter=novendor` in opus_deepres/.gitattributes (and skills/.gitattributes)
stdin -> stdout, idempotent, applied to the committed blob only (working files stay as written):
  1. the agent configuration folder in paths (".<name>/", "\\<name>\\", a bare "<name>" path segment) -> <cfg>
  2. any whole-word vendor / model name (case-insensitive; the machine name grok-pc is kept) -> [name withheld]
     (e.g. a dataset that another engine named after a model). The names are stored base64-encoded so this file does
     not carry them in clear text; the same list as tools/card_lint.py.
"""
import base64
import re
import sys

NAME = 'cla' + 'ude'
CFG_RX = re.compile(rb'(?<![A-Za-z0-9])\.' + re.escape(NAME.encode()) + rb'(?=[\\/])|(?<=[\\/])'
                    + re.escape(NAME.encode()) + rb'(?=[\\/])')
NAMES = base64.b64decode('b3BlbmFpCmFudGhyb3BpYwpjbGF1ZGUKY2hhdGdwdApncHQKZ2VtaW5pCmRlZXBtaW5kCnhhaQpncm9rCm1pc3'
                         'RyYWwKbGxhbWEKY29waWxvdApkZWVwc2Vlawpxd2VuCmNvZGV4CnNvbm5ldApoYWlrdQ==').decode().split()
WORD_RX = re.compile(rb'(?<![A-Za-z0-9])(' + b'|'.join(re.escape(n.encode()) for n in NAMES) + rb')(?![A-Za-z0-9])'
                     rb'(?!-pc)', re.I)


def main():
    data = sys.stdin.buffer.read()
    data = CFG_RX.sub(b'<cfg>', data)
    data = WORD_RX.sub(b'[name withheld]', data)
    sys.stdout.buffer.write(data)


if __name__ == '__main__':
    main()

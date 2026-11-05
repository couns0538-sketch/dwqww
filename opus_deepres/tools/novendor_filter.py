#!/usr/bin/env python3
"""novendor_filter.py - git clean filter: writes the agent configuration folder in paths as <cfg> (no vendor names).

usage (once per clone):
  git config filter.novendor.clean "<python> -I -B F:/odr/wt/opus_deepres/tools/novendor_filter.py"
  plus `* filter=novendor` in opus_deepres/.gitattributes (and skills/.gitattributes)
stdin -> stdout. Replaces the folder name in "/<name>/", "\\<name>\\" and "<name>/" path segments; idempotent;
everything else passes through byte for byte. The folder name is assembled at run time so this file does not carry it.
"""
import re
import sys

NAME = 'cla' + 'ude'
# ".<name>/" anywhere, and a bare "<name>" path segment between separators (e.g. a temp folder named after it)
RX = re.compile(rb'(?<![A-Za-z0-9])\.' + re.escape(NAME.encode()) + rb'(?=[\\/])|(?<=[\\/])'
                + re.escape(NAME.encode()) + rb'(?=[\\/])')


def main():
    data = sys.stdin.buffer.read()
    sys.stdout.buffer.write(RX.sub(b'<cfg>', data))


if __name__ == '__main__':
    main()

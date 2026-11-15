#!/bin/sh
{ printf 'setoption name AspFailHighReduce value 1\nsetoption name AspFailHighMaxReduce value 3\n'; cat; } | /tmp/forge_packc28/build/forge

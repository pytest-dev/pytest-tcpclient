#!/usr/bin/env bash

# This is a generic test script. It's behaviour can be modified by passing
# in arguments that will be passed to `pytest`. See `_test.sh` for an example.

set -e
set -u

export PYTHONPATH=src

#no_style=

pytest_args=()

for i in "$@"; do
    case $i in
    #--no-style) no_style=true;;
    *) pytest_args+=("$i");;
    esac
done

#if [ -z $no_style ]; then
#    # See setup.cfg for further configuration of pycodestyle
#    pycodestyle src tests conftest.py
#fi

python -m pytest \
    --log-cli-format "[%(asctime)s.%(msecs)s][%(name)s][%(funcName)s]: %(message)s" \
    --cov src --cov-report term-missing \
    -rf -s "${pytest_args[@]}"

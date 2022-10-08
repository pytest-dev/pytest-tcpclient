#!/usr/bin/env bash

# This is a generic test script. It's behaviour can be modified by passing
# in arguments that will be passed to `pytest`. See `_test.sh` for an example.

set -e
set -u

export PYTHONPATH=src

pytest_args=()

python -m pytest \
    --log-cli-format "[%(asctime)s.%(msecs)s][%(name)s][%(funcName)s]: %(message)s" \
    --cov src --cov-report term-missing \
    -rf -s "${@}"

#!/usr/bin/env bash

# This is a generic test script. It's behaviour can be modified by passing
# in arguments that will be passed to `pytest`.

set -e
set -u

export PYTHONPATH=src

# We're using `--cov-append` below so we have to erase previous coverage data
coverage erase

# For configuration of `pytest-cov`, see the following:
#
#   . https://pytest-cov.readthedocs.io/en/latest/plugins.html
#

export COV_CORE_SOURCE=src
export COV_CORE_CONFIG=.coveragerc
export COV_CORE_DATAFILE=.coverage.eager

python -m pytest \
    --color=yes \
    --log-cli-format "[%(asctime)s.%(msecs)s][%(name)s][%(funcName)s]: %(message)s" \
    --cov src --cov-report term-missing --cov-append \
    -rf \
    "${@}"

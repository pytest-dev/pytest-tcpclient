=========
Changelog
=========

0.7.24 (2022-11-11)
===================

Adding `CHANGELOG.rst`

- Closes `https://github.com/andersglindstrom/pytest-tcpclient/issues/65`

0.7.23 (2022-11-11)
===================

Removed `license.file` from `pyproject.toml` because the license _contents_ were being
included in the `pypi` page but we just want the license `name`. The license name is
already defined in the Trove classifiers and is now reported correctly on `pypi`.

- Closes `https://github.com/andersglindstrom/pytest-tcpclient/issues/64`

0.7.22 (2022-10-24)
===================

The `github` `build` workflow used to trigger on `push` but now trigger on `pull_request`.

- Closes `https://github.com/andersglindstrom/pytest-tcpclient/issues/56`

0.7.21 (2022-10-24)
===================

Added `.github/workflows/publish.yml` that publishes the package when a new tag on
`main` branch is created.

0.7.20 (2022-10-24)
===================

Build system config files have been rationalised. In particular, `setup.cfg` has been
removed and all build config now resides in `pyproject.toml`

- Closes `https://github.com/andersglindstrom/pytest-tcpclient/issues/47`

0.7.19 (2022-10-23)
===================

`setuptools_scm` is now being used to generate package version number

- Closes `https://github.com/andersglindstrom/pytest-tcpclient/issues/43`

Added fail-through message to `plugin.py::interpret_error` to report uninterpreted
errors.

0.7.18 (2022-10-22)
===================

* Improved `tox` configuration

  * It now invokes `build_scripts/run_tests.sh` to achieve consistency with other build
    tools

* 100% test coverage has been achieved

0.6.0 (2022-10-12)
===================

First release of `pytest-tcpclient`. Previously, it was know as `pytest-mocktcp`

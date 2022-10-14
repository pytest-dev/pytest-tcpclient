.DEFAULT_GOAL := style_and_test

PYPY_README := pypi/README.rst
GITHUB_README := .github/README.rst

message = @echo "\033[1;38;5:123m$1\033[0m"

.PHONY: verify_active_venv
verify_active_venv:
	$(call message,Checking that virtual environment is active...)
	@if [ -z "${VIRTUAL_ENV}" ]; then \
		echo "Virtual environment is not active. Please activate it and try again."; \
		exit 1; \
	fi

.make/venv_refreshed: setup.cfg pyproject.toml requirements.txt | verify_active_venv
	python -m pip install -v -r requirements.txt
	python -m pip install -v -e .
	mkdir -p ${@D}
	touch $@

.PHONY: style_and_test
style_and_test:
	$(MAKE) style
	$(MAKE) test

.PHONY: refresh_env
refresh_env: .make/venv_refreshed $(GITHUB_README)

.PHONY: test
test: refresh_env
	build_scripts/run_tests.sh tests

.PHONY: testone
testone: refresh_env
	pytest --log-cli-level INFO --last-failed tests/pytest_tcpclient/test_plugin.py::test_second_connection_causes_failure

.PHONY: testlf
testlf: refresh_env
	build_scripts/run_tests.sh --log-cli-level INFO --last-failed tests

.PHONY: run_examples
run_examples: refresh_env
	pytest examples

.PHONY: clean
clean:
	rm -rf build dist .pytest_cache .tox .make .coverage docs
	find . -name __pycache__ | xargs rm -rf
	find . -name '*.egg-info' | xargs rm -rf

.PHONY: distclean
distclean: clean
	rm -rf venv

.PHONY: style
style: refresh_env
	pycodestyle src tests

#------------------------------------------------------------------------------
# tox

tox_initialised := .make/tox_initialised

.PHONY: tox
tox: ${tox_initialised} refresh_env
	tox

${tox_initialised}: tox.ini refresh_env
	$(call message,Building tox environment...)
	mkdir -p ${@D}
	tox -r --notest
	touch $@

#------------------------------------------------------------------------------
# distribution

.PHONY: dist
dist: setup.cfg setup.py ${PYPY_README} refresh_env
	-rm -rf dist
	$(call message,Building distributions...)
	python3 -m build

#------------------------------------------------------------------------------
# testpypi
.PHONY: publish_to_testpypi
publish_to_testpypi: dist refresh_env
	$(call message,Publishing to testpypi...)
	twine upload --repository testpypi dist/*

#------------------------------------------------------------------------------
# pypi
.PHONY: publish
publish: dist refresh_env
	$(call message,Publishing to pypi...)
	twine upload --repository pypi dist/*

#------------------------------------------------------------------------------
# Example files

example_files := $(shell find examples)

#------------------------------------------------------------------------------
# Generating README.html for preview

README.html: README.rst $(example_files)
	$(call message,Generating $@...)
	rst2html.py $< $@

#------------------------------------------------------------------------------
# `pypi` and `github` don't honour `include` directives. We generate a flattened
# version of `docs/README.rst`

$(PYPY_README): README.rst $(example_files)
	$(call message,Generating $@...)
	mkdir -p $(@D)
	rm -f $@
	rst_include include $< $@

$(GITHUB_README): README.rst $(example_files)
	$(call message,Generating $@...)
	mkdir -p $(@D)
	rm -f $@
	rst_include include $< $@

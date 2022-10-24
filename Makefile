.DEFAULT_GOAL := style_and_test

GITHUB_README_RST := .github/README.rst
GITHUB_README_HTML := .github/README.html

message = @echo "\033[1;38;5:123m$1\033[0m"

.PHONY: verify_active_venv
verify_active_venv:
	$(call message,Checking that virtual environment is active...)
	@if [ -z "${VIRTUAL_ENV}" ]; then \
		echo "Virtual environment is not active. Please activate it and try again."; \
		exit 1; \
	fi

.make/venv_refreshed: setup.cfg pyproject.toml dev_dependencies.txt | verify_active_venv
	python -m pip install -v ".[dev]"
	python -m pip install -v -e .
	mkdir -p ${@D}
	touch $@

.PHONY: style_and_test
style_and_test:
	$(MAKE) style
	$(MAKE) test

.PHONY: refresh_env
refresh_env: .make/venv_refreshed

.PHONY: test
test: | refresh_env
	build_scripts/run_tests.sh tests

.PHONY: testone
testone: | refresh_env
	build_scripts/run_tests.sh tests/pytest_tcpclient/test_plugin.py::test_second_connection_causes_failure

.PHONY: testlf
testlf: | refresh_env
	build_scripts/run_tests.sh --last-failed tests

.PHONY: run_examples
run_examples: refresh_env
	pytest examples

.PHONY: clean
clean:
	rm -rf build dist .pytest_cache .tox .make .coverage examples_output
	find . -name __pycache__ | xargs rm -rf
	find . -name '*.egg-info' | xargs rm -rf
	$(MAKE) -C docs clean

.PHONY: distclean
distclean: clean
	rm -rf venv

.PHONY: style
style: | refresh_env
	pycodestyle src tests

#------------------------------------------------------------------------------
# tox

tox_initialised := .make/tox_initialised

.PHONY: tox
tox: ${tox_initialised} | refresh_env
	tox

${tox_initialised}: tox.ini | refresh_env
	$(call message,Building tox environment...)
	mkdir -p ${@D}
	tox -r --notest
	touch $@

#------------------------------------------------------------------------------
# distribution

.PHONY: dist
dist: setup.cfg setup.py $(GITHUB_README_RST) | refresh_env
	-rm -rf dist
	$(call message,Building distributions...)
	python3 -m build
	twine check dist/*

#------------------------------------------------------------------------------
# testpypi
.PHONY: publish_to_testpypi
publish_to_testpypi: dist | refresh_env
	$(call message,Publishing to testpypi...)
	twine upload --repository testpypi dist/*

#------------------------------------------------------------------------------
# pypi
.PHONY: publish
publish: dist | refresh_env
	$(call message,Publishing to pypi...)
	twine upload --verbose --repository pypi dist/*

#------------------------------------------------------------------------------
# html
.PHONY: html
html:
	$(MAKE) -C docs html

readme_example_files := \
	examples/test_hello.py \
	examples/test_expect_bytes_times_out.py

readme_example_output_files := \
	$(patsubst examples/%.py,examples_output/%.txt,$(readme_example_files))

GITHUB_README_INPUT_FILES := \
	GITHUB_README_TEMPLATE.rst \
	$(readme_example_files) \
	$(readme_example_output_files)

$(GITHUB_README_RST): $(GITHUB_README_INPUT_FILES) | refresh_env
	$(call message,Generating $@...)
	@mkdir -p $(@D)
	@rm -f $@
	@rst_include include $< $@

$(GITHUB_README_HTML): $(GITHUB_README_RST) | refresh_env
	$(call message,Generating $@...)
	@rst2html.py $< $@

examples_output/%.txt: examples/%.py | refresh_env
	$(call message,Generating $@...)
	@mkdir -p $(@D)
	@# The following construct is to ignore and suppress deliberate test errors
	@pytest $< > $@ || true

.PHONY: readme
readme: $(GITHUB_README_RST)

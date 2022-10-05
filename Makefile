.DEFAULT_GOAL := style_and_test

message = @echo "\033[1;38;5:123m$1\033[0m"

.PHONY: verify_active_venv
verify_active_venv:
	$(call message,Checking that virtual environment is active...)
	@if [ -z "${VIRTUAL_ENV}" ]; then \
		echo "Virtual environment is not active. Please activate it and try again."; \
		exit 1; \
	fi

.make/venv_refreshed: requirements.txt dev_requirements.txt | verify_active_venv
	python -m pip install -r dev_requirements.txt
	python -m pip install -e .
	mkdir -p ${@D}
	touch $@

.PHONY: style_and_test
style_and_test:
	$(MAKE) style
	$(MAKE) test

.PHONY: refresh_venv
refresh_venv: .make/venv_refreshed

.PHONY: test
test: refresh_venv
	scripts/run_tests.sh --log-cli-level INFO tests
	#scripts/run_tests.sh --log-cli-level DEBUG tests/test_mocktcp.py::test_no_remaining_sent_data

.PHONY: testlf
testlf: refresh_venv
	scripts/run_tests.sh --log-cli-level INFO --last-failed tests

.PHONY: distclean
distclean:
	rm -rf .make

.PHONY: style
style: refresh_venv
	pycodestyle src tests

tox_initialised := .make/tox_initialised

.PHONY: tox
tox: ${tox_initialised} refresh_venv
	tox

${tox_initialised}: tox.ini refresh_venv
	$(call message,Building tox environment...)
	mkdir -p ${@D}
	tox -r --notest
	touch $@

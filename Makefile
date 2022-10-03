.DEFAULT_GOAL := test

.make/venv_refreshed: requirements.txt dev_requirements.txt
	@if [ -z "${VIRTUAL_ENV}" ]; then \
		echo "Virtual environment is not active. Please activate it and try again."; \
		exit 1; \
	fi
	python -m pip install -r requirements.txt
	python -m pip install -r dev_requirements.txt
	mkdir -p ${@D}
	touch $@

.PHONY: refresh_venv
refresh_venv: .make/venv_refreshed

.PHONY: test
test: | refresh_venv
	scripts/run_tests.sh --log-cli-level INFO tests
	#scripts/run_tests.sh --log-cli-level DEBUG tests/test_mocktcp.py::test_no_remaining_sent_data

.PHONY: testlf
testlf: | refresh_venv
	scripts/run_tests.sh --log-cli-level INFO --last-failed tests

.PHONY: distclean
distclean:
	rm -rf .make

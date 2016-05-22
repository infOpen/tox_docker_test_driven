clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr reports/

test-all:
	tox

test-env:
ifndef TOXENV
	$(error TOXENV is undefined)
endif
	tox -e "${TOXENV}"

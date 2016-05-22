clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr reports/

test:
	tox

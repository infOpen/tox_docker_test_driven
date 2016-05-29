clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr reports/

test-all:
	tox

test-ansible19:
	-@/usr/bin/docker rm -f py27-ansible19-trusty py27-ansible19-xenial


test-env:
ifndef TOXENV
	$(error TOXENV is undefined)
endif
ifndef DOCKER_IMAGE
	$(error DOCKER_IMAGE is undefined)
endif
	tox -e "${TOXENV}"

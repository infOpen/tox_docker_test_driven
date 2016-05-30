"""
Role tests
"""
import pytest

# Not wokg :/
# To mark all the tests as destructive:
# pytestmark = pytest.mark.destructive

# To run all the tests on given docker images:
pytestmark = pytest.mark.docker_images('infopen/ubuntu-trusty-ssh')
#pytestmark = pytest.mark.docker_images('infopen/ubuntu-trusty-ssh',
#                                       'infopen/ubuntu-xenial-ssh')

# Both
# pytestmark = [
#     pytest.mark.destructive,
#     pytest.mark.docker_images("debian:jessie", "centos:7")
# ]


def test_foo(User):
    assert User().name == 'root'

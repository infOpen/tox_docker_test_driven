import pytest

# To mark all the tests as destructive:
# pytestmark = pytest.mark.destructive

# To run all the tests on given docker images:
# pytestmark = pytest.mark.docker_images("debian:jessie", "centos:7")

# Both
# pytestmark = [
#     pytest.mark.destructive,
#     pytest.mark.docker_images("debian:jessie", "centos:7")
# ]


# This test will run on default image (debian:jessie)
@pytest.fixture(scope="module", autouse=True)
@pytest.mark.docker_images('infopen/ubuntu-trusty-ssh', 'infopen/ubuntu-xenial-ssh')
def provision(Docker, LocalCommand):
    Docker.set_authorized_keys()
    Docker.provision_as(LocalCommand)

def test_foo(User):
    assert User().name == 'alexandre'
#def test_default(Process):
#    assert Process._backend.name == ''
#    assert Process.get(pid=1).comm == "tail"
#def test_default_2(Process):
#    assert Process._backend.name == ''
#    assert Process.get(pid=1).comm == "tail"


# This test will run on both debian:jessie and centos:7 images
#@pytest.mark.docker_images("debian:jessie", "centos:7")
#def test_multiple(Process):
#    assert Process.get(pid=1).comm == "tail"


# This test is marked as destructive and will run on its own container
# It will create a /foo file and run 3 times with different params
#@pytest.mark.destructive
#@pytest.mark.parametrize("content", ["bar", "baz", "qux"])
#def test_destructive(Command, File, content):
#    assert not File("/foo").exists
#    Command.check_output("echo %s > /foo", content)
#    assert File("/foo").content == content + "\n"

import pytest
import re
import testinfra


DOCKER_IMAGES = ['infopen/ubuntu-trusty-ssh']


@pytest.fixture(scope='module', params=DOCKER_IMAGES)
def image_name(request):
    """
    This fixture returns the image names to test
    """

    return request.param


@pytest.fixture(scope='module')
def LocalCommand(TestinfraBackend):
    """Run commands locally
    Same as `Command` but run commands locally with subprocess even
    when the connection backend is not "local".
    Note: `LocalCommand` does NOT respect ``--sudo`` option
    """

    return testinfra.get_backend("local://").get_module("Command")


@pytest.fixture(scope='module')
def docker_image(image_name, LocalCommand):
    return image_name


@pytest.fixture(scope='module')
def Docker(request, image_name, LocalCommand):
    """
    Boot and stop a docker image.
    """

    # Run a new container. Run in privileged mode, so systemd will start
    docker_id = LocalCommand.check_output(
        "docker run --privileged -d -P %s", image_name)

    def teardown():
        LocalCommand("docker kill %s", docker_id)
        LocalCommand("docker rm %s", docker_id)
        LocalCommand("rm /tmp/%s", docker_id)

    # At the end of each test, we destroy the container
    request.addfinalizer(teardown)

    # Get Docker host mapping for container SSH port expose
    host_ssh_port = LocalCommand.check_output(
        "docker inspect --format"
        " '{{ (index (index .NetworkSettings.Ports \"22/tcp\") 0).HostPort }}'"
        " %s" % docker_id)

    _manage_inventory_file(docker_id, host_ssh_port, LocalCommand)

    return testinfra.get_backend("docker://%s" % docker_id)


def _manage_inventory_file(docker_id, host_ssh_port, LocalCommand):
    """
    Manage ansible inventory file

    :param docker_id: Testing container ID
    :param host_ssh_port: Docker host mapping for container SSH port expose
    :param LocalCommand: Testinfra LocalCommand fixture with module scope
    :type docker_id: str
    :type host_ssh_port: str
    :type LocalCommand: pytest.fixture
    """

    ansible_version = LocalCommand.check_output('ansible --version')
    is_ansible_v2 = re.match('^ansible\s+2.*', ansible_version)
    ansible_prefix = 'ansible_ssh'

    if is_ansible_v2:
        ansible_prefix = 'ansible'

    inventory_content = ("{1} {0}_port={2} {0}_host=127.0.0.1\n".format(
                         ansible_prefix, docker_id, host_ssh_port))

    with open('/tmp/{}'.format(docker_id), 'w') as tmp_inventory:
        tmp_inventory.write(inventory_content)


def set_authorized_keys(self):
    """
    Set authorized keys content for root user into container
    """

    with open('/home/alexandre/.ssh/id_rsa.pub') as public_key_file:
        self.run('mkdir /root/.ssh')
        self.run('echo "%s" > /root/.ssh/authorized_keys' %
                 public_key_file.read())


def provision_with_ansible_by_ssh(self, LocalCommand):
    """
    Provision the image with Ansible
    """

    cmd = LocalCommand(
            "ANSIBLE_SSH_CONTROL_PATH=./%%h-%%r "
            "ANSIBLE_PRIVATE_KEY_FILE=/home/alexandre/.ssh/id_rsa "
            "ANSIBLE_REMOTE_USER=root "
            "ANSIBLE_HOST_KEY_CHECKING=False "
            "ANSIBLE_SSH_PIPELINING=True "
            "ansible -m setup {0} -i /tmp/{0}".format(self.name))
    assert cmd.rc == 0
    return cmd

testinfra.backend.docker.DockerBackend.set_authorized_keys = set_authorized_keys
testinfra.backend.docker.DockerBackend.provision_as = provision_with_ansible_by_ssh

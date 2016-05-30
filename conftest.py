"""
Ansible role testing base module
"""

import logging
import logging.config
import os
import re
import testinfra
import pytest


# Use testinfra to get a handy function to run commands locally
local_command = testinfra.get_backend('local://').get_module('Command')

# Manage logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,  # this fixes the problem

    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
})


@pytest.yield_fixture(scope='function', autouse=True)
def newline_before_logging(request):
    """
    Add a new line before logging, more readeable
    """

    if request.config.getoption('capture') == 'no':
        print  # new-line
    yield


def pytest_generate_tests(metafunc):
    """
    Overload pytest_generate_tests to set scope and image usage
    """

    if "TestinfraBackend" in metafunc.fixturenames:

        # Lookup "docker_images" marker
        marker = getattr(metafunc.function, "docker_images", None)
        if marker is not None:
            images = marker.args
        else:
            # Default image
            images = ["debian:jessie"]

        # If the test has a destructive marker, we scope TestinfraBackend
        # at function level (i.e. executing for each test). If not we scope
        # at session level (i.e. all tests will share the same container)
        if getattr(metafunc.function, "destructive", None) is not None:
            scope = "function"
        else:
            scope = "session"

        metafunc.parametrize(
            "TestinfraBackend", images, indirect=True, scope=scope)


@pytest.fixture
def TestinfraBackend(request):
    """
    Boot and stop a docker image.
    """

    # Run a new container. Run in privileged mode, so systemd will start
    docker_id = local_command.check_output(
        "docker run --privileged -d -P %s", request.param)

    def teardown():
        """
        Actions to execute on fixture end of life
        """

        local_command.check_output("docker kill %s", docker_id)
        local_command.check_output("docker rm %s", docker_id)
        local_command.check_output("rm /tmp/%s", docker_id)

    # At the end of each test, we destroy the container
    request.addfinalizer(teardown)

    # Get Docker host mapping for container SSH port expose
    host_ssh_port = local_command.check_output(
        "docker inspect --format"
        " '{{ (index (index .NetworkSettings.Ports \"22/tcp\") 0).HostPort }}'"
        " %s" % docker_id)

    is_verbose = (request.config.option.verbose > 0)
    _manage_inventory_file(docker_id, host_ssh_port)
    container = testinfra.get_backend("docker://%s" % docker_id)
    set_authorized_keys(container, is_verbose)
    provision_with_ansible_by_ssh(container, is_verbose)

    return container


def _manage_inventory_file(docker_id, host_ssh_port):
    """
    Manage ansible inventory file

    :param docker_id: Testing container ID
    :param host_ssh_port: Docker host mapping for container SSH port expose
    :param LocalCommand: Testinfra LocalCommand fixture with module scope
    :type docker_id: str
    :type host_ssh_port: str
    :type LocalCommand: pytest.fixture
    """

    ansible_version = local_command.check_output('ansible --version')
    is_ansible_v2 = re.match(r'^ansible\s+2.*', ansible_version)
    ansible_prefix = 'ansible_ssh'

    if is_ansible_v2:
        ansible_prefix = 'ansible'

    inventory_content = ("[{1}]\n{1} {0}_port={2} {0}_host=127.0.0.1\n".format(
        ansible_prefix, docker_id, host_ssh_port))

    with open('/tmp/{}'.format(docker_id), 'w') as tmp_inventory:
        tmp_inventory.write(inventory_content)


def set_authorized_keys(container, is_verbose):
    """
    Set authorized keys content for root user into container
    """

    public_key_file_path = os.environ.get('SSH_PUBLIC_KEY_PATH')
    with open(public_key_file_path) as public_key_file:
        public_key = public_key_file.read()
        container.run('mkdir /root/.ssh')
        container.run('echo "%s" > /root/.ssh/authorized_keys' % public_key)

        if is_verbose:
            logger = logging.getLogger('set_authorized_keys')
            logger.info('Add public SSH key: %s', public_key)


def provision_with_ansible_by_ssh(container, is_verbose):
    """
    Provision the image with Ansible
    """

    # TODO: Check to display output if -v
    private_key_file_path = os.environ.get('SSH_PRIVATE_KEY_PATH')
    cmd = local_command(
        "ANSIBLE_SSH_CONTROL_PATH=./%%h-%%r "
        "ANSIBLE_PRIVATE_KEY_FILE={1} "
        "ANSIBLE_REMOTE_USER=root "
        "ANSIBLE_HOST_KEY_CHECKING=False "
        "ANSIBLE_SSH_PIPELINING=True "
        "ANSIBLE_ROLES_PATH={2}/../:{2}:{3} "
        "ansible-playbook -i /tmp/{0} ./testing_deployment.yml".format(
            container.name, private_key_file_path,
            os.path.dirname(os.getcwd()), os.getcwd()))

    if is_verbose:
        logger = logging.getLogger('provision_with_ansible_by_ssh')
        logger.info('Ansible provision command:\n%s', cmd.command)
        logger.info('Execute ansible provision:\n%s', cmd.stdout)

    assert cmd.rc == 0
    return cmd

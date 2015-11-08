########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############

# Install Cloudify on Debian and Ubuntu
# apt-get update
# apt-get install -y curl
# curl -O -L http://gigaspaces-repository-eu.s3.amazonaws.com/org/cloudify3/get-cloudify.py && python get-cloudify.py -f  # NOQA

# Install Cloudify on Arch Linux
# pacman -Syu --noconfirm
# pacman-db-upgrade
# pacman -S python2 --noconfirm
# curl -O -L http://gigaspaces-repository-eu.s3.amazonaws.com/org/cloudify3/get-cloudify.py && python2 get-cloudify.py -f --python_path=python2 # NOQA

# Install Cloudify on CentOS/RHEL
# yum -y update
# yum groupinstall -y development
# yum install -y zlib-dev openssl-devel sqlite-devel bzip2-devel wget gcc tar
# wget http://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz
# tar -xzvf Python-2.7.6.tgz
# cd Python-2.7.6
# ./configure --prefix=/usr/local && make && make altinstall
# curl -O -L http://gigaspaces-repository-eu.s3.amazonaws.com/org/cloudify3/get-cloudify.py && python2.7 get-cloudify.py --python_path=python2.7 -f # NOQA

# Install Cloudify on Windows (Python 32/64bit)
# Install Python 2.7.x 32/64bit from https://www.python.org/downloads/release/python-279/  # NOQA
# Make sure that when you install, you choose to add Python to the system path.
# Download http://gigaspaces-repository-eu.s3.amazonaws.com/org/cloudify3/get-cloudify.py to any directory  # NOQA
# Run python get-cloudify.py -f


import sys
import subprocess
import argparse
import platform
import os
import urllib
import struct
import tempfile
import logging
import shutil
import time
import tarfile
from threading import Thread
from contextlib import closing


DESCRIPTION = '''This script attempts(!) to install Cloudify's CLI on Linux,
Windows (with Python32 AND 64), and OS X (Darwin).
On the linux front, it supports Debian/Ubuntu, CentOS/RHEL and Arch.

Note that the script attempts to not be instrusive by forcing the user
to explicitly declare installation of various dependencies.

Installations are supported for both system python, the currently active
virtualenv and a declared virtualenv (using the --virtualenv flag).

If you're already running the script from within a virtualenv and you're not
providing a --virtualenv path, Cloudify will be installed within the virtualenv
you're in.

The script allows you to install requirement txt files when installing from
--source.
If --with-requirements is provided with a value (a URL or path to
a requirements file) it will use it. If it's provided without a value, it
will try to download the archive provided in --source, extract it, and look for
dev-requirements.txt and requirements.txt files within it.

Passing the --wheels-path allows for an offline installation of Cloudify
from predownloaded Cloudify dependency wheels. Note that if wheels are found
within the default wheels directory or within --wheels-path, they will (unless
the --force-online flag is set) be used instead of performing an online
installation.

The script will attempt to install all necessary requirements including
python-dev and gcc (for Fabric on Linux), pycrypto (for Fabric on Windows),
pip and virtualenv (if --virtualenv was specified) depending on the OS and
Distro you're running on.
Note that to install certain dependencies (like pip or pythondev), you must
run the script as sudo.

It's important to note that even if you're running as sudo, if you're
installing in a declared virtualenv, the script will drop the root privileges
since you probably declared a virtualenv so that it can be installed using
the current user.
Also note, that if you're running with sudo and you have an active virtualenv,
much like any other python script, the installation will occur in the system
python.

By default, the script assumes that the Python executable is in the
path and is called 'python' on Linux and 'c:\python27\python.exe on Windows.
The Python path can be overriden by using the --python_path flag.

Please refer to Cloudify's documentation at http://getcloudify.org for
additional information.'''

IS_VIRTUALENV = hasattr(sys, 'real_prefix')

REQUIREMENT_FILE_NAMES = ['dev-requirements.txt', 'requirements.txt']
# TODO: put these in a private storage
PIP_URL = 'https://bootstrap.pypa.io/get-pip.py'
PYCR64_URL = 'http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win-amd64-py2.7.exe'  # NOQA
PYCR32_URL = 'http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win32-py2.7.exe'  # NOQA

NODEJS_URL = 'http://nodejs.org/dist/v{0}/node-v{0}-linux-x64.tar.gz'.format('0.10.35')  # NOQA
DSL_PARSER_CLI_URL = 'https://github.com/cloudify-cosmo/cloudify-dsl-parser-cli/archive/master.zip'  # NOQA
COMPOSER_URL = 'https://s3.amazonaws.com/cloudify-ui/composer-builds/{0}/blueprintcomposer-{0}.tgz'  # NOQA

PLATFORM = sys.platform
IS_WIN = (PLATFORM == 'win32')
IS_DARWIN = (PLATFORM == 'darwin')
IS_LINUX = (PLATFORM == 'linux2')

PROCESS_POLLING_INTERVAL = 0.1

# defined below
lgr = None

if not (IS_LINUX or IS_DARWIN or IS_WIN):
    sys.exit('Platform {0} not supported.'.format(PLATFORM))


def init_logger(logger_name):
    logger = logging.getLogger(logger_name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] '
                                      '[%(name)s] %(message)s',
                                  datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def run(cmd, suppress_errors=False):
    """Executes a command
    """
    lgr.debug('Executing: {0}...'.format(cmd))
    pipe = subprocess.PIPE
    proc = subprocess.Popen(
        cmd, shell=True, stdout=pipe, stderr=pipe)

    stderr_log_level = logging.NOTSET if suppress_errors else logging.ERROR

    stdout_thread = PipeReader(proc.stdout, proc, lgr, logging.DEBUG)
    stderr_thread = PipeReader(proc.stderr, proc, lgr, stderr_log_level)

    stdout_thread.start()
    stderr_thread.start()

    while proc.poll() is None:
        time.sleep(PROCESS_POLLING_INTERVAL)

    stdout_thread.join()
    stderr_thread.join()

    proc.aggr_stdout = stdout_thread.aggr
    proc.aggr_stderr = stderr_thread.aggr

    return proc


def drop_root_privileges():
    """Drop root privileges

    This is used so that when installing cloudify within a virtualenv
    using sudo, the default behavior will not be to install using sudo
    as a virtualenv is created especially so that users don't have to
    install in the system Python or using a Sudoer.
    """
    # maybe we're not root
    if not os.getuid() == 0:
        return

    lgr.info('Dropping root permissions...')
    os.setegid(int(os.environ.get('SUDO_GID', 0)))
    os.seteuid(int(os.environ.get('SUDO_UID', 0)))


def make_virtualenv(virtualenv_dir, python_path='python2'):
    """This will create a virtualenv. If no `python_path` is supplied,
    will assume that `python` is in path. This default assumption is provided
    via the argument parser.
    """
    lgr.info('Creating Virtualenv {0}...'.format(virtualenv_dir))
    result = run('virtualenv -p {0} {1}'.format(python_path, virtualenv_dir))
    if not result.returncode == 0:
        sys.exit('Could not create virtualenv: {0}'.format(virtualenv_dir))


def install_module(module, version=False, pre=False, virtualenv_path=False,
                   wheels_path=False, requirement_files=None, upgrade=False):
    """This will install a Python module.

    Can specify a specific version.
    Can specify a prerelease.
    Can specify a virtualenv to install in.
    Can specify a list of paths or urls to requirement txt files.
    Can specify a local wheels_path to use for offline installation.
    Can request an upgrade.
    """
    lgr.info('Installing {0}...'.format(module))
    pip_cmd = ['pip', 'install']
    if virtualenv_path:
        pip_cmd[0] = os.path.join(
            _get_env_bin_path(virtualenv_path), pip_cmd[0])
    if requirement_files:
        for req_file in requirement_files:
            pip_cmd.extend(['-r', req_file])
    module = '{0}=={1}'.format(module, version) if version else module
    pip_cmd.append(module)
    if wheels_path:
        pip_cmd.extend(
            ['--use-wheel', '--no-index', '--find-links', wheels_path])
    if pre:
        pip_cmd.append('--pre')
    if upgrade:
        pip_cmd.append('--upgrade')
    if IS_VIRTUALENV and not virtualenv_path:
        lgr.info('Installing within current virtualenv: {0}...'.format(
            IS_VIRTUALENV))
    result = run(' '.join(pip_cmd))
    if not result.returncode == 0:
        lgr.error(result.aggr_stdout)
        sys.exit('Could not install module: {0}.'.format(module))


def untar_requirement_files(archive, destination):
    """This will extract requirement files from an archive.
    """
    with tarfile.open(name=archive) as tar:
        req_files = [req_file for req_file in tar.getmembers()
                     if os.path.basename(req_file.name)
                     in REQUIREMENT_FILE_NAMES]
        tar.extractall(path=destination, members=req_files)


def download_file(url, destination):
    lgr.info('Downloading {0} to {1}'.format(url, destination))
    final_url = urllib.urlopen(url).geturl()
    if final_url != url:
        lgr.debug('Redirected to {0}'.format(final_url))
    f = urllib.URLopener()
    f.retrieve(final_url, destination)


def get_os_props():
    distro, _, release = platform.linux_distribution(
        full_distribution_name=False)
    return distro, release


def _get_env_bin_path(env_path):
    """returns the bin path for a virtualenv
    """
    try:
        import virtualenv
        return virtualenv.path_locations(env_path)[3]
    except ImportError:
        # this is a fallback for a race condition in which you're trying
        # to use the script and create a virtualenv from within
        # a virtualenv in which virtualenv isn't installed and so
        # is not importable.
        return os.path.join(env_path, 'scripts' if IS_WIN else 'bin')


class PipeReader(Thread):
    def __init__(self, fd, proc, logger, log_level):
        Thread.__init__(self)
        self.fd = fd
        self.proc = proc
        self.logger = logger
        self.log_level = log_level
        self.aggr = ''

    def run(self):
        while self.proc.poll() is None:
            output = self.fd.readline()
            if len(output) > 0:
                self.aggr += output
                self.logger.log(self.log_level, output)
            else:
                time.sleep(PROCESS_POLLING_INTERVAL)


def untar(archive, destination):
    """Extracts files from an archive to a destination folder.
    """
    lgr.debug('Extracting tar.gz {0} to {1}...'.format(archive, destination))
    with closing(tarfile.open(name=archive)) as tar:
        files = [f for f in tar.getmembers()]
        tar.extractall(path=destination, members=files)


class ComposerInstaller():

    NODEJS_HOME = '/opt/nodejs'

    def __init__(self, version, uninstall=False):
        self.version = version
        self.uninstall = uninstall

    def execute(self):
        if self.uninstall:
            lgr.info('Uninstalling Cloudify Blueprint Composer.')
            sys.exit(self.remove_all())
        self.install_nodejs()
        self.install_composer()
        self.install_dsl_parser()
        lgr.info(
            'You can now run: '
            'sudo {0}/bin/node '
            '/var/www/blueprint-composer/package/server.js '
            'to run Cloudify Blueprint Composer.'.format(
                self.NODEJS_HOME))

    def install_nodejs(self):
        tmp_dir = tempfile.mkdtemp()
        fd, tmp_file = tempfile.mkstemp()
        os.close(fd)
        run('mkdir -p {0}'.format(self.NODEJS_HOME))
        try:
            download_file(NODEJS_URL, tmp_file)
            untar(tmp_file, tmp_dir)
            source = os.path.join(
                tmp_dir, [d for d in os.walk(tmp_dir).next()[1]][0])
            run('mv {0}/* {1}'.format(source, self.NODEJS_HOME))
        finally:
            shutil.rmtree(tmp_dir)
            os.remove(tmp_file)

    @staticmethod
    def install_dsl_parser():
        drop_root_privileges()
        home = os.path.expanduser('~')
        venv = '{0}/dsl-cli-ve2'.format(home)
        make_virtualenv(venv)
        install_module(DSL_PARSER_CLI_URL, virtualenv_path=venv)

    def install_composer(self):
        fd, tmp_file = tempfile.mkstemp()
        os.close(fd)
        composer_path = '/var/www/blueprint-composer'
        run('mkdir -p {0}'.format(composer_path))
        try:
            download_file(COMPOSER_URL.format(self.version), tmp_file)
            untar(tmp_file, composer_path)
        finally:
            os.remove(tmp_file)

    def remove_all(self):
        home = os.path.expanduser('~')
        venv = '{0}/dsl-cli-ve2'.format(home)
        lgr.info('Removing Nodejs')
        run('rm -rf {0}'.format(self.NODEJS_HOME))
        lgr.info('Removing DSL Parser...')
        run('rm -rf {0}'.format(venv))
        lgr.info('Removing Composer...')
        run('rm -rf /var/www/blueprint-composer')


class CloudifyInstaller():
    def __init__(self, force=False, upgrade=False, virtualenv='',
                 version='', pre=False, source='', with_requirements='',
                 force_online=False, wheels_path='wheelhouse',
                 python_path='python', install_pip=False,
                 install_virtualenv=False, install_pythondev=False,
                 install_pycrypto=False, os_distro=None, os_release=None,
                 **kwargs):
        self.force = force
        self.upgrade = upgrade
        self.virtualenv = virtualenv
        self.version = version
        self.pre = pre
        self.source = source
        self.with_requirements = with_requirements
        self.force_online = force_online
        self.wheels_path = wheels_path
        self.python_path = python_path
        self.install_pip = install_pip
        self.install_virtualenv = install_virtualenv
        self.install_pythondev = install_pythondev
        self.install_pycrypto = install_pycrypto

        # TODO: we should test all mutually exclusive arguments.
        if not IS_WIN and self.install_pycrypto:
            lgr.warning('Pycrypto only relevant on Windows.')
        if not (IS_LINUX or IS_DARWIN) and self.install_pythondev:
            lgr.warning('Pythondev only relevant on Linux or OSx.')

        os_props = get_os_props()
        self.distro = os_distro or os_props[0].lower()
        self.release = os_release or os_props[1].lower()

    def execute(self):
        """Installation Logic

        --force argument forces installation of all prerequisites.
        If a wheels directory is found, it will be used for offline
        installation unless explicitly prevented using the --force_online flag.
        If an offline installation fails (for instance, not all wheels were
        found), an online installation process will commence.
        """
        lgr.debug('Identified Platform: {0}'.format(PLATFORM))
        lgr.debug('Identified Distribution: {0}'.format(self.distro))
        lgr.debug('Identified Release: {0}'.format(self.release))

        module = self.source or 'cloudify'

        if self.force or self.install_pip:
            self.install_pip()

        if self.virtualenv:
            if self.force or self.install_virtualenv:
                self.install_virtualenv()
            env_bin_path = _get_env_bin_path(self.virtualenv)

        if IS_LINUX and (self.force or self.install_pythondev):
            self.install_pythondev(self.distro)
        if (IS_VIRTUALENV or self.virtualenv) and not IS_WIN:
            # drop root permissions so that installation is done using the
            # current user.
            drop_root_privileges()
        if self.virtualenv:
            if not os.path.isfile(os.path.join(
                    env_bin_path, ('activate.bat' if IS_WIN else 'activate'))):
                make_virtualenv(self.virtualenv, self.python_path)

        if IS_WIN and (self.force or self.install_pycrypto):
            self.install_pycrypto(self.virtualenv)

        # if with_requirements is not provided, this will be False.
        # if it's provided without a value, it will be a list.
        if isinstance(self.with_requirements, list):
            self.with_requirements = self.with_requirements \
                or self._get_default_requirement_files(self.source)

        if self.force_online or not os.path.isdir(self.wheels_path):
            install_module(module=module,
                           version=self.version,
                           pre=self.pre,
                           virtualenv_path=self.virtualenv,
                           requirement_files=self.with_requirements,
                           upgrade=self.upgrade)
        elif os.path.isdir(self.wheels_path):
            lgr.info('Wheels directory found: "{0}". '
                     'Attemping offline installation...'.format(
                         self.wheels_path))
            try:
                install_module(module=module,
                               pre=True,
                               virtualenv_path=self.virtualenv,
                               wheels_path=self.wheels_path,
                               requirement_files=self.with_requirements,
                               upgrade=self.upgrade)
            except Exception as ex:
                lgr.warning('Offline installation failed ({0}).'.format(
                    str(ex)))
                install_module(module=module,
                               version=self.version,
                               pre=self.pre,
                               virtualenv_path=self.virtualenv,
                               requirement_files=self.with_requirements,
                               upgrade=self.upgrade)
        if self.virtualenv:
            activate_path = os.path.join(env_bin_path, 'activate')
            activate_command = \
                '{0}.bat'.format(activate_path) if IS_WIN \
                else 'source {0}'.format(activate_path)
            lgr.info('You can now run: "{0}" to activate '
                     'the Virtualenv.'.format(activate_command))

    @staticmethod
    def find_virtualenv():
        try:
            import virtualenv  # NOQA
            return True
        except:
            return False

    def install_virtualenv(self):
        if not self.find_virtualenv():
            lgr.info('Installing virtualenv...')
            install_module('virtualenv')
        else:
            lgr.info('virtualenv is already installed in the path.')

    @staticmethod
    def find_pip():
        try:
            import pip  # NOQA
            return True
        except:
            return False

    def install_pip(self):
        lgr.info('Installing pip...')
        if not self.find_pip():
            try:
                tempdir = tempfile.mkdtemp()
                get_pip_path = os.path.join(tempdir, 'get-pip.py')
                try:
                    download_file(PIP_URL, get_pip_path)
                except Exception as e:
                    sys.exit('Failed downloading pip from {0}. ({1})'.format(
                             PIP_URL, e.message))
                result = run('{0} {1}'.format(
                    self.python_path, get_pip_path))
                if not result.returncode == 0:
                    sys.exit('Could not install pip')
            finally:
                shutil.rmtree(tempdir)
        else:
            lgr.info('pip is already installed in the path.')

    @staticmethod
    def _get_default_requirement_files(source):
        if os.path.isdir(source):
            return [os.path.join(source, f) for f in REQUIREMENT_FILE_NAMES
                    if os.path.isfile(os.path.join(source, f))]
        else:
            tempdir = tempfile.mkdtemp()
            archive = os.path.join(tempdir, 'cli_source')
            # TODO: need to handle deletion of the temp source dir
            try:
                download_file(source, archive)
            except Exception as ex:
                lgr.error('Could not download {0} ({1})'.format(
                    source, str(ex)))
                sys.exit(1)
            try:
                untar_requirement_files(archive, tempdir)
            except Exception as ex:
                lgr.error('Could not extract {0} ({1})'.format(
                    archive, str(ex)))
                sys.exit(1)
            finally:
                os.remove(archive)
            # GitHub always adds a single parent directory to the tree.
            # TODO: look in parent dir, then one level underneath.
            # the GitHub style tar assumption isn't a very good one.
            req_dir = os.path.join(tempdir, os.listdir(tempdir)[0])
            return [os.path.join(req_dir, f) for f in REQUIREMENT_FILE_NAMES
                    if os.path.isfile(os.path.join(req_dir, f))]

    def install_pythondev(self, distro):
        """Installs python-dev and gcc

        This will try to match a command for your platform and distribution.
        """
        lgr.info('Installing python-dev...')
        if distro in ('ubuntu', 'debian'):
            cmd = 'apt-get install -y gcc python-dev'
        elif distro in ('centos', 'redhat', 'fedora'):
            cmd = 'yum -y install gcc python-devel'
        elif os.path.isfile('/etc/arch-release'):
            # Arch doesn't require a python-dev package.
            # It's already supplied with Python.
            cmd = 'pacman -S gcc --noconfirm'
        elif IS_DARWIN:
            lgr.info('python-dev package not required on Darwin.')
            return
        else:
            sys.exit('python-dev package installation not supported '
                     'in current distribution.')
        run(cmd)

    # Windows only
    def install_pycrypto(self, virtualenv_path):
        """This will install PyCrypto to be used by Fabric.
        PyCrypto isn't compiled with Fabric on Windows by default thus it needs
        to be provided explicitly.
        It will attempt to install the 32 or 64 bit version according to the
        Python version installed.
        """
        # check 32/64bit to choose the correct PyCrypto installation
        is_pyx32 = True if struct.calcsize("P") == 4 else False

        lgr.info('Installing PyCrypto {0}bit...'.format(
            '32' if is_pyx32 else '64'))
        # easy install is used instead of pip as pip doesn't handle windows
        # executables.
        cmd = 'easy_install {0}'.format(PYCR32_URL if is_pyx32 else PYCR64_URL)
        if virtualenv_path:
            cmd = os.path.join(_get_env_bin_path(virtualenv_path), cmd)
        run(cmd)


def check_cloudify_installed(virtualenv_path=None):
    if virtualenv_path:
        result = run(
            os.path.join(_get_env_bin_path(virtualenv_path),
                         'python -c "import cloudify"'),
            suppress_errors=True)
        return result.returncode == 0
    else:
        try:
            import cloudify  # NOQA
            return True
        except ImportError:
            return False


def handle_upgrade(upgrade=False, virtualenv=''):
    if check_cloudify_installed(virtualenv):
        lgr.info('Cloudify is already installed in the path.')
        if upgrade:
            lgr.info('Upgrading...')
        else:
            lgr.error('Use the --upgrade flag to upgrade.')
            sys.exit(1)


def parse_args(args=None):
    class VerifySource(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not args.source:
                parser.error(
                    '--source is required when calling --with_requirements.')
            setattr(args, self.dest, values)

    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter)
    default_group = parser.add_mutually_exclusive_group()
    default_group.add_argument('-v', '--verbose', action='store_true',
                               help='Verbose level logging to shell.')
    default_group.add_argument('-q', '--quiet', action='store_true',
                               help='Only print errors.')

    subparsers = parser.add_subparsers(help='Cloudify Installer.')

    cli = subparsers.add_parser('cli', help='Installs Cloudify CLI.')
    version_group = cli.add_mutually_exclusive_group()
    online_group = cli.add_mutually_exclusive_group()
    cli.add_argument(
        '-f', '--force', action='store_true',
        help='Force install any requirements (USE WITH CARE!).')
    cli.add_argument(
        '-e', '--virtualenv', type=str,
        help='Path to a Virtualenv to install Cloudify in.')
    version_group.add_argument(
        '--version', type=str,
        help='Attempt to install a specific version of Cloudify.')
    version_group.add_argument(
        '--pre', action='store_true',
        help='Attempt to install the latest Cloudify Milestone.')
    version_group.add_argument(
        '-s', '--source', type=str,
        help='Install from the provided URL or local path.')
    cli.add_argument(
        '-r', '--with-requirements', nargs='*',
        help='Install default or provided requirements file.',
        action=VerifySource)
    cli.add_argument(
        '-u', '--upgrade', action='store_true',
        help='Upgrades Cloudify if already installed.')
    online_group.add_argument(
        '--force-online', action='store_true',
        help='Even if wheels are found locally, install from PyPI.')
    online_group.add_argument(
        '--wheels-path', type=str, default='wheelhouse',
        help='Path to wheels (defaults to "<cwd>/wheelhouse").')
    if IS_WIN:
        cli.add_argument(
            '--python-path', type=str, default='c:/python27/python.exe',
            help='Python path to use (defaults to "c:/python27/python.exe") '
                 'when creating a virtualenv.')
    else:
        cli.add_argument(
            '--python-path', type=str, default='python',
            help='Python path to use (defaults to "python") '
                 'when creating a virtualenv.')
    cli.add_argument(
        '--install-pip', action='store_true',
        help='Attempt to install pip.')
    cli.add_argument(
        '--install-virtualenv', action='store_true',
        help='Attempt to install Virtualenv.')
    if IS_LINUX:
        cli.add_argument(
            '--install-pythondev', action='store_true',
            help='Attempt to install Python Developers Package.')
    elif IS_WIN:
        cli.add_argument(
            '--install-pycrypto', action='store_true',
            help='Attempt to install PyCrypto.')

    composer = subparsers.add_parser(
        'composer', help='Installs Cloudufy Composer.')
    composer = composer.add_mutually_exclusive_group(required=True)
    composer.add_argument(
        '--version', type=str,
        help='Installs a specific version.')
    composer.add_argument(
        '--uninstall', action='store_true',
        help='Uninstalls the composer.')

    return parser.parse_args(args)


lgr = init_logger(__file__)


if __name__ == '__main__':
    args = parse_args()
    if args.quiet:
        lgr.setLevel(logging.ERROR)
    elif args.verbose:
        lgr.setLevel(logging.DEBUG)
    else:
        lgr.setLevel(logging.INFO)

    xargs = ['quiet', 'verbose']
    args = {arg: v for arg, v in vars(args).items() if arg not in xargs}
    if 'source' in args:
        handle_upgrade(args['upgrade'], args['virtualenv'])
        installer = CloudifyInstaller(**args)
        installer.execute()
    else:
        installer = ComposerInstaller(**args)
        installer.execute()

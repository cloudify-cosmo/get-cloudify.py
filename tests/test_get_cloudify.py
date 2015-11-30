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
from copy import copy
import importlib
import logging
import mock
import os
import shutil
from StringIO import StringIO
import sys
import tarfile
import tempfile
import testtools
import urllib

sys.path.append("../")

get_cloudify = importlib.import_module('get-cloudify')


class CliBuilderUnitTests(testtools.TestCase):
    """Unit tests for functions in get_cloudify.py"""

    def setUp(self):
        super(CliBuilderUnitTests, self).setUp()
        self.get_cloudify = get_cloudify
        self.get_cloudify.IS_VIRTUALENV = False

    def _create_dummy_requirements_tar(self, url, destination):
        tempdir = os.path.dirname(destination)
        fpath = self._generate_requirements_file(tempdir)
        try:
            tar = tarfile.open(name=destination, mode='w:gz')
            tar.add(name=tempdir, arcname='maindir')
            tar.close()
        finally:
            os.remove(fpath)
        return destination

    def _generate_requirements_file(self, path):
        fpath = os.path.join(path, 'dev-requirements.txt')
        with open(fpath, 'w') as f:
            f.write('sh==1.11\n')
        return fpath

    def test_validate_urls(self):
        self._validate_url(self.get_cloudify.PIP_URL)
        self._validate_url(self.get_cloudify.PYCR64_URL)
        self._validate_url(self.get_cloudify.PYCR32_URL)

    @staticmethod
    def _validate_url(url):
        try:
            status = urllib.urlopen(url).getcode()
            if not status == 200:
                raise AssertionError('url {} is not valid.'.format(url))
        except:
            raise AssertionError('url {} is not valid.'.format(url))

    def test_run_valid_command(self):
        proc = self.get_cloudify._run('echo Hi!')
        self.assertEqual(proc.returncode, 0, 'process execution failed')

    def test_run_invalid_command(self):
        builder_stdout = StringIO()
        # replacing builder stdout
        self.get_cloudify.sys.stdout = builder_stdout
        cmd = 'this is not a valid command'
        proc = self.get_cloudify._run(cmd)
        self.assertIsNot(proc.returncode, 0, 'command \'{}\' execution was '
                                             'expected to fail'.format(cmd))

    def test_installer_init_unexpected_argument(self):
        """Make sure typos in parse_args don't go un-noticed with **kwargs."""
        self.assertRaises(
            TypeError,
            self.get_cloudify.CloudifyInstaller,
            unknown_argument='unknown',
        )

    def test_installer_init_no_args(self):
        """Installer should initialise with no args."""
        self.get_cloudify.CloudifyInstaller()

    @mock.patch('get-cloudify.IS_WIN')
    def test_installer_init_pycrypto_not_windows(self, mock_win):
        """Installer init should complain with pycrypto not on windows."""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_WIN = False

        self.assertRaises(
            self.get_cloudify.ArgumentNotValidForOS,
            self.get_cloudify.CloudifyInstaller,
            install_pycrypto=True,
        )

    @mock.patch('get-cloudify.IS_WIN')
    def test_installer_init_pycrypto_windows(self, mock_win):
        """Installer init should work with pycrypto on windows."""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_WIN = True

        self.get_cloudify.CloudifyInstaller(
            install_pycrypto=True,
        )

    def test_installer_init_version_set(self):
        """Installer init should work with version set."""
        self.get_cloudify.CloudifyInstaller(
            version='1',
        )

    def test_installer_init_pre_set(self):
        """Installer init should work with pre set."""
        self.get_cloudify.CloudifyInstaller(
            pre=True,
        )

    def test_installer_init_source_set(self):
        """Installer init should work with source set."""
        self.get_cloudify.CloudifyInstaller(
            source='http://www.example.com/example.tar.gz',
        )

    def test_installer_init_version_and_pre_failure(self):
        """Installer init should fail with version and pre."""
        self.assertRaises(
            self.get_cloudify.ArgumentCombinationInvalid,
            self.get_cloudify.CloudifyInstaller,
            version='1',
            pre=True,
        )

    def test_installer_init_version_and_source_failure(self):
        """Installer init should fail with version and source."""
        self.assertRaises(
            self.get_cloudify.ArgumentCombinationInvalid,
            self.get_cloudify.CloudifyInstaller,
            version='1',
            source='http://www.example.com/example.tar.gz',
        )

    def test_installer_init_pre_and_source_failure(self):
        """Installer init should fail with pre and source."""
        self.assertRaises(
            self.get_cloudify.ArgumentCombinationInvalid,
            self.get_cloudify.CloudifyInstaller,
            pre=True,
            source='http://www.example.com/example.tar.gz',
        )

    def test_installer_init_pre_and_version_and_source_failure(self):
        """Installer init should fail with pre, version and source."""
        self.assertRaises(
            self.get_cloudify.ArgumentCombinationInvalid,
            self.get_cloudify.CloudifyInstaller,
            pre=True,
            version='1',
            source='http://www.example.com/example.tar.gz',
        )

    def test_is_module_installed(self):
        installer = self.get_cloudify.CloudifyInstaller()

        self.assertTrue(installer.is_installed('os'))

    def test_is_module_not_installed(self):
        installer = self.get_cloudify.CloudifyInstaller()

        self.assertFalse(installer.is_installed('not_real_module'))

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify._exit',
                side_effect=SystemExit)
    @mock.patch('get-cloudify.PLATFORM')
    def test_main_unsupported_os(self,
                                 mock_platform,
                                 mock_exit,
                                 mock_darwin,
                                 mock_win,
                                 mock_linux):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False
        self.get_cloudify.PLATFORM = 'fake'

        self.assertRaises(
            SystemExit,
            self.get_cloudify.main,
        )
        mock_exit.assert_called_once_with(
            message='Platform fake not supported.',
            status='unsupported_platform',
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.CloudifyInstaller')
    @mock.patch(
        'get-cloudify.parse_args',
        return_value={
            'quiet': False,
            'verbose': False,
        },
    )
    def test_main_linux(self,
                        mock_parse_args,
                        mock_installer,
                        mock_log,
                        mock_darwin,
                        mock_win,
                        mock_linux):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        self.get_cloudify.main()

        mock_parse_args.assert_called_once_with()
        mock_log.setLevel.assert_called_once_with(logging.INFO)
        mock_installer.assert_called_once_with()
        mock_installer().execute.assert_called_once_with()

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.CloudifyInstaller')
    @mock.patch(
        'get-cloudify.parse_args',
        return_value={
            'quiet': False,
            'verbose': False,
        },
    )
    def test_main_windows(self,
                          mock_parse_args,
                          mock_installer,
                          mock_log,
                          mock_darwin,
                          mock_win,
                          mock_linux):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = True
        self.get_cloudify.IS_DARWIN = False

        self.get_cloudify.main()

        mock_parse_args.assert_called_once_with()
        mock_log.setLevel.assert_called_once_with(logging.INFO)
        mock_installer.assert_called_once_with()
        mock_installer().execute.assert_called_once_with()

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.CloudifyInstaller')
    @mock.patch(
        'get-cloudify.parse_args',
        return_value={
            'quiet': False,
            'verbose': False,
        },
    )
    def test_main_darwin(self,
                         mock_parse_args,
                         mock_installer,
                         mock_log,
                         mock_darwin,
                         mock_win,
                         mock_linux):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = True

        self.get_cloudify.main()

        mock_parse_args.assert_called_once_with()
        mock_log.setLevel.assert_called_once_with(logging.INFO)
        mock_installer.assert_called_once_with()
        mock_installer().execute.assert_called_once_with()

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.CloudifyInstaller')
    @mock.patch(
        'get-cloudify.parse_args',
        return_value={
            'quiet': True,
            'verbose': False,
        },
    )
    def test_main_quiet_logging(self,
                                mock_parse_args,
                                mock_installer,
                                mock_log,
                                mock_darwin,
                                mock_win,
                                mock_linux):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = True

        self.get_cloudify.main()

        mock_parse_args.assert_called_once_with()
        mock_log.setLevel.assert_called_once_with(logging.ERROR)
        mock_installer.assert_called_once_with()
        mock_installer().execute.assert_called_once_with()

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.CloudifyInstaller')
    @mock.patch(
        'get-cloudify.parse_args',
        return_value={
            'quiet': False,
            'verbose': True,
        },
    )
    def test_main_verbose_logging(self,
                                  mock_parse_args,
                                  mock_installer,
                                  mock_log,
                                  mock_darwin,
                                  mock_win,
                                  mock_linux):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = True

        self.get_cloudify.main()

        mock_parse_args.assert_called_once_with()
        mock_log.setLevel.assert_called_once_with(logging.DEBUG)
        mock_installer.assert_called_once_with()
        mock_installer().execute.assert_called_once_with()

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.CloudifyInstaller')
    @mock.patch(
        'get-cloudify.parse_args',
        return_value={
            'quiet': False,
            'verbose': False,
            'fake_arg': 'this',
        },
    )
    def test_main_parsed_args_used(self,
                                   mock_parse_args,
                                   mock_installer,
                                   mock_log,
                                   mock_darwin,
                                   mock_win,
                                   mock_linux):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = True

        self.get_cloudify.main()

        mock_parse_args.assert_called_once_with()
        mock_log.setLevel.assert_called_once_with(logging.INFO)
        mock_installer.assert_called_once_with(
            fake_arg='this',
        )
        mock_installer().execute.assert_called_once_with()

    @mock.patch('get-cloudify.IS_WIN')
    def test_get_env_bin_path_windows(self, mock_win):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_WIN = True

        result = self.get_cloudify._get_env_bin_path('path')
        self.assertEquals('path/scripts', result)

    @mock.patch('get-cloudify.IS_WIN')
    def test_get_env_bin_path_not_windows(self, mock_win):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_WIN = False

        result = self.get_cloudify._get_env_bin_path('path')
        self.assertEquals('path/bin', result)

    @mock.patch('get-cloudify.os')
    def test_is_root(self, mock_os):
        mock_os.getuid.return_value = 0
        self.assertTrue(self.get_cloudify._is_root())

    @mock.patch('get-cloudify.os')
    def test_not_is_root(self, mock_os):
        mock_os.getuid.return_value = 1
        self.assertFalse(self.get_cloudify._is_root())

    @mock.patch('get-cloudify._is_root')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.os')
    def test_drop_root_privileges_from_sudo(self,
                                            mock_os,
                                            mock_log,
                                            mock_root_check):
        mock_root_check.return_value = True
        type(mock_os).environ = mock.PropertyMock(
            return_value={
                'SUDO_GID': 12345,
                'SUDO_UID': 54321,
            },
        )

        self.get_cloudify._drop_root_privileges()

        mock_log.info.assert_called_once_with('Dropping root permissions...')
        mock_os.setegid.assert_called_once_with(12345)
        mock_os.seteuid.assert_called_once_with(54321)

    @mock.patch('get-cloudify._is_root')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.os')
    def test_drop_root_privileges_without_sudo(self,
                                               mock_os,
                                               mock_log,
                                               mock_root_check):
        mock_root_check.return_value = True
        type(mock_os).environ = mock.PropertyMock(
            return_value={},
        )

        self.get_cloudify._drop_root_privileges()

        mock_log.info.assert_called_once_with('Dropping root permissions...')
        mock_os.setegid.assert_called_once_with(0)
        mock_os.seteuid.assert_called_once_with(0)

    @mock.patch('get-cloudify._is_root')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.os')
    def test_no_drop_root_privileges(self,
                                     mock_os,
                                     mock_log,
                                     mock_root_check):
        mock_root_check.return_value = False

        self.get_cloudify._drop_root_privileges()

        self.assertFalse(mock_log.info.called)
        self.assertFalse(mock_os.setegid.called)
        self.assertFalse(mock_os.seteuid.called)

    @mock.patch('get-cloudify.sys.exit')
    @mock.patch('get-cloudify.logger')
    def test_exit_unsupported_os(self,
                                 mock_log,
                                 mock_exit):
        self.get_cloudify._exit(
            message='Unsupported OS',
            status='unsupported_platform',
        )

        mock_log.error.assert_called_once_with('Unsupported OS')
        mock_exit.assert_called_once_with(200)

    @mock.patch('get-cloudify.sys.exit')
    @mock.patch('get-cloudify.logger')
    def test_exit_venv_create_fail(self,
                                   mock_log,
                                   mock_exit):
        self.get_cloudify._exit(
            message='Venv creation failure',
            status='virtualenv_creation_failure',
        )

        mock_log.error.assert_called_once_with('Venv creation failure')
        mock_exit.assert_called_once_with(210)

    @mock.patch('get-cloudify.sys.exit')
    @mock.patch('get-cloudify.logger')
    def test_exit_dep_download_fail(self,
                                    mock_log,
                                    mock_exit):
        self.get_cloudify._exit(
            message='Download failure',
            status='dependency_download_failure',
        )

        mock_log.error.assert_called_once_with('Download failure')
        mock_exit.assert_called_once_with(220)

    @mock.patch('get-cloudify.sys.exit')
    @mock.patch('get-cloudify.logger')
    def test_exit_dep_extract_fail(self,
                                   mock_log,
                                   mock_exit):
        self.get_cloudify._exit(
            message='Extraction failure',
            status='dependency_extraction_failure',
        )

        mock_log.error.assert_called_once_with('Extraction failure')
        mock_exit.assert_called_once_with(221)

    @mock.patch('get-cloudify.sys.exit')
    @mock.patch('get-cloudify.logger')
    def test_exit_dep_install_fail(self,
                                   mock_log,
                                   mock_exit):
        self.get_cloudify._exit(
            message='Install failure',
            status='dependency_installation_failure',
        )

        mock_log.error.assert_called_once_with('Install failure')
        mock_exit.assert_called_once_with(222)

    @mock.patch('get-cloudify.sys.exit')
    @mock.patch('get-cloudify.logger')
    def test_exit_dep_unsupported_distro(self,
                                         mock_log,
                                         mock_exit):
        self.get_cloudify._exit(
            message='Wrong distro',
            status='dependency_unsupported_on_distribution',
        )

        mock_log.error.assert_called_once_with('Wrong distro')
        mock_exit.assert_called_once_with(223)

    @mock.patch('get-cloudify.sys.exit')
    @mock.patch('get-cloudify.logger')
    def test_exit_cloudify_already_uninstalled(self,
                                               mock_log,
                                               mock_exit):
        self.get_cloudify._exit(
            message='Cloudify already here',
            status='cloudify_already_installed',
        )

        mock_log.error.assert_called_once_with('Cloudify already here')
        mock_exit.assert_called_once_with(230)

    @mock.patch('get-cloudify._exit',
                side_effect=SystemExit)
    @mock.patch('get-cloudify._download_file',
                side_effect=StandardError('Boom!'))
    @mock.patch('get-cloudify.CloudifyInstaller.is_installed',
                return_value=False)
    def test_install_pip_failed_download(self,
                                         mock_find_pip,
                                         mock_download,
                                         mock_exit):
        installer = self.get_cloudify.CloudifyInstaller()

        self.assertRaises(
            SystemExit,
            installer.get_pip,
        )
        mock_exit.assert_called_once_with(
            message='Failed pip download from {0}. (Boom!)'.format(
                get_cloudify.PIP_URL,
            ),
            status='dependency_download_failure',
        )

    @mock.patch('get-cloudify._exit',
                side_effect=SystemExit)
    @mock.patch('get-cloudify._download_file',
                return_value=None)
    @mock.patch('get-cloudify.CloudifyInstaller.is_installed',
                return_value=False)
    def test_install_pip_fail(self,
                              mock_find_pip,
                              mock_download,
                              mock_exit):
        python_path = 'non_existing_path'
        installer = self.get_cloudify.CloudifyInstaller(
            python_path=python_path,
        )

        self.assertRaises(
            SystemExit,
            installer.get_pip,
        )
        mock_exit.assert_called_once_with(
            message='Could not install pip',
            status='dependency_installation_failure',
        )

    @mock.patch('get-cloudify._exit',
                side_effect=SystemExit)
    def test_make_virtualenv_fail(self, mock_exit):
        self.assertRaises(
            SystemExit,
            self.get_cloudify._make_virtualenv,
            '/path/to/dir',
            'non_existing_path',
        )

        mock_exit.assert_called_once_with(
            message='Could not create virtualenv: /path/to/dir',
            status='virtualenv_creation_failure',
        )

    @mock.patch('get-cloudify._exit',
                side_effect=SystemExit)
    def test_install_non_existing_module(self, mock_exit):
        self.assertRaises(
            SystemExit,
            self.get_cloudify._install_package,
            'nonexisting_module',
        )
        mock_exit.assert_called_once_with(
            message='Could not install package: nonexisting_module.',
            status='dependency_installation_failure',
        )

    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify._run')
    @mock.patch('get-cloudify.IS_VIRTUALENV')
    def test_install_in_existing_venv_no_path(self,
                                              mock_is_venv,
                                              mock_run,
                                              mock_log):
        # Original value will be restored by mock patch
        self.get_cloudify.IS_VIRTUALENV = True

        type(mock_run.return_value).returncode = mock.PropertyMock(
            return_value=0,
        )

        self.get_cloudify._install_package('test-package')

        expected_info_log_calls = [
            mock.call('Installing test-package...'),
            mock.call('Installing within current virtualenv.'),
        ]
        mock_log.info.assert_has_calls(expected_info_log_calls)
        self.assertEquals(2, mock_log.info.call_count)
        mock_run.assert_called_once_with(
            'pip install test-package',
        )

    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify._run')
    @mock.patch('get-cloudify.IS_VIRTUALENV')
    @mock.patch('get-cloudify._get_env_bin_path',
                return_value='/my/venv/bin')
    def test_install_with_venv_path(self,
                                    mock_bin_path,
                                    mock_is_venv,
                                    mock_run,
                                    mock_log):
        # Original value will be restored by mock patch
        self.get_cloudify.IS_VIRTUALENV = False

        type(mock_run.return_value).returncode = mock.PropertyMock(
            return_value=0,
        )

        self.get_cloudify._install_package('test-package',
                                           virtualenv_path='/my/venv')

        mock_log.info.assert_called_once_with(
            'Installing test-package...',
        )
        mock_run.assert_called_once_with(
            '/my/venv/bin/pip install test-package',
        )

    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify._run')
    @mock.patch('get-cloudify.IS_VIRTUALENV')
    @mock.patch('get-cloudify._get_env_bin_path',
                return_value='/my/venv/bin')
    def test_install_with_venv_path_ignores_current_venv(self,
                                                         mock_bin_path,
                                                         mock_is_venv,
                                                         mock_run,
                                                         mock_log):
        # Original value will be restored by mock patch
        self.get_cloudify.IS_VIRTUALENV = True

        type(mock_run.return_value).returncode = mock.PropertyMock(
            return_value=0,
        )

        self.get_cloudify._install_package('test-package',
                                           virtualenv_path='/my/venv')

        mock_log.info.assert_called_once_with(
            'Installing test-package...',
        )
        mock_run.assert_called_once_with(
            '/my/venv/bin/pip install test-package',
        )

    def test_get_os_props(self):
        distro = self.get_cloudify._get_os_props()[0]
        distros = ('ubuntu', 'redhat', 'debian', 'fedora', 'centos',
                   'archlinux')
        if distro.lower() not in distros:
            self.fail('distro prop \'{0}\' should be equal to one of: '
                      '{1}'.format(distro, distros))

    def test_download_file(self):
        self.get_cloudify.VERBOSE = True
        tmp_file = tempfile.NamedTemporaryFile(delete=True)
        self.get_cloudify._download_file('http://www.google.com', tmp_file.name)
        with open(tmp_file.name) as f:
            content = f.readlines()
            self.assertIsNotNone(content)

    def test_check_cloudify_not_installed_in_venv(self):
        tmp_venv = tempfile.mkdtemp()
        installer = self.get_cloudify.CloudifyInstaller(virtualenv=tmp_venv)
        try:
            self.get_cloudify._make_virtualenv(tmp_venv, 'python')
            self.assertFalse(
                installer.check_cloudify_installed()
            )
        finally:
            shutil.rmtree(tmp_venv)

    def test_check_cloudify_installed_in_venv(self):
        tmp_venv = tempfile.mkdtemp()
        try:
            self.get_cloudify._make_virtualenv(tmp_venv, 'python')
            installer = get_cloudify.CloudifyInstaller(virtualenv=tmp_venv)
            installer.execute()
            self.assertTrue(
                installer.check_cloudify_installed()
            )
        finally:
            shutil.rmtree(tmp_venv)

    def test_get_requirements_from_source_url(self):
        def get(url, destination):
            return self._create_dummy_requirements_tar(url, destination)

        self.get_cloudify._download_file = get
        try:
            installer = self.get_cloudify.CloudifyInstaller()
            req_list = installer._get_default_requirement_files('null')
            self.assertEquals(len(req_list), 1)
            self.assertIn('dev-requirements.txt', req_list[0])
        finally:
            self.get_cloudify._download_file = get_cloudify._download_file

    def test_get_requirements_from_source_path(self):
        tempdir = tempfile.mkdtemp()
        self._generate_requirements_file(tempdir)
        try:
            installer = self.get_cloudify.CloudifyInstaller()
            req_list = installer._get_default_requirement_files(tempdir)
            self.assertEquals(len(req_list), 1)
            self.assertIn('dev-requirements.txt', req_list[0])
        finally:
            shutil.rmtree(tempdir)


class TestArgParser(testtools.TestCase):
    """Unit tests for functions in get_cloudify.py"""

    def setUp(self):
        super(TestArgParser, self).setUp()
        self.get_cloudify = get_cloudify
        self.get_cloudify.IS_VIRTUALENV = False

        self.expected_args = {
            'verbose': False,
            'quiet': False,
            'version': None,
            'pre': False,
            'source': None,
            'force': False,
            'virtualenv': None,
            'install_pip': False,
            'install_virtualenv': False,
            'with_requirements': None,
            'upgrade': False,
            'pip_args': None,
        }

        self.expected_repo_url = \
            'https://github.com/{user}/cloudify-cli/archive/{branch}.tar.gz'
        self.expected_repo_default_user = 'cloudify-cosmo'

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    def test_expected_argsr_linux(self,
                                  mock_linux,
                                  mock_win,
                                  mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False
        args = self.get_cloudify.parse_args([])

        expected_args = copy(self.expected_args)
        expected_args['install_pythondev'] = False

        self.assertEquals(expected_args, args)

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    def test_expected_args_windows(self,
                                   mock_linux,
                                   mock_win,
                                   mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = True
        self.get_cloudify.IS_DARWIN = False
        args = self.get_cloudify.parse_args([])

        expected_args = copy(self.expected_args)
        expected_args['install_pycrypto'] = False

        self.assertEquals(expected_args, args)

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    def test_expected_args_darwin(self,
                                  mock_linux,
                                  mock_win,
                                  mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = True
        args = self.get_cloudify.parse_args([])

        self.assertEquals(self.expected_args, args)

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_deprecated_withrequirements(self,
                                         mock_log,
                                         mock_linux,
                                         mock_win,
                                         mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        # Source required when using with-requirements
        args = self.get_cloudify.parse_args([
            '--source=notreal',
            '--withrequirements=test',
        ])

        self.assertEquals(['test'], args['with_requirements'])
        mock_log.warning.assert_called_once_with(
            '--withrequirements is deprecated. Use --with-requirements. '
            '--withrequirements will be removed in a future release.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_deprecated_installvirtualenv(self,
                                          mock_log,
                                          mock_linux,
                                          mock_win,
                                          mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        args = self.get_cloudify.parse_args(['--installvirtualenv'])

        self.assertTrue(args['install_virtualenv'])
        mock_log.warning.assert_called_once_with(
            '--installvirtualenv is deprecated. Use --install-virtualenv. '
            '--installvirtualenv will be removed in a future release.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_deprecated_installpip(self,
                                   mock_log,
                                   mock_linux,
                                   mock_win,
                                   mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        args = self.get_cloudify.parse_args(['--installpip'])

        self.assertTrue(args['install_pip'])
        mock_log.warning.assert_called_once_with(
            '--installpip is deprecated. Use --install-pip. '
            '--installpip will be removed in a future release.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_deprecated_installpycrypto(self,
                                        mock_log,
                                        mock_linux,
                                        mock_win,
                                        mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = True
        self.get_cloudify.IS_DARWIN = False

        args = self.get_cloudify.parse_args(['--installpycrypto'])

        self.assertTrue(args['install_pycrypto'])
        mock_log.warning.assert_called_once_with(
            '--installpycrypto is deprecated. Use --install-pycrypto. '
            '--installpycrypto will be removed in a future release.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_deprecated_installpythondev(self,
                                         mock_log,
                                         mock_linux,
                                         mock_win,
                                         mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        args = self.get_cloudify.parse_args(['--installpythondev'])

        self.assertTrue(args['install_pythondev'])
        mock_log.warning.assert_called_once_with(
            '--installpythondev is deprecated. Use --install-pythondev. '
            '--installpythondev will be removed in a future release.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_deprecated_pythonpath(self,
                                   mock_log,
                                   mock_linux,
                                   mock_win,
                                   mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        args = self.get_cloudify.parse_args(['--pythonpath=test'])

        self.assertEquals('test', args['python_path'])
        mock_log.warning.assert_called_once_with(
            '--pythonpath is deprecated. '
            'To use a different interpreter, run this script with '
            'your preferred interpreter and that interpreter will be '
            'used.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_deprecated_forceonline(self,
                                    mock_log,
                                    mock_linux,
                                    mock_win,
                                    mock_darwin):
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        args = self.get_cloudify.parse_args(['--forceonline'])

        # This should currently be completely ignored
        self.assertNotIn('force_online', args)
        self.assertNotIn('forceonline', args)
        mock_log.warning.assert_called_once_with(
            '--forceonline is deprecated. '
            'Online install is currently the only option, so this '
            'argument will be ignored.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    def test_args_chosen(self,
                         mock_linux,
                         mock_win,
                         mock_darwin):
        """Check that parse_args actually sets arguments."""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        set_args = self.get_cloudify.parse_args(['-f',
                                                 '--virtualenv=venv_path',
                                                 '--quiet',
                                                 '--version=3.2',
                                                 '--install-pip',
                                                 '--install-pythondev'])

        self.assertTrue(set_args['force'])
        self.assertTrue(set_args['install_pip'])
        self.assertTrue(set_args['quiet'])
        self.assertEqual(set_args['version'], '3.2')
        self.assertEqual(set_args['virtualenv'], 'venv_path')

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.argparse.ArgumentParser.error',
                side_effect=SystemExit)
    def test_with_requirements_alone_fails(self,
                                           mock_parse_error,
                                           mock_linux,
                                           mock_win,
                                           mock_darwin):
        """with_requirements should fail when used alone"""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        self.assertRaises(
            SystemExit,
            self.get_cloudify.parse_args,
            ['--with-requirements=test'],
        )

        mock_parse_error.assert_called_once_with(
            '--source or --use-branch is required when '
            'calling with --with-requirements.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    def test_with_requirements_and_use_branch(self,
                                              mock_linux,
                                              mock_win,
                                              mock_darwin):
        """with_requirements with use_branch should not fail"""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        # No need to assert, we're just happy not to have errors
        self.get_cloudify.parse_args(['--use-branch=test',
                                      '--with-requirements=test'])

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    def test_with_requirements_and_source(self,
                                          mock_linux,
                                          mock_win,
                                          mock_darwin):
        """with_requirements with source should not fail"""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        # No need to assert, we're just happy not to have errors
        self.get_cloudify.parse_args(['--source=test',
                                      '--with-requirements=test'])

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_source_with_no_requirements(self,
                                         mock_log,
                                         mock_linux,
                                         mock_win,
                                         mock_darwin):
        """source should warn if called without requirements"""
        # It's quite likely to be an error for anything but the most trivial
        # changes

        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        self.get_cloudify.parse_args([
            '--source=test',
        ])

        mock_log.warning.assert_called_once_with(
            'A source URL or branch was specified, but '
            '--with-requirements was omitted. You may need to retry using '
            '--with-requirements if the installation fails.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_branch_with_no_requirements(self,
                                         mock_log,
                                         mock_linux,
                                         mock_win,
                                         mock_darwin):
        """use_branch should warn if called without requirements"""
        # It's quite likely to be an error for anything but the most trivial
        # changes

        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        self.get_cloudify.parse_args([
            '--use-branch=test',
        ])

        mock_log.warning.assert_called_once_with(
            'A source URL or branch was specified, but '
            '--with-requirements was omitted. You may need to retry using '
            '--with-requirements if the installation fails.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.argparse.ArgumentParser.error',
                side_effect=SystemExit)
    def test_use_branch_invalid_format(self,
                                       mock_parse_error,
                                       mock_linux,
                                       mock_win,
                                       mock_darwin):
        """use_branch should not work with more than one slash"""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        self.assertRaises(
            SystemExit,
            self.get_cloudify.parse_args,
            ['--use-branch=test/this/fails'],
        )

        mock_parse_error.assert_called_once_with(
            '--use-branch should be specified either as '
            '<branch> or as <user>/<branch>. '
            'Too many "/" found in arguments.'
        )

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    def test_use_branch_just_branch(self,
                                    mock_log,
                                    mock_linux,
                                    mock_win,
                                    mock_darwin):
        """use_branch without slash should just set branch"""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        args = self.get_cloudify.parse_args([
            '--use-branch=test',
        ])

        expected_repo_url = self.expected_repo_url.format(
            user=self.expected_repo_default_user,
            branch='test',
        )

        self.assertEquals(expected_repo_url, args['source'])

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    def test_use_branch_user_and_branch(self,
                                        mock_linux,
                                        mock_win,
                                        mock_darwin):
        """use_branch with slash should set user and branch"""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        args = self.get_cloudify.parse_args([
            '--use-branch=user/branch',
        ])

        expected_repo_url = self.expected_repo_url.format(
            user='user',
            branch='branch',
        )

        self.assertEquals(expected_repo_url, args['source'])

    def test_mutually_exclusive_verbosity(self):
        ex = self.assertRaises(
            SystemExit, self.get_cloudify.parse_args, ['--verbose', '--quiet'])
        exit_code = ex.message
        self.assertEqual(2, exit_code)

    def test_mutually_exclusive_pre_version(self):
        ex = self.assertRaises(
            SystemExit, self.get_cloudify.parse_args, ['--version', '--pre'])
        exit_code = ex.message
        self.assertEqual(2, exit_code)

    def test_mutually_exclusive_version_source(self):
        ex = self.assertRaises(
            SystemExit,
            self.get_cloudify.parse_args,
            ['--version', '--source=test'],
        )
        exit_code = ex.message
        self.assertEqual(2, exit_code)

    def test_mutually_exclusive_pre_source(self):
        ex = self.assertRaises(
            SystemExit,
            self.get_cloudify.parse_args,
            ['--pre', '--source=test'],
        )
        exit_code = ex.message
        self.assertEqual(2, exit_code)

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    def test_listvar_with_requirements(self,
                                       mock_linux,
                                       mock_win,
                                       mock_darwin):
        """We are expecting to be able to provide multiple requirements"""
        # Original values will be restored by mock patch
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        self.get_cloudify.IS_DARWIN = False

        args = self.get_cloudify.parse_args([
            '--source=requiredwithargs',
            '--with-requirements', 'test.txt', 'test2.txt',
        ])

        self.assertEquals(
            ['test.txt', 'test2.txt'],
            args['with_requirements'],
        )


class ArgsObject(object):
    pass

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
import testtools
import urllib
import tempfile
from StringIO import StringIO
import mock
import shutil
import os
import tarfile
import logging
import importlib
import sys

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
        proc = self.get_cloudify.run('echo Hi!')
        self.assertEqual(proc.returncode, 0, 'process execution failed')

    def test_run_invalid_command(self):
        builder_stdout = StringIO()
        # replacing builder stdout
        self.get_cloudify.sys.stdout = builder_stdout
        cmd = 'this is not a valid command'
        proc = self.get_cloudify.run(cmd)
        self.assertIsNot(proc.returncode, 0, 'command \'{}\' execution was '
                                             'expected to fail'.format(cmd))

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.exit',
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
        return_value=[
            {
                'quiet': False,
                'verbose': False,
            },
            [],
        ],
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
        return_value=[
            {
                'quiet': False,
                'verbose': False,
            },
            [],
        ],
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
        return_value=[
            {
                'quiet': False,
                'verbose': False,
            },
            [],
        ],
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
        return_value=[
            {
                'quiet': True,
                'verbose': False,
            },
            [],
        ],
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
        return_value=[
            {
                'quiet': False,
                'verbose': True,
            },
            [],
        ],
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
        return_value=[
            {
                'quiet': False,
                'verbose': False,
                'fake_arg': 'this',
            },
            [],
        ],
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

    @mock.patch('get-cloudify.IS_LINUX')
    @mock.patch('get-cloudify.IS_WIN')
    @mock.patch('get-cloudify.IS_DARWIN')
    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.CloudifyInstaller')
    @mock.patch(
        'get-cloudify.parse_args',
        return_value=[
            {
                'quiet': False,
                'verbose': False,
                'fake_arg': 'this',
                'ignored_arg': 'that',
                'also_ignored': 'other',
            },
            [
                'ignored_arg',
                'also_ignored',
            ],
        ],
    )
    def test_main_deprecated_not_passed(self,
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

        self.get_cloudify.drop_root_privileges()
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

        self.get_cloudify.drop_root_privileges()
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

        self.get_cloudify.drop_root_privileges()
        self.assertFalse(mock_log.info.called)
        self.assertFalse(mock_os.setegid.called)
        self.assertFalse(mock_os.seteuid.called)

    @mock.patch('get-cloudify.sys.exit')
    @mock.patch('get-cloudify.logger')
    def test_exit_unsupported_os(self,
                                 mock_log,
                                 mock_exit):
        self.get_cloudify.exit(
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
        self.get_cloudify.exit(
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
        self.get_cloudify.exit(
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
        self.get_cloudify.exit(
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
        self.get_cloudify.exit(
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
        self.get_cloudify.exit(
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
        self.get_cloudify.exit(
            message='Cloudify already here',
            status='cloudify_already_installed',
        )

        mock_log.error.assert_called_once_with('Cloudify already here')
        mock_exit.assert_called_once_with(230)

    @mock.patch('get-cloudify.exit',
                side_effect=SystemExit)
    @mock.patch('get-cloudify.download_file',
                side_effect=StandardError('Boom!'))
    @mock.patch('get-cloudify.CloudifyInstaller.find_pip',
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

    @mock.patch('get-cloudify.exit',
                side_effect=SystemExit)
    @mock.patch('get-cloudify.download_file',
                return_value=None)
    @mock.patch('get-cloudify.CloudifyInstaller.find_pip',
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

    @mock.patch('get-cloudify.exit',
                side_effect=SystemExit)
    def test_make_virtualenv_fail(self, mock_exit):
        self.assertRaises(
            SystemExit,
            self.get_cloudify.make_virtualenv,
            '/path/to/dir',
            'non_existing_path',
        )

        mock_exit.assert_called_once_with(
            message='Could not create virtualenv: /path/to/dir',
            status='virtualenv_creation_failure',
        )

    @mock.patch('get-cloudify.exit',
                side_effect=SystemExit)
    def test_install_non_existing_module(self, mock_exit):
        self.assertRaises(
            SystemExit,
            self.get_cloudify.install_package,
            'nonexisting_module',
        )
        mock_exit.assert_called_once_with(
            message='Could not install package: nonexisting_module.',
            status='dependency_installation_failure',
        )

    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.run')
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

        self.get_cloudify.install_package('test-package')

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
    @mock.patch('get-cloudify.run')
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

        self.get_cloudify.install_package('test-package',
                                          virtualenv_path='/my/venv')

        mock_log.info.assert_called_once_with(
            'Installing test-package...',
        )
        mock_run.assert_called_once_with(
            '/my/venv/bin/pip install test-package',
        )

    @mock.patch('get-cloudify.logger')
    @mock.patch('get-cloudify.run')
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

        self.get_cloudify.install_package('test-package',
                                          virtualenv_path='/my/venv')

        mock_log.info.assert_called_once_with(
            'Installing test-package...',
        )
        mock_run.assert_called_once_with(
            '/my/venv/bin/pip install test-package',
        )

    def test_get_os_props(self):
        distro = self.get_cloudify.get_os_props()[0]
        distros = ('ubuntu', 'redhat', 'debian', 'fedora', 'centos',
                   'archlinux')
        if distro.lower() not in distros:
            self.fail('distro prop \'{0}\' should be equal to one of: '
                      '{1}'.format(distro, distros))

    def test_download_file(self):
        self.get_cloudify.VERBOSE = True
        tmp_file = tempfile.NamedTemporaryFile(delete=True)
        self.get_cloudify.download_file('http://www.google.com', tmp_file.name)
        with open(tmp_file.name) as f:
            content = f.readlines()
            self.assertIsNotNone(content)

    def test_check_cloudify_not_installed_in_venv(self):
        tmp_venv = tempfile.mkdtemp()
        installer = self.get_cloudify.CloudifyInstaller(virtualenv=tmp_venv)
        try:
            self.get_cloudify.make_virtualenv(tmp_venv, 'python')
            self.assertFalse(
                installer.check_cloudify_installed()
            )
        finally:
            shutil.rmtree(tmp_venv)

    def test_check_cloudify_installed_in_venv(self):
        tmp_venv = tempfile.mkdtemp()
        try:
            self.get_cloudify.make_virtualenv(tmp_venv, 'python')
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

        self.get_cloudify.download_file = get
        try:
            installer = self.get_cloudify.CloudifyInstaller()
            req_list = installer._get_default_requirement_files('null')
            self.assertEquals(len(req_list), 1)
            self.assertIn('dev-requirements.txt', req_list[0])
        finally:
            self.get_cloudify.download_file = get_cloudify.download_file

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

    def test_args_parser_linux(self):
        self.get_cloudify.IS_LINUX = True
        self.get_cloudify.IS_WIN = False
        args, _ = self.get_cloudify.parse_args([])
        self.assertNotIn('install_pycrypto', args)
        self.assertIn('install_pythondev', args)

    def test_args_parser_windows(self):
        self.get_cloudify.IS_LINUX = False
        self.get_cloudify.IS_WIN = True
        args, _ = self.get_cloudify.parse_args([])
        self.assertIn('install_pycrypto', args)
        self.assertNotIn('install_pythondev', args)

    def test_default_args(self):
        args, _ = self.get_cloudify.parse_args([])
        self.assertFalse(args['force'])
        self.assertFalse(args['forceonline'])
        self.assertFalse(args['installpip'])
        self.assertFalse(args['installvirtualenv'])
        self.assertFalse(args['pre'])
        self.assertFalse(args['quiet'])
        self.assertFalse(args['verbose'])
        self.assertIsNone(args['version'])
        self.assertIsNone(args['virtualenv'])

    def test_args_chosen(self):
        self.get_cloudify.IS_LINUX = True
        set_args, _ = self.get_cloudify.parse_args(['-f',
                                                    '--forceonline',
                                                    '--installpip',
                                                    '--virtualenv=venv_path',
                                                    '--quiet',
                                                    '--version=3.2',
                                                    '--installpip',
                                                    '--installpythondev'])

        self.assertTrue(set_args['force'])
        self.assertTrue(set_args['force_online'])
        self.assertTrue(set_args['install_pip'])
        self.assertTrue(set_args['quiet'])
        self.assertEqual(set_args['version'], '3.2')
        self.assertEqual(set_args['virtualenv'], 'venv_path')

    def test_mutually_exclude_groups(self):
        # # test with args that do not go together
        ex = self.assertRaises(
            SystemExit, self.get_cloudify.parse_args, ['--version', '--pre'])
        self.assertEqual(2, ex.message)

        ex = self.assertRaises(
            SystemExit, self.get_cloudify.parse_args, ['--verbose', '--quiet'])
        self.assertEqual(2, ex.message)

        ex = self.assertRaises(
            SystemExit, self.get_cloudify.parse_args,
            ['--wheels_path', '--force_online'])
        self.assertEqual(2, ex.message)


class ArgsObject(object):
    pass

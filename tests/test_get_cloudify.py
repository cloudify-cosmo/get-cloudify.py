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
            self.get_cloudify.install_module,
            'nonexisting_module',
        )
        mock_exit.assert_called_once_with(
            message='Could not install module: nonexisting_module.',
            status='dependency_install_failure',
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
        try:
            self.get_cloudify.make_virtualenv(tmp_venv, 'python')
            self.assertFalse(
                self.get_cloudify.check_cloudify_installed(tmp_venv))
        finally:
            shutil.rmtree(tmp_venv)

    def test_check_cloudify_installed_in_venv(self):
        tmp_venv = tempfile.mkdtemp()
        try:
            self.get_cloudify.make_virtualenv(tmp_venv, 'python')
            installer = get_cloudify.CloudifyInstaller(virtualenv=tmp_venv)
            installer.execute()
            self.assertTrue(
                self.get_cloudify.check_cloudify_installed(tmp_venv))
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
        self.assertEqual(args['wheels_path'], 'wheelhouse')

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

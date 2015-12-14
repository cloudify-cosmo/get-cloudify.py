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
import shutil
import tempfile
import mock
import os
import importlib
import sys

sys.path.append("../")

get_cloudify = importlib.import_module('get-cloudify')

cloudify_cli_url = \
    'https://github.com/cloudify-cosmo/cloudify-cli/archive/3.2.tar.gz'


class CliInstallTests(testtools.TestCase):
    @staticmethod
    def install_cloudify(args):
        installer = get_cloudify.CloudifyInstaller(**args)
        installer.execute()
        return installer

    def setUp(self):
        super(CliInstallTests, self).setUp()
        self.get_cloudify = get_cloudify

    def test_full_cli_install(self):
        tempdir = tempfile.mkdtemp()
        install_args = {
            'force': True,
            'virtualenv': tempdir,
        }

        try:
            self.install_cloudify(install_args)
            if self.get_cloudify.IS_WIN:
                cfy_name = 'cfy.exe'
            else:
                cfy_name = 'cfy'
            cfy_path = os.path.join(
                self.get_cloudify._get_env_bin_path(tempdir), cfy_name)
            proc = self.get_cloudify._run('{0} --version'.format(cfy_path))
            self.assertIn('Cloudify CLI 3', proc.aggr_stderr)
        finally:
            shutil.rmtree(tempdir)

    def test_install_from_source_with_requirements(self):
        tempdir = tempfile.mkdtemp()
        temp_requirements_file = os.path.join(tempdir, 'temprequirements.txt')
        with open(temp_requirements_file, 'w') as requirements_file:
            # We use mock for tests so we'll fail elsewhere on a name change
            requirements_file.write('mock')
        install_args = {
            'source': cloudify_cli_url,
            'with_requirements': [temp_requirements_file],
            'virtualenv': tempdir,
        }

        try:
            self.install_cloudify(install_args)
            if self.get_cloudify.IS_WIN:
                cfy_name = 'cfy.exe'
            else:
                cfy_name = 'cfy'
            cfy_path = os.path.join(
                self.get_cloudify._get_env_bin_path(tempdir), cfy_name)
            proc = self.get_cloudify._run('{0} --version'.format(cfy_path))
            self.assertIn('Cloudify CLI 3', proc.aggr_stderr)
            # TODO: We should check that mock also gets installed
        finally:
            shutil.rmtree(tempdir)

    def test_cli_installed_and_upgrade(self):
        tempdir = tempfile.mkdtemp()
        install_args = {
            'virtualenv': tempdir,
            'upgrade': True
        }

        try:
            self.install_cloudify(install_args)
            # Repeat should succeed with upgrade flag set
            self.install_cloudify(install_args)
        finally:
            shutil.rmtree(tempdir)

    @mock.patch('get-cloudify._exit',
                side_effect=SystemExit)
    def test_cli_installed_and_no_upgrade(self, mock_exit):
        tempdir = tempfile.mkdtemp()
        install_args = {
            'virtualenv': tempdir,
            'upgrade': False
        }

        try:
            self.install_cloudify(install_args)
            self.assertRaises(
                SystemExit,
                self.install_cloudify,
                install_args,
            )
            mock_exit.assert_called_once_with(
                message='Use the --upgrade flag to upgrade.',
                status='cloudify_already_installed',
            )
        finally:
            shutil.rmtree(tempdir)

    def test_cli_specific_version(self):
        tempdir = tempfile.mkdtemp()
        install_args = {
            'virtualenv': tempdir,
            'version': '3.2'
        }
        try:
            self.install_cloudify(install_args)
            if self.get_cloudify.IS_WIN:
                cfy_name = 'cfy.exe'
            else:
                cfy_name = 'cfy'
            cfy_path = os.path.join(
                self.get_cloudify._get_env_bin_path(tempdir), cfy_name)
            proc = self.get_cloudify._run('{0} --version'.format(cfy_path))
            self.assertIn('Cloudify CLI 3.2', proc.aggr_stderr)
        finally:
            shutil.rmtree(tempdir)

    # Note: This test WILL fail when there is no PRE version (e.g. just after
    # a major version is released)
    def test_cli_install_pre(self):
        tempdir = tempfile.mkdtemp()
        install_args = {
            'virtualenv': tempdir,
            'pre': True
        }
        try:
            self.install_cloudify(install_args)
            if self.get_cloudify.IS_WIN:
                cfy_name = 'cfy.exe'
            else:
                cfy_name = 'cfy'
            cfy_path = os.path.join(
                self.get_cloudify._get_env_bin_path(tempdir), cfy_name)
            proc = self.get_cloudify._run('{0} --version'.format(cfy_path))
            self.assertIn('Cloudify CLI 3', proc.aggr_stderr)
            # We would also like to check that m (milestone) or r (release
            # candidate) appears in the output, but that doesn't happen all of
            # the time- e.g. it is absent just after a major release.
        finally:
            shutil.rmtree(tempdir)

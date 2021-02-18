# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.lib import decorators

from senlin_tempest_plugin.common import utils
from senlin_tempest_plugin.tests.api import base


class TestProfileTypeOpeList(base.BaseSenlinAPITest):

    @utils.api_microversion('1.4')
    @decorators.idempotent_id('c4216ea0-df06-434d-b51f-bc1b5661c0bb')
    def test_profile_type_operation_list(self):
        res = self.client.list_profile_type_operation('os.nova.server-1.0')

        # Verify resp of profile type operation list API
        self.assertEqual(200, res['status'])
        self.assertIn('change_password', res['body'])
        self.assertIn('description', res['body']['change_password'])
        self.assertIn('parameters', res['body']['change_password'])

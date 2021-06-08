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


class TestServicesList(base.BaseSenlinAPITest):

    @utils.api_microversion('1.7')
    @decorators.idempotent_id('ff263248-19e2-488d-8fb3-fc09ed3b078e')
    def test_services_list(self):
        res = self.admin_client.list_objs('services')

        self.assertEqual(200, res['status'])
        self.assertIsNotNone(res['body'])
        services = res['body']
        for service in services:
            for key in ['binary', 'host', 'id', 'state',
                        'status', 'topic', 'updated_at']:
                self.assertIn(key, service)

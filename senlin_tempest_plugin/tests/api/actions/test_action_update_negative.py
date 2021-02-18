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
from tempest.lib import exceptions

from senlin_tempest_plugin.common import utils
from senlin_tempest_plugin.tests.api import base


class TestActionUpdateNegative(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestActionUpdateNegative, self).setUp()
        profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, profile_id)

        params = {
            'cluster': {
                'profile_id': profile_id,
                'desired_capacity': 0,
                'min_size': 0,
                'max_size': -1,
                'timeout': None,
                'metadata': {},
                'name': 'test-cluster-action-show'
            }
        }
        res = self.client.create_obj('clusters', params)
        self.action_id = res['location'].split('/actions/')[1]
        self.addCleanup(utils.delete_a_cluster, self, res['body']['id'])

        self.client.wait_for_status('actions', self.action_id, 'SUCCEEDED')

    @utils.api_microversion('1.12')
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('72a123c3-cbce-4452-bb53-d3c939116c2f')
    def test_action_update_not_found(self):
        params = {
            "action": {
                "status": "CANCELLED",
            }
        }
        self.assertRaises(
            exceptions.NotFound, self.client.update_obj, 'actions',
            '26cb0f3a-4e6c-49f6-8475-7cb472933bff', params)

    @utils.api_microversion('1.12')
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('802b24bc-7004-4b25-8b53-a3709e0ad6ed')
    def test_action_update_status_invalid(self):
        params = {
            "action": {
                "status": "invalid",
            }
        }
        self.assertRaises(
            exceptions.BadRequest, self.client.update_obj, 'actions',
            self.action_id, params)

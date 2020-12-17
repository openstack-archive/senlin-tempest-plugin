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


class TestReceiverUpdate(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestReceiverUpdate, self).setUp()
        profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, profile_id)

        cluster_id = utils.create_a_cluster(self, profile_id)
        self.addCleanup(utils.delete_a_cluster, self, cluster_id)

        self.receiver_id = utils.create_a_receiver(self, cluster_id,
                                                   'CLUSTER_SCALE_IN',
                                                   params={"count": 5})
        self.addCleanup(self.client.delete_obj, 'receivers', self.receiver_id)

    @decorators.idempotent_id('fdb2f393-effb-4794-95ac-1f6a119f4474')
    def test_receiver_update(self):
        params = {
            "receiver": {
                "name": "update-receiver-name",
                "action": "CLUSTER_SCALE_IN",
                "params": {
                    "count": "2"
                }
            }
        }
        res = self.client.update_obj('receivers', self.receiver_id, params)

        self.assertEqual(200, res['status'])
        self.assertIsNotNone(res['body'])
        receivers = res['body']

        for key in ['action', 'cluster_id', 'created_at', 'domain', 'id',
                    'name', 'params', 'project', 'type', 'updated_at', 'user']:
            self.assertIn(key, receivers)
        self.assertEqual('update-receiver-name', receivers['name'])
        self.assertEqual({'count': '2'}, receivers['params'])

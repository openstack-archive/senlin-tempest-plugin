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

from tempest import config
from tempest.lib import decorators
import testtools

from senlin_tempest_plugin.common import utils
from senlin_tempest_plugin.tests.api import base

CONF = config.CONF


class TestClusterDelete(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestClusterDelete, self).setUp()
        profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, profile_id)

        # cluster will be deleted by test case
        self.cluster_id = utils.create_a_cluster(self, profile_id)

    @decorators.idempotent_id('33d7426e-0138-42c9-9ab4-ba796a7d1fdc')
    def test_cluster_delete_in_active_status(self):
        res = self.client.delete_obj('clusters', self.cluster_id)

        # Verify resp code, body and location in headers
        self.assertEqual(202, res['status'])
        self.assertIsNone(res['body'])
        self.assertIn('actions', res['location'])

        action_id = res['location'].split('/actions/')[1]
        self.client.wait_for_status('actions', action_id, 'SUCCEEDED')


class TestClusterDeleteWithPolicy(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestClusterDeleteWithPolicy, self).setUp()
        profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, profile_id)

        self.cluster_id = utils.create_a_cluster(self, profile_id)

        policy_id = utils.create_a_policy(self)
        self.addCleanup(utils.delete_a_policy, self, policy_id)

        utils.cluster_attach_policy(self, self.cluster_id, policy_id)

    @decorators.idempotent_id('e563b05d-6b7f-4207-a7ac-e48e6607d4d8')
    @testtools.skipUnless(CONF.clustering.delete_with_dependency,
                          'Deleting clusters with dependancies not enabled')
    def test_cluster_delete_policy(self):
        res = self.client.delete_obj('clusters', self.cluster_id)

        # Verify resp code, body and location in headers
        self.assertEqual(202, res['status'])
        self.assertIsNone(res['body'])
        self.assertIn('actions', res['location'])

        action_id = res['location'].split('/actions/')[1]
        self.client.wait_for_status('actions', action_id, 'SUCCEEDED')


class TestClusterDeleteReceiver(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestClusterDeleteReceiver, self).setUp()
        profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, profile_id)

        self.cluster_id = utils.create_a_cluster(self, profile_id)

        self.receiver_id = utils.create_a_receiver(
            self, self.cluster_id, 'CLUSTER_SCALE_OUT', 'webhook',
            'fake', params={'count': '1'})

    @decorators.idempotent_id('bff84a28-1b81-42f2-ae88-42f50c9f0bb9')
    @testtools.skipUnless(CONF.clustering.delete_with_dependency,
                          'Deleting clusters with dependancies not enabled')
    def test_cluster_delete_receiver(self):
        res = self.client.delete_obj('clusters', self.cluster_id)

        # Verify resp code, body and location in headers
        self.assertEqual(202, res['status'])
        self.assertIsNone(res['body'])
        self.assertIn('actions', res['location'])

        action_id = res['location'].split('/actions/')[1]
        self.client.wait_for_status('actions', action_id, 'SUCCEEDED')

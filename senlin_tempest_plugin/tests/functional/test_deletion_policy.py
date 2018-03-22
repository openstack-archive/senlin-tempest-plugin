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

from senlin_tempest_plugin.common import constants
from senlin_tempest_plugin.common import utils
from senlin_tempest_plugin.tests.functional import base


class TestDeletionPolicy(base.BaseSenlinFunctionalTest):

    def setUp(self):
        super(TestDeletionPolicy, self).setUp()
        self.profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, self.profile_id)
        self.cluster_id = utils.create_a_cluster(self, self.profile_id,
                                                 min_size=0, max_size=5,
                                                 desired_capacity=2)
        self.addCleanup(utils.delete_a_cluster, self, self.cluster_id)

    @decorators.attr(type=['functional'])
    @decorators.idempotent_id('bc4af63f-c236-4e8c-a644-d6211c2ec160')
    def test_deletion_policy(self):
        # Create a deletion policy
        spec = constants.spec_deletion_policy
        policy_id = utils.create_a_policy(self, spec)
        del_policy = utils.get_a_policy(self, policy_id)
        self.addCleanup(utils.delete_a_policy, self, del_policy['id'])

        # Attach deletion policy to cluster
        utils.cluster_attach_policy(self, self.cluster_id, del_policy['id'])
        self.addCleanup(utils.cluster_detach_policy, self, self.cluster_id,
                        del_policy['id'])

        # Scale out cluster
        utils.cluster_scale_out(self, self.cluster_id)

        # Verify scale out result
        cluster = utils.get_a_cluster(self, self.cluster_id)
        self.assertEqual('ACTIVE', cluster['status'])
        self.assertEqual(3, cluster['desired_capacity'])
        self.assertEqual(3, len(cluster['nodes']))

        # Scale in cluster
        utils.cluster_scale_in(self, self.cluster_id)

        # Verify scale in result
        cluster = utils.get_a_cluster(self, self.cluster_id)
        self.assertEqual('ACTIVE', cluster['status'])
        self.assertEqual(2, cluster['desired_capacity'])
        self.assertEqual(2, len(cluster['nodes']))

    @decorators.attr(type=['functional'])
    @decorators.idempotent_id('b08a229f-2cd4-496a-950a-1daff78e4e70')
    def test_deletion_policy_with_hook(self):
        # Create a deletion policy with hook
        spec = constants.spec_deletion_policy_with_hook
        policy_id = utils.create_a_policy(self, spec)
        del_policy = utils.get_a_policy(self, policy_id)
        self.addCleanup(utils.delete_a_policy, self, del_policy['id'])

        # Attach deletion policy to cluster
        utils.cluster_attach_policy(self, self.cluster_id, del_policy['id'])
        self.addCleanup(utils.cluster_detach_policy, self, self.cluster_id,
                        del_policy['id'])

        # Scale out cluster
        utils.cluster_scale_out(self, self.cluster_id)

        # Verify scale out result
        cluster = utils.get_a_cluster(self, self.cluster_id)
        self.assertEqual('ACTIVE', cluster['status'])
        self.assertEqual(3, cluster['desired_capacity'])
        self.assertEqual(3, len(cluster['nodes']))

        # Scale in cluster
        _, action_id = utils.cluster_scale_in(self, self.cluster_id,
                                              expected_status='WAITING')

        # get action details of scale in action
        action = utils.get_a_action(self, action_id)
        self.assertTrue(1, len(action['depends_on']))

        # get dependent action and check status
        dep_action_id = action['depends_on'][0]
        dep_action = utils.get_a_action(self, dep_action_id)
        self.assertEqual('WAITING_LIFECYCLE_COMPLETION', dep_action['status'])

        # complete lifecycle
        utils.cluster_complete_lifecycle(self, self.cluster_id,
                                         dep_action_id, wait_timeout=10)

        # verify cluster has been scaled in
        cluster = utils.get_a_cluster(self, self.cluster_id)
        self.assertEqual('ACTIVE', cluster['status'])
        self.assertEqual(2, cluster['desired_capacity'])
        self.assertEqual(2, len(cluster['nodes']))

    @decorators.attr(type=['functional'])
    @decorators.idempotent_id('88ea4617-10a6-4005-a641-b9459418661f')
    def test_deletion_policy_with_hook_timeout(self):
        # Create a deletion policy with hook
        spec = constants.spec_deletion_policy_with_hook
        spec['properties']['hooks']['timeout'] = 1

        policy_id = utils.create_a_policy(self, spec)
        del_policy = utils.get_a_policy(self, policy_id)
        self.addCleanup(utils.delete_a_policy, self, del_policy['id'])

        # Attach deletion policy to cluster
        utils.cluster_attach_policy(self, self.cluster_id, del_policy['id'])
        self.addCleanup(utils.cluster_detach_policy, self, self.cluster_id,
                        del_policy['id'])

        # Scale out cluster
        utils.cluster_scale_out(self, self.cluster_id)

        # Verify scale out result
        cluster = utils.get_a_cluster(self, self.cluster_id)
        self.assertEqual('ACTIVE', cluster['status'])
        self.assertEqual(3, cluster['desired_capacity'])
        self.assertEqual(3, len(cluster['nodes']))

        # Scale in cluster
        _, action_id = utils.cluster_scale_in(self, self.cluster_id,
                                              expected_status='SUCCEEDED',
                                              wait_timeout=10)

        # verify cluster has been scaled in
        cluster = utils.get_a_cluster(self, self.cluster_id)
        self.assertEqual('ACTIVE', cluster['status'])
        self.assertEqual(2, cluster['desired_capacity'])
        self.assertEqual(2, len(cluster['nodes']))

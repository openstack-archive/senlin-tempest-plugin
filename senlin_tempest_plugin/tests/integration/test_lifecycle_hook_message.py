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
from senlin_tempest_plugin.tests.integration import base


class TestLifecycleHookMessage(base.BaseSenlinIntegrationTest):

    def setUp(self):
        super(TestLifecycleHookMessage, self).setUp()
        self.profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, self.profile_id)
        self.cluster_id = utils.create_a_cluster(self, self.profile_id,
                                                 min_size=0, max_size=5,
                                                 desired_capacity=2)
        self.addCleanup(utils.delete_a_cluster, self, self.cluster_id)

    @decorators.skip_because(bug="1747904")
    @decorators.attr(type=['integration'])
    @decorators.idempotent_id('9ac7ed9d-7338-45fb-b749-f67ddeb6caa2')
    def test_lifecycle_hook_message(self):
        # Create a deletion policy with hook
        spec = constants.spec_deletion_policy_with_hook
        policy_id = utils.create_a_policy(self, spec)
        del_policy = utils.get_a_policy(self, policy_id)
        self.addCleanup(utils.delete_a_policy, self, del_policy['id'])

        # Create zaqar queue
        queue_name = spec['properties']['hooks']['params']['queue']
        utils.create_queue(self, queue_name)
        self.addCleanup(utils.delete_queue, self, queue_name)

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

        # get lifecycle hook message from zaqar queue
        messages = utils.list_messages(self, queue_name)
        self.assertEqual(1, len(messages))
        lifecycle_hook_message = messages[0]['body']

        # get dependent action and check status
        dep_action_id = action['depends_on'][0]
        dep_action = utils.get_a_action(self, dep_action_id)
        self.assertEqual('WAITING_LIFECYCLE_COMPLETION', dep_action['status'])
        self.assertEqual(dep_action_id,
                         lifecycle_hook_message['lifecycle_action_token'])
        self.assertEqual(dep_action['target'],
                         lifecycle_hook_message['node_id'])

        # complete lifecycle
        utils.cluster_complete_lifecycle(self, self.cluster_id,
                                         dep_action_id, wait_timeout=10)

        # verify cluster has been scaled in
        cluster = utils.get_a_cluster(self, self.cluster_id,
                                      expected_status='ACTIVE')
        self.assertEqual(2, cluster['desired_capacity'])
        self.assertEqual(2, len(cluster['nodes']))

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

import six

from tempest.lib import decorators

from senlin_tempest_plugin.common import utils
from senlin_tempest_plugin.tests.integration import base


class TestNovaServerCluster(base.BaseSenlinIntegrationNonAdminTest):

    def setUp(self):
        super(TestNovaServerCluster, self).setUp()
        utils.prepare_and_cleanup_for_nova_server(self)
        self.profile_id = utils.create_a_profile(self, self.spec)
        self.addCleanup(utils.delete_a_profile, self, self.profile_id)

    @decorators.attr(type=['integration'])
    @decorators.idempotent_id('c26eae1c-5c46-4a5f-be63-954d7229c8cc')
    def test_cluster_create_delete(self):
        # Create a cluster
        desired_capacity = 2
        min_size = 1
        max_size = 3
        metadata = {'k1': 'v1'}
        timeout = 600
        cluster_id = utils.create_a_cluster(
            self, self.profile_id, desired_capacity, min_size, max_size,
            timeout, metadata)

        # Verify creation result
        cluster = utils.get_a_cluster(self, cluster_id)
        self.assertIsNotNone(cluster)
        self.assertEqual(desired_capacity, cluster['desired_capacity'])
        self.assertEqual(desired_capacity, len(cluster['nodes']))
        for nid in cluster['nodes']:
            node = utils.get_a_node(self, nid, show_details=True)
            self.assertEqual('ACTIVE', node['status'])
            self.assertEqual(cluster_id, node['cluster_id'])
            self.assertIsNotNone(node['details'])
            self.assertEqual('ACTIVE', node['details']['status'])
            self.assertEqual(self.spec['properties']['flavor'],
                             node['details']['flavor'])
            self.assertEqual(self.spec['properties']['name'],
                             node['details']['name'])
            metadata = {
                'cluster_id': cluster['id'],
                'cluster_node_id': node['id'],
                'cluster_node_index': six.text_type(node['index'])
            }
            self.assertEqual(metadata, node['details']['metadata'])

        # Delete cluster
        utils.delete_a_cluster(self, cluster_id)

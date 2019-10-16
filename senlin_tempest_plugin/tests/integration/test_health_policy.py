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
from tempest.lib import exceptions
import time

from senlin_tempest_plugin.common import constants
from senlin_tempest_plugin.common import utils
from senlin_tempest_plugin.tests.integration import base

CONF = config.CONF


class TestHealthPolicy(base.BaseSenlinIntegrationTest):
    def setUp(self):
        super(TestHealthPolicy, self).setUp()

        spec = utils.create_spec_from_config()
        spec['properties']['networks'][0]['network'] = 'private-hp'
        utils.prepare_and_cleanup_for_nova_server(self, "192.168.199.0/24",
                                                  spec)
        self.profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, self.profile_id)
        self.cluster_id = utils.create_a_cluster(self, self.profile_id,
                                                 min_size=0, max_size=5,
                                                 desired_capacity=1)
        self.addCleanup(utils.delete_a_cluster, self, self.cluster_id)

    @classmethod
    def skip_checks(cls):
        super(TestHealthPolicy, cls).skip_checks()
        if CONF.clustering.health_policy_version != '1.1':
            skip_msg = ("%s skipped as only Health Policy 1.1 is supported" %
                        cls.__name__)
            raise cls.skipException(skip_msg)

    def _detach_policy(self, policy_id):
        # ignore BadRequest exceptions that are raised because
        # policy is not attached
        try:
            utils.cluster_detach_policy(self, self.cluster_id, policy_id)

            # wait to let health checks stop
            time.sleep(5)
        except exceptions.BadRequest:
            pass

    @decorators.attr(type=['integration'])
    def test_health_policy(self):
        # Create a health policy
        spec = constants.spec_health_policy
        policy_id = utils.create_a_policy(self, spec)
        del_policy = utils.get_a_policy(self, policy_id)
        self.addCleanup(utils.delete_a_policy, self, del_policy['id'], True)
        http_server, log_file = utils.start_http_server()
        self.addCleanup(utils.terminate_http_server, http_server, log_file)

        # Attach health policy to cluster
        utils.cluster_attach_policy(self, self.cluster_id, del_policy['id'])
        self.addCleanup(self._detach_policy, del_policy['id'])

        # wait for health checks to run
        time.sleep(5)

        # check that URL was queried for each node as part of health check
        out = utils.terminate_http_server(http_server, log_file)
        self.assertTrue(out.count('GET') == 1)

    def _get_node(self, expected_len, index):
        # get physical id of node (cluster is expected to only contain 1 node)
        raw_nodes = utils.list_nodes(self)
        nodes = {
            n['id']: n['physical_id'] for n in raw_nodes
            if n['cluster_id'] == self.cluster_id
        }
        self.assertTrue(len(nodes) == expected_len)

        return list(nodes.keys())[index], list(nodes.values())[index]

    @decorators.idempotent_id('52f34125-3d6e-4250-9d2e-b619a2905969')
    @decorators.attr(type=['integration'])
    def test_multiple_detection_modes_any(self):
        # Create a health policy
        spec = constants.spec_health_policy
        spec['properties']['detection']['recovery_conditional'] = 'ANY_FAILED'
        policy_id = utils.create_a_policy(self, spec)
        del_policy = utils.get_a_policy(self, policy_id)
        self.addCleanup(utils.delete_a_policy, self, del_policy['id'], True)
        http_server, log_file = utils.start_http_server()
        self.addCleanup(utils.terminate_http_server, http_server, log_file)

        # manually shutdown server
        node_id, server_id = self._get_node(1, 0)
        self.compute_client.run_operation_obj(
            'servers', server_id, 'action', {'os-stop': None})

        # verify that server is shutdown
        self.compute_client.wait_for_status('servers', server_id,
                                            'SHUTOFF', 60)

        # Attach health policy to cluster
        utils.cluster_attach_policy(self, self.cluster_id, del_policy['id'])
        self.addCleanup(self._detach_policy, del_policy['id'])

        # wait for health checks to run and recover node
        time.sleep(15)

        # verify that node has been recovered
        self.client.wait_for_status('nodes', node_id, 'ACTIVE', 60)

        # verify that new server is ACTIVE
        old_server_id = server_id
        node_id, server_id = self._get_node(1, 0)
        self.assertNotEqual(old_server_id, server_id)
        self.compute_client.wait_for_status('servers', server_id, 'ACTIVE', 60)

        # verify that old server no longer exists
        self.assertRaises(
            exceptions.NotFound,
            self.compute_client.get_obj, 'servers', old_server_id)

    @decorators.attr(type=['integration'])
    def test_multiple_detection_modes_all(self):
        # Create a health policy
        spec = constants.spec_health_policy
        spec['properties']['detection']['recovery_conditional'] = 'ALL_FAILED'
        policy_id = utils.create_a_policy(self, spec)
        del_policy = utils.get_a_policy(self, policy_id)
        self.addCleanup(utils.delete_a_policy, self, del_policy['id'], True)
        http_server, log_file = utils.start_http_server()
        self.addCleanup(utils.terminate_http_server, http_server, log_file)

        # manually shutdown server
        node_id, server_id = self._get_node(1, 0)
        self.compute_client.run_operation_obj(
            'servers', server_id, 'action', {'os-stop': None})

        # verify that server is shutdown
        self.compute_client.wait_for_status('servers', server_id,
                                            'SHUTOFF', 60)

        # Attach health policy to cluster
        utils.cluster_attach_policy(self, self.cluster_id, del_policy['id'])
        self.addCleanup(self._detach_policy, del_policy['id'])

        # wait for health checks to run
        time.sleep(15)

        # verify that node status has not changed
        res = self.client.get_obj('nodes', node_id)
        self.assertEqual(res['body']['status'], 'ACTIVE')

        # verify that server is still stopped
        res = self.compute_client.get_obj('servers', server_id)
        self.assertEqual(res['body']['status'], 'SHUTOFF')

        # check that URL was queried because ALL_FAILED
        # was specified in the policy
        out = utils.terminate_http_server(http_server, log_file)
        self.assertTrue(out.count('GET') >= 0)

        # wait for health checks to run and recover node
        time.sleep(15)

        # verify that node has been recovered
        self.client.wait_for_status('nodes', node_id, 'ACTIVE', 60)

        # verify that new server is ACTIVE
        old_server_id = server_id
        node_id, server_id = self._get_node(1, 0)
        self.assertNotEqual(old_server_id, server_id)
        self.compute_client.wait_for_status('servers', server_id, 'ACTIVE', 60)

        # verify that old server no longer exists
        self.assertRaises(
            exceptions.NotFound,
            self.compute_client.get_obj, 'servers', old_server_id)

    @decorators.attr(type=['integration'])
    def test_multiple_detection_modes_all_poll_url_fail(self):
        # Create a health policy
        spec = constants.spec_health_policy
        spec['properties']['detection']['recovery_conditional'] = 'ALL_FAILED'
        policy_id = utils.create_a_policy(self, spec)
        del_policy = utils.get_a_policy(self, policy_id)
        self.addCleanup(utils.delete_a_policy, self, del_policy['id'], True)

        # get node_id
        node_id, server_id = self._get_node(1, 0)

        # Attach health policy to cluster without http server running
        utils.cluster_attach_policy(self, self.cluster_id, del_policy['id'])
        self.addCleanup(self._detach_policy, del_policy['id'])

        # wait for health checks to run
        time.sleep(15)

        # verify that node status has not changed
        res = self.client.get_obj('nodes', node_id)
        self.assertEqual(res['body']['status'], 'ACTIVE')

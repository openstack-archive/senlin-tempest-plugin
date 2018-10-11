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
from tempest.lib import exceptions as exc
import time

from senlin_tempest_plugin.common import constants
from senlin_tempest_plugin.common import utils
from senlin_tempest_plugin.tests.functional import base


@decorators.skip_because(bug=1797270)
class TestHealthPolicy(base.BaseSenlinFunctionalTest):
    def setUp(self):
        super(TestHealthPolicy, self).setUp()

        self.profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, self.profile_id)
        self.cluster_id = utils.create_a_cluster(self, self.profile_id,
                                                 min_size=0, max_size=5,
                                                 desired_capacity=1)
        self.addCleanup(utils.delete_a_cluster, self, self.cluster_id)

    @decorators.attr(type=['functional'])
    @decorators.idempotent_id('adfd813c-08c4-4650-9b66-a1a6e63b842e')
    def test_health_policy(self):
        # Create a health policy
        spec = constants.spec_health_policy
        policy_id = utils.create_a_policy(self, spec)
        del_policy = utils.get_a_policy(self, policy_id)
        self.addCleanup(utils.delete_a_policy, self, del_policy['id'], True)
        http_server = utils.start_http_server('5050')
        self.addCleanup(utils.terminate_http_server, http_server)

        # Attach health policy to cluster
        utils.cluster_attach_policy(self, self.cluster_id, del_policy['id'])
        self.addCleanup(utils.cluster_detach_policy, self, self.cluster_id,
                        del_policy['id'])

        # wait for health checks to run
        time.sleep(15)

        # check that URL was queried for each node as part of health check
        out = utils.terminate_http_server(http_server)
        self.assertTrue(out.count('GET') >= 1)

    @decorators.attr(type=['functional'])
    @decorators.idempotent_id('569ca522-00ec-4c1e-b217-4f89d13fe800')
    def test_invalid_health_policy_duplicate_type(self):
        # Create a health policy
        spec = constants.spec_health_policy_duplicate_type
        with self.assertRaisesRegex(
                exc.BadRequest,
                '.*(?i)duplicate detection modes.*'):
            utils.create_a_policy(self, spec)

    @decorators.attr(type=['functional'])
    @decorators.idempotent_id('6f0e0d2c-4381-4afb-ac17-3c2cfed35829')
    def test_invalid_health_policy_invalid_combo(self):
        # Create a health policy
        spec = constants.spec_health_policy_invalid_combo
        with self.assertRaisesRegex(
                exc.BadRequest,
                '.*(?i)invalid detection modes.*'):
            utils.create_a_policy(self, spec)

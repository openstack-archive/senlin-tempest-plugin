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


class TestClusterDeleteNegativeNotFound(base.BaseSenlinAPITest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8a583b8e-eeaa-4920-a6f5-2880b070624f')
    def test_cluster_delete_not_found(self):
        # Verify notfound exception(404) is raised.
        ex = self.assertRaises(exceptions.NotFound,
                               self.client.delete_obj,
                               'clusters',
                               '8a583b8e-eeaa-4920-a6f5-2880b070624f')

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The cluster '8a583b8e-eeaa-4920-a6f5-2880b070624f' could "
            "not be found.", str(message))


class TestClusterDeleteNegativeBadRequest(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestClusterDeleteNegativeBadRequest, self).setUp()
        profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, profile_id)

        self.cluster_id1 = utils.create_a_cluster(self, profile_id,
                                                  name='c-01')
        self.addCleanup(utils.delete_a_cluster, self, self.cluster_id1)
        self.cluster_id2 = utils.create_a_cluster(self, profile_id,
                                                  name='c-01')
        self.addCleanup(utils.delete_a_cluster, self, self.cluster_id2)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('3d8b73db-e2d2-42c2-952c-936048d36f21')
    def test_cluster_delete_multiple_choice(self):
        # Verify badrequest exception(400) is raised.
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.delete_obj,
                               'clusters', 'c-01')

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "Multiple results found matching the query criteria 'c-01'. "
            "Please be more specific.", str(message))

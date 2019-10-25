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


class TestProfileDeleteNegativeConflict(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestProfileDeleteNegativeConflict, self).setUp()
        self.profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, self.profile_id)
        cluster_id = utils.create_a_cluster(self, self.profile_id)
        self.addCleanup(utils.delete_a_cluster, self, cluster_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8e5e8414-b757-41f4-b633-e0fa83d72ea2')
    def test_profile_delete_conflict(self):
        # Verify conflict exception(409) is raised.
        ex = self.assertRaises(exceptions.Conflict,
                               self.client.delete_obj,
                               'profiles', self.profile_id)

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The profile '%s' cannot be deleted: still referenced by "
            "some clusters and/or nodes." % self.profile_id, str(message))


class TestProfileDeleteNegativeNotFound(base.BaseSenlinAPITest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('41990227-e75c-4fc3-9503-87aa7ac06e7e')
    def test_profile_delete_not_found(self):
        # Verify notfound exception(404) is raised.
        ex = self.assertRaises(exceptions.NotFound,
                               self.client.delete_obj, 'profiles',
                               'b6e7911d-5f65-4ec6-a08b-b88809fe2b9e')

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The profile 'b6e7911d-5f65-4ec6-a08b-b88809fe2b9e' "
            "could not be found.", str(message))


class TestProfileDeleteNegativeBadRequest(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestProfileDeleteNegativeBadRequest, self).setUp()
        self.profile_id1 = utils.create_a_profile(self, name='p-01')
        self.addCleanup(utils.delete_a_profile, self, self.profile_id1)
        self.profile_id2 = utils.create_a_profile(self, name='p-01')
        self.addCleanup(utils.delete_a_profile, self, self.profile_id2)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b6e7911d-5f65-4ec6-a08b-b88809fe2b9e')
    def test_profile_delete_multiple_choice(self):
        # Verify badrequest exception(400) is raised.
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.delete_obj,
                               'profiles', 'p-01')

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "Multiple results found matching the query criteria 'p-01'. "
            "Please be more specific.", str(message))

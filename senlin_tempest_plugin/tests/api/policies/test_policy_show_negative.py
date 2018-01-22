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


class TestPolicyShowNegativeNotFound(base.BaseSenlinAPITest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f1615466-7fca-4670-8c9a-66cb4bb24e54')
    def test_policy_show_not_found(self):
        ex = self.assertRaises(exceptions.NotFound,
                               self.client.get_obj, 'policies',
                               'f1615466-7fca-4670-8c9a-66cb4bb24e54')

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The policy 'f1615466-7fca-4670-8c9a-66cb4bb24e54' "
            "could not be found.", str(message))


class TestPolicyShowNegativeBadRequest(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestPolicyShowNegativeBadRequest, self).setUp()
        self.policy_id1 = utils.create_a_policy(self, name='p-01')
        self.policy_id2 = utils.create_a_policy(self, name='p-01')
        self.addCleanup(utils.delete_a_policy, self, self.policy_id1)
        self.addCleanup(utils.delete_a_policy, self, self.policy_id2)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c2eadbae-29b7-4d12-a407-259f387286f5')
    def test_policy_show_multiple_choice(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.get_obj,
                               'policies', 'p-01')

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "Multiple results found matching the query criteria 'p-01'. "
            "Please be more specific.", str(message))

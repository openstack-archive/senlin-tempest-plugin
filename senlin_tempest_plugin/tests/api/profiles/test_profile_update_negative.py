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


class TestProfileUpdateNegativeNotFound(base.BaseSenlinAPITest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5fe90195-aaed-4c1f-a73a-806b3f044bf8')
    def test_profile_update_profile_not_found(self):
        ex = self.assertRaises(exceptions.NotFound,
                               self.client.update_obj, 'profiles',
                               '5fe90195-aaed-4c1f-a73a-806b3f044bf8',
                               {'profile': {'name': 'new-name'}})

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The profile '5fe90195-aaed-4c1f-a73a-806b3f044bf8' "
            "could not be found.", str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('12a6772b-baea-47cc-a689-528a8e48ae22')
    def test_profile_update_profile_no_param(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.update_obj, 'profiles',
                               '5fe90195-aaed-4c1f-a73a-806b3f044bf8',
                               {})

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "Malformed request data, missing 'profile' key in "
            "request body.", str(message))


class TestProfileUpdateNegativeBadRequest(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestProfileUpdateNegativeBadRequest, self).setUp()
        # Create a profile
        profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, profile_id)
        self.profile_id = profile_id

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('45df7339-8fff-459a-b4e3-0aeafbcb4232')
    def test_profile_update_no_property_updated(self):
        # No property is updated
        params = {
            'profile': {}
        }
        # Verify badrequest exception(400) is raised.
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.update_obj,
                               'profiles', self.profile_id, params)

        message = ex.resp_body['error']['message']
        self.assertEqual("No property needs an update.",
                         str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0f4edfc0-78fa-414e-b995-100b67544410')
    def test_profile_update_spec_not_updatable(self):
        # Try to update spec of profile which is not allowed.
        params = {
            'profile': {
                'name': 'new-name',
                'spec': {'k1': 'v1'}
            }
        }
        # Verify badrequest exception(400) is raised.
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.update_obj,
                               'profiles', self.profile_id, params)

        message = ex.resp_body['error']['message']
        self.assertIn("Additional properties are not allowed", str(message))

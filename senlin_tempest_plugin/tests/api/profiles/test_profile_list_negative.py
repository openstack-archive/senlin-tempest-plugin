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

from senlin_tempest_plugin.tests.api import base


class TestProfileListNegativeBadRequest(base.BaseSenlinAPITest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0747310b-6d97-47d3-a7d6-c3d6121cee75')
    def test_profile_list_invalid_params(self):
        self.assertRaises(exceptions.BadRequest,
                          self.client.list_objs,
                          'profiles', {'bogus': 'foo'})

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5dcb1ec1-e870-4e25-a0b8-4b596f0607c0')
    def test_profile_list_limit_not_int(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.list_objs,
                               'profiles', {'limit': 'not-int'})

        message = ex.resp_body['error']['message']
        self.assertEqual("The value for limit must be an integer: 'not-int'.",
                         str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7e389aa6-039d-4d5d-8d4a-ac33c6d471a3')
    def test_profile_list_global_project_false(self):
        ex = self.assertRaises(exceptions.Forbidden,
                               self.client.list_objs,
                               'profiles', {'global_project': 'True'})

        message = ex.resp_body['error']['message']
        self.assertEqual("You are not authorized to complete this operation.",
                         str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('6891a01f-e8ab-4e95-bc74-4260745a8fe5')
    def test_profile_list_global_project_not_bool(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.list_objs,
                               'profiles', {'global_project': 'not-bool'})

        message = ex.resp_body['error']['message']
        self.assertEqual("Invalid value 'not-bool' specified for "
                         "'global_project'", str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b0bc73b2-dff8-416a-b0e5-8d1389468201')
    def test_profile_list_invalid_sort(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.list_objs,
                               'profiles', {'sort': 'bad-sort'})

        message = ex.resp_body['error']['message']
        self.assertEqual("Unsupported sort key 'bad-sort' for 'sort'.",
                         str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d84461d1-fc0d-4983-8030-3096cf360d45')
    def test_profile_list_invalid_marker(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.list_objs,
                               'profiles', {'marker': 'bad-marker'})

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The value for marker is not a valid UUID: 'bad-marker'.",
            str(message))

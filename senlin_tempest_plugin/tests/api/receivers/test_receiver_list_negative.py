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


class TestReceiverListNegativeBadRequest(base.BaseSenlinAPITest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5c2e7114-dab9-41c7-aecb-8e0c272a529d')
    def test_receiver_list_invalid_params(self):
        self.assertRaises(exceptions.BadRequest,
                          self.client.list_objs,
                          'receivers', {'bogus': 'foo'})

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('6b93221e-ca14-443b-be54-4423a636672a')
    def test_receiver_list_limit_not_int(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.list_objs,
                               'receivers', {'limit': 'not-int'})

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The value for limit must be an integer: 'not-int'.",
            str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d13e3011-32b5-4f9d-bb57-3532c4c46228')
    def test_receiver_list_global_project_false(self):
        ex = self.assertRaises(exceptions.Forbidden,
                               self.client.list_objs,
                               'receivers', {'global_project': 'True'})

        message = ex.resp_body['error']['message']
        self.assertEqual("You are not authorized to complete this operation.",
                         str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d7804b5e-6efd-4084-adec-531d0a8399dc')
    def test_receiver_list_global_project_not_bool(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.list_objs,
                               'receivers', {'global_project': 'not-bool'})

        message = ex.resp_body['error']['message']
        self.assertEqual("Invalid value 'not-bool' specified for "
                         "'global_project'", str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('6ca48051-6030-4333-9483-074e03da5ba0')
    def test_receiver_list_invalid_sort(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.list_objs,
                               'receivers', {'sort': 'bad-sort'})

        message = ex.resp_body['error']['message']
        self.assertEqual("Unsupported sort key 'bad-sort' for 'sort'.",
                         str(message))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('588517ed-bfcf-4d92-9d7c-5ed11fc2c2ee')
    def test_receiver_list_invalid_marker(self):
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.list_objs,
                               'receivers', {'marker': 'bad-marker'})

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The value for marker is not a valid UUID: 'bad-marker'.",
            str(message))

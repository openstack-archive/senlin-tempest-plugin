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


class TestEventShowNegativeNotFound(base.BaseSenlinAPITest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('318ae275-ed68-48f5-9151-523085107112')
    def test_event_show_not_found(self):
        ex = self.assertRaises(exceptions.NotFound,
                               self.client.get_obj, 'events',
                               '318ae275-ed68-48f5-9151-523085107112')

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The event '318ae275-ed68-48f5-9151-523085107112' could "
            "not be found.", str(message))

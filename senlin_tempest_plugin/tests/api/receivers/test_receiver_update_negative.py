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


class TestReceiverUpdateNegativeNotFound(base.BaseSenlinAPITest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('db22cabd-32af-4045-81e8-c87980f1e9f5')
    def test_receiver_update_receiver_not_found(self):
        params = {
            "receiver": {
                "name": "update-receiver-name",
                "action": "CLUSTER_SCALE_IN",
                "params": {
                    "count": "2"
                }
            }
        }
        self.assertRaises(exceptions.NotFound, self.client.update_obj,
                          'receivers', 'db22cabd-32af-4045-81e8-c87980f1e9f5',
                          params)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('79fcfab6-bb4a-4539-a36e-044f92161062')
    def test_receiver_update_receiver_no_param(self):
        self.assertRaises(exceptions.BadRequest, self.client.update_obj,
                          'receivers', 'db22cabd-32af-4045-81e8-c87980f1e9f5',
                          {})

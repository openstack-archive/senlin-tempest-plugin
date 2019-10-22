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
from tempest.lib.common import api_version_utils
from tempest.lib import decorators
from tempest.lib import exceptions
import time

from senlin_tempest_plugin.common import utils
from senlin_tempest_plugin.tests.api import base


CONF = config.CONF


class TestClusterActionScaleOut(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestClusterActionScaleOut, self).setUp()
        profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, profile_id)
        self.cluster_id = utils.create_a_cluster(self, profile_id)
        self.addCleanup(utils.delete_a_cluster, self, self.cluster_id)

    @decorators.idempotent_id('f15ff8cc-4be3-4c93-9979-6be428e83cd7')
    def test_cluster_action_scale_out(self):
        params = {
            "scale_out": {
                "count": "1"
            }
        }
        # Trigger cluster action
        res = self.client.trigger_action('clusters', self.cluster_id,
                                         params=params)

        # Verify resp code, body and location in headers
        self.assertEqual(202, res['status'])
        self.assertIn('actions', res['location'])

        action_id = res['location'].split('/actions/')[1]
        self.client.wait_for_status('actions', action_id, 'SUCCEEDED')


class TestClusterScaleOutNegativeBadRequest(base.BaseSenlinAPITest):

    def setUp(self):
        super(TestClusterScaleOutNegativeBadRequest, self).setUp()
        profile_id = utils.create_a_profile(self)
        self.addCleanup(utils.delete_a_profile, self, profile_id)
        self.cluster_id = utils.create_a_cluster(self, profile_id,
                                                 min_size=0, max_size=5,
                                                 desired_capacity=1)
        self.addCleanup(utils.delete_a_cluster, self, self.cluster_id)

    @decorators.idempotent_id('2bbf6e0c-a8cc-4b29-8060-83652ffd6cd2')
    def test_cluster_scale_out_invalid_count(self):
        params = {
            "scale_out": {
                "count": -1
            }
        }

        # Verify badrequest exception(400) is raised.
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.trigger_action,
                               'clusters', self.cluster_id, params)

        message = ex.resp_body['error']['message']
        self.assertEqual("Value must be >= 0 for field 'count'.",
                         str(message))


class TestClusterScaleOutInvalidRequest(base.BaseSenlinAPITest):

    @decorators.idempotent_id('7aa3fd0c-c092-4a54-8dae-3814492101b0')
    def test_cluster_scale_out_invalid_count(self):
        params = {
            "scale_out": {
                "count": "bad-count"
            }
        }

        # Verify badrequest exception(400) is raised.
        ex = self.assertRaises(exceptions.BadRequest,
                               self.client.trigger_action,
                               'clusters', 'fake', params)

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The value for count must be an integer: 'bad-count'.",
            str(message))


class TestClusterScaleOutNegativeNotFound(base.BaseSenlinAPITest):

    @decorators.idempotent_id('b7038d95-204c-455f-a866-94dc535dd840')
    def test_cluster_scale_out_cluster_not_found(self):
        params = {
            "scale_out": {
                "count": 1
            }
        }

        # Verify notfound exception(404) is raised.
        ex = self.assertRaises(exceptions.NotFound,
                               self.client.trigger_action, 'clusters',
                               'b7038d95-204c-455f-a866-94dc535dd840',
                               params)

        message = ex.resp_body['error']['message']
        self.assertEqual(
            "The cluster 'b7038d95-204c-455f-a866-94dc535dd840' could "
            "not be found.", str(message))


class TestClusterScaleOutNegativeResourceIsLocked(base.BaseSenlinAPITest):

    min_microversion = '1.11'
    max_microversion = 'latest'

    @classmethod
    def skip_checks(cls):
        super(base.BaseSenlinAPITest, cls).skip_checks()
        api_version_utils.check_skip_with_microversion(
            cls.min_microversion, cls.max_microversion,
            CONF.clustering.min_microversion,
            CONF.clustering.max_microversion)

    def setUp(self):
        super(TestClusterScaleOutNegativeResourceIsLocked, self).setUp()
        # create profile with simulated wait time to test
        # cluster locked scenario
        profile_id = utils.create_a_profile(
            self, metadata={'simulated_wait_time': 10})
        self.addCleanup(utils.delete_a_profile, self, profile_id)
        self.cluster_id = utils.create_a_cluster(self, profile_id)
        self.addCleanup(utils.delete_a_cluster, self, self.cluster_id)

    @decorators.idempotent_id('3ecc8a73-03b2-4937-bb98-5b49554baf06')
    def test_cluster_action_scale_out_locked_cluster(self):
        params = {
            "scale_out": {
                "count": "1"
            }
        }
        # Trigger cluster scale out
        res = self.client.trigger_action('clusters', self.cluster_id,
                                         params=params)

        self.assertEqual(202, res['status'])

        # sleep long enough for the action to start executing and locking
        # the clusters
        time.sleep(5)

        # Verify resource locked exception(409) is raised
        # when another scale out is called within 5 secs
        ex = self.assertRaises(exceptions.Conflict,
                               self.client.trigger_action, 'clusters',
                               self.cluster_id, params)

        message = ex.resp_body['error']['message']
        self.assertEqual(
            ("CLUSTER_SCALE_OUT for cluster '{}' cannot be completed because "
             "it is already locked.").format(self.cluster_id), str(message))

        # sleep long enough for the cluster lock to clear
        time.sleep(15)

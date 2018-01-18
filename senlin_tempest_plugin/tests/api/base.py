#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest import config

from senlin_tempest_plugin import base
from senlin_tempest_plugin.common import clustering_client
from senlin_tempest_plugin.common import compute_client
from senlin_tempest_plugin.common import network_client

CONF = config.CONF


class BaseSenlinAPITest(base.BaseSenlinTest):

    @classmethod
    def setup_credentials(cls):
        # Set no network resources for test accounts
        cls.set_network_resources()
        super(BaseSenlinAPITest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(BaseSenlinAPITest, cls).setup_clients()
        cls.client = clustering_client.ClusteringAPIClient(
            cls.os_primary.auth_provider,
            CONF.clustering.catalog_type,
            CONF.identity.region,
            **cls.default_params_with_timeout_values
        )

        cls.compute_client = compute_client.V21ComputeClient(
            cls.os_primary.auth_provider,
            CONF.compute.catalog_type,
            CONF.identity.region,
            **cls.default_params_with_timeout_values
        )

        cls.network_client = network_client.NetworkClient(
            cls.os_primary.auth_provider,
            CONF.network.catalog_type,
            CONF.identity.region,
            **cls.default_params_with_timeout_values
        )

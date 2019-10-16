#
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

from oslo_config import cfg

service_option = cfg.BoolOpt("senlin",
                             default=True,
                             help="Whether or not senlin is expected to be"
                                  "available")

clustering_group = cfg.OptGroup(name="clustering",
                                title="Clustering Service Options")

ClusteringGroup = [
    cfg.StrOpt("catalog_type",
               default="clustering",
               help="Catalog type of the clustering service."),
    cfg.IntOpt("wait_timeout",
               default=180,
               help="Waiting time for a specific status, in seconds."),
    cfg.StrOpt('min_microversion',
               default=None,
               help="Lower version of the test target microversion range. "
                    "The format is 'X.Y', where 'X' and 'Y' are int values. "
                    "Tempest selects tests based on the range between "
                    "min_microversion and max_microversion. If both values "
                    "are None, Tempest avoids tests which require a "
                    "microversion."),
    cfg.StrOpt('max_microversion',
               default='latest',
               help="Upper version of the test target microversion range. "
                    "The format is 'X.Y'. where 'X' and 'Y' are int values. "
                    "Tempest selects tests based on the range between "
                    "microversion and max_microversion. If both values "
                    "are None, Tempest avoids tests which require a "
                    "microversion."),
    cfg.BoolOpt('delete_with_dependency',
                default=False,
                help="Enables tests that delete clusters with resources such "
                     "as policies or receivers attached to it."),
    cfg.StrOpt('health_policy_version',
               default='1.0',
               help='Supported version of the health policy.'),
]

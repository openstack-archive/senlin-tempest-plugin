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

from oslo_serialization import jsonutils
from oslo_utils import timeutils
from six.moves.urllib import parse as urllib
from tempest import config
from tempest.lib.common import rest_client
from tempest.lib import exceptions
import time

CONF = config.CONF


class V21ComputeClient(rest_client.RestClient):
    def __init__(self, auth_provider, service, region, **kwargs):
        super(V21ComputeClient, self).__init__(
            auth_provider, service, region, **kwargs)

    def get_resp(self, resp, body):
        # Parse status code and location
        res = {
            'status': int(resp.pop('status')),
            'location': resp.pop('location', None)
        }
        # Parse other keys included in resp
        res.update(resp)

        # Parse body
        res['body'] = self._parse_resp(body)
        return res

    def create_obj(self, obj_type, attrs):
        uri = '/{0}'.format(obj_type)
        resp, body = self.post(uri, body=jsonutils.dumps(attrs))

        return self.get_resp(resp, body)

    def delete_obj(self, obj_type, obj_id):
        uri = '/{0}/{1}'.format(obj_type, obj_id)
        resp, body = self.delete(uri)

        return self.get_resp(resp, body)

    def run_operation_obj(self, obj_type, obj_id, operation, attrs):
        uri = '/{0}/{1}/{2}'.format(obj_type, obj_id, operation)
        resp, body = self.post(uri, body=jsonutils.dumps(attrs))

        return self.get_resp(resp, body)

    def get_obj(self, obj_type, obj_id, params=None):
        uri = '/{0}/{1}'.format(obj_type, obj_id)
        if params:
            uri += '?{0}'.format(urllib.urlencode(params))
        resp, body = self.get(uri)

        return self.get_resp(resp, body)

    def wait_for_status(self, obj_type, obj_id, expected_status, timeout=None):
        timeout = timeout or CONF.clustering.wait_timeout

        with timeutils.StopWatch(timeout) as timeout_watch:
            while not timeout_watch.expired():
                time.sleep(5)
                res = self.get_obj(obj_type, obj_id)
                if res['body']['status'] == expected_status:
                    return res

        raise exceptions.TimeoutException()

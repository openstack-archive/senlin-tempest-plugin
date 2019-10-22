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

import functools
import os
import signal
from six.moves import BaseHTTPServer
from six.moves import http_client as http
from stevedore import extension
import tempfile
import tenacity

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions

from senlin_tempest_plugin.common import constants

CONF = config.CONF


def api_microversion(api_microversion):
    """Decorator used to specify api_microversion for test."""
    def decorator(func):
        @functools.wraps(func)
        def wrapped(self):
            old = self.client.api_microversion
            self.client.api_microversion = api_microversion
            func(self)
            self.client.api_microversion = old
        return wrapped
    return decorator


def is_policy_supported(policy_name_and_version):
    """Check if specified policy is supported

    :param policy_name_and_version: Combined string of policy name and version.
    E.g. senlin.policy.scaling-1.0
    :returns: True if policy_name_and_version is supported. False otherwise.
    """
    mgr = extension.ExtensionManager(
        namespace='senlin.policies',
        invoke_on_load=False)
    return policy_name_and_version in mgr.names()


def prepare_and_cleanup_for_nova_server(base, cidr, spec=None):
    keypair_name = create_a_keypair(base, is_admin_manager=False)
    if spec is None:
        base.spec = constants.spec_nova_server
    else:
        base.spec = spec

    base.spec['properties']['key_name'] = keypair_name
    base.addCleanup(delete_a_keypair, base, keypair_name,
                    is_admin_manager=False)

    n_name = base.spec['properties']['networks'][0]['network']
    network_id = create_a_network(base, name=n_name)
    base.addCleanup(delete_a_network, base, network_id)

    subnet_id = create_a_subnet(base, network_id, cidr)
    base.addCleanup(delete_a_subnet, base, subnet_id)


def create_spec_from_config():
    """Utility function that creates a spec object from tempest config"""
    spec = constants.spec_nova_server

    spec['properties']['flavor'] = CONF.compute.flavor_ref
    spec['properties']['image'] = CONF.compute.image_ref

    return spec


def create_a_profile(base, spec=None, name=None, metadata=None):
    """Utility function that generates a Senlin profile."""

    if spec is None:
        spec = constants.spec_nova_server

    if name is None:
        name = data_utils.rand_name("tempest-created-profile")

    if metadata:
        spec['properties']['metadata'] = metadata

    params = {
        'profile': {
            'name': name,
            'spec': spec,
        }
    }
    res = base.client.create_obj('profiles', params)
    return res['body']['id']


def delete_a_profile(base, profile_id, ignore_missing=False):
    """Utility function that deletes a Senlin profile."""
    res = base.client.delete_obj('profiles', profile_id)
    if res['status'] == 404:
        if ignore_missing:
            return
        raise exceptions.NotFound()


def create_a_cluster(base, profile_id, desired_capacity=0, min_size=0,
                     max_size=-1, timeout=None, metadata=None, name=None,
                     config=None, wait_timeout=None):
    """Utility function that generates a Senlin cluster.

    Create a cluster and return it after it is ACTIVE. The function is used for
    deduplicate code in API tests where an 'existing' cluster is needed.
    """
    if name is None:
        name = data_utils.rand_name("tempest-created-cluster")
    params = {
        'cluster': {
            'profile_id': profile_id,
            'desired_capacity': desired_capacity,
            'min_size': min_size,
            'max_size': max_size,
            'timeout': timeout,
            'metadata': metadata,
            'name': name,
            'config': config
        }
    }
    res = base.client.create_obj('clusters', params)
    cluster_id = res['body']['id']
    action_id = res['location'].split('/actions/')[1]
    base.client.wait_for_status('actions', action_id, 'SUCCEEDED',
                                wait_timeout)
    return cluster_id


def update_a_cluster(base, cluster_id, profile_id=None, name=None,
                     expected_status='SUCCEEDED', metadata=None,
                     timeout=None, wait_timeout=None):
    """Utility function that updates a Senlin cluster.

    Update a cluster and return it after it is ACTIVE.
    """
    params = {
        'cluster': {
            'profile_id': profile_id,
            'metadata': metadata,
            'name': name,
            'timeout': timeout
        }
    }
    res = base.client.update_obj('clusters', cluster_id, params)
    action_id = res['location'].split('/actions/')[1]
    base.client.wait_for_status('actions', action_id, expected_status,
                                wait_timeout)
    return res['body']


def get_a_cluster(base, cluster_id, expected_status=None, wait_timeout=None):
    """Utility function that gets a Senlin cluster."""
    if expected_status is None:
        res = base.client.get_obj('clusters', cluster_id)
    else:
        base.client.wait_for_status('clusters', cluster_id, expected_status,
                                    wait_timeout)
        res = base.client.get_obj('clusters', cluster_id)

    return res['body']


def list_clusters(base):
    """Utility function that lists Senlin clusters."""
    res = base.client.list_objs('clusters')
    return res['body']


def _return_last_value(retry_state):
    return retry_state.outcome.result()


@tenacity.retry(
    retry=(tenacity.retry_if_exception_type(exceptions.Conflict) |
           tenacity.retry_if_result(lambda x: x is False)),
    wait=tenacity.wait_fixed(2),
    retry_error_callback=_return_last_value,
    stop=tenacity.stop_after_attempt(5)
)
def delete_a_cluster(base, cluster_id, wait_timeout=None):
    """Utility function that deletes a Senlin cluster."""
    res = base.client.delete_obj('clusters', cluster_id)
    action_id = res['location'].split('/actions/')[1]

    action = base.client.wait_for_status(
        'actions', action_id, ['SUCCEEDED', 'FAILED'], wait_timeout)
    if action['body']['status'] == 'FAILED':
        return False

    base.client.wait_for_delete("clusters", cluster_id, wait_timeout)
    return True


def create_a_node(base, profile_id, cluster_id=None, metadata=None,
                  role=None, name=None, wait_timeout=None):
    """Utility function that creates a node.

    Create a node and return it after it is ACTIVE. This function is for
    minimizing the code duplication that could happen in API tests where
    an 'existing' Senlin node is needed.
    """
    if name is None:
        name = data_utils.rand_name("tempest-created-node")

    params = {
        'node': {
            'profile_id': profile_id,
            'cluster_id': cluster_id,
            'metadata': metadata,
            'role': role,
            'name': name
        }
    }
    res = base.client.create_obj('nodes', params)
    node_id = res['body']['id']
    action_id = res['location'].split('/actions/')[1]
    base.client.wait_for_status('actions', action_id, 'SUCCEEDED',
                                wait_timeout)
    res = base.client.get_obj('nodes', node_id)
    return res['body']['id']


def get_a_node(base, node_id, show_details=False):
    """Utility function that gets a Senlin node."""
    params = None
    if show_details:
        params = {'show_details': True}
    res = base.client.get_obj('nodes', node_id, params)
    return res['body']


def list_nodes(base):
    """Utility function that lists Senlin nodes."""
    res = base.client.list_objs('nodes')
    return res['body']


def update_a_node(base, node_id, profile_id=None, name=None,
                  metadata=None, tainted=None, role=None,
                  wait_timeout=None):
    """Utility function that updates a Senlin node.

    Update a node and return it after it is ACTIVE.
    """
    params = {
        'node': {
            'profile_id': profile_id,
            'metadata': metadata,
            'name': name,
            'role': role
        }
    }
    if tainted is not None:
        params['node']['tainted'] = tainted

    res = base.client.update_obj('nodes', node_id, params)
    action_id = res['location'].split('/actions/')[1]
    base.client.wait_for_status('actions', action_id, 'SUCCEEDED',
                                wait_timeout)

    return res['body']['status_reason']


def delete_a_node(base, node_id, wait_timeout=None):
    """Utility function that deletes a Senlin node."""
    res = base.client.delete_obj('nodes', node_id)
    action_id = res['location'].split('/actions/')[1]
    base.client.wait_for_status('actions', action_id, 'SUCCEEDED',
                                wait_timeout)
    return


def create_a_policy(base, spec=None, name=None):
    """Utility function that generates a Senlin policy."""

    params = {
        'policy': {
            'name': name or data_utils.rand_name("tempest-created-policy"),
            'spec': spec or constants.spec_scaling_policy
        }
    }
    res = base.client.create_obj('policies', params)
    return res['body']['id']


def get_a_policy(base, policy_id):
    """Utility function that gets a Senlin policy."""
    res = base.client.get_obj('policies', policy_id)
    return res['body']


def delete_a_policy(base, policy_id, ignore_missing=False):
    """Utility function that deletes a policy."""
    res = base.client.delete_obj('policies', policy_id)
    if res['status'] == 404:
        if ignore_missing:
            return
        raise exceptions.NotFound()
    return


def get_a_action(base, action_id):
    """Utility function that gets a Senlin action."""
    res = base.client.get_obj('actions', action_id)
    return res['body']


def cluster_attach_policy(base, cluster_id, policy_id,
                          expected_status='SUCCEEDED', wait_timeout=None):
    """Utility function that attach a policy to cluster."""

    params = {
        'policy_attach': {
            'enabled': True,
            'policy_id': policy_id
        }
    }
    res = base.client.trigger_action('clusters', cluster_id, params=params)
    action_id = res['location'].split('/actions/')[1]
    res = base.client.wait_for_status('actions', action_id, expected_status,
                                      wait_timeout)

    return res['body']['status_reason']


@tenacity.retry(
    retry=(tenacity.retry_if_exception_type(exceptions.Conflict) |
           tenacity.retry_if_result(lambda x: x is False)),
    wait=tenacity.wait_fixed(2),
    retry_error_callback=_return_last_value,
    stop=tenacity.stop_after_attempt(5)
)
def cluster_detach_policy(base, cluster_id, policy_id,
                          expected_status='SUCCEEDED', wait_timeout=None):
    """Utility function that detach a policy from cluster."""

    params = {
        'policy_detach': {
            'policy_id': policy_id
        }
    }
    res = base.client.trigger_action('clusters', cluster_id, params=params)
    action_id = res['location'].split('/actions/')[1]

    res = base.client.wait_for_status(
        'actions', action_id, ['SUCCEEDED', 'FAILED'], wait_timeout)
    if res['body']['status'] == 'FAILED':
        return False

    return res['body']['status_reason']


def cluster_replace_nodes(base, cluster_id, nodes,
                          expected_status='SUCCEEDED', wait_timeout=None):
    """Utility function that replace nodes of cluster."""

    params = {
        'replace_nodes': {
            'nodes': nodes
        }
    }
    res = base.client.cluster_replace_nodes('clusters', cluster_id,
                                            params=params)
    action_id = res['location'].split('/actions/')[1]
    res = base.client.wait_for_status('actions', action_id, expected_status,
                                      wait_timeout)
    return res['body']['status_reason']


def cluster_add_nodes(base, cluster_id, nodes, expected_status='SUCCEEDED',
                      wait_timeout=None):
    """Utility function that add nodes to cluster."""

    params = {
        'add_nodes': {
            'nodes': nodes
        }
    }
    res = base.client.trigger_action('clusters', cluster_id, params=params)
    action_id = res['location'].split('/actions/')[1]
    res = base.client.wait_for_status('actions', action_id, expected_status,
                                      wait_timeout)
    return res['body']['status_reason']


def cluster_del_nodes(base, cluster_id, nodes, expected_status='SUCCEEDED',
                      wait_timeout=None):
    """Utility function that delete nodes from cluster."""

    params = {
        'del_nodes': {
            'nodes': nodes
        }
    }
    res = base.client.trigger_action('clusters', cluster_id, params=params)
    action_id = res['location'].split('/actions/')[1]
    res = base.client.wait_for_status('actions', action_id, expected_status,
                                      wait_timeout)
    return res['body']['status_reason']


def cluster_scale_out(base, cluster_id, count=None,
                      expected_status='SUCCEEDED', wait_timeout=None):
    """Utility function that scale out cluster."""

    params = {
        'scale_out': {
            'count': count
        }
    }
    res = base.client.trigger_action('clusters', cluster_id, params=params)
    action_id = res['location'].split('/actions/')[1]
    res = base.client.wait_for_status('actions', action_id, expected_status,
                                      wait_timeout)
    return res['body']['status_reason']


def cluster_scale_in(base, cluster_id, count=None,
                     expected_status='SUCCEEDED', wait_timeout=None):
    """Utility function that scale in cluster."""

    params = {
        'scale_in': {
            'count': count
        }
    }
    res = base.client.trigger_action('clusters', cluster_id, params=params)
    action_id = res['location'].split('/actions/')[1]
    res = base.client.wait_for_status('actions', action_id, expected_status,
                                      wait_timeout)
    return res['body']['status_reason'], action_id


def cluster_resize(base, cluster_id, adj_type=None, number=None, min_size=None,
                   max_size=None, min_step=None, strict=True,
                   expected_status='SUCCEEDED', wait_timeout=None):
    """Utility function that resize cluster."""

    params = {
        'resize': {
            'adjustment_type': adj_type,
            'number': number,
            'min_size': min_size,
            'max_size': max_size,
            'min_step': min_step,
            'strict': strict
        }
    }
    res = base.client.trigger_action('clusters', cluster_id, params=params)
    action_id = res['location'].split('/actions/')[1]
    res = base.client.wait_for_status('actions', action_id, expected_status,
                                      wait_timeout)
    return res['body']['status_reason']


def cluster_complete_lifecycle(base, cluster_id, lifecycle_action_token,
                               expected_status='SUCCEEDED', wait_timeout=None):
    """Utility function that completes lifecycle for a cluster."""

    params = {
        'complete_lifecycle': {
            'lifecycle_action_token': lifecycle_action_token
        }
    }
    res = base.client.trigger_action('clusters', cluster_id, params=params)
    action_id = res['location'].split('/actions/')[1]
    res = base.client.wait_for_status('actions', action_id, expected_status,
                                      wait_timeout)
    return res['body']['status_reason']


def create_a_receiver(base, cluster_id, action, r_type=None, name=None,
                      params=None):
    """Utility function that generates a Senlin receiver."""

    if name is None:
        name = data_utils.rand_name("tempest-created-receiver")

    body = {
        'receiver': {
            'name': name,
            'cluster_id': cluster_id,
            'type': r_type or 'webhook',
            'params': params or {}
        }
    }

    if action is not None:
        body['receiver']['action'] = action

    res = base.client.create_obj('receivers', body)
    return res['body']['id']


def get_a_receiver(base, receiver_id):
    """Utility function that gets a Senlin receiver."""
    res = base.client.get_obj('receivers', receiver_id)
    return res['body']


def delete_a_receiver(base, receiver_id, ignore_missing=False):
    """Utility function that deletes a Senlin receiver."""
    res = base.client.delete_obj('receivers', receiver_id)
    if res['status'] == 404:
        if ignore_missing:
            return
        raise exceptions.NotFound()


def create_a_keypair(base, name=None, is_admin_manager=True):
    """Utility function that creates a Nova keypair."""

    if name is None:
        name = data_utils.rand_name("tempest-created-keypair")

    if is_admin_manager is True:
        body = base.os_admin.keypairs_client.create_keypair(name=name)
        body = body['keypair']
    else:
        params = {
            "keypair": {
                "name": name,
            }
        }
        body = base.compute_client.create_obj('os-keypairs', params)['body']

    return body['name']


def delete_a_keypair(base, name, is_admin_manager=True, ignore_missing=False):
    """Utility function that deletes a Nova keypair."""

    if is_admin_manager is True:
        base.os_admin.keypairs_client.delete_keypair(name)
        return

    res = base.compute_client.delete_obj('os-keypairs', name)
    if res['status'] == 404:
        if ignore_missing is True:
            return
        raise exceptions.NotFound()


def create_a_network(base, name=None):
    """Utility function that creates a Neutron network"""

    if name is None:
        name = data_utils.rand_name("tempest-created-network")

    params = {
        "network": {
            "name": name,
        }
    }
    body = base.network_client.create_obj('networks', params)

    return body['body']['id']


def delete_a_network(base, network_id, ignore_missing=False,
                     wait_timeout=None):
    """Utility function that deletes a Neutron network."""

    res = base.network_client.delete_obj('networks', network_id)
    if res['status'] == 404:
        if ignore_missing is True:
            return
        raise exceptions.NotFound()

    base.network_client.wait_for_delete('networks', network_id, wait_timeout)


def create_a_subnet(base, network_id, cidr, ip_version=4, name=None):
    """Utility function that creates a Neutron subnet"""

    if name is None:
        name = data_utils.rand_name("tempest-created-subnet")

    params = {
        "subnet": {
            "name": name,
            "network_id": network_id,
            "cidr": cidr,
            "ip_version": ip_version,
        }
    }
    body = base.network_client.create_obj('subnets', params)

    return body['body']['id']


def delete_a_subnet(base, subnet_id, ignore_missing=False, wait_timeout=None):
    """Utility function that deletes a Neutron subnet."""

    res = base.network_client.delete_obj('subnets', subnet_id)
    if res['status'] == 404:
        if ignore_missing is True:
            return
        raise exceptions.NotFound()

    base.network_client.wait_for_delete('subnets', subnet_id, wait_timeout)


def create_queue(base, queue_name):
    """Utility function that creates Zaqar queue."""
    res = base.messaging_client.create_queue(queue_name)

    if res['status'] != 201 and res['status'] != 204:
        msg = 'Failed in creating Zaqar queue %s' % queue_name
        raise Exception(msg)


def delete_queue(base, queue_name):
    """Utility function that deletes Zaqar queue."""
    res = base.messaging_client.delete_queue(queue_name)

    if res['status'] != 204:
        msg = 'Failed in deleting Zaqar queue %s' % queue_name
        raise Exception(msg)


def list_messages(base, queue_name):
    """Utility function that lists messages in Zaqar queue."""
    res = base.messaging_client.list_messages(queue_name)

    if res['status'] != 200:
        msg = 'Failed in listing messsages for Zaqar queue %s' % queue_name
        raise Exception(msg)

    return res['body']['messages']


def post_messages(base, queue_name, messages):
    """Utility function that posts message(s) to Zaqar queue."""
    res = base.messaging_client.post_messages(queue_name,
                                              {'messages': messages})
    if res['status'] != 201:
        msg = 'Failed in posting messages to Zaqar queue %s' % queue_name
        raise Exception(msg)


def start_http_server(port=5050):
    def _get_http_handler_class(filename):
        class StaticHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

            def do_GET(self):
                data = b'healthy\n'
                self.send_response(http.OK)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            def log_message(self, fmt, *args):
                msg = fmt % args
                with open(filename, 'a+') as tmp:
                    tmp.write("%s\n" % msg)
                return

        return StaticHTTPRequestHandler

    server_address = ('127.0.0.1', port)
    new_file, filename = tempfile.mkstemp()
    handler_class = _get_http_handler_class(filename)
    httpd = BaseHTTPServer.HTTPServer(server_address, handler_class)

    pid = os.fork()
    if pid == 0:
        httpd.serve_forever()
    else:
        return pid, filename


def terminate_http_server(pid, filename):
    os.kill(pid, signal.SIGKILL)

    if not os.path.isfile(filename):
        return ''

    with open(filename, 'r') as f:
        contents = f.read()

    os.remove(filename)
    return contents

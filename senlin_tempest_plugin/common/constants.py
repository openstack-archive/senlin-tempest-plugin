# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


spec_nova_server = {
    "type": "os.nova.server",
    "version": "1.0",
    "properties": {
        "flavor": "1",
        "name": "new-server-test",
        "image": "cirros-0.4.0-x86_64-disk",
        "networks": [
            {"network": "private"}
        ]
    }
}

spec_heat_stack = {
    "type": "os.heat.stack",
    "version": "1.0",
    "properties": {
        "template": {
            "heat_template_version": "2014-10-16",
            "parameters": {
                "str_length": {
                    "type": "number",
                    "default": 64
                }
            },
            "resources": {
                "random": {
                    "type": "OS::Heat::RandomString",
                    "properties": {
                        "length": {"get_param": "str_length"}
                    }
                }
            },
            "outputs": {
                "result": {
                    "value": {"get_attr": ["random", "value"]}
                }
            }
        }
    }
}

spec_scaling_policy = {
    "type": "senlin.policy.scaling",
    "version": "1.0",
    "properties": {
        "event": "CLUSTER_SCALE_IN",
        "adjustment": {
            "type": "CHANGE_IN_CAPACITY",
            "number": 1,
            "min_step": 1,
            "best_effort": True
        }
    }
}

spec_lb_policy = {
    "type": "senlin.policy.loadbalance",
    "version": "1.1",
    "properties": {
        "pool": {
            "protocol": "HTTP",
            "protocol_port": 80,
            "subnet": "private-subnet",
            "lb_method": "ROUND_ROBIN",
            "session_persistence": {
                "type": "SOURCE_IP",
                "cookie_name": "test-cookie"
            }
        },
        "vip": {
            "subnet": "private-subnet",
            "connection_limit": 100,
            "protocol": "HTTP",
            "protocol_port": 80
        },
        "health_monitor": {
            "type": "HTTP",
            "delay": "1",
            "timeout": 1,
            "max_retries": 5,
            "admin_state_up": True,
            "http_method": "GET",
            "url_path": "/index.html",
            "expected_codes": "200,201,202"
        },
        "lb_status_timeout": 300
    }
}

spec_batch_policy = {
    "type": "senlin.policy.batch",
    "version": "1.0",
    "properties": {
        "min_in_service": 1,
        "max_batch_size": 1,
        "pause_time": 3
    }
}

spec_deletion_policy = {
    "type": "senlin.policy.deletion",
    "version": "1.1",
    "properties": {
        "criteria": "OLDEST_FIRST"
    }
}

spec_deletion_policy_with_hook = {
    "type": "senlin.policy.deletion",
    "version": "1.1",
    "properties": {
        "hooks": {
            "type": "zaqar",
            "timeout": 300,
            "params": {
                "queue": "test_queue"
            }
        },
        "criteria": "OLDEST_FIRST"
    }
}

spec_health_policy = {
    "version": "1.1",
    "type": "senlin.policy.health",
    "description": "A policy for maintaining node health from a cluster.",
    "properties": {
        "detection": {
            "detection_modes": [
                {
                    "type": "NODE_STATUS_POLLING"
                },
                {
                    "type": "NODE_STATUS_POLL_URL",
                    "options": {
                        "poll_url_retry_limit": 3,
                        "poll_url": "http://127.0.0.1:5050",
                        "poll_url_retry_interval": 2
                    }
                }
            ],
            "node_update_timeout": 10,
            "interval": 10
        },
        "recovery": {
            "node_delete_timeout": 90,
            "actions": [
                {
                    "name": "RECREATE"
                }
            ],
            "node_force_recreate": True
        }
    }
}

spec_health_policy_duplicate_type = {
    "version": "1.1",
    "type": "senlin.policy.health",
    "properties": {
        "detection": {
            "detection_modes": [
                {
                    "type": "NODE_STATUS_POLLING"
                },
                {
                    "type": "NODE_STATUS_POLLING",
                }
            ],
        },
        "recovery": {
            "actions": [
                {
                    "name": "RECREATE"
                }
            ],
        }
    }
}

spec_health_policy_invalid_combo = {
    "version": "1.1",
    "type": "senlin.policy.health",
    "properties": {
        "detection": {
            "detection_modes": [
                {
                    "type": "NODE_STATUS_POLLING"
                },
                {
                    "type": "LIFECYCLE_EVENTS",
                }
            ],
        },
        "recovery": {
            "actions": [
                {
                    "name": "RECREATE"
                }
            ],
        }
    }
}

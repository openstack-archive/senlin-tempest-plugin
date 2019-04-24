========================
Team and repository tags
========================

.. image:: https://governance.openstack.org/tc/badges/senlin.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

.. Change things from this point on

==============================
Tempest integration of Senlin
==============================

This project contains the Tempest plugin for the Senlin project for
OpenStack Clustering.

For more information about Senlin see:
https://docs.openstack.org/senlin/latest/

For more information about Tempest plugins see:
https://docs.openstack.org/tempest/latest/plugin.html

* Free software: Apache license
* Source: http://opendev.org/openstack/senlin-tempest-plugin

Installing
----------

Clone this repository to the destination machine, and call from the repo::

    $ pip install -e .

Running the tests
-----------------

To run all the tests from this plugin, call from the tempest repo::

    $ tox -e all-plugin -- senlin_tempest_plugin

To run a single test case, call with full path, for example::

    $ tox -e all-plugin -- senlin_tempest_plugin.tests.api.policies.test_policy_update.TestPolicyUpdate.test_policy_update

To retrieve a list of all tempest tests, run::

    $ testr list-tests

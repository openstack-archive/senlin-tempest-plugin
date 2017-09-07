Senlin Style Commandments
=========================

- Step 1: Read the OpenStack Style Commandments
  https://docs.openstack.org/developer/hacking/
- Step 2: Read on

Senlin Specific Commandments
----------------------------

- [S318] Use assertion ``assertIsNone(A)`` instead of ``assertEqual(A, None)``
         or ``assertEqual(None, A)``.
- [S319] Use ``jsonutils`` functions rather than using the ``json`` package
         directly.
- [S320] Default arguments of a method should not be mutable.
- [S321] The api_version decorator has to be the first decorator on a method.
- [S322] LOG.warn is deprecated. Enforce use of LOG.warning.
- [S323] Use assertTrue(...) rather than assertEqual(True, ...).

*******
Logging
*******

GsshaPy uses the default Python logging module.
By default, nothing is logged anywhere. Here is how
to configure your instance.

Print to console
================

To use the default logging:

.. code:: python

  import gsshapy
  gsshapy.log_to_console()

  # then use gsshapy


To set custom level:

.. code:: python

  import gsshapy
  gsshapy.log_to_console(level='INFO')

  # then use gsshapy


.. autofunction:: gsshapy.log_to_console

Log to file
===========

To use the default logging:

.. code:: python

  import gsshapy
  gsshapy.log_to_file(filename='gsshapy_run.log')

  # then use gsshapy


To set custom level:

.. code:: python

  import gsshapy
  gsshapy.log_to_file(filename='gsshapy_run.log', level='INFO')

  # then use gsshapy


.. autofunction:: gsshapy.log_to_file

***************
GSSHA Framework
***************

Installation
============

First, follow these instructions: :ref:`gsshapy-installation`.


Install RAPIDpy
---------------
In addition to the usual gsshapy installation, you need it install RAPIDpy.
Full instructions for installation are here: http://rapidpy.readthedocs.io/en/latest/installation.html

.. warning:: The latest version of RAPIDpy is the version you should install. Do not install via pip!

If Mac/Linux::

    $ git clone https://github.com/erdc-cm/RAPIDpy.git
    $ cd RAPIDpy
    $ source activate gssha
    (gssha)$ python setup.py install

If Windows:

.. note:: You will need to download RAPIDpy from https://github.com/erdc-cm/RAPIDpy 
          or clone the repository using a git program first.

::
    
    > cd RAPIDpy
    > activate gssha
    (gssha)> python setup.py install

(Optional) Install spt_dataset_manager
--------------------------------------

.. warning:: Make sure you have your Miniconda gssha environment activated during installation.

See: https://github.com/erdc-cm/spt_dataset_manager

GSSHAFramework
==============

.. autoclass:: gridtogssha.framework.GSSHAFramework
    
GSSHA_WRF_Framework
===================

.. autoclass:: gridtogssha.framework.GSSHA_WRF_Framework
    :show-inheritance:


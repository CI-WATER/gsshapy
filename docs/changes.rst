**********************
Changes in Version 2.2
**********************

**Last Updated:** March 2, 2017

The release of GsshaPy 2.2.0 constitutes many changes which will be summarized here. Changes vary from minor bug fixes
to completely new file objects for files not previously supported. Several non-reverse compatible changes were also made
to make using GsshaPy more convenient. The following list covers the major changes:


New Modeling Methods
====================

To run existing GSSHA models and couple output from Land Surface Models or RAPID,
the :class:`gsshapy.modeling.GSSHAFramework` class was created.

To create basic GSSHA models, the :class:`gsshapy.modeling.GSSHAModel` class was created.


Methods to connect with Land Surface Models
===========================================

.. toctree::
    :maxdepth: 1

    api/grid/lsm_tools
    api/grid/hrrr_tools


Enjoy!

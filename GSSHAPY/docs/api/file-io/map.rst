*********
Map Files
*********

Although index maps and other raster maps are both GRASS ASCII maps, a special
table was created for index maps for easier implementation.

Index Map File Object
=====================

File extension: **idx**

**This file object supports spatial objects.**

.. autoclass:: gsshapy.orm.IndexMap
    :members:
    :show-inheritance:



Raster Map File Object
======================

File extensions: **Variable** (e.g.: ele, msk, aqe)

**This file object supports spatial objects.**

.. autoclass:: gsshapy.orm.RasterMapFile
    :members:
    :show-inheritance:

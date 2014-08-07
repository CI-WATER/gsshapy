***************************
Query using GsshaPy Objects
***************************

**Last Updated:** July 30, 2014

Explore the Database
====================

To prove that the exercise has actually done something, let's explore database. Before we do this using the GsshaPy
objects, lets explore a little using the **psql** commandline utility. Open a new terminal  or command prompt (leave the
terminal with your Python prompt running) and issue the following commands::

    $ psql -U gsshapy -d gsshapy_tutorial

Enter the password if prompted, which should be "pass" if you set up the database using the credentials in the last
tutorial. You should now have an SQL prompt to your database. Issue the following command::

    gsshapy_tutorial=> \dt

                        List of relations
     Schema |             Name             | Type  |  Owner
    --------+------------------------------+-------+---------
     public | cif_bcs_points               | table | gsshapy
     public | cif_breakpoint               | table | gsshapy
     public | cif_channel_input_files      | table | gsshapy
     public | cif_culverts                 | table | gsshapy
     public | cif_links                    | table | gsshapy
     public | cif_nodes                    | table | gsshapy
     public | cif_reservoir_points         | table | gsshapy
     public | cif_reservoirs               | table | gsshapy
     public | cif_trapezoid                | table | gsshapy
     public | cif_upstream_links           | table | gsshapy
     public | cif_weirs                    | table | gsshapy

     ...

     public | prj_project_cards            | table | gsshapy
     public | prj_project_files            | table | gsshapy

     ...

     public | wms_dataset_files            | table | gsshapy
     public | wms_dataset_rasters          | table | gsshapy
    (61 rows)

This will list all the tables in the gsshapy_tutorial database. If the database was initialized correctly, you should
see a list of 60+ or so tables. The three letter prefix on the filename is associted with the file extension or in some
cases the type of file. For example, there are two tables used to store project files: ``prj_project_files`` and
``prj_project_cards``. The project file table is not very interesting, so, we will query the ``prj_project_cards`` table.
This can be done as follows::

    gsshapy_tutorial=> SELECT * FROM prj_project_cards;

     id | projectFileID |        name        |                       value
    ----+---------------+--------------------+----------------------------------------------------
      1 |             1 | WMS                | WMS 9.1 (64-Bit)
      2 |             1 | WATERSHED_MASK     | "parkcity.msk"
      3 |             1 | PROJECT_PATH       | ""
      4 |             1 | #LandSoil          | "parkcity.lsf"
      5 |             1 | #PROJECTION_FILE   | "parkcity_prj.pro"
      6 |             1 | NON_ORTHO_CHANNELS |
      7 |             1 | FLINE              | "parkcity.map"
      8 |             1 | METRIC             |
      9 |             1 | GRIDSIZE           | 90.000000
     10 |             1 | ROWS               | 72
     11 |             1 | COLS               | 67

     ...

     37 |             1 | IN_HYD_LOCATION    | "parkcity.ihl"
     38 |             1 | OUT_HYD_LOCATION   | "parkcity.ohl"
     39 |             1 | CHAN_DEPTH         | "parkcity.cdp"
    (39 rows)

Each record in the ``prj_project_cards`` table stores the name and value of one card in the project file.
The ``prj_project_cards`` table is related to the ``prj_project_files`` table through a foreign
key column called ``projectFileID`` (the column with all 1's).

Execute the following command to quit the **psql** program::

    gsshapy_tutorial=> \q

Querying Using GsshaPy Objects
==============================

The **ProjectCard** *table* class maps to the ``prj_project_cards`` table and the **ProjectFile** class maps to the
``prj_project_files`` table. Instances of these classes can be used to query the database. Suppose we need to retrieve
all of the project cards from a project file. We can use SQLAlchemy_ session object and SQL expression language to do
this. Back in the Python console, execute the following::

    >>> from gsshapy.orm import ProjectCard
    >>> cards = session.query(ProjectCard).all()
    >>> for card in cards:
    ...	    print card
    ...

.. seealso::

    For an overview of the SQLAlchemy_ SQL expression language see the following tutorials:
    `Object Relational Tutorial`_ and `SQL Expression Language`_.

As in the previous tutorial, the query returns a list of :class:`gsshapy.orm.ProjectCard` objects that represent the
records in the ``prj_project_cards`` table. The :class:`gsshapy.orm.ProjectCard` class also has a relationship property
called *projectFile* that maps to the associated :class:`gsshapy.orm.ProjectFile` class. If we wanted to ensure that we
only queried for project cards that belong to the project file we read in during the first exercise, we could use the
``filter()`` method of the ``query`` object::

    >>> cards = session.query(ProjectCard).filter(ProjectCard.projectFile == projectFile).all()
    >>> for card in cards:
    ...	    print card
    ...


The result is the same as before, because we only have one project file read into the database. As illustrated in the
previous tutorial, we could also use the relationship properties to issue the queries to the database::

    >>> cards = projectFile.projectCards
    >>> for card in cards:
    ...	    print card
    ...

The later two methods are equivalent. This is only a micro tasting of the power of the SQLAlchemy query language.
Please review the SQLAlchemy documentation for a more detailed explanation of querying.

Updating Records Using GsshaPy Objects
======================================

Using GsshaPy you can modify existing records in the database. For example, suppose you would like to modify one of the
parameters in the project file. In the next step we will retrieve the project file and access the "MAP_FREQ" card. We'll
change the value to 10, indicating that we would like the maps to be written every 10 minutes of simulation time. First,
we query the database for the project file and use the ``getCard()`` method to retrieve the "MAP_FREQ" card::

    >>> projectFile = session.query(ProjectFile).first()
    >>> mapFreqCard = projectFile.getCard('MAP_FREQ')
    >>> print mapFreqCard
    <ProjectCard: Name=MAP_FREQ, Value=30>

The results of the ``print mapFreqCard`` reveal that the value of the "MAP_FREQ" card is currently 30. To change it to 10
simply reassign the ``value`` property on the ``mapFreqCard`` object.::

    >>> mapFreqCard.value = 10
    >>> print mapFreqCard
    <ProjectCard: Name=MAP_FREQ, Value=10>

The ``print mapFreqCard`` command reveals that the value is now set to 10. However, this change has only occurred with
our copy of the card. To persist the change in the database, we need to tell the session to flush all the changes out to the
database. This can be done by calling the ``commit()`` method of the session object. Be sure to use the same session
object that you used to query project file. The session object has been tracking all the changes you have been making.
You can inspect the changes that the session object is tracking via the ``dirty`` property of the session object::

    >>> session.dirty
    >>> session.commit()
    >>> session.dirty

You'll notice that the ``dirty`` property is empty after the session has been committed to the database. That's it, the
"MAP_FREQ" card has been changed. You will see the change when we write the data back out to file in the next tutorial.
However, there are other things we need to learn before going on.

Creating New Records Using GsshaPy Objects
==========================================



.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Object Relational Tutorial: http://docs.sqlalchemy.org/en/rel_0_8/orm/tutorial.html
.. _SQL Expression Language: http://docs.sqlalchemy.org/en/rel_0_8/core/tutorial.html
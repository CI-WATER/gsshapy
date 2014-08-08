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

The :class:`gsshapy.orm.ProjectCard` *table* class maps to the ``prj_project_cards`` table and the :class:`gsshapy.orm.ProjectFile` class maps to the
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
called *projectFile* that maps to the associated :class:`gsshapy.orm.ProjectFile` class. If you wanted to ensure that you
only queried for project cards that belong to the project file you read in during the first exercise, you could use the
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

The later two methods are equivalent.

Updating Records Using GsshaPy Objects
======================================

You can modify existing records in the database using GsshaPy. As an example scenario, suppose you need to modify the
GSSHA model so that it outputs depth maps every 10 minutes instead of every 30 minutes. This is done by changing the value
of the "MAP_FREQ" card in the project file. To modify the "MAP_FREQ" card, we need to access the appropriate record in the :class:`gsshapy.orm.ProjectCard` table. However, we want
to make sure we are changing the card that belongs to the correct project file, so we will first query for the :class:`gsshapy.orm.ProjectFile`
we want and then use its ``getCard()`` method to access its "MAP_FREQ" card::

    >>> from gsshapy.orm import ProjectFile
    >>> projectFile = session.query(ProjectFile).first()
    >>> mapFreqCard = projectFile.getCard('MAP_FREQ')

As the name implies, the ``getCard()`` method of the :class:`gsshapy.orm.ProjectFile` object returns the :class:`gsshapy.orm.ProjectCard` object that matches the
name provided. :class:`gsshapy.orm.ProjectCard` objects have three properties: ``name``, ``value``, and ``projectFile``. The ``name`` and ``value``
properties map to the **name** and **value** columns in the :class:`gsshapy.orm.ProjectCard` table. The ``projectFile`` property is a *relationship*
property. It maps to the :class:`gsshapy.orm.ProjectFile` to which the :class:`gsshapy.orm.ProjectCard` belongs. Execute these lines to learn more about the
:class:`gsshapy.orm.ProjectCard` object::

    >>> print mapFreqCard.name
    MAP_FREQ
    >>> print mapFreqCard.value
    30
    >>> mapFreqCard.projectFile is projectFile
    True
    >>> print mapFreqCard
    <ProjectCard: Name=MAP_FREQ, Value=30>

Notice that the value of the ``projectFile`` property is the same as the ``projectFile`` object that was the result of our
query in the previous step. Most GsshaPy object have relationship properties like these that can be used to access
related objects. Behind the scenes, GsshaPy (via SQLAlchemy) performs a join between the two tables, queries for the
appropriate record, and returns the result in the form of an object. Also notice, the results of the ``print mapFreqCard``
reveals that the value of the "MAP_FREQ" card is currently 30. To change it to 10 simply reassign the ``value`` property
on the ``mapFreqCard`` object.::

    >>> mapFreqCard.value = 10
    >>> print mapFreqCard
    <ProjectCard: Name=MAP_FREQ, Value=10>

The ``print mapFreqCard`` command reveals that the value is now set to 10. However, this change has only occurred with
our "copy" of the card record. To persist the change in the database, we need to tell the session to commit all the changes
to the database. This can be done by calling the ``commit()`` method of the session object.  The session object has been
tracking all the changes you have been making. You can inspect changes you make to GsshaPy objects that the session object
is tracking via the ``dirty`` property of the session object::

    >>> session.dirty
    >>> session.commit()
    >>> session.dirty

You'll notice that the ``dirty`` property is empty after the session has been committed to the database. The "MAP_FREQ"
card has been changed in the database. You will see the change when we write the data back out to file in the next tutorial.
However, there are other changes that need to be made before getting to that point.

.. note::

    Although the session tracking seems like black magic, the session object was already aware of our :class:`gsshapy.orm.ProjectCard`
    object, because we accessed it via a query with the session (although indirectly through the :class:`gsshapy.orm.ProjectFile`).

Deleting Records Using GsshaPy Objects
======================================

Another common task that can be done using GsshaPy objects is deleting records in the database. Say, for instance you would
like to change the units that are output by GSSHA from metric to imperial. This requires adding the new card,
"ENGLISH", and deleting the "METRIC" card. Deleting cards is fairly straight forward. First, use the ``getCard()`` method
again to get the "METRIC" card object and then tell the session to delete it using the ``delete()`` method::

    >>> metricCard = projectFile.getCard("METRIC")
    >>> print metricCard
    <ProjectCard: Name=METRIC, Value=None>
    >>> session.delete(metricCard)
    >>> session.deleted

Just as ``session.dirty`` contains a list of objects that have changes, ``session.deleted`` tracks objects that have been
marked for deletion. Again, the ``commit()`` method must be called to persist this change. However, before you commit,
you will create the new "ENGLISH" card.

Creating New Records Using GsshaPy Objects
==========================================

Creating new records is somewhat involved, but the basic process is this:

(1) create a new GsshaPy object that maps to the type of record you would like to make
(2) set the values for all of the column properties
(3) set the values for all relationship properties
(4) add the new object to the session using the ``add()`` method

Step 3 can involve creating other GsshaPy objects or querying for the appropriate object if it already exists.
For example, we want to associate our new "ENGLISH" card with the project file that we are modifying. We don't need to
create a new project file, because it already exists. Execute these lines to create the new card::

    >>> from gsshapy.orm import ProjectCard
    >>> englishCard = ProjectCard(name='ENGLISH', value=None)
    >>> englishCard.projectFile = projectFile
    >>> print englishCard
    <ProjectCard: Name=ENGLISH, Value=None>
    >>> session.add(englishCard)
    >>> session.new

You can use the ``session.new`` property to inspect any new records that have been created, but not persisted in the
database. Before committing our changes to the database, there is one more lesson to learn. ID columns are automatically
handled by the GsshaPy objects (again, via SQLAlchemy). To illustrate this, inspect the id column of the new :class:`gsshapy.orm.ProjectCard`
we created::

    >>> print englishCard.id
    None

There is currently no ID assigned to the object. This will be assigned automatically after we commit our changes::

    >>> session.commit()
    >>> print englishCard.id
    40

GsshaPy is powered by SQLAlchemy. What has been demonstrated here is only a small sample of the powerful SQLAlchemy
query language. For an overview of the SQLAlchemy_ SQL expression language see the following tutorials: `Object Relational Tutorial`_
and `SQL Expression Language`_.

In the next tutorial, you will write the project file back out file to see the changes that you have made.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Object Relational Tutorial: http://docs.sqlalchemy.org/en/rel_0_8/orm/tutorial.html
.. _SQL Expression Language: http://docs.sqlalchemy.org/en/rel_0_8/core/tutorial.html
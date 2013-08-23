***************************
Query using GsshaPy Objects
***************************

**Last Updated:** August 23, 2013

Explore the Database
====================

To prove that the excercise has actually done something, let's explore database.
Before we do this using the GsshaPy objects, lets explore a little using the ``sqlite`` commandline
utility. Open a terminal or command prompt and issue the following commands::

	$ cd /path/to/tutorial-data/db
	$ sqlite3 gsshapy_parkcity.db
	sqlite> .tables
	
If the database was initialized correctly, you should see a list of about 50 or so tables. The three
letter prefix on the filename is associted with the file extension or in some cases the type of file.
For example, there are two tables used to store project files: ``prj_project_files`` and ``prj_project_cards``.
Most of the data is stored in the ``prj_project_cards`` table. Inspect the data in this table by issuing the following query::

	sqlite> SELECT * FROM prj_project_cards;
	
Each record in the ``prj_project_cards`` table stores the name and value of one card in the project file.
The ``prj_project_cards`` table is related to the ``prj_project_files`` table through a foreign
key column called *projectFileID* (the column with all 1's).

Querying Using GsshaPy Objects
==============================

The **ProjectCard** *table* class maps to the ``prj_project_cards`` table and the **ProjectFile** class 
maps to the ``prj_project_files`` table. Instances of these classes can be used to query the
database. Suppose we need to retrieve all of the project cards from a project file. We can use SQLAlchemy_
session object and SQL expression language to do this. Back in the python console, do the following::
	
	>>> from gsshapy.orm import ProjectCard
	>>> cards = session.query(ProjectCard).filter(ProjectCard.projectFileID == 1).all()
	>>> for card in cards:
	...	print card
	...	
	

.. seealso::
	
	For an overview of the SQLAlchemy_ SQL expression language see the following tutorials:
	`Object Relational Tutorial`_ and `SQL Expression Language`_.
	
The query returns a list of ProjectCard objects that represent the records in the ``prj_project_cards``
table that have *projectFileID* equal to 1, where *projectFileID* is the foreign key field used
in the relationship between the ``prj_project_cards`` and ``prj_project_files`` tables. The **ProjectCard**
class also has a relationship property called *projectFile* that maps to the associated **ProjectFile**
class. Equivalently, we can filter the query using the **ProjectFile** instance we have already created::

	>>> cards = session.query(ProjectCard).filter(ProjectCard.projectFile == projectFile).all()
	>>> for card in cards:
	...	print card
	...	
	
Alternatively, the relationship properties can be used to issue the queries to the database.
The **ProjectFile** also has a relationship property, *projectCards*, that back references the *projectFile*
property of the **ProjectCard** class. It can be used through the instance of our **ProjectFile** class 
in this way::

	>>> cards = projectFile.projectCards
	>>> for card in cards:
	...	print card
	...	
	
The attributes of each **ProjectCard** object can be retrieved using normal dot notation. The **ProjectCard**
has two value column attributes: *name* and *value*. Access their values like so::

	>>> for card in cards:
	...	print card.name, card.value
	...
	
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Object Relational Tutorial: http://docs.sqlalchemy.org/en/rel_0_8/orm/tutorial.html
.. _SQL Expression Language: http://docs.sqlalchemy.org/en/rel_0_8/core/tutorial.html
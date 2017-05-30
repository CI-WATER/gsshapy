"""
********************************************************************************
* Name: GeometricObjectBase
* Author: Nathan Swain
* Created On: July 18, 2014
* Copyright: (c) Brigham Young University 2014
* License: BSD 2-Clause
********************************************************************************
"""

__all__ = ['GeometricObjectBase']


class GeometricObjectBase:
    """
    Abstract base class for geometric objects.
    """

    # These properties must be defined in the class that implements this ABC
    tableName = None           #: Name of the table that the geometry column belongs to
    id = None                  #: ID of the record with the geometry column in the table that will be retrieved
    geometryColumnName = None  #: Name of the geometry column

    def getAsKml(self, session):
        """
        Retrieve the geometry in KML format.

        This method is a veneer for an SQL query that calls the ``ST_AsKml()`` function on the geometry column.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.

        Returns:
            str: KML string representation of geometry.
        """
        statement = """
                    SELECT ST_AsKml({0}) AS kml
                    FROM {1}
                    WHERE id={2};
                    """.format(self.geometryColumnName,
                               self.tableName,
                               self.id)

        result = session.execute(statement)

        for row in result:
            return row.kml

    def getAsWkt(self, session):
        """
        Retrieve the geometry in Well Known Text format.

        This method is a veneer for an SQL query that calls the ``ST_AsText()`` function on the geometry column.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.

        Returns:
            str: Well Known Text string representation of geometry.
        """
        statement = """
                    SELECT ST_AsText({0}) AS wkt
                    FROM {1}
                    WHERE id={2};
                    """.format(self.geometryColumnName,
                               self.tableName,
                               self.id)

        result = session.execute(statement)

        for row in result:
            return row.wkt

    def getAsGeoJson(self, session):
        """
        Retrieve the geometry in GeoJSON format.

        This method is a veneer for an SQL query that calls the ``ST_AsGeoJSON()`` function on the geometry column.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.

        Returns:
            str: GeoJSON string representation of geometry.
        """
        statement = """
                    SELECT ST_AsGeoJSON({0}) AS json
                    FROM {1}
                    WHERE id={2};
                    """.format(self.geometryColumnName,
                               self.tableName,
                               self.id)

        result = session.execute(statement)

        for row in result:
            return row.json

    def getSpatialReferenceId(self, session):
        """
        Retrieve the spatial reference id by which the geometry column is registered.

        This method is a veneer for an SQL query that calls the ``ST_SRID()`` function on the geometry column.

        Args:
            session (:mod:`sqlalchemy.orm.session.Session`): SQLAlchemy session object bound to PostGIS enabled database.

        Returns:
            str: PostGIS spatial reference ID.
        """
        statement = """
                    SELECT ST_SRID({0}) AS srid
                    FROM {1}
                    WHERE id={2};
                    """.format(self.geometryColumnName,
                               self.tableName,
                               self.id)

        result = session.execute(statement)

        for row in result:
            return row.srid
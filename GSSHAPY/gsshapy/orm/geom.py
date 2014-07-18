"""
********************************************************************************
* Name: GeometricObject
* Author: Nathan Swain
* Created On: July 18, 2014
* Copyright: (c) Brigham Young University 2014
* License: BSD 2-Clause
********************************************************************************
"""


class GeometricObject:
    """
    Abstract base class for geometric objects
    """

    # These properties must be defined in the class that implements this ABC
    tableName = None           # Name of the table that the geometry column belongs to
    id = None                  # ID of the record with the geometry column in the table that will be retrieved
    geometryColumnName = None  # Name of the geometry column

    def getAsKml(self, session):
        """
        Retrieve the geometry in KML format
        :param session: SQLAlchemy session object bound to a PostGIS enabled database
        :rtype : string
        """
        statement = '''
                    SELECT ST_AsKml({0}) AS kml
                    FROM {1}
                    WHERE id={2};
                    '''.format(self.geometryColumnName,
                               self.tableName,
                               self.id)

        result = session.execute(statement)

        for row in result:
            return row.kml

    def getAsWkt(self, session):
        """
        Retrieve the geometry in Well Known Text format
        :param session: SQLAlchemy session object bound to a PostGIS enabled database
        :rtype : string
        """
        statement = '''
                    SELECT ST_AsText({0}) AS wkt
                    FROM {1}
                    WHERE id={2};
                    '''.format(self.geometryColumnName,
                               self.tableName,
                               self.id)

        result = session.execute(statement)

        for row in result:
            return row.wkt

    def getAsGeoJson(self, session):
        """
        Retrieve the geometry in GeoJSON format
        :param session: SQLAlchemy session object bound to a PostGIS enabled database
        :rtype : string
        """
        statement = '''
                    SELECT ST_AsGeoJSON({0}) AS json
                    FROM {1}
                    WHERE id={2};
                    '''.format(self.geometryColumnName,
                               self.tableName,
                               self.id)

        result = session.execute(statement)

        for row in result:
            return row.json

    def getSpatialReferenceId(self, session):
        """
        Retrieve the spatial reference id by which the geometry column is registered
        """
        statement = '''
                    SELECT ST_SRID({0}) AS srid
                    FROM {1}
                    WHERE id={2};
                    '''.format(self.geometryColumnName,
                               self.tableName,
                               self.id)

        result = session.execute(statement)

        for row in result:
            return row.srid
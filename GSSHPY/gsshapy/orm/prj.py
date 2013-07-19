'''
********************************************************************************
* Name: ProjectFileModel
* Author: Nathan Swain
* Created On: Mar 18, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['ProjectFile',
           'ProjectCard']

import os, re, shlex

from sqlalchemy import ForeignKey, Column, Table
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase, metadata
from gsshapy.orm.gag import PrecipFile
from gsshapy.orm.cmt import MapTableFile



assocProject = Table('assoc_project_files_options', metadata,
    Column('projectFileID', Integer, ForeignKey('prj_project_files.id')),
    Column('projectCardID', Integer, ForeignKey('prj_project_cards.id'))
    )

class ProjectFile(DeclarativeBase):
    '''
    ProjectFile is the file ORM object that interfaces with the project files directly.
    '''
    __tablename__ = 'prj_project_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    precipFileID = Column(Integer, ForeignKey('gag_precipitation_files.id'))
    mapTableFileID = Column(Integer, ForeignKey('cmt_map_table_files.id'))

    # Relationship Properties
    projectCards = relationship('ProjectCard', secondary=assocProject, back_populates='projectFiles')
    precipFile = relationship('PrecipFile', back_populates='projectFile')
    mapTableFile = relationship('MapTableFile', back_populates='projectFile')
    
    
    # Global Properties
    PATH = None
    PROJECT_NAME = None
    DIRECTORY = None
    SESSION = None
    HEADERS = ['GSSHAPROJECT', 'WMS']
    
    def __init__(self, path, session):
        self.PATH = path
        self.SESSION = session
        
        if '\\' in path:
            splitPath = path.split('\\')
            self.DIRECTORY = '\\'.join(splitPath[:-1]) + '\\'
            
        elif '/' in path:
            splitPath = path.split('/')
            self.DIRECTORY = '/'.join(splitPath[:-1]) + '/'
        else:
            self.DIRECTORY = '""'
            
        self.PROJECT_NAME = splitPath[-1].split('.')[0]
    
    def read(self):
        '''
        Project File Read from File Method
        '''
        
        with open(self.PATH, 'r') as f:
            for line in f:
                card = {}
                try:
                    card = self._extractCard(line)    
                    
                except:
                    card = self._extractDirectoryCard(line)
                # Now that the cardName and cardValue are separated
                # load them into the gsshapy objects
                if card['name'] not in self.HEADERS:
                    # Initiate database objects
                    prjCard = ProjectCard(name=card['name'], value=card['value'])
                    self.projectCards.append(prjCard)
        
        self.SESSION.add(self)
                     
    def readAll(self):
        '''
        GSSHA Project Read from File Method
        '''
        
        # First read self
        self.read()
        
        # Initiate GSSHAPY MapTableFile object, associate with this object, and read map table file
        mapTable = MapTableFile(directory=self.DIRECTORY, name=self.PROJECT_NAME, session=self.SESSION)
        mapTable.projectFile = self
        mapTable.read()
        
        
        # Initiate GSSHAPY PrecipFile object, associate it with this object, and read precipitation file
        precip = PrecipFile(directory=self.DIRECTORY, name=self.PROJECT_NAME, session=self.SESSION)
        precip.projectFile = self
        precip.read()
    
    def write(self, session, directory, name):
        '''
        Project File Write to File Method
        '''
        # Initiate project file
        fullPath = '%s%s%s' % (directory, name, '.prj')
        
        with open(fullPath, 'w') as f:
            f.write('GSSHAPROJECT\n')
        
            # Initiate write on each ProjectCard that belongs to this ProjectFile
            for card in self.projectCards:
                f.write(card.write())
                
    def writeAll(self, session, directory, name):
        '''
        GSSHA Project Write to File Method
        '''
        
        # First write self
        self.write(session, directory, name)
        
        # Write map table file
        mapTableFile = session.query(MapTableFile).\
                                filter(MapTableFile.projectFile == self).\
                                one()
        mapTableFile.write(session=session, directory=directory, name=name)
        
        # Write precipitation file
        precipFile = session.query(PrecipFile).\
                                filter(PrecipFile.projectFile == self).\
                                one()
        precipFile.write(session=session, directory=directory, name=name)
        
        
    def _extractCard(self, projectLine):
        splitLine = shlex.split(projectLine)
        cardName = splitLine[0]
        # pathSplit will fail on boolean cards (no value
        # = no second parameter in list (currLine[1])
        try:
            # Split the path by / or \\ and retrieve last
            # item to store relative paths as Card Value
            pathSplit = re.split('/|\\\\', splitLine[1])
            
            # Wrap paths in double quotes
            try:
                # If the value is able to be converted to a
                # float (any number) then store value only
                float(pathSplit[-1])
                cardValue = pathSplit[-1]
            except:
                # A string will through an exception with
                # an atempt to convert to float. In this 
                # case wrap the string in double quotes.
                if '.' in pathSplit[-1]:
                    # If the string contains a '.' it is a
                    # path: wrap in double quotes
                    cardValue = '"%s"' % pathSplit[-1]
                elif pathSplit[-1] == '':
                    # For directory cards with unix paths 
                    # use double quotes
                    cardValue = '""'
                else:
                    # Else it is a card name/option
                    # don't wrap in quotes
                    cardValue = pathSplit[-1]
        
        # For boolean cards store the empty string
        except:
            cardValue = None
            
        return {'name': cardName, 'value': cardValue}
    
    def _extractDirectoryCard(self, projectLine):
        PROJECT_PATH = ['PROJECT_PATH']
        
        # Handle special case with directory cards in
        # windows. shlex.split fails because windows 
        # directory cards end with an escape character.
        # e.g.: "this\path\ends\with\escape\"
        currLine = projectLine.strip().split()
        
        # Extract Card Name from the first item in the list
        cardName = currLine[0]
        
        if cardName in PROJECT_PATH:
            cardValue = '""'
        else:
            # TODO: Write code to handle nested directory cards
            cardValue = '""'
        
        return {'name': cardName, 'value': cardValue} 

     
class ProjectCard(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'prj_project_cards'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Value Columns
    name = Column(String, nullable=False)
    value = Column(String)
    
    # Relationship Properties
    projectFiles = relationship('ProjectFile', secondary=assocProject, back_populates='projectCards')
    
    def __init__(self, name, value):
        '''
        Constructor
        '''
        self.name = name
        self.value = value
        

    def __repr__(self):
        return '<ProjectCard: Name=%s, Value=%s>' % (self.name, self.value)
    
    def write(self):
        # Determine number of spaces between card and value for nice alignment
        numSpaces = 25 - len(self.name)
        
        # Handle special case of booleans
        if self.value is None:
            line = '%s\n' % (self.name)
        else:
            line ='%s%s%s\n' % (self.name,' '*numSpaces, self.value)
        return line

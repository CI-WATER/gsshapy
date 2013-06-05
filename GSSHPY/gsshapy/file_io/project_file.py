'''
********************************************************************************
* Name: Project File IO Object
* Author: Nathan Swain
* Created On: June 5, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['ProjectFile']

from gsshapy.orm.prj import *

class ProjectFile(object):
    '''
    classdocs
    '''
    path = ''
    session = object
    scenario = object
    data = object
    
    
    def __init__(self, session, scenario):
        '''
        Constructor
        '''
        self.session = session
        self.scenario = scenario
        self.data = self.__retrieve(session, scenario)
        
    
    def write(self, path):
        '''
        Project File Write Method
        '''
        
        
        
    def __retrieve(self, session, scenario):
        '''
        Retrieve project file cards from the database
        '''
        return session.query(ProjectCard, ProjectOption).\
                            join(ProjectOption.card).\
                            filter(ProjectOption.scenarios.contains(scenario)).\
                            all()
        
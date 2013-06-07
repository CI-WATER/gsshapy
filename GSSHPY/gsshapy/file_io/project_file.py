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
        
    
    def write(self, path):
        '''
        Project File Write Method
        '''
        self.data = self.retrieve()
        
        # Initiate write on each ProjectOption
        for crd, opt in self.data:
            print opt.write()
        
        
        
    def retrieve(self):
        '''
        Retrieve project file cards from the database
        '''
        return self.session.query(ProjectCard, ProjectOption).\
                            join(ProjectOption.card).\
                            filter(ProjectOption.scenarios.contains(self.scenario)).\
                            all()
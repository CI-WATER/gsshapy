import os
import re
from builtins import str as text
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import String, Integer
import yaml

from . import DeclarativeBase
from ..base.file_base import GsshaPyFileObjectBase

class ProjectFileEventManager(DeclarativeBase, GsshaPyFileObjectBase):
    __tablename__ = "project_file_event_manager"

    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    project_file_id = Column(Integer, ForeignKey('prj_project_files.id'))
    projectFile = relationship('ProjectFile')
    fileExtension = Column(String, default='yml')
    events = relationship('ProjectFileEvent',
                          lazy='dynamic',
                          cascade="save-update,merge,delete,delete-orphan")  #: RELATIONSHIP


    def _similar_event_exists(self, subfolder):
        """
        Check if events exist
        """
        return self.events.filter_by(subfolder=subfolder).first()

    def _read(self, directory, filename, session, path, name, extension,
              spatial=None, spatialReferenceID=None, replaceParamFile=None):
        """
        ProjectFileEvent Read from File Method
        """
        yml_events = []
        with open(path) as fo:
            yml_events = yaml.load(fo)

        for yml_event in yml_events:
            if os.path.exists(os.path.join(directory, yml_event.subfolder)):
                orm_event = yml_event.as_orm()
                if not self._similar_event_exists(orm_event.subfolder):
                    session.add(orm_event)
                    self.events.append(orm_event)

        session.commit()

    def _write(self, session, openFile, replaceParamFile=None):
        """
        ProjectFileEvent Write to File Method
        """
        openFile.write(
            text(
                yaml.dump([evt.as_yml() for evt in
                           self.events.order_by(ProjectFileEvent.name,
                           ProjectFileEvent.subfolder)]
                          )
            )
        )

    def next_id(self, subfolder):
        """
        ProjectFileEvent Write to File Method
        """
        evt_sim_folders = self.events.filter(
                        ProjectFileEvent.subfolder
                            .like("{0}_%".format(subfolder))
                    )
        max_id = 0
        num_search = re.compile(r'{0}_(\d+)'.format(subfolder), re.IGNORECASE)
        for prj_event in evt_sim_folders:
            found_num = num_search.findall(prj_event.subfolder)
            if found_num is not None:
                max_id = max(max_id, int(found_num[0]))
        return max_id + 1

    def add_event(self, name, subfolder, session):
        """
        Add an event
        """
        if self._similar_event_exists(subfolder):
            subfolder += "_{0}".format(self.next_id(subfolder))
        new_event = ProjectFileEvent(name=name, subfolder=subfolder)
        session.add(new_event)
        self.events.append(new_event)
        session.commit()
        return new_event

    def generate_event(self, session):
        """
        Add an event
        """
        event_name = "event_{0}".format(self.next_id("event"))
        return self.add_event(name=event_name, subfolder=event_name,
                              session=session)

class ProjectFileEvent(DeclarativeBase):
    __tablename__ = "project_file_event"

    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    project_file_event_manager_id = Column(Integer, ForeignKey('project_file_event_manager.id'))
    name = Column(String)
    subfolder = Column(String)

    def __init__(self, name, subfolder):
        self.name = name
        self.subfolder = subfolder

    def __repr__(self):
        return ("{class_name}(name={name}, subfolder={subfolder})"
                .format(class_name=self.__class__.__name__,
                        name=self.name,
                        subfolder=self.subfolder)
                )
    def as_yml(self):
        """
        Return yml compatible version of self
        """
        return YmlFileEvent(name=str(self.name),
                            subfolder=str(self.subfolder))


class YmlFileEvent(yaml.YAMLObject):

    yaml_tag = u'!ProjectFileEvent'

    def __init__(self, name, subfolder):
        self.name = name
        self.subfolder = subfolder

    def __repr__(self):
        return ("{class_name}(name={name}, subfolder={subfolder})"
                .format(class_name=self.__class__.__name__,
                        name=self.name,
                        subfolder=self.subfolder)
                )
    def as_orm(self):
        """
        Returns ORM version of self
        """
        return ProjectFileEvent(name=self.name, subfolder=self.subfolder)

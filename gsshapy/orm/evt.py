import os

from sqlalchemy import Column, ForeignKey, or_
from sqlalchemy.exc import IntegrityError
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
                try:
                    orm_event = yml_event.as_orm()
                    session.add(orm_event)
                    self.events.append(orm_event)
                except IntegrityError:
                    pass

        session.commit()

    def _write(self, session, openFile, replaceParamFile=None):
        """
        ProjectFileEvent Write to File Method
        """
        openFile.write(yaml.dump([evt.as_yml() for evt in self.events.order_by(ProjectFileEvent.name)]))

    def add_event(self, name, subfolder, session):
        """
        Add an event
        """
        int_err = True
        new_event = None
        while int_err:
            try:
                new_event = ProjectFileEvent(name=name, subfolder=subfolder)
                session.add(new_event)
                self.events.append(new_event)
                session.commit()
            except IntegrityError as int_err:
                subfolder += "_{0}".format(self.events.count()+1)
                pass
        return new_event


class ProjectFileEvent(DeclarativeBase):
    __tablename__ = "project_file_event"

    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    project_file_event_manager_id = Column(Integer, ForeignKey('project_file_event_manager.id'))
    name = Column(String)
    subfolder = Column(String, unique=True)

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

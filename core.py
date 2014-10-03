# -*- encoding: utf-8 -*-
import setting
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

class Core():
    _dbe = None
    @property
    def dbe(self):
        if self._dbe is None:
            self._dbe = create_engine(setting.DB)
        return self._dbe
        
    _dbs = None
    @property
    def dbs(self):
        if self._dbs is None:
            self._dbs = sessionmaker(bind=self.dbe)
        return self._dbs
        
    _BaseModel = None
    @property
    def BaseModel(self):
        if self._BaseModel is None:
            self._BaseModel = declarative_base()
        return self._BaseModel
        

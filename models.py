# -*- encoding: utf-8 -*-
#from django.db import models, connection
#from django.utils.translation import ugettext as _
#import markdown
#import os
#import datetime
#from django.template import Template, Context
#from .tools import dict_fetchall

from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Text, DateTime
from core import Core
core = Core()
print core.dbe
BaseModel = core.BaseModel

#class MyBaseModel: #(_BaseModel):
#    @property
#    def __table__(self):
#        return self.__class__.__name__

#class BaseEnum:
#    @classmethod
#    def choices(cls):
#        res = []
#        for a in cls.__dict__:
#            if a[0] != '_' and a != 'choices':
#                res.append((a, cls.__dict__[a]))
#
#        return res


#class EnumField(Column(Integer)):
#    def __init__(self, enum, *args, **kwargs):
#        kwargs["choices"] = enum.choices()
#        super(EnumField, self).__init__(*args, **kwargs)

def ColID():
    return Column(Integer, primary_key=True)
    
def ColFK(table, col = "id"):
    if type(table) is not str:
        table = table.__tablename__
    return Column(Integer, ForeignKey(table + '.' + col))
    

## Moduly
class EntityType(BaseModel):
    __tablename__ = "EntityType"
    id = ColID()
    name = Column(String(200))
    enabled = Column(Boolean)
    class_name = Column(String(200))

#    def get_class(self):
#        p = self.class_name.rfind('.')
#        return getattr(__import__(self.class_name[0:p]).models, self.class_name[p + 1:])
#
#    def __unicode__(self):
#        return self.name


## Obsah
#class EEntityRelType(BaseEnum):
#    Primary = 1
#    Secondary = 2
#    Hide = 3


# Základní entita obsahu
class Entity(BaseModel):
    __tablename__ = "Entity"
    id = ColID()
    name = Column(String(200))
    subname = Column(String(200))
    entity_type = ColFK(EntityType)
    uid = Column(String(200))
    description = Column(Text)
    content = Column(Text)
    date_time = Column(DateTime)

    def get_gear(self):
        entity_type = EntityType.objects.get(id=self.entity_type_id)
        obj = entity_type.get_class()()
        obj.entity = self
        return obj

    # Vrati seznam vnořených entit
    def get_subentites(self, date_valid, in_menu, in_list, order_by=None):
        where = ['r.parent_id = %s']
        params = [self.id]

        if date_valid:
            if type(date_valid) is not datetime.datetime:
                date_valid = datetime.datetime.now()
            where += ['dt_from IS NULL OR dt_from <= %s', 'dt_to IS NULL OR dt_to >= %s']
            params += [date_valid, date_valid]

        if not order_by:
            order_by = 'r.position, e.name'

        return Entity.objects.raw(
            'SELECT e.* FROM mcms_entity e '
            + 'LEFT JOIN mcms_entityrel r ON r.current_id = e.id '
            + 'WHERE (' + ') AND ('.join(where) + ') '
            + 'ORDER BY ' + order_by,
            params
        )

    ### metody pro admin část
    def admin_rels(self):
        cursor = connection.cursor()
        # print "fffff ", self.pk
        cursor.execute(
            'SELECT e.name, r.rel_type, r.position, r.dt_from, r.dt_to, r.in_list, r.in_menu, '
            + 'r.id, r.parent_id '
            + 'FROM mcms_entityrel r '
            + 'LEFT JOIN mcms_entity e ON r.parent_id = e.id '
            + 'WHERE r.current_id = %s '
            + 'ORDER BY rel_type, e.name ',
            [self.id]
        )

        return dict_fetchall(cursor)

    def admin_get(self):
        return {
            'data': {
                'name': self.name,
                'subname': self.subname,
                'content': self.content,
                'description': self.description,
                'rel': self.admin_rels()
            },
            'defs': {}
        }

    @classmethod
    def admin_subentites(cls, id):
        where = ['r.parent_id IS NULL' if id is None else 'r.parent_id = %s']
        params = [] if id is None else [id]

        order_by = 'r.position, e.name'

        cursor = connection.cursor()
        cursor.execute(
            'SELECT e.name, e.id, e.date_time, t.name AS type_name, '
            + 'r.dt_from, r.dt_to, r.in_list, r.in_menu '
            + 'FROM mcms_entity e '
            + 'LEFT JOIN mcms_entitytype t ON t.id = entity_type_id '
            + 'LEFT JOIN mcms_entityrel r ON r.current_id = e.id '
            + 'WHERE (' + ') AND ('.join(where) + ') '
            + 'ORDER BY ' + order_by,
            params
        )

        return dict_fetchall(cursor)

    def __unicode__(self):
        return self.name

    #def __init__(self):
        # pomocna promenna napojeni
        #self.rel = None


# Vazby mezi entitamy
class EntityRel(BaseModel):
    __tablename__ = "EntityRel"
    id = ColID()
    parent = ColFK(Entity)
    current = ColFK(Entity)
    rel_type = Column(Enum("Primary", "Secondary", "Hide"))
    position = Column(Integer)
    dt_from = Column(DateTime)
    dt_to = Column(DateTime)
    in_list = Column(Boolean)
    in_menu = Column(Boolean)


# Soubory navazane ne entity (obrázky, náhledy, přílohy, ...)
class EntityAttach(BaseModel):
    __tablename__ = "EntityAttach"
    id = ColID()
    # Nez se ulozi entita, není známé id entity
    entity = ColFK(Entity)
    file_name = Column(String(200))
    description = Column(Text)
    content_type = Column(String(200))


# Nastavení
#class Setting(BaseModel):


# Základní prováděcí třída
class BaseGear(object):
    entity = None
    entity_class = None
    detail_template = None
    request = None
    context = {}

    def set_template(self, path, file_name):
        self.detail_template = os.path.dirname(path) + '/' + file_name

    def show_detail(self):
        with open(self.detail_template) as f:
            t = Template(f.read())

        return t.render(Context(dict({
            'content_html': self.content_html,
            'entity': self.entity,
            'gear': self
        }.items() + self.context.items())))

    @property
    def content_html(self):
        return markdown.markdown(self.entity.content)

    @property
    def description_html(self):
        return markdown.markdown(self.entity.content)

    #
    def prepare(self):
        pass

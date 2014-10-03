# -*- coding: utf-8 -*-
from django.db import connection
import datetime

from mcms.models import EEntityRelType

# Zkrácená cesta na webu má tento formát:
#    aktualni_prvek[-prvek_cesty-dalsi_prvek_cesty-...]
#    Prvek cesty se uvádí jen v případě že cesta prochází sekundárním spojením
# Generovani menu, drobeckove navigace, sitemapy


class MenuItem(object):

    def __init__(self, params):
        (self.entity_id, self.parent_id, self.rel_id, self.name,
            self.rel_type, self.position, self.in_in_list, self.in_menu) = params

    entity_id = None
    parent_id = None
    rel_id = None
    name = None
    rel_type = None
    position = None
    in_list = None
    in_menu = None

    level = 0
    in_path = False
    selected = False

    def url_id(self):
        return str(self.entity_id)

    @property
    def css_class(self):
        cls = []
        if self.in_path:
            cls.append("in-path")
        if self.selected:
            cls.append("selected")
        return cls

    def __str__(self):
        return ("+" * self.level) + " " + self.name + " #" + str(self.entity_id) \
            + " (" + " ".join(self.css_class) + ")"


class Navigate(object):

    items = []
    path = []
    items_by_id = {}
    items_by_parent = {}
    entity_id = None

    def load(self, path_str, date_valid, root_entity=[], order_by=None, in_menu=None):
        self.items = []
        self.path = []
        self.items_by_parent = {}
        self.items_by_id = {}
        path_ids = path_str.split('-')
        # path_ids.reverse()
        # print path_ids
        eid = int(path_ids[0]) if path_ids[0] != "None" else None
        self.entity_id = eid
        # path_ids = path_ids[1:]
        self.path = []
        # nacte cestu
        while eid:
            self.path.append(int(eid))
            if eid in root_entity:
                break
            # Najdi nadrazeny uzel
            cursor = connection.cursor()
            cursor.execute(
                "SELECT parent_id FROM mcms_entityrel WHERE current_id= %s "
                # + "ORDER BY current_id IN (" + ", ".join(path_ids) + ") DESC, rel_type",
                + "ORDER BY current_id IN (" + ', '.join(['%s'] * len(path_ids))
                + ") DESC, rel_type",
                [eid] + path_ids
            )
            r = cursor.fetchone()
            eid = r[0] if r else None
        else:
            self.path.append(None)

        params = []
        where = []

        if date_valid:
            if type(date_valid) is not datetime.datetime:
                date_valid = datetime.datetime.now()
            where += ['dt_from IS NULL OR dt_from <= %s', 'dt_to IS NULL OR dt_to >= %s']
            params += [date_valid, date_valid]

        if not order_by:
            order_by = 'r.position, e.name, e.id'

        subwhere = []
        if len(self.path):
            subwhere += [
                "r.parent_id IN (" + ', '.join(['%s'] * len(self.path)) + ")",
                "e.id IN (" + ', '.join(['%s'] * len(self.path)) + ")"
            ]
            params += self.path * 2

        if len(root_entity) == 0:
            subwhere += ["r.parent_id IS NULL"]

        where += [" OR ".join(subwhere)]
        if in_menu is not None:
            where += ["in_menu = 1" if in_menu else "in_menu = 0"]

        q = "SELECT e.id AS entity_id, r.parent_id, r.id AS rel_id, e.name, " \
            + "r.rel_type, r.position, r.in_list, r.in_menu " \
            + "FROM mcms_entity e " \
            + "LEFT JOIN mcms_entityrel r ON  r.current_id = e.id " \
            + "WHERE (" + ") AND (".join(where) + ") " \
            + "ORDER BY " + order_by

        cursor = connection.cursor()
        print((q, params))
        cursor.execute(q, params)

        for item in cursor:
            menu_item = MenuItem(item)
            menu_item.in_path = menu_item.entity_id in self.path
            menu_item.selected = menu_item.entity_id == self.entity_id
            self.items.append(menu_item)
            self.items_by_id[menu_item.entity_id] = menu_item
            if menu_item.parent_id not in self.items_by_parent:
                self.items_by_parent[menu_item.parent_id] = []
            self.items_by_parent[menu_item.parent_id].append(menu_item)

    def path_items(self):
        print(("path_items: ", self.items_by_id, self.path))
        p = [self.items_by_id[id] for id in self.path if id is not None and id in self.items_by_id]
        p.reverse()
        return p

    def single(self, level):
        # parent_id = None if level == 0 else self.path[level]
        parent_id = self.path[level - 1]
        if parent_id in self.items_by_parent:
            return self.items_by_parent[parent_id]
        else:
            return []

    def tree(self, from_level):
        ls = []
        self.tree_node(None, ls, from_level, -1)

        return ls

    def tree_node(self, id, ls, from_level, level=0):
        if id not in self.items_by_parent:
            return

        #print id, self.items_by_parent

        for item in self.items_by_parent[id]:
            item.level = level
            if level >= from_level:
                ls.append(item)
            self.tree_node(item.entity_id, ls, from_level, level + 1)

    def short_path(self, id, parent_id=None):
        # print self.items_by_id
        if id in self.items_by_id:
            item = self.items_by_id[id]
            path_str = item.url_id()
            pid = item.parent_id
        else:
            path_str = str(id)
            pid = int(parent_id)

        while pid:
            if pid not in self.items_by_id:
                break
            item = self.items_by_id[pid]
            if item.rel_type == EEntityRelType.Secondary or True:
                path_str += "-" + item.url_id()
            pid = item.parent_id

        #print path_str, type(path_str)
        return path_str

    def url(self, id, parent_id=None):
        return "/article/" + self.short_path(id, parent_id)

    def admin_json(self):
        return {
            'tree': [
                {
                    'name': item.name,
                    'level': item.level + 1,
                    'id': item.entity_id,
                    'inPath': item.in_path
                } for item in self.tree(-1)
            ],
            'path': [
                {
                    'name': item.name,
                    'level': item.level + 1,
                    'id': item.entity_id
                } for item in self.path_items()
            ]
        }

#!/usr/bin/python
#-*-coding: utf-8 -*-

import threading
import sqlite3

import sys

__module__ = sys.modules[__name__]

def setup_database(database):
    Mapper.initialize(database)

def bind_mapper(mapper_name, model_cls, mapper_cls = None):

    if mapper_cls is None:
        mapper_cls = Mapper
    mapper = mapper_cls(model_cls)
    setattr(__module__, mapper_name, mapper)

class FieldError(Exception):

    def __init__(self, message,  *args, **kwargs):
        Exception.__init__(self, message, *args, **kwargs)


class Field:

    def __init__(self, name, affinity=None, validator=None, required=False, default=None,  **kwargs):

        self.affinity = affinity
        self.validator = validator
        self.default = default
        self.required = required
        self.name = name
        self.kwargs = kwargs

    def get_value(self):
        if hasattr(self, "data"):
            return self.data
        else:
            raise FieldError("Field is not initilize")

    def set_value(self, value):
        self.value = self.process_formdata(value)

    value = property(get_value, set_value)

    def validate(self):
        if self.required and self.data is None:
            raise FieldError("Field is required!")
        if self.value == self.default:
            return
        if self.validator:
            self.validator(self)

    def process_formdata(self, value):
        if value or self.required == False:
            try:
                self.data = value
            except ValueError:
                self.data = None
                raise ValueError('Not a valid integer value')

    def _pre_validate(self):
        pass

    def __call__(self):
        if hasattr(self, "value"):
            return self.value
        else:
            raise FieldError("Filed is not initilize")


class IntegerField(Field):

    """
    A text field, except all input is coerced to an integer.  Erroneous input
    is ignored and will not be accepted as a value.
    """

    def __init__(self, name, affinity=None, validator=None, required=False, defalut=None,  **kwargs):
        Field.__init__(self, name, validator, required, defalut,  **kwargs)

    def process_formdata(self, value):
        if value:
            try:
                self.value = int(value)
            except ValueError:
                self.value = None
                raise ValueError('Not a valid integer value')


def with_metaclass(meta, bases=(object,)):
    return meta("NewBase", bases, {})

class ModelMeta(type):

    def __new__(metacls, cls_name, bases, attrs):
        fields = {}
        new_attrs = {}
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                fields[k] = v
            else:
                new_attrs[k] = v

        cls = type.__new__(metacls, cls_name, bases, new_attrs)
        cls.fields = cls.fields.copy()
        cls.fields.update(fields)
        return cls

class ModelMinix(object):

    fields = {}
    
    def __str__(self):
        return '<' + self.__class__.__name__ + \
            ' : {' + ", ".join(["%s=%s" % (field.name, getattr(self, column))
                                for column, field in self.fields.items()]) + '}>'

    def save(self):
        return self.__mapper__.save(self)
      
        
class Model(with_metaclass(ModelMeta, (ModelMinix,))):

    def __init__(self, **kwargs):
        for k in kwargs:
            try:
                if k in self.fields:
                    setattr(self, k, kwargs[k])
            except:
                raise ValueError("not found filed %s" % (k))

    def __json__(self):
        raise NotImplemented("subclass of Model must implement __json__")

    @classmethod
    def create_table(cls):
        raise NotImplemented("subclass of Model must implement create_table")



class Mapper:

    _local = threading.local()

    """Database Mapper"""
    def __init__(self, model_cls):
         self.model = model_cls
         self.model.__mapper__ = self

    @staticmethod
    def initialize(database):
        if not hasattr(Model, "__database__ "):
            Mapper.__database__ = database

    def execute(self, sql):
        with self.connect() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
            except sqlite3.Error, e:   
                conn.rollback()

    def query(self, sql):
        with self.connect() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql)
                return cursor.fetchall()
            except sqlite3.Error as e:
                raise e


    @staticmethod
    def initialized():
        """Returns true if the class variable __database__ has been setted."""
        print Mapper.__database__
        return hasattr(Mapper, "__database__")

    @classmethod
    def connect(cls):
        """create a thread local connection if there isn't one yet"""
        # print('connect',cls)
        if not hasattr(cls._local, 'conn'):
            try:
                cls._local.conn = sqlite3.connect(cls.__database__)
                #cls._local.conn.execute('pragma integrity_check')
                cls._local.conn.row_factory = sqlite3.Row
            except sqlite3.Error, e:    
                print "Error %s:" % e.args[0]
        return cls._local.conn


    def create_table(self):
        sql = 'CREATE TABLE ' + self.model.__tablename__ +' (\n'

        column_sql = []
        for name, field in self.model.fields.iteritems():
            column_sql.append('\t' + name + ' ' + field.affinity)
        sql += ',\n'.join(column_sql)
        sql += '\n)'
        self.execute(sql)

    def drop_table(self):
        sql = 'DROP TABLE IF EXISTS ' + self.model.__tablename__
        self.execute(sql)

    def deleteby(self, paterns=None, **kwargs):
        dels = []
        vals = []
        for k, v in kwargs.iteritems():
            if k in self.model.fields:
                dels.append(k + '=?')
                vals.append(v)
        sql = 'DELETE FROM %s WHERE %s' % (self.model.__tablename__, ' AND '.join(dels))
        with self.connect() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql, vals)
                conn.commit()
                return True
            except sqlite3.Error as e:    
                conn.rollback()
        return False

    def save(self, model):
        cols = model.fields.keys()
        vals = [getattr(model, c) for c in self.model.fields]
        sql = 'INSERT INTO ' + self.model.__tablename__ + \
            ' ('  + ', '.join(cols) + ')' + \
            ' VALUES (' + ', ' .join(['?'] * len(cols)) + ')'
        with self.connect() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(sql, vals)
                conn.commit()
                return True
            except sqlite3.Error as e:    
                conn.rollback()
        return False




    

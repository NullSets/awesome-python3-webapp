
# import json
#
#
# with open("text.txt", encoding="UTF-8") as f:
#     j = json.load(f)
#
# print(type(j))

from pprint import pprint

import time

import asyncio

#from www.models import next_id
#from www.orm import Model, StringField, BoolanField, FloatField


class A(dict):
    def __init__(self,**kw):
        print("__init__")
        super(A, self).__init__(**kw)

    def __setattr__(self, key, value):
        print("__setattr__")
        super(A, self).__setattr__(key,value)

    def __getattr__(self, item):
        return self[item]

    def __getattribute__(self, item):
        print("__getattribute__")
        object.__getattribute__(self, item)

    def __setitem__(self, key, value):
        print("__setitem__")
        super(A, self).__setitem__(key,value)

    def __getitem__(self, item):
        print("__getitem__")
        super(A, self).__getitem__(item)

# a = A()
# #pprint(dir(a))
# a.name = "123"
# # a['age'] = 12
#
# print(a.name)
# print(a['age'])
# pprint(a.__dict__)
# pprint(a)
# pprint(A.__dict__)
#
# print(dir(a))


class B(dict):
    b = 123

    def __init__(self, **kw):
        self.att = 1
        super(B, self).__init__(**kw)

    def setA(self,key, value):
        self[key] = value

    def __setitem__(self, key, value):
        print("__setitem__")
        super(B, self).__setitem__(key,value)

    def __getitem__(self, item):
        print("__getitem__")
        return super(B, self).__getitem__(item)

    def __getattr__(self, key):
        try:
            print("__getattr__")
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        print("__setattr__")
        self[key] = value

    def getAtt(self):
        print("getAtt")
        return self.att


a = B(name='dwl', age=12, address="福田")
#
# # print(a.__dict__)
# print(B.__dict__)
# # print(dir(a))
# # print(dir(B))
#
# # a.setA("aaaa","123")
print(a['name'])
print(a.name)
#
# print(a.getAtt())





# class User(Model):
#     __table__ = "users"
#
#     id = StringField(primary_key=True,default=next_id,ddl="varchar(50)")
#     email = StringField(ddl="varchar(50)")
#     passwd = StringField(ddl="varchar(50)")
#     admin = BoolanField()
#     name = StringField(ddl="varchar(50)")
#     image = StringField(ddl="varchar(500)")
#     created_at = FloatField(default=time.time)
#
# user = User(id=1)
#
# print(dir(user.items()))
# print(user.items())

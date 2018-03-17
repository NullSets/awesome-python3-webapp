

# from  www.ORM import Model,StringField,IntegerField
#
#
# class User(Model):
#     __table__ = 'users'
#
#     id = IntegerField(primary_key=True)
#     name = StringField()
#
# user = User(id = 123,name = 'dwl')
# users = User.find()




# import time
# import www.orm as orm
# from www.models import User,Blog,Comment
# import asyncio
#
#
# async def test(loop):
#     await orm.create_pool(loop,user="www-data",password='www-data',db='awesome')
#
#     u = User(name ='Test',email='test1@example.com',passwd='1234567890',image='about:blank')
#
#     await u.save()
#
#
# loop = asyncio.get_event_loop()
# # loop.run_until_complete(test(loop))





# import inspect
# # inspect.Parameter.kind 类型：
# # POSITIONAL_ONLY          位置参数
# # KEYWORD_ONLY             命名关键词参数
# # VAR_POSITIONAL           可选参数 *args
# # VAR_KEYWORD              关键词参数 **kw
# # POSITIONAL_OR_KEYWORD    位置或必选参数
# def foo(a, b=10, *c, d, **kw):
#     pass
#
# sig = inspect.signature(foo)
# for k,v in sig.parameters.items():
#     print("k===>%s" % k)
#     print("v ==>%s" % v.kind)
# """
# k===>a
# v ==>POSITIONAL_OR_KEYWORD
# k===>b
# v ==>POSITIONAL_OR_KEYWORD
# k===>c
# v ==>VAR_POSITIONAL
# k===>d
# v ==>KEYWORD_ONLY
# k===>kw
# v ==>VAR_KEYWORD
#
# """




# import os
# print(os.path.dirname(os.path.abspath(__file__)))





# a = 1,2,3,8
# b = 4,5,6
#
# for k,v in zip(a,b):
#     print(k,v)





class Fun(dict):
    def __init__(self,**kw):
        super(Fun, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError("no '%s'" % key)

    def __getattribute__(self, item):
        return ("invoke_getattribute",item)

    def __setattr__(self, key, value):
        self[key] = value





class Dict(dict):
    '''
    通过使用__setattr__,__getattr__,__delattr__
    可以重写dict,使之通过“.”调用
    '''

    def __setattr__(self, key, value):
        print("In '__setattr__")
        self[key] = value
        # self.__dict__[key] = value

    def __getattr__(self, key):
        try:
            print("In '__getattr__")
            return self[key]
        except KeyError as k:
            return None

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            return None

    # __call__方法用于实例自身的调用,达到()调用的效果
    def __call__(self, key):  # 带参数key的__call__方法
        try:
            print("In '__call__'")
            return self[key]
        except KeyError as k:
            return "In '__call__' error"


s = Dict()
print(s.__dict__)
# {}

s.name = "hello"    # 调用__setattr__
# In '__setattr__

print(s.__dict__) # 由于调用的'__setattr__', name属性没有加入实例属性字典中。
# {}
print(s['name'])
# hello

print(s("name"))    # 调用__call__
# In '__call__'
# hello

print(s["name"])    # dict默认行为
# hello

# print(s)
print(s.name)       # 调用__getattr__
# In '__getattr__
# hello

del s.name          # 调用__delattr__
print(s("name"))    # 调用__call__
# None





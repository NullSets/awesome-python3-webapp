

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






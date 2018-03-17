#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import asyncio,inspect

__author__ = 'Michael Liao'


"""
url handlers
"""

from www.coroweb import get
from www.models import User,Blog
import time

# @get("/")
# async def index(request=None):
#     return "<h1>Awesome</h1>"
#
# @get("/hello")
# async def hello(request=None):
#     return "<h1>hello</h1>"
#
#
# if __name__ == "__main__":
#     print(asyncio.iscoroutinefunction(index))
#     print(inspect.isgeneratorfunction(index))
#     index = asyncio.coroutine(index)
#     print(asyncio.iscoroutinefunction(index))
#     print(inspect.isgeneratorfunction(index))

#
# @get("/")
# async def index(request=None):
#     users =await User.findAll()
#     return {
#         "__template__":"test.html",
#         "users":users
#     }



@get("/")
def index(request=None):
    summary = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    blogs = [
        Blog(id="1",name="'Test Blog",summary=summary,created_at=time.time()-120),
        Blog(id="2",name="Something New",summary=summary,created_at=time.time()-3600),
        Blog(id="3", name="'Learn Swift", summary=summary, created_at=time.time() - 7200)
    ]
    return {
        "__template__":"blogs.html",
        "blogs":blogs
    }

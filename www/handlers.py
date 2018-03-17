#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import asyncio,inspect

__author__ = 'Michael Liao'


"""
url handlers
"""

from www.coroweb import get
from www.models import User

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


@get("/")
async def index(request=None):
    users =await User.findAll()
    return {
        "__template__":"test.html",
        "users":users
    }


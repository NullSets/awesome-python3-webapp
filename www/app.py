#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


__author__ = 'Michael Liao'

"""
async web application
"""

import logging
logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader

import www.orm
from www.coroweb import add_routes, add_static
from www.handlers import cookie2user, COOKIE_NAME


def init_jinja2(app, **kw):
    logging.info("init jinja2...")
    options = dict(
        # 自动转义xml/html的特殊字符
        autoescape = kw.get("autoescape",True),
        # 代码块的开始、结束标志
        block_start_string = kw.get("block_start_string","{%"),
        block_end_string = kw.get("block_end_string","%}"),
        # 变量的开始、结束标志
        variable_start_string = kw.get("variable_start_string","{{"),
        variable_end_string = kw.get("variable_end_string","}}"),
        # 自动加载修改后的模板文件
        auto_reload=kw.get("auto_reload",True)
    )
    # 获取模板文件夹路径
    path = kw.get("path",None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"templates")
    logging.info("set jinja2 template path: %s" % path)
    # Environment类是jinja2的核心类，用来保存配置、全局对象以及模板文件的路径
    # FileSystemLoader类加载path路径中的模板文件
    env = Environment(loader=FileSystemLoader(path), **options)
    # todo  还不懂这个变量filters
    filters = kw.get("filters",None)
    if filters is not None:
        for name, f in filters.items():
            # filters是Environment类的属性：过滤器字典
            env.filters[name] = f
    # 所有的一切是为了给app添加__templating__字段
    # 前面将jinja2的环境配置都赋值给env了，这里再把env存入app的dict中，这样app就知道要到哪儿去找模板，怎么解析模板。
    app["__templating__"] = env  # app是一个dict-like对象


# 编写用于输出日志的middleware
async def logger_factory(app,handler):
    async def logger(request):
        logging.info("Request: %s %s" % (request.method,request.path))
        # await asyncio.sleep(0.3)
        #logging.info("logger_factory.................%s" % str(handler))
        return (await handler(request))
    return logger


async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith("application/json"):
                request.__data__ =  await request.json()
                logging.info("request form: %s" % str(request.__data__))
            elif request.content_type.startswith("application/x-www-form-urlencoded"):
                request.__data__ = await request.post()
                logging.info("request form: %s" % str(request.__data__))
        return (await handler(request))
    return parse_data


# 请求对象request的处理工序：
#       logger_factory => response_factory => RequestHandler().__call__ => handler
#
async def response_factory(app,handler):
    async def response(request):
        logging.info("Response handler...")
        #logging.info("response_factory.................%s" % str(handler))
        r = await handler(request)
        logging.info("Response result = %s" % str(r))
        if isinstance(r,web.StreamResponse):  # StreamResponse是所有Response对象的父类
            return r  # 无需构造，直接返回
        if isinstance(r,bytes):
            resp = web.Response(body=r)  # 继承自StreamResponse
            resp.content_type = "application/octet-stream"
            return resp
        if isinstance(r,str):
            # 重定向
            if r.startswith("redirect:"):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode("utf-8"))
            resp.content_type = "text/html;charset=utf-8"
            return resp
        if isinstance(r,dict):
            # 在后续构造视图函数返回值时，会加入__template__值，用以选择渲染的模板
            template = r.get('__template__',None)
            if template is None:
                # ensure_ascii：默认True，仅能输出ascii格式数据。故设置为False。
                resp = web.Response(body=json.dumps(r, ensure_ascii=False,default=lambda o: o.__dict__).encode("utf-8"))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                r["__user__"] = request.__user__
                # app[__templating__]获取已初始化的Environment对象，调用get_template()方法返回的Template对象
                # 调用Template对象的render（）方法，传入r渲染模板，返回unicode格式字符串，转为utf-8编码
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode("utf-8"))
                resp.content_type = "text/html;charset=utf-8"
                return resp
        # 返回响应码
        if isinstance(r,int) and r >= 100 and r < 600:
            return web.Response(status=r)
        # 返回响应码和原因 如：(200, 'OK'), (404, 'Not Found')
        if isinstance(r,tuple) and len(r) == 2:
            status_code, message = r
            if isinstance(status_code,int) and status_code >= 100 and status_code < 600:
                return web.Response(status=status_code, text=str(message))
        # default:
        resp = web.Response(body=str(r).encode("utf-8"))
        resp.content_type = "text/plain;charset=utf-8"
        return resp
    return response


async def auth_factory(app, handler):
    async def auth(request):
        logging.info("check user: %s %s" % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = await cookie2user(cookie_str)
            if user:
                logging.info("ser current user: %s" % user.email)
                request.__user__ = user
        if request.path.startswith("/manager/") and (request.__user__ is None or not request.__user__.admin):
            return web.HTTPFound("/signin")
        return (await handler(request))
    return auth


# 过滤器
def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u"1分钟前"
    if delta < 3600:   # 小时
        return u"%s分钟前" % (delta // 60)
    if delta < 86400:   # 天
        return u"%s小时前" % (delta // 3600)
    if delta < 604800:  # 周
        return u"%s天前" % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u"%s年%s月%s日" % (dt.year,dt.month,dt.day)


async def init(loop):
    await www.orm.create_pool(loop=loop, host="127.0.0.1", port=3306, user="www-data", password="www-data",
                              db="awesome")
    app = web.Application(loop=loop, middlewares=[
        logger_factory, auth_factory, response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, "handlers")
    add_static(app)
    srv = await loop.create_server(app.make_handler(), "127.0.0.1", 9000)
    logging.info("server started at http://127.0.0.1:9000...")
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()


"""
  logger_factory --> response_factory --> RequestHandler.__call__() --> handler()
"""



#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


__author__ = "Michael Liao"


import asyncio ,os,inspect,logging,functools
from urllib import parse
from aiohttp import web
from www.apis import APIError


def get(path):
    """
    Define decorator @get("/path")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator


def post(path):
    """
    Define decorator @post("/path")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = "POST"
        wrapper.__route__ = path
        return wrapper
    return decorator


def get_required_kw_args(fn):
    # 获取无默认值的命名关键名参数
    args = []
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)


def get_named_kw_args(fn):
    # 获取命名关键字参数
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)


def has_named_kw_args(fn):
    # 判断是否有命名关键字参数
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True


def has_var_kw_arg(fn):
    # 判断是否有关键字参数
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


def has_request_arg(fn):
    # 判断是否含有名叫'request'的参数，且位置在最后
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    print(found)
    return found


# 定义RequestHandler从url处理函数中分析其需要接受的参数，从web.Request中获取必要的参数
# 调用url处理函数，然后把结果转换为web.Response对象，符合aiohttp框架要求
class RequestHandler(object):

    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    async def __call__(self, request):
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_args or self._has_request_arg:
            if request.method == "POST":
                if not request.content_type:
                    return web.HTTPBadRequest(text="Missing Content-Type.")
                ct = request.content_type.lower()
                if ct.startswith("application/json"):
                    params = await request.json()
                    if not isinstance(params,dict):
                        return web.HTTPBadRequest(text="JSON body must be object.")
                    kw = params
                elif ct.startswith("application/x-www-form-urlencoded") or ct.startswith("multipart/form-data"):
                    params = await request.post() # 返回post的内容中解析后的数据。键值对
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest(text="Unsupported Content-Type: %s" % request.content_type)
            if request.method == "GET":
                qs = request.query_string    # url ? 后的键值
                if qs:
                    kw = dict()
                    """                             
                    解析url中?后面的键值对的内容 
                    qs = 'first=f,s&second=s' 
                    parse.parse_qs(qs, True).items() 
                    >>> dict([('first', ['f,s']), ('second', ['s'])]) 
                    """
                    for k,v in parse.parse_qs(qs,True).items():    # True表示不忽略空格
                        kw[k] = v[0]
        # post/get 是否有传值（body中或url？后的键值）
        if kw is None:
            # request.match_info返回dict对象。可变路由中的可变字段{variable}为参数名，传入request请求的path为值
            # 若存在可变路由：/a/{name}/c，可匹配path为：/a/jack/c的request
            # 则reqwuest.match_info返回{name = jack}
            kw = dict(**request.match_info)
        else:
            # 若url处理函数只有命名关键词参数没有关键词参数
            if not self._has_var_kw_arg and self._named_kw_args:
                # remove all unamed kw:
                copy = dict()
                # 只保留命名关键字参数，移除url处理函数参数中不存在的参数值（如果有）
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            # check named arg:
            for k,v in request.match_info.items():
                # 是否存在相同名称
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        # 若存在request
        if self._has_request_arg:
            kw['request'] = request
        # 若存在无默认值的命名关键字参数
        if self._required_kw_args:
            for name in self._required_kw_args:
                # 若未传入必须的参数值，则报错
                if not name in kw:
                    return web.HTTPBadRequest(text="Missing argument: %s" % name)
        logging.info("call with args: %s" % str(kw))
        try:
            # 调用url处理函数
            r = await self._func(**kw)
            return r
        except APIError as e:
           return dict(error=e.error,data=e.data,message=e.message)


def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
    app.router.add_static('/static/',path)
    logging.info("add static %s => %s" % ('/static',path))


def add_route(app, fn):
    method = getattr(fn,"__method__",None)
    path = getattr(fn,"__route__",None)
    if path is None or method is None:
        raise ValueError("@get or @post no defined in %s." % str(fn))
    # 判断URL处理函数是否是协程 并且 是生成器（URL处理函数都不是）
    # @asyncio.coroutine可以把一个generator标记为coroutine类型
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        # 转换成协程
        fn = asyncio.coroutine(fn)
    logging.info("add route %s %s => %s(%s)" % (method, path,fn.__name__,
                                                ','.join(inspect.signature(fn).parameters.keys())))
    # RequestHandler是一个类,由于定义了__call__()方法，因此可以将其实例视为函数。
    app.router.add_route(method,path,RequestHandler(app,fn))


# 批量注册
def add_routes(app,module_name):
    n = module_name.rfind(".")
    if n == (-1):
        mod = __import__(module_name,globals(),locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n],globals(),locals(),[name]),name)
    for attr in dir(mod):
        if attr.startswith("_"):
            continue
        fn = getattr(mod,attr)
        if callable(fn):
            method = getattr(fn,"__method__",None)
            path = getattr(fn,"__route__",None)
            if method and path:
                add_route(app, fn)

































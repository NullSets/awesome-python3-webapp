# -*- coding:UTF-8 -*-


__author__ = 'Michael Liao'

import asyncio
import aiomysql
import logging
# 设置调试级别level，此处为logging.INFO，不设置logging.info()没有任何作用等同于pass
logging.basicConfig(level=logging.INFO)

"""
由于Web框架使用了基于asyncio的aiohttp，这是基于协程的异步模型。在协程中，不能调用普通的同步IO操作，
因为所有用户都是由一个线程服务的，协程的执行速度必须非常快，才能处理大量用户的请求。
而耗时的IO操作不能在协程中以同步的方式调用，否则，等待一个IO操作时，系统无法响应任何其他用户。
这就是异步编程的一个原则：
一旦决定使用异步，则系统每一层都必须是异步，“开弓没有回头箭”。
幸运的是aiomysql为MySQL数据库提供了异步IO的驱动。
"""


def log(sql,args=()):
    logging.info("SQL: %s" % sql)



async def create_pool(loop,**kw):
    logging.info("create database conncetion pool...")
    # 此处为全局变量,相当于在函数外定义了一个变量,但是有一点区别是,函数外声明的变量一旦import导入模块,就声明了,
    # 在函数内部通过global声明全局变量,函数不执行,就不会创建该全局变量(这里是个人理解,总之一点global声明的变量是全局变量,
    # 如果在函数内部声明的,该函数不执行,在函数外部访问时,会报错,因为函数不执行,该全局变量就未被声明)
    global  __pool
    __pool = await aiomysql.create_pool(
        host = kw.get("host","localhost"),
        port = kw.get("port",3306),
        user = kw["user"],
        password = kw["password"],
        db = kw["db"],
        charset = kw.get("charset","utf8"),
        autocommit = kw.get("autocommit",True),
        maxsize = kw.get("maxsize",10),
        minsize = kw.get("minsize",1),
        loop = loop
    )
"""
#注意到yield from将调用一个子协程（也就是在一个协程中调用另一个协程）并直接获得子协程的返回结果。
"""


async def select(sql,args,size=None):
    log(sql,args)
    global __pool
    # 例子中用的get()方法来获取数据库连接,最新的文档中使用的是acquire(),所以在此做出修改
    # 异步上下文管理器 async with  ；异步迭代器  async for
    async with __pool.acquire() as conn:
        # 获取游标,默认游标返回的结果为元组,每一项是另一个元组,这里可以指定元组的元素为字典通过aiomysql.DictCursor
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 第一个sql语句可以包含占位符，第二个为占位符对应的值，使用该形式可以避免直接使用字符串拼接出来的sql的注入攻击
            # sql占位符为? ，而mysql的占位符为%s，故替换
            await cur.execute(sql.replace("?", "%s"), args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                # 获取所有数据，此处返回的是一个数组，数组元素为字典
                rs =await cur.fetchall()
            logging.info("rows returned: %s" % len(rs))
            return rs


async def execute(sql, args, autocommit=True):
    log(sql)
    async with __pool.acquire() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace("?", "%s"), args)
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                # 回滚,在执行commit()之前如果出现错误,就回滚到执行事务前的状态,以免影响数据库的完整性
                await conn.rollback()
            raise
        return affected



# 创建拥有占位符的字符串
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ','.join(L)



# 该类是为了保存数据库列名和类型的基类
class Field(object):
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type   # 类型
        self.primary_key = primary_key  # 是否为主键
        self.default = default  # 默认值
    def __str__(self):
        return "<%s,%s:%s>" % (self.__class__.__name__,self.column_type,self.name)


class StringField(Field):
    def __init__(self,name=None,primary_key = False,default=None,ddl="varchar(100)"):
        super(StringField, self).__init__(name,ddl,primary_key,default)


class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super(IntegerField, self).__init__(name,'bigint',primary_key,default)


class BoolanField(Field):
    def __init__(self,name=None, default=False):
        super(BoolanField, self).__init__(name, 'boolean',False,default)


class FloatField(Field):
    def __init__(self,name=None,primary_key=False,default=0.0):
        super(FloatField, self).__init__(name,"real",primary_key,default)


class TextField(Field):
    def __init__(self,name=None,default=None):
        super(TextField, self).__init__(name,'text',False,default)


class ModelMetaclass(type):
    def __new__(cls, name,bases,attrs):
        # 排除model类本身
        if name == "Model":
            return type.__new__(cls,name,bases,attrs)
        # 保存表名,如果获取不到,则把类名当做表名,完美利用了or短路原理
        tableName = attrs.get("__table__",None) or name
        logging.info("found model: %s (table: %s)" % (name,tableName))
        # 准备获取所有的Field和主键名
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            # 是列名的就保存下来
            if isinstance(v, Field):
                # 如 id = IntegerField("id"), k为id，v为实例
                logging.info(" found mapping: %s ==> %s" % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # 找到主键
                    if primaryKey:
                        raise RuntimeError("Duplicate primary key for field: %s" % k)
                    primaryKey = k
                else:
                    # 保存非主键的列名
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError("Primary key not found")
        # 从类属性中去除Field，否则，容易造成运行时错误（实例的属性会遮盖类的同名属性）
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f:'`%s`' % f, fields))
        attrs['__mapping__'] = mappings  #保存属性和列的映射关系 如 id = IntegerField()
        attrs["__table__"] = tableName    #表名
        attrs["__primary_key__"] = primaryKey   #主键属性名 如 id
        attrs["__fields__"] = fields  # 除主键外的属性名   如 name、age等
        # 构造默认的SELECT,INSERT,UPDATE和DELETE语句：
        # 其中添加的反引号``,是为了避免与sql关键字冲突的,否则sql语句会执行出错
        attrs["__select__"] = "select `%s`,%s from `%s`" % (primaryKey,','.join(escaped_fields),tableName)
        attrs['__insert__'] = "insert into `%s` (%s,`%s`) VALUES (%s)" % (tableName,','.join(escaped_fields),primaryKey,
                                                                          create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = "update `%s` set %s where `%s`=?" % (tableName, ','.join(map(lambda f: '`%s`=?' % (mappings.get(f).name), fields)), primaryKey)
        attrs['__delete__'] = "delete from `%s` where `%s`=?" % (tableName,primaryKey)
        return type.__new__(cls,name,bases,attrs)
"""反引号是为了区分的保留字与普通字符而引入的符号。
举个例子：SELECT `select` FROM `test` WHERE select='字段值',
在test表中，有个select字段，如果不用反引号，Mysql将把select视为保留字而导致出错，所以，有Mysql保留字作为字段或者表名的，必须加上反引号来区分 .
"""


# 所有ORM映射的基类Model
class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        # super().__init__(**kw)
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        # 获取对象object的属性或者方法
        # 调用getattr获取一个未存在的属性,也会走__getattr__方法,但是因为指定了默认返回的值,__getattr__里面的
        # 错误永远不会抛出
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mapping__[key]
            if field.default is not None:
                # field.default是方法的话就调用，否则返回值
                value = field.default() if callable(field.default) else field.default
                logging.debug("using default value for %s: %s" % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    async def findAll(cls,where=None,args=None,**kw):
        "fine objects by where clause."
        sql = [cls.__select__]
        if where:
            sql.append("where")
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get("orderBy",None)
        if orderBy:
            sql.append("order by")
            sql.append(orderBy)
        limit = kw.get("limit",None)
        if limit is not None:
            sql.append("limit")
            if isinstance(limit,int):
                sql.append("?")
                args.append(limit)
            elif isinstance(limit,tuple) and len(limit) == 2:
                sql.append("?,?")
                args.extend(limit)
            else:
                raise ValueError("Invalid limit value: %s" % str(limit))
        rs = await select(' '.join(sql),args)
        return [cls(**r) for r in rs]

    # 查询数量
    @classmethod
    async def findNumber(cls,selectField,where=None,args=None):
        "find number by select and where"
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]    # _num_ :别名
        if where:
            sql.append("where")
            sql.append(where)
        rs = await select(' '.join(sql),args,1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    @classmethod
    async def find(cls,pk):
        "find object by primary key"
        rs = await select("%s where `%s`=?" % (cls.__select__, cls.__primary_key__),[pk],1)
        if len(rs) == 0:
            return None
            # 类似[('2', 'Michael')] ? 但这里数据库返回的列表的元素是字典
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warning('failed to insert record: affected rows: %s' % rows)

    async def update(self):
        args = list(map(self.getValue,self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warning('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__,args)
        if rows != 1:
            logging.warning('failed to remove by primary key: affected rows: %s' % rows)


    # @classmethod
    # def create_tables_sql(cls):
    #     """根据models生成sql脚本"""
    #     sql = []
    #
    #     # todo
    #
    #     with open("schema.sql","a",encoding="utf-8") as f:
    #         f.write("".join(sql))

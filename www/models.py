import time, uuid

from www.orm import Model, StringField, BoolanField, FloatField, TextField

def next_id():
    return "%015d%s000" % (int(time.time() * 1000),uuid.uuid4().hex)
#print(next_id())


class User(Model):
    __table__ = "users"

    id = StringField(primary_key=True,default=next_id,ddl="varchar(50)")
    email = StringField(ddl="varchar(50)")
    passwd = StringField(ddl="varchar(50)")
    admin = BoolanField()
    name = StringField(ddl="varchar(50)")
    image = StringField(ddl="varchar(500)")
    created_at = FloatField(default=time.time)


class Blog(Model):
    __table__ = 'blogs'

    id = StringField(name='id', primary_key=True,default=next_id,ddl="varchar(50)")
    user_id = StringField(name='user_id',ddl="varchar(50)")
    user_name = StringField(name='user_name', ddl="varchar(50)")
    user_image = StringField(name='user_image', ddl="varchar(500)")
    name = StringField(name='name', ddl="varchar(50)")
    summary = StringField(name='summary', ddl="varchar(200)")
    content = TextField(name='content')
    created_at = FloatField(name='created_at', default=time.time)


class Comment(Model):
    __table__ = "comments"

    id = StringField(primary_key=True, default=next_id, ddl="varchar(50)")
    blog_id = StringField(ddl="varchar(50)")
    user_id = StringField(ddl="varchar(50)")
    user_name = StringField(ddl="varchar(50)")
    user_image = StringField(ddl="varchar(500)")
    content = TextField()
    created_at = FloatField(default=time.time)




import datetime
import json
import sqlite3

import C
import poster
import R
import store

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Text, Date


engine = create_engine(C.DSN, echo=True)


Base = declarative_base()


Session = sessionmaker(bind=engine)


session = Session()


def db_init():
    try:
        Base.metadata.create_all(bind=engine)
        print("init tables success")
    except Exception as e:
        print("init tables except : ", e)

"""
    'CREATE TABLE posters (id integer NOT NULL PRIMARY KEY AUTOINCREMENT, code text, name text, preview text, json text, create_time date, update_time date, status integer)',
    'CREATE TABLE links (id integer NOT NULL PRIMARY KEY AUTOINCREMENT, code text, pid integer, params text, create_time date)',
"""


class Posters(Base):
    __tablename__ = 'posters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text)
    name = Column(Text)
    preview = Column(Text)
    json = Column(Text)
    create_time = Column(Date)
    update_time = Column(Date)
    status = Column(Integer)


class Links(Base):
    __tablename__ = 'links'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text)
    pid = Column(Integer)
    params = Column(Text)
    create_time = Column(Date)



def db_save_poster(code: str, name: str, preview: str, json: str):
    params = [code, name, preview, json, now_str(), int(C.STATUS_NORMAL)]
    session.execute("insert into posters (code, name, preview, json, create_time, status) values (?, ?, ?, ?, ?, ?)",params)


def db_update_poster(id: int, code: str, name: str, preview: str, json: str):
    params = (code, name, preview, json, now_str(), id)
    session.execute("update posters set code=%s,name=%s,preview=%s,json=%s,update_time=%s where id='%s'" % params)


def db_delete_poster(id: int):
    params = (C.STATUS_DELETE, id)
    session.execute("update posters set status=%s where id='%s'" % params)


def db_save_share(code, poster_id, param):
    params = (code, poster_id, param, now_str())
    session.execute("insert into links (code, pid, params, create_time) values (%s, %s, %s, %s)" %params)


def query_user_posters():
    r = session.execute('select * from posters where status=1 order by id desc')
    posters = []
    for row in r:
        posters.append({
                'id': row[0],
                'code': row[1],
                'name': row[2],
                'preview': row[3],
                'json': row[4],
                'create_time': row[5],
                'update_time': row[6],
                # 'status': row[7],
            })
    return posters


def query_user_poster(poster_id: int):
    r = session.execute('select * from posters where id = "%s" limit 1;'%poster_id)
    row = r.fetchone()
    if row is not None:
        return {
                'id': row[0],
                'code': row[1],
                'name': row[2],
                'preview': row[3],
                'json': row[4],
                'create_time': row[5],
                'update_time': row[6],
                'status': row[7],
            }
    return None


def query_user_share(code: str):
    r = session.execute('select * from links where code = "%s" limit 1;' %code)
    row = r.fetchone()
    if row is not None:
        return {
                'id': row[0],
                'code': row[1],
                'pid': row[2],
                'params': row[3],
                'create_time': row[4],
            }
    return None


def now_str(days=0):
    return (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')


def save_user_poster(data, pd):
    code = C.code(16)
    name = data['name']
    buf, mimetype = poster.drawio(pd, 0.4)
    path = store.save(buf.getvalue(), f"a.{pd['type']}", 'preview')
    return db_save_poster(code, name, path, data['json'])


def update_user_poster(data, pd, id):
    code = data.get('code', C.code(16))
    name = data['name']
    buf, mimetype = poster.drawio(pd, 0.4)
    path = store.save(buf.getvalue(), f"a.{pd['type']}", 'preview')
    return db_update_poster(id, code, name, path, data['json'])


def save_or_update_user_poster(data):
    pd = json.loads(data['json'])
    print(pd)
    id = data.get('id', 0)
    if id == 0:
        return save_user_poster(data, pd)
    else:
        return update_user_poster(data, pd, id)


def copy_user_poster(id):
    p = query_user_poster(id)
    if p:
        return db_save_poster(p['code'], p['name'] + '-复制', p['preview'], p['json'])
    return None


def get_share_link(code, param):
    s = query_user_share(code)
    if s:
        return True
    posterId = int(param['posterId'])
    p = query_user_poster(posterId)
    if p is None:
        print('海报不存在')
        return R.error('海报不存在').json()
    db_save_share(code, posterId, json.dumps(param))
    return True


def find_share_data(code):
    s = query_user_share(code)
    if s is None:
        return None
    params = json.loads(s['params'])

    poster_id = int(params['posterId'])
    p = query_user_poster(poster_id)

    data = json.loads(p['json'])
    items = data['items']
    dic = {}
    for item in items:
        vd = item['vd']
        if vd.strip():
            dic[vd] = item
    if p is None:
        return None
    for item in params.items():
        k = item[0]
        v = item[1]
        if k == 'bgUrl':
            data['bgUrl'] = v
        if dic.get(k, None) is not None:
            dic[k]['v'] = v
    return data

import datetime
import json
import sqlite3

import C
import poster
import R
import store

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, Date


dsn = f"mysql+pymysql://{C.DB_USER}:{C.DB_PASS}@{C.DB_HOST}/{C.DB_NAME}?charset={C.DB_CHAR}"

engine = create_engine(dsn)

Session = sessionmaker(bind=engine)

Base = declarative_base()

'''
    'CREATE TABLE posters (id integer NOT NULL PRIMARY KEY AUTOINCREMENT, code text, name text, preview text, json text, create_time date, update_time date, status integer)',
    'CREATE TABLE links (id integer NOT NULL PRIMARY KEY AUTOINCREMENT, code text, pid integer, params text, create_time date)',
    'CREATE TABLE tokens (id integer NOT NULL PRIMARY KEY AUTOINCREMENT, token text, create_time date, expire_time date)',

'''

db = Session()

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



def save_poster(self, code, name, preview, json):
    try:
        items = Posters(code=code, name=name, preview=preview, json=json, create_time=now_str(),
                status=int(C.STATUS_NORMAL))
        db.add(items)
        db.commit()
    except:
        db.rollback()


def update_poster(id, code, name, preview, json):
    try:
        db.query(Posters).filter(id=id).update({Posters.code: code, Posters.name: name, Posters.preview: preview,
            Posters.json: json})
        db.commit()
    except:
        print("[*] upate exception")
        db.rollback()

def get_share_poster_link(code, param):
    ...


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

def db_update_poster(id: int, code: str, name: str, preview: str, json: str):
    with conn() as con:
        c = con.cursor()
        params = [code, name, preview, json, now_str(), id]
        c.execute("update posters set code=?,name=?,preview=?,json=?,update_time=? where id=?", params)
        con.commit()

def db_save_poster(code: str, name: str, preview: str, json: str):
    with conn() as con:
        c = con.cursor()
        params = [code, name, preview, json, now_str(), int(C.STATUS_NORMAL)]
        c.execute("insert into posters (code, name, preview, json, create_time, status) values (?, ?, ?, ?, ?, ?)",
                  params)
        con.commit()
        return c.lastrowid

def now_str(days=0):
    return (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

def init_tables():
    try:
        Base.metadata.create_all(engine)
        print("init table success")
    except:
        print("init table except")


def conn():
    return sqlite3.connect(C.STORE_DB + '/poster.sqlite')


INIT_SQL = [
    'CREATE TABLE posters (id integer NOT NULL PRIMARY KEY AUTOINCREMENT, code text, name text, preview text, json text, create_time date, update_time date, status integer)',
    'CREATE TABLE links (id integer NOT NULL PRIMARY KEY AUTOINCREMENT, code text, pid integer, params text, create_time date)',
    'CREATE TABLE tokens (id integer NOT NULL PRIMARY KEY AUTOINCREMENT, token text, create_time date, expire_time date)',
]


def db_delete_poster(id: int):
    with conn() as con:
        c = con.cursor()
        params = [C.STATUS_DELETE, id]
        c.execute("update posters set status=? where id=?", params)
        con.commit()


def db_save_share(code, poster_id, param):
    with conn() as con:
        c = con.cursor()
        params = [code, poster_id, param, now_str()]
        c.execute("insert into links (code, pid, params, create_time) values (?, ?, ?, ?)", params)
        con.commit()
        return c.lastrowid


def query_user_posters():
    with conn() as con:
        c = con.cursor()
        r = c.execute('select * from posters where status=1 order by id desc')
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
    with conn() as con:
        c = con.cursor()
        r = c.execute('select * from posters where id = ? limit 1', [poster_id])
        row = r.fetchone()
        # print(row)
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
        else:
            return None


def query_user_share(code: str):
    with conn() as con:
        c = con.cursor()
        r = c.execute('select * from links where code = ? limit 1', [code])
        row = r.fetchone()
        # print(row)
        if row is not None:
            return {
                'id': row[0],
                'code': row[1],
                'pid': row[2],
                'params': row[3],
                'create_time': row[4],
            }
        else:
            return None



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


def save_token(token):
    with conn() as con:
        c = con.cursor()
        params = [token, now_str(), now_str(days=10)]
        c.execute("insert into tokens (token, create_time, expire_time) values (?, ?, ?)", params)
        con.commit()
        return c.lastrowid


def query_token(token):
    with conn() as con:
        c = con.cursor()
        r = c.execute('select * from tokens where token = ? and expire_time >= ? limit 1', [token, now_str()])
        row = r.fetchone()
        print(row)
        return row is not None
    return None

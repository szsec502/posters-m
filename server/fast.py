import base64
import os
import re
from os.path import join, dirname

import tornado.ioloop
from tornado.web import RequestHandler, StaticFileHandler, Application

import C
import R
import dao
import json
import poster
import store


class BaseHandler(RequestHandler):

    def set_default_headers(self) -> None:
        origin_url = self.request.headers.get('Origin')
        if not origin_url:
            origin_url = '*'
        self.set_header('Access-Control-Allow-Methods', 'POST, PUT, DELETE, GET, OPTIONS')
        self.set_header('Server', 'data')
        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Allow-Origin', origin_url)
        self.set_header('Access-Control-Allow-Headers', 'x-requested-with,token,Content-type')

    def options(self):
        self.set_status(200)  # 这里的状态码一定要设置200
        self.finish()
        print('options')

    def check_token(self):
        ...

    def json(self, r: R):
        self.set_header('Content-Type', 'application/json;charset=UTF-8')
        self.write(r.json())


class ApiLinkHandler(BaseHandler):

    def post(self):
        print("body---", self.request.body)
        param = json.loads(self.request.body)
        # TODO: use http's Authorization header
        code = C.md5(param, 16)
        if dao.get_share_link(code, param):
            url = f"http://0.0.0.0:5000/v/{code}".replace('//v', '/v')
            self.json(R.ok().add('url', url))
        else:
            self.json(R.error(f'the poster [{param["posterId"]}] not exits.'))



class MyStaticFileHandler(StaticFileHandler, BaseHandler):
    pass


def make_app(p):
    settings = {
        'debug': True
    }
    return Application([
        (f"{p}api/link", ApiLinkHandler),
        (f'{p}(store/.*)$', StaticFileHandler, {"path": join(dirname(__file__), "data")}),
        (f'{p}resource/(.*)$', MyStaticFileHandler, {"path": join(dirname(__file__), "resource")}),

    ], **settings)


def run_app():
    banner = '''
      __              _                       _               
     / _|            | |                     | |              
    | |_   __ _  ___ | |_  _ __    ___   ___ | |_   ___  _ __ 
    |  _| / _` |/ __|| __|| '_ \  / _ \ / __|| __| / _ \| '__|
    | |  | (_| |\__ \| |_ | |_) || (_) |\__ \| |_ |  __/| |   
    |_|   \__,_||___/ \__|| .__/  \___/ |___/ \__| \___||_|   
                          | |                                 
                          |_|                                 
                                        fastposter(v2.6.2)     
                                 https://poster.prodapi.cn/docs/   
                                                                '''
    PORT = 5000
    print(banner)
    uri = os.environ.get('POSTER_URI_PREFIX', f'http://0.0.0.0:{PORT}/')
    print(f'Listening at {uri}\n')
    g = re.search(r'http[s]?://.*?(/.*)', uri)
    web_context_path = '/' if not g else g.group(1)
    app = make_app(web_context_path)
    app.listen(port=PORT, address='0.0.0.0')
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    try:
        run_app()
    except KeyboardInterrupt:
        print("[*] shutdown the server app ...")
        exit(0)

import json
from datetime import timedelta
from robot import config
import tornado.web
import tornado.ioloop
from tornado import gen
import tornado.httpserver
import tornado.options
import hashlib
import threading
import logging
import asyncio

from tornado.websocket import WebSocketHandler


logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

conversation = None

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")


class MainHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        global conversation
        if not self.current_user:
            self.redirect("/login")
            return
        if conversation:
            self.render('index.html', history=conversation.getHistory())
        else:
            self.render('index.html', history=[])
        
class HistoryHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        global conversation
        if not self.current_user:
            res = {'code': 1, 'message': 'illegal visit'};
            self.write(json.dumps(res))
        else:
            res = {'code': 0, 'message': json.dumps(conversation.getHistory())}
            self.write(json.dumps(res));
        self.finish()

        
class LoginHandler(BaseHandler):
    
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        self.render('login.html', error=None)

    def post(self):
        if self.get_argument('username') == config.get('/server/username') and \
           hashlib.md5(self.get_argument('password').encode('utf-8')).hexdigest() \
           == config.get('/server/validate'):
            self.set_secure_cookie("username", self.get_argument("username"))
            self.redirect("/")
        else:
            self.render('login.html', error="登录失败")


class LogoutHandler(BaseHandler):
    
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        self.set_secure_cookie("username", '')
        self.redirect("/login")


settings = {
    "cookie_secret" : b'*\xc4bZv0\xd7\xf9\xb2\x8e\xff\xbcL\x1c\xfa\xfeh\xe1\xb8\xdb\xd1y_\x1a',
    "template_path": "server/templates",
    "static_path": "server/static",
    "debug": True
}

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/login", LoginHandler),
    (r"/history", HistoryHandler),
    (r"/logout", LogoutHandler),
], **settings)


def start_server(con):
    global conversation
    conversation = con
    if config.get('/server/enable', False):
        host = config.get('/server/host', '0.0.0.0')
        port = config.get('/server/port', '5000')
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            application.listen(int(port))
            tornado.ioloop.IOLoop.instance().start()
        except Exception as e:
            logger.critical('服务器启动失败: {}'.format(e))
        

def run(conversation):
    t = threading.Thread(target=lambda: start_server(conversation))
    t.start()

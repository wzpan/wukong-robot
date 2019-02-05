import json
from datetime import timedelta
from robot import config
import tornado.web
import tornado.ioloop
from tornado import gen
import hashlib
import threading
import logging
import asyncio

logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

class MainHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        self.render('index.html')
        
        
class LoginHandler(BaseHandler):
    
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        self.render('login.html')

    def post(self):
        if self.get_argument('username') == config.get('/server/username') and \
           hashlib.md5(self.get_argument('password').encode('utf-8')).hexdigest() \
           == config.get('/server/validate'):
            self.set_secure_cookie("username", self.get_argument("username"))
            self.redirect("/")

settings = {
    "cookie_secret" : b'*\xc4bZv0\xd7\xf9\xb2\x8e\xff\xbcL\x1c\xfa\xfeh\xe1\xb8\xdb\xd1y_\x1a',
    "template_path": "server/templates",
    "static_path": "server/static"
}

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/login", LoginHandler),
], **settings)


def start_server():
    if config.get('/server/enable', False):
        host = config.get('/server/host', '0.0.0.0')
        port = config.get('/server/port', '5000')
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            application.listen(int(port))
            tornado.ioloop.IOLoop.instance().start()
        except Exception as e:
            logger.critical('服务器启动失败: {}'.format(e))
        

def run():
    t = threading.Thread(target=start_server)
    t.start()

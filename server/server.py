import json
from robot import config, utils, logging, constants, Updater
import base64
import requests
import tornado.web
import tornado.ioloop
from tornado import gen
import tornado.httpserver
import tornado.options
import hashlib
import threading
import asyncio
import subprocess
import os
import time
import yaml
import markdown
import random

logger = logging.getLogger(__name__)

conversation, wukong = None, None

suggestions = [
    '现在几点',
    '你吃饭了吗',
    '上海的天气',
    '写一首关于大海的诗',
    '来玩成语接龙',
    '我有多少邮件',
    '你叫什么名字',
    '讲个笑话'
]

class BaseHandler(tornado.web.RequestHandler):
    def isValidated(self):
        return self.get_cookie("validation") == config.get('/server/validate', '')
    def validate(self, validation):
        return validation == config.get('/server/validate', '')


class MainHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        global conversation, wukong, suggestions
        if not self.isValidated():
            self.redirect("/login")
            return
        if conversation:
            info = Updater.fetch(wukong._dev)
            suggestion = random.choice(suggestions)
            notices = None
            if 'notices' in info:
                notices=info['notices']
            self.render('index.html', history=conversation.getHistory(), update_info=info, suggestion=suggestion, notices=notices)
        else:
            self.render('index.html', history=[])

class ChatHandler(BaseHandler):

    def onResp(self, msg):
        logger.debug('response msg: {}'.format(msg))
        res = {'code': 0, 'message': 'ok', 'resp': msg}
        self.write(json.dumps(res))

    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        global conversation        
        if self.validate(self.get_argument('validate')):
            if self.get_argument('type') == 'text':
                query = self.get_argument('query')
                uuid = self.get_argument('uuid')
                conversation.doResponse(query, uuid, onSay=lambda msg: self.onResp(msg))
                
            elif self.get_argument('type') == 'voice':
                voice_data = self.get_argument('voice')
                tmpfile = utils.write_temp_file(base64.b64decode(voice_data), '.wav')
                fname, suffix = os.path.splitext(tmpfile)
                nfile = fname + '-16k' + suffix
                # downsampling
                soxCall = 'sox ' + tmpfile + \
                          ' ' + nfile + ' rate 16k'
                subprocess.call([soxCall], shell=True, close_fds=True)
                utils.check_and_delete(tmpfile)
                conversation.doConverse(nfile, onSay=lambda msg: self.onResp(msg))
            else:
                res = {'code': 1, 'message': 'illegal type'}
                self.write(json.dumps(res))
        else:
            res = {'code': 1, 'message': 'illegal visit'}
            self.write(json.dumps(res))
        self.finish()
        
        
class GetHistoryHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        global conversation
        if not self.validate(self.get_argument('validate')):
            res = {'code': 1, 'message': 'illegal visit'}
            self.write(json.dumps(res))
        else:
            res = {'code': 0, 'message': 'ok', 'history': json.dumps(conversation.getHistory())}
            self.write(json.dumps(res))
        self.finish()


class GetConfigHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if not self.validate(self.get_argument('validate')):
            res = {'code': 1, 'message': 'illegal visit'}
            self.write(json.dumps(res))
        else:
            key = self.get_argument("key", default="")
            res = ''
            if key == '':
                res = {'code': 0, 'message': 'ok', 'config': config.getText(), 'sensitivity': config.get('sensitivity', 0.5)}
            else:
                res = {'code': 0, 'message': 'ok', 'value': config.get(key)}
            self.write(json.dumps(res))
        self.finish()


class GetLogHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if not self.validate(self.get_argument('validate')):
            res = {'code': 1, 'message': 'illegal visit'}
            self.write(json.dumps(res))
        else:
            lines = self.get_argument('lines', default=200)
            res = {'code': 0, 'message': 'ok', 'log': logging.readLog(lines)}
            self.write(json.dumps(res))
        self.finish()


class LogHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            self.render("log.html")


class OperateHandler(BaseHandler):

    def post(self):
        global wukong
        if self.validate(self.get_argument('validate')):
            if self.get_argument('type') == 'restart':
                res = {'code': 0, 'message': 'ok'}
                self.write(json.dumps(res))
                self.finish()
                time.sleep(3)
                wukong.restart()
            else:
                res = {'code': 1, 'message': 'illegal type'}
                self.write(json.dumps(res))
                self.finish()
        else:
            res = {'code': 1, 'message': 'illegal visit'}
            self.write(json.dumps(res))
            self.finish()

class ConfigHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            self.render('config.html', sensitivity=config.get('sensitivity'))

    def post(self):
        global conversation        
        if self.validate(self.get_argument('validate')):            
            configStr = self.get_argument('config')
            try:
                yaml.load(configStr)
                config.dump(configStr)
                res = {'code': 0, 'message': 'ok'}
                self.write(json.dumps(res))
            except:
                res = {'code': 1, 'message': 'YAML解析失败，请检查内容'}
                self.write(json.dumps(res))
        else:
            res = {'code': 1, 'message': 'illegal visit'}
            self.write(json.dumps(res))
        self.finish()


class DonateHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
            return
        r = requests.get('https://raw.githubusercontent.com/wzpan/wukong-contrib/master/docs/donate.md')
        content = markdown.markdown(r.text, extensions=['codehilite',
                                               'tables',
                                               'fenced_code',
                                               'meta',
                                               'nl2br',
                                               'toc'
        ])
        self.render('donate.html', content=content)        

    

class APIHandler(BaseHandler):
    
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if not self.isValidated():
            self.redirect("/login")
        else:
            content = ''
            with open(os.path.join(constants.TEMPLATE_PATH, "api.md"), 'r') as f:
                content = f.read()
            content = markdown.markdown(content, extensions=['codehilite',
                                               'tables',
                                               'fenced_code',
                                               'meta',
                                               'nl2br',
                                               'toc'
            ])
            self.render('api.html', content=content)


class UpdateHandler(BaseHandler):
    
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        global wukong
        if self.validate(self.get_argument('validate')):            
            if wukong.update():
                res = {'code': 0, 'message': 'ok'}
                self.write(json.dumps(res))
                self.finish()
                time.sleep(3)
                wukong.restart()
            else:
                res = {'code': 1, 'message': '更新失败，请手动更新'}
                self.write(json.dumps(res))
        else:
            res = {'code': 1, 'message': 'illegal visit'}
            self.write(json.dumps(res))
        self.finish()
    
        
class LoginHandler(BaseHandler):
    
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if self.isValidated():
            self.redirect('/')
        else:
            self.render('login.html', error=None)

    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        if self.get_argument('username') == config.get('/server/username') and \
           hashlib.md5(self.get_argument('password').encode('utf-8')).hexdigest() \
           == config.get('/server/validate'):
            self.set_cookie("validation", config.get('/server/validate'))
            self.redirect("/")
        else:
            self.render('login.html', error="登录失败")


class LogoutHandler(BaseHandler):
    
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if self.isValidated():
            self.set_cookie("validation", '')
        self.redirect("/login")


settings = {
    "cookie_secret" : b'*\xc4bZv0\xd7\xf9\xb2\x8e\xff\xbcL\x1c\xfa\xfeh\xe1\xb8\xdb\xd1y_\x1a',
    "template_path": "server/templates",
    "static_path": "server/static",
    "debug": False
}

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/login", LoginHandler),
    (r"/gethistory", GetHistoryHandler),
    (r"/chat", ChatHandler),
    (r"/config", ConfigHandler),
    (r"/getconfig", GetConfigHandler),
    (r"/operate", OperateHandler),
    (r"/getlog", GetLogHandler),
    (r"/log", LogHandler),
    (r"/logout", LogoutHandler),
    (r"/api", APIHandler),
    (r"/upgrade", UpdateHandler),
    (r"/donate", DonateHandler)
], **settings)


def start_server(con, wk):
    global conversation, wukong
    conversation = con
    wukong = wk
    if config.get('/server/enable', False):
        port = config.get('/server/port', '5000')
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            application.listen(int(port))
            tornado.ioloop.IOLoop.instance().start()
        except Exception as e:
            logger.critical('服务器启动失败: {}'.format(e))
        

def run(conversation, wukong):
    t = threading.Thread(target=lambda: start_server(conversation, wukong))
    t.start()

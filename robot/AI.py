# -*- coding: utf-8-*-
import requests
import json
from robot import logging
from robot import config
from uuid import getnode as get_mac
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)

class AbstractRobot(object):

    __metaclass__ = ABCMeta

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def chat(self, texts):
        pass


class TulingRobot(AbstractRobot):

    SLUG = "tuling"

    def __init__(self, tuling_key):
        """
        图灵机器人
        """
        super(self.__class__, self).__init__()
        self.tuling_key = tuling_key

    @classmethod
    def get_config(cls):
        # Try to get ali_yuyin config from config
        return config.get('tuling', {})

    def chat(self, texts):
        """
        使用图灵机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = ''.join(texts)
        try:
            url = "http://www.tuling123.com/openapi/api"
            userid = str(get_mac())[:32]
            body = {'key': self.tuling_key, 'info': msg, 'userid': userid}
            r = requests.post(url, data=body)
            respond = json.loads(r.text)
            result = ''
            if respond['code'] == 100000:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            elif respond['code'] == 200000:
                result = respond['url']
            elif respond['code'] == 302000:
                for k in respond['list']:
                    result = result + u"【" + k['source'] + u"】 " +\
                        k['article'] + "\t" + k['detailurl'] + "\n"
            else:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            logger.info('{} 回答：{}'.format(self.SLUG, result))
            return result
        except Exception:
            logger.critical("Tuling robot failed to responsed for %r",
                                  msg, exc_info=True)            
            return "抱歉, 我的大脑短路了，请稍后再试试."


class Emotibot(AbstractRobot):

    SLUG = "emotibot"

    def __init__(self, appid, location, more):
        """
        Emotibot机器人
        """
        super(self.__class__, self).__init__()        
        self.appid, self.location, self.more = appid, location, more

    @classmethod
    def get_config(self):
        appid = config.get('/emotibot/appid', '')
        location = config.get('location', '深圳')
        more = config.get('active_mode', False)        
        return {
            'appid': appid,
            'location': location,
            'more': more
        }

    def chat(self, texts):
        """
        使用Emotibot机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = ''.join(texts)
        try:
            url = "http://idc.emotibot.com/api/ApiKey/openapi.php"
            userid = str(get_mac())[:32]
            register_data = {
                "cmd": "chat",
                "appid": self.appid,
                "userid": userid,
                "text": msg,
                "location": self.location
            }
            r = requests.post(url, params=register_data)
            jsondata = json.loads(r.text)
            result = ''
            responds = []
            if jsondata['return'] == 0:
                if self.more:
                    datas = jsondata.get('data')
                    for data in datas:
                        if data.get('type') == 'text':
                            responds.append(data.get('value'))
                else:
                    responds.append(jsondata.get('data')[0].get('value'))
                result = '\n'.join(responds)
            else:
                result = "抱歉, 我的大脑短路了，请稍后再试试."
            logger.info('{} 回答：{}'.format(self.SLUG, result))            
            return result
        except Exception:
            logger.critical("Emotibot failed to responsed for %r",
                                  msg, exc_info=True)
            return "抱歉, 我的大脑短路了，请稍后再试试."




def get_robot_by_slug(slug):
    """
    Returns:
        A robot implementation available on the current platform
    """
    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_robots = list(filter(lambda robot: hasattr(robot, "SLUG") and
                             robot.SLUG == slug, get_robots()))
    if len(selected_robots) == 0:
        raise ValueError("No robot found for slug '%s'" % slug)
    else:
        if len(selected_robots) > 1:
            logger.warning("WARNING: Multiple robots found for slug '%s'. " +
                  "This is most certainly a bug." % slug)        
        robot = selected_robots[0]
        logger.info("使用 {} 对话机器人".format(robot.SLUG))
        return robot.get_instance()


def get_robots():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses
    return [robot for robot in
            list(get_subclasses(AbstractRobot))
            if hasattr(robot, 'SLUG') and robot.SLUG]

# -*- coding: utf-8 -*-
import json
import random
import requests
from uuid import getnode as get_mac
from abc import ABCMeta, abstractmethod
from robot import logging, config, utils

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
        return config.get("tuling", {})

    def chat(self, texts):
        """
        使用图灵机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        try:
            url = "http://www.tuling123.com/openapi/api"
            userid = str(get_mac())[:32]
            body = {"key": self.tuling_key, "info": msg, "userid": userid}
            r = requests.post(url, data=body)
            respond = json.loads(r.text)
            result = ""
            if respond["code"] == 100000:
                result = respond["text"].replace("<br>", "  ")
                result = result.replace(u"\xa0", u" ")
            elif respond["code"] == 200000:
                result = respond["url"]
            elif respond["code"] == 302000:
                for k in respond["list"]:
                    result = (
                        result
                        + u"【"
                        + k["source"]
                        + u"】 "
                        + k["article"]
                        + "\t"
                        + k["detailurl"]
                        + "\n"
                    )
            else:
                result = respond["text"].replace("<br>", "  ")
                result = result.replace(u"\xa0", u" ")
            logger.info("{} 回答：{}".format(self.SLUG, result))
            return result
        except Exception:
            logger.critical(
                "Tuling robot failed to response for %r", msg, exc_info=True
            )
            return "抱歉, 我的大脑短路了，请稍后再试试."


class Emotibot(AbstractRobot):
    """
    Emotibot 机器人对话服务，已废弃
    """

    SLUG = "emotibot"

    def __init__(self, appid, location, more):
        """
        Emotibot机器人
        """
        super(self.__class__, self).__init__()
        self.appid, self.location, self.more = appid, location, more

    @classmethod
    def get_config(self):
        appid = config.get("/emotibot/appid", "")
        location = config.get("location", "深圳")
        more = config.get("active_mode", False)
        return {"appid": appid, "location": location, "more": more}

    def chat(self, texts):
        """
        使用Emotibot机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        try:
            url = "http://idc.emotibot.com/api/ApiKey/openapi.php"
            userid = str(get_mac())[:32]
            register_data = {
                "cmd": "chat",
                "appid": self.appid,
                "userid": userid,
                "text": msg,
                "location": self.location,
            }
            r = requests.post(url, params=register_data)
            jsondata = json.loads(r.text)
            result = ""
            responds = []
            if jsondata["return"] == 0:
                if self.more:
                    datas = jsondata.get("data")
                    for data in datas:
                        if data.get("type") == "text":
                            responds.append(data.get("value"))
                else:
                    responds.append(jsondata.get("data")[0].get("value"))
                result = "\n".join(responds)
            else:
                result = "抱歉, 我的大脑短路了，请稍后再试试."
            logger.info("{} 回答：{}".format(self.SLUG, result))
            return result
        except Exception:
            logger.critical("Emotibot failed to response for %r", msg, exc_info=True)
            return "抱歉, 我的大脑短路了，请稍后再试试."


class AnyQRobot(AbstractRobot):

    SLUG = "anyq"

    def __init__(self, host, port, solr_port, threshold, secondary):
        """
        AnyQ机器人
        """
        super(self.__class__, self).__init__()
        self.host = host
        self.threshold = threshold
        self.port = port
        self.secondary = secondary

    @classmethod
    def get_config(cls):
        # Try to get anyq config from config
        return config.get("anyq", {})

    def chat(self, texts):
        """
        使用AnyQ机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        try:
            url = "http://{}:{}/anyq?question={}".format(self.host, self.port, msg)
            r = requests.get(url)
            respond = json.loads(r.text)
            logger.info("anyq response: {}".format(respond))
            if len(respond) > 0:
                # 有命中，进一步判断 confidence 是否达到要求
                confidence = respond[0]["confidence"]
                if confidence >= self.threshold:
                    # 命中该问题，返回回答
                    answer = respond[0]["answer"]
                    if utils.validjson(answer):
                        answer = random.choice(json.loads(answer))
                    logger.info("{} 回答：{}".format(self.SLUG, answer))
                    return answer
            # 没有命中，走兜底
            if self.secondary != "null" and self.secondary is not None:
                try:
                    ai = get_robot_by_slug(self.secondary)
                    return ai.chat(texts)
                except Exception:
                    logger.critical(
                        "Secondary robot {} failed to response for {}".format(
                            self.secondary, msg
                        )
                    )
                    return get_unknown_response()
            else:
                return get_unknown_response()
        except Exception:
            logger.critical("AnyQ robot failed to response for %r", msg, exc_info=True)
            return "抱歉, 我的大脑短路了，请稍后再试试."


def get_unknown_response():
    """
    不知道怎么回答的情况下的答复

    :returns: 表示不知道的答复
    """
    results = ["抱歉，我不会这个呢", "我不会这个呢", "我还不会这个呢", "我还没学会这个呢", "对不起，你说的这个，我还不会"]
    return random.choice(results)


def get_robot_by_slug(slug):
    """
    Returns:
        A robot implementation available on the current platform
    """
    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_robots = list(
        filter(
            lambda robot: hasattr(robot, "SLUG") and robot.SLUG == slug, get_robots()
        )
    )
    if len(selected_robots) == 0:
        raise ValueError("No robot found for slug '%s'" % slug)
    else:
        if len(selected_robots) > 1:
            logger.warning(
                "WARNING: Multiple robots found for slug '%s'. "
                + "This is most certainly a bug." % slug
            )
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

    return [
        robot
        for robot in list(get_subclasses(AbstractRobot))
        if hasattr(robot, "SLUG") and robot.SLUG
    ]

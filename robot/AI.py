# -*- coding: utf-8 -*-
import json
import random
import requests

from uuid import getnode as get_mac
from abc import ABCMeta, abstractmethod
from robot import logging, config, utils
from robot.sdk import unit

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
    def chat(self, texts, parsed):
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
        return config.get("tuling", {})

    def chat(self, texts, parsed=None):
        """
        使用图灵机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        try:
            url = "http://openapi.turingapi.com/openapi/api/v2"
            userid = str(get_mac())[:32]
            body = {
                "perception": {"inputText": {"text": msg}},
                "userInfo": {"apiKey": self.tuling_key, "userId": userid},
            }
            r = requests.post(url, json=body)
            respond = json.loads(r.text)
            result = ""
            if "results" in respond:
                for res in respond["results"]:
                    result += "\n".join(res["values"].values())
            else:
                result = "图灵机器人服务异常，请联系作者"
            logger.info("{} 回答：{}".format(self.SLUG, result))
            return result
        except Exception:
            logger.critical(
                "Tuling robot failed to response for %r", msg, exc_info=True
            )
            return "抱歉, 我的大脑短路了，请稍后再试试."


class UnitRobot(AbstractRobot):

    SLUG = "unit"

    def __init__(self):
        """
        百度UNIT机器人
        """
        super(self.__class__, self).__init__()

    @classmethod
    def get_config(cls):
        return {}

    def chat(self, texts, parsed):
        """
        使用百度UNIT机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        intents = [
            "USER_AQI",
            "USER_CLOTHES",
            "USER_CLOUDY",
            "USER_EXERCISE",
            "USER_FOG",
            "USER_HIGH_TEMP",
            "USER_INFLUENZA",
            "USER_LOW_TEMP",
            "USER_RAIN",
            "USER_SNOW",
            "USER_SUNNY",
            "USER_TEMP",
            "USER_TRIP",
            "USER_ULTRAVIOLET",
            "USER_WASH_CAR",
            "USER_WEATHER",
            "USER_WIND",
        ]
        try:
            for intent in intents:
                if unit.hasIntent(parsed, intent):
                    return unit.getSay(parsed, intent)
            return unit.getSay(parsed, "BUILT_CHAT")
        except Exception:
            logger.critical("UNIT robot failed to response for %r", msg, exc_info=True)
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

    def chat(self, texts, parsed):
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
            if self.secondary != "null" and self.secondary:
                try:
                    ai = get_robot_by_slug(self.secondary)
                    return ai.chat(texts, parsed)
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


class OPENAIRobot(AbstractRobot):

    SLUG = "openai"

    def __init__(self, openai_api_key, model, 
                 temperature, max_tokens, 
                 top_p, frequency_penalty, 
                 presence_penalty, stop_ai):
        """
        OpenAI机器人
        openai.api_key = os.getenv("OPENAI_API_KEY")
        """
        super(self.__class__, self).__init__()
        self.openai_api_key = openai_api_key
        try:
            import openai
        except Exception:
            logger.critical('OpenAI 初始化失败，请确认 Python 版本 ')
        openai.api_key=self.openai_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop_ai = stop_ai

    @classmethod
    def get_config(cls):
        # Try to get anyq config from config
        return config.get("openai", {})

    def chat(self, texts, parsed):
        """
        使用OpenAI机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        try:
            response = openai.Completion.create(
            model=self.model,
            prompt=msg,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop=self.stop_ai
            )
            #print(response)
            respond = response.choices[0].text
            logger.info("openai response: {}".format(respond))
            return respond
            
        except Exception:
            logger.critical("openai robot failed to response for %r", msg, exc_info=True)
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

# -*- coding: utf-8 -*-
from .sdk import unit
from robot import logging
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)


class AbstractNLU(object):
    """
    Generic parent class for all NLU engines
    """

    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    @abstractmethod
    def parse(self, query, **args):
        """
        进行 NLU 解析

        :param query: 用户的指令字符串
        :param **args: 可选的参数
        """
        return None

    @abstractmethod
    def getIntent(self, parsed):
        """ 
        提取意图

        :param parsed: 解析结果
        :returns: 意图数组
        """
        return None

    @abstractmethod
    def hasIntent(self, parsed, intent):
        """ 
        判断是否包含某个意图

        :param parsed: 解析结果
        :param intent: 意图的名称
        :returns: True: 包含; False: 不包含
        """
        return False

    @abstractmethod
    def getSlots(self, parsed, intent):
        """ 
        提取某个意图的所有词槽
    
        :param parsed: 解析结果
        :param intent: 意图的名称
        :returns: 词槽列表。你可以通过 name 属性筛选词槽，
        再通过 normalized_word 属性取出相应的值
        """
        return None

    @abstractmethod
    def getSlotWords(self, parsed, intent, name):
        """ 
        找出命中某个词槽的内容
    
        :param parsed: 解析结果
        :param intent: 意图的名称
        :param name: 词槽名
        :returns: 命中该词槽的值的列表。
        """
        return None

    @abstractmethod
    def getSay(self, parsed, intent):
        """
        提取回复文本

        :param parsed: 解析结果
        :param intent: 意图的名称
        :returns: 回复文本
        """
        return ""


class UnitNLU(AbstractNLU):
    """
    百度UNIT的NLU API.
    """

    SLUG = "unit"

    def __init__(self):
        super(self.__class__, self).__init__()

    @classmethod
    def get_config(cls):
        """
        百度UNIT的配置

        无需配置，所以返回 {}
        """
        return {}

    def parse(self, query, **args):
        """
        使用百度 UNIT 进行 NLU 解析

        :param query: 用户的指令字符串
        :param **args: UNIT 的相关参数
            - service_id: UNIT 的 service_id
            - api_key: UNIT apk_key
            - secret_key: UNIT secret_key
        :returns: UNIT 解析结果。如果解析失败，返回 None
        """
        if (
            "service_id" not in args
            or "api_key" not in args
            or "secret_key" not in args
        ):
            logger.critical("{} NLU 失败：参数错误！".format(self.SLUG))
            return None
        return unit.getUnit(
            query, args["service_id"], args["api_key"], args["secret_key"]
        )

    def getIntent(self, parsed):
        """ 
        提取意图

        :param parsed: 解析结果
        :returns: 意图数组
        """
        return unit.getIntent(parsed)

    def hasIntent(self, parsed, intent):
        """ 
        判断是否包含某个意图

        :param parsed: UNIT 解析结果
        :param intent: 意图的名称
        :returns: True: 包含; False: 不包含
        """
        return unit.hasIntent(parsed, intent)

    def getSlots(self, parsed, intent):
        """ 
        提取某个意图的所有词槽
    
        :param parsed: UNIT 解析结果
        :param intent: 意图的名称
        :returns: 词槽列表。你可以通过 name 属性筛选词槽，
        再通过 normalized_word 属性取出相应的值
        """
        return unit.getSlots(parsed, intent)

    def getSlotWords(self, parsed, intent, name):
        """ 
        找出命中某个词槽的内容
    
        :param parsed: UNIT 解析结果
        :param intent: 意图的名称
        :param name: 词槽名
        :returns: 命中该词槽的值的列表。
        """
        return unit.getSlotWords(parsed, intent, name)

    def getSay(self, parsed, intent):
        """
        提取 UNIT 的回复文本

        :param parsed: UNIT 解析结果
        :param intent: 意图的名称
        :returns: UNIT 的回复文本
        """
        return unit.getSay(parsed, intent)


def get_engine_by_slug(slug=None):
    """
    Returns:
        An NLU Engine implementation available on the current platform

    Raises:
        ValueError if no speaker implementation is supported on this platform
    """

    if not slug or type(slug) is not str:
        raise TypeError("无效的 NLU slug '%s'", slug)

    selected_engines = list(
        filter(
            lambda engine: hasattr(engine, "SLUG") and engine.SLUG == slug,
            get_engines(),
        )
    )

    if len(selected_engines) == 0:
        raise ValueError("错误：找不到名为 {} 的 NLU 引擎".format(slug))
    else:
        if len(selected_engines) > 1:
            logger.warning("注意: 有多个 NLU 名称与指定的引擎名 {} 匹配").format(slug)
        engine = selected_engines[0]
        logger.info("使用 {} NLU 引擎".format(engine.SLUG))
        return engine.get_instance()


def get_engines():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses

    return [
        engine
        for engine in list(get_subclasses(AbstractNLU))
        if hasattr(engine, "SLUG") and engine.SLUG
    ]

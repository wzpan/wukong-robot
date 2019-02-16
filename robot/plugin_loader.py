# -*- coding: utf-8-*-
import pkgutil
from . import constants
from . import config
from robot import logging
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)
_has_init = False

# plugins run at query
_plugins_query = []

def init_plugins(con):
    """
    动态加载技能插件

    参数：
    con -- 会话模块
    """

    global _has_init
    locations = [
        constants.PLUGIN_PATH,
        constants.CONTRIB_PATH,
        constants.CUSTOM_PATH
    ]
    logger.debug("检查插件目录：{}".format(locations))

    global _plugins_query
    nameSet = set()

    for finder, name, ispkg in pkgutil.walk_packages(locations):
        try:
            loader = finder.find_module(name)
            mod = loader.load_module(name)
        except Exception:
            logger.warning("插件 {} 加载出错，跳过".format(name),
                            exc_info=True)
            continue

        if not hasattr(mod, 'Plugin'):
            logger.debug("模块 {} 非插件，跳过".format(name))
            continue

        # plugins run at query
        plugin = mod.Plugin(con)

        if plugin.SLUG == 'AbstractPlugin':
            plugin.SLUG = name

        # check conflict
        if plugin.SLUG in nameSet:
            logger.warning("插件 {} SLUG({}) 重复，跳过".format(name,
                                                                 plugin.SLUG))
            continue
        nameSet.add(plugin.SLUG)

        # whether a plugin is enabled
        if config.has(plugin.SLUG) and 'enable' in config.get(plugin.SLUG):
            if not config.get(plugin.SLUG)['enable']:
                logger.info("插件 {} 已被禁用".format(name))
                continue

        if issubclass(mod.Plugin, AbstractPlugin):
            logger.info("插件 {} 加载成功 ".format(name))
            _plugins_query.append(plugin)

    def sort_priority(m):
        if hasattr(m, 'PRIORITY'):
            return m.PRIORITY
        return 0

    _plugins_query.sort(key=sort_priority, reverse=True)
    _has_init = True


def get_plugins(con):
    global _plugins_query
    _plugins_query = []
    init_plugins(con)
    return _plugins_query


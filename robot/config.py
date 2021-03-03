# -*- coding: utf-8-*-
import yaml
import logging
import os
from . import constants

logger = logging.getLogger(__name__)

_config = {}
has_init = False

def reload():
    """
    重新加载配置
    """
    logger.info('配置文件发生变更，重新加载配置文件')
    init()

def init():
    global has_init
    if os.path.isfile(constants.CONFIG_PATH):
        logger.critical("错误：{} 应该是个目录，而不应该是个文件".format(constants.CONFIG_PATH))
    if not os.path.exists(constants.CONFIG_PATH):
        os.makedirs(constants.CONFIG_PATH)
    if not os.path.exists(constants.getConfigPath()):
        yes_no = input("配置文件{}不存在，要创建吗？(y/n)".format(constants.getConfigPath()))
        if yes_no.lower() == 'y':
            constants.newConfig()
            doInit(constants.getConfigPath())
        else:
            doInit(constants.getDefaultConfigPath())
    else:
        doInit(constants.getConfigPath())
    has_init = True

def doInit(config_file=constants.getDefaultConfigPath()):
    # Create config dir if it does not exist yet
    if not os.path.exists(constants.CONFIG_PATH):
        try:
            os.makedirs(constants.CONFIG_PATH)
        except OSError:
            logger.error("Could not create config dir: '%s'",
                          constants.CONFIG_PATH, exc_info=True)
            raise

    # Check if config dir is writable
    if not os.access(constants.CONFIG_PATH, os.W_OK):
        logger.critical("Config dir %s is not writable. Dingdang " +
                         "won't work correctly.",
                         constants.CONFIG_PATH)

    global _config

    # Read config
    logger.debug("Trying to read config file: '%s'", config_file)
    try:
        with open(config_file, "r") as f:
            _config = yaml.safe_load(f)
    except Exception as e:
        logger.error("配置文件 {} 读取失败: {}".format(config_file, e))
        raise


def get_path(items, default=None, warn=False):
    global _config
    curConfig = _config
    if isinstance(items, str) and items[0] == '/':
        items = items.split('/')[1:]
    for key in items:
        if key in curConfig:
            curConfig = curConfig[key]
        else:
            if warn:
                logger.warning("/%s not specified in profile, defaulting to "
                             "'%s'", '/'.join(items), default)
            else:
                logger.debug("/%s not specified in profile, defaulting to "
                             "'%s'", '/'.join(items), default)
            return default
    return curConfig


def has_path(items):
    global _config
    curConfig = _config
    if isinstance(items, str) and items[0] == '/':
        items = items.split('/')[1:]
    else:
        items = [items]
    for key in items:
        if key in curConfig:
            curConfig = curConfig[key]
        else:
            return False
    return True


def has(item):
    """
    判断配置里是否包含某个配置项

    :param item: 配置项名
    :returns: True: 包含; False: 不包含
    """
    return has_path(item)


def get(item='', default=None, warn=False):
    """
    获取某个配置的值

    :param item: 配置项名。如果是多级配置，则以 "/a/b" 的形式提供
    :param default: 默认值（可选）
    :param warn: 不存在该配置时，是否告警
    :returns: 这个配置的值。如果没有该配置，则提供一个默认值
    """
    global has_init
    if not has_init:
        init()
    if not item:
        return _config
    if item[0] == '/':
        return get_path(item, default, warn)
    try:
        return _config[item]
    except KeyError:
        if warn:
            logger.warning("%s not specified in profile, defaulting to '%s'",
                         item, default)
        else:
            logger.debug("%s not specified in profile, defaulting to '%s'",
                         item, default)
        return default
    
def getConfig():
    """
    返回全部配置数据

    :returns: 全部配置数据（字典类型）
    """
    return _config

def getText():
    if os.path.exists(constants.getConfigPath()):
        with open(constants.getConfigPath(), 'r') as f:
            return f.read()
    return ''

def dump(configStr):
    with open(constants.getConfigPath(), 'w') as f:
        f.write(configStr)


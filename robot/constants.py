# -*- coding: utf-8-*-
import os
import shutil

# Wukong main directory
APP_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir))

LIB_PATH = os.path.join(APP_PATH, "robot")
DATA_PATH = os.path.join(APP_PATH, "static")
TEMP_PATH = os.path.join(APP_PATH, "temp")
PLUGIN_PATH = os.path.join(APP_PATH, "plugins")
DEFAULT_CONFIG_NAME = 'default.yml'
CUSTOM_CONFIG_NAME = 'config.yml'

CONFIG_PATH = os.path.expanduser(
    os.getenv('WUKONG_CONFIG', '~/.wukong')
)
CONTRIB_PATH = os.path.expanduser(
    os.getenv('WUKONG_CONFIG', '~/.wukong/contrib')
)
CUSTOM_PATH = os.path.expanduser(
    os.getenv('WUKONG_CONFIG', '~/.wukong/custom')
)

def getConfigPath():
    return os.path.join(CONFIG_PATH, CUSTOM_CONFIG_NAME)

def getConfigData(*fname):
    return os.path.join(CONFIG_PATH, *fname)

def getData(*fname):
    return os.path.join(DATA_PATH, *fname)

def getDefaultConfigPath():
    return getData(DEFAULT_CONFIG_NAME)

def newConfig():
    shutil.copyfile(getDefaultConfigPath(), getConfigPath())

def getHotwordModel(fname):
    if os.path.exists(getData(fname)):
        return getData(fname)
    else:
        return getConfigData(fname)

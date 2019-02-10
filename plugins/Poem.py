# -*- coding: utf-8-*-
# author: wzpan
# 写诗

import logging
import requests
import json
from robot import config
from robot.sdk import unit

SLUG = "poem"

logger = logging.getLogger(__name__)

def get_item(parsed):
    """ 获取位置 """
    slots = unit.getSlots(parsed)
    # 如果 query 里包含了地点，用该地名作为location
    for slot in slots:
        if slot['name'] == 'user_loc':
            return slot['normalized_word']
    # 如果不包含地点，但配置文件指定了 location，则用 location
    else:
        return config.get('location', '深圳')


def handle(text, mic, parsed):
    """
    Responds to user-input, typically speech text

    Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)        
        parsed -- NLU structure parsed by Baidu UNIT
    """

    # get config
    
    try:
        responds = unit.getSay(parsed)
        mic.say(responds, cache=True, plugin=__name__)
    except Exception as e:
        logger.error(e)
        mic.say('抱歉，写诗插件出问题了，请稍后再试', cache=True, plugin=__name__)
        
    
def isValid(text, parsed=None):
    """
        Returns True if the input is related to weather.

        Arguments:
        text -- user-input, typically transcribed speech
        parsed -- NLU structure parsed by Baidu UNIT
    """
    return unit.getIntent(parsed) == 'BUILT_POEM' and '写' in text and '诗' in text
        
        

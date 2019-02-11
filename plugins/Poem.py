# -*- coding: utf-8-*-
# author: wzpan
# 写诗

import logging
import requests
import json
from robot import config
from robot.sdk import unit

SLUG = "poem"
INTENT = "BUILT_POEM"

logger = logging.getLogger(__name__)


def handle(text, mic, parsed):
    """
    Responds to user-input, typically speech text

    Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)        
        parsed -- NLU structure parsed by Baidu UNIT
    """

    try:
        responds = unit.getSay(parsed, INTENT)
        mic.say(responds, cache=True, plugin=__name__)
    except Exception as e:
        logger.error(e)
        mic.say('抱歉，写诗插件出问题了，请稍后再试', cache=True, plugin=__name__)
        

def isValid(text, parsed=None, immersiveMode=None):
    """
        Returns True if the input is related to weather.

        Arguments:
        text -- user-input, typically transcribed speech
        parsed -- NLU structure parsed by Baidu UNIT
        immersiveMode -- current immersive mode
    """
    return unit.hasIntent(parsed, INTENT) and '写' in text and '诗' in text
        
        

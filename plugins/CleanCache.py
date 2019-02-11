# -*- coding: utf-8-*-

import os
import shutil
from robot import constants

SLUG = "cleancache"

PRIORITY = 0


def handle(text, mic, parsed=None):
    """
        Reports the current time based on the user's timezone.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)        
        parsed -- NLU structure parsed by Baidu UNIT
    """
    temp = constants.TEMP_PATH
    for f in os.listdir(temp):
        if os.path.isfile(os.path.join(temp, f)):
            os.remove(os.path.join(temp, f))
        else:
            shutil.rmtree(os.path.join(temp, f))
    mic.say(u'缓存目录已清空', cache=True, plugin=__name__)


def isValid(text, parsed=None, immersiveMode=None):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
        parsed -- NLU structure parsed by Baidu UNIT
        immersiveMode -- current immersive mode
    """
    return any(word in text.lower() for word in ["清除缓存", u"清空缓存", u"清缓存"])

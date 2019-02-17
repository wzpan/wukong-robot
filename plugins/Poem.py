# -*- coding: utf-8-*-
# author: wzpan
# 写诗

import logging
import requests
import json
from robot import config
from robot.sdk import unit
from robot.sdk.AbstractPlugin import AbstractPlugin

INTENT = "BUILT_POEM"

logger = logging.getLogger(__name__)

class Plugin(AbstractPlugin):

    SLUG = "poem"

    def handle(self, text, parsed):
        try:
            responds = unit.getSay(parsed, INTENT)
            self.say(responds, cache=True)
        except Exception as e:
            logger.error(e)
            self.say('抱歉，写诗插件出问题了，请稍后再试', cache=True)

    def isValid(self, text, parsed):
        return unit.hasIntent(parsed, INTENT) and '写' in text and '诗' in text
        
        

# -*- coding: utf-8 -*-
# author: wzpan
# 写诗

import logging
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)


class Plugin(AbstractPlugin):
    def handle(self, text, parsed):
        text = text.lower().replace("echo", "").replace(u"传话", "")
        self.say(text, cache=False)

    def isValid(self, text, parsed):
        return any(word in text.lower() for word in ["echo", u"传话"])

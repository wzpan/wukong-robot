# -*- coding: utf-8 -*-
# author: wzpan
# 闲聊一下

import logging
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)


class Plugin(AbstractPlugin):

    IS_IMMERSIVE = True

    def handle(self, text, parsed):

        if "闲聊一下" in text or "进入闲聊" in text:
            # 进入闲聊模式
            self.say("好的，已进入闲聊模式", cache=True)
        else:
            self.clearImmersive()  # 去掉沉浸式
            self.say("结束闲聊", cache=True)

    def isValid(self, text, parsed):
        return any(word in text.lower() for word in ["闲聊一下", "进入闲聊", "结束闲聊", "退出闲聊"])

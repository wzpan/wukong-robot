# -*- coding: utf-8 -*-
# author: wzpan
# 闲聊一下

import logging
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)

ENTRY_WORDS = ["进入", "打开", "激活", "开启", "一下"]
CLOSE_WORDS = ["退出", "结束", "停止"]


class Plugin(AbstractPlugin):

    IS_IMMERSIVE = True

    def handle(self, text, parsed):

        if "闲聊一下" in text or "进入闲聊" in text:
            # 进入闲聊模式
            self.say("好的，已进入闲聊模式", cache=True)
        else:
            self.clearImmersive()  # 去掉沉浸式
            self.say("结束闲聊", cache=True)

    def isValidImmersive(self, text, parsed):
        return "闲聊" in text and any(word in text for word in CLOSE_WORDS)

    def isValid(self, text, parsed):
        return "闲聊" in text and any(word in text for word in ENTRY_WORDS)

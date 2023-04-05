# -*- coding: utf-8 -*-
from robot import config, logging
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)


class Plugin(AbstractPlugin):

    IS_IMMERSIVE = True  # 这是个沉浸式技能
    SLUG = "geek"

    def __init__(self, con):
        super(Plugin, self).__init__(con)
        self.silent_count = 0

    def handle(self, text, parsed):
        if any(word in text for word in ["开启", "激活", "开始", "进入", "打开"]):
            self.silent_count = 0
            self.say(
                "进入极客模式",
                cache=True,
                onCompleted=lambda: self.onAsk(self.activeListen(silent=True)),
            )
        else:
            self.say("退出极客模式", cache=True)
            self.clearImmersive()

    def onAsk(self, input):
        if input:
            logger.debug(f"input: {input}")
            self.silent_count = 0
            self.con.doResponse(input)
        else:
            self.silent_count += 1
            if self.silent_count >= config.get("/geek/max_silent_count", 20):
                self.say("退出极客模式", cache=True)
                self.clearImmersive()
            else:
                self.onAsk(self.activeListen(silent=True))

    def restore(self):
        self.onAsk(self.activeListen(silent=True))

    def isValidImmersive(self, text, parsed):
        return (
            "模式" in text
            and any(word in text for word in ["即刻", "即可", "极客", "即客", "集团", "集客"])
            and any(word in text for word in ["退出", "结束", "停止"])
        )

    def isValid(self, text, parsed):
        return (
            "模式" in text
            and any(word in text for word in ["即刻", "即可", "即客", "集团", "极客", "集客"])
            and any(word in text for word in ["开启", "激活", "开始", "进入", "打开"])
        )

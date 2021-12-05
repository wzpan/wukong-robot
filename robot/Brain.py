# -*- coding: utf-8 -*-
import re
from robot import config
from robot import logging
from . import plugin_loader

logger = logging.getLogger(__name__)


class Brain(object):
    def __init__(self, conversation):
        """
        大脑模块，负责处理技能的匹配和响应

        参数：
        conversation -- 管理对话
        """
        self.conversation = conversation
        self.plugins = plugin_loader.get_plugins(self.conversation)
        self.handling = False

    def match(self, patterns, text):
        for pattern in patterns:
            if re.match(pattern, text):
                return True
        return False

    def isValid(self, plugin, text, parsed):
        patterns = config.get("/{}/patterns".format(plugin.SLUG), [])
        if len(patterns) > 0:
            return plugin.isValid(text, parsed) or self.match(patterns, text)
        else:
            return plugin.isValid(text, parsed)

    def isValidImmersive(self, plugin, text, parsed):
        patterns = config.get("/{}/patterns".format(plugin.SLUG), [])
        if len(patterns) > 0:
            return plugin.isValidImmersive(text, parsed) or self.match(patterns, text)
        else:
            return plugin.isValidImmersive(text, parsed)

    def isImmersive(self, plugin, text, parsed):
        return self.conversation.getImmersiveMode() == plugin.SLUG and self.isValidImmersive(
            plugin, text, parsed
        )

    def printPlugins(self):
        plugin_list = []
        for plugin in self.plugins:
            plugin_list.append(plugin.SLUG)
        logger.info("已激活插件：{}".format(plugin_list))

    def query(self, text):
        """
        query 模块

        Arguments:
        text -- 用户输入
        """

        args = {
            "service_id": config.get("/unit/service_id", "S13442"),
            "api_key": config.get("/unit/api_key", "w5v7gUV3iPGsGntcM84PtOOM"),
            "secret_key": config.get(
                "/unit/secret_key", "KffXwW6E1alcGplcabcNs63Li6GvvnfL"
            ),
        }
        parsed = self.conversation.doParse(text, **args)

        for plugin in self.plugins:
            if not self.isValid(plugin, text, parsed) and not self.isImmersive(
                plugin, text, parsed
            ):
                continue

            logger.info("'{}' 命中技能 {}".format(text, plugin.SLUG))
            self.conversation.matchPlugin = plugin.SLUG

            if plugin.IS_IMMERSIVE:
                self.conversation.setImmersiveMode(plugin.SLUG)

            continueHandle = False
            try:
                self.handling = True
                continueHandle = plugin.handle(text, parsed)
                self.handling = False
            except Exception:
                logger.critical("Failed to execute plugin", exc_info=True)
                reply = u"抱歉，插件{}出故障了，晚点再试试吧".format(plugin.SLUG)
                self.conversation.say(reply, plugin=plugin.SLUG)
            else:
                logger.debug(
                    "Handling of phrase '%s' by " + "plugin '%s' completed",
                    text,
                    plugin.SLUG,
                )
            finally:
                if not continueHandle:
                    return True

        logger.debug("No plugin was able to handle phrase {} ".format(text))
        return False

    def restore(self):
        """ 恢复某个技能的处理 """
        if not self.conversation.immersiveMode:
            return
        for plugin in self.plugins:
            if plugin.SLUG == self.conversation.immersiveMode and plugin.restore:
                plugin.restore()

    def pause(self):
        """ 暂停某个技能的处理 """
        if not self.conversation.immersiveMode:
            return
        for plugin in self.plugins:
            if plugin.SLUG == self.conversation.immersiveMode and plugin.pause:
                plugin.pause()

    def understand(self, fp):
        if self.conversation and self.conversation.asr:
            return self.conversation.asr.transcribe(fp)
        return None

    def say(self, msg, cache=False):
        if self.conversation and self.conversation.tts:
            self.conversation.tts.say(msg, cache)

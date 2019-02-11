# -*- coding: utf-8-*-
from robot import logging
from robot.sdk.unit import getUnit
from . import plugin_loader
from . import config

logger = logging.getLogger(__name__)

class Brain(object):

    def __init__(self, conversation):
        """
        Instantiates a new Brain object, which cross-references user
        input with a list of plugins. Note that the order of brain.plugins
        matters, as the Brain will cease execution on the first plugin
        that accepts a given input.

        Arguments:
        mic -- used to interact with the user (for both input and output)
        """
        self.plugins = plugin_loader.get_plugins()
        self.handling = False
        self.conversation = conversation

    def query(self, text, immersiveMode):
        """
        Passes user input to the appropriate plugin, testing it against
        each candidate plugin's isValid function.

        Arguments:
        text -- user input, typically speech, to be parsed by a plugin
        """

        parsed = getUnit(text, "S13442",
                         'w5v7gUV3iPGsGntcM84PtOOM',
                         'KffXwW6E1alcGplcabcNs63Li6GvvnfL')

        for plugin in self.plugins:
            if not plugin.isValid(text, parsed, immersiveMode):
                continue

            logger.info("'{}' 命中技能 {}".format(text, plugin.__name__))

            continueHandle = False
            try:
                self.handling = True
                continueHandle = plugin.handle(text, self.conversation, parsed)
                self.handling = False                
            except Exception:
                logger.critical('Failed to execute plugin',
                                   exc_info=True)
                reply = u"抱歉，插件{}出故障了，晚点再试试吧".format(plugin.__name__)
                self.conversation.say(reply, plugin=plugin.__name__)
            else:
                logger.debug("Handling of phrase '%s' by " +
                                   "plugin '%s' completed", text,
                                   plugin.__name__)                    
            finally:
                if not continueHandle:
                    return True

        logger.debug("No plugin was able to handle phrase {} ".format(text))
        return False

    def restore(self, slug):
        """ 恢复某个技能的处理 """
        for plugin in self.plugins:
            if plugin.SLUG == slug and plugin.restore:
                plugin.restore()

    def understand(self, fp):
        if self.conversation and self.conversation.asr:
            return self.conversation.asr.transcribe(fp)
        return None

    def say(self, msg, cache=False):
        if self.conversation and self.conversation.tts:
            self.conversation.tts.say(msg, cache)

    
            

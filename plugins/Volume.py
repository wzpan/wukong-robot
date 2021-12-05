# -*- coding: utf-8 -*-
from robot.Player import MusicPlayer
from robot import logging
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)


class Plugin(AbstractPlugin):
    def __init__(self, con):
        super(Plugin, self).__init__(con)
        self.player = None

    def handle(self, text, parsed):
        if not self.player:
            self.player = MusicPlayer([], self)
        if self.nlu.hasIntent(parsed, "CHANGE_VOL"):
            slots = self.nlu.getSlots(parsed, "CHANGE_VOL")
            for slot in slots:
                if slot["name"] == "user_d":
                    word = self.nlu.getSlotWords(parsed, "CHANGE_VOL", "user_d")[0]
                    if word == "--HIGHER--":
                        self.player.turnUp()
                        self.say("好的", cache=True)
                    else:
                        self.player.turnDown()
                        self.say("好的", cache=True)
                    return
                elif slot["name"] == "user_vd":
                    word = self.nlu.getSlotWords(parsed, "CHANGE_VOL", "user_vd")[0]
                    if word == "--LOUDER--":
                        self.player.turnUp()
                        self.say("好的", cache=True)
                    else:
                        self.player.turnDown()
                        self.say("好的", cache=True)

    def isValid(self, text, parsed):
        return self.nlu.hasIntent(parsed, "CHANGE_VOL")

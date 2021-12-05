# -*- coding: utf-8 -*-
import os
from robot import config, logging
from robot.Player import MusicPlayer
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)


class Plugin(AbstractPlugin):

    IS_IMMERSIVE = True  # 这是个沉浸式技能

    def __init__(self, con):
        super(Plugin, self).__init__(con)
        self.player = None
        self.song_list = None

    def get_song_list(self, path):
        if not os.path.exists(path) or not os.path.isdir(path):
            return []
        song_list = list(
            filter(lambda d: d.endswith(".mp3") or d.endswith("wav"), os.listdir(path))
        )
        return [os.path.join(path, song) for song in song_list]

    def init_music_player(self):
        self.song_list = self.get_song_list(config.get("/LocalPlayer/path"))
        if self.song_list == None:
            logger.error("{} 插件配置有误".format(self.SLUG))
        logger.info("本地音乐列表：{}".format(self.song_list))
        return MusicPlayer(self.song_list, self)

    def handle(self, text, parsed):
        if not self.player:
            self.player = self.init_music_player()
        if len(self.song_list) == 0:
            self.clearImmersive()  # 去掉沉浸式
            self.say("本地音乐目录并没有音乐文件，播放失败")
            return
        if self.nlu.hasIntent(parsed, "MUSICRANK"):
            self.player.play()
        elif self.nlu.hasIntent(parsed, "CHANGE_TO_NEXT"):
            self.player.next()
        elif self.nlu.hasIntent(parsed, "CHANGE_TO_LAST"):
            self.player.prev()
        elif self.nlu.hasIntent(parsed, "CHANGE_VOL"):
            slots = self.nlu.getSlots(parsed, "CHANGE_VOL")
            for slot in slots:
                if slot["name"] == "user_d":
                    word = self.nlu.getSlotWords(parsed, "CHANGE_VOL", "user_d")[0]
                    if word == "--HIGHER--":
                        self.player.turnUp()
                    else:
                        self.player.turnDown()
                    return
                elif slot["name"] == "user_vd":
                    word = self.nlu.getSlotWords(parsed, "CHANGE_VOL", "user_vd")[0]
                    if word == "--LOUDER--":
                        self.player.turnUp()
                    else:
                        self.player.turnDown()

        elif self.nlu.hasIntent(parsed, "PAUSE"):
            self.player.pause()
        elif self.nlu.hasIntent(parsed, "CONTINUE"):
            self.player.resume()
        elif self.nlu.hasIntent(parsed, "CLOSE_MUSIC"):
            self.player.stop()
            self.clearImmersive()  # 去掉沉浸式
        else:
            self.say("没听懂你的意思呢，要停止播放，请说停止播放", wait=True)
            self.player.resume()

    def pause(self):
        if self.player:
            self.player.stop()

    def restore(self):
        if self.player and not self.player.is_pausing():
            self.player.resume()

    def isValidImmersive(self, text, parsed):
        return any(
            self.nlu.hasIntent(parsed, intent)
            for intent in [
                "CHANGE_TO_LAST",
                "CHANGE_TO_NEXT",
                "CHANGE_VOL",
                "CLOSE_MUSIC",
                "PAUSE",
                "CONTINUE",
            ]
        )

    def isValid(self, text, parsed):
        return "本地音乐" in text

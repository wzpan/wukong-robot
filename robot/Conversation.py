# -*- coding: utf-8-*-
from robot import ASR, TTS, AI, Player, config, constants, utils
from robot.Brain import Brain
from snowboy import snowboydecoder
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Conversation(object):

    def __init__(self):
        self.player = None
        self.brain = Brain(self)
        self.reload()

    def reload(self):
        try:
            self.asr = ASR.get_engine_by_slug(config.get('asr_engine', 'tencent-asr'))
            self.ai = AI.get_robot_by_slug(config.get('robot', 'tuling'))
            self.tts = TTS.get_engine_by_slug(config.get('tts_engine', 'baidu-tts'))
        except Exception as e:
            logger.critical("对话初始化失败：{}".format(e))

    def converse(self, fp):
        try:
            self.interrupt()
            snowboydecoder.play_audio_file(constants.getData('beep_lo.wav'))
            query = self.asr.transcribe(fp)
            utils.check_and_delete(fp)
            if not self.brain.query([query]):
                # 没命中技能，使用机器人回复
                msg = self.ai.chat(query)
                self.say(msg)
        except Exception as e:
            logger.critical(e)
            utils.clean()

    def say(self, msg, cache=False):
        voice = self.tts.get_speech(msg)
        self.player = Player.SoxPlayer()
        self.player.play(voice, True)

    def interrupt(self):
        if self.player is not None and self.player.is_playing():
            self.player.stop()
            self.player = None

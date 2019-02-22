# -*- coding: utf-8-*-
from robot import ASR, TTS, NLU, AI, Player, config, constants, utils, statistic
from robot.Brain import Brain
from snowboy import snowboydecoder
import time 
from robot import logging
import uuid

logger = logging.getLogger(__name__)

class Conversation(object):

    def __init__(self):
        self.reload()
        # 历史会话消息
        self.history = []
        # 沉浸模式，处于这个模式下，被打断后将自动恢复这个技能
        self.immersiveMode = None
        self.isRecording = False

    def getHistory(self):
        return self.history

    def interrupt(self):
        if self.player is not None and self.player.is_playing():
            self.player.stop()
            self.player = None

    def reload(self):
        """ 重新初始化 """
        try:
            self.asr = ASR.get_engine_by_slug(config.get('asr_engine', 'tencent-asr'))
            self.ai = AI.get_robot_by_slug(config.get('robot', 'tuling'))
            self.tts = TTS.get_engine_by_slug(config.get('tts_engine', 'baidu-tts'))
            self.nlu = NLU.get_engine_by_slug(config.get('nlu_engine', 'unit'))
            self.player = None
            self.brain = Brain(self)
            self.brain.printPlugins()
        except Exception as e:
            logger.critical("对话初始化失败：{}".format(e))

    def checkRestore(self):
        if self.immersiveMode:
            self.brain.restore()

    def doResponse(self, query, UUID=''):
        statistic.report(1)
        self.interrupt()
        self.appendHistory(0, query, UUID)
        if not self.brain.query(query):
            # 没命中技能，使用机器人回复
            msg = self.ai.chat(query)
            self.say(msg, True, onCompleted=self.checkRestore)

    def doParse(self, query, **args):
        return self.nlu.parse(query, **args)

    def setImmersiveMode(self, slug):
        self.immersiveMode = slug

    def getImmersiveMode(self):
        return self.immersiveMode

    def converse(self, fp, callback=None):
        """ 核心对话逻辑 """
        Player.play(constants.getData('beep_lo.wav'))
        logger.info('结束录音')
        self.isRecording = False
        self.doConverse(fp, callback)

    def doConverse(self, fp, callback=None):
        try:
            self.interrupt()
            query = self.asr.transcribe(fp)
            utils.check_and_delete(fp)
            self.doResponse(query, callback)
        except Exception as e:
            logger.critical(e)
            utils.clean()

    def appendHistory(self, t, text, UUID=''):
        """ 将会话历史加进历史记录 """
        if t in (0, 1) and text != '':
            if text.endswith(',') or text.endswith('，'):
                text = text[:-1]
            if UUID == '' or UUID == None or UUID == 'null':
                UUID = str(uuid.uuid1())
            self.history.append({'type': t, 'text': text, 'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), 'uuid': UUID})

    def _onCompleted(self, msg):
        if config.get('active_mode', False) and \
           (
               msg.endswith('?') or 
               msg.endswith(u'？') or 
               u'告诉我' in msg or u'请回答' in msg
           ):
            query = self.activeListen()
            self.doResponse(query)

    def say(self, msg, cache=False, plugin='', onCompleted=None):
        """ 说一句话 """
        if plugin != '':
            self.appendHistory(1, "[{}] {}".format(plugin, msg))
        else:
            self.appendHistory(1, msg)
        voice = ''
        if utils.getCache(msg):
            logger.info("命中缓存，播放缓存语音")
            voice = utils.getCache(msg)
        else:
            try:
                voice = self.tts.get_speech(msg)
                if cache:
                    utils.saveCache(voice, msg)
            except Exception as e:
                logger.error('保存缓存失败！')
        if onCompleted is None:
            onCompleted = lambda: self._onCompleted(msg)
        self.player = Player.SoxPlayer()
        self.player.play(voice, not cache, onCompleted)

    def activeListen(self):
        """ 主动问一个问题(适用于多轮对话) """
        time.sleep(1)
        Player.play(constants.getData('beep_hi.wav'))        
        listener = snowboydecoder.ActiveListener([constants.getHotwordModel(config.get('hotword', 'wukong.pmdl'))])
        voice = listener.listen(
            silent_count_threshold=config.get('silent_threshold', 15),
            recording_timeout=config.get('recording_timeout', 5) * 4
        )
        Player.play(constants.getData('beep_lo.wav'))
        query = self.asr.transcribe(voice)
        utils.check_and_delete(voice)
        return query

    def play(self, src, delete=False, onCompleted=None, volume=1):
        """ 播放一个音频 """
        if self.player:
            self.interrupt()
        self.player = Player.SoxPlayer()
        self.player.play(src, delete, onCompleted=onCompleted, volume=volume)
    

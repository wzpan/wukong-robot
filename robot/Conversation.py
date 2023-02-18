# -*- coding: utf-8 -*-
import time
import uuid
import cProfile
import pstats
import io
import re
import os
from robot.LifeCycleHandler import LifeCycleHandler
from robot.Brain import Brain
from robot.sdk import LED, MessageBuffer
from snowboy import snowboydecoder
from robot import (
    logging,
    ASR,
    TTS,
    NLU,
    AI,
    Player,
    config,
    constants,
    utils,
    statistic,
)


logger = logging.getLogger(__name__)


class Conversation(object):
    def __init__(self, profiling=False):
        self.brain = None
        self.asr = None
        self.ai = None
        self.tts = None
        self.nlu = None
        self.reInit()
        self.player = None
        self.brain = Brain(self)
        self.brain.printPlugins()
        # 历史会话消息
        self.history = MessageBuffer.MessageBuffer()
        # 沉浸模式，处于这个模式下，被打断后将自动恢复这个技能
        self.matchPlugin = None
        self.immersiveMode = None
        self.isRecording = False
        self.profiling = profiling
        self.onSay = None
        self.hasPardon = False
        self.lifeCycleHandler = LifeCycleHandler(self)

    def getHistory(self):
        return self.history

    def interrupt(self):
        if self.player and self.player.is_playing():
            self.player.stop()
            self.player = None
        if self.immersiveMode:
            self.brain.pause()

    def reInit(self):
        """重新初始化"""
        try:
            self.asr = ASR.get_engine_by_slug(config.get("asr_engine", "tencent-asr"))
            self.ai = AI.get_robot_by_slug(config.get("robot", "tuling"))
            self.tts = TTS.get_engine_by_slug(config.get("tts_engine", "baidu-tts"))
            self.nlu = NLU.get_engine_by_slug(config.get("nlu_engine", "unit"))
            self.player = None
            self.brain = Brain(self)
            self.brain.printPlugins()
        except Exception as e:
            logger.critical("对话初始化失败：{}".format(e))

    def checkRestore(self):
        if self.immersiveMode:
            logger.info("处于沉浸模式，恢复技能")
            self.lifeCycleHandler.onRestore()
            self.brain.restore()

    def doResponse(self, query, UUID="", onSay=None):
        statistic.report(1)
        self.interrupt()
        self.appendHistory(0, query, UUID)

        if onSay:
            self.onSay = onSay

        if query.strip() == "":
            self.pardon()
            return

        lastImmersiveMode = self.immersiveMode

        args = {
            "service_id": config.get("/unit/service_id", "S13442"),
            "api_key": config.get("/unit/api_key", "w5v7gUV3iPGsGntcM84PtOOM"),
            "secret_key": config.get(
                "/unit/secret_key", "KffXwW6E1alcGplcabcNs63Li6GvvnfL"
            ),
        }
        parsed = self.doParse(query, **args)
        if not self.brain.query(query, parsed):
            # 没命中技能，使用机器人回复
            msg = self.ai.chat(query, parsed)
            self.say(msg, True, onCompleted=self.checkRestore)
        else:
            if lastImmersiveMode and lastImmersiveMode != self.matchPlugin:
                time.sleep(1)
                if self.player and self.player.is_playing():
                    logger.debug("等说完再checkRestore")
                    self.player.appendOnCompleted(lambda: self.checkRestore())
                else:
                    logger.debug("checkRestore")
                    self.checkRestore()

    def doParse(self, query, **args):
        return self.nlu.parse(query, **args)

    def setImmersiveMode(self, slug):
        self.immersiveMode = slug

    def getImmersiveMode(self):
        return self.immersiveMode

    def converse(self, fp, callback=None):
        """核心对话逻辑"""
        logger.info("结束录音")
        self.lifeCycleHandler.onThink()
        self.isRecording = False
        if self.profiling:
            logger.info("性能调试已打开")
            pr = cProfile.Profile()
            pr.enable()
            self.doConverse(fp, callback)
            pr.disable()
            s = io.StringIO()
            sortby = "cumulative"
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.print_stats()
            print(s.getvalue())
        else:
            self.doConverse(fp, callback)

    def doConverse(self, fp, callback=None, onSay=None):
        self.interrupt()
        try:
            query = self.asr.transcribe(fp)
        except Exception as e:
            logger.critical("ASR识别失败：{}".format(e))
        utils.check_and_delete(fp)
        try:
            self.doResponse(query, callback, onSay)
        except Exception as e:
            logger.critical("回复失败：{}".format(e))
        utils.clean()

    def appendHistory(self, t, text, UUID="", plugin=""):
        """将会话历史加进历史记录"""
        if t in (0, 1) and text:
            if text.endswith(",") or text.endswith("，"):
                text = text[:-1]
            if UUID == "" or UUID == None or UUID == "null":
                UUID = str(uuid.uuid1())
            # 将图片处理成HTML
            pattern = r"https?://.+\.(?:png|jpg|jpeg|bmp|gif|JPG|PNG|JPEG|BMP|GIF)"
            url_pattern = r"^https?://.+"
            imgs = re.findall(pattern, text)
            for img in imgs:
                text = text.replace(
                    img,
                    '<a data-fancybox="images" href="{}"><img src={} class="img fancybox"></img></a>'.format(
                        img, img
                    ),
                )
            urls = re.findall(url_pattern, text)
            for url in urls:
                text = text.replace(
                    url, '<a href={} target="_blank">{}</a>'.format(url, url)
                )
            self.lifeCycleHandler.onResponse(t, text)
            self.history.add_message(
                {
                    "type": t,
                    "text": text,
                    "time": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(time.time())
                    ),
                    "uuid": UUID,
                    "plugin": plugin,
                }
            )

    def _onCompleted(self, msg):
        if config.get("active_mode", False) and (
            msg.endswith("?") or msg.endswith("？") or "告诉我" in msg or "请回答" in msg
        ):
            query = self.activeListen()
            self.doResponse(query)

    def pardon(self):
        if not self.hasPardon:
            self.say(
                "抱歉，刚刚没听清，能再说一遍吗？",
                onCompleted=lambda: self.doResponse(self.activeListen()),
            )
            self.hasPardon = True
        else:
            self.say("没听清呢")
            self.hasPardon = False

    def say(self, msg, cache=False, plugin="", onCompleted=None, wait=False, append_history=True):
        """
        说一句话
        :param msg: 内容
        :param cache: 是否缓存这句话的音频
        :param plugin: 来自哪个插件的消息（将带上插件的说明）
        :param onCompleted: 完成的回调
        :param wait: 是否要等待说完（为True将阻塞主线程直至说完这句话）
        """
        append_history and self.appendHistory(1, msg, plugin=plugin)
        is_too_long = False
        pattern = r"http[s]?://.+"
        if re.match(pattern, msg):
            logger.info("内容包含URL，屏蔽后续内容")
            msg = re.sub(pattern, '', msg)
        if not msg:
            return
        msg = utils.stripPunctuation(msg)
        msg = msg.strip()
        logger.info(f"即将朗读语音：{msg}")
        if config.get("trim_too_long_text", True) and \
            len(msg) > config.get('max_text_length', 128):
            # 文本太长，TTS 会报错
            logger.info("文本超长，需进行截断")
            # 采用截断的方案
            lines = re.split("。|！|？|\.|\!|\?|\n", msg)
            shorter_msg = ''
            if "\n" in msg:
                idx = 0
                while True:
                    shorter_msg += lines[idx]
                    idx += 1
                    if len(shorter_msg) >= 128:
                        break
                msg = shorter_msg
            else:
                msg = msg[0:128]
            logger.info(f"截断后的文本：{msg}")
            is_too_long = True
        voice = ""
        cache_path = ""
        if utils.getCache(msg):
            logger.info("命中缓存，播放缓存语音")
            voice = utils.getCache(msg)
            cache_path = utils.getCache(msg)
        else:
            try:
                voice = self.tts.get_speech(msg)
                cache_path = utils.saveCache(voice, msg)
            except Exception as e:
                logger.error("语音合成失败：{}".format(e))
        if self.onSay:
            logger.info(cache)
            audio = "http://{}:{}/audio/{}".format(
                config.get("/server/host"),
                config.get("/server/port"),
                os.path.basename(cache_path),
            )
            logger.info("onSay: {}, {}".format(msg, audio))
            self.onSay(msg, audio, plugin=plugin)
            self.onSay = None
        if onCompleted is None:
            onCompleted = lambda: self._onCompleted(msg)
        self.player = Player.SoxPlayer()
        if config.get("trim_too_long_text", True) and is_too_long:
            self.player.preappendCompleted(lambda: self.say("后面的内容太长了，我就不念了", append_history=False))
        self.player.play(voice, not cache, onCompleted, wait)
        utils.lruCache()  # 清理缓存

    def activeListen(self, silent=False):
        """主动问一个问题(适用于多轮对话)"""
        logger.debug("activeListen")
        try:
            if not silent:
                self.lifeCycleHandler.onWakeup()
            listener = snowboydecoder.ActiveListener(
                [constants.getHotwordModel(config.get("hotword", "wukong.pmdl"))]
            )
            voice = listener.listen(
                silent_count_threshold=config.get("silent_threshold", 15),
                recording_timeout=config.get("recording_timeout", 5) * 4,
            )
            if not silent:
                self.lifeCycleHandler.onThink()
            if voice:
                query = self.asr.transcribe(voice)
                utils.check_and_delete(voice)
                return query
            return ""
        except Exception as e:
            logger.error("主动聆听失败".format(e))
            return ""

    def play(self, src, delete=False, onCompleted=None, volume=1):
        """播放一个音频"""
        if self.player:
            self.interrupt()
        self.player = Player.SoxPlayer()
        self.player.play(src, delete=delete, onCompleted=onCompleted)

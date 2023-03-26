# -*- coding: utf-8 -*-
import time
import uuid
import cProfile
import pstats
import io
import re
import os
import queue
import threading
import traceback

from concurrent.futures import ThreadPoolExecutor, as_completed

from snowboy import snowboydecoder

from robot.LifeCycleHandler import LifeCycleHandler
from robot.Brain import Brain
from robot.Scheduler import Scheduler
from robot.sdk import MessageBuffer
from robot import (
    AI,
    ASR,
    config,
    constants,
    logging,
    NLU,
    Player,
    statistic,
    TTS,
    utils,
)


logger = logging.getLogger(__name__)


class Conversation(object):
    def __init__(self, profiling=False):
        self.brain, self.asr, self.ai, self.tts, self.nlu = None, None, None, None, None
        self.reInit()
        self.scheduler = Scheduler(self)
        # 历史会话消息
        self.history = MessageBuffer.MessageBuffer()
        # 沉浸模式，处于这个模式下，被打断后将自动恢复这个技能
        self.matchPlugin = None
        self.immersiveMode = None
        self.isRecording = False
        self.profiling = profiling
        self.onSay = None
        self.hasPardon = False
        self.player = Player.SoxPlayer()
        self.lifeCycleHandler = LifeCycleHandler(self)
        self.audios = []
        self.tts_index = 0
        self.tts_lock = threading.Lock()
        self.play_lock = threading.Lock()

    def _ttsAction(self, msg, index, cache):
        if msg:
            logger.info(f"开始合成第{index}段TTS：{msg}")
            voice = ""
            if utils.getCache(msg):
                logger.info(f"第{index}段TTS命中缓存，播放缓存语音")
                voice = utils.getCache(msg)
                while index != self.tts_index:
                    # 阻塞直到轮到这个音频播放                    
                    continue
                with self.play_lock:
                    self.player.play(voice, not cache)
                    self.tts_index += 1
                return (voice, index)
            else:
                try:
                    voice = self.tts.get_speech(msg)
                    logger.info(f"合成第{index}段TTS合成成功：{msg}")
                    logger.debug(f"self.tts_index: {self.tts_index}")
                    while index != self.tts_index:
                        # 阻塞直到轮到这个音频播放                        
                        continue
                    with self.play_lock:
                        self.player.play(voice, not cache)
                        self.tts_index += 1                        
                    return (voice, index)
                except Exception as e:
                    logger.error(f"语音合成失败：{e}", stack_info=True)
                    traceback.print_exc()
                    return None

    def getHistory(self):
        return self.history

    def interrupt(self):
        if self.player and self.player.is_playing():
            self.player.stop()
        if self.immersiveMode:
            self.brain.pause()

    def reInit(self):
        """重新初始化"""
        try:
            self.asr = ASR.get_engine_by_slug(config.get("asr_engine", "tencent-asr"))
            self.ai = AI.get_robot_by_slug(config.get("robot", "tuling"))
            self.tts = TTS.get_engine_by_slug(config.get("tts_engine", "baidu-tts"))
            self.nlu = NLU.get_engine_by_slug(config.get("nlu_engine", "unit"))
            self.player = Player.SoxPlayer()
            self.brain = Brain(self)
            self.brain.printPlugins()
        except Exception as e:
            logger.critical(f"对话初始化失败：{e}", stack_info=True)

    def checkRestore(self):
        if self.immersiveMode:
            logger.info("处于沉浸模式，恢复技能")
            self.lifeCycleHandler.onRestore()
            self.brain.restore()

    def doResponse(self, query, UUID="", onSay=None):
        """
        响应指令

        :param query: 指令
        :UUID: 指令的UUID
        :onSay: 朗读时的回调
        """
        statistic.report(1)
        self.interrupt()
        self.appendHistory(0, query, UUID)

        if onSay:
            self.onSay = onSay

        if query.strip() == "":
            self.pardon()
            return

        lastImmersiveMode = self.immersiveMode

        parsed = self.doParse(query)
        if not self.brain.query(query, parsed):
            if self.nlu.hasIntent(parsed, "PAUSE") or "闭嘴" in query:
                # 停止说话
                self.player.stop()
            else:
                # 没命中技能，使用机器人回复
                msg = self.ai.chat(query, parsed)
                self.say(msg, True, onCompleted=self.checkRestore)
        else:
            # 命中技能
            if lastImmersiveMode and lastImmersiveMode != self.matchPlugin:
                if self.player:
                    if self.player.is_playing():
                        logger.debug("等说完再checkRestore")
                        self.player.appendOnCompleted(lambda: self.checkRestore())
                else:
                    logger.debug("checkRestore")
                    self.checkRestore()

    def doParse(self, query):
        args = {
            "service_id": config.get("/unit/service_id", "S13442"),
            "api_key": config.get("/unit/api_key", "w5v7gUV3iPGsGntcM84PtOOM"),
            "secret_key": config.get(
                "/unit/secret_key", "KffXwW6E1alcGplcabcNs63Li6GvvnfL"
            ),
        }
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
            logger.critical(f"ASR识别失败：{e}", stack_info=True)
            traceback.print_exc()
        utils.check_and_delete(fp)
        try:
            self.doResponse(query, callback, onSay)
        except Exception as e:
            logger.critical(f"回复失败：{e}", stack_info=True)
            traceback.print_exc()
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
                    f'<a data-fancybox="images" href="{img}"><img src={img} class="img fancybox"></img></a>',
                )
            urls = re.findall(url_pattern, text)
            for url in urls:
                text = text.replace(url, f'<a href={url} target="_blank">{url}</a>')
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

    def say(
        self,
        msg,
        cache=False,
        plugin="",
        onCompleted=None,
        append_history=True,
    ):
        """
        说一句话
        :param msg: 内容
        :param cache: 是否缓存这句话的音频
        :param plugin: 来自哪个插件的消息（将带上插件的说明）
        :param onCompleted: 完成的回调
        :param append_history: 是否要追加到聊天记录
        """
        # 确保同时只有一个say
        with self.tts_lock:
            append_history and self.appendHistory(1, msg, plugin=plugin)
            pattern = r"http[s]?://.+"
            if re.match(pattern, msg):
                logger.info("内容包含URL，屏蔽后续内容")
                msg = re.sub(pattern, "", msg)
            msg = utils.stripPunctuation(msg)
            msg = msg.strip()
            if not msg:
                return
            logger.info(f"即将朗读语音：{msg}")
            # 分拆成多行，分别进行TTS
            lines = re.split("。|！|？|\.|\!|\?|\n", msg)
            self.audios = []
            cached_audios = []
            self.tts_index = 0
            # 创建一个包含5条线程的线程池
            with ThreadPoolExecutor(max_workers=5) as pool:
                index = 0
                all_task = []
                for line in lines:
                    if line:
                        task = pool.submit(self._ttsAction, line, index, cache)
                        index += 1
                        all_task.append(task)
                res_audios = []
                for task in as_completed(all_task):
                    task.result() and res_audios.append(task.result())
                sorted_audios = sorted(res_audios, key=lambda x: x[1])
                self.audios = [audio[0] for audio in sorted_audios]
            if self.onSay:
                for voice in self.audios:
                    audio = "http://{}:{}/audio/{}".format(
                        config.get("/server/host"),
                        config.get("/server/port"),
                        os.path.basename(voice),
                    )
                    cached_audios.append(audio)
                logger.info(f"onSay: {msg}, {cached_audios}")
                self.onSay(msg, cached_audios, plugin=plugin)
                self.onSay = None            
            if onCompleted is None:
                onCompleted = lambda: self._onCompleted(msg)
            onCompleted and onCompleted()
            utils.lruCache()  # 清理缓存

    def activeListen(self, silent=False):
        """
        主动问一个问题(适用于多轮对话)
        :param silent: 是否不触发唤醒表现（主要用于极客模式）
        :param
        """
        if self.immersiveMode:
            self.player.stop()
        elif self.player.is_playing():
            self.player.join()  # 确保所有音频都播完
        logger.info("进入主动聆听...")
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
            logger.error(f"主动聆听失败：{e}", stack_info=True)
            traceback.print_exc()
            return ""

    def play(self, src, delete=False, onCompleted=None, volume=1):
        """播放一个音频"""
        if self.player:
            self.interrupt()
        self.player = Player.SoxPlayer()
        self.player.play(src, delete=delete, onCompleted=onCompleted)

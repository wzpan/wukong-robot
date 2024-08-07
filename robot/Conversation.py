# -*- coding: utf-8 -*-
import time
import uuid
import cProfile
import pstats
import io
import re
import os
import threading
import traceback

from concurrent.futures import ThreadPoolExecutor, as_completed

from snowboy import snowboydecoder

from robot.LifeCycleHandler import LifeCycleHandler
from robot.Brain import Brain
from robot.Scheduler import Scheduler
from robot.sdk import History
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
        self.history = History.History()
        # 沉浸模式，处于这个模式下，被打断后将自动恢复这个技能
        self.matchPlugin = None
        self.immersiveMode = None
        self.isRecording = False
        self.profiling = profiling
        self.onSay = None
        self.onStream = None
        self.hasPardon = False
        self.player = Player.SoxPlayer()
        self.lifeCycleHandler = LifeCycleHandler(self)
        self.tts_count = 0
        self.tts_index = 0
        self.tts_lock = threading.Lock()
        self.play_lock = threading.Lock()

    def _lastCompleted(self, index, onCompleted):
        # logger.debug(f"{index}, {self.tts_index}, {self.tts_count}")
        if index >= self.tts_count - 1:
            # logger.debug(f"执行onCompleted")
            onCompleted and onCompleted()

    def _ttsAction(self, msg, cache, index, onCompleted=None):
        if msg:
            voice = ""
            if utils.getCache(msg):
                logger.info(f"第{index}段TTS命中缓存，播放缓存语音")
                voice = utils.getCache(msg)
                while index != self.tts_index:
                    # 阻塞直到轮到这个音频播放
                    continue
                with self.play_lock:
                    self.player.play(
                        voice,
                        not cache,
                        onCompleted=lambda: self._lastCompleted(index, onCompleted),
                    )
                    self.tts_index += 1
                return voice
            else:
                try:
                    voice = self.tts.get_speech(msg)
                    logger.info(f"第{index}段TTS合成成功。msg: {msg}")
                    while index != self.tts_index:
                        # 阻塞直到轮到这个音频播放
                        continue
                    with self.play_lock:
                        logger.info(f"即将播放第{index}段TTS。msg: {msg}")
                        self.player.play(
                            voice,
                            not cache,
                            onCompleted=lambda: self._lastCompleted(index, onCompleted),
                        )
                        self.tts_index += 1
                    return voice
                except Exception as e:
                    logger.error(f"语音合成失败：{e}", stack_info=True)
                    self.tts_index += 1
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

    def _InGossip(self, query):
        return self.immersiveMode in ["Gossip"] and not "闲聊" in query

    def doResponse(self, query, UUID="", onSay=None, onStream=None):
        """
        响应指令

        :param query: 指令
        :UUID: 指令的UUID
        :onSay: 朗读时的回调
        :onStream: 流式输出时的回调
        """
        statistic.report(1)
        self.interrupt()
        self.appendHistory(0, query, UUID)

        if onSay:
            self.onSay = onSay

        if onStream:
            self.onStream = onStream

        if query.strip() == "":
            self.pardon()
            return

        lastImmersiveMode = self.immersiveMode

        parsed = self.doParse(query)
        if self._InGossip(query) or not self.brain.query(query, parsed):
            # 进入闲聊
            if self.nlu.hasIntent(parsed, "PAUSE") or "闭嘴" in query:
                # 停止说话
                self.player.stop()
            else:
                # 没命中技能，使用机器人回复
                if self.ai.SLUG == "openai":
                    stream = self.ai.stream_chat(query)
                    self.stream_say(stream, True, onCompleted=self.checkRestore)
                else:
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

    def doConverse(self, fp, callback=None, onSay=None, onStream=None):
        self.interrupt()
        try:
            query = self.asr.transcribe(fp)
        except Exception as e:
            logger.critical(f"ASR识别失败：{e}", stack_info=True)
            traceback.print_exc()
        utils.check_and_delete(fp)
        try:
            self.doResponse(query, callback, onSay, onStream)
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
        pass

    def pardon(self):
        if not self.hasPardon:
            self.say("抱歉，刚刚没听清，能再说一遍吗？", cache=True)
            self.hasPardon = True
        else:
            self.say("没听清呢")
            self.hasPardon = False

    def _tts_line(self, line, cache, index=0, onCompleted=None):
        """
        对单行字符串进行 TTS 并返回合成后的音频
        :param line: 字符串
        :param cache: 是否缓存 TTS 结果
        :param index: 合成序号
        :param onCompleted: 播放完成的操作
        """
        line = line.strip()
        pattern = r"http[s]?://.+"
        if re.match(pattern, line):
            logger.info("内容包含URL，屏蔽后续内容")
            return None
        line.replace("- ", "")
        if line:
            result = self._ttsAction(line, cache, index, onCompleted)
            return result
        return None

    def _tts(self, lines, cache, onCompleted=None):
        """
        对字符串进行 TTS 并返回合成后的音频
        :param lines: 字符串列表
        :param cache: 是否缓存 TTS 结果
        """
        audios = []
        pattern = r"http[s]?://.+"
        logger.info("_tts")
        with self.tts_lock:
            with ThreadPoolExecutor(max_workers=config.get("tts_parallel", 5)) as pool:
                all_task = []
                index = 0
                for line in lines:
                    if re.match(pattern, line):
                        logger.info("内容包含URL，屏蔽后续内容")
                        self.tts_count -= 1
                        continue
                    if line:
                        task = pool.submit(
                            self._ttsAction, line.strip(), cache, index, onCompleted
                        )
                        index += 1
                        all_task.append(task)
                    else:
                        self.tts_count -= 1
                for future in as_completed(all_task):
                    audio = future.result()
                    if audio:
                        audios.append(audio)
            return audios

    def _after_play(self, msg, audios, plugin=""):
        cached_audios = [
            f"http://{config.get('/server/host')}:{config.get('/server/port')}/audio/{os.path.basename(voice)}"
            for voice in audios
        ]
        if self.onSay:
            logger.info(f"onSay: {msg}, {cached_audios}")
            self.onSay(msg, cached_audios, plugin=plugin)
            self.onSay = None
        utils.lruCache()  # 清理缓存

    def stream_say(self, stream, cache=False, onCompleted=None):
        """
        从流中逐字逐句生成语音
        :param stream: 文字流，可迭代对象
        :param cache: 是否缓存 TTS 结果
        :param onCompleted: 声音播报完成后的回调
        """
        lines = []
        line = ""
        resp_uuid = str(uuid.uuid1())
        audios = []
        if onCompleted is None:
            onCompleted = lambda: self._onCompleted(msg)
        self.tts_index = 0
        self.tts_count = 0
        index = 0
        skip_tts = False
        for data in stream():
            if self.onStream:
                self.onStream(data, resp_uuid)
            line += data
            if any(char in data for char in utils.getPunctuations()):
                if "```" in line.strip():
                    skip_tts = True
                if not skip_tts:
                    audio = self._tts_line(line.strip(), cache, index, onCompleted)
                    if audio:
                        self.tts_count += 1
                        audios.append(audio)
                        index += 1
                else:
                    logger.info(f"{line} 属于代码段，跳过朗读")
                lines.append(line)
                line = ""
        if line.strip():
            lines.append(line)
        if skip_tts:
            self._tts_line("内容包含代码，我就不念了", True, index, onCompleted)
        msg = "".join(lines)
        self.appendHistory(1, msg, UUID=resp_uuid, plugin="")
        self._after_play(msg, audios, "")

    def say(self, msg, cache=False, plugin="", onCompleted=None, append_history=True):
        """
        说一句话
        :param msg: 内容
        :param cache: 是否缓存这句话的音频
        :param plugin: 来自哪个插件的消息（将带上插件的说明）
        :param onCompleted: 完成的回调
        :param append_history: 是否要追加到聊天记录
        """
        if append_history:
            self.appendHistory(1, msg, plugin=plugin)
        msg = utils.stripPunctuation(msg).strip()

        if not msg:
            return

        logger.info(f"即将朗读语音：{msg}")
        lines = re.split("。|！|？|\!|\?|\n", msg)
        if onCompleted is None:
            onCompleted = lambda: self._onCompleted(msg)
        self.tts_index = 0
        self.tts_count = len(lines)
        logger.debug(f"tts_count: {self.tts_count}")
        audios = self._tts(lines, cache, onCompleted)
        self._after_play(msg, audios, plugin)

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

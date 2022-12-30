import time
import logging
import multiprocessing
import _thread as thread

from watchdog.observers import Observer
from robot import config, constants, statistic, Player
from robot.ConfigMonitor import ConfigMonitor
from robot.sdk import LED

logger = logging.getLogger(__name__)


def singleton(cls):
    _instance = {}

    def inner(conversation):
        if cls not in _instance:
            _instance[cls] = cls(conversation)
        return _instance[cls]

    return inner


"""
抽象出来的生命周期，
方便在这里针对 wukong 的各个状态做定制
"""


@singleton
class LifeCycleHandler(object):
    def __init__(self, conversation):
        self._observer = Observer()
        self._unihiker = None
        self._wakeup = None
        self._conversation = conversation

    def onInit(self):
        """
        wukong-robot 初始化
        """
        config.init()
        statistic.report(0)

        # 初始化配置监听器
        config_event_handler = ConfigMonitor(self._conversation)
        self._observer.schedule(config_event_handler, constants.CONFIG_PATH, False)
        self._observer.schedule(config_event_handler, constants.DATA_PATH, False)
        self._observer.start()

        # 行空板
        self._init_unihiker()
        # LED 灯
        self._init_LED()
        # Muse 头环
        self._init_muse()

    def _init_unihiker(self):
        global unihiker
        if config.get("/unihiker/enable", False):
            try:
                from robot.sdk.Unihiker import Unihiker

                self._unihiker = Unihiker()
                thread.start_new_thread(self._unihiker_shake_event, ())
            except ImportError:
                logger.error("错误：请确保当前硬件环境为天行板")

    def _init_LED(self):
        if config.get("/LED/enable", False) and config.get("/LED/type") == "aiy":
            thread.start_new_thread(self._aiy_button_event, ())

    def _init_muse(self):
        if config.get("/muse/enable", False):
            try:
                from robot import BCI

                self._wakeup = multiprocessing.Event()
                bci = BCI.MuseBCI(self._wakeup)
                bci.start()
                thread.start_new_thread(self._muse_loop_event, ())
            except ImportError:
                logger.error("错误：请确保当前硬件搭配了Muse头环并安装了相关驱动")

    def _unihiker_shake_event(self):
        """
        天行板摇一摇的监听逻辑
        """
        while True:
            from pinpong.extension.unihiker import accelerometer
            if accelerometer.get_strength() >= 1.5:
                logger.info("天行版摇一摇触发唤醒")
                self._conversation.interrupt()
                query = self._conversation.activeListen()
                self._conversation.doResponse(query)
            time.sleep(0.1)

    def _aiy_button_event(self):
        """
        Google AIY VoiceKit 的监听逻辑
        """
        try:
            from aiy.board import Board
        except ImportError:
            logger.error("错误：请确保当前硬件环境为Google AIY VoiceKit并正确安装了驱动")
            return
        with Board() as board:
            while True:
                board.button.wait_for_press()
                logger.info("Google AIY Voicekit 触发唤醒")
                self._conversation.interrupt()
                query = self._conversation.activeListen()
                self._conversation.doResponse(query)

    def _muse_loop_event(self):
        """
        Muse 头环的监听逻辑
        """
        while True:
            self._wakeup.wait()
            self._conversation.interrupt()
            logger.info("Muse 头环触发唤醒")
            query = self._conversation.activeListen()
            self._conversation.doResponse(query)
            self._wakeup.clear()

    def _beep_hi(self, onCompleted=None, wait=False):
        Player.play(constants.getData("beep_hi.wav"), onCompleted, wait)

    def _beep_lo(self):
        Player.play(constants.getData("beep_lo.wav"))

    def onWakeup(self, onCompleted=None):
        """
        唤醒并进入录音的状态
        """
        self._beep_hi(onCompleted=onCompleted, wait=onCompleted)
        if config.get("/LED/enable", False):
            LED.wakeup()
        self._unihiker and self._unihiker.record(1, "我正在聆听...")
        self._unihiker and self._unihiker.wakeup()

    def onThink(self):
        """
        录音结束并进入思考的状态
        """
        self._beep_lo()
        self._unihiker and self._unihiker.think()
        self._unihiker and self._unihiker.record(1, "我正在思考...")
        if config.get("/LED/enable", False):
            LED.think()

    def onResponse(self, t=1, text=""):
        """
        思考完成并播放结果的状态
        """
        self._unihiker and self._unihiker.record(t, text)
        if config.get("/LED/enable", False):
            LED.off()

    def onRestore(self):
        """
        恢复沉浸式技能的状态
        """
        pass

    def onKilled(self):
        self._observer.stop()

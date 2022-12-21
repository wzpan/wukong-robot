#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import fire
import signal
import hashlib
import urllib3

from robot.Updater import Updater
from robot.Conversation import Conversation
from robot.LifeCycleHandler import LifeCycleHandler

from robot import config, utils, constants, logging, Player

from server import server
from snowboy import snowboydecoder
from tools import make_json, solr_tools

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class Wukong(object):

    _profiling = False

    def init(self):
        self.detector = None
        self.gui = None
        self._interrupted = False
        print(
            """
********************************************************
*          wukong-robot - 中文语音对话机器人           *
*          (c) 2019 潘伟洲 <m@hahack.com>              *
*     https://github.com/wzpan/wukong-robot.git        *
********************************************************

            后台管理端：http://{}:{}
            如需退出，可以按 Ctrl-4 组合键

""".format(
                config.get("/server/host", "0.0.0.0"),
                config.get("/server/port", "5001"),
            )
        )

        self.conversation = Conversation(self._profiling)
        self.conversation.say(
            "{} 你好！试试对我喊唤醒词叫醒我吧".format(config.get("first_name", "主人")), True
        )
        self.lifeCycleHandler = LifeCycleHandler(self.conversation)
        self.lifeCycleHandler.onInit()

    def _signal_handler(self, signal, frame):
        self._interrupted = True
        utils.clean()
        self.lifeCycleHandler.onKilled()

    def _detected_callback(self):
        def _start_record():
            logger.info("开始录音")
            self.conversation.isRecording = True
            utils.setRecordable(True)

        if not utils.is_proper_time():
            logger.warning("勿扰模式开启中")
            return
        if self.conversation.isRecording:
            logger.warning("正在录音中，跳过")
            return
        self.conversation.interrupt()
        utils.setRecordable(False)
        self.lifeCycleHandler.onWakeup(onCompleted=_start_record)

    def _interrupt_callback(self):
        return self._interrupted

    def run(self):
        self.init()
        # capture SIGINT signal, e.g., Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        # 后台管理端
        server.run(self.conversation, self)
        try:
            # 初始化离线唤醒
            self.initDetector()
        except AttributeError:
            logger.error("初始化离线唤醒功能失败")
            pass

    def initDetector(self):
        if self.detector is not None:
            self.detector.terminate()
        models = constants.getHotwordModel(config.get("hotword", "wukong.pmdl"))
        self.detector = snowboydecoder.HotwordDetector(
            models, sensitivity=config.get("sensitivity", 0.5)
        )
        # main loop
        try:
            callbacks = self._detected_callback
            self.detector.start(
                detected_callback=callbacks,
                audio_recorder_callback=self.conversation.converse,
                interrupt_check=self._interrupt_callback,
                silent_count_threshold=config.get("silent_threshold", 15),
                recording_timeout=config.get("recording_timeout", 5) * 4,
                sleep_time=0.03,
            )
            self.detector.terminate()
        except Exception as e:
            logger.critical("离线唤醒机制初始化失败：{}".format(e))

    def help(self):
        print(
            """=====================================================================================
    python3 wukong.py [命令]
    可选命令：
      md5                      - 用于计算字符串的 md5 值，常用于密码设置
      update                   - 手动更新 wukong-robot
      upload [thredNum]        - 手动上传 QA 集语料，重建 solr 索引。
                                 threadNum 表示上传时开启的线程数（可选。默认值为 10）
      profiling                - 运行过程中打印耗时数据
    如需更多帮助，请访问：https://wukong.hahack.com/#/run
====================================================================================="""
        )

    def md5(self, password):
        """
        计算字符串的 md5 值
        """
        return hashlib.md5(str(password).encode("utf-8")).hexdigest()

    def update(self):
        """
        更新 wukong-robot
        """
        updater = Updater()
        return updater.update()

    def fetch(self):
        """
        检测 wukong-robot 的更新
        """
        updater = Updater()
        updater.fetch()

    def upload(self, threadNum=10):
        """
        手动上传 QA 集语料，重建 solr 索引
        """
        try:
            qaJson = os.path.join(constants.TEMP_PATH, "qa_json")
            make_json.run(constants.getQAPath(), qaJson)
            solr_tools.clear_documents(
                config.get("/anyq/host", "0.0.0.0"),
                "collection1",
                config.get("/anyq/solr_port", "8900"),
            )
            solr_tools.upload_documents(
                config.get("/anyq/host", "0.0.0.0"),
                "collection1",
                config.get("/anyq/solr_port", "8900"),
                qaJson,
                threadNum,
            )
        except Exception as e:
            logger.error("上传失败：{}".format(e))

    def restart(self):
        """
        重启 wukong-robot
        """
        logger.critical("程序重启...")
        try:
            self.detector.terminate()
        except AttributeError:
            pass
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def profiling(self):
        """
        运行过程中打印耗时数据
        """
        logger.info("性能调优")
        self._profiling = True
        self.run()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        wukong = Wukong()
        wukong.run()
    elif "-h" in (sys.argv):
        wukong = Wukong()
        wukong.help()
    else:
        fire.Fire(Wukong)

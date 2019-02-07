# -*- coding: utf-8-*-
from snowboy import snowboydecoder
from robot import config, utils, constants, logging, statistic
from robot.ConfigMonitor import ConfigMonitor
from robot.Conversation import Conversation
from server import server
from watchdog.observers import Observer
from subprocess import call
import sys
import os
import signal
import yaml
import requests
import hashlib
import os
import fire

logger = logging.getLogger(__name__)

class Wukong(object):
    
    def init(self):
        global conversation
        self.detector = None
        self._interrupted = False
        print('''
********************************************************
*          wukong-robot - 中文语音对话机器人           *
*          (c) 2019 潘伟洲 <m@hahack.com>              *
*     https://github.com/wzpan/wukong-robot.git        *
********************************************************

            如需退出，可以按 Ctrl-4 组合键。

''')
        
        config.init()
        self._conversation = Conversation()
        self._conversation.say('{} 你好！试试对我喊唤醒词叫醒我吧'.format(config.get('first_name', '主人')), True)
        self._observer = Observer()
        event_handler = ConfigMonitor(self._conversation)
        self._observer.schedule(event_handler, constants.CONFIG_PATH, False)
        self._observer.schedule(event_handler, constants.DATA_PATH, False)
        self._observer.start()

    def _signal_handler(self, signal, frame):
        self._interrupted = True
        utils.clean()
        self._observer.stop()

    def _detected_callback(self):
        if not utils.is_proper_time():
            logger.warning('勿扰模式开启中')
            return
        snowboydecoder.play_audio_file(constants.getData('beep_hi.wav'))
        self._conversation.interrupt()    

    def _do_not_bother_on_callback(self):
        utils.do_not_bother = True
        snowboydecoder.play_audio_file(constants.getData('off.wav'))
        logger.info('勿扰模式打开')

    def _do_not_bother_off_callback(self):
        utils.do_not_bother = False
        snowboydecoder.play_audio_file(constants.getData('on.wav'))
        logger.info('勿扰模式关闭')

    def _interrupt_callback(self):
        return self._interrupted

    def run(self):
        self.init()
        
        # capture SIGINT signal, e.g., Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # site
        server.run(self._conversation, self)

        statistic.report(0)

        self.initDetector()

    def initDetector(self):
        if self.detector is not None:
            self.detector.terminate()
        models = [
            constants.getHotwordModel(config.get('hotword', 'wukong.pmdl')),
            constants.getHotwordModel(utils.get_do_not_bother_on_hotword()),
            constants.getHotwordModel(utils.get_do_not_bother_off_hotword())
        ]
        self.detector = snowboydecoder.HotwordDetector(models, sensitivity=config.get('sensitivity', 0.5))
        # main loop
        self.detector.start(detected_callback=[self._detected_callback,
                                          self._do_not_bother_on_callback,
                                          self._do_not_bother_off_callback],
                       audio_recorder_callback=self._conversation.converse,
                       interrupt_check=self._interrupt_callback,
                       silent_count_threshold=5,
                       sleep_time=0.03)
        self.detector.terminate()            

    def md5(self, password):
        return hashlib.md5(password.encode('utf-8')).hexdigest()

    def _pull(self, cwd):
        if os.path.exists(cwd):
            return call(['git', 'pull'], cwd=cwd, shell=False) == 0
        else:
            logger.error("目录 {} 不存在".format(cwd))
            return False

    def _pip(self, cwd):
        if os.path.exists(cwd):
            return call(['pip', 'install', '-r', 'requirements.txt'], cwd=cwd, shell=False) == 0
        else:
            logger.error("目录 {} 不存在".format(cwd))
            return False

    def update(self):
        if self._pull(constants.APP_PATH) and self._pip(constants.APP_PATH):
            logger.info('wukong-robot 更新成功！')
        else:
            logger.info('wukong-robot 更新失败！')
        if self._pull(constants.CONTRIB_PATH) and self._pip(constants.CONTRIB_PATH):
            logger.info('wukong-contrib 更新成功！')
        else:
            logger.info('wukong-contrib 更新失败！')

    def restart(self):
        logger.critical('程序重启...')
        python = sys.executable
        os.execl(python, python, * sys.argv)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        wukong = Wukong()
        wukong.run()
    else:
        fire.Fire(Wukong)


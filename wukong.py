# -*- coding: utf-8-*-
from snowboy import snowboydecoder
from robot import config, utils, constants
from robot.ConfigMonitor import ConfigMonitor
from robot.Conversation import Conversation
from server import server
from watchdog.observers import Observer
import sys
import signal
import yaml
import requests
import logging
import hashlib
import os
import fire

logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class Wukong(object):
    
    def init(self):
        global conversation
        self._interrupted = False
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
        models = [
            constants.getHotwordModel(config.get('hotword', 'wukong.pmdl')),
            constants.getHotwordModel(utils.get_do_not_bother_on_hotword()),
            constants.getHotwordModel(utils.get_do_not_bother_off_hotword())
        ]

        # capture SIGINT signal, e.g., Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        detector = snowboydecoder.HotwordDetector(models, sensitivity=config.get('sensitivity', 0.5))
        print('Listening... Press Ctrl+C to exit')

        # site
        server.run()

        # main loop
        detector.start(detected_callback=[self._detected_callback,
                                          self._do_not_bother_on_callback,
                                          self._do_not_bother_off_callback],
                       audio_recorder_callback=self._conversation.converse,
                       interrupt_check=self._interrupt_callback,
                       silent_count_threshold=5,
                       sleep_time=0.03)
        detector.terminate()        
            

    def md5(self, password):
        return hashlib.md5(password.encode('utf-8')).hexdigest()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        wukong = Wukong()
        wukong.run()
    else:
        fire.Fire(Wukong)


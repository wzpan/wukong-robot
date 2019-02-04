# -*- coding: utf-8-*-
from snowboy import snowboydecoder
from robot import config, utils, constants
from robot.Conversation import Conversation
from watchdog.observers import Observer
from watchdog.events import *
import sys
import signal
import yaml
import requests
import logging
import os

interrupted = False

logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

conversation = None
observer = None

class ConfigEventHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)

    # 文件修改
    def on_modified(self, event):
        if not event.is_directory:
            config.reload()
    
def init():
    global conversation, observer
    config.init()
    conversation = Conversation()
    conversation.say('{} 你好！'.format(config.get('first_name', '主人')))
    observer = Observer()
    event_handler = ConfigEventHandler()
    observer.schedule(event_handler, constants.CONFIG_PATH, False)
    observer.schedule(event_handler, constants.DATA_PATH, False)
    observer.start()

def signal_handler(signal, frame):
    global interrupted
    interrupted = True
    utils.clean()
    observer.stop()

def detected_callback():
    global conversation
    if not utils.is_proper_time():
        logger.warning('勿扰模式开启中')
        return
    snowboydecoder.play_audio_file(constants.getData('beep_hi.wav'))
    conversation.interrupt()    

def do_not_bother_on_callback():    
    utils.do_not_bother = True
    snowboydecoder.play_audio_file(constants.getData('off.wav'))
    logger.info('勿扰模式打开')

def do_not_bother_off_callback():
    utils.do_not_bother = False
    snowboydecoder.play_audio_file(constants.getData('on.wav'))
    logger.info('勿扰模式关闭')
    

def interrupt_callback():
    global interrupted
    return interrupted

def main():
    global conversation
    init()
    models = [
        constants.getHotwordModel(config.get('hotword', 'wukong.pmdl')),
        constants.getHotwordModel(utils.get_do_not_bother_on_hotword()),
        constants.getHotwordModel(utils.get_do_not_bother_off_hotword())
    ]
    # capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    detector = snowboydecoder.HotwordDetector(models, sensitivity=config.get('sensitivity', 0.5))
    print('Listening... Press Ctrl+C to exit')

    # main loop
    detector.start(detected_callback=[detected_callback,
                                      do_not_bother_on_callback,
                                      do_not_bother_off_callback],
                   audio_recorder_callback=conversation.converse,
                   interrupt_check=interrupt_callback,
                   silent_count_threshold=5,
                   sleep_time=0.03)
    detector.terminate()

if __name__ == '__main__':
    main()


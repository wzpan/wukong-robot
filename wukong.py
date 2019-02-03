# -*- coding: utf-8-*-
from snowboy import snowboydecoder
from robot import config, utils, constants
from robot.Conversation import Conversation
import sys
import signal
import yaml
import requests
import logging
import os

interrupted = False

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

conversation = None

def init():
    global conversation
    config.init()
    conversation = Conversation()
    conversation.say('{} 你好！'.format(config.get('first_name', '主人')))

def signal_handler(signal, frame):
    global interrupted
    interrupted = True
    utils.clean()

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


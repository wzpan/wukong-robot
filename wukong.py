# -*- coding: utf-8-*-
from snowboy import snowboydecoder
from robot import config, conversation, utils, constants
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

def init():
    config.init()
    conversation.init()

def signal_handler(signal, frame):
    global interrupted
    interrupted = True
    utils.clean()

def detected_callback():
    if not utils.is_proper_time():
        return
    snowboydecoder.play_audio_file(constants.getData('beep_hi.wav'))
    conversation.stop()    

def do_not_bother_callback():    
    utils.do_not_bother = not utils.do_not_bother
    if utils.do_not_bother:
        snowboydecoder.play_audio_file(constants.getData('off.wav'))
        logger.info('勿扰模式打开')
    else:
        snowboydecoder.play_audio_file(constants.getData('on.wav'))
        logger.info('勿扰模式关闭')

def interrupt_callback():
    global interrupted
    return interrupted

def main():
    init()
    logger.debug('config: {}'.format(config.getConfig()))
    models = [
        constants.getHotwordModel(config.get('hotword', 'wukong.pmdl')),
        constants.getHotwordModel(utils.get_do_not_bother_hotword())        
    ]
    # capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    detector = snowboydecoder.HotwordDetector(models, sensitivity=config.get('sensitivity', 0.5))
    print('Listening... Press Ctrl+C to exit')

    # main loop
    detector.start(detected_callback=[detected_callback,
                                      do_not_bother_callback],
                   audio_recorder_callback=conversation.converse,
                   interrupt_check=interrupt_callback,
                   silent_count_threshold=5,
                   sleep_time=0.03)
    detector.terminate()

if __name__ == '__main__':
    main()


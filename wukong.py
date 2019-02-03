from snowboy import snowboydecoder
from robot import ASR, TTS, AI, Player, config, utils, constants
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

player, asr, ai, tts = None, None, None, None

def init():
    global asr, ai, tts
    config.init()
    asr = ASR.get_engine_by_slug(config.get('asr_engine', 'tencent-asr'))
    ai = AI.get_robot_by_slug(config.get('robot', 'tuling'))
    tts = TTS.get_engine_by_slug(config.get('tts_engine', 'baidu-tts'))

def signal_handler(signal, frame):
    global interrupted
    interrupted = True
    utils.clean()

def detected_callback():
    snowboydecoder.play_audio_file(constants.getData('beep_hi.wav'))
    global player
    if player is not None and player.is_playing():
        player.stop()
        player = None

def interrupt_callback():
    global interrupted
    return interrupted

def conversation(fp):
    global player, asr, ai, tts
    try:
        snowboydecoder.play_audio_file(constants.getData('beep_lo.wav'))
        print("converting audio to text")        
        query = asr.transcribe(fp)
        utils.check_and_delete(fp)        
        msg = ai.chat(query)        
        voice = tts.get_speech(msg)
        player = Player.getPlayerByFileName(voice)
        player.play(voice)
    except ValueError as e:
        logger.critical(e)
        utils.clean()

def main():
    init()
    logger.debug('config: {}'.format(config.getConfig()))
    model = constants.getHotwordModel(config.get('hotword', 'wukong.pmdl'))

    # capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    detector = snowboydecoder.HotwordDetector(model, sensitivity=config.get('sensitivity', 0.5))
    print('Listening... Press Ctrl+C to exit')

    # main loop
    detector.start(detected_callback=detected_callback,
                   audio_recorder_callback=conversation,
                   interrupt_check=interrupt_callback,
                   silent_count_threshold=5,
                   sleep_time=0.03)
    detector.terminate()

if __name__ == '__main__':
    main()

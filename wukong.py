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

player = None

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

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
    global player
    snowboydecoder.play_audio_file(constants.getData('beep_lo.wav'))
    print("converting audio to text")
    #asr = ASR.BaiduASR('9670645', 'qg4haN8b2bGvFtCbBGqhrmZy', '585d4eccb50d306c401d7df138bb02e7', 1936)
    asr = ASR.TencentASR('1253537070', 'AKID7C7JK9QomcWJUjcsKbK8iLQjhju8fC3z', '2vhKRVSn4mXQ9PiT7eOtBqQhR5Z6IvPn')
    #asr = ASR.XunfeiASR('5c540c39', '859bc21e90c64d97fae77695579eb05e')
    #asr = ASR.AliASR('x04ujKJ7oRvDgt6h', '7237029b69f146e89bac004bb61c09ee')
    query = asr.transcribe(fp)
    utils.check_and_delete(fp)
    ai = AI.TulingRobot('4d6eec9d9a9148bca73236bac6f35824')
    msg = ai.chat(query)
    #tts = TTS.BaiduTTS('9670645', 'qg4haN8b2bGvFtCbBGqhrmZy', '585d4eccb50d306c401d7df138bb02e7', 1, 'zh')
    #tts = TTS.TencentTTS('1253537070', 'AKID7C7JK9QomcWJUjcsKbK8iLQjhju8fC3z', '2vhKRVSn4mXQ9PiT7eOtBqQhR5Z6IvPn', 'ap-guangzhou', 1, 1)
    #tts = TTS.XunfeiTTS('5c540c39', '680c0eba7c1752503fa0a6ac971ce2cd', 'xiaoyan')
    tts = TTS.AliTTS('x04ujKJ7oRvDgt6h', '7237029b69f146e89bac004bb61c09ee', 'xiaoyun')
    voice_fname = tts.get_speech(msg)
    Player.play(voice_fname)    
    

def main():
    logger.info('config: {}'.format(config.getConfig()))
    model = constants.getData("wukong.pmdl")

    # capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)
    print('Listening... Press Ctrl+C to exit')

    # main loop
    detector.start(detected_callback=detected_callback,
                   audio_recorder_callback=conversation,
                   interrupt_check=interrupt_callback,
                   silent_count_threshold=5,
                   sleep_time=0.03)
    detector.terminate()

if __name__ == '__main__':
    config.init()
    main()

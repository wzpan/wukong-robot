from snowboy import snowboydecoder
from robot import asr, tts, ai, player, utils
import sys
import signal
import yaml
import requests
import logging
import os

interrupted = False
detected = False

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

mp3_player = None

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def detected_callback():
    snowboydecoder.play_audio_file()
    global detected, mp3_player
    detected = True
    if mp3_player is not None and mp3_player.is_playing():
        mp3_player.stop()
        mp3_player = None

def interrupt_callback():
    global interrupted
    return interrupted

def conversation(fp):
    global detected, mp3_player
    detected = False
    snowboydecoder.play_audio_file(snowboydecoder.DETECT_DONG)
    print("converting audio to text")
    asr_engine = asr.BaiduASR('9670645', 'qg4haN8b2bGvFtCbBGqhrmZy', '585d4eccb50d306c401d7df138bb02e7')
    query = asr_engine.transcribe(fp)
    utils.check_and_delete(fp)
    ai_engine = ai.TulingRobot('4d6eec9d9a9148bca73236bac6f35824')
    msg = ai_engine.chat(query)
    tts_engine = tts.BaiduTTS('9670645', 'qg4haN8b2bGvFtCbBGqhrmZy', '585d4eccb50d306c401d7df138bb02e7')
    voice = tts_engine.get_speech(msg)
    mp3_player = player.SoxPlayer()
    mp3_player.play(voice)
    

model = "wukong.pmdl"

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

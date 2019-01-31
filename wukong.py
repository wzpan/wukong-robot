from snowboy import snowboydecoder
import sys
import signal
import yaml
import requests
import logging

interrupted = False

def audioRecorderCallback(fp):
    snowboydecoder.play_audio_file(snowboydecoder.DETECT_DONG)
    print("converting audio to text")
    
    

def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted

model = "wukong.pmdl"

# capture SIGINT signal, e.g., Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)
print('Listening... Press Ctrl+C to exit')

def silence_callback():
    print("silence")
    

def test_vad():
    snowboydecoder.play_audio_file(snowboydecoder.DETECT_DING)
    print("say something...")
    


# main loop
detector.start(detected_callback=snowboydecoder.play_audio_file,
               audio_recorder_callback=audioRecorderCallback,
               interrupt_check=interrupt_callback,
               silent_count_threshold=3,
               sleep_time=0.03)

detector.terminate()

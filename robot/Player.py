# -*- coding: utf-8-*-
import subprocess
import threading
import os
import wave
from . import utils
import pyaudio
from robot import logging
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
from contextlib import contextmanager

logger = logging.getLogger(__name__)

def py_error_handler(filename, line, function, err, fmt):
    pass

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def no_alsa_error():
    try:
        asound = cdll.LoadLibrary('libasound.so')
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except:
        yield
        pass

def play(fname, onCompleted=None):
    # WavPlayer does not work well on my Macbook,
    # henceforce I choose SoxPlayer
    #player = getPlayerByFileName(fname)
    player = SoxPlayer()
    player.play(fname, onCompleted)

def getPlayerByFileName(fname):
    foo, ext = os.path.splitext(fname)
    if ext == '.mp3':
        return SoxPlayer()
    elif ext == '.wav':
        return WavPlayer()

class AbstractSoundPlayer(threading.Thread):

    def __init__(self, **kwargs):
        super(AbstractSoundPlayer, self).__init__()

    def play(self):
        pass

    def play_block(self):
        pass

    def stop(self):
        pass

    def is_playing(self):
        return False
    

class SoxPlayer(AbstractSoundPlayer):
    SLUG = 'SoxPlayer'

    def __init__(self, **kwargs):
        super(SoxPlayer, self).__init__(**kwargs)
        self.playing = False
        self.pipe = None
        self.delete = False
        self.volume = 1
        self.onCompleteds = []

    def run(self):
        cmd = ['play', '-v', str(self.volume), str(self.src)]
        logger.debug('Executing %s', ' '.join(cmd))

        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.playing = True
        self.proc.wait()
        self.playing = False
        if self.delete:
            utils.check_and_delete(self.src)
        logger.debug('play completed')
        for onCompleted in self.onCompleteds:
            if onCompleted:                
                onCompleted()
        self.onCompleteds = []

    def play(self, src, delete=False, onCompleted=None, volume=1):
        self.src = src        
        self.delete = delete
        self.onCompleteds.append(onCompleted)
        self.volume = volume
        self.start()

    def appendOnCompleted(self, onCompleted):
        if onCompleted:
            self.onCompleteds.append(onCompleted)

    def play_block(self):
        self.run()

    def stop(self):
        if self.proc:
            self.onCompleteds = []
            self.proc.terminate()
            if self.delete:
                utils.check_and_delete(self.src)                

    def is_playing(self):
        return self.playing


class WavPlayer(AbstractSoundPlayer):
    SLUG = 'WavPlayer'

    def __init__(self, **kwargs):
        super(WavPlayer, self).__init__(**kwargs)
        self.playing = False
        self.stop = False        

    def run(self):
        # play a voice
        CHUNK = 1024

        logger.debug("playing wave %s", self.src)
        f = wave.open(self.src, "rb")

        with no_alsa_error():
            audio = pyaudio.PyAudio()

        stream = audio.open(
            format=audio.get_format_from_width(f.getsampwidth()),
            channels=f.getnchannels(),
            rate=f.getframerate(),
            input=False,
            output=True)
        
        self.playing = True
        stream.start_stream()
        data = f.readframes(CHUNK)
        while data != '' and not self.stop:
            stream.write(data)
            data = f.readframes(CHUNK)
            print('data=="": {}, self.stop: {}'.format(data == '', self.stop))

        self.playing = False
        stream.stop_stream()
        stream.close()
        audio.terminate()
        if self.onCompleteds:
            for onCompleted in self.onCompleteds:
                if onCompleted:
                    onCompleted()

    def play(self, src, onCompleted=None):
        self.src = src
        self.onCompleted = onCompleted
        self.start()

    def play_block(self):
        self.run()

    def stop(self):
        self.stop = True
        utils.check_and_delete(self.src)

    def is_playing(self):
        return self.playing

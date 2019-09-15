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
    player = getPlayerByFileName(fname)
    player.play(fname, onCompleted)

def getPlayerByFileName(fname):
    foo, ext = os.path.splitext(fname)
    if ext in ['.mp3', '.wav']:
        return SoxPlayer()    

class AbstractPlayer(threading.Thread):

    def __init__(self, **kwargs):
        super(AbstractPlayer, self).__init__()

    def play(self):
        pass

    def play_block(self):
        pass

    def stop(self):
        pass

    def is_playing(self):
        return False
    

class SoxPlayer(AbstractPlayer):
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



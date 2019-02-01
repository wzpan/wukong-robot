# -*- coding: utf-8-*-
import subprocess
import time
import logging
import tempfile
import threading
from . import utils
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SoxPlayer(threading.Thread):
    SLUG = 'play'

    def __init__(self, **kwargs):
        super(SoxPlayer, self).__init__(**kwargs)
        self.playing = False
        self.pipe = None

    def run(self):
        cmd = ['play', str(self.src)]
        logger.debug('Executing %s', ' '.join(cmd))

        with tempfile.TemporaryFile() as f:
            self.pipe = subprocess.Popen(cmd, stdout=f, stderr=f)
            self.playing = True
            self.pipe.wait()
            self.playing = False
            f.seek(0)
            output = f.read()
            if output:
                logger.debug("play Output was: '%s'", output)
        utils.check_and_delete(self.src)

    def play(self, src):
        self.src = src
        self.start()

    def play_block(self):
        self.run()

    def stop(self):
        if self.pipe:
            self.pipe.kill()

    def is_playing(self):
        return self.playing

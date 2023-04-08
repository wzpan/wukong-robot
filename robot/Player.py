# -*- coding: utf-8 -*-
import asyncio
import subprocess
import os
import platform
import queue
import signal
import threading

from robot import logging
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
from contextlib import contextmanager

from . import utils

logger = logging.getLogger(__name__)


def py_error_handler(filename, line, function, err, fmt):
    pass


ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)


@contextmanager
def no_alsa_error():
    try:
        asound = cdll.LoadLibrary("libasound.so")
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except:
        yield
        pass


def play(fname, onCompleted=None):
    player = getPlayerByFileName(fname)
    player.play(fname, onCompleted=onCompleted)


def getPlayerByFileName(fname):
    foo, ext = os.path.splitext(fname)
    if ext in [".mp3", ".wav"]:
        return SoxPlayer()


class AbstractPlayer(object):
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

    def join(self):
        pass


class SoxPlayer(AbstractPlayer):
    SLUG = "SoxPlayer"

    def __init__(self, **kwargs):
        super(SoxPlayer, self).__init__(**kwargs)
        self.playing = False
        self.proc = None
        self.delete = False
        self.onCompleteds = []
        # 创建一个锁用于保证同一时间只有一个音频在播放
        self.play_lock = threading.Lock()
        self.play_queue = queue.Queue()  # 播放队列
        self.consumer_thread = threading.Thread(target=self.playLoop)
        self.consumer_thread.start()
        self.loop = asyncio.new_event_loop()  # 创建事件循环
        self.thread_loop = threading.Thread(target=self.loop.run_forever)
        self.thread_loop.start()

    def executeOnCompleted(self, res, onCompleted):
        # 全部播放完成，播放统一的 onCompleted()
        res and onCompleted and onCompleted()
        if self.play_queue.empty():
            for onCompleted in self.onCompleteds:
                onCompleted and onCompleted()

    def playLoop(self):
        while True:
            (src, onCompleted) = self.play_queue.get()
            if src:
                with self.play_lock:
                    logger.info(f"开始播放音频：{src}")
                    self.src = src
                    res = self.doPlay(src)
                    self.play_queue.task_done()
                    # 将 onCompleted() 方法的调用放到事件循环的线程中执行
                    self.loop.call_soon_threadsafe(
                        self.executeOnCompleted, res, onCompleted
                    )

    def doPlay(self, src):
        system = platform.system()
        if system == "Darwin":
            cmd = ["afplay", str(src)]
        else:
            cmd = ["play", str(src)]
        logger.debug("Executing %s", " ".join(cmd))
        self.proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.playing = True
        self.proc.wait()
        self.playing = False
        if self.delete:
            utils.check_and_delete(src)
        logger.info(f"播放完成：{src}")
        return self.proc and self.proc.returncode == 0

    def play(self, src, delete=False, onCompleted=None):
        if src and (os.path.exists(src) or src.startswith("http")):
            self.delete = delete
            self.play_queue.put((src, onCompleted))
        else:
            logger.critical(f"path not exists: {src}", stack_info=True)

    def preappendCompleted(self, onCompleted):
        onCompleted and self.onCompleteds.insert(0, onCompleted)

    def appendOnCompleted(self, onCompleted):
        onCompleted and self.onCompleteds.append(onCompleted)

    def play_block(self):
        self.run()

    def stop(self):
        if self.proc:
            self.onCompleteds = []
            self.proc.terminate()
            self.proc.kill()
            self.proc = None
            self.playing = False
            self._clear_queue()
            if self.delete:
                utils.check_and_delete(self.src)

    def is_playing(self):
        return self.playing or not self.play_queue.empty()

    def join(self):
        self.play_queue.join()

    def _clear_queue(self):
        with self.play_queue.mutex:
            self.play_queue.queue.clear()


class MusicPlayer(SoxPlayer):
    """
    给音乐播放器插件使用的，
    在 SOXPlayer 的基础上增加了列表的支持，
    并支持暂停和恢复播放
    """

    SLUG = "MusicPlayer"

    def __init__(self, playlist, plugin, **kwargs):
        super(MusicPlayer, self).__init__(**kwargs)
        self.playlist = playlist
        self.plugin = plugin
        self.idx = 0
        self.pausing = False

    def update_playlist(self, playlist):
        super().stop()
        self.playlist = playlist
        self.idx = 0
        self.play()

    def play(self):
        logger.debug("MusicPlayer play")
        path = self.playlist[self.idx]
        super().stop()
        super().play(path, False, self.next)

    def next(self):
        logger.debug("MusicPlayer next")
        super().stop()
        self.idx = (self.idx + 1) % len(self.playlist)
        self.play()

    def prev(self):
        logger.debug("MusicPlayer prev")
        super().stop()
        self.idx = (self.idx - 1) % len(self.playlist)
        self.play()

    def pause(self):
        logger.debug("MusicPlayer pause")
        self.pausing = True
        if self.proc:
            os.kill(self.proc.pid, signal.SIGSTOP)

    def stop(self):
        if self.proc:
            logger.debug(f"MusicPlayer stop {self.proc.pid}")
            self.onCompleteds = []
            os.kill(self.proc.pid, signal.SIGSTOP)
            self.proc.terminate()
            self.proc.kill()
            self.proc = None

    def resume(self):
        logger.debug("MusicPlayer resume")
        self.pausing = False
        self.onCompleteds = [self.next]
        if self.proc:
            os.kill(self.proc.pid, signal.SIGCONT)

    def is_playing(self):
        return self.playing

    def is_pausing(self):
        return self.pausing

    def turnUp(self):
        system = platform.system()
        if system == "Darwin":
            res = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                shell=False,
                capture_output=True,
                universal_newlines=True,
            )
            volume = int(res.stdout.strip())
            volume += 20
            if volume >= 100:
                volume = 100
                self.plugin.say("音量已经最大啦")
            subprocess.run(["osascript", "-e", f"set volume output volume {volume}"])
        elif system == "Linux":
            res = subprocess.run(
                ["amixer sget Master | grep 'Mono:' | awk -F'[][]' '{ print $2 }'"],
                shell=True,
                capture_output=True,
                universal_newlines=True,
            )
            if res.stdout != "" and res.stdout.strip().endswith("%"):
                volume = int(res.stdout.strip().replace("%", ""))
                volume += 20
                if volume >= 100:
                    volume = 100
                    self.plugin.say("音量已经最大啦")
                subprocess.run(["amixer", "set", "Master", f"{volume}%"])
            else:
                subprocess.run(["amixer", "set", "Master", "20%+"])
        else:
            self.plugin.say("当前系统不支持调节音量")
        self.resume()

    def turnDown(self):
        system = platform.system()
        if system == "Darwin":
            res = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                shell=False,
                capture_output=True,
                universal_newlines=True,
            )
            volume = int(res.stdout.strip())
            volume -= 20
            if volume <= 20:
                volume = 20
                self.plugin.say("音量已经很小啦")
            subprocess.run(["osascript", "-e", f"set volume output volume {volume}"])
        elif system == "Linux":
            res = subprocess.run(
                ["amixer sget Master | grep 'Mono:' | awk -F'[][]' '{ print $2 }'"],
                shell=True,
                capture_output=True,
                universal_newlines=True,
            )
            if res.stdout != "" and res.stdout.endswith("%"):
                volume = int(res.stdout.replace("%", "").strip())
                volume -= 20
                if volume <= 20:
                    volume = 20
                    self.plugin.say("音量已经最小啦")
                subprocess.run(["amixer", "set", "Master", f"{volume}%"])
            else:
                subprocess.run(["amixer", "set", "Master", "20%-"])
        else:
            self.plugin.say("当前系统不支持调节音量")
        self.resume()

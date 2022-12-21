from robot import constants, config
from unihiker import Audio, GUI
from pinpong.board import Board, Pin, Tone
from pinpong.extension.unihiker import *


class Unihiker(object):
    def __init__(self):
        Board().begin()
        self._gui = GUI()
        self._tone = Tone(Pin(Pin.P26))
        self._gui.draw_image(w=240, h=320, image=constants.getData("background.png"))
        self._my_bubble = self._gui.draw_text(
            x=20, y=25, w=150, color="red", text="(请说唤醒词)", font_size=10
        )
        self._bot_bubble = self._gui.draw_text(
            x=40, y=80, w=150, color="black", text="", font_size=10
        )

    def _play_tones(self, tones, duration):
        for tone in tones:
            self._tone.freq(tone)
            self._tone.on()
            time.sleep(duration)
            self._tone.off()

    def wakeup(self):
        if config.get("/unihiker/beep", False):
            self._play_tones([225, 329], 0.1)

    def think(self):
        if config.get("/unihiker/beep", False):
            self._play_tones([329, 225], 0.1)

    def record(self, t, text=""):
        self._my_bubble.config(
            text=text, color="black"
        ) if t == 0 else self._bot_bubble.config(text=text)

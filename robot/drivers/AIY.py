import time


class AIY:
    def __init__(self):
        self._wakeup = False
        self._think = False

    def wakeup(self):
        from aiy.board import Board, Led
        from aiy.leds import Leds, Pattern, Color

        self._wakeup = True
        with Board() as board:
            with Leds() as leds:
                while self._wakeup:
                    board.led.state = Led.ON
                    leds.pattern = Pattern.breathe(1000)
                    leds.update(Leds.rgb_pattern(Color.BLUE))
                    time.sleep(1)

    def think(self):
        from aiy.leds import Leds, Pattern, Color

        self._wakeup = False
        self._think = True
        with Leds() as leds:
            while self._think:
                leds.pattern = Pattern.blink(500)
                leds.update(Leds.rgb_pattern(Color.GREEN))
                time.sleep(1)

    def off(self):
        from aiy.board import Board, Led

        self._wakeup = False
        self._think = False
        with Board() as board:
            board.led.state = Led.OFF
        self.led = False

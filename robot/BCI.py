import importlib
import multiprocessing
from robot import config, logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MuseBCI(object):
    def __init__(self, event):
        self._wakeup_event = event
        self.last_blink = datetime.now() - timedelta(days=1.5)
        self.last_jaw = datetime.now() - timedelta(days=1.5)

    def start(self):
        osc_process = multiprocessing.Process(target=self._start_osc)
        osc_process.start()

    def blink_handler(self, unused_addr, args, blink):
        if blink:
            logger.info("blink detected")
            self.last_blink = datetime.now()
            if (self.last_blink - self.last_jaw) <= timedelta(seconds=1):
                self._wakeup_event.set()

    def jaw_clench_handler(self, unused_addr, args, jaw):
        if jaw:
            logger.info("Jaw_Clench detected")
            self.last_jaw = datetime.now()
            if (self.last_jaw - self.last_blink) <= timedelta(seconds=1):
                self._wakeup_event.set()

    def _start_osc(self):
        if not importlib.util.find_spec("pythonosc"):
            logger.critical("错误：请先安装 python-osc ！")
            return

        from pythonosc import dispatcher as dsp
        from pythonosc import osc_server

        dispatcher = dsp.Dispatcher()
        dispatcher.map("/muse/elements/blink", self.blink_handler, "EEG")
        dispatcher.map("/muse/elements/jaw_clench", self.jaw_clench_handler, "EEG")

        try:
            server = osc_server.ThreadingOSCUDPServer(
                (
                    config.get("/muse/ip", "127.0.0.1"),
                    int(config.get("/muse/port", "5001")),
                ),
                dispatcher,
            )
            logger.info(f"Muse serving on {server.server_address}")
            server.serve_forever()
        except Exception as e:
            logger.error(e, stack_info=True)

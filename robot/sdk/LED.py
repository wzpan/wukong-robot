import _thread as thread
from robot import config, logging
from robot.drivers.AIY import AIY

logger = logging.getLogger(__name__)

aiy = AIY()


def wakeup():
    if config.get("/LED/enable", False):
        if config.get("/LED/type") == "aiy":
            thread.start_new_thread(aiy.wakeup, ())
        elif config.get("/LED/type") == "respeaker":
            from robot.drivers.pixels import pixels

            pixels.wakeup()
        else:
            logger.error("错误：不支持的灯光类型")


def think():
    if config.get("/LED/enable", False):
        if config.get("/LED/type") == "aiy":
            thread.start_new_thread(aiy.think, ())
        elif config.get("/LED/type") == "respeaker":
            from robot.drivers.pixels import pixels

            pixels.think()
        else:
            logger.error("错误：不支持的灯光类型")


def off():
    if config.get("/LED/enable", False):
        if config.get("/LED/type") == "aiy":
            thread.start_new_thread(aiy.off, ())
        elif config.get("/LED/type") == "respeaker":
            from robot.drivers.pixels import pixels

            pixels.off()
        else:
            logger.off("错误：不支持的灯光类型")

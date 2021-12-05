# -*- coding: utf-8 -*-

import os
import subprocess
import time
from robot import config, constants, logging
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)


class Plugin(AbstractPlugin):

    SLUG = "camera"

    def handle(self, text, parsed):
        quality = config.get("/camera/quality", 100)
        count_down = config.get("/camera/count_down", 3)
        dest_path = config.get("/camera/dest_path", os.path.expanduser("~/pictures"))
        device = config.get("/camera/device", "/dev/video0")
        vertical_flip = config.get("/camera/verical_flip", False)
        horizontal_flip = config.get("/camera/horizontal_flip", False)
        sound = config.get("/camera/sound", True)
        camera_type = config.get("/camera/type", 0)
        if config.has("/camera/usb_camera") and config.get("/camera/usb_camera"):
            camera_type = 0
        if any(word in text for word in [u"安静", u"偷偷", u"悄悄"]):
            sound = False
        try:
            if not os.path.exists(dest_path):
                os.makedirs(dest_path)
        except Exception:
            self.say(u"抱歉，照片目录创建失败", cache=True)
            return
        dest_file = os.path.join(dest_path, "%s.jpg" % time.time())
        if camera_type == 0:
            # usb camera
            logger.info("usb camera")
            command = ["fswebcam", "--no-banner", "-r", "1024x765", "-q", "-d", device]
            if vertical_flip:
                command.extend(["-s", "v"])
            if horizontal_flip:
                command.extend(["-s", "h"])
            command.append(dest_file)
        elif camera_type == 1:
            # Raspberry Pi 5MP
            logger.info("Raspberry Pi 5MP camera")
            command = ["raspistill", "-o", dest_file, "-q", str(quality)]
            if count_down > 0 and sound:
                command.extend(["-t", str(count_down * 1000)])
            if vertical_flip:
                command.append("-vf")
            if horizontal_flip:
                command.append("-hf")
        else:
            # notebook camera
            logger.info("notebook camera")
            command = ["imagesnap", dest_file]
            if count_down > 0 and sound:
                command.extend(["-w", str(count_down)])
        if sound and count_down > 0:
            self.say(u"收到，%d秒后启动拍照" % (count_down), cache=True)
            if camera_type == 0:
                time.sleep(count_down)

        try:
            subprocess.run(command, shell=False, check=True)
            if sound:
                self.play(constants.getData("camera.wav"))
                photo_url = "http://{}:{}/photo/{}".format(
                    config.get("/server/host"),
                    config.get("/server/port"),
                    os.path.basename(dest_file),
                )
                self.say(u"拍照成功：{}".format(photo_url), cache=True)
        except subprocess.CalledProcessError as e:
            logger.error(e)
            if sound:
                self.say(u"拍照失败，请检查相机是否连接正确", cache=True)

    def isValid(self, text, parsed):
        return any(word in text for word in ["拍照", "拍张照"])

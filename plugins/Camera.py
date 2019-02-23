# -*- coding: utf-8-*-

import os
import subprocess
import time
import sys
from robot import config, constants
from robot.sdk.AbstractPlugin import AbstractPlugin

class Plugin(AbstractPlugin):

    SLUG = "camera"

    def handle(self, text, parsed):
        sys.path.append(constants.LIB_PATH)
        from robot.utils import emailUser

        quality = 100
        count_down = 3
        dest_path = os.path.expanduser('~/pictures')
        device = '/dev/video0'
        vertical_flip = False
        horizontal_flip = False
        send_to_user = True
        sound = True
        usb_camera = False
        # read config
        profile = config.get()
        if profile[self.SLUG] and 'enable' in profile[self.SLUG] and \
           profile[self.SLUG]['enable']:
            if 'count_down' in profile[self.SLUG] and \
               profile[self.SLUG]['count_down'] > 0:
                count_down = profile[self.SLUG]['count_down']
            if 'quality' in profile[self.SLUG] and \
               profile[self.SLUG]['quality'] > 0:
                quality = profile[self.SLUG]['quality']
            if 'dest_path' in profile[self.SLUG] and \
               profile[self.SLUG]['dest_path'] != '':
                dest_path = profile[self.SLUG]['dest_path']
            if 'device' in profile[self.SLUG] and \
               profile[self.SLUG]['device'] != '':
                device = profile[self.SLUG]['device']
            if 'vertical_flip' in profile[self.SLUG] and \
               profile[self.SLUG]['vertical_flip']:
                vertical_flip = True
            if 'horizontal_flip' in profile[self.SLUG] and \
               profile[self.SLUG]['horizontal_flip']:
                horizontal_flip = True
            if 'send_to_user' in profile[self.SLUG] and \
               not profile[self.SLUG]['send_to_user']:
                send_to_user = False
            if 'sound' in profile[self.SLUG] and \
               not profile[self.SLUG]['sound']:
                sound = False
            if 'usb_camera' in profile[self.SLUG] and \
                    profile[self.SLUG]['usb_camera']:
                usb_camera = True
            if any(word in text for word in [u"安静", u"偷偷", u"悄悄"]):
                sound = False
            try:
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
            except Exception:
                self.say(u"抱歉，照片目录创建失败", cache=True)
                return
            dest_file = os.path.join(dest_path, "%s.jpg" % time.time())
            if usb_camera:
                command = "fswebcam --no-banner -r 1024x765 -q -d %s" % (device)
                if vertical_flip:
                    command = command+' -s v '
                if horizontal_flip:
                    command = command+'-s h '
                command = command+dest_file
            else:
                command = ['raspistill', '-o', dest_file, '-q', str(quality)]
                if count_down > 0 and sound:
                    command.extend(['-t', str(count_down*1000)])
                if vertical_flip:
                    command.append('-vf')
                if horizontal_flip:
                    command.append('-hf')
            if sound and count_down > 0:
                self.say(u"收到，%d秒后启动拍照" % (count_down), cache=True)
                if usb_camera:
                    time.sleep(count_down)

            process = subprocess.Popen(command, shell=usb_camera)
            res = process.wait()
            if res != 0:
                if sound:
                    self.say(u"拍照失败，请检查相机是否连接正确", cache=True)
                return
            if sound:
                self.play(constants.getData('camera.wav'))
            # send to user
            if send_to_user:
                if sound:
                    self.say(u'拍照成功！正在发送照片到您的邮箱', cache=True)
                if emailUser(u"这是刚刚为您拍摄的照片", "", [dest_file]):
                    if sound:
                        self.say(u'发送成功', cache=True)
                else:
                    if sound:
                        self.say(u'发送失败了', cache=True)
        else:
            self.say(u"请先在配置文件中开启相机拍照功能", cache=True)


    def isValid(self, text, parsed):
        return any(word in text for word in ["拍照", "拍张照"])

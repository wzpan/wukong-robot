# -*- coding: utf-8-*-

import os
import subprocess
import time
import sys
from robot import config

SLUG = "camera"

def handle(text, mic, parsed=None):
    """
        Reports the current time based on the user's timezone.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        parsed -- NLU structure parsed by Baidu UNIT
    """
    sys.path.append(mic.dingdangpath.LIB_PATH)
    from utils import emailUser

    quality = 100
    count_down = 3
    dest_path = os.path.expanduser('~/pictures')
    vertical_flip = False
    horizontal_flip = False
    send_to_user = True
    sound = True
    usb_camera = False
    # read config
    profile = config.get()
    if profile[SLUG] and 'enable' in profile[SLUG] and \
       profile[SLUG]['enable']:
        if 'count_down' in profile[SLUG] and \
           profile[SLUG]['count_down'] > 0:
            count_down = profile[SLUG]['count_down']
        if 'quality' in profile[SLUG] and \
           profile[SLUG]['quality'] > 0:
            quality = profile[SLUG]['quality']
        if 'dest_path' in profile[SLUG] and \
           profile[SLUG]['dest_path'] != '':
            dest_path = profile[SLUG]['dest_path']
        if 'vertical_flip' in profile[SLUG] and \
           profile[SLUG]['vertical_flip']:
            vertical_flip = True
        if 'horizontal_flip' in profile[SLUG] and \
           profile[SLUG]['horizontal_flip']:
            horizontal_flip = True
        if 'send_to_user' in profile[SLUG] and \
           not profile[SLUG]['send_to_user']:
            send_to_user = False
        if 'sound' in profile[SLUG] and \
           not profile[SLUG]['sound']:
            sound = False
        if 'usb_camera' in profile[SLUG] and \
                profile[SLUG]['usb_camera']:
            usb_camera = True
        if any(word in text for word in [u"安静", u"偷偷", u"悄悄"]):
            sound = False
        try:
            if not os.path.exists(dest_path):
                os.makedirs(dest_path)
        except Exception:
            mic.say(u"抱歉，照片目录创建失败", cache=True, plugin=__name__)
            return
        dest_file = os.path.join(dest_path, "%s.jpg" % time.time())
        if usb_camera:
            command = "fswebcam --no-banner -r 1024x765 -q "
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
            mic.say(u"收到，%d秒后启动拍照" % (count_down), cache=True, plugin=__name__)
            if usb_camera:
                time.sleep(count_down)

        process = subprocess.Popen(command, shell=usb_camera)
        res = process.wait()
        if res != 0:
            if sound:
                mic.say(u"拍照失败，请检查相机是否连接正确", cache=True, plugin=__name__)
            return
        if sound:
            mic.play(mic.dingdangpath.data('audio', 'camera.wav'))
        # send to user
        if send_to_user:
            if sound:
                mic.say(u'拍照成功！正在发送照片到您的邮箱' % target, cache=True, plugin=__name__)
            if emailUser(u"这是刚刚为您拍摄的照片", "", [dest_file]):
                if sound:
                    mic.say(u'发送成功', cache=True, plugin=__name__)
            else:
                if sound:
                    mic.say(u'发送失败了', cache=True, plugin=__name__)
    else:
        mic.say(u"请先在配置文件中开启相机拍照功能", cache=True, plugin=__name__)


def isValid(text, parsed=None, immersiveMode=None):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
        parsed -- NLU structure parsed by Baidu UNIT
        immersiveMode -- current immersive mode
    """
    return any(word in text for word in ["拍照", "拍张照"])
